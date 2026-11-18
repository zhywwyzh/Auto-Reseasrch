"""Reduce each L1/L2 manifest to n=1 per task (issue-type): pick ONE cell per world_label, FROZEN with a
fixed seed so the SAME instantiation is used for every model (fair cross-model comparison). Error bars then
come from the spread ACROSS tasks within a level (mean +/- SD over the issue-types), not within a task.

Reversible: the full n=3 manifest is backed up to manifest_full.json; the n=1 subset becomes manifest.json
(runners/graders read manifest.json). Cell numbers are preserved, so already-run outputs (e.g. claude-opus-5)
for the selected cells are reused as-is -- no re-run of those. Records the choice in n1_selection.json.

usage:  python select_n1.py [--apply]   (default = dry-run preview; --apply writes the subset manifests)
"""
import json, os, sys, random
from collections import defaultdict

RUN_DIRS = ["results/gwas_qc_run", "results/gwas_signaleda_run",
            "results/gwas_task2_run", "results/gwas_twas_run"]
SEED = 0                       # frozen selection -> reproducible + identical across models
APPLY = "--apply" in sys.argv
CHECK_MODEL = "claude-opus-5"  # report which selected cells are already run (reusable)

rng = random.Random(SEED)
for rd in RUN_DIRS:
    man_path = f"{rd}/manifest.json"
    full_path = f"{rd}/manifest_full.json"
    src = full_path if os.path.exists(full_path) else man_path      # idempotent: always subset from the FULL set
    man = json.load(open(src))
    by_label = defaultdict(list)
    for m in man:
        by_label[m.get("world_label", m.get("issue_type", m.get("task")))].append(m)
    picked, sel_log = [], {}
    for label in sorted(by_label):                                  # sorted -> deterministic with the seed
        choice = rng.choice(by_label[label])
        picked.append(choice); sel_log[label] = choice["cell"]
    picked.sort(key=lambda m: m["cell"])
    # reuse check against an already-run model
    reused = sum(os.path.exists(m["agent_output"].replace(".json", f"_{CHECK_MODEL}.json")) for m in picked)
    print(f"{rd:<32} {len(man)} -> {len(picked)} tasks | picks(cell): "
          f"{ {k: sel_log[k] for k in list(sel_log)[:11]} } | {CHECK_MODEL} reusable: {reused}/{len(picked)}")
    if APPLY:
        if not os.path.exists(full_path):
            json.dump(man, open(full_path, "w"), indent=1)          # back up the full n=3 set once
        json.dump(picked, open(man_path, "w"), indent=1)            # n=1 subset becomes the active manifest
        json.dump({"seed": SEED, "selection": sel_log}, open(f"{rd}/n1_selection.json", "w"), indent=1)

print("\n" + ("APPLIED: manifest.json is now n=1 (full set in manifest_full.json)." if APPLY
              else "DRY-RUN: re-run with --apply to write the subsets."))
