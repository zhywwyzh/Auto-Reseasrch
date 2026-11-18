"""Project live recovery evidence ahead of historical scientific blockers."""
import json

import code_repair


def apply(store, public):
    progress = public['progress']
    active = next((task for task in store.tasks() if task['phase'] == code_repair.PHASE
                   and task['status'] in ('RUNNING', 'PENDING')), None)
    if active:
        saved = code_repair.session(store, active['id']) or {}
        progress['current_task'] = {k: active[k] for k in ('id', 'title', 'phase', 'status')}
        progress['blocking_error'] = '系统代码自动修复中：' + saved.get('error', '')
        progress['next_action'] = '修复agent修改候选代码后，由控制器独立复验；通过前不重投原实验、不放行科学阶段。'
        progress['recovery_note'] = '当前显示实际代码修复任务；历史研究阻点保留在任务明细中。'
        return
    recovery = public.get('recovery_control', {})
    if recovery.get('mode') == 'system_error' or recovery.get('action') == 'supervisor_error':
        progress['blocking_error'] = recovery.get('reason') or '恢复控制器发生异常；查看原始错误'
        progress['next_action'] = '核对外层监督器的自动修复派发记录；当前不能用历史预算原因代替系统异常。'
        return
    # A scientific blocker is still a blocker; only its superseded budget
    # wording is replaced. Never rewrite or mark the historical task accepted.
    if not progress.get('pending_decision') and store.state()['reason']:
        prior = progress.get('blocking_error', '')
        if any(word in prior for word in ('预算未批准', '预算及首项截尾处置未获决定', '预算未获决定')):
            approved = store.db.execute("SELECT 1 FROM events WHERE type='workflow.budget_decision_approved' LIMIT 1").fetchone()
            if approved:
                progress['blocking_error'] = store.state()['reason']
