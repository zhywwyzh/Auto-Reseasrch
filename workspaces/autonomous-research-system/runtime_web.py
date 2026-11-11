"""Same-host HTML controls for the actual agent runtime; no remote publication."""
import hmac
import json
from pathlib import Path
import secrets
import sqlite3
from urllib.parse import parse_qs, urlsplit

import ars

TOKEN = secrets.token_urlsafe(32)


def campaign_paths():
    roots = {'ARS-DEMO': ars.HERE}
    for row in ars.read_json(ars.REPO / 'workspaces/topics.json')['topics']:
        roots[row['id']] = ars.REPO / row['workspace']
    found = {}
    for topic, root in roots.items():
        for p in (root / 'runs/ars').glob('*/state.sqlite3'):
            if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):
                continue
            found[topic + '/' + p.parent.name] = p.parent
    return found


class RuntimeMixin:
    def runtime_json(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def runtime_host_allowed(self):
        port = self.server.server_address[1]
        return self.headers.get('Host') in {f'127.0.0.1:{port}', f'localhost:{port}'}

    def do_GET(self):
        url = urlsplit(self.path)
        if not url.path.startswith('/api/agent/'):
            return super().do_GET()
        if not self.runtime_host_allowed():
            return self.runtime_json(403, {'error': '仅允许本机地址访问'})
        try:
            paths = campaign_paths()
            if url.path == '/api/agent/campaigns':
                rows = []
                for key, directory in paths.items():
                    s = ars.Store(directory)
                    try:
                        state = s.state()
                        rows.append({'key': key, 'id': state['id'], 'topic': state['topic'], 'goal': state['goal'], 'status': state['status'], 'backend': state['config']['backend'], 'updated_at': state['updated_at']})
                    finally:
                        s.close()
                return self.runtime_json(200, {'campaigns': sorted(rows, key=lambda x: x['updated_at'], reverse=True), 'token': TOKEN, 'version': ars.VERSION})
            key = parse_qs(url.query).get('key', [''])[0]
            if key not in paths:
                return self.runtime_json(404, {'error': '不存在的运行'})
            s = ars.Store(paths[key])
            try:
                if url.path == '/api/agent/state':
                    out = ars.public_state(s)
                    out['report'] = (s.directory / 'artifacts/report.md').read_text() if (s.directory / 'artifacts/report.md').exists() else ''
                    out['memories'] = [dict(r) for r in s.db.execute('SELECT kind,text,status,created_at FROM memories ORDER BY rowid DESC LIMIT 25')]
                    return self.runtime_json(200, out)
            finally:
                s.close()
            return self.runtime_json(404, {'error': '未知接口'})
        except (ValueError, OSError, sqlite3.Error) as exc:
            return self.runtime_json(400, {'error': str(exc)})

    def do_POST(self):
        if not self.path.startswith('/api/agent/'):
            return self.runtime_json(404, {'error': '未知接口'})
        expected_origin = 'http://' + self.headers.get('Host', '')
        if not self.runtime_host_allowed() or self.headers.get('Origin', expected_origin) != expected_origin or not hmac.compare_digest(self.headers.get('X-ARS-Token', ''), TOKEN):
            return self.runtime_json(403, {'error': '来源或操作令牌无效，请刷新操作台'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size <= 0 or size > 64000 or self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                raise ValueError('需要不超过64KB的JSON请求')
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError('JSON需要为对象')
            action = self.path.rsplit('/', 1)[-1]
            if action == 'create':
                allowed = {'topic', 'goal', 'backend', 'max_calls', 'max_seconds', 'task_timeout', 'max_tokens', 'model', 'name', 'import_history'}
                if set(data) - allowed:
                    raise ValueError('不支持的创建字段')
                do_import = data.pop('import_history', False)
                for k in ('topic', 'goal', 'backend', 'model', 'name'):
                    if k in data and not isinstance(data[k], str):
                        raise ValueError('目标、课题与模型字段需要为文本')
                for k in ('max_calls', 'max_seconds', 'task_timeout', 'max_tokens'):
                    if k in data and type(data[k]) is not int:
                        raise ValueError('预算参数必须为整数')
                directory = ars.create_campaign(**data)
                if do_import:
                    s = ars.Store(directory)
                    try:
                        ars.import_history(s)
                    finally:
                        s.close()
                return self.runtime_json(201, {'key': data['topic'] + '/' + directory.name})
            paths = campaign_paths()
            key = data.get('key')
            if key not in paths:
                return self.runtime_json(404, {'error': '不存在的运行'})
            directory = paths[key]
            if action == 'start':
                return self.runtime_json(200, ars.start_campaign(directory))
            if action == 'stop':
                ars.stop_campaign(directory)
                return self.runtime_json(200, {'status': 'STOPPED_USER'})
            if action == 'resume':
                ars.resume_campaign(directory)
                return self.runtime_json(200, ars.start_campaign(directory))
            if action == 'import-history':
                s = ars.Store(directory)
                try:
                    return self.runtime_json(200, ars.import_history(s))
                finally:
                    s.close()
            if action == 'add':
                s = ars.Store(directory)
                try:
                    with s.tx():
                        task = s.add_task(str(data.get('title', '')), str(data.get('instruction', '')))
                        s.memory('decision', '用户补充：' + str(data.get('instruction', '')), status='user_instruction')
                        if s.state()['status'] in ('COMPLETED', 'WAITING_EXTERNAL'):
                            s.status('READY')
                    ars.write_report(s)
                    return self.runtime_json(200, {'task_id': task})
                finally:
                    s.close()
            return self.runtime_json(404, {'error': '未知操作'})
        except (ValueError, TypeError, KeyError, OSError, sqlite3.Error) as exc:
            return self.runtime_json(400, {'error': str(exc)})
