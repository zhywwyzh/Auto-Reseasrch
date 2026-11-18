"""Refresh model-neutral indexes and release integrity checks, without regrading."""
import csv
import hashlib
import json
import re
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def main():
    rows = list(csv.DictReader((ROOT/'verification/authority_index.csv').open()))
    models = sorted({r['model'] for r in rows} | {'claude-fable-5'})
    manifests = sorted({r['manifest'] for r in rows})
    index = {}
    for model in models:
        artifacts = sorted(str(p.relative_to(ROOT)) for m in manifests
            for p in (ROOT/m).parent.glob(f'*{model}*.json'))
        sources = sorted({r['aggregate_authority'] for r in rows if r['model'] == model})
        rollup = ROOT/'results/model_reports'/f'ROLLUP_{model}.json'
        if rollup.exists():
            sources.append(str(rollup.relative_to(ROOT)))
        index[model] = {'recorded_artifacts': artifacts, 'score_authority': sources,
            'coverage_note': 'Do not infer completion from artifact count; consult eligibility, refusal status and finalized scores.'}
    dest = ROOT/'results/models'; dest.mkdir(exist_ok=True)
    (dest/'index.json').write_text(json.dumps({'models':index,
        'fallback_replay': 'results/model_reports/FALLBACK_REPLAY_claude-fable-5_to_claude-opus-5.json',
        'note':'Models use one schema. Original scores and ledgers remain authoritative; this index does not regrade.'}, indent=2)+'\n')
    # Replace the original concatenated, non-TSV source policy with a real table.
    headings = {'bulk_rnaseq':'Bulk RNA-seq','cf_gwas':'Counterfactual GWAS',
        'clinvar_acmg':'ClinVar / ACMG','crispr_screen':'CRISPR',
        'enhancer_activity':'Enhancer','hist_gene_exp':'Histone','protein_ddg':'Protein',
        'scrna':'Single-cell','calorimetry':'Calorimetry','nuclear_decay':'Nuclear'}
    sections = (ROOT/'DATA_SOURCES_AND_LICENSES.md').read_text().split('\n### ')[1:]
    runtime = list(csv.DictReader((ROOT/'verification/runtime_files.csv').open()))
    with (ROOT/'SOURCE_DATA_POLICY.tsv').open('w',newline='') as f:
        fields=['track','upstream_links','construction_data_policy','runtime_files_indexed','redistribution_status']
        w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',lineterminator='\n'); w.writeheader()
        for track in sorted({r['track'] for r in rows}):
            matches=[s for s in sections if s.split('\n',1)[0].lower().startswith(headings[track].lower())]
            links=sorted(set(re.findall(r'https?://[^\s)]+','\n'.join(matches))))
            w.writerow({'track':track,'upstream_links':'; '.join(links),
                'construction_data_policy':'link-only; see DATA_SOURCES_AND_LICENSES.md',
                'runtime_files_indexed':sum(r['path'].startswith(f'tracks/{track}/') for r in runtime),
                'redistribution_status':'review staged runtime payloads before upload'})
    # Check every existing score, trace and manifest against its original Git blob.
    tracked = subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD'], cwd=ROOT,text=True).splitlines()
    cleanup_path=ROOT/'verification/identity_cleanup.json'
    cleanup={r['path']:r for r in json.loads(cleanup_path.read_text())} if cleanup_path.exists() else {}
    checked, changed, redacted = 0, [], []
    for rel in tracked:
        if not (rel.startswith(('results/','tracks/','verification/')) and rel.endswith(('.json','.csv'))):
            continue
        path = ROOT/rel
        if not path.exists():
            changed.append(rel); continue
        actual = subprocess.check_output(['git','hash-object',str(path)],cwd=ROOT,text=True).strip()
        original = subprocess.check_output(['git','rev-parse',f'HEAD:{rel}'],cwd=ROOT,text=True).strip()
        checked += 1
        if actual != original:
            entry=cleanup.get(rel)
            if entry and rel.endswith('.trace.json') and entry['kind']=='text_identity_redaction':
                old=subprocess.check_output(['git','show',f'HEAD:{rel}'],cwd=ROOT)
                from clean_release_identity import numeric_tree
                if (hashlib.sha256(old).hexdigest()==entry['before_sha256']
                        and digest(path)==entry['after_sha256']
                        and numeric_tree(json.loads(old))==numeric_tree(json.loads(path.read_text()))):
                    redacted.append(rel); continue
            changed.append(rel)
    report = {'original_record_files_checked':checked,'changed_original_records':changed,
              'logged_identity_only_trace_redactions':redacted,
              'model_ids':models,'live_model_calls':0,
              'fresh_execution_validated':False,
              'publication_ready':False}
    (ROOT/'verification/release_update_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if changed:
        raise SystemExit('Original records changed; investigate before release')

if __name__ == '__main__': main()
