"""Trusted strategy boundary: immutable releases, isolated execution, safe fallback."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
FILES = ('runtime_policy.py', 'research_strategy.py')


def fingerprint(directory):
    root = Path(directory)
    hashes = {}
    for name in FILES:
        p = root / name
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 160000:
            raise ValueError('Invalid strategy file: ' + name)
        hashes[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def invoke(directory, requests, timeout=10):
    """No home, credentials, ledger, network or evaluator mounted in candidate process."""
    if not shutil.which('bwrap'):
        raise RuntimeError('bubblewrap is required to execute candidate strategies')
    root = Path(directory).resolve()
    fingerprint(root)
    argv = ['bwrap', '--unshare-all', '--die-with-parent', '--new-session', '--cap-drop', 'ALL',
            '--ro-bind', '/usr', '/usr', '--ro-bind', '/lib', '/lib',
            '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--dir', '/candidate']
    if Path('/lib64').exists():
        argv += ['--ro-bind', '/lib64', '/lib64']
    for name in FILES:
        argv += ['--ro-bind', str(root / name), '/candidate/' + name]
    argv += ['--ro-bind', str(HERE / 'strategy_worker.py'), '/worker.py', '--chdir', '/tmp',
             '/usr/bin/python3', '-I', '-B', '/worker.py']
    # A file bounds memory even if the candidate prints indefinitely. RLIMIT_FSIZE
    # applies in the worker; the parent never accumulates an unbounded pipe.
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        p = subprocess.run(argv, input=json.dumps(requests).encode(), stdout=output, stderr=errors,
                           timeout=timeout, env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'})
        output.seek(0); raw = output.read(1024**2 + 1)
        if p.returncode or len(raw) > 1024**2:
            errors.seek(0)
            raise ValueError('Strategy process rejected: ' + errors.read(2000).decode(errors='replace'))
        result = json.loads(raw)
        if not isinstance(result, list) or len(result) != len(requests):
            raise ValueError('Strategy response shape mismatch')
        return result


def active_release():
    path = HERE / 'runs/evolution/active.json'
    if not path.exists():
        return None
    value = json.loads(path.read_text())
    root = (HERE / 'runs/evolution/versions' / value['version']).resolve()
    if not root.is_relative_to((HERE / 'runs/evolution/versions').resolve()):
        raise ValueError('Invalid release path')
    if fingerprint(root) != value['digest']:
        raise ValueError('Active release hash mismatch')
    return value | {'directory': str(root)}


def call(function, args, release=None):
    """Caller validates semantics. Failed candidates never take over the kernel."""
    if release:
        root = Path(release['directory'])
        if fingerprint(root) != release['digest']:
            raise ValueError('Pinned release changed')
        return invoke(root, [{'function': function, 'args': args}])[0]
    import runtime_policy
    import research_strategy
    module = research_strategy if function in ('task_guidance', 'improvement_prompt') else runtime_policy
    return getattr(module, function)(*args)
