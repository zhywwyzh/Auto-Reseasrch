"""Run one bounded CPU probe; no server access, GPU access or paid API."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import os
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--execute', action='store_true', help='Explicitly execute the bounded validation')
parser.add_argument('--source', type=Path, default=ROOT / 'thesis-reference/notes/thesis-uav-crowdsensing/deep-research-2026-11-10/DRL-MTVCS')
args = parser.parse_args()
protocol = json.loads((HERE / 'protocol.json').read_text())
if not args.execute:
    print(json.dumps(protocol, ensure_ascii=False, indent=2))
    raise SystemExit(0)
source = args.source.resolve()
head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
if head != protocol['source_commit']:
    raise SystemExit('Upstream commit differs from the reviewed protocol.')
if subprocess.check_output(['git', '-C', str(source), 'diff', '--name-only'], text=True).strip():
    raise SystemExit('Upstream has modified tracked files; review before probing.')
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out = HERE.parent / 'runs' / ('cpu-smoke-' + stamp)
out.mkdir(parents=True)
name = 'tr001-cpu-smoke-' + stamp.lower()
image = subprocess.check_output(['docker', 'image', 'inspect', 'tr001-cpu-smoke:v1', '--format', '{{.Id}}'], text=True).strip()
command = ['docker', 'run', '--rm', '--name', name, '--network', 'none', '--cpus', '2',
           '--memory', '3g', '--memory-swap', '3g', '--pids-limit', '128', '--read-only',
           '--tmpfs', '/tmp:rw,nosuid,size=128m', '--cap-drop', 'ALL',
           '--security-opt', 'no-new-privileges', '--user', str(os.getuid())+':'+str(os.getgid()),
           '-e', 'HOME=/tmp', '-v', str(source)+':/upstream:ro', '-v', str(HERE)+':/probe:ro',
           '-v', str(out)+':/run:rw', image, 'python', '/probe/run_cpu_smoke.py']
manifest = {'started_utc': stamp, 'source_commit': head, 'image_id': image, 'command': command,
            'files_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in HERE.iterdir() if p.is_file()}, 'protocol': protocol}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
started = time.monotonic()
with (out / 'console.log').open('w') as log:
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    try:
        code = process.wait(timeout=300)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        subprocess.run(['docker', 'stop', '--time', '3', name], stdout=log, stderr=log)
        process.wait(timeout=15)
        code = 124
manifest.update(exit_code=code, wall_seconds=time.monotonic()-started)
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
print(json.dumps({'run': str(out), 'exit_code': code, 'wall_seconds': manifest['wall_seconds']}, indent=2))
raise SystemExit(code)
