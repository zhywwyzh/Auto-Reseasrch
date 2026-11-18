"""Remove local account paths from newly added text files only; log byte hashes.

This is a path anonymization pass, not a complete identity or secret audit.
Existing release records are never modified. Review the generated ledger before
publication. Re-run the packager afterwards to refresh input checksums.
"""
import getpass
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent

def main():
    user = getpass.getuser()
    replacements = {}
    for base in ('/home/', '/data/'):
        replacements[base+user+'/genomic_discovery_gym/gwas_counterfactual_benchmark'] = '/workspace/discern-benchmark'
        replacements[base+user] = base+'anonymous'
    paths = subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    changes = []
    for rel in paths:
        p = ROOT/rel
        if p.is_symlink() or p.suffix not in {'.json','.py','.txt','.md','.csv','.tsv'}:
            continue
        try:
            before = p.read_text()
        except UnicodeError:
            continue
        after = before
        for src,dst in replacements.items():
            after = after.replace(src,dst)
        if after == before:
            continue
        p.write_text(after)
        changes.append({'path':rel,'before_sha256':hashlib.sha256(before.encode()).hexdigest(),
                        'after_sha256':hashlib.sha256(after.encode()).hexdigest()})
    ledger = ROOT/'verification/path_anonymization.json'
    previous = json.loads(ledger.read_text()) if ledger.exists() else []
    ledger.write_text(json.dumps(previous+changes,indent=2)+'\n')
    print(f'Path-anonymized {len(changes)} new text files; existing release records untouched.')

if __name__ == '__main__': main()
