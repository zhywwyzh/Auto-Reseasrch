"""Workflow-independent, durable continuation. Never grants scientific acceptance.

The same saved executor handles repairs; this module neither calls a model nor
submits research jobs. All decisions run under the campaign worker/recovery locks.
"""
import execution_limits
import hashlib
import json
from pathlib import Path

VERSION = 'autonomous-progress-v1'
POLICY = {'enabled': True, 'version': VERSION, 'max_followups_per_stage': 8,
          'max_diagnostics_per_stage': 2}
ACTIVE = {'READY', 'RUNNING', 'WAITING_EXTERNAL'}
EVENT = 'autonomy.followup_queued'


def enabled(state):
    policy = state['config'].get('autonomy', {})
    return policy.get('enabled') is True and policy.get('version') == VERSION


def allowed(store):
    state = store.state()
    return (enabled(state) and state['status'] in ACTIVE
            and not any(t['status'] in ('PENDING', 'RUNNING', 'UNKNOWN') for t in store.tasks())
            and not any(state['config'].get(limit, 0) > 0 and state[used] >= state['config'][limit]
                        for used, limit in [('calls', 'max_calls'), ('tokens', 'max_tokens'),
                                            ('active_seconds', 'max_seconds')]))


def history(store):
    return [json.loads(row[0]) for row in store.db.execute(
        'SELECT payload FROM events WHERE type=? ORDER BY seq', (EVENT,))]


def verified(store, task):
    if task['status'] != 'COMPLETED':
        return False
    result = json.loads(task.get('result') or '{}')
    verification = json.loads(task.get('verification') or '{}')
    if (result.get('status') != 'done' or result.get('verdict') != 'revise'
            or verification.get('gate') != 'structure_and_source_correspondence'):
        return False
    # A previously verified file can change while waiting. Never schedule from
    # such a stale result, or treat a URL as a local file.
    import paper_workflow
    for source in verification.get('sources', []):
        if source.get('status') != 'source_match_only':
            continue
        try:
            path = paper_workflow._artifact_path(source['source'], store.state())
            if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
                return False
        except (OSError, KeyError, ValueError):
            return False
    return True


def maybe_queue(store):
    """Continue one verified plan step, even when an older blocker remains open.

    Steps are serial, idempotent across restarts, same-stage and bounded. Failed,
    blocked or unknown steps never release later steps. Accept still goes through
    the original stage verifier; old blockers and budgets are never rewritten.
    """
    if not allowed(store):
        return False
    import paper_workflow
    if paper_workflow.ucs.enabled(store.state()):
        # This contract already owns versioned dependency/revision budgets and
        # measured research continuation. Do not create a second allowance.
        return False
    tasks = [task for task in store.tasks() if task['phase'] != 'code_repair']
    rows = history(store)
    # Only the latest task in a phase can propose more work. An earlier revise
    # must not resurrect after a later accepted/failed attempt.
    latest = {task['phase']: task for task in tasks}
    for task in reversed(list(latest.values())):
        if not verified(store, task):
            continue
        phase = task['phase']
        maximum = min(24, max(0, int(store.state()['config']['autonomy']['max_followups_per_stage'])))
        if not execution_limits.unrestricted(store.state()) and sum(row['phase'] == phase for row in rows) >= maximum:
            return False
        owner, index = task, 0
        previous = next((r for r in rows if r['task_id'] == task['id'] and not r.get('diagnostic')), None)
        if previous:
            plan = next(t for t in tasks if t['id'] == previous['plan_task'])
            steps = json.loads(plan['result']).get('next_tasks', [])[:3]
            if previous['step_index'] + 1 < len(steps):
                owner, index = plan, previous['step_index'] + 1
        steps = json.loads(owner.get('result') or '{}').get('next_tasks', [])[:3]
        if not steps or any(r.get('plan_task') == owner['id'] and r.get('step_index') == index
                            and not r.get('diagnostic') for r in rows):
            continue
        step = steps[index]
        if not all(isinstance(step.get(k), str) and step[k].strip() for k in ('title', 'instruction')):
            continue
        # Existing workflow schedulers may already have dispatched the step.
        if any(t.get('parent') == owner['id'] and t['title'] == step['title']
               and t['instruction'] == step['instruction'] for t in tasks):
            continue
        task_id = store.add_task(step['title'], step['instruction'], phase, owner['id'])
        if not task_id:
            continue
        store.event(EVENT, {'task_id': task_id, 'phase': phase, 'plan_task': owner['id'],
            'step_index': index, 'diagnostic': False, 'acceptance_gate_unchanged': True})
        store.status('READY', '自动接续已核验任务的后续步骤：' + step['title'] + '；原阻点与验收保持')
        return True
    return False


