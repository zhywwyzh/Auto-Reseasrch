"""Generic artifact workflow; scientific contracts and validators are task-owned."""
import json
from pathlib import Path
import execution_limits
import research_quality
import manuscript_quality
import research_assurance
import revision_workflow
STAGES = {phase: (phase, '按本课题已冻结契约执行并保存真实产物') for phase in {'resolve', 'implement', 'validate', 'pilot', 'experiment', 'analyze', 'write', 'paper_review'} | revision_workflow.PHASES}

def enabled(config):
    return config.get('workflow', 'readonly') == 'paper'

def require_contract(config):
    if not revision_workflow.enabled(config or {}):
        raise ValueError('需要本课题私有阶段契约与固定验证器；没有默认科学验收')

def stages(topic, config=None):
    require_contract(config)
    return revision_workflow.stages(config)

def paper_root(topic, config=None):
    require_contract(config)
    return config['revision_workflow']['spec']['paper_root']

def required_roles(topic, phase, config=None):
    require_contract(config)
    return set(next((s for s in config['revision_workflow']['spec']['stages'] if s['phase'] == phase))['roles'])

def instruction(phase, topic='', config=None):
    return stages(topic, config)[phase]

def context(state, directory, phase):
    require_contract(state['config'])
    return revision_workflow.context(state, directory, phase)

def verify_stage(state, directory, phase):
    require_contract(state['config'])
    return revision_workflow.verify(state, directory, phase)

def supplement_phase(tasks, topic, config=None):
    primary = [t for t in tasks if t['phase'] in stages(topic, config)]
    resolved = superseded_problems(tasks)
    problem = next((t for t in primary if t['status'] in ('BLOCKED', 'FAILED') and t['id'] not in resolved), None)
    return problem['phase'] if problem else primary[-1]['phase'] if primary else 'resolve'

def manifest_path(directory, phase):
    return Path(directory) / 'artifacts' / 'stages' / (phase + '.json')

def _artifact_path(raw, state):
    if not isinstance(raw, str) or not raw:
        raise ValueError('阶段产物路径无效')
    repo = Path(state['repo']).resolve()
    path = Path(raw)
    path = (repo / path).resolve() if not path.is_absolute() else path.resolve()
    roots = [repo / state['config']['workspace'], repo / state['config']['docs'], repo / paper_root(state['topic'], state['config'])]
    if not any((path.is_relative_to(root.resolve()) for root in roots)) or not path.is_file():
        raise ValueError('阶段产物缺失或超出本课题范围：' + raw)
    return path

def superseded_problems(tasks):
    """A later verified same-stage repair closes a blocker without erasing it."""
    resolved = {}
    for (index, task) in enumerate(tasks):
        if task['status'] not in ('BLOCKED', 'FAILED'):
            continue
        for later in reversed(tasks[index + 1:]):
            if later['phase'] != task['phase'] or later['status'] != 'COMPLETED' or (not later.get('result')):
                continue
            result = json.loads(later['result'])
            verification = json.loads(later.get('verification') or '{}')
            if result['verdict'] == 'accept' and verification.get('stage_artifacts'):
                resolved[task['id']] = later['id']
                break
    return resolved

def recovering_problems(tasks):
    """An active explicit descendant is handling a problem, not yet a pass."""
    by_id = {task['id']: task for task in tasks}
    recovering = {}
    for task in tasks:
        if task['status'] not in ('PENDING', 'RUNNING'):
            continue
        ancestor = task.get('parent')
        visited = set()
        while ancestor in by_id and ancestor not in visited:
            visited.add(ancestor)
            prior = by_id[ancestor]
            if prior['phase'] == task['phase'] and prior['status'] in ('FAILED', 'BLOCKED'):
                recovering[ancestor] = task['id']
            ancestor = prior.get('parent')
    return recovering

