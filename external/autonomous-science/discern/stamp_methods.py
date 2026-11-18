"""Stamp per-task content from task_spec into each run manifest, so the shared engines read it (not hardcode):
 - `expected_method` -> for the judge's actions/method axis.
 - `verify_rubric`   -> the per-task L2 verify rubric (from info["rubric"]); verify_grades reads this instead of
   a hardcoded dict, so verify_grades is a pure engine. L1 has no rubric -> verify_grades falls back to LADDER.
Idempotent. usage: stamp_methods.py [spec_name=cf_gwas]
"""
import json, sys, os
import task_spec as T

spec = T.load(sys.argv[1] if len(sys.argv) > 1 else "cf_gwas")
# spec-generic: L1 + every L2 sub-task (whatever the track named them) + L3 if present.
tasks = [spec["L1"], *spec.get("L2", {}).values()]
if spec.get("L3"):
    tasks.append(spec["L3"])
for t in tasks:
    method = t.get("expected_method")
    rubric = (t.get("info") or {}).get("rubric")
    mpath = f"{t['run_dir']}/manifest.json"
    if not ((method or rubric) and os.path.exists(mpath)):
        print(f"  [skip] {t['run_dir']} (nothing to stamp or no manifest)"); continue
    man = json.load(open(mpath))
    for w in man:
        if method: w["expected_method"] = method
        if rubric: w["verify_rubric"] = rubric
    json.dump(man, open(mpath, "w"), indent=1)
    print(f"  stamped {'method+rubric' if (method and rubric) else 'method' if method else 'rubric'} "
          f"into {len(man)} worlds -> {mpath}")
print("done")
