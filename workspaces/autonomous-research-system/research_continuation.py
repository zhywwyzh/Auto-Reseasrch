"""Continue an incomplete stage only after new verified work within pinned caps.

An implementation/scientific revision allowance is not a limit on productive
tranches. No prose-only progress, reused receipt, UNKNOWN job or enlarged cap
qualifies. This module queues the same authorized executor, not research jobs.
"""
import hashlib
import json
import math
from pathlib import Path
import runtime_policy
VERSION = 'evidenced-stage-continuation-v1'
EVENT = 'workflow.progress_continuation_queued'
INSTRUCTION = '同阶段有真实新执行证据且原预算有余额时可继续，不把普通研究分段当成候选机制重新修订。若本阶段仍未通过，返回done+revise及具体同阶段next_tasks，并在evidence逐字引用中绑定最新累计budget-accounting JSON及本次新成功服务器计算receipt。累计成本须含失败、修复和未知成本预留；实际已对账的旧回执列closed_receipts，未闭合的未知作业不得重新提交。总交互、更新、CPU、墙钟、存储、提交次数及单作业上界沿用原冻结预算，不因接续而增加或重置。只有完整阶段真正通过才accept，研究不足不能改成已完成；无新进展、真实资源不足或外部依赖须如实记录。'
ROLLING_VERSION = 'unlimited-total-bounded-batches-v1'
ROLLING_INSTRUCTION = '累计资源授权只取当前任务已登记并绑定的本地授权。每批次独立冻结工作量与验收，保留全部失败、成本、未知活动和历史证据。没有有效授权不得扩大累计预算或继承其他任务资源。'

def rolling_authority(state):
    policy = state['config'].get('aggregate_research_budget', {})
    if policy.get('mode') != ROLLING_VERSION:
        return None
    import paper_workflow
    import research_quality
    read = research_quality.Reader(lambda raw: paper_workflow._artifact_path(raw, state))
    authority = read.bound(policy['authority_source'], True)
    if authority.get('topic') != state['topic'] or authority.get('mode') != ROLLING_VERSION or authority.get('authorized') is not True:
        raise ValueError('无累计上限授权与当前课题不匹配')
    return policy

def instruction(state):
    import execution_limits
    if execution_limits.unrestricted(state):
        return execution_limits.INSTRUCTION
    return ROLLING_INSTRUCTION if rolling_authority(state) else INSTRUCTION

def enabled(state):
    p = state['config'].get('research_continuation', {})
    return p.get('version') == VERSION and p.get('enabled') is True and (state['config'].get('workflow') == 'paper')

def submission_limit(store):
    """Read a hash-bound exhausted limit; model prose cannot invent or waive it."""
    state = store.state()
    if not enabled(state):
        return None
    if rolling_authority(state):
        return None
    policy = state['config']['research_continuation']
    task = next((t for t in reversed(store.tasks()) if t['phase'] == policy['phase']), None)
    if not task or task['status'] != 'COMPLETED':
        return None
    result = json.loads(task.get('result') or '{}')
    if result.get('status') != 'done' or result.get('verdict') != 'revise':
        return None
    import paper_workflow
    import research_quality
    read = research_quality.Reader(lambda raw: paper_workflow._artifact_path(raw, state))
    cap = read.bound(policy['cap_source'], True)
    maximum = cap.get('submission_cap')
    if type(maximum) is not int or maximum < 0:
        return None
    (seen, budgets) = (set(), [])
    for item in json.loads(task.get('verification') or '{}').get('sources', []):
        key = (item['source'], item['sha256'])
        if key in seen:
            continue
        seen.add(key)
        ref = dict(path=key[0], sha256=key[1])
        try:
            value = json.loads(read.bound(ref))
        except (json.JSONDecodeError, UnicodeError):
            continue
        if isinstance(value, dict) and all((k in value for k in policy['accounting_to_bound'])):
            budgets.append((ref, value))
    if len(budgets) != 1:
        return None
    (ref, paid) = budgets[0]
    used = paid.get('frozen_attempt_slots_used')
    if type(used) is not int or used < maximum:
        return None
    if paid.get('submission_cap') != maximum or paid.get('cap_source') != policy['cap_source']:
        raise ValueError('提交槽账本与冻结上限来源不一致')
    registry = paid.get('submission_registry', [])
    if len({r['path'] for r in registry}) != used:
        raise ValueError('提交槽计数与唯一冻结登记不一致')
    for entry in registry:
        read.bound(entry)
    return dict(task_id=task['id'], phase=task['phase'], limit='submission_cap', used=used, maximum=maximum, remaining=max(0, maximum - used), cap_source=policy['cap_source'], budget_evidence=ref, budget_extension_authorized=False, reason=f'研究作业提交槽已用 {used}/{maximum}；需先形成资源补充方案，当前不自动追加作业')

