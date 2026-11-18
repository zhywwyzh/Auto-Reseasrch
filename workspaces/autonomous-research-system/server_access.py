"""Recover an explicitly registered SSH login; never submit a research job.

The enrollment points to one previously supplied visible user message. Passwords
are read into memory only, passed through a private PTY, and never logged/saved.
No credential discovery, remote access changes, or relaxed host-key checks.
"""
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import uuid

import ars
import runtime_policy


def registered_target(state, policy):
    catalog = ars.read_json(Path(state['repo']) / 'workspaces/autonomous-research-system/execution-targets.json')
    target = next(row for row in catalog['targets'] if row['id'] == policy['target_id'])
    expected = {k: target['ssh'][k] for k in ('host', 'user', 'port')}
    if expected != policy['endpoint']:
        raise ValueError('Registered SSH endpoint changed; explicit enrollment required')
    return expected


def read_registered_password(state, policy):
    source = Path(policy['source_file'])
    if source.is_symlink() or not source.is_file():
        raise ValueError('Registered credential source missing')
    info = source.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('Registered credential source must be private')
    # Read exactly one registered line, not a general history search.
    with source.open() as stream:
        header = json.loads(stream.readline())
        if header.get('type') != 'session_meta' or header['payload'].get('cwd') != state['repo']:
            raise ValueError('Credential source belongs to a different workspace')
        stream.seek(0)
        raw = next((line for number, line in enumerate(stream, 1) if number == policy['source_line']), None)
    if raw is None:
        raise ValueError('Registered user message missing')
    item = json.loads(raw)
    payload = item.get('payload', {})
    if (item.get('type') != 'response_item' or payload.get('type') != 'message'
            or payload.get('role') != 'user' or item.get('timestamp') != policy['source_timestamp']):
        raise ValueError('Credential must come from the registered visible user message')
    message = '\n'.join(c.get('text', '') for c in payload.get('content', [])
                        if isinstance(c, dict) and c.get('type') in ('text', 'input_text'))
    endpoint = registered_target(state, policy)
    if endpoint['host'] not in message:
        raise ValueError('Credential source target mismatch')
    match = re.search(r'(?:密码|password)\s*(?:为|是)?\s*[:：=]?\s*(\S+)', message, re.I)
    if not match:
        raise ValueError('Registered password field missing')
    return match.group(1).strip('`\'"，。')


def master_alive(control, endpoint):
    if not control:
        return False
    path = Path(control)
    try:
        info, parent = path.lstat(), path.parent.stat()
        if (not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid()
                or parent.st_uid != os.getuid() or parent.st_mode & 0o077):
            return False
        result = subprocess.run(['ssh', '-S', str(path), '-O', 'check', '-p', str(endpoint['port']),
                                 endpoint['user'] + '@' + endpoint['host']],
                                capture_output=True, timeout=5)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def authenticate(endpoint, control, password):
    import pexpect
    args = ['-M', '-S', str(control), '-o', 'ControlPersist=yes', '-o', 'StrictHostKeyChecking=yes',
            '-o', 'ForwardAgent=no', '-o', 'PubkeyAuthentication=no',
            '-o', 'PreferredAuthentications=password', '-o', 'NumberOfPasswordPrompts=1',
            '-o', 'ConnectTimeout=8', '-o', 'ServerAliveInterval=30', '-o', 'ServerAliveCountMax=3',
            '-fN', '-p', str(endpoint['port']), endpoint['user'] + '@' + endpoint['host']]
    child = pexpect.spawn('ssh', args, encoding='utf-8', timeout=15, echo=False)
    # Do not attach a logfile or propagate child output/exceptions: those may
    # contain echoed terminal input. Only fixed outcome labels leave this call.
    try:
        if child.expect([r'(?i)password:', pexpect.EOF, pexpect.TIMEOUT]) != 0:
            return False
        child.sendline(password)
        outcome = child.expect([pexpect.EOF, r'(?i)permission denied', pexpect.TIMEOUT])
        child.close(force=outcome != 0)
        return outcome == 0 and child.exitstatus == 0
    finally:
        if child.isalive():
            child.close(force=True)


def recover(store):
    """Under worker.lock, before ordinary bounded repair. No model/job dispatch."""
    state = store.state()
    policy = state['config'].get('ssh_access_recovery', {})
    if (not policy.get('enabled') or state['topic'] != policy.get('topic')
            or state['config'].get('workflow') != 'paper' or state['status'] != 'WAITING_EXTERNAL'):
        return False
    tasks = store.tasks()
    if any(t['status'] in ('PENDING', 'RUNNING', 'UNKNOWN') for t in tasks):
        return False
    if any(state['config'].get(limit, 0) > 0 and state[used] >= state['config'][limit]
           for used, limit in [('calls', 'max_calls'), ('tokens', 'max_tokens'), ('active_seconds', 'max_seconds')]):
        return False
    # Only the latest task in each phase can request access recovery.
    latest = {t['phase']: t for t in tasks}
    for task in reversed(list(latest.values())):
        error = ars.task_error(task) or json.loads(task.get('result') or '{}').get('summary', '')
        if task['status'] not in ('BLOCKED', 'FAILED') or runtime_policy.incident(error) != 'transport:auth':
            continue
        marker = {'task_id': task['id'], 'operation_id': task['operation_id']}
        # One authentication attempt per known failed operation and explicitly
        # enrolled source version. Failed logins never spin every supervisor tick.
        prior = [json.loads(row[0]) for row in store.db.execute(
            "SELECT payload FROM events WHERE type='access_recovery.attempted'")]
        if any(all(row.get(k) == v for k, v in marker.items())
               and row.get('source_version') == policy['source_version'] for row in prior):
            continue
        with store.tx():
            store.event('access_recovery.attempted', marker | {'source_version': policy['source_version'],
                        'credentials_persisted': False, 'job_submitted': False})
        try:
            endpoint = registered_target(state, policy)
            control = state['config'].get('ssh_control_path')
            reused = master_alive(control, endpoint)
            if not reused:
                folder = Path(policy['control_directory'])
                folder.mkdir(mode=0o700, parents=True, exist_ok=True)
                info = folder.lstat()
                if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                    raise ValueError('SSH control directory must be private')
                # Leave any stale/unverified socket untouched.
                control = str(folder / ('ssh-' + uuid.uuid4().hex[:12]))
                password = read_registered_password(state, policy)
                try:
                    authenticated = authenticate(endpoint, control, password)
                finally:
                    password = None
                if not authenticated or not master_alive(control, endpoint):
                    raise ValueError('Registered SSH authentication failed')
            with store.tx():
                config = store.state()['config']; config['ssh_control_path'] = control
                store.db.execute('UPDATE campaign SET config=?', (ars.dump(config),))
                store.event('access_recovery.succeeded', marker | {'control_path': control,
                            'reused_master': reused, 'credentials_persisted': False, 'job_submitted': False})
                store.event('self_repair.condition_changed', marker | {'incident': 'transport:auth',
                            'observed': 'registered SSH master authenticated', 'authentication_verified': True,
                            'job_submitted': False, 'total_task_repair_cap_retained': True})
            return True
        except Exception:
            # Never serialize arbitrary exception text or source message content.
            with store.tx():
                store.event('access_recovery.failed', marker | {'reason': 'Registered access recovery did not verify a usable master',
                            'credentials_persisted': False, 'job_submitted': False})
            return False
    return False
