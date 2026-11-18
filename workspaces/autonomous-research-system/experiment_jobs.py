"""Run a bounded foreground command and retain a process receipt, never a model call.

SSH jobs also carry a remote timeout. A lost SSH connection is UNKNOWN, not safe to
retry blindly. Credentials belong to SSH configuration/agent, never to arguments.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import stat
import subprocess
import time
import uuid
import sqlite3
import execution_limits
import experiment_monitor

def unrestricted_root(root):
    """Only a registered run with explicit current user authority may use zero."""
    for folder in [root, *root.parents]:
        path = folder / 'state.sqlite3'
        if not path.is_file():
            continue
        db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
        db.row_factory = sqlite3.Row
        try:
            state = dict(db.execute('SELECT * FROM campaign').fetchone())
            state['config'] = json.loads(state['config'])
            return execution_limits.unrestricted(state)
        finally:
            db.close()
    return False

def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def write(path, value):
    temp = path.with_suffix('.tmp')
    with temp.open('w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)

def registered_scope(root, cwd):
    """Use a run's own registration; never borrow another topic's workspace."""
    campaign = experiment_monitor.find_campaign(root)
    if campaign is None:
        return None
    db = sqlite3.connect((campaign / 'state.sqlite3').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        state = dict(db.execute('SELECT * FROM campaign').fetchone())
        state['config'] = json.loads(state['config'])
    finally:
        db.close()
    import git_boundary
    git_boundary.validate_state(state, campaign)
    repo = Path(state['repo']).resolve()
    entries = json.loads((repo / 'workspaces/topics.json').read_text()).get('topics', [])
    info = next((r for r in entries if r.get('id') == state['topic']), None)
    if not info or info.get('workspace') != state['config'].get('workspace'):
        raise ValueError('作业课题与本地任务登记不匹配')
    scope = (repo / info['workspace']).resolve()
    if not root.is_relative_to(campaign) or not campaign.is_relative_to(scope / 'runs'):
        raise ValueError('作业回执须在本课题登记运行内')
    if state['config'].get('workflow') != 'paper' or state['config'].get('backend') != 'codex':
        raise ValueError('只读或模拟调用没有实验作业执行授权；观测要求不会扩大权限')
    allowed = [scope]
    if info.get('paper_reserved'):
        allowed.append((repo / info['paper_reserved']).resolve())
    checkout = state['config'].get('implementation_checkout')
    if checkout:
        allowed.extend((Path(checkout).resolve() / p.relative_to(repo) for p in list(allowed)))
    if not cwd.is_dir() or not any((cwd.is_relative_to(p) for p in allowed)):
        raise ValueError('作业工作目录须属于回执对应的同一课题')
    return (repo, scope)

def run_job(root, argv, cwd, timeout, kind, target='local', remote_cwd=None, ssh_control_path=None):
    if kind not in ('acceptance', 'pilot', 'comparison', 'compile'):
        raise ValueError('需要明确的验收/先导/对照/编译类别')
    if not argv or type(timeout) is not int or timeout < 0:
        raise ValueError('需要命令argv与非负整数超时；0表示用户已授权不限时')
    (root, cwd) = (Path(root).resolve(), Path(cwd).resolve())
    if timeout == 0 and (not unrestricted_root(root)):
        raise ValueError('零超时须有当前运行的用户不限额授权')
    registered = registered_scope(root, cwd)
    if registered:
        (repo, scope) = registered
    else:
        raise ValueError('作业回执须属于本课题已登记并授权的运行')
    if target != 'local':
        raise ValueError('远端执行须配置本课题私有执行适配器；不得继承其他任务设备')
    dashboard = experiment_monitor.job_requirement(root, kind)
    directory = root / (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S-') + uuid.uuid4().hex[:8])
    directory.mkdir(parents=True, mode=448)
    command = list(argv)
    log = directory / 'console.log'
    receipt_path = directory / 'receipt.json'
    receipt = {'status': 'running', 'simulated': False, 'experiment_kind': kind,
               'target': target, 'argv': argv, 'executed_argv': command, 'cwd': str(cwd),
               'remote_cwd': remote_cwd, 'started_at': stamp(), 'timeout_seconds': timeout,
               'log_path': str(log), 'exit_code': None}
    if dashboard:
        receipt['dashboard'] = dashboard
    if timeout == 0:
        receipt['timeout_policy'] = execution_limits.VERSION
    write(receipt_path, receipt)
    started = time.monotonic()
    process = None
    previous_handler = signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        with log.open('wb') as output:
            process = subprocess.Popen(command, cwd=cwd, stdout=output, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
            receipt['pid'] = process.pid
            import ars
            receipt['child_process'] = ars.process_identity(process.pid)
            write(receipt_path, receipt)
            try:
                deadline = started + timeout + (25 if target != 'local' else 0) if timeout else None
                while True:
                    remaining = deadline - time.monotonic() if deadline else None
                    if remaining is not None and remaining <= 0:
                        raise subprocess.TimeoutExpired(command, timeout)
                    try:
                        code = process.wait(timeout=min(5, remaining) if remaining is not None else 5)
                        break
                    except subprocess.TimeoutExpired:
                        try:
                            receipt.update(observed_at=stamp(), wall_seconds=time.monotonic() - started, log_bytes=log.stat().st_size)
                            write(receipt_path, receipt)
                        except OSError as error:
                            receipt['monitor_warning'] = str(error)
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                code = 124
            receipt['exit_code'] = code
            receipt['status'] = 'unknown' if target != 'local' and code in (255, 124) else 'succeeded' if code == 0 else 'failed'
    except OSError as error:
        receipt.update(status='failed', error=str(error))
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        signal.signal(signal.SIGTERM, previous_handler)
        receipt.update(finished_at=stamp(), wall_seconds=time.monotonic() - started, observed_at=stamp(), log_bytes=log.stat().st_size if log.exists() else 0, log_sha256=hashlib.sha256(log.read_bytes() if log.exists() else b'').hexdigest())
        write(receipt_path, receipt)
    return (receipt_path, receipt)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--cwd', type=Path, required=True)
    parser.add_argument('--timeout', type=int, required=True)
    parser.add_argument('--kind', required=True, choices=['acceptance', 'pilot', 'comparison', 'compile'])
    parser.add_argument('--target', default='local', choices=['local', 'research-server'])
    parser.add_argument('--remote-cwd')
    parser.add_argument('--ssh-control-path', help='当前用户私有SSH复用socket路径；不接收密码')
    parser.add_argument('argv', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.argv[1:] if args.argv[:1] == ['--'] else args.argv
    (path, receipt) = run_job(args.root, command, args.cwd, args.timeout, args.kind, args.target, args.remote_cwd, args.ssh_control_path)
    print(json.dumps({'receipt': str(path), 'status': receipt['status'], 'exit_code': receipt['exit_code']}, ensure_ascii=False))
    raise SystemExit(0 if receipt['status'] == 'succeeded' else 1)
import local_extensions as _local_extensions
_local_extensions.apply(globals())
if __name__ == '__main__':
    main()
