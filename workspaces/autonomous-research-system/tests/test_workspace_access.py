"""Exercise direct remote access without starting any model or experiment."""
from http.server import ThreadingHTTPServer
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import serve
import runtime_web
import workspace_access as access


class RemoteWorkspaceTests(unittest.TestCase):
    def setUp(self):
        class RemoteHandler(serve.Handler):
            def setup(self):
                super().setup()
                self.client_address = ('192.0.2.15', self.client_address[1])

            def log_message(self, *_):
                pass

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        here = self.root / 'workspaces/autonomous-research-system'
        (here / 'ui/dist/assets').mkdir(parents=True)
        (here / 'ui/dist/index.html').write_text('public application shell')
        (here / 'runtime.html').write_text('private legacy research snapshot')
        (self.root / 'workspaces/topics.json').write_text('{"topics": []}')
        for target, field, value in ((serve, 'REPO', self.root), (runtime_web, 'campaign_paths', lambda: {})):
            p = patch.object(target, field, value)
            p.start(); self.addCleanup(p.stop)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), RemoteHandler)
        self.policy = access.WorkspaceAccess('synthetic-key-for-network-tests-only-0123456789')
        self.server.workspace_access = self.policy
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()

    def request(self, path, method='GET', data=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        self.addCleanup(conn.close)
        kwargs = {'Content-Type': 'application/json', **(headers or {})}
        conn.request(method, path, json.dumps(data) if data is not None else None, kwargs)
        response = conn.getresponse()
        body = response.read()
        return response.status, dict(response.getheaders()), body

    def login(self):
        status, headers, body = self.request('/api/agent/connect', 'POST', {'access_key': self.policy.key})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)['authenticated'])
        self.assertIn('HttpOnly; SameSite=Strict', headers['Set-Cookie'])
        return {'Cookie': headers['Set-Cookie'].split(';')[0]}

    def test_remote_shell_is_public_but_research_and_tokens_require_login(self):
        page = serve.PREFIX + 'runtime.html'
        self.assertEqual(self.request(page)[0], 200)
        for path in ('/api/agent/campaigns', '/workspaces/topics.json', page + '?legacy=1'):
            self.assertEqual(self.request(path)[0], 401, path)
        self.assertEqual(self.request('/workspaces/topics.json', 'HEAD')[0], 401)
        info = json.loads(self.request('/api/agent/connection')[2])
        self.assertFalse(info['authenticated'])
        self.assertNotIn('access_key', info)
        self.assertNotIn('addresses', info)
        authenticated = self.login()
        self.assertEqual(self.request('/api/agent/campaigns', headers=authenticated)[0], 200)
        self.assertEqual(self.request('/workspaces/topics.json', headers=authenticated)[0], 200)
        self.assertNotIn('access_key', json.loads(self.request('/api/agent/connection', headers=authenticated)[2]))

    def test_invalid_credentials_cookie_expiry_and_foreign_origins_are_rejected(self):
        self.assertEqual(self.request('/api/agent/connect', 'POST', {'access_key': 'wrong'})[0], 401)
        self.assertEqual(self.request('/api/agent/connect', 'POST', {'access_key': '中文'})[0], 401)
        self.assertEqual(self.request('/api/agent/connect', 'POST', {'access_key': self.policy.key}, {'Origin': 'http://untrusted.invalid'})[0], 403)
        self.assertEqual(self.request('/api/agent/connect', 'POST', [self.policy.key])[0], 401)
        cookie = self.login()
        tampered = {'Cookie': cookie['Cookie'] + 'x'}
        self.assertEqual(self.request('/api/agent/campaigns', headers=tampered)[0], 401)
        with patch.object(access.time, 'time', return_value=time.time() + access.SESSION_SECONDS + 1):
            self.assertEqual(self.request('/api/agent/campaigns', headers=cookie)[0], 401)

    def test_authenticated_actions_still_require_the_operation_token(self):
        cookie = self.login()
        token = json.loads(self.request('/api/agent/campaigns', headers=cookie)[2])['token']
        self.assertEqual(self.request('/api/agent/stop', 'POST', {'key': 'not-registered'}, cookie)[0], 403)
        headers = {**cookie, 'X-ARS-Token': token}
        self.assertEqual(self.request('/api/agent/stop', 'POST', {'key': 'not-registered'}, {**headers, 'Origin': 'http://untrusted.invalid'})[0], 403)
        # A valid session and operation token reach normal key validation.
        self.assertEqual(self.request('/api/agent/stop', 'POST', {'key': 'not-registered'}, headers)[0], 404)

    def test_wrong_host_is_rejected_even_with_a_valid_session(self):
        cookie = self.login()
        self.assertEqual(self.request('/api/agent/campaigns', headers={**cookie, 'Host': f'untrusted.invalid:{self.server.server_port}'})[0], 403)
        self.assertEqual(self.request('/api/agent/connection', headers={'Host': f'192.0.2.123:{self.server.server_port}'})[0], 403)

    def test_local_access_remains_automatic_and_only_local_shows_connection_code(self):
        class LocalHandler(serve.Handler):
            def log_message(self, *_): pass
        local = ThreadingHTTPServer(('127.0.0.1', 0), LocalHandler)
        self.addCleanup(local.server_close)
        local.workspace_access = self.policy
        thread = threading.Thread(target=local.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(local.shutdown)
        conn = http.client.HTTPConnection('127.0.0.1', local.server_port)
        self.addCleanup(conn.close)
        conn.request('GET', '/api/agent/connection')
        info = json.loads(conn.getresponse().read())
        self.assertTrue(info['authenticated'])
        self.assertTrue(info['local'])
        self.assertEqual(info['access_key'], self.policy.key)
        local.workspace_access = None
        conn.request('GET', '/api/agent/connection')
        self.assertFalse(json.loads(conn.getresponse().read())['remote_enabled'])

    def test_connection_code_is_persistent_local_file_with_private_permissions(self):
        path = self.root / '.local/workbench-access.json'
        first = access.WorkspaceAccess.load(path)
        self.assertEqual(first.key, access.WorkspaceAccess.load(path).key)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertGreaterEqual(len(first.key), 32)


if __name__ == '__main__':
    unittest.main()
