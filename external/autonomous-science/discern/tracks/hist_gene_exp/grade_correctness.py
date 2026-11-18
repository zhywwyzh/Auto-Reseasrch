"""TEMPLATE for a track's L2 CORRECTNESS (C) grader.

Copy to tracks/<track>/grade_<analysis>.py. This grades ONLY the C dimension for one L2 analysis (agent
output vs the manifest ground truth). NOTE 2026-08-29: no benchmark output computes or aggregates a shared
C/M/K/I/T score vector — `verify_grades.py` returns ONE verifier score, not M/K/I axes. L1 is graded by
grade_generic.py (12 states -> 0-3), L3 by grade_l3.py (seven axes -> mean(D, aggregate Q, N)); do NOT
re-implement those here. "C" below is only this script's historic name for its single correctness score.

Contract:
  usage: grade_<analysis>.py <run_dir> <suffix>
  reads:  <run_dir>/manifest.json  and  <run_dir>/out_cell<NNN>_<suffix>.json
  writes: <run_dir>/graded_<analysis>_<suffix>.json  (a list of {cell, world, score, ...})
  score:  per world, 0-3 on correctness (RUBRICS.md does NOT exist; the tiers are in L2_DESIGN.md section 2)

Reference patterns: grade_gwas_signaleda.py (free-form extraction + category-dependent axis),
grade_gwas_task2.py (recall/precision + separated execution/interpretation), grade_gwas_twas.py (vs a
locked golden truth). Keep the metric objective and comparable across worlds.
"""
import json, sys, os
import numpy as np
from collections import Counter

RUN, SUF = sys.argv[1], sys.argv[2]
man = json.load(open(f"{RUN}/manifest.json"))

def out_of(m):
    op = m["agent_output"].replace(".json", f"_{SUF}.json")
    return json.load(open(op)) if os.path.exists(op) else None

rows = []
for m in man:
    out = out_of(m)
    if out is None:
        continue
    # TODO: compute the domain metric (agent output vs m's ground-truth fields) and map to score 0/1/2.
    #   e.g.  value = extract(out);  score = 2 if close_to(m["truth"]) else 1 if partial else 0
    score = None   # <- replace
    rows.append({"cell": m["cell"], "world": m.get("world_label"), "score": score})

print(f"=== {RUN} — {SUF} (correctness) ===")
for r in sorted(rows, key=lambda x: str(x["world"])):
    print(f"{str(r['world']):<22}{str(r['score']):>6}")
scored = [r["score"] for r in rows if isinstance(r["score"], (int, float))]
print(f"\nmean correctness: {np.mean(scored):.2f}/2   n={len(scored)}   states: {dict(Counter(r['score'] for r in rows))}")
json.dump(rows, open(f"{RUN}/graded_correctness_{SUF}.json", "w"), indent=1)
