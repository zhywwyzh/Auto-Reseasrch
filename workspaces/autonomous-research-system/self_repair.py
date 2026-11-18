"""Bounded repair-first recovery; never relax evidence gates or repeat UNKNOWN work.

Only the existing campaign executor performs diagnosis in its saved write scope.
This module schedules recovery, supplies prior evidence, and derives an audit trail.
"""
import execution_limits
import json
import datetime as dt
import runtime_policy
import strategy_runtime
VERSION = 'repair-first-v2'
POLICY = {'version': VERSION, 'enabled': True, 'max_cycles_per_task': 8, 'max_cycles_per_incident': 2, 'backoff_seconds': 5, 'notification': 'final_report_unless_external_action_required'}
INSTRUCTION = '执行偏好：遇到技术问题优先自行解决，成功修复无需逐次向用户提问。先读取本次错误、已有回执/结果/日志和当前授权；不要重复索要用户已提供的信息。区分缺数据、数值失败、环境/网络、产物清单及来源核对问题，提出并执行针对性修复，复验通过后继续。例如空stderr是合法原始输出：保留其字节，用非空JSON登记路径、零字节大小和SHA256；不要填充日志或取消门槛。先复用已经成功且版本匹配的结果，不无故重新训练/求解；先查作业回执，UNKNOWN或远端状态不明时不得盲目重投。修复限当前课题和已有授权，保留所有成功/失败回执；不改评价器门槛、科学目标、实验数据或证据要求来制造通过。不要额外启动智能体、付费API或扩大预算/发布权限。仅确实缺必要外部材料、可用凭据、用户决策或授权时，写清已查依据、已试办法、具体缺失项，并继续不受影响的工作。在阶段及最终报告登记问题、原因、修复、复验、额外成本和未决项；不能将可修复工程问题当整轮终点。'

def enabled(state):
    saved = state['config'].get('self_repair', {})
    return state['config'].get('backend') in ('codex', 'mock') and saved.get('enabled', False) is True

def classify(error):
    return runtime_policy.classify(error)

def strategy_classify(store, error):
    """Recovery routing is fixed; strategy advice cannot invent a blocking cause.

    Unclassified FAILED work receives bounded diagnosis. Unclassified BLOCKED
    work retains its dependency scheduler and other independent branches.
    """
    return classify(error)

def delay_remaining(store, task_id):
    for row in store.db.execute("SELECT payload FROM events WHERE type IN ('self_repair.queued','task.failed') ORDER BY seq DESC"):
        event = json.loads(row[0])
        if event.get('task_id') == task_id:
            when = event.get('not_before')
            return max(0, (dt.datetime.fromisoformat(when) - dt.datetime.now(dt.timezone.utc)).total_seconds()) if when else 0
    return 0

def events(store):
    return [dict(r) for r in store.db.execute("SELECT seq,type,payload,created_at FROM events WHERE type IN ('task.failed','task.blocked','self_repair.queued') ORDER BY seq")]

def context(store, task):
    if not enabled(store.state()):
        return None
    prior = []
    for event in events(store):
        payload = json.loads(event['payload'])
        if payload.get('task_id') == task['id']:
            prior.append({'time': event['created_at'], 'event': event['type'], 'error': payload.get('error') or payload.get('summary', ''), 'cycle': payload.get('cycle')})
    operations = [dict(r) for r in store.db.execute('SELECT id,directory,state FROM operations WHERE task_id=? ORDER BY rowid', (task['id'],))]
    queued = next((json.loads(e['payload']) for e in reversed(events(store)) if e['type'] == 'self_repair.queued' and json.loads(e['payload']).get('task_id') == task['id']), {})
    diagnosis_only = queued.get('category') == 'unclassified'
    instruction = INSTRUCTION
    if store.state()['config'].get('workflow', 'readonly') != 'paper':
        instruction += ' 本运行保持只读：只能读取已有材料和生成本运行结果，不得修改研究源码、安装依赖、训练或提交实验。'
    if diagnosis_only:
        instruction += ' 本次为未分类阻点的有界只读诊断：只检查已有日志、回执、配置与权限，不提交研究作业、不重复求解、不修改预算或科学定义。定位后报告具体根因、证据及同阶段修复任务；确需外部决策时明确缺失项，不能只写“无法继续”。'
    return {'policy': store.state()['config']['self_repair'], 'instruction': instruction, 'diagnosis_only': diagnosis_only, 'previous_failures': prior[-8:], 'previous_operations': operations[-4:], 'acceptance_gate_unchanged': True, 'unknown_jobs_must_not_be_resubmitted': True}

