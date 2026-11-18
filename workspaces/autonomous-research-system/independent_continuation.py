"""Run explicitly enrolled independent work without waiving a blocked stage.

The controller reads a pinned graph supplied within the existing authorization.
It never guesses from prose whether an instruction may submit more experiments.
"""
import hashlib
import json
VERSION = 'tr002-independent-saved-evidence-v1'
SCOPES = {'saved_output_evaluation', 'recovery_preparation'}

def maybe_queue(store, problem):
    state = store.state()
    policy = state['config'].get('independent_continuation', {})
    if state['config'].get('workflow') != 'paper' or not policy.get('enabled') or policy.get('version') != VERSION:
        return False
    if state['status'] not in ('READY', 'RUNNING', 'WAITING_EXTERNAL') or any((t['status'] in ('PENDING', 'RUNNING', 'UNKNOWN') for t in store.tasks())):
        return False
    if any((state['config'].get(limit, 0) > 0 and state[used] >= state['config'][limit] for (used, limit) in [('calls', 'max_calls'), ('tokens', 'max_tokens'), ('active_seconds', 'max_seconds')])):
        return False
    import paper_workflow
    resolve = lambda raw: paper_workflow._artifact_path(raw, state)
    plan_path = resolve(policy['plan']['path'])
    if hashlib.sha256(plan_path.read_bytes()).hexdigest() != policy['plan']['sha256']:
        raise ValueError('已登记独立工作计划哈希不匹配')
    plan = json.loads(plan_path.read_text())
    if plan.get('version') != VERSION or plan.get('topic') != state['topic']:
        raise ValueError('独立工作计划身份不匹配')
    tasks = {t['id']: t for t in store.tasks()}
    prior = {json.loads(row[0])['node_id']: json.loads(row[0])['task_id'] for row in store.db.execute("SELECT payload FROM events WHERE type='workflow.independent_node_queued' ORDER BY seq")}
    for node in plan.get('nodes', []):
        if node['id'] in prior or node.get('phase') != problem['phase']:
            continue
        if node.get('phase') != problem['phase'] or node.get('scope') not in SCOPES:
            raise ValueError('独立节点不得越过阶段或扩大研究作业授权')
        if node.get('new_solver_calls') != 0 or node.get('new_simulation_episodes') != 0:
            raise ValueError('独立节点只允许保存证据评价或恢复准备')
        if any((dep not in prior or tasks[prior[dep]]['status'] != 'COMPLETED' for dep in node.get('depends_on', []))):
            continue
        for ref in node.get('inputs', []):
            path = resolve(ref['path'])
            if hashlib.sha256(path.read_bytes()).hexdigest() != ref['sha256']:
                raise ValueError('独立节点输入证据哈希不匹配')
        instruction = node['instruction'] + '\n控制器独立节点约束：原科学阻点保留，不准推进analyze/write。只评价已保存输出或准备恢复方案；新增求解/仿真调用必须为0，不扩大预算、线程或权限。先核对所有已有实际成本，受剩余预算限制；不得把独立节点结束标作experiment通过。本节点结束须保存可核对产物、原始错误与成本，done+revise保留整阶段未完成。'
        task_id = store.add_task(node['title'], instruction, node['phase'], problem['id'])
        store.event('workflow.independent_node_queued', {'node_id': node['id'], 'task_id': task_id, 'blocked_task': problem['id'], 'scope': node['scope'], 'scientific_blocker_waived': False, 'budget_extension_authorized': False})
        store.status('RUNNING', '继续已有保存结果的独立工作；正式补测仍待预算决定')
        return True
    return False
import local_extensions as _local_extensions
_local_extensions.apply(globals())
