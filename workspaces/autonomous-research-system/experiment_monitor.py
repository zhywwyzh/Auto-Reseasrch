"""Operation-scoped experiment dashboards and side-channel job observations.

Dashboard design is data, never executable HTML supplied by a research agent.
The platform renders it in the existing UI. Monitoring cannot admit science,
submit work, retry SSH or turn process liveness into training progress.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import uuid
import execution_visibility

from experiment_progress import load, stamp

VERSION = 'experiment-dashboard-v1'
PHASES = {'validate', 'pilot', 'experiment', 'prepare_implementation'}
STATES = {'pending', 'running', 'completed', 'failed', 'blocked', 'unknown'}
INSTRUCTION = (
    '实验进度前端是本阶段必需交付。开始实验作业前，主动根据本轮协议设计看板，'
    '使用experiment_monitor.py plan登记title、objective、steps（id/label/unit/total/target_basis）；'
    'total未知填null，不虚构分母。平台自动渲染并每2秒刷新，无需用户催促，也无需另开Web服务。'
    '步骤应具体到准备、各对照/种子/批次、汇总和独立复验，不能只写“实验中”。'
    '每个步骤开始/结束、失败、修复、复验和阶段切换时主动调用update；包含summary、'
    'current_step、next_action、blocker和steps。每项steps包含id/status/detail；真实计数'
    'completed/failed须同时绑定本次运行内source.path及source.sha256证据；默认核对证据中的'
    'completed/failed同名字段，也可通过source.completed_field/failed_field指定点分字段路径。不把计划当实测。'
    '长作业用job_runner自动保留5秒心跳；训练器/只读旁路采集器按约5秒更新真实计数，'
    '不能仅在模型返回时描述进度。冻结源码不能热改；监控异常只记录，不重投实验。'
    '结束前发布最终说明及剩余工作；工作项状态与科学验收分开。研究看板数据仅存本任务Git忽略区。'
)


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def folder(directory, operation):
    if not isinstance(operation, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', operation):
        raise ValueError('无效实验operation身份')
    root = Path(directory).resolve()
    path = root / 'telemetry/experiments' / operation
    if not path.resolve().is_relative_to(root) or any(p.is_symlink() for p in [path, *path.parents] if p != root and p.is_relative_to(root)):
        raise ValueError('拒绝符号链接实验看板目录')
    return path


def dashboard_folder(directory, operation):
    """Use the executor-writable artifact area, retaining legacy dashboards."""
    root = Path(directory).resolve()
    if (root / 'artifacts').is_symlink():
        raise ValueError('拒绝符号链接实验产物目录')
    writable = folder(root / 'artifacts', operation)
    legacy = folder(root, operation)
    # Existing executors already publish here because only artifacts is writable.
    # Prefer their data over a requirement-only legacy directory.
    if (writable / 'requirement.json').exists() or not (legacy / 'requirement.json').exists():
        return writable
    return legacy


def prepare(state, directory, task):
    if task.get('phase') not in PHASES or not task.get('operation_id'):
        return None
    import git_boundary
    git_boundary.validate_state(state, directory)
    path = dashboard_folder(directory, task['operation_id'])
    requirement = path / 'requirement.json'
    if not requirement.exists():
        write(requirement, dict(version=VERSION, topic=state['topic'], run_id=state['id'],
              task_id=task['id'], operation_id=task['operation_id'], phase=task['phase'],
              task_title=task['title'], visibility_version=execution_visibility.VERSION, created_at=stamp(time.time())))
    saved = load(requirement, Path(directory).resolve())
    return {'version': VERSION, 'module': str(Path(__file__).resolve()),
            'directory': str(directory), 'operation_id': task['operation_id'],
            'plan_path': str(path / 'plan.json'), 'status_path': str(path / 'status.json'),
            'instruction': INSTRUCTION + execution_visibility.INSTRUCTION,
            'observation_required': saved.get('visibility_version') == execution_visibility.VERSION,
            'commands': {'plan': 'python3 <module> plan --directory <directory> --operation <operation_id> --input <design.json>',
                         'update': 'python3 <module> update --directory <directory> --operation <operation_id> --input <status.json>'},
            'design_example': {'title': '本轮对照与复验', 'objective': '填写本轮要检验的问题',
                'observation': execution_visibility.example(),
                'steps': [{'id': 'comparison', 'label': '填写具体方法与批次', 'unit': '回合',
                           'total': None, 'target_basis': '待冻结协议确定'}]},
            'status_example': {'summary': '填写当前具体动作与已观察结果', 'current_step': 'comparison',
                'next_action': '填写接下来要执行和核验的步骤', 'blocker': '',
                'steps': [{'id': 'comparison', 'status': 'running', 'detail': '填写实际进展'}]},
            'unknown_step_example': {'id': 'comparison', 'status': 'unknown', 'detail': '原退出回执缺失，不能猜测服务器停止',
                'checks': [{'what': '填写缺失的具体证据', 'evidence': '填写原回执/日志/采集路径或明确尚未取得',
                            'system_action': '填写系统接下来的具体检查及修复动作',
                            'user_action': '通常由系统处理，无需手工核对', 'user_required': False}]}}


def text(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise ValueError('缺少或超长看板字段：' + name)
    return value


def validate_plan(data):
    if not isinstance(data, dict):
        raise ValueError('看板设计须为对象')
    text(data.get('title'), 'title'); text(data.get('objective'), 'objective')
    steps = data.get('steps')
    if not isinstance(steps, list) or not 1 <= len(steps) <= 100:
        raise ValueError('看板需要1至100个具体工作项')
    ids = []
    for step in steps:
        if not isinstance(step, dict):
            raise ValueError('工作项须为对象')
        key = text(step.get('id'), 'id')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', key):
            raise ValueError('工作项id无效')
        ids.append(key)
        for name in ('label', 'unit', 'target_basis'):
            text(step.get(name), name)
        total = step.get('total')
        if total is not None and (type(total) is not int or total <= 0):
            raise ValueError('工作项分母须为正整数或null')
    if len(set(ids)) != len(ids):
        raise ValueError('工作项id重复')
    if 'observation' in data:execution_visibility.validate(data['observation'])
    return data


def validate_required_observation(plan, requirement, published=True):
    if requirement.get('visibility_version') == execution_visibility.VERSION:
        if published and plan.get('visibility_version') != execution_visibility.VERSION:
            raise ValueError('本次调用的观测契约版本缺失或不匹配')
        execution_visibility.validate(plan.get('observation'))


def required_contract(directory, operation):
    """An erased artifact must not silently downgrade a new call to legacy."""
    root = Path(directory).resolve()
    db = sqlite3.connect((root/'state.sqlite3').as_uri()+'?mode=ro', uri=True)
    try:
        row = db.execute('SELECT directory FROM operations WHERE id=?', (operation,)).fetchone()
    finally:db.close()
    required = False
    if row:
        request = Path(row[0])/'request.json'
        if request.exists():
            context = load(request, root).get('context', {})
            required = context.get('execution_workflow', {}).get('experiment_dashboard', {}).get('observation_required') is True
    path = dashboard_folder(root, operation)/'requirement.json'
    if not path.exists():
        if required:raise ValueError('本次调用要求自适应观测设计，不能删除requirement绕过启动/验收检查')
        return None
    requirement = load(path, root)
    if required and requirement.get('visibility_version') != execution_visibility.VERSION:
        raise ValueError('本次调用的观测契约被降级，不能跳过启动/验收检查')
    return requirement


def identity(directory, operation):
    path = dashboard_folder(directory, operation)
    requirement = load(path / 'requirement.json', Path(directory).resolve())
    if requirement.get('version') != VERSION or requirement.get('operation_id') != operation:
        raise ValueError('实验看板身份不匹配')
    return path, requirement


def publish_plan(directory, operation, design):
    path, requirement = identity(directory, operation)
    validate_plan(design)
    validate_required_observation(design, requirement, published=False)
    result = {**design, **requirement, 'updated_at': stamp(time.time())}
    # A dispatched job's denominator must not shrink through later redesigns.
    if (path / 'plan.json').exists():
        previous = load(path / 'plan.json', Path(directory).resolve())
        if previous['steps'] != result['steps'] or previous.get('observation') != result.get('observation'):
            raise ValueError('已登记工作项与分母不可覆盖；新增实验须由后续operation登记')
    write(path / 'plan.json', result)
    return result


def validate_status(directory, plan, data):
    if not isinstance(data, dict):
        raise ValueError('看板状态须为对象')
    text(data.get('summary'), 'summary'); text(data.get('next_action'), 'next_action')
    if not isinstance(data.get('blocker', ''), str):
        raise ValueError('blocker须为文本')
    indexed = {step['id']: step for step in plan['steps']}
    if data.get('current_step') is not None and data['current_step'] not in indexed:
        raise ValueError('当前步骤未登记')
    rows = data.get('steps')
    if not isinstance(rows, list) or len(rows) > len(indexed):
        raise ValueError('无效工作项更新')
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('工作项状态须为对象')
        key = row.get('id')
        if key not in indexed or key in seen or row.get('status') not in STATES:
            raise ValueError('工作项身份或状态不匹配')
        seen.add(key); text(row.get('detail'), 'detail')
        if plan.get('visibility_version') == execution_visibility.VERSION and row['status'] in ('unknown','blocked','failed'):
            checks = row.get('checks')
            if not isinstance(checks, list) or not 1 <= len(checks) <= 30:
                raise ValueError('异常状态须明确checks：缺什么、证据、系统动作及用户是否需决定')
            for check in checks:
                if not isinstance(check, dict):raise ValueError('核对项须为对象')
                for name in ('what','evidence','system_action','user_action'):text(check.get(name), 'checks.'+name)
                if type(check.get('user_required')) is not bool:raise ValueError('核对项须明确user_required')
        values = [row.get(k) for k in ('completed', 'failed')]
        if any(v is not None for v in values):
            if any(type(v) is not int or v < 0 for v in values):
                raise ValueError('完成与失败计数须同时为非负整数')
            total = indexed[key].get('total')
            if total is not None and sum(values) > total:
                raise ValueError('实测计数超过登记分母')
            source = row.get('source') or {}
            if not isinstance(source, dict):
                raise ValueError('计数来源须为对象')
            root = Path(directory).resolve()
            evidence = root / source['path']
            observed = load(evidence, root)  # Includes containment, symlink and size checks.
            if hashlib.sha256(evidence.read_bytes()).hexdigest() != source.get('sha256'):
                raise ValueError('进度计数证据哈希不匹配')
            for key, number in zip(('completed', 'failed'), values):
                actual = observed
                fields = text(source.get(key + '_field', key), '计数字段路径')
                for field in fields.split('.'):
                    actual = actual[field]
                if type(actual) is not int or actual != number:
                    raise ValueError('进度计数与证据字段不匹配')
    return data


def publish_status(directory, operation, data):
    path, requirement = identity(directory, operation)
    plan = validate_plan(load(path / 'plan.json', Path(directory).resolve()))
    validate_status(directory, plan, data)
    destination = path / 'status.json'
    previous = load(destination, Path(directory).resolve()) if destination.exists() else {}
    merged = {row['id']: row for row in previous.get('steps', [])}
    for row in data['steps']:
        old = merged.get(row['id'], {})
        for key in ('completed', 'failed'):
            if key in row and key in old and row[key] < old[key]:
                raise ValueError('同一工作项的累计计数不能回退或删除失败')
    merged.update({row['id']: row for row in data['steps']})
    result = {**data, **requirement, 'steps': list(merged.values()), 'updated_at': stamp(time.time())}
    write(path / ('event-%s-%s.json' % (time.time_ns(), uuid.uuid4().hex)), result)
    write(destination, result)
    return result


def find_campaign(root):
    for candidate in [Path(root).resolve(), *Path(root).resolve().parents]:
        if (candidate / 'state.sqlite3').is_file():
            return candidate
    return None


def job_requirement(root, kind):
    """Enforce only new contracted operations; in-flight legacy work is untouched."""
    directory = find_campaign(root)
    if directory is None or kind == 'compile':
        return None
    db = sqlite3.connect((directory / 'state.sqlite3').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        state = dict(db.execute('SELECT * FROM campaign').fetchone())
        state['config'] = json.loads(state['config'])
        import git_boundary
        git_boundary.validate_state(state, directory)
        task = db.execute("SELECT * FROM tasks WHERE status='RUNNING' AND operation_id IS NOT NULL ORDER BY rowid DESC LIMIT 1").fetchone()
        if not task:
            return None
        path = dashboard_folder(directory, task['operation_id'])
        requirement = required_contract(directory, task['operation_id'])
        if requirement is None:
            return None
        plan = validate_plan(load(path / 'plan.json', directory))
        validate_required_observation(plan, requirement)
        if plan.get('task_id') != task['id'] or plan.get('operation_id') != task['operation_id']:
            raise ValueError('实验作业缺少当前operation的看板设计')
        status = load(path / 'status.json', directory)
        validate_status(directory, plan, status)
        if plan.get('visibility_version') == execution_visibility.VERSION:
            age = time.time()-dt.datetime.fromisoformat(status['updated_at']).timestamp()
            if not -5 <= age <= 120:
                raise ValueError('新作业启动前须更新具体工作状态；不能复用过期说明')
        if (status.get('operation_id') != task['operation_id'] or status.get('task_id') != task['id']
                or not any(row['id'] == status.get('current_step') and row['status'] == 'running' for row in status['steps'])):
            raise ValueError('实验启动前须说明当前正在执行的具体工作项')
        return {'operation_id': task['operation_id'], 'task_id': task['id'],
                'plan_sha256': hashlib.sha256((path / 'plan.json').read_bytes()).hexdigest(),
                'visibility_version': plan.get('visibility_version')}
    finally:
        db.close()


def verify(store, task):
    operation = task.get('operation_id')
    if not operation or task['phase'] not in PHASES:
        return None
    path = dashboard_folder(store.directory, operation)
    requirement = required_contract(store.directory, operation)
    if requirement is None:
        return None  # Never retroactively reject a legacy scientific result.
    plan = validate_plan(load(path / 'plan.json', store.directory.resolve()))
    validate_required_observation(plan, requirement)
    data = load(path / 'status.json', store.directory.resolve())
    if any(value.get('operation_id') != operation or value.get('task_id') != task['id'] for value in (plan, data)):
        raise ValueError('阶段看板不属于当前任务')
    validate_status(store.directory, plan, data)
    if set(row['id'] for row in data['steps']) != set(row['id'] for row in plan['steps']):
        raise ValueError('阶段结束前须说明所有工作项状态与剩余工作')
    return {'version': VERSION, 'plan': str(path / 'plan.json'), 'status': str(path / 'status.json'),
            'scientific_admission_inferred': False}


def sampled_dashboard(root, state, task, since, now):
    """Adapt receipt-bound lane snapshots already produced by legacy launchers.

    Every displayed counter must match the successful collector's exact stdout;
    the denominator must match this batch's configuration, never an older run.
    This observes existing local files and makes no remote request.
    """
    candidates = []
    for i, path in enumerate((root / 'artifacts').glob('*/*/observations/*.json')):
        if i >= 2048:
            break
        try:
            if since is None or path.stat().st_mtime >= since:
                candidates.append((path.stat().st_mtime, path))
        except OSError:
            continue
    for _, path in sorted(candidates, reverse=True)[:128]:
        try:
            envelope = load(path, root)
            snapshot = envelope['snapshot']
            config = load(path.parent.parent / 'configuration.json', root)
            guard = snapshot['guard']
            if (config.get('topic') != state['topic'] or guard.get('topic') != state['topic']
                    or not config.get('phase') or config['phase'] != snapshot.get('phase')
                    or guard.get('phase') != snapshot['phase'] or snapshot.get('execution_exists') is not True):
                continue
            reference = envelope['receipt']
            receipt_path = root / reference['path']
            receipt = load(receipt_path, root)
            if (hashlib.sha256(receipt_path.read_bytes()).hexdigest() != reference['sha256']
                    or receipt.get('status') != 'succeeded' or receipt.get('exit_code') != 0
                    or receipt.get('simulated') is not False or receipt.get('target') != 'research-server'):
                continue
            log_path = root / receipt['log_path']
            logged = load(log_path, root)
            if hashlib.sha256(log_path.read_bytes()).hexdigest() != receipt['log_sha256'] or logged != snapshot:
                continue
            observed = snapshot['observed_at']
            if (type(observed) not in (int, float) or not 0 <= now - observed < 86400
                    or (since is not None and observed < since)):
                continue
            total = config['expected_episodes']
            if type(total) is not int or total <= 0 or guard.get('expected_episodes') != total:
                continue
            steps = []
            for key, lane in snapshot['lanes'].items():
                status = lane['status']
                done, expected, starts = lane['terminals'], status['expected'], lane['starts']
                if (any(type(n) is not int for n in (done, expected, starts))
                        or not 0 <= done <= starts <= expected or status.get('completed') != done
                        or status.get('topic') != state['topic'] or expected <= 0):
                    raise ValueError('执行分路计数不一致')
                last = status.get('last') or {}
                detail = '最近返回：' + str(last.get('episode_id', '未观测'))
                if last.get('reason'):
                    detail += '；结束原因：' + str(last['reason'])
                steps.append(dict(id=str(key), label='执行分路 ' + str(key), unit='回合', total=expected,
                    terminal=done, status='completed' if done == expected else ('running' if status.get('status') == 'running' and now-observed <= 90 else 'unknown'),
                    detail=detail, target_basis='本轮执行配置与服务器采样分母一致',
                    source={'path': str(path.relative_to(root))}))
            if not steps or sum(step['total'] for step in steps) != total:
                continue
            done = sum(step['terminal'] for step in steps)
            return dict(title=(task or {}).get('title', '本轮实验采样进度'), objective='本次运行的远端只读采样，计数已核对采集回执与日志。',
                mode='sampled' if now-observed <= 90 else 'stale',
                summary='本轮已记录终态 %s / %s 回合（%.1f%%，包含所有结束结果）。' % (done, total, 100*done/total),
                next_action=('所有计划回合已有终态，接下来收集原日志、核对逐项结果与回执并独立复验；不要重新提交已结束身份。' if done == total else '按本轮协议继续剩余回合；执行结束后独立复验完整性与结果。'), blocker='',
                steps=steps, jobs=[], timeline=[], updated_at=stamp(observed), warnings=[],
                scientific_admission_inferred=False)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            continue
    return None


def observe(store, state, original, now=None):
    if original is None:
        original = {'topic': state['topic'], 'mode': 'unavailable', 'source_at': None,
                    'summary': '尚无可读取的实验计数，不推测完成比例。',
                    'warnings': [], 'metrics': [], 'counts': None}
    now = time.time() if now is None else now
    root = store.directory.resolve()
    current = state.get('progress', {}).get('current_task') or {}
    task = next((t for t in store.tasks() if t['id'] == current.get('id')), None)
    # Keep the latest designed dashboard visible after its operation ends.
    if not task or task.get('phase') not in PHASES:
        task = next((t for t in reversed(store.tasks()) if t.get('phase') in PHASES and t.get('operation_id')), None)
    dashboard = {'title': (task or {}).get('title', '实验工作进度'), 'objective': '',
                 'mode': 'awaiting_design', 'summary': '执行智能体尚未登记本轮具体工作项。',
                 'next_action': '本轮执行时应主动设计看板并接入真实进度。', 'blocker': '',
                 'steps': [], 'jobs': [], 'timeline': [], 'updated_at': None, 'warnings': [],
                 'scientific_admission_inferred': False}
    if task and task.get('operation_id'):
        path = dashboard_folder(root, task['operation_id'])
        try:
            plan = validate_plan(load(path / 'plan.json', root))
            validate_required_observation(plan, required_contract(root, task['operation_id']) or {})
            if plan.get('task_id') != task['id'] or plan.get('operation_id') != task['operation_id']:
                raise ValueError('看板不属于当前任务')
            dashboard.update(title=plan['title'], objective=plan['objective'], mode='planned', steps=plan['steps'],
                             observation=plan.get('observation'),
                             operation_id=task['operation_id'], task_id=task['id'])
            dashboard['summary'] = '工作项已登记，等待首次执行更新。'
            if (path / 'status.json').exists():
                data = load(path / 'status.json', root)
                if data.get('operation_id') != task['operation_id'] or data.get('task_id') != task['id']:
                    raise ValueError('状态不属于当前任务')
                validate_status(root, plan, data)
                age = now - dt.datetime.fromisoformat(data['updated_at']).timestamp()
                if age < -5:
                    raise ValueError('进度时间位于未来')
                dashboard.update({k: data.get(k, '') for k in ('summary', 'next_action', 'blocker', 'updated_at', 'current_step')})
                dashboard['mode'] = 'stale' if age > 30 else 'live'
                indexed = {row['id']: row for row in data['steps']}
                dashboard['steps'] = [{**step, **indexed.get(step['id'], {'status': 'pending'})} for step in plan['steps']]
            for event_path in sorted(path.glob('event-*.json'), reverse=True)[:30]:
                event = load(event_path, root)
                if event.get('operation_id') == task['operation_id'] and event.get('task_id') == task['id']:
                    dashboard['timeline'].append({k: event.get(k, '') for k in ('updated_at', 'summary', 'blocker', 'next_action')})
        except FileNotFoundError:
            pass
        except (OSError, ValueError, KeyError, TypeError):
            dashboard.update(mode='invalid', steps=[])
            dashboard['warnings'].append('本轮看板未通过身份或证据检查，未显示其计数。')
    # Also observe existing jobs; no SSH, log-content disclosure or resubmission.
    started = (state.get('progress', {}).get('activity') or {}).get('started_at')
    since = dt.datetime.fromisoformat(started).timestamp() if started else None
    if dashboard['mode'] == 'awaiting_design':
        sampled = sampled_dashboard(root, state, task, since, now)
        if sampled:
            dashboard = sampled
    paths = []
    for i, path in enumerate((root / 'artifacts').rglob('receipt.json')):
        if i >= 2048:
            break
        try:
            if since is None or path.stat().st_mtime >= since:
                paths.append((path.stat().st_mtime, path))
        except OSError:
            continue
    for modified, path in sorted(paths, reverse=True)[:12]:
        try:
            receipt = load(path, root)
            if receipt.get('simulated') is not False or receipt.get('experiment_kind') not in ('acceptance', 'pilot', 'comparison'):
                continue
            if since is not None and dt.datetime.fromisoformat(receipt['started_at']).timestamp() < since - 1:
                continue
            if task and receipt.get('dashboard') and receipt['dashboard'].get('operation_id') != task.get('operation_id'):
                continue
            observed_at = receipt.get('observed_at', receipt.get('finished_at', stamp(modified)))
            age = now - dt.datetime.fromisoformat(observed_at).timestamp()
            status = receipt['status']
            if status == 'running' and age > 30:
                status = 'unknown'
            dashboard['jobs'].append(dict(status=status, kind=receipt['experiment_kind'],
                target=receipt.get('target'), started_at=receipt['started_at'], observed_at=observed_at,
                elapsed_seconds=receipt.get('wall_seconds'), log_bytes=receipt.get('log_bytes'),
                exit_code=receipt.get('exit_code'), source=str(path.relative_to(root))))
        except (OSError, ValueError, TypeError, KeyError):
            continue
    result = {**original, 'dashboard': dashboard}
    if dashboard['mode'] in ('sampled', 'live', 'stale'):
        result.update(original_summary=original['summary'], summary=dashboard['summary'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'update'])
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--operation', required=True)
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    # Use the campaign's registration and Git boundary even for direct writes.
    import ars
    import git_boundary
    store = ars.Store(args.directory)
    try:
        git_boundary.validate_state(store.state(), store.directory)
        value = load(args.input, store.directory.resolve())
        action = publish_plan if args.action == 'plan' else publish_status
        action(store.directory, args.operation, value)
        print(json.dumps({'status': 'published', 'action': args.action, 'operation_id': args.operation}))
    finally:
        store.close()


if __name__ == '__main__':
    main()
