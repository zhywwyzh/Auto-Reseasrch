"""Refresh release checksums from Git's tracked + nonignored file selection."""
from pathlib import Path
import subprocess
from prepare_runtime_release import sha

ROOT=Path(__file__).resolve().parent
paths=sorted(set(subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()))
lines=[]
for name in paths:
    if name=='MANIFEST.sha256':continue
    p=ROOT/name
    if p.is_symlink():
        if not p.resolve().is_relative_to(ROOT):raise SystemExit('External symlink: '+name)
        # Directory aliases are checked separately; their targets are indexed once.
        if p.is_dir():continue
    if p.is_file():lines.append(f'{sha(p)}  ./{name}\n')
(ROOT/'MANIFEST.sha256').write_text(''.join(lines))
print(f'Indexed {len(lines)} release files.')