def continue_revision_plan(store, tasks, latest):
    """Finish the remaining steps of an already admitted, finite repair plan.

    UCS dispatches one step at a time. A completed diagnostic step does not
    discard its parent's remaining steps or consume a new scientific revision.
    A failed/blocked/unknown step never authorizes the dependent next step.
    """
    state = store.state()
    if state['status'] not in ('READY', 'RUNNING', 'WAITING_EXTERNAL') or any((t['status'] in ('PENDING', 'RUNNING', 'UNKNOWN') for t in tasks)) or any((state['config'].get(limit, 0) > 0 and state[used] >= state['config'][limit] for (used, limit) in [('calls', 'max_calls'), ('tokens', 'max_tokens'), ('active_seconds', 'max_seconds')])):
        return False
    if latest['status'] != 'COMPLETED':
        return False
    result = json.loads(latest.get('result') or '{}')
    if result.get('status') != 'done' or result.get('verdict') != 'revise':
        return False
    parent = next((t for t in tasks if t['id'] == latest.get('parent') and t['phase'] == latest['phase'] and (t['status'] == 'COMPLETED')), None)
    if not parent or not parent.get('verification'):
        return False
    original = json.loads(parent.get('result') or '{}')
    if original.get('status') != 'done' or original.get('verdict') != 'revise':
        return False
    steps = original.get('next_tasks', [])[:3]
    index = next((i for (i, step) in enumerate(steps) if step['title'] == latest['title'] and step['instruction'] == latest['instruction']), None)
    if index is None or index + 1 >= len(steps):
        return False
    following = steps[index + 1]
    if any((t.get('parent') == parent['id'] and t['phase'] == latest['phase'] and (t['title'] == following['title']) and (t['instruction'] == following['instruction']) for t in tasks)):
        return False
    task_id = store.add_task(following['title'], following['instruction'], latest['phase'], parent['id'], dedup=False)
    store.event('workflow.revision_step_queued', {'phase': latest['phase'], 'plan_task': parent['id'], 'completed_step': latest['id'], 'next_step': task_id, 'step_index': index + 1, 'plan_steps': len(steps), 'new_revision': False, 'acceptance_gate_unchanged': True})
    return True

def resume_revision_plan(store):
    """Reconcile a previously truncated plan after controller code reload."""
    if not enabled(store.state()['config']):
        return False
    tasks = store.tasks()
    latest = {t['phase']: t for t in tasks}
    for task in reversed(list(latest.values())):
        if continue_revision_plan(store, tasks, task):
            store.status('READY', '接续已登记修复计划的下一步；原预算与阶段验收保持')
            return True
    import research_continuation
    if research_continuation.resume(store):
        return True
    return False

def advance(store):
    """Call inside the controller's transaction, after all queued work finishes."""
    tasks = [t for t in store.tasks() if t['phase'] != 'code_repair']
    if any((t['status'] in ('PENDING', 'RUNNING', 'UNKNOWN') for t in tasks)):
        return
    superseded = superseded_problems(tasks)
    problem = next((t for t in tasks if t['status'] in ('FAILED', 'BLOCKED') and t['id'] not in superseded), None)
    if problem:
        result = json.loads(problem['result'] or '{}')
        detail = result.get('summary', '')
        store.status('WAITING_EXTERNAL', '等待处理：' + problem['title'] + ('。' + detail if detail else '；查看具体执行错误'))
        return
    order = list(stages(store.state()['topic'], store.state()['config']))
    import runtime_policy
    import strategy_runtime
    expected = runtime_policy.frontier(tasks, order)
    primary = next((t for t in tasks if t['id'] == expected))
    try:
        release = strategy_runtime.active_release()
        if release:
            proposed = strategy_runtime.call('frontier', [tasks, order], release)
            if proposed != expected:
                raise ValueError('Candidate scheduling violates stage precedence or latest-attempt rule')
    except Exception as exc:
        store.event('strategy.failed', {'operation': 'frontier', 'error': str(exc)[:500], 'fallback': True})
    phase = primary['phase']
    result = json.loads(primary['result'])
    if result['verdict'] != 'accept':
        previous = sum((t['phase'] == phase for t in tasks))
        repairs = result['next_tasks'][:3]
        if not repairs or (not execution_limits.unrestricted(store.state()) and previous > store.state()['config']['max_rounds']):
            store.status('WAITING_EXTERNAL', '本阶段未通过，不能跳到论文：' + result['summary'])
        else:
            for repair in repairs:
                store.add_task(repair['title'], repair['instruction'], phase, tasks[-1]['id'], dedup=False)
        return
    if phase == order[-1]:
        store.status('COMPLETED', '修订稿及全文复评产物通过本次冻结流程核验；不代表独立科学认可或已投稿' if revision_workflow.enabled(store.state()['config']) else '实验、分析、论文源码/PDF及全文审查产物通过流程核验；科学贡献和投稿价值仍须作者判断，未投稿或发布')
    else:
        following = order[order.index(phase) + 1]
        if following in ('analyze', 'write', 'paper_review') and research_assurance.enabled(store.state()):
            try:
                research_assurance.verify_coverage(store.state(), store.directory, lambda raw: _artifact_path(raw, store.state()))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                store.status('WAITING_EXTERNAL', '完整研究尚未准入下一阶段：' + str(exc))
                store.event('workflow.coverage_blocked', {'phase': following, 'error': str(exc)})
                return
        (title, task) = instruction(following, store.state()['topic'], store.state()['config'])
        store.add_task(title, task, following, primary['id'])
import local_extensions as _local_extensions
_local_extensions.apply(globals())