def decision(store, task_id, action, reason, category=None):
    """Persist why the controller repairs, waits, or exhausts its allowance."""
    payload = {'task_id': task_id, 'action': action, 'reason': reason, 'category': category}
    previous = store.db.execute("SELECT payload FROM events WHERE type='self_repair.decision' AND json_extract(payload,'$.task_id') IS ? ORDER BY seq DESC LIMIT 1", (task_id,)).fetchone()
    if not previous or json.loads(previous[0]) != payload:
        store.event('self_repair.decision', payload)

def maybe_queue(store):
    """Inside the caller transaction. Recover an exhausted, known technical failure."""
    state = store.state()
    if not enabled(state) or state['status'] not in ('READY', 'RUNNING', 'WAITING_EXTERNAL'):
        return False
    tasks = store.tasks()
    if any((t['status'] in ('PENDING', 'RUNNING', 'UNKNOWN') for t in tasks)):
        for task in tasks:
            if task['status'] == 'UNKNOWN':
                decision(store, task['id'], 'reconcile', '执行状态待核对；禁止盲目重投', 'uncertain_execution')
        return False
    if any((state['config'].get(limit, 0) > 0 and state[used] >= state['config'][limit] for (used, limit) in [('calls', 'max_calls'), ('tokens', 'max_tokens'), ('active_seconds', 'max_seconds')])):
        decision(store, None, 'budget_stop', '模型调用或控制器预算达到上限，未扩大预算')
        return False
    import code_repair
    if state['config']['self_repair'].get('version') == VERSION and code_repair.maybe_queue(store):
        return True
    from paper_workflow import superseded_problems
    superseded = superseded_problems(tasks)
    history = events(store)
    for task in tasks:
        if task['phase'] == code_repair.PHASE:
            continue
        if task['id'] in superseded or task['status'] not in ('FAILED', 'BLOCKED'):
            continue
        verification = json.loads(task.get('verification') or '{}')
        result = json.loads(task.get('result') or '{}')
        error = verification.get('error') or result.get('summary', '')
        category = strategy_classify(store, error)
        if category in ('uncertain_execution', 'authorization', 'external_evidence', 'provider_quota'):
            decision(store, task['id'], 'reconcile' if category == 'uncertain_execution' else 'external_required', error, category)
            continue
        if task['status'] == 'BLOCKED' and category not in ('artifact_contract', 'provenance', 'environment', 'transport', 'implementation', 'unclassified'):
            decision(store, task['id'], 'external_required', error, category)
            continue
        cycles = [json.loads(e['payload']) for e in history if e['type'] == 'self_repair.queued' and json.loads(e['payload']).get('task_id') == task['id']]
        policy = state['config']['self_repair']
        modern = policy.get('version') == VERSION
        maximum = min(12 if modern else 3, max(0, int(policy.get('max_cycles_per_task', 2))))
        if not execution_limits.unrestricted(state) and len(cycles) >= maximum:
            decision(store, task['id'], 'repair_exhausted', '同任务有界修复次数耗尽；原始错误：' + error, category)
            continue
        incident = runtime_policy.incident(error)
        try:
            release = strategy_runtime.active_release()
            strategy_version = release['version'] if release else 'bundled-v2'
        except Exception:
            strategy_version = 'bundled-v2'
        condition_event = store.db.execute("SELECT seq FROM events WHERE type='self_repair.condition_changed' AND json_extract(payload,'$.task_id')=? ORDER BY seq DESC LIMIT 1", (task['id'],)).fetchone()
        condition_epoch = condition_event[0] if condition_event else 0
        matching = [c for c in cycles if c.get('incident', runtime_policy.incident(c.get('error', ''))) == incident and c.get('strategy_version', 'bundled-v2') == strategy_version and (c.get('condition_epoch', 0) == condition_epoch)]
        if not execution_limits.unrestricted(state) and modern and (len(matching) >= min(3, max(0, int(policy.get('max_cycles_per_incident', 2))))):
            decision(store, task['id'], 'incident_exhausted', '相同根因及条件下修复次数耗尽；原始错误：' + error, category)
            continue
        cycle = len(cycles) + 1
        delay = min(300, max(0, policy.get('backoff_seconds', 0)) * 2 ** min(len(matching), 10)) if modern else 0
        not_before = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=delay)).isoformat()
        store.event('self_repair.queued', {'task_id': task['id'], 'phase': task['phase'], 'cycle': cycle, 'category': category, 'error': error, 'incident': incident, 'incident_cycle': len(matching) + 1, 'not_before': not_before, 'strategy_version': strategy_version, 'condition_epoch': condition_epoch, 'previous_status': task['status'], 'previous_result': result, 'operation_id': task.get('operation_id'), 'acceptance_gate_unchanged': True})
        store.db.execute("UPDATE tasks SET status='PENDING' WHERE id=?", (task['id'],))
        decision(store, task['id'], 'diagnose' if category == 'unclassified' else 'repair', error, category)
        store.status('RUNNING', '正在自行诊断并修复：' + task['title'] + '；处理结果汇入最终报告')
        return True
    return False

