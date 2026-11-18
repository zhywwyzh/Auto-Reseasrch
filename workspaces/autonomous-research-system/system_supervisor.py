#!/usr/bin/env python3
"""Durable outer supervision of explicitly enrolled campaigns.

Rechecks existing results before reserving any new calls, watches receipt arrival,
and restarts controllers without resubmitting UNKNOWN jobs. An incident may wake
the bounded system optimizer; genuine external dependencies remain visible.
"""
import argparse
import contextlib
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import sqlite3
import subprocess
import sys
import time

import ars
import self_repair
import strategy_runtime
import runtime_policy
import server_access
import executor_errors
import paper_workflow
import autonomy
from concurrent.futures import ThreadPoolExecutor

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'runs/supervisor'


def ensure_running(repo):
    """Starting any workflow also ensures outer supervision, without a web tab.

    Prefer the installed user service (restart and login persistence). A detached
    host process is a fallback where systemd is unavailable; it has no boot claim.
    """
    root = Path(repo) / 'workspaces/autonomous-research-system'
    script = root / 'system_supervisor.py'
    if not script.is_file():
        return {'available': False, 'reason': 'supervisor source unavailable'}
    saved = root / 'runs/supervisor/process.json'
    if saved.exists():
        try:
            if ars.same_process(ars.read_json(saved)):
                return {'available': True, 'action': 'already_running'}
        except (OSError, ValueError, KeyError):
            pass
    environment = dict(os.environ)
    runtime = Path('/run/user') / str(os.getuid())
    if (runtime / 'bus').exists():
        environment.setdefault('XDG_RUNTIME_DIR', str(runtime))
        environment.setdefault('DBUS_SESSION_BUS_ADDRESS', 'unix:path=' + str(runtime / 'bus'))
        try:
            result = subprocess.run(['systemctl', '--user', 'start', 'autoresearch-supervisor.service'],
                capture_output=True, text=True, timeout=8, env=environment)
            if result.returncode == 0:
                return {'available': True, 'action': 'user_service_started'}
        except (OSError, subprocess.TimeoutExpired):
            pass
    logdir = root / 'runs/supervisor'; logdir.mkdir(parents=True, exist_ok=True)
    with (logdir / 'service.log').open('a') as output:
        child = subprocess.Popen([sys.executable, str(script), 'serve'], stdout=output, stderr=output,
            stdin=subprocess.DEVNULL, start_new_session=True)
    ars.BACKGROUND.append(child)
    return {'available': True, 'action': 'detached_host_service', 'pid': child.pid,
            'boot_persistence': False}


def write_status(value):
    ROOT.mkdir(parents=True, exist_ok=True)
    ars.atomic_json(ROOT / 'status.json', value)


def enroll(directory):
    """Explicit deployment action; retains task, budget, operation, and science state."""
    directory = Path(directory).resolve()
    store = ars.Store(directory)
    try:
        with store.tx():
            state = store.state(); cfg = state['config']
            if cfg.get('workflow') != 'paper' or cfg.get('backend') != 'codex':
                raise ValueError('Only an already authorized paper campaign can be enrolled')
            cfg['system_supervisor'] = {'enabled': True, 'version': 'v2'}
            cfg['self_repair'] = dict(self_repair.POLICY)
            cfg['delivery_contract'] = 'parsed-pdf-v1'
            store.db.execute('UPDATE campaign SET config=?', (ars.dump(cfg),))
            store.event('system.enrolled', {'version': ars.VERSION, 'budget_retained': True,
                                          'task_state_retained': True, 'authorization': 'current user requested autonomous system upgrade'})
        return {'directory': str(directory), 'status': state['status'], 'calls': state['calls']}
    finally:
        store.close()