def maybe_queue(store, latest):
    (state, tasks) = (store.state(), store.tasks())
    if not enabled(state) or state['status'] not in ('READY', 'RUNNING', 'WAITING_EXTERNAL'):
        return False
    policy = state['config']['research_continuation']
    rolling = rolling_authority(state)
    if latest['phase'] != policy['phase'] or latest['status'] != 'COMPLETED':
        return False
    if any((t['status'] in ('PENDING', 'RUNNING', 'UNKNOWN') for t in tasks)):
        return False
    if any((state['config'].get(limit, 0) > 0 and state[used] >= state['config'][limit] for (used, limit) in [('calls', 'max_calls'), ('tokens', 'max_tokens'), ('active_seconds', 'max_seconds')])):
        return False
    if any((t.get('parent') == latest['id'] for t in tasks)):
        return False
    if submission_limit(store):
        return False
    result = json.loads(latest.get('result') or '{}')
    verification = json.loads(latest.get('verification') or '{}')
    if result.get('status') != 'done' or result.get('verdict') != 'revise' or (not result.get('next_tasks')) or (not verification.get('sources')):
        return False
    if runtime_policy.classify(verification.get('error') or result.get('summary', '')) in ('authorization', 'external_evidence', 'uncertain_execution', 'provider_quota'):
        return False
    import ars
    import paper_workflow
    import research_quality
    resolve = lambda raw: paper_workflow._artifact_path(raw, state)
    read = research_quality.Reader(resolve)
    cap = read.bound(policy['cap_source'], True)
    keys = policy['accounting_to_bound']
    sources = []
    seen_sources = set()
    for item in verification['sources']:
        source_key = (item['source'], item['sha256'])
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        ref = {'path': item['source'], 'sha256': item['sha256']}
        body = read.bound(ref)
        try:
            value = json.loads(body)
        except (ValueError, UnicodeError):
            continue
        if isinstance(value, dict):
            sources.append((ref, value))
    budgets = [(ref, value) for (ref, value) in sources if all((key in value for key in keys))]
    if len(budgets) != 1:
        return False
    (budget_ref, paid) = budgets[0]
    for (key, bound) in keys.items():
        (value, maximum) = (paid[key], cap['bounds'][bound])
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or (type(maximum) not in (int, float)) or (not math.isfinite(maximum)) or (not rolling and (not value < maximum)):
            return False
    closed = set(paid.get('closed_receipts', []))
    if any((row.get('receipt') not in closed for row in paid.get('unknown_reservations', []))):
        return False
    history = [json.loads(r[0]) for r in store.db.execute('SELECT payload FROM events WHERE type=? ORDER BY seq', (EVENT,))]
    previous = next((e['consumed'] for e in reversed(history) if e['phase'] == latest['phase']), None)
    progress_keys = policy['progress_keys']
    if previous and (any((paid[k] < previous[k] for k in keys)) or not any((paid[k] > previous[k] for k in progress_keys))):
        return False
    used = {r['sha256'] for event in history for r in event.get('new_receipts', [])}
    operation = store.operation(latest['operation_id'])
    started = research_quality.timestamp(operation['created_at'])
    receipts = []
    for (ref, value) in sources:
        if ref['sha256'] in used or value.get('status') != 'succeeded' or value.get('exit_code') != 0 or (value.get('simulated') is not False) or (value.get('target') != policy['target']) or (value.get('experiment_kind') != policy['experiment_kind']) or (not value.get('finished_at')):
            continue
        if research_quality.timestamp(value['started_at']) < started:
            continue
        argv = value.get('argv', [])
        if not argv or Path(str(argv[0])).name in {'scp', 'rsync', 'cat', 'ls', 'stat', 'sha256sum'}:
            continue
        read.bound({'path': value['log_path'], 'sha256': value['log_sha256']})
        receipts.append(ref)
    if not receipts:
        return False
    follow = result['next_tasks'][0]
    follow_instruction = '依据最新无累计上限授权继续同阶段；先核对最新产物、修改旧累计限制的执行路径并制定后续实验方案，再实际执行充分性、独立重复与创新检验。历史next_task中要求因内部预算耗尽再次申请的句子已被本次用户授权替代。\n' + follow['instruction'] + '\n最新授权优先：\n' + instruction(state) if rolling else follow['instruction'] + '\n' + INSTRUCTION
    task_id = store.add_task(follow['title'], follow_instruction, latest['phase'], latest['id'], dedup=False)
    store.event(EVENT, {'task_id': task_id, 'parent_task': latest['id'], 'phase': latest['phase'], 'cap_source': policy['cap_source'], 'budget_evidence': budget_ref, 'consumed': {k: paid[k] for k in keys}, 'remaining': {k: None if rolling else cap['bounds'][bound] - paid[k] for (k, bound) in keys.items()}, 'new_receipts': receipts, 'original_max_rounds': state['config']['max_rounds'], 'new_scientific_revision': False, 'budget_extension_authorized': bool(rolling), 'aggregate_budget_mode': ROLLING_VERSION if rolling else 'original_finite_cap', 'authority_source': rolling.get('authority_source') if rolling else None, 'scientific_gate_waived': False, 'new_research_job_submitted': False})
    store.status('READY' if state['status'] == 'WAITING_EXTERNAL' else 'RUNNING', '已有新执行证据，按用户累计不限额授权继续下一有限批次' if rolling else '已有新执行证据且原预算有余额，继续同一阶段；完整实验与论文门槛保持')
    return True

def resume(store):
    if not enabled(store.state()):
        return False
    phase = store.state()['config']['research_continuation']['phase']
    latest = next((t for t in reversed(store.tasks()) if t['phase'] == phase), None)
    return bool(latest and maybe_queue(store, latest))
import local_extensions as _local_extensions
_local_extensions.apply(globals())
