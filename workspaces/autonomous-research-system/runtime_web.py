"""Same-host HTML controls for the actual agent runtime; no remote publication."""
import hmac
import hashlib
import json
import mimetypes
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
from urllib.parse import parse_qs, urlsplit, quote

import ars
import experiment_progress
import experiment_series
import experiment_monitor
import recovery_observation
import research_delivery
import token_usage
import task_trace
import model_routing
import draft_delivery
import execution_observation
import verification_monitor
import recovery_actions
import workspace_access

TOKEN = secrets.token_urlsafe(32)


def campaign_lifecycle(store):
    """Read lifecycle dates from the ledger, never from generic update times."""
    state = store.state()
    result = {'created_at': state['created_at'], 'last_started_at': None,
              'stopped_at': None, 'stop_source': None, 'status_changed_at': None,
              'reason': state['reason'], 'stop_reason': None}
    for row in store.db.execute("SELECT type,payload,created_at FROM events WHERE type IN ('campaign.status','controller.started','campaign.stop_requested') ORDER BY seq DESC"):
        payload = json.loads(row['payload'])
        kind, at = row['type'], row['created_at']
        if kind == 'campaign.status' and result['status_changed_at'] is None:
            result['status_changed_at'] = at
        if result['last_started_at'] is None and (kind == 'controller.started' or
                (kind == 'campaign.status' and payload.get('status') == 'RUNNING')):
            result['last_started_at'] = at
        if state['status'].startswith('STOPPED_'):
            if kind == 'campaign.status' and payload.get('status') == state['status'] and result['stopped_at'] is None:
                result['stopped_at'] = at
            if kind == 'campaign.stop_requested' and result['stop_source'] is None:
                # An older explicit stop must not explain a later legacy stop.
                if result['stopped_at'] is None or at >= result['stopped_at']:
                    result['stop_source'] = payload.get('source')
        if result['last_started_at'] is not None and result['status_changed_at'] is not None:
            break
    if state['status'] == 'STOPPED_USER':
        result['stop_reason'] = ('已收到明确停止请求（来源：' + result['stop_source'] + '）'
                                 if result['stop_source'] else
                                 '旧版停止记录未记录来源，无法区分主动停止与控制器退出信号。')
    elif state['status'].startswith('STOPPED_'):
        result['stop_reason'] = state['reason']
    return result