def controlled_paths():
    ROOT.mkdir(parents=True, exist_ok=True)
    roots = [HERE]
    for row in ars.read_json(ars.REPO / 'workspaces/topics.json')['topics']:
        roots.append(ars.REPO / row['workspace'])
    for root in roots:
        for p in (root / 'runs/ars').glob('*/state.sqlite3'):
            if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):
                continue
            store = None
            try:
                store = ars.Store(p.parent)
                state = store.state(); cfg = state['config']
                if cfg.get('autonomy', {}).get('enabled') is False:
                    continue
                registered = (cfg.get('system_supervisor', {}).get('enabled')
                              or cfg.get('recovery_control', {}).get('enabled')
                              or cfg.get('system_runtime_pin', {}).get('enabled'))
                legacy_started = (state['calls'] > 0 and state['topic'] != 'ARS-DEMO'
                                  and state['status'] not in ('COMPLETED', 'STOPPED_USER', 'STOPPED_BUDGET'))
                if registered or legacy_started:
                    if state['status'] not in ('COMPLETED', 'STOPPED_USER', 'STOPPED_BUDGET'):
                        with store.tx():
                            autonomy.enroll(store)
                    yield p.parent
            except (OSError, ValueError, sqlite3.Error) as exc:
                # One damaged campaign must not hide every other task.
                ars.atomic_json(ROOT / ('discovery-error-' + p.parent.name + '.json'),
                                {'at': ars.now(), 'directory': str(p.parent), 'error': executor_errors.redact(str(exc))})
            finally:
                if store:
                    store.close()


@contextlib.contextmanager
def idle_worker(directory):
    with (Path(directory) / 'worker.lock').open('a+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        yield True


def tick_campaign(directory):
    # All recovery decisions pass through one persistent control plane.
    import recovery_control
    return recovery_control.reconcile_once(directory)


def probe_network_change(store):
    """Read-only TCP probe of the registered endpoint, never auth or a job submission.

Only a recorded route/connectivity failure can use this wake-up. Authentication,
scientific inputs, permissions, user stops and budgets have different semantics.
"""
    if store.state()['status'] != 'WAITING_EXTERNAL':
        return False
    target_file = Path(store.state()['repo']) / 'workspaces/autonomous-research-system/execution-targets.json'
    if not target_file.exists():
        return False
    catalog = ars.read_json(target_file)
    target = next((x for x in catalog.get('targets', []) if x['id'] == catalog.get('default_experiment_target')), None)
    if not target or not target.get('ssh'):
        return False
    for task in store.tasks():
        if task['status'] not in ('FAILED', 'BLOCKED'):
            continue
        error = ars.task_error(task) or json.loads(task.get('result') or '{}').get('summary', '')
        if runtime_policy.incident(error) not in ('transport:route', 'transport:timeout'):
            continue
        marker = {'task_id': task['id'], 'operation_id': task['operation_id'], 'incident': runtime_policy.incident(error)}
        if any(all(json.loads(r[0]).get(k) == v for k, v in marker.items()) for r in store.db.execute("SELECT payload FROM events WHERE type='self_repair.condition_changed'")):
            continue
        try:
            with socket.create_connection((target['ssh']['host'], int(target['ssh'].get('port', 22))), timeout=2):
                pass
        except OSError:
            return False
        with store.tx():
            store.event('self_repair.condition_changed', marker | {'observed': 'registered TCP endpoint reachable',
                        'authentication_verified': False, 'job_submitted': False, 'total_task_repair_cap_retained': True})
        return True
    return False


def optimizer_feedback(paths):
    issues = []
    for directory in paths:
        store = ars.Store(directory)
        try:
            state = store.state()
            for event in store.db.execute("SELECT seq,type,payload FROM events WHERE type IN ('system.repair_required','strategy.failed','task.failed','task.blocked') ORDER BY seq DESC LIMIT 4"):
                payload = json.loads(event['payload'])
                # Only compact engineering observations; no paper data or credentials.
                error = payload.get('error') or payload.get('summary') or payload.get('kind', '')
                issues.append({'campaign': state['topic'] + '/' + state['id'], 'event': event['seq'],
                               'kind': event['type'], 'category': self_repair.classify(error), 'error': error[:600]})
        finally:
            store.close()
    return issues


def tick():
    paths = list(controlled_paths()); rows = []
    def check(directory):
        try:
            import recovery_control
            return recovery_control.fresh_tick(directory)
        except Exception as exc:
            error = {'at': ars.now(), 'id': directory.name, 'action': 'supervisor_error',
                     'error': executor_errors.redact(str(exc))}
            ars.atomic_json(directory / 'recovery-service-error.json', error)
            # A failed recovery controller cannot be responsible for starting
            # its own repair. Enter through this independent outer-layer path.
            try:
                import supervisor_faults
                error['repair'] = supervisor_faults.capture(directory, error['error'])
                if error['repair']['action'] == 'repair_agent_queued':
                    error['action'] = 'repair_agent_queued'
            except Exception as repair_error:
                error['repair_bootstrap_error'] = executor_errors.redact(str(repair_error))
            return error
    # Independent campaigns do not wait for one slow SSH/import/SQLite probe.
    # These are local checks, never extra research/model agents.
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(check, paths))
    # A broken active strategy is rolled back; research tasks use bundled fallback meanwhile.
    try:
        release = strategy_runtime.active_release()
        if release:
            answer = strategy_runtime.call('classify', ['缺少回执且无法确认执行状态'], release)
            if answer != 'uncertain_execution':
                raise ValueError('Active strategy health check failed')
        strategy_status = {'version': release['version'] if release else 'bundled-v2'}
    except Exception as exc:
        strategy_status = {'error': str(exc), 'fallback': 'bundled-v2'}
        import evolution
        archive = evolution.Archive()
        try:
            strategy_status['rollback'] = archive.rollback('Active strategy failed integrity check')
        except Exception as rollback_error:
            strategy_status['rollback_error'] = str(rollback_error)
        finally:
            archive.close()
    out = {'at': ars.now(), 'version': ars.VERSION, 'campaigns': rows, 'strategy': strategy_status,
           'feedback': optimizer_feedback(paths)}
    write_status(out)
    return out


