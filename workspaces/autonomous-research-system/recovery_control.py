"""Durable recovery control plane. No model invocation or experiment resubmission.

One serialized decision per campaign: honor stops, adopt receipts, reuse results,
resume timed conditions, repair, continue the admitted plan, then start a worker.
Each decision survives a process restart and says what the next wake-up can do.
"""
import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import ars
import executor_errors
import paper_workflow
import runtime_revision
import self_repair
import server_access
import autonomy
import code_repair

VERSION = 'recovery-control-v3'
SNAPSHOT = 'recovery-control.json'
STOPS = {'STOPPED_USER', 'STOPPED_BUDGET', 'COMPLETED'}
INTERVAL = 10


@contextlib.contextmanager
def lease(directory):
    with (Path(directory) / 'recovery.lock').open('a+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        yield True


def enabled(state):
    return (state['config'].get('recovery_control', {}).get('enabled') is True
            or autonomy.enabled(state))


def observe(store):
    path = store.directory / SNAPSHOT
    if not path.exists():
        return {'enabled': enabled(store.state()), 'available': False}
    out = ars.read_json(path)
    checked = dt.datetime.fromisoformat(out['checked_at'])
    out['age_seconds'] = max(0, (dt.datetime.now(dt.timezone.utc) - checked).total_seconds())
    out['stale'] = out['age_seconds'] > 90
    out['available'] = True
    out['enabled'] = enabled(store.state())
    out['source_matches_disk'] = out.get('revision') == runtime_revision.revision()
    error_path = store.directory / 'recovery-service-error.json'
    if error_path.exists():
        error = ars.read_json(error_path)
        if error.get('at', '') > out['checked_at']:
            out['service_error'] = error
    return out


def record(store, action, reason, *, mode=None, retry_at=None, details=None):
    state = store.state()
    heartbeat = store.directory / 'heartbeat.json'
    worker = ars.read_json(heartbeat) if heartbeat.exists() else {}
    current = dt.datetime.now(dt.timezone.utc)
    row = dict(version=VERSION, revision=runtime_revision.LOADED,
               topic=state['topic'], id=state['id'], status=state['status'],
               action=action, reason=executor_errors.redact(reason), mode=mode or action,
               checked_at=current.isoformat(), retry_at=retry_at,
               next_check_at=(current + dt.timedelta(seconds=INTERVAL)).isoformat(),
               controller_revision=worker.get('runtime_revision'),
               controller_upgrade_pending=bool(not state['config'].get('system_runtime_pin', {}).get('enabled')
                    and worker.get('runtime_revision') != runtime_revision.LOADED),
               executor_runtime_root=str(ars.HERE),
               recovery_runtime_root=str(Path(__file__).resolve().parent),
               fingerprint=ars.progress_fingerprint(store), calls=state['calls'])
    if details:
        row.update(details)
    # Heartbeats update the snapshot, not the scientific/task event history.
    old_path = store.directory / SNAPSHOT
    old = ars.read_json(old_path) if old_path.exists() else {}
    if old.get('launch_key') == runtime_revision.LOADED + ':' + row['fingerprint']:
        for key in ('launch_key', 'launch_attempts', 'launch_after'):
            if key in old:
                row.setdefault(key, old[key])
    keys = ('version', 'revision', 'status', 'action', 'reason', 'mode', 'retry_at', 'fingerprint')
    if any(old.get(key) != row.get(key) for key in keys):
        with store.tx():
            store.event('recovery.transition', {key: row[key] for key in keys})
    ars.atomic_json(old_path, row)
    return row


def waiting(store):
    tasks = store.tasks()
    if any(t['status'] == 'UNKNOWN' for t in tasks):
        return record(store, 'waiting_for_receipt', '等待原调用回执或可核对的执行状态；自动检查，禁止重复派发', mode='reconcile')
    latest = {t['phase']: t for t in tasks}
    for task in reversed(list(latest.values())):
        if task['status'] != 'FAILED':
            continue
        diagnostic = json.loads(task.get('verification') or '{}').get('executor_diagnostic', {})
        if diagnostic.get('category') == 'provider_quota':
            return record(store, 'external_or_exhausted', '执行器配额等待；到期自动恢复原阶段',
                          mode='scheduled_retry', retry_at=diagnostic.get('retry_after'))
    decision = self_repair.progress(store)
    choice = (decision or {}).get('last_decision') or {}
    mode = {'repair_exhausted': 'repair_exhausted', 'incident_exhausted': 'repair_exhausted',
            'external_required': 'external_dependency', 'budget_stop': 'budget_stop',
            'dependency_scheduler': 'research_dependency'}.get(choice.get('action'), 'stage_not_accepted')
    return record(store, 'external_or_exhausted', choice.get('reason') or store.state()['reason'] or
                  '没有已准入的下一步；阶段未验收，保留全部预算和证据门槛', mode=mode)


def upgrade_controller(store):
    """Replace an obsolete controller only, preserving a proven live activity.

    SIGTERM is deliberately unsuitable: the legacy handler stops the activity.
    Exact PID/start-time/cmdline checks plus an existing activity receipt/identity
    let the current kernel adopt that original operation without redispatch.
    """
    if not autonomy.enabled(store.state()) or not code_repair.enabled(store.state()):
        return None
    heartbeat=store.directory/'heartbeat.json'
    worker_path=store.directory/'worker.json'
    if not heartbeat.exists() or not worker_path.exists():return None
    if ars.read_json(heartbeat).get('runtime_revision')==runtime_revision.LOADED:return None
    task=next((t for t in store.tasks() if t['status']=='RUNNING'),None)
    if not task or not task.get('operation_id'):return None
    operation=store.operation(task['operation_id']);directory=Path(operation['directory'])
    if (directory/'receipt.json').exists():
        return None  # Never interrupt a controller's in-progress acceptance test.
    identities=[ars.read_json(directory/name) for name in ('supervisor.json','child.json') if (directory/name).exists()]
    if not (directory/'receipt.json').exists() and not any(ars.same_process(row) for row in identities):return None
    def owned(identity,command):
        if not ars.same_process(identity):return False
        try:
            argv=(Path('/proc')/str(identity['pid'])/'cmdline').read_bytes().decode().split('\0')
            index=argv.index('--campaign')
            return command in argv and Path(argv[index+1]).resolve()==store.directory
        except (OSError,ValueError,IndexError):return False
    worker=ars.read_json(worker_path)
    if not owned(worker,'run'):return None
    watchdog_path=store.directory/'watchdog.json'
    watchdog=ars.read_json(watchdog_path) if watchdog_path.exists() else None
    if watchdog and owned(watchdog,'_watch'):
        os.kill(watchdog['pid'],signal.SIGKILL)
    os.kill(worker['pid'],signal.SIGKILL)
    with store.tx():
        store.event('controller.recovery_kernel_handoff',dict(previous_worker=worker,
            original_operation=operation['id'],activity_preserved=True,calls_unchanged=True,
            recovery_revision=runtime_revision.LOADED))
    return operation['id']


def reconcile_once(directory):
    """Serialized with recovery peers AND the research worker; starting is idempotent."""
    import system_supervisor
    directory = Path(directory).resolve()
    with lease(directory) as owned:
        if not owned:
            return {'action': 'recovery_owned_elsewhere'}
        store = ars.Store(directory)
        try:
            if store.state()['status'] in STOPS:
                return record(store, 'observed', store.state()['reason'], mode='terminal')
            with system_supervisor.idle_worker(directory) as idle:
                if not idle:
                    handed_off=upgrade_controller(store)
                    if handed_off:
                        return record(store,'controller_handoff','旧控制器已交接，原活动及operation保留；下一轮接管原回执',mode='monitoring',details={'preserved_operation':handed_off})
                    return record(store, 'controller_alive', '当前控制器持有执行锁；保留在途调用，结束后接续', mode='monitoring')
                if any(t['status'] in ('UNKNOWN', 'RUNNING') for t in store.tasks()):
                    returned = []
                    for task in store.tasks():
                        if task['status'] not in ('UNKNOWN', 'RUNNING') or not task.get('operation_id'):
                            continue
                        operation = store.operation(task['operation_id'])
                        receipt = Path(operation['directory']) / 'receipt.json'
                        if receipt.exists() and ars.read_json(receipt).get('success') is True:
                            returned.append(task)
                    if returned:
                        # A monitoring tick has a short liveness timeout. Full
                        # source/PDF/test validation belongs to the durable worker.
                        with store.tx():
                            for task in returned:
                                store.db.execute("UPDATE tasks SET status='RUNNING' WHERE id=?", (task['id'],))
                            store.status('READY', '原调用已返回，交由持久控制器独立复验；保留原operation，不重复派发')
                    else:
                        ars.reconcile(store)
                    if any(t['status'] == 'UNKNOWN' for t in store.tasks()):
                        if store.state()['status'] != 'NEEDS_RECONCILIATION':
                            with store.tx():
                                store.status('NEEDS_RECONCILIATION', '缺少可核对回执，监督器持续检查，禁止盲重投')
                        return waiting(store)
                    # Finalizing a receipt may set a quota wait or an explicit stop.
                    # Never overwrite that result with unconditional READY.
                    if store.state()['status'] in STOPS:
                        return record(store, 'observed', store.state()['reason'], mode='terminal')
                    if (store.state()['status'] == 'NEEDS_RECONCILIATION'
                            or any(t['status'] == 'RUNNING' for t in store.tasks())):
                        with store.tx():
                            store.status('READY', '原回执已核对，接续原阶段')
            if any(t['status'] == 'FAILED' for t in store.tasks()):
                try:
                    ars.recheck_failed_results(directory, automatic=True)
                except ValueError as exc:
                    if '控制器仍在运行' in str(exc):
                        return record(store, 'controller_started', '控制器已接管', mode='monitoring')
                    raise
            with system_supervisor.idle_worker(directory) as idle:
                if not idle:
                    return record(store, 'controller_started', '控制器已接管', mode='monitoring')
                state = store.state()
                if state['status'] in STOPS:
                    return record(store, 'observed', state['reason'], mode='terminal')
                if any(t['status'] == 'UNKNOWN' for t in store.tasks()):
                    return waiting(store)
                if state['status'] == 'WAITING_EXTERNAL':
                    import research_continuation
                    limit = research_continuation.submission_limit(store)
                    if limit and not any(t['status'] in ('PENDING', 'RUNNING', 'UNKNOWN') for t in store.tasks()):
                        with store.tx():
                            old = store.db.execute("SELECT payload FROM events WHERE type='workflow.resource_limit_reached' ORDER BY seq DESC LIMIT 1").fetchone()
                            if not old or json.loads(old[0]) != limit:
                                store.event('workflow.resource_limit_reached', limit)
                            store.status('WAITING_EXTERNAL', limit['reason'])
                        return record(store, 'resource_limit_reached', limit['reason'], mode='budget_stop',
                                      details={'resource_limit': limit})
                    executor_errors.maybe_resume(store)
                    server_access.recover(store)
                    system_supervisor.probe_network_change(store)
                    with store.tx():
                        queued = self_repair.maybe_queue(store)
                    if not queued and store.state()['status'] == 'WAITING_EXTERNAL':
                        with store.tx():
                            queued = paper_workflow.resume_revision_plan(store)
                    if not queued and store.state()['status'] == 'WAITING_EXTERNAL':
                        # Dependency scheduling belongs to the actual workflow,
                        # not a topic-specific shortcut in the supervisor.
                        ars.advance(store)
                    if store.state()['status'] == 'WAITING_EXTERNAL' and any(t['status'] == 'PENDING' for t in store.tasks()):
                        with store.tx():
                            store.status('READY', '已有已准入的待执行任务，监督器接续')
                    if store.state()['status'] == 'WAITING_EXTERNAL':
                        with store.tx():
                            autonomy.maybe_queue(store)
                    if store.state()['status'] == 'WAITING_EXTERNAL':
                        with store.tx():
                            autonomy.maybe_diagnose(store)
                    if store.state()['status'] == 'WAITING_EXTERNAL':
                        return waiting(store)
                if store.state()['status'] not in ('READY', 'RUNNING'):
                    return record(store, 'state_requires_reconciliation', store.state()['reason'], mode='reconcile')
            # Crash-loop circuit is durable across supervisor restarts. A source
            # change or task progress can reopen it; no model counter is reset.
            key = runtime_revision.LOADED + ':' + ars.progress_fingerprint(store)
            old_path = directory / SNAPSHOT
            old = ars.read_json(old_path) if old_path.exists() else {}
            attempts = old.get('launch_attempts', 0) if old.get('launch_key') == key else 0
            if old.get('launch_key') == key and old.get('launch_after') and ars.now() < old['launch_after']:
                return record(store, 'controller_backoff', '控制器未取得任务进展；按持久退避时间检查', mode='scheduled_retry',
                    retry_at=old['launch_after'], details={k: old[k] for k in ('launch_key', 'launch_attempts', 'launch_after')})
            start = ars.start_campaign(directory)
            launch_after = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=min(300, 10 * 2 ** min(attempts, 5)))).isoformat()
            return record(store, 'start_or_adopt_controller', '已启动或接管控制器；模型/实验仍须原预算与原验收',
                mode='dispatch', details=dict(start=start, launch_key=key, launch_attempts=attempts + 1, launch_after=launch_after))
        except Exception as exc:
            record(store, 'supervisor_error', f'{type(exc).__name__}: {exc}', mode='system_error')
            raise
        finally:
            store.close()