def order_campaigns(rows):
    ordered = sorted(rows, key=lambda r: (r['last_started_at'] or r['created_at'], r['created_at'], r['key']), reverse=True)
    topics = set()
    for row in ordered:
        row['is_latest_run'] = row['topic'] not in topics
        topics.add(row['topic'])
    return ordered


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
    def runtime_json(self, status, value, download_name=None):
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        if download_name:
            self.send_header('Content-Disposition', "attachment; filename*=UTF-8''" + quote(download_name))
        self.end_headers()
        self.wfile.write(body)

    def runtime_host_allowed(self):
        return workspace_access.host_allowed(self)

    def do_GET(self):
        url = urlsplit(self.path)
        if not url.path.startswith('/api/agent/'):
            return super().do_GET()
        if not self.runtime_host_allowed():
            return self.runtime_json(403, {'error': '工作空间地址不匹配'})
        try:
            if url.path == '/api/agent/options':
                capability_path = ars.REPO / '.local/workspace-capabilities.json'
                capabilities = ars.read_json(capability_path) if capability_path.is_file() else {}
                topics = [{'id': 'ARS-DEMO', 'title': '独立程序验证'}]
                topics += [{'id': row['id'], 'title': row.get('title', row['id'])} for row in ars.read_json(ars.REPO / 'workspaces/topics.json')['topics']]
                targets = [{'id': row['id'], 'label': row['label'], 'kind': row['kind'], 'description': row.get('description', ''), 'has_review_profile': bool(row.get('review_profile'))} for row in ars.submission_targets(ars.REPO).values()]
                return self.runtime_json(200, {'topics': topics, 'submission_targets': targets, 'default_submission_target': 'none', 'model_routing': model_routing.options(), 'paper_topics': capabilities.get('paper_topics', [])})
            if url.path == '/api/agent/system':
                import evolution
                import system_supervisor
                out = {'version': ars.VERSION, 'token': TOKEN, 'evolution': None, 'supervisor': None}
                if (evolution.DEFAULT_ROOT / 'archive.sqlite3').exists():
                    archive = evolution.Archive()
                    try:
                        if archive.db.execute('SELECT 1 FROM settings').fetchone():
                            out['evolution'] = archive.status()
                    finally: archive.close()
                status = system_supervisor.ROOT / 'status.json'
                if status.exists(): out['supervisor'] = ars.read_json(status)
                identity = system_supervisor.ROOT / 'process.json'
                out['supervisor_alive'] = identity.exists() and ars.same_process(ars.read_json(identity))
                validation = ars.HERE / 'system-validation.json'
                if validation.exists(): out['validation'] = ars.read_json(validation)
                return self.runtime_json(200, out)
            paths = campaign_paths()
            if url.path == '/api/agent/usage-overview':
                return self.runtime_json(200, token_usage.portfolio(paths),
                    'research-model-token-usage.json' if parse_qs(url.query).get('download') == ['1'] else None)
            if url.path == '/api/agent/campaigns':
                rows = []
                for key, directory in paths.items():
                    s = ars.Store(directory)
                    try:
                        state = s.state()
                        if (state['status'] == 'READY' and
                                state['config'].get('experiment_observations', {}).get('enabled') is True):
                            observed = ars.public_state(s)
                            experiment_series.apply_active_status(observed)
                            state['status'] = observed['status']
                        rows.append({'key': key, 'id': state['id'], 'topic': state['topic'], 'goal': state['goal'], 'status': state['status'], 'backend': state['config']['backend'], 'workflow': state['config'].get('workflow', 'readonly'), 'submission_target': ars.saved_submission_target(state['config']), 'updated_at': state['updated_at'], **campaign_lifecycle(s)})
                    finally:
                        s.close()
                return self.runtime_json(200, {'campaigns': order_campaigns(rows), 'token': TOKEN, 'version': ars.VERSION})
            key = parse_qs(url.query).get('key', [''])[0]
            if key not in paths:
                return self.runtime_json(404, {'error': '不存在的运行'})
            s = ars.Store(paths[key])
            try:
                if url.path == '/api/agent/operation-log':
                    return self.runtime_json(200, recovery_actions.operation_log(s, parse_qs(url.query).get('operation', [''])[0]))
                if url.path == '/api/agent/job-log':
                    reference = parse_qs(url.query).get('job',[''])[0]
                    return self.runtime_json(200, execution_observation.log(s.directory, reference))
                if url.path == '/api/agent/verification-log':
                    return self.runtime_json(200,verification_monitor.log(s.directory,parse_qs(url.query).get('session',[''])[0]))
                if url.path == '/api/agent/usage':
                    return self.runtime_json(200, token_usage.describe(s, include_requests=True),
                        s.state()['id'] + '-token-usage.json' if parse_qs(url.query).get('download') == ['1'] else None)
                if url.path == '/api/agent/artifact':
                    query = parse_qs(url.query)
                    try:
                        if query.get('stage') == ['draft']:
                            entry, body = draft_delivery.artifact_bytes(s.directory, s.state(),
                                int(query.get('index', ['-1'])[0]),query.get('sha256', [''])[0])
                        elif query.get('stage') == ['supplement']:
                            entry, body = recovery_observation.artifact_bytes(
                                s.directory, s.state(), int(query.get('index', ['-1'])[0]),
                                query.get('sha256', [''])[0])
                        else:
                            entry, body = research_delivery.artifact_bytes(
                                ars.REPO, s.state(), query.get('stage', [''])[0],
                                int(query.get('index', ['-1'])[0]), query.get('sha256', [''])[0])
                    except ValueError as exc:
                        return self.runtime_json(404, {'error': str(exc)})
                    if entry['path'].suffix.lower() == '.html' and query.get('download') != ['1']:
                        body = research_delivery.reader_bytes(ars.REPO, s.state(), entry, body)
                    mime = mimetypes.guess_type(entry['path'].name)[0] or 'application/octet-stream'
                    if mime.startswith('text/') or mime in ('application/json', 'image/svg+xml'):
                        mime += '; charset=utf-8'
                    self.send_response(200)
                    self.send_header('Content-Type', mime)
                    self.send_header('Content-Length', str(len(body)))
                    self.send_header('Cache-Control', 'no-store')
                    self.send_header('X-Content-Type-Options', 'nosniff')
                    self.send_header('ETag', '"' + hashlib.sha256(body).hexdigest() + '"')
                    self.send_header('X-ARS-Source-SHA256', entry['sha256'])
                    disposition = 'attachment' if query.get('download') == ['1'] else 'inline'
                    self.send_header('Content-Disposition', disposition + "; filename*=UTF-8''" + quote(entry['path'].name))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                if url.path == '/api/agent/state':
                    out = ars.public_state(s)
                    experiment_series.apply_active_status(out)
                    out['experiment_progress'] = experiment_progress.observe(s.directory, out)
                    out['experiment_progress'] = recovery_observation.observe(s.directory, out, out['experiment_progress'])
                    out['experiment_progress'] = experiment_series.observe(s, out, out['experiment_progress'])
                    out['experiment_progress'] = experiment_monitor.observe(s, out, out['experiment_progress'])
                    out['execution_observation'] = execution_observation.describe(s, out)
                    out['verification_tracking'] = verification_monitor.describe(s,out,out['execution_observation'])
                    out['recovery_actions'] = recovery_actions.describe(s)
                    out['delivery'] = research_delivery.describe(ars.REPO, out)
                    out['drafts'] = draft_delivery.describe(s.directory, out)
                    if out['delivery']:
                        out['delivery']['links'] += recovery_observation.links(out, out['experiment_progress'])
                    out['token_usage'] = token_usage.observe(s)
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
            if action in ('system-init', 'system-optimize', 'system-rollback', 'system-stop', 'system-budget'):
                import evolution
                archive = evolution.Archive()
                try:
                    if action == 'system-init':
                        with archive.lock():
                            if not evolution.benchmark.evaluate(ars.HERE)['viable']:
                                raise ValueError('当前策略或隔离执行环境未通过初始化检查')
                            archive.configure(data.get('max_calls', 2), data.get('timeout', 300), str(data.get('model', '')))
                            initial = archive.register(ars.HERE, origin='bootstrap', hypothesis='Measured current bundled system strategy')
                            archive.promote(initial['id'], initial=True)
                    elif action == 'system-stop': archive.stop()
                    elif action == 'system-rollback':
                        with archive.lock(): archive.rollback('User requested rollback from system console')
                    elif action == 'system-budget':
                        additional = data.get('additional_calls')
                        if type(additional) is not int or not 1 <= additional <= 20:
                            raise ValueError('新增系统优化调用须为1至20的整数')
                        with archive.lock():
                            cfg, _ = archive.config(); cfg['max_calls'] += additional; cfg['stopped'] = False
                            archive.db.execute('UPDATE settings SET config=?', (ars.dump(cfg),))
                            archive.event('budget.user_extended', {'additional_calls': additional})
                    else:
                        cfg, calls = archive.config()
                        if cfg['stopped'] or calls >= cfg['max_calls']:
                            raise ValueError('系统优化已停止或达到调用上限；研究任务预算独立保留')
                        with archive.lock():
                            active = archive.db.execute("SELECT 1 FROM operations WHERE state IN ('RESERVED','RUNNING','UNKNOWN')").fetchone()
                            if active: raise ValueError('已有系统优化调用正在运行或等待回执')
                        with (archive.root / 'controller.log').open('a') as log:
                            child = subprocess.Popen([sys.executable, str(ars.HERE / 'evolution.py'), 'run', '--iterations', '1'],
                                                     stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
                        ars.BACKGROUND.append(child)
                    return self.runtime_json(200, {'status': 'accepted', 'calls': archive.config()[1]})
                finally: archive.close()
            if action == 'create-research':
                import research_registry
                return self.runtime_json(201, research_registry.create(data))
            if action == 'create':
                allowed = {'topic', 'goal', 'backend', 'max_calls', 'max_seconds', 'task_timeout', 'max_tokens', 'model', 'model_policy', 'name', 'import_history', 'submission_target', 'submission_target_name', 'workflow'}
                if set(data) - allowed:
                    raise ValueError('不支持的创建字段')
                do_import = data.pop('import_history', False)
                for k in ('topic', 'goal', 'backend', 'model', 'name', 'submission_target', 'submission_target_name', 'workflow'):
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
            if action == 'recovery-action':
                return self.runtime_json(202, recovery_actions.submit(directory, data))
            if action == 'model-policy':
                s = ars.Store(directory)
                try:
                    return self.runtime_json(200, model_routing.save(s, data.get('policy'), data.get('default_model')))
                finally:s.close()
            if action == 'system-enroll':
                import system_supervisor
                return self.runtime_json(200, system_supervisor.enroll(directory))
            if action == 'start':
                return self.runtime_json(200, ars.start_campaign(directory))
            if action == 'stop':
                ars.stop_campaign(directory, source='web')
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
                        phase = ars.paper_workflow.supplement_phase(s.tasks(), s.state()['topic'], s.state()['config']) if ars.paper_workflow.enabled(s.state()['config']) else 'investigate'
                        task = s.add_task(str(data.get('title', '')), str(data.get('instruction', '')), phase)
                        s.memory('decision', '用户补充：' + str(data.get('instruction', '')), status='user_instruction')
                        if s.state()['status'] in ('COMPLETED', 'WAITING_EXTERNAL'):
                            s.status('READY')
                    ars.write_report(s)
                    return self.runtime_json(200, {'task_id': task})
                finally:
                    s.close()
            if action == 'supplement':
                s = ars.Store(directory)
                try:
                    return self.runtime_json(200, task_trace.save(s, data))
                finally:
                    s.close()
            return self.runtime_json(404, {'error': '未知操作'})
        except (ValueError, TypeError, KeyError, OSError, sqlite3.Error) as exc:
            return self.runtime_json(400, {'error': str(exc)})