def serve(interval=10, optimize=False):
    ROOT.mkdir(parents=True, exist_ok=True)
    with (ROOT / 'service.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ars.atomic_json(ROOT / 'process.json', ars.process_identity(__import__('os').getpid()))
        stopping = False
        def stop(*_):
            nonlocal stopping
            stopping = True
        signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
        child = None
        while not stopping:
            try:
                # Refresh discovery and recovery code as well as workflow code.
                result = subprocess.run([sys.executable, str(Path(__file__).resolve()), 'tick'],
                    capture_output=True, text=True, timeout=58, stdin=subprocess.DEVNULL)
                if result.returncode:
                    raise RuntimeError(executor_errors.redact(result.stderr[-1800:]))
                out = json.loads(result.stdout)
            except Exception as exc:
                ars.atomic_json(ROOT / 'service-error.json', {'at': ars.now(), 'error': executor_errors.redact(str(exc))})
                out = {'feedback': []}
            if optimize and out['feedback'] and (child is None or child.poll() is not None):
                import evolution
                if (evolution.DEFAULT_ROOT / 'archive.sqlite3').exists():
                    archive = evolution.Archive()
                    try:
                        try:
                            with archive.lock(): archive.reconcile()
                        except ValueError:
                            pass  # A live optimizer owns its lock and receipt commits.
                        cfg, calls = archive.config()
                        outstanding = archive.db.execute("SELECT 1 FROM operations WHERE state IN ('RUNNING','RESERVED','UNKNOWN')").fetchone()
                        if calls < cfg['max_calls'] and not cfg['stopped'] and not outstanding:
                            # Passing feedback via file avoids command interpolation.
                            ars.atomic_json(ROOT / 'optimization-feedback.json', out['feedback'])
                            child = subprocess.Popen([sys.executable, str(HERE / 'evolution.py'), 'run', '--iterations', '1',
                                                      '--feedback', str(ROOT / 'optimization-feedback.json')],
                                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    finally:
                        archive.close()
            for _ in range(max(1, int(interval * 5))):
                if stopping: break
                time.sleep(0.2)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    enroll_parser = sub.add_parser('enroll'); enroll_parser.add_argument('--campaign', type=Path, required=True)
    sub.add_parser('tick')
    daemon = sub.add_parser('serve'); daemon.add_argument('--interval', type=int, default=10); daemon.add_argument('--optimize', action='store_true')
    args = p.parse_args()
    if args.command == 'serve': serve(args.interval, args.optimize)
    else: print(json.dumps(enroll(args.campaign) if args.command == 'enroll' else tick(), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
