"""Stage runtime inputs from a private benchmark checkout; never uploads anything.

Uses the existing release authority index as the run allowlist, not a glob of all
experiments. Original release records are never overwritten. Construction-only
raw data are not copied. New payloads require redistribution review before push.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
INPUT_KEYS = {'agent_input', 'agent_metadata', 'dossier', 'twas_csv', 'gold', 'golden_truth'}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', required=True, type=Path)
    ap.add_argument('--reference-fasta', type=Path)
    ap.add_argument('--esm-checkpoints', type=Path)
    args = ap.parse_args()
    source = args.source.resolve()
    rows = list(csv.DictReader((ROOT / 'verification/authority_index.csv').open()))
    manifests = sorted({r['manifest'] for r in rows})
    records, missing, added = {}, [], []
    def copy_path(rel, role):
        rel = Path(rel)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError(f'Unsafe relative path: {rel}')
        src = source / rel
        if not src.exists():
            missing.append({'path': str(rel), 'role': role})
            return
        files = sorted(src.rglob('*')) if src.is_dir() else [src]
        for f in files:
            if not f.is_file() or '__pycache__' in f.parts:
                continue
            relative = f.relative_to(source)
            dst = ROOT / relative
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst)
                added.append(str(relative))
            records[str(relative)] = dict(path=str(relative), role=role,
                bytes=dst.stat().st_size, sha256=sha(dst))
    for manifest in manifests:
        cells = json.loads((ROOT / manifest).read_text())
        for cell in cells:
            for key in INPUT_KEYS:
                value = cell.get(key)
                if not isinstance(value, str):
                    continue
                if '/discern-benchmark/' in value:
                    copy_path(value.split('/discern-benchmark/', 1)[1], key)
                elif value.startswith('tracks/'):
                    copy_path(value, key)
        # Fable uses the same per-run artifact layout and same task definitions.
        run = Path(manifest).parent
        for f in sorted((source / run).glob('*claude-fable-5*.json')):
            copy_path(f.relative_to(source), 'recorded_model_artifact')
    # Shared, agent-visible dependencies, not complete source collections.
    for rel in (
        'tracks/clinvar_acmg/L2/l2/resources',
        'tracks/cf_gwas/L2/predictdb_gtex_v8/eqtl/mashr/mashr_Lung.db',
        'tracks/cf_gwas/L2/predictdb_gtex_v8/eqtl/mashr/mashr_Lung.txt.gz',
    ):
        copy_path(rel, 'runtime_reference')
    for track in sorted({r['track'] for r in rows}):
        for name in ('data_dictionary.json', 'study_metadata.json'):
            rel = Path('tracks') / track / 'data' / name
            if (source / rel).exists():
                copy_path(rel, 'runtime_documentation')
    # Match documentation locations actually requested by each task spec.
    import task_spec
    for track in sorted({r['track'] for r in rows}):
        spec = task_spec.load(track)
        for name in spec.get('docs', []):
            doc = Path(spec['docs_dir']) / name
            try:
                rel = doc.relative_to(ROOT)
            except ValueError:
                continue
            copy_path(rel, 'runtime_documentation')
        def references(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == 'ro_paths':
                        for item in value:
                            try:
                                rel = Path(item).relative_to(ROOT)
                            except ValueError:
                                continue
                            if str(rel).startswith('tracks/'):
                                copy_path(rel, 'runtime_reference')
                    references(value)
            elif isinstance(obj, list):
                for item in obj:
                    references(item)
        references(spec)
    external = []
    if args.reference_fasta:
        external += [(args.reference_fasta, Path('resources/hg38.fa')),
                     (Path(str(args.reference_fasta)+'.fai'), Path('resources/hg38.fa.fai'))]
    if args.esm_checkpoints:
        for model in ('esm2_t30_150M_UR50D', 'esm2_t33_650M_UR50D'):
            for suffix in ('.pt','-contact-regression.pt'):
                external.append((args.esm_checkpoints/(model+suffix),
                                 Path('resources/torch/hub/checkpoints')/(model+suffix)))
    for src, rel in external:
        if not src.is_file():
            missing.append({'path':str(rel),'role':'runtime_reference'}); continue
        dst=ROOT/rel
        if not dst.exists():
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst); added.append(str(rel))
        records[str(rel)]={'path':str(rel),'role':'runtime_reference',
                          'bytes':dst.stat().st_size,'sha256':sha(dst)}
    # Preserve indexing on subsequent runs when external sources aren't provided.
    for dst in sorted((ROOT/'resources').rglob('*')):
        if dst.is_file():
            rel=str(dst.relative_to(ROOT))
            if rel not in records:
                records[rel]={'path':rel,'role':'runtime_reference',
                              'bytes':dst.stat().st_size,'sha256':sha(dst)}
    out = ROOT / 'verification/runtime_files.csv'
    with out.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['path', 'role', 'bytes', 'sha256'])
        w.writeheader(); w.writerows(records[k] for k in sorted(records))
    (ROOT / 'verification/runtime_staging.json').write_text(json.dumps({
        'manifest_count': len(manifests), 'indexed_file_count': len(records),
        'indexed_bytes': sum(r['bytes'] for r in records.values()),
        'missing': missing, 'new_files': added,
        'publication_status': 'local staging only; redistribution and anonymity review required',
    }, indent=2) + '\n')
    print(json.dumps({'manifests': len(manifests), 'indexed_files': len(records),
                      'new_files': len(added), 'missing': missing}, indent=2))

if __name__ == '__main__':
    main()
