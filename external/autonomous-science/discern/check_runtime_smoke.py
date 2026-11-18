"""Offline representative input-loading and isolation smoke test, not a rerun.

Checks the first recorded world in each authority-index manifest in a fresh sealed
sandbox. Mounts only its selected agent input, never gold, manifests or results.
Parses structured inputs and samples tables/binary readers; this is not full
scientific execution, checkpoint inference, or exhaustive input validation.
"""
import csv
import json
from pathlib import Path
import sys
import tempfile

from release_paths import ROOT, relocate
from sandbox_seal import run_sealed


PROBE = r'''
import gzip, json, os, tarfile
from pathlib import Path
import numpy, pandas as pd, pysam, pyBigWig
from Bio.PDB import PDBParser

assert not Path(forbidden).exists(), 'evaluator files visible'
assert not any(k.endswith('API_KEY') for k in os.environ), 'API credential inherited'
files = sorted(source.rglob('*')) if source.is_dir() else [source]
counts = {}
for p in files:
    if not p.is_file(): continue
    name = p.name.lower()
    kind = 'text'
    if name.endswith('.json'):
        json.loads(p.read_text()); kind = 'json'
    elif name.endswith(('.tar.gz', '.tgz')):
        with tarfile.open(p) as archive:
            members = [m for m in archive if m.isfile()]
            assert members
            for member in members:
                with archive.extractfile(member) as f: f.read(1024)
        kind = 'tar_members_sampled'
    elif name.endswith(('.csv', '.csv.gz', '.tsv', '.tsv.gz')):
        sep = '\t' if '.tsv' in name else ','
        pd.read_csv(p, sep=sep, nrows=2); kind = 'table_sampled'
    elif name.endswith('.xlsx'):
        pd.read_excel(p, nrows=2); kind = 'xlsx_sampled'
    elif name.endswith(('.vcf', '.vcf.gz')):
        with pysam.VariantFile(str(p)) as f: next(iter(f), None)
        kind = 'vcf_sampled'
    elif name.endswith('.bam'):
        with pysam.AlignmentFile(str(p), 'rb') as f:
            assert f.references
            next(f.fetch(until_eof=True), None)
        kind = 'bam_sampled'
    elif name.endswith(('.bw', '.bigwig')):
        with pyBigWig.open(str(p)) as f: assert f.chroms()
        kind = 'bigwig_header'
    elif name.endswith('.pdb'):
        PDBParser(QUIET=True).get_structure('input', p); kind = 'pdb'
    elif name.endswith('.bai'):
        with p.open('rb') as f: assert f.read(4) == b'BAI\x01'
        kind = 'bam_index_header'
    elif name.endswith('.gz'):
        with gzip.open(p, 'rb') as f: f.read(1024)
        kind = 'gzip_sampled'
    else:
        with p.open('rb') as f: f.read(1024)
        kind = 'bytes_sampled'
    counts[kind] = counts.get(kind, 0) + 1
assert counts, 'no input files checked'
print(json.dumps(counts, sort_keys=True))
'''


def main():
    with (ROOT / 'verification/authority_index.csv').open() as f:
        manifests = sorted({r['manifest'] for r in csv.DictReader(f)})
    outcomes = []
    for manifest in manifests:
        cells = relocate(json.loads((ROOT / manifest).read_text()))
        cell = cells[0]
        source = Path(cell.get('agent_input') or cell['dossier'])
        if not source.is_absolute(): source = ROOT / source
        header = 'from pathlib import Path\n'
        header += f'source = Path({str(source)!r})\n'
        header += f'forbidden = {str(ROOT / "verification/authority_index.csv")!r}\n'
        with tempfile.TemporaryDirectory(prefix='discern_smoke_') as work:
            out, ok = run_sealed(sys.executable, header + PROBE, work, 180,
                                 ro_paths=[str(source)],
                                 env_extra={'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'})
        # Normalize diagnostic paths before writing public validation metadata.
        out = out.replace(str(ROOT), '/workspace/discern-benchmark')
        row = {'manifest': manifest, 'passed': ok, 'output': out.strip()}
        outcomes.append(row)
        print(('PASS ' if ok else 'FAIL ') + manifest, flush=True)
    report = {'scope': __doc__.strip(), 'network': 'disabled by bubblewrap',
              'model_api_calls': 0, 'manifest_count': len(manifests),
              'passed': all(r['passed'] for r in outcomes), 'checks': outcomes}
    (ROOT / 'verification/runtime_smoke.json').write_text(json.dumps(report, indent=2) + '\n')
    if not report['passed']: raise SystemExit(1)


if __name__ == '__main__': main()
