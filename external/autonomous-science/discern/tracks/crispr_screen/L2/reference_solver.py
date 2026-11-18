#!/usr/bin/env python3
"""REFERENCE SOLVER for crispr_screen L2 — single source of truth for the golden + solver-first fire-checks.

RE-AUTHORED 2026-08-12 (see RECOVERY_NOTE.md): the canonical source was lost when the quarantined HAP1 scan
overwrote it; this reconstruction imports the canonical l2_common (module/.pyc), regenerates the byte-verified
gold/golden_{scores,essential,context}.csv + gold/gold_solver.json, and asserts every trap FIRES (naive default
silently wrong, robust move recovers). Deterministic (l2_common RNG_SEED) so the gold reproduces exactly. Exits
NON-ZERO on any failure — world_builder.py refuses to run on a failing gold file. Run with the bench venv.

  python reference_solver.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import l2_common as C

HERE = Path(__file__).parent
GOLD_DIR = HERE / "gold"
GOLD_DIR.mkdir(exist_ok=True)

CHECKS = []
def check(name, ok, detail):
    CHECKS.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def _recovered(scores, genes, truth, thr):
    """How many affected genes each method gets RIGHT vs the CEG/NEG truth."""
    ess = truth.startswith("essential")
    naive = scores.mean_lfc.loc[genes] < -1.0
    med = scores.median_lfc.loc[genes] < -1.0
    bf = scores.bf.loc[genes] > thr
    best = scores.best_lfc.loc[genes] < -1.0
    ok = (lambda call: int((call == ess).sum()))
    return {"naive_mean": ok(naive), "median": ok(med), "bf": ok(bf), "best_guide": ok(best), "n": len(genes)}


def solve_scoring():
    counts = C.load_counts(); ceg, neg = C.load_gene_lists()
    base = C.gene_scores(counts, ceg, neg); thr = C.essential_threshold(base)
    lab = base[base.is_ceg | base.is_neg]
    from sklearn.metrics import roc_auc_score
    au = roc_auc_score(lab.is_ceg.astype(int), lab.bf)
    check("scoring clean solvable", au > 0.95, f"clean CEG-vs-NEG AUROC(BF)={au:.3f} (correct tool separates)")
    base.reset_index().rename(columns={"index": "gene"}).to_csv(GOLD_DIR / "golden_scores.csv", index=False)
    g = {"clean": {"auroc_bf": round(float(au), 4), "n_essential": int((base.bf > thr).sum()),
                   "essential_thr": round(thr, 3)},
         "golden_csv": str(GOLD_DIR / "golden_scores.csv"), "essential_thr": round(thr, 3)}

    de, i1 = C.inj_guide_efficiency(counts, ceg); s1 = C.gene_scores(de, ceg, neg)
    r1 = _recovered(s1, i1["genes"], i1["truth"], thr)
    check("scoring guide_efficiency fires",
          r1["naive_mean"] <= r1["n"] * 0.5 and r1["best_guide"] >= r1["n"] * 0.9,
          f"dead-guide dilution: naive gene-MEAN recovers {r1['naive_mean']}/{r1['n']} real essentials, "
          f"best-guide {r1['best_guide']}/{r1['n']}, BF {r1['bf']}/{r1['n']}")
    g["guide_efficiency"] = {"affected": i1["genes"], "truth": i1["truth"], **r1}

    dp, i3 = C.inj_off_target_promiscuous(counts, neg); s3 = C.gene_scores(dp, ceg, neg)
    r3 = _recovered(s3, i3["genes"], i3["truth"], thr)
    drop_ok = 0
    for gene in i3["genes"]:
        keep = dp[(dp.gene == gene) & (~dp.sgRNA.isin(i3["promiscuous_guides"][gene]))]
        drop_ok += int(C.guide_lfc(keep)["mean"].median() >= -1.0)
    check("scoring off_target_promiscuous fires (median FAILS, alignment needed)",
          r3["median"] <= r3["n"] * 0.5 and drop_ok >= len(i3["genes"]) * 0.8,
          f"two promiscuous guides: robust MEDIAN still wrong ({r3['median']}/{r3['n']} correct); "
          f"dropping the alignment-flagged guides recovers {drop_ok}/{len(i3['genes'])}")
    g["off_target_promiscuous"] = {"affected": i3["genes"], "truth": i3["truth"],
                                   "promiscuous_guides": i3["promiscuous_guides"], "median_correct": r3["median"],
                                   "drop_flagged_correct": drop_ok, "n": r3["n"]}
    return g


def solve_calling():
    counts = C.load_counts(); ceg, neg = C.load_gene_lists()
    base = C.gene_scores(counts, ceg, neg); thr = C.essential_threshold(base)
    ess = C.call_essential(base, thr)
    out = base.assign(essential=ess).reset_index().rename(columns={"index": "gene"})
    out[["gene", "bf", "mean_lfc", "essential", "is_ceg", "is_neg"]].to_csv(GOLD_DIR / "golden_essential.csv", index=False)
    rec = (ess & base.is_ceg).sum() / base.is_ceg.sum()
    g = {"clean": {"n_essential": int(ess.sum()), "ceg_recall": round(float(rec), 4),
                   "neg_false": int((ess & base.is_neg).sum()), "essential_thr": round(thr, 3)},
         "golden_csv": str(GOLD_DIR / "golden_essential.csv"), "essential_thr": round(thr, 3)}

    mu, sd = base.mean_lfc.mean(), base.mean_lfc.std()
    z_all = (base.mean_lfc - mu) / sd
    rec_all = ((z_all < -2) & base.is_ceg).sum() / base.is_ceg.sum()
    check("calling null_calibration fires",
          rec_all < 0.85 and rec > 0.95,
          f"ALL-GENE null z<-2 silently misses essentials (CEG recall {rec_all:.3f}) vs NEG-anchored "
          f"null ({rec:.3f}); all-gene sd={sd:.2f} inflated by the essentials in the pool (NEG sd="
          f"{base.loc[base.is_neg,'mean_lfc'].std():.2f})")
    g["null_calibration"] = {"ceg_recall_allgene_null": round(float(rec_all), 4),
                             "ceg_recall_neg_null": round(float(rec), 4)}

    dr, ir = C.inj_replicate_irreproducible(counts, neg); sr = C.gene_scores(dr, ceg, neg)
    pooled_wrong = int((sr.mean_lfc.loc[ir["genes"]] < -1.0).sum())
    repaware_wrong = int(C.rep_concordant(sr).loc[ir["genes"]].sum())
    check("calling replicate_irreproducible fires",
          pooled_wrong >= len(ir["genes"]) * 0.4 and repaware_wrong <= len(ir["genes"]) * 0.2,
          f"one-replicate depletion: pooled MEAN wrongly essential {pooled_wrong}/{len(ir['genes'])}; "
          f"rep-concordance(>=2/3) wrongly essential {repaware_wrong}/{len(ir['genes'])}")
    g["replicate_irreproducible"] = {"affected": ir["genes"], "truth": "non-essential",
                                     "pooled_wrong": pooled_wrong, "repaware_wrong": repaware_wrong,
                                     "n": len(ir["genes"])}

    n_at = {c: int((base.mean_lfc < c).sum()) for c in (-0.5, -1.0, -1.5)}
    swing = (n_at[-0.5] - n_at[-1.5]) / max(1, n_at[-1.0])
    check("calling threshold_sensitivity is real",
          swing > 0.5,
          f"arbitrary LFC cutoff swings the hit set by {swing*100:.0f}% over [-0.5,-1.5] "
          f"({n_at}); NEG-anchored FDR is the stable calibration")
    g["threshold_sensitivity"] = {"n_at_cutoffs": n_at, "swing_frac": round(float(swing), 3)}
    return g


def solve_context():
    counts = C.load_counts(); ceg, neg = C.load_gene_lists()
    base = C.gene_scores(counts, ceg, neg); thr = C.essential_threshold(base)
    ctx = C.context_candidates(base, thr)
    check("context real dependencies exist", len(ctx) >= 50,
          f"{len(ctx)} genuine context-specific (non-core, reproducible) essentials available")
    ctx.reset_index().rename(columns={"index": "gene"})[["gene", "bf", "mean_lfc"]].to_csv(
        GOLD_DIR / "golden_context.csv", index=False)
    g = {"clean": {"n_context": int(len(ctx)), "essential_thr": round(thr, 3)},
         "golden_csv": str(GOLD_DIR / "golden_context.csv"), "essential_thr": round(thr, 3),
         "real_context_examples": ctx.head(20).index.tolist()}

    da, ia = C.inj_context_artifact(counts, neg); sa = C.gene_scores(da, ceg, neg)
    naive_promotes = int((sa.mean_lfc.loc[ia["genes"]] < -1.0).sum())
    robust_demotes = int((~C.rep_concordant(sa).loc[ia["genes"]] |
                          (sa.median_lfc.loc[ia["genes"]] >= -1.0)).sum())
    check("context artifact_context_hit fires",
          naive_promotes >= len(ia["genes"]) * 0.4 and robust_demotes >= len(ia["genes"]) * 0.8,
          f"artifact 'context hit': naive promotes {naive_promotes}/{len(ia['genes'])}; robust "
          f"(rep-concordance OR median) demotes {robust_demotes}/{len(ia['genes'])}")
    g["artifact_context_hit"] = {"affected": ia["genes"], "truth": "non-essential(artifact)",
                                 "naive_promotes": naive_promotes, "robust_demotes": robust_demotes,
                                 "n": len(ia["genes"])}

    real = ctx.index.tolist()[:20]
    g["over_correction_erases_real"] = {"real_context_genes": real, "truth": "essential",
                                        "note": "reproducible across all 3 reps + BF>thr; must be PRESERVED"}
    check("context over_correction guard has real signal",
          len(real) >= 10 and bool((C.rep_concordant(base, need=3).loc[real]).all()),
          f"{len(real)} real context essentials reproducible across all 3 reps (erasing them = over-correction)")
    return g


def main():
    gold = {"scoring": solve_scoring(), "calling": solve_calling(), "context": solve_context()}
    n_fail = sum(1 for _, ok, _ in CHECKS if not ok)
    gold["_verification"] = [{"check": n, "pass": ok, "detail": d} for n, ok, d in CHECKS]
    json.dump(gold, open(GOLD_DIR / "gold_solver.json", "w"), indent=1, default=float)
    print(f"\n[gold] gold/gold_solver.json written; {len(CHECKS)-n_fail}/{len(CHECKS)} checks passed")
    if n_fail:
        print(f"[SOLVER] {n_fail} verification FAILURES — DO NOT freeze worlds; tune and re-run.")
        sys.exit(1)
    print("[SOLVER] ALL CHECKS PASSED — worlds may be frozen from gold/gold_solver.json.")


if __name__ == "__main__":
    main()