def maybe_diagnose(store):
    """One bounded same-executor diagnosis of an otherwise silent scheduler stall.

    Known external dependencies and exhausted repair incidents keep their wait
    semantics. This is for an unclassified stall, not a way around a known cap.
    """
    if not allowed(store):
        return False
    import runtime_policy
    import self_repair
    tasks = [task for task in store.tasks() if task['phase'] != 'code_repair']
    if not tasks:
        return False
    choices = list(store.db.execute("SELECT payload FROM events WHERE type='self_repair.decision' ORDER BY seq DESC LIMIT 1"))
    choice = json.loads(choices[0][0]) if choices else {}
    continuous = execution_limits.unrestricted(store.state())
    if not continuous and choice.get('action') in ('external_required', 'budget_stop', 'repair_exhausted', 'incident_exhausted', 'reconcile'):
        return False
    task = tasks[-1]
    if task['status'] != 'COMPLETED' or not verified(store, task):
        return False
    reason = store.state()['reason']
    if not continuous and runtime_policy.classify(reason) in ('authorization', 'external_evidence', 'uncertain_execution', 'provider_quota'):
        return False
    rows = history(store)
    policy = store.state()['config']['autonomy']
    if not execution_limits.unrestricted(store.state()) and (sum(r['phase'] == task['phase'] for r in rows) >= policy['max_followups_per_stage']
            or sum(r['phase'] == task['phase'] and r.get('diagnostic') for r in rows) >= policy['max_diagnostics_per_stage']):
        return False
    instruction = ('自动停滞诊断，使用当前任务的原执行器和原权限。先读全部原始错误、回执、'
        '最近已核验结果及其next_tasks，核对已登记授权与预算、执行代码版本及依赖。'
        '指出不能接续的具体根因，完成原权限内的工程修复和原门槛复验，提出可执行的同阶段后续步骤；'
        '已有批准不得再次索取，不把历史阻点当当前授权。诊断本身不得提交新训练/求解/仿真，'
        '不得改科学定义、验收器、原始记录或预算，不重投UNKNOWN。'
        '有真实外部缺项则blocked并准确列出；否则done+revise并给具体next_tasks。'
        '不得把诊断结束当作阶段通过。原阻点保留。\n当前原因：' + reason)
    title = '自动诊断任务停滞并形成接续步骤'
    if continuous:
        title = '依据最新授权自动推进未完成研究'
        instruction = ('继续原研究目标，不能以历史子任务的局部只读限制、旧预算等待或next_tasks为空结束。'
            '先读取原始目标、最新有效授权、最新完成证据和真实报错；判断尚未完成的科学义务，'
            '选定一个有必要性依据、可执行且能产生新证据的下一步并实际推进。'
            '已有独立评价与核查结果应复用，不重复做同一审计；代码错误须修代码并复验。'
            '确需新计算时先冻结前瞻协议、清单和目标，用已分配设备及原CPU/内存分区执行并留回执；'
            '不能把已读TEST当新的独立确认，不能重投UNKNOWN或覆盖原始结果。'
            '原历史实验及未知端点保留；若旧计划的某项首次观测不可恢复，应提出并核验新的前瞻研究方案，'
            '明确估计对象、独立数据、必要对照和旧方案缺失，不得修改旧事实、科学目标或放宽验收来制造完成。'
            '本接续步骤本身不是科学阶段验收；完成后done+revise给出具体可执行next_tasks，'
            '不新增模型/智能体，不提交/推送/公开任务材料。\n当前目标：' + store.state()['goal'] +
            '\n最新完成：' + json.loads(task['result']).get('summary', '') + '\n当前原因：' + reason)
    task_id = store.add_task(title, instruction, task['phase'], task['id'])
    if not task_id:
        return False
    store.event(EVENT, dict(task_id=task_id, phase=task['phase'], plan_task=task['id'],
        step_index=0, diagnostic=True, research_continuation=continuous, acceptance_gate_unchanged=True))
    store.status('READY', '自动诊断调度停滞；原权限、预算和验收保持')
    return True


def context(store, task):
    if not enabled(store.state()):
        return None
    rows = history(store)
    return {'version': VERSION, 'no_user_presence_required': True,
            'original_write_scope_and_budgets_retained': True,
            'instruction': '自行排障、复验并继续。后续步骤由控制器串行接续，无需用户打开页面或聊天。'
              '先核对当前已批准授权、真实回执与最新结果，不重复索取已有决定。'
              '不扩大预算、权限、科学定义或降低验收，不重投UNKNOWN；确有外部缺项时具体登记。',
            'requires_followup': any(r['task_id'] == task['id'] and r.get('research_continuation') for r in rows),
            'diagnostic': any(r['task_id'] == task['id'] and r.get('diagnostic') for r in rows)}


def enroll(store):
    """Enable universal recovery only; preserve task state, limits and write scope."""
    import self_repair
    import code_repair
    cfg = store.state()['config']
    if cfg.get('autonomy', {}).get('enabled') is False:
        return False
    if enabled(store.state()) and 'code_repair' in cfg:
        return False
    cfg['autonomy'] = dict(POLICY)
    cfg.setdefault('self_repair', dict(self_repair.POLICY))
    cfg.setdefault('code_repair', dict(code_repair.POLICY))
    store.db.execute('UPDATE campaign SET config=?', (json.dumps(cfg, ensure_ascii=False),))
    store.event('autonomy.enrolled', {'version': VERSION, 'budgets_unchanged': True,
                                    'tasks_unchanged': True, 'write_scope_unchanged': True})
    return True
