"""Offline input/reference availability check. Never executes a model or builder."""
import csv
import json
from pathlib import Path
import task_spec
from release_paths import relocate

ROOT = Path(__file__).resolve().parent

def main():
    rows=list(csv.DictReader((ROOT/'verification/authority_index.csv').open()))
    missing_inputs, missing_refs = [], set()
    checked = 0
    for manifest in sorted({r['manifest'] for r in rows}):
        for cell in relocate(json.loads((ROOT/manifest).read_text())):
            for key in ('agent_input','agent_metadata','dossier','twas_csv','gold','golden_truth'):
                value=cell.get(key)
                if not isinstance(value,str): continue
                path=Path(value)
                if not path.is_absolute(): path=ROOT/path
                checked+=1
                if not path.exists(): missing_inputs.append({'manifest':manifest,'field':key,'path':value})
    def walk(track,obj):
        if isinstance(obj,dict):
            for k,v in obj.items():
                paths=v if k=='ro_paths' else [v] if k in ('software','model_db','cov') else []
                for item in paths:
                    if not Path(item).exists():
                        p=Path(item)
                        try: label=str(p.relative_to(ROOT))
                        except ValueError: label='external resource: '+p.name
                        missing_refs.add((track,label))
                walk(track,v)
        elif isinstance(obj,list):
            for v in obj: walk(track,v)
    tracks=sorted({r['track'] for r in rows})
    for track in tracks: walk(track,task_spec.load(track))
    report={'track_count':len(tracks),'input_references_checked':checked,
        'missing_inputs':missing_inputs,'missing_runtime_references':sorted(missing_refs),
        'note':'Existence checks only; not a sandbox execution or scientific validation.'}
    (ROOT/'verification/runtime_availability.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if missing_inputs or missing_refs: raise SystemExit(1)

if __name__=='__main__': main()
