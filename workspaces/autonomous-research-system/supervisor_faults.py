"""Escape hatch: turn recovery-controller exceptions into real repair tasks.

This runs in the outer supervisor's fresh process, never through the failed
scientific scheduler. It records once, queues once, and retains UNKNOWN guards.
"""
import contextlib
import fcntl
import hashlib
import json
from pathlib import Path

import ars
import code_repair
import executor_errors
import runtime_revision


@contextlib.contextmanager
def lock(path):
    with Path(path).open('a+') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        yield True


def capture(directory, error):
    """No model call here: persist the repair step for the normal executor."""
    directory = Path(directory).resolve()
    with lock(directory / 'recovery.lock') as owned:
        if not owned:
            return {'action': 'recovery_owned_elsewhere'}
        with lock(directory / 'worker.lock') as idle:
            if not idle:
                return {'action': 'controller_still_active'}
            store = ars.Store(directory)
            try:
                if store.state()['status'] in ('STOPPED_USER', 'STOPPED_BUDGET', 'COMPLETED'):
                    return {'action': 'explicit_stop_retained'}
                if not code_repair.enabled(store.state()):
                    return {'action': 'code_repair_disabled'}
                if any(t['status'] in ('RUNNING', 'UNKNOWN') for t in store.tasks()):
                    for task in store.tasks():
                        if task['status'] != 'RUNNING' or not task.get('operation_id'):
                            continue
                        operation = store.operation(task['operation_id'])
                        receipt = Path(operation['directory']) / 'receipt.json'
                        if receipt.exists() and ars.read_json(receipt).get('success') is True:
                            return {'action': 'returned_operation_needs_durable_validation'}
                    ars.reconcile(store)
                tasks = store.tasks()
                if any(t['status'] in ('RUNNING', 'UNKNOWN') for t in tasks):
                    return {'action': 'original_activity_retained'}
                active = next((t for t in tasks if t['phase'] == code_repair.PHASE and t['status'] == 'PENDING'), None)
                message = executor_errors.redact(error)
                if not active:
                    if any(t['status'] == 'PENDING' for t in tasks):
                        return {'action': 'existing_task_retained'}
                    fingerprint = hashlib.sha256((runtime_revision.LOADED + '\n' + message).encode()).hexdigest()
                    with store.tx():
                        prior = store.db.execute("SELECT seq FROM events WHERE type='system.repair_required' AND json_extract(payload,'$.fault_fingerprint')=? ORDER BY seq DESC LIMIT 1", (fingerprint,)).fetchone()
                        if not prior:
                            store.event('system.repair_required', {'kind': 'recovery_controller_exception',
                                'error': message, 'fault_fingerprint': fingerprint,
                                'runtime_revision': runtime_revision.LOADED,
                                'science_state_unchanged': True})
                        code_repair.maybe_queue(store)
                    active = next((t for t in store.tasks() if t['phase'] == code_repair.PHASE and t['status'] == 'PENDING'), None)
                if not active:
                    return {'action': 'repair_not_queued'}
                old_path = directory / 'recovery-control.json'
                snapshot = ars.read_json(old_path) if old_path.exists() else {}
                snapshot.update(version='recovery-control-v3', revision=runtime_revision.LOADED,
                    topic=store.state()['topic'], id=store.state()['id'], status=store.state()['status'],
                    action='repair_agent_queued', mode='repairing_system', checked_at=ars.now(),
                    reason='恢复控制器报错已交给代码修复agent：' + message,
                    repair_task_id=active['id'], original_error=message, calls=store.state()['calls'])
                ars.atomic_json(old_path, snapshot)
                return {'action': 'repair_agent_queued', 'task_id': active['id'],
                        'calls': store.state()['calls'], 'research_jobs_resubmitted': 0}
            finally:
                store.close()
