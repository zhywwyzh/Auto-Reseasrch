"""Aggregate repeated runs into mean +/- SD (item 2: error bars).

The per-level graders are already suffix-driven, and run_level.py writes one output per repeat with suffix
`<model>_rep<r>`. So this just: (1) runs the right grader once per repeat, (2) loads the per-rep graded JSON,
(3) reports the headline score as mean +/- SD both per world and overall. No edits to the existing graders.

usage: aggregate_reps.py <run_dir> <grader> <model> <reps>
  grader in {generic, signaleda, task2, twas, l3}
"""
import json, sys, os, subprocess, statistics
from collections import defaultdict

RUN, GRADER, MODEL, REPS = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
VENV = sys.executable

# grader script, its graded-file prefix, the per-world score field, and the world key
G = {
    "generic":   ("grade_generic.py",        "graded",           "score",       "world"),
    "signaleda": ("grade_gwas_signaleda.py",  "graded_signaleda", "core_score",  "world"),
    "task2":     ("grade_gwas_task2.py",      "graded_task2",     "score",       "world"),
    "twas":      ("grade_gwas_twas.py",       "graded_twas",      "score",       "world"),
    "l3":        ("grade_l3.py",              "graded_l3",        "composite",   "world"),
}
if GRADER not in G:
    raise SystemExit(f"unknown grader '{GRADER}'. Options: {list(G)}")
script, prefix, field, wkey = G[GRADER]

per_world = defaultdict(list)          # world -> [score per rep]
n_ok = 0
for r in range(REPS):
    suf = f"{MODEL}_rep{r}"
    extra = ["gpt-5", MODEL, "3"] if GRADER == "l3" else []      # l3: judge, bench, k
    res = subprocess.run([VENV, script, RUN, suf, *extra], capture_output=True, text=True)
    gfile = f"{RUN}/{prefix}_{suf}.json"
    if not os.path.exists(gfile):
        print(f"  [rep{r}] no graded file ({gfile}); grader stderr tail:\n{res.stderr[-300:]}"); continue
    n_ok += 1
    for row in json.load(open(gfile)):
        v = row.get(field)
        if isinstance(v, (int, float)):
            per_world[row.get(wkey)].append(v)

def ms(xs):
    return (round(statistics.mean(xs), 3), round(statistics.stdev(xs), 3) if len(xs) > 1 else 0.0)

print(f"=== {RUN} — {GRADER} — {MODEL} — reps={REPS} (graded reps ok: {n_ok}/{REPS}) ===")
print(f"{'world':<24}{'mean':>8}{'SD':>8}{'n':>4}   draws")
world_means = []
for w in sorted(per_world):
    xs = per_world[w]; mean, sd = ms(xs); world_means.append(mean)
    print(f"{str(w):<24}{mean:>8}{sd:>8}{len(xs):>4}   {xs}")
if world_means:
    om, osd = ms(world_means)
    print(f"\nOVERALL {field}: mean={om} +/- {osd} (SD across per-world means, {len(world_means)} worlds)")
json.dump({"model": MODEL, "grader": GRADER, "reps": REPS, "field": field,
           "per_world": {w: per_world[w] for w in per_world},
           "overall_mean": (ms(world_means)[0] if world_means else None),
           "overall_sd": (ms(world_means)[1] if world_means else None)},
          open(f"{RUN}/aggregated_{GRADER}_{MODEL}.json", "w"), indent=1)