def enroll(directory):
    """Explicit scope migration. Never alters tasks, operations, budgets or stops."""
    store = ars.Store(directory)
    try:
        with lease(directory) as owned:
            if not owned:
                raise ValueError('恢复调度正在处理此任务，稍后再迁移')
            with store.tx():
                cfg = store.state()['config']
                autonomy.enroll(store)
                cfg = store.state()['config']
                cfg['recovery_control'] = {'enabled': True, 'version': VERSION, 'owner': 'scoped-service'}
                # The old resident supervisor discovers only enabled entries.
                # Its task processes are deliberately left alive.
                cfg['system_supervisor'] = {**cfg.get('system_supervisor', {}), 'enabled': False}
                store.db.execute('UPDATE campaign SET config=?', (ars.dump(cfg),))
                store.event('recovery.enrolled', {'version': VERSION, 'revision': runtime_revision.LOADED,
                    'authorization': '用户要求修改自动研究智能体系统本身', 'budgets_unchanged': True,
                    'tasks_unchanged': True, 'inflight_operations_preserved': True})
    finally:
        store.close()


def fresh_tick(directory):
    # Import each decision in a fresh process. Restarting this supervisor is
    # no longer needed when repair/workflow Python modules change on disk.
    script = Path(__file__).resolve()
    store = ars.Store(directory)
    try:
        pin = store.state()['config'].get('system_runtime_pin', {})
        if pin.get('enabled'):
            # Execution must use the recorded runtime, never silently fall back
            # to a different checkout when a pin is unavailable or corrupted.
            root = Path(pin['code_root']).resolve()
            index_path = Path(pin['index']['path'])
            import hashlib
            if hashlib.sha256(index_path.read_bytes()).hexdigest() != pin['index']['sha256']:
                raise ValueError('独立执行端版本索引不匹配')
            for name, digest in ars.read_json(index_path)['files'].items():
                source = (root / name).resolve()
                if not source.is_relative_to(root) or hashlib.sha256(source.read_bytes()).hexdigest() != digest:
                    raise ValueError('独立执行端代码发生漂移：' + name)
            # Older pinned runtimes need not contain the new control module.
            # Keep their scientific code immutable and overlay recovery only.
            script = Path(__file__).with_name('recovery_bridge.py')
    finally:
        store.close()
    argv = ([sys.executable, str(script), str(directory)] if script.name == 'recovery_bridge.py'
            else [sys.executable, str(script), 'tick', '--campaign', str(directory)])
    result = subprocess.run(argv,
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=55)
    if result.returncode:
        raise RuntimeError(executor_errors.redact(result.stderr[-1000:]) or 'recovery tick failed')
    return json.loads(result.stdout)


def serve(directory):
    directory = Path(directory).resolve()
    with (directory / 'recovery-service.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ars.atomic_json(directory / 'recovery-service.json', ars.process_identity(os.getpid()))
        stopping = False
        def stop(*_):
            nonlocal stopping
            stopping = True
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        while not stopping:
            try:
                fresh_tick(directory)
            except Exception as exc:
                # Keep the service alive; a broken import/timeout must be visible
                # even if the new decision process could not write its snapshot.
                ars.atomic_json(directory / 'recovery-service-error.json',
                    {'at': ars.now(), 'error': executor_errors.redact(str(exc))})
            for _ in range(INTERVAL * 5):
                if stopping:
                    break
                time.sleep(.2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['tick', 'serve', 'enroll'])
    parser.add_argument('--campaign', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'serve':
        serve(args.campaign)
    elif args.command == 'enroll':
        enroll(args.campaign)
    else:
        print(json.dumps(reconcile_once(args.campaign), ensure_ascii=False))


if __name__ == '__main__':
    main()