def journal(store):
    """Derive outcomes from actual accepted task states, never from model claims."""
    raw_tasks = store.tasks()
    tasks = {t['id']: t for t in raw_tasks}
    from paper_workflow import superseded_problems
    superseded = superseded_problems(raw_tasks)
    from paper_workflow import recovering_problems
    recovering = recovering_problems(raw_tasks)
    entries = []
    history = events(store)
    for event in history:
        payload = json.loads(event['payload'])
        task_id = payload.get('task_id')
        if event['type'] == 'self_repair.queued':
            continue
        task = tasks.get(superseded.get(task_id, recovering.get(task_id, task_id)), {})
        verification = json.loads(task.get('verification') or '{}')
        result = json.loads(task.get('result') or '{}')
        verified_gate = bool(verification.get('stage_artifacts')) if store.state()['config'].get('workflow') == 'paper' else verification.get('gate') == 'structure_and_source_correspondence'
        resolved = task.get('status') == 'COMPLETED' and result.get('status') == 'done' and (result.get('verdict') == 'accept') and verified_gate
        error = payload.get('error') or payload.get('summary', '')
        entries.append({'event_seq': event['seq'], 'task_id': task_id, 'resolved_by_task': task.get('id') if resolved else None, 'phase': task.get('phase'), 'time': event['created_at'], 'error': error, 'category': classify(error), 'outcome': 'verified_recovered' if resolved else 'repairing' if task.get('status') in ('RUNNING', 'PENDING') else 'unresolved', 'extra_repair_cycles': sum((e['type'] == 'self_repair.queued' and json.loads(e['payload']).get('task_id') == task_id for e in history)), 'repair_summary': result.get('summary', '') if resolved else '', 'verification': verification if resolved else None})
    return entries

def progress(store):
    if not enabled(store.state()):
        return None
    rows = journal(store)
    from paper_workflow import recovering_problems
    successors = set(recovering_problems(store.tasks()).values())
    active = next((t for t in store.tasks() if t['status'] in ('RUNNING', 'PENDING') and (any((e['task_id'] == t['id'] for e in rows)) or t['id'] in successors)), None)
    last = store.db.execute("SELECT payload FROM events WHERE type='self_repair.decision' ORDER BY seq DESC LIMIT 1").fetchone()
    return {'enabled': True, 'notification': POLICY['notification'], 'last_decision': json.loads(last[0]) if last else None, 'recovering_task': active['id'] if active else None, 'issues': len(rows), 'recovered': sum((e['outcome'] == 'verified_recovered' for e in rows)), 'unresolved': sum((e['outcome'] == 'unresolved' for e in rows)), 'summary': '正在自行处理，原因、修复和复验将汇入最终报告。' if active else '问题处理记录将随最终报告交付。'}

def report_lines(store):
    if not enabled(store.state()):
        return []
    rows = journal(store)
    lines = ['## 自修复与未决问题', '', '策略：先读取已有证据并修复，复验通过后继续；保留全部失败与成本，不放宽验收。', '']
    if not rows:
        return lines + ['本轮尚无已记录的失败或阻塞。', '']
    labels = {'verified_recovered': '已通过原阶段复验', 'repairing': '自动处理中', 'unresolved': '未决，见具体缺失项'}
    last = store.db.execute("SELECT payload FROM events WHERE type='self_repair.decision' ORDER BY seq DESC LIMIT 1").fetchone()
    if last:
        choice = json.loads(last[0])
        names = {'repair': '自动修复', 'diagnose': '有界只读诊断', 'reconcile': '先核对执行状态', 'external_required': '确需外部条件', 'budget_stop': '预算停止', 'repair_exhausted': '任务修复次数耗尽', 'incident_exhausted': '相同根因修复次数耗尽', 'dependency_scheduler': '交由既有依赖调度器继续独立工作'}
        lines += ['控制器最新处置：' + names.get(choice['action'], choice['action']) + '。' + choice['reason'], '']
    for row in rows:
        lines += [f"- {row['phase']} · {row['category']} · {labels[row['outcome']]}：{row['error']}", f"  原始事件 #{row['event_seq']}；额外修复周期 {row['extra_repair_cycles']}；历史回执和用量保留。"]
        if row['repair_summary']:
            lines += ['  修复与复验：' + row['repair_summary']]
    lines += ['', '修复细节与复验依据见对应阶段报告和 operation 回执；工程恢复不等于研究结论成立。', '']
    return lines
import local_extensions as _local_extensions
_local_extensions.apply(globals())
