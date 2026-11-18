from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE))
import evolution
import runtime_web


class SystemApiTests(unittest.TestCase):
    def test_console_initialization_budget_and_auth_without_model_calls(self):
        class Handler(runtime_web.RuntimeMixin, BaseHTTPRequestHandler):
            def log_message(self, *_): pass
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); original = evolution.Archive
            with patch.object(evolution, 'DEFAULT_ROOT', root), patch.object(evolution, 'Archive', side_effect=lambda: original(root)):
                server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
                thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
                try:
                    base = 'http://127.0.0.1:' + str(server.server_address[1]) + '/api/agent/'
                    def get():
                        with urlopen(base + 'system') as response: return json.load(response)
                    def post(action, data, token):
                        request = Request(base + action, data=json.dumps(data).encode(),
                                          headers={'Content-Type': 'application/json', 'X-ARS-Token': token})
                        with urlopen(request) as response: return json.load(response)
                    state = get(); self.assertIsNone(state['evolution'])
                    with self.assertRaises(HTTPError) as rejected:
                        post('system-init', {'max_calls': 1}, 'wrong-token')
                    self.assertEqual(rejected.exception.code, 403)
                    post('system-init', {'max_calls': 1}, state['token'])
                    state = get(); self.assertEqual(state['evolution']['calls'], 0)
                    post('system-stop', {}, state['token'])
                    with self.assertRaises(HTTPError) as rejected:
                        post('system-optimize', {}, state['token'])
                    self.assertEqual(rejected.exception.code, 400)
                    post('system-budget', {'additional_calls': 2}, state['token'])
                    state = get(); self.assertEqual(state['evolution']['config']['max_calls'], 3)
                    self.assertEqual(state['evolution']['calls'], 0)
                finally:
                    server.shutdown(); server.server_close(); thread.join()
