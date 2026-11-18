"""Durable workbench recovery actions; preserve original calls and science gates."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

import ars
import execution_observation as observation
import git_boundary

LABELS = {'inspect': '立即核对', 'revalidate': '复验已有产物', 'recover': '修复并接续'}


def root(directory):
    return observation.safe(directory, Path(directory) / 'telemetry/recovery-actions')


def read(path):
    return ars.read_json(path)


def update(directory, record, state, detail, **extra):
    record.update(state=state, detail=observation.redact(detail), updated_at=ars.now(), **extra)
    record.setdefault('steps', []).append({'at': ars.now(), 'state': state, 'detail': record['detail']})
    ars.atomic_json(root(directory) / (record['id'] + '.json'), record)
    store = ars.Store(directory)
    try:
        with store.tx():
            store.event('ui.recovery_step', {k: record[k] for k in ('id', 'action', 'task_id', 'state', 'detail')})
    finally:
        store.close()


def describe(store):
    records = []
    for path in sorted(root(store.directory).glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
        try:
            value = read(path)
            if value['state'] in ('queued', 'running') and value.get('worker') and not ars.same_process(value['worker']):
                value = {**value, 'state': 'interrupted', 'detail': '此恢复操作的进程已退出，未留下终态；可再次核对，原任务记录保留'}
            records.append(value)
        except (OSError, ValueError, KeyError):
            continue
    return {'history': records, 'active': next((r for r in records if r['state'] in ('queued', 'running')), None)}


def submit(directory, data):
    action = data.get('action')
    if action not in LABELS:
        raise ValueError('不支持的恢复操作')
    store = ars.Store(directory)
    try:
        git_boundary.validate_state(store.state(), directory)
        task = next((t for t in store.tasks() if t['id'] == data.get('task_id')), None)
        if not task:
            raise ValueError('请选择本运行中的工作项')
        if data.get('operation_id') != task.get('operation_id'):
            raise ValueError('此工作项调用已变化，请刷新后操作')
        folder = root(directory); folder.mkdir(parents=True, exist_ok=True)
        with (folder / 'request.lock').open('a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            active = describe(store)['active']
            if active:
                return {'accepted': True, 'duplicate': True, 'operation': active}
            record = dict(id=ars.uid(), action=action, label=LABELS[action], task_id=task['id'],
                          operation_id=task.get('operation_id'), title=task['title'], state='queued',
                          created_at=ars.now(), updated_at=ars.now(), steps=[], detail='操作已登记，等待恢复执行器接管')
            ars.atomic_json(folder / (record['id'] + '.json'), record)
            with (folder / (record['id'] + '.log')).open('ab') as log:
                child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'work',
                    '--directory', str(Path(directory).resolve()), '--id', record['id']],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
            record['worker'] = ars.process_identity(child.pid)
            ars.atomic_json(folder / (record['id'] + '.json'), record)
            ars.BACKGROUND.append(child)
            return {'accepted': True, 'operation': record}
    finally:
        store.close()


def operation_log(store, operation_id):
    op = store.operation(operation_id)
    if not op:
        raise ValueError('不存在的调用')
    folder = observation.safe(store.directory, op['directory'])
    commands, messages = {}, []
    path = folder / 'events.jsonl'
    if path.exists():
        raw, _, at = observation.tail(path, 384000)
        for line in raw.splitlines():
            try:
                event = json.loads(line)
                if not isinstance(event, dict):
                    continue
                item = event.get('item', {})
                if not isinstance(item, dict):
                    continue
                if item.get('type') == 'agent_message':
                    messages.append(observation.redact(str(item.get('text', '')))[:4000])
                elif item.get('type') == 'command_execution':
                    commands[item.get('id', str(len(commands)))] = {
                        'state': item.get('status'), 'exit_code': item.get('exit_code'),
                        'command': observation.redact(str(item.get('command', '')))[:1200],
                        'output': observation.redact(str(item.get('aggregated_output', '')))[-6000:]}
            except (ValueError, TypeError):
                continue
    else:
        at = None
    stderr = folder / 'stderr.log'
    return {'operation_id': operation_id, 'updated_at': at, 'messages': messages[-6:],
            'commands': list(commands.values())[-10:],
            'stderr': observation.redact(observation.tail(stderr)[0]) if stderr.exists() else '',
            'scope': '仅公开执行说明、命令及原始输出；不提供私有推理或凭据文件'}


def live_commands(store, task):
    """Match full command argv; bare PIDs in container receipts are not identities."""
    wanted = []
    operation = store.operation(task['operation_id']) if task.get('operation_id') else None
    for reference in observation.inventory(str(store.directory.resolve()), int(__import__('time').time() // 5)):
        try:
            _, data, _ = observation.receipt(store.directory, reference)
            if operation and data.get('started_at', '') < operation['created_at']:
                continue
            if data.get('status') in ('running', 'unknown') and data.get('target') == 'local' and data.get('executed_argv'):
                wanted.append((reference, data['executed_argv']))
        except (OSError, ValueError, KeyError):
            continue
    alive = []
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            argv = (proc / 'cmdline').read_bytes().decode().rstrip('\0').split('\0')
            for reference, expected in wanted:
                if argv == expected:
                    alive.append({'job': reference, 'pid': int(proc.name)})
        except (OSError, UnicodeError):
            continue
    return alive


def recover(store, task, record):
    operation = store.operation(task['operation_id']) if task.get('operation_id') else None
    if task['status'] not in ('UNKNOWN', 'FAILED', 'BLOCKED'):
        raise ValueError('仅对待核对、失败或阻塞工作项发起修复；当前状态已变化')
    # Only the call executor is closed. Unknown experiment outcomes remain in
    # their original receipts and must be reconciled by the recovery task.
    if operation:
        folder = Path(operation['directory'])
        if (folder / 'receipt.json').exists() and task['status'] == 'UNKNOWN':
            raise ValueError('原回执已到达，请先立即核对并交由控制器验收')
        for name in ('child.json', 'supervisor.json'):
            path = folder / name
            if path.exists() and ars.same_process(read(path)):
                raise ValueError('原执行进程仍在运行；保留该调用，不派发第二份修复')
    alive = live_commands(store, task)
    if alive:
        raise ValueError('发现原命令仍在运行，保留作业等待其终态：' + ', '.join(x['job'] for x in alive))
    prior = next((t for t in store.tasks() if t.get('parent') == task['id'] and t['status'] in ('PENDING', 'RUNNING', 'UNKNOWN')), None)
    if prior:
        return {'recovery_task_id': prior['id'], 'duplicate': True}
    instruction = (
        '这是用户从工作台请求的失败恢复，必须实际修复并接续，不能以“等待回执”或检查报告结束。'
        '本任务所有研究内容仅写本地Git忽略区，不上传、不提交、不推送。'
        '先读取原调用目录中的请求、公开事件、真实错误和本任务artifacts，核对残留本地及远端作业。'
        '原调用终态回执缺失必须保留，不制造原exit_code或成功回执；原未知实验身份及其费用不删除。'
        '本次恢复优先复用已经保存的输入、结果、归档和检查点，禁止重复提交未知或已完成的实验；'
        '确认既有作业终态后，从失败的采集/核验/封口步骤接续。'
        '发现代码或环境错误时先复现和修复，再实际复验；系统源码修复须走既有代码修复流程。'
        '控制器仍独立验收，不能降低科学门槛、扩大设备权限或更改模型/资源策略。'
        '开始任何操作前登记本恢复任务的具体看板，运行中持续更新当前动作、真实计数、报错、修复与下一步。'
        '完整原阶段未通过时返回done+revise并给可执行next_tasks，不把恢复操作当科学阶段完成。\n'
        '原工作项：' + task['title'] + '\n原调用：' + str(task.get('operation_id')) +
        '\n原调用目录：' + str(operation['directory'] if operation else '未派发') +
        '\n原始错误：' + (ars.task_error(task) or '原执行器退出且最终回执缺失，退出原因待复现') +
        '\n原任务指令：' + task['instruction'])
    with store.tx():
        if task['status'] == 'UNKNOWN':
            # Existing explicit-resolution semantics: retain all old bytes,
            # consumed call slots and costs. This is NOT experiment acceptance.
            store.db.execute("UPDATE operations SET state='ABANDONED' WHERE id=?", (operation['id'],))
            store.db.execute("UPDATE tasks SET status='FAILED' WHERE id=?", (task['id'],))
            store.event('operation.user_resolved', {'operation_id': operation['id'], 'action': 'fail',
                'source': 'workbench_recovery', 'warning': '原调用配额不退回，未知实验结果及外部费用仍保留'})
        task_id = store.add_task('修复并接续：' + task['title'], instruction[:10000], task['phase'], task['id'])
        if not task_id:
            raise ValueError('已有相同恢复工作项，请刷新查看')
        store.event('ui.recovery_task_queued', dict(action_id=record['id'], task_id=task_id,
            original_task=task['id'], original_operation=task.get('operation_id'),
            original_receipt_preserved=True, unknown_experiments_resubmitted=False, scientific_gate_waived=False))
        store.status('READY', '工作台已登记实际修复任务，保留原始失败与未知实验；接续既有结果，不盲重投')
    return {'recovery_task_id': task_id, 'original_operation': task.get('operation_id'), 'new_experiments_submitted': 0}


def work(directory, identity):
    directory = Path(directory).resolve()
    path = observation.safe(directory, root(directory) / (identity + '.json'))
    with (root(directory) / 'request.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        record = read(path)
    record['worker'] = ars.process_identity(os.getpid())
    try:
        update(directory, record, 'running', '读取原调用、回执、结果和当前进程；保留原始记录')
        store = ars.Store(directory)
        try:
            git_boundary.validate_state(store.state(), directory)
            task = next(t for t in store.tasks() if t['id'] == record['task_id'])
            if task.get('operation_id') != record['operation_id']:
                raise ValueError('工作项已换用后续调用，本次操作停止；请刷新后选择当前调用')
            if record['action'] == 'inspect':
                state = ars.public_state(store)
                selected = next(t for t in state['tasks'] if t['id'] == task['id'])
                result = {'task_status': task['status'], 'execution': selected.get('execution'),
                          'live_commands': live_commands(store, task), 'new_model_calls': 0}
                text = ((selected.get('execution') or {}).get('reconciliation') or {}).get('summary') or ars.task_error(task) or '已读取原调用；可查看执行证据和日志'
                update(directory, record, 'completed', '核对结果：' + text + '。需恢复时点击“修复并接续”。', result=result)
                return
        finally:
            store.close()
        if record['action'] == 'revalidate':
            update(directory, record, 'running', '控制器正在重新验收已保存产物；不调用模型、不重新运行实验')
            result = ars.recheck_failed_results(directory)
            update(directory, record, 'completed', f"复验完成：通过 {len(result['recovered_tasks'])} 项，仍未通过 {len(result['rejected_tasks'])} 项；未新增模型或实验调用", result=result)
            return
        # Serialize with both the recovery monitor and research controller.
        with (directory / 'recovery.lock').open('a+') as recovery_lock, (directory / 'worker.lock').open('a+') as worker_lock:
            for lock in (recovery_lock, worker_lock):
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise ValueError('控制器正在处理原调用，请待其返回后重试；本操作没有重复派发')
            store = ars.Store(directory)
            try:
                if store.state()['status'] == 'STOPPED_USER':
                    raise ValueError('本运行已被明确停止；请先在工作台继续运行，再发起修复')
                task = next(t for t in store.tasks() if t['id'] == record['task_id'])
                if task.get('operation_id') != record['operation_id']:
                    raise ValueError('原调用身份已变化，请刷新')
                if any(t['status'] in ('UNKNOWN', 'RUNNING') and t['id'] != task['id'] for t in store.tasks()):
                    raise ValueError('还有其他在途或未知调用；先核对该调用，不能并行派发恢复')
                result = recover(store, task, record)
            finally:
                store.close()
        update(directory, record, 'running', '修复任务已登记，正在唤醒原控制器；后续模型沿用当前阶段分配规则', result=result)
        import recovery_control
        result['controller'] = recovery_control.fresh_tick(directory)
        update(directory, record, 'completed', '已交给控制器执行修复并接续；请查看下方恢复工作项，原失败与实验记录完整保留', result=result)
    except Exception as exc:
        update(directory, record, 'failed', str(exc), error=observation.redact(str(exc)))


def priority(store, task):
    queued = {json.loads(r[0])['task_id'] for r in store.db.execute("SELECT payload FROM events WHERE type='ui.recovery_task_queued'")}
    return 0 if task['id'] in queued else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['work'])
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--id', required=True)
    args = parser.parse_args()
    work(args.directory, args.id)
