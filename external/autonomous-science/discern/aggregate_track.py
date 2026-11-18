#!/usr/bin/env python3
"""Track-level aggregation — the CHAIN is weakest-link (PAPER_NOTES §3b).

Per-track score = GEOMETRIC MEAN of the normalized level means, rescaled to [0,3]:
    track = 3 * (L1/3 * L2/3 * L3/3) ** (1/3)
This compounds: any weak level drags the track down; a collapsed level (->0) tanks it -- the correct
pipeline semantics (an agent that fails L1 cannot buy it back with slick L2/L3 on garbage). Precedent:
series-system reliability R=prod(R_i); HotpotQA joint EM/F1 and MultiWOZ joint-goal (multiply dependent
sub-scores); Fleming & Wallace CACM'86 (geometric mean is the correct scale for normalized ratios).

Within a level, sub-tasks are PARALLEL (independent analyses) -> arithmetic mean.
Across tracks, tracks are independent -> OVERALL = arithmetic mean over tracks.
Always report the (L1,L2,L3) triple beside the scalar (HELM: don't collapse the profile).

Reads results/final_scores.json (field: mean_final). GWAS L3 is injected from PAPER_NOTES P5 (CF-mean,
confounded cells already excluded per model) since it is not in final_scores.json.
usage: aggregate_track.py [--l3 cf|full]   (full = mean over real+cf worlds, DEFAULT since 2026-08-12;
       cf = counterfactual-mean only, kept as the reported trust-vs-prior SLICE. The PENDING cf-mean
       question is RESOLVED: the real/clean world counts in the L3 aggregate now that the abstention
       D-gate scores real-world calibrated holds on merit (target_gene gate) — generativity on real
       data is part of the L3 skill, not just prior-override.)
"""
import json, os, sys
from math import prod

ROOT = os.path.dirname(os.path.abspath(__file__))
FS = json.load(open(os.path.join(ROOT, "results", "final_scores.json")))["levels"]
MODELS = ["claude-opus-5", "gpt-5.6-sol", "glm-5.2", "deepseek-v4-pro", "kimi-k3", "gpt-4.1"]

# level -> list of final_scores keys (L2 sub-tasks arithmetic-averaged). L3 for GWAS injected below.
TRACKS = {
    "GWAS":    {"L1": ["GWAS L1"], "L2": ["GWAS L2 signal-eda", "GWAS L2 locus", "GWAS L2 twas"], "L3": ["GWAS L3"]},
    "clinvar": {"L1": ["clinvar L1"], "L2": ["clinvar L2 classify", "clinvar L2 prioritize", "clinvar L2 sf"], "L3": ["clinvar L3"]},
}


def level_mean(keys, model):
    """Arithmetic mean of mean_final across the (parallel) sub-task keys for one model; None if missing."""
    vals = []
    for k in keys:
        cell = FS.get(k, {}).get(model)
        if isinstance(cell, dict) and cell.get("mean_final") is not None:
            vals.append(float(cell["mean_final"]))
    return sum(vals) / len(vals) if vals else None


def l3_mean(track, model, mode):
    cell = FS.get(TRACKS[track]["L3"][0], {}).get(model, {})
    if mode == "cf" and cell.get("mean_counterfactual") is not None:
        return float(cell["mean_counterfactual"])
    return float(cell["mean_final"]) if cell.get("mean_final") is not None else None


def geo(levels):
    """Geometric mean of level means, each normalized /3, rescaled *3. None if any level missing."""
    if any(v is None for v in levels):
        return None
    return 3.0 * prod(v / 3.0 for v in levels) ** (1.0 / len(levels))


def main():
    mode = "full"                        # DEFAULT full (real+cf) since 2026-08-12; --l3 cf for the slice
    if "--l3" in sys.argv:
        mode = sys.argv[sys.argv.index("--l3") + 1]
    print(f"# Track-level aggregation  (L3 = {'counterfactual-mean' if mode=='cf' else 'full L3 mean'})\n")
    overall = {m: [] for m in MODELS}
    for track in TRACKS:
        print(f"## {track}")
        print(f"{'model':<17}{'L1':>6}{'L2':>6}{'L3':>6}   {'GEO(track)':>11}   {'[arith cf]':>10}")
        rows = []
        for m in MODELS:
            L1 = level_mean(TRACKS[track]["L1"], m)
            L2 = level_mean(TRACKS[track]["L2"], m)
            L3 = l3_mean(track, m, mode)
            g = geo([L1, L2, L3])
            a = (sum([L1, L2, L3]) / 3.0) if None not in (L1, L2, L3) else None
            rows.append((m, L1, L2, L3, g, a))
            if g is not None:
                overall[m].append(g)
            f = lambda x: f"{x:.2f}" if x is not None else "  --"
            print(f"{m:<17}{f(L1):>6}{f(L2):>6}{f(L3):>6}   {f(g):>11}   {f(a):>10}")
        print()
    print("## OVERALL (arithmetic mean of GEO track scores; tracks are independent)")
    for m in MODELS:
        gs = overall[m]
        o = sum(gs) / len(gs) if gs else None
        print(f"{m:<17}{('%.2f'%o) if o else '--':>6}   (from {len(gs)} tracks)")


if __name__ == "__main__":
    main()
