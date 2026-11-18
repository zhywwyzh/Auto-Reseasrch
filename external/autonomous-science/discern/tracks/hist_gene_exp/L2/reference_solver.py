"""hist_gene_exp L2 — REFERENCE SOLVER (run END-TO-END at build time, BEFORE worlds are frozen).

The benchmark-wide L2 rule (the TWAS lesson): golden truth is not asserted, it is PRODUCED by
actually running the correct analysis on the real substrate — which simultaneously PROVES each
clean world is solvable with the mounted toolset — and every confound/trap world must be VERIFIED
TO FIRE (naive default != golden; robust move ~= golden) before it ships. Grader thresholds are
then calibrated against these numbers (gold/gold_solver.json), never chosen a priori.

v2 (2026-08-12): world parameterization locked after the v1 run FAILED 5/12 fire checks on real
data — see l2_common docstrings for what changed and why. Exits non-zero if ANY check fails.

usage: /workspace/home/miniconda3/envs/histl2/bin/python reference_solver.py
"""
import json, sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import l2_common as C

GOLD_DIR = Path(__file__).parent / "gold"
GOLD_DIR.mkdir(exist_ok=True)
SCRATCH = GOLD_DIR / "solver_work"
SCRATCH.mkdir(exist_ok=True)

CHECKS = []
def check(name, ok, detail):
    CHECKS.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


# ================================================================ sub-task (1) regression
def solve_regression():
    print("== (1) regression — mark->expression on the per-gene table ==")
    df = pd.read_csv(C.GENE_TABLE)
    g = {}
    g["clean"] = {"pearson_r": C.pearson(df[C.TARGET_MARK], df.gene_expression),
                  "spearman_rho": C.spearman(df[C.TARGET_MARK], df.gene_expression),
                  "partial_r_gc_adjusted": C.partial_r(df), "n_genes": len(df)}
    print(f"  clean: r={g['clean']['pearson_r']:+.3f} rho={g['clean']['spearman_rho']:+.3f} "
          f"partial_r={g['clean']['partial_r_gc_adjusted']:+.3f}")
    check("regression/clean solvable", abs(g["clean"]["pearson_r"]) > 0.4,
          f"canonical positive association present (r={g['clean']['pearson_r']:+.3f})")

    d = C.inj_gc_cpg_confound(df)
    r_b, p_b = C.pearson(d[C.TARGET_MARK], d.gene_expression), C.partial_r(d)
    g["gc_cpg_confound"] = {"naive_pearson": r_b, "partial_r_gc_adjusted": p_b,
                            "clean_pearson": g["clean"]["pearson_r"],
                            "clean_partial_r": g["clean"]["partial_r_gc_adjusted"]}
    infl = r_b - g["clean"]["pearson_r"]
    drift = abs(p_b - g["clean"]["partial_r_gc_adjusted"])
    # spec schema reports adjusted_beta_std -> store the confounded-table value as an accepted gold
    Xc = np.column_stack([C.zscore(d[c]) for c in [C.TARGET_MARK] + C.COVARS] + [np.ones(len(d))])
    bstd = float(np.linalg.lstsq(Xc, C.zscore(d.gene_expression), rcond=None)[0][0])
    g["gc_cpg_confound"]["adjusted_beta_std"] = bstd
    g["gc_cpg_confound"]["spearman_rho"] = C.spearman(d[C.TARGET_MARK], d.gene_expression)
    check("gc_cpg_confound fires", infl >= 0.05 and drift <= 0.01,
          f"naive r inflates {g['clean']['pearson_r']:+.3f}->{r_b:+.3f} (+{infl:.3f}); "
          f"GC-adjusted partial r drifts {drift:.4f} (exact recovery)")

    d, out_genes = C.inj_outlier_leverage(df)
    r_o, rho_o = C.pearson(d[C.TARGET_MARK], d.gene_expression), C.spearman(d[C.TARGET_MARK], d.gene_expression)
    g["outlier_leverage"] = {"naive_pearson": r_o, "spearman_rho": rho_o, "outlier_gene_ids": out_genes,
                             "clean_pearson": g["clean"]["pearson_r"], "clean_spearman": g["clean"]["spearman_rho"]}
    dp, dr = abs(r_o - g["clean"]["pearson_r"]), abs(rho_o - g["clean"]["spearman_rho"])
    check("outlier_leverage fires", dp >= 0.05 and dr <= 0.02,
          f"|dPearson|={dp:.3f} (dragged) vs |dSpearman|={dr:.3f} (stable); {len(out_genes)} planted outliers")

    d = C.inj_nonlinearity_saturation(df)
    r_s, rho_s = C.pearson(d[C.TARGET_MARK], d.gene_expression), C.spearman(d[C.TARGET_MARK], d.gene_expression)
    g["nonlinearity_saturation"] = {"naive_pearson": r_s, "spearman_rho": rho_s,
                                    "clean_pearson": g["clean"]["pearson_r"],
                                    "clean_spearman": g["clean"]["spearman_rho"]}
    drop, keep = g["clean"]["pearson_r"] - r_s, abs(rho_s - g["clean"]["spearman_rho"])
    check("nonlinearity_saturation fires", drop >= 0.05 and keep <= 0.03,
          f"Pearson understates {g['clean']['pearson_r']:+.3f}->{r_s:+.3f}; Spearman moves {keep:.3f}")
    return g


# ================================================================ sub-task (2) quantify (BAM panel)
def solve_quantify():
    print("== (2) quantify — promoter signal from raw ENCODE alignments (tool-trap flagship) ==")
    genes = C.panel_genes()
    expr = genes.gene_expression.values
    print(f"  panel genes: {len(genes)} on {sorted(genes.chrom.unique())}")
    g = {"n_panel_genes": len(genes)}

    cnt = {}
    for name, half in (("h3k4me3", 1000), ("h3k27me3", 1000), ("input", 1000),
                       ("h3k27me3", 10000), ("input", 10000)):
        cnt[(name, half)] = C.promoter_read_counts(C._bam(name), genes, half=half)

    # ---- CLEAN (h3k4me3, +-1kb): golden = input-normalized; the naive default is NOT wrong here
    gold_k4 = C.norm_log2ratio(cnt[("h3k4me3", 1000)], cnt[("input", 1000)])
    naive_k4 = np.log1p(cnt[("h3k4me3", 1000)])
    g["clean"] = {"golden_rho_vs_expr": C.spearman(gold_k4, expr),
                  "naive_rho_vs_expr": C.spearman(naive_k4, expr),
                  "naive_vs_golden_corr": C.spearman(naive_k4, gold_k4),
                  "crosscheck_vs_encode_fc": C.spearman(gold_k4, genes.h3k4me3.values)}
    print(f"  clean(k4me3 +-1kb): golden rho={g['clean']['golden_rho_vs_expr']:+.3f} "
          f"naive rho={g['clean']['naive_rho_vs_expr']:+.3f} naive~golden={g['clean']['naive_vs_golden_corr']:.3f} "
          f"encodeFC-xcheck={g['clean']['crosscheck_vs_encode_fc']:.3f}")
    check("quantify/clean solvable + default OK",
          g["clean"]["golden_rho_vs_expr"] > 0.35 and g["clean"]["naive_vs_golden_corr"] > 0.85
          and g["clean"]["crosscheck_vs_encode_fc"] > 0.6,
          "input-normalized golden reproduces the canonical relation; naive default survives on the "
          "strong sharp mark; hand-rolled golden agrees with the independent ENCODE FC track")

    # ---- no_input_normalization (TOOL TRAP): H3K27me3 +-10kb, input PRESENT but unused
    gold_k27 = C.norm_log2ratio(cnt[("h3k27me3", 10000)], cnt[("input", 10000)])
    naive_k27 = np.log1p(cnt[("h3k27me3", 10000)])
    rho_g, rho_n = C.spearman(gold_k27, expr), C.spearman(naive_k27, expr)
    agree = C.spearman(naive_k27, gold_k27)
    g["no_input_normalization"] = {"golden_rho_vs_expr": rho_g, "naive_rho_vs_expr": rho_n,
                                   "naive_vs_golden_corr": agree}
    print(f"  no_input(k27me3 +-10kb): golden rho={rho_g:+.3f}  naive(no-input) rho={rho_n:+.3f}  "
          f"naive~golden={agree:.3f}")    # low-S/N broad mark: input bias dominates raw coverage
    check("no_input_normalization fires", rho_g <= -0.30 and (rho_g - rho_n) <= -0.15 and agree <= 0.80,
          f"skipping the PRESENT input control collapses the repressive relation {rho_g:+.3f}->{rho_n:+.3f} "
          f"and decorrelates per-gene values (corr {agree:.2f}) — a silent failure")

    # ---- broad_mark_narrow_default (TOOL TRAP): MACS3 default narrow fragments the domains
    npk = C.macs3_callpeak("h3k27me3", SCRATCH, broad=False)
    bpk = C.macs3_callpeak("h3k27me3", SCRATCH, broad=True)
    ns, bs = C.peak_stats(npk), C.peak_stats(bpk)
    nb, bb = C.overlap_bp(npk, genes), C.overlap_bp(bpk, genes)
    q10 = np.quantile(expr, 0.10)
    sil_n, sil_b = float((nb[expr < q10] > 0).mean()), float((bb[expr < q10] > 0).mean())
    g["broad_mark_narrow_default"] = {
        "narrow": ns, "broad": bs,
        "per_gene_rho_narrow": C.spearman(nb, expr), "per_gene_rho_broad": C.spearman(bb, expr),
        "silent_decile_domain_coverage_narrow": sil_n, "silent_decile_domain_coverage_broad": sil_b}
    print(f"  macs3 narrow: {ns['n_peaks']} peaks {ns['total_bp']/1e6:.1f} Mb (mean {ns['mean_width']:.0f}bp); "
          f"silent-decile coverage {sil_n:.1%}")
    print(f"  macs3 broad : {bs['n_peaks']} peaks {bs['total_bp']/1e6:.1f} Mb (mean {bs['mean_width']:.0f}bp); "
          f"silent-decile coverage {sil_b:.1%}")
    # WHY the domain deliverable: per-gene peak-overlap CANNOT discriminate narrow-vs-broad
    # (narrow~broad overlap corr 0.88; 81-85% of genes have zero overlap -> tie-dominated)
    g["broad_mark_narrow_default"]["per_gene_overlap_corr_narrow_vs_broad"] = C.spearman(nb, bb)
    g["broad_mark_narrow_default"]["frac_genes_zero_overlap_broad"] = float((bb == 0).mean())
    check("broad_mark_narrow_default fires",
          bs["total_bp"] >= 1.8 * max(1, ns["total_bp"]) and (sil_b - sil_n) >= 0.05,
          f"default narrow recovers {ns['total_bp']/1e6:.1f} Mb of domain vs broad {bs['total_bp']/1e6:.1f} Mb "
          f"(x{bs['total_bp']/max(1,ns['total_bp']):.2f}); repressed-gene (silent-decile) domain coverage "
          f"{sil_n:.1%} -> {sil_b:.1%}")

    # ---- wrong_promoter_window (TOOL TRAP): the +-1kb TSS convention mis-captures the broad mark
    k27_1k = C.norm_log2ratio(cnt[("h3k27me3", 1000)], cnt[("input", 1000)])
    rho_10k, rho_1k = C.spearman(gold_k27, expr), C.spearman(k27_1k, expr)
    g["wrong_promoter_window"] = {"golden_rho_10kb": rho_10k, "naive_rho_1kb": rho_1k,
                                  "value_corr_1k_vs_10k": C.spearman(k27_1k, gold_k27)}
    print(f"  window(k27me3): +-10kb rho={rho_10k:+.3f} vs +-1kb rho={rho_1k:+.3f}")
    check("wrong_promoter_window fires", abs(rho_10k) - abs(rho_1k) >= 0.05 and rho_10k < 0,
          f"the mark-appropriate broad window recovers {rho_10k:+.3f}; the +-1kb default weakens it to {rho_1k:+.3f}")

    out = genes[["gene_id", "gene_name", "chrom", "tss", "gene_expression"]].copy()
    out["golden_k4me3_log2ratio_1kb"] = np.round(gold_k4, 4)
    out["golden_k27me3_log2ratio_10kb"] = np.round(gold_k27, 4)
    out["naive_k4me3_coverage_1kb"] = np.round(naive_k4, 4)
    out["naive_k27me3_coverage_10kb"] = np.round(naive_k27, 4)
    out["naive_k27me3_log2ratio_1kb"] = np.round(k27_1k, 4)
    out.to_csv(GOLD_DIR / "golden_quantify.csv", index=False)
    print("  [gold] per-gene golden quantifications -> gold/golden_quantify.csv")
    return g


# ================================================================ sub-task (3) effect_ranking
def solve_effect_ranking():
    print("== (3) effect_ranking — per-mark independent effect / ranking ==")
    df = pd.read_csv(C.GENE_TABLE)
    g = {}
    preds, full = C.MARKS, C.MARKS + C.COVARS
    marg = {p: C.pearson(df[p], df.gene_expression) for p in preds}
    ols_j = C.ols_std(df, full)
    ridge_j = C.ridge_std(df, full)
    vifs = C.vif(df, preds)
    rank_gold = sorted(preds, key=lambda p: -abs(ridge_j[p]))
    rank_marg = sorted(preds, key=lambda p: -abs(marg[p]))
    g["clean"] = {"marginal_r": marg, "ols_with_covariates": ols_j, "ridge_with_covariates": ridge_j,
                  "vif": vifs, "golden_ranking": rank_gold, "marginal_ranking": rank_marg}
    print("  marginal r     : " + ", ".join(f"{p}={marg[p]:+.3f}" for p in preds))
    print("  ridge (+covars): " + ", ".join(f"{p}={ridge_j[p]:+.3f}" for p in preds))
    print("  VIF            : " + ", ".join(f"{p}={vifs[p]:.2f}" for p in preds))
    print(f"  golden ranking : {rank_gold}   (marginal ranking: {rank_marg})")
    check("effect_ranking/clean solvable",
          all(np.sign(ridge_j[p]) == np.sign(marg[p]) for p in ("h3k4me3", "h3k27me3"))
          and rank_marg != rank_gold and marg["dnase"] >= 0.45 and abs(ridge_j["dnase"]) <= 0.10,
          "golden keeps canonical signs AND the marginal-vs-joint contrast exists on the clean table "
          f"(dnase marginal {marg['dnase']:+.3f} vs joint {ridge_j['dnase']:+.3f} — shared variance, VIF "
          f"{vifs['dnase']:.1f})")

    # ---- multicollinearity (TOOL TRAP): n=400 pilot mini-cohort, naive OLS silently wrong
    sub = C.sub_multicollinearity(df)
    ols_sub = C.ols_std(sub, preds)
    stab = C.bootstrap_sign_stability(sub, preds)
    vif_sub = C.vif(sub, preds)
    g["multicollinearity"] = {"n": len(sub), "ols_marks_only": ols_sub, "bootstrap_sign_stability": stab,
                              "vif": vif_sub, "golden_ridge_full_table": ridge_j}
    print(f"  mini-cohort n={len(sub)}: OLS " + ", ".join(f"{p}={ols_sub[p]:+.3f}" for p in preds))
    print("  sign stability : " + ", ".join(f"{p}={stab[p]:.2f}" for p in preds))
    lost = abs(ols_sub["h3k27me3"]) <= 0.5 * abs(ridge_j["h3k27me3"])
    check("multicollinearity fires", min(stab.values()) <= 0.75 and lost and max(vif_sub.values()) >= 2.0,
          f"naive OLS on the pilot subset loses H3K27me3 ({ols_sub['h3k27me3']:+.3f} vs golden "
          f"{ridge_j['h3k27me3']:+.3f}) and min sign stability {min(stab.values()):.2f} (VIFmax {max(vif_sub.values()):.1f})")

    # ---- omitted_confounder (DATA CONFOUND): prepared matrix omits H3K27ac
    prep_df = C.prepared_matrix_omit(df)
    prep_preds = ["h3k4me3", "h3k27me3", "dnase"]
    ols_prep = C.ols_std(prep_df, prep_preds)
    shift = abs(ols_prep["h3k4me3"] - ridge_j["h3k4me3"])
    g["omitted_confounder"] = {"prepared_predictors": prep_preds, "ols_prepared": ols_prep,
                               "golden_with_h3k27ac": {p: ridge_j[p] for p in prep_preds},
                               "h3k4me3_inflation": shift, "omitted": ["h3k27ac"] + C.COVARS}
    print(f"  prepared-matrix OLS: " + ", ".join(f"{p}={ols_prep[p]:+.3f}" for p in prep_preds)
          + f"  (h3k4me3 inflates by {shift:.3f})")
    check("omitted_confounder fires", shift >= 0.10,
          f"omitting H3K27ac inflates H3K4me3's apparent independent effect "
          f"{ridge_j['h3k4me3']:+.3f} -> {ols_prep['h3k4me3']:+.3f} (classic omitted-variable bias)")

    # ---- aggregation_reversal (STATISTICAL): CGI vs non-CGI strata
    cgi = C.cgi_mask(df)
    strata = {}
    for lab, sub_df in (("CGI", df[cgi]), ("nonCGI", df[~cgi])):
        strata[lab] = {p: C.pearson(sub_df[p], sub_df.gene_expression) for p in ("h3k4me3", "h3k27me3")}
        strata[lab]["n"] = int(len(sub_df))
    g["aggregation_reversal"] = {"pooled": {p: marg[p] for p in ("h3k4me3", "h3k27me3")}, "strata": strata}
    gap = max(abs(strata["CGI"][p] - strata["nonCGI"][p]) for p in ("h3k4me3", "h3k27me3"))
    print(f"  strata: CGI(n={strata['CGI']['n']}) k27me3 r={strata['CGI']['h3k27me3']:+.3f} | "
          f"nonCGI(n={strata['nonCGI']['n']}) k27me3 r={strata['nonCGI']['h3k27me3']:+.3f}")
    check("aggregation_reversal fires", gap >= 0.10,
          f"max stratum gap = {gap:.3f} (the pooled slope misleads for at least one mark)")
    return g


def main():
    gold = {"regression": solve_regression(),
            "quantify": solve_quantify(),
            "effect_ranking": solve_effect_ranking()}
    n_fail = sum(1 for _, ok, _ in CHECKS if not ok)
    gold["_verification"] = [{"check": n, "pass": ok, "detail": d} for n, ok, d in CHECKS]
    json.dump(gold, open(GOLD_DIR / "gold_solver.json", "w"), indent=1)
    print(f"\n[gold] gold/gold_solver.json written; {len(CHECKS)-n_fail}/{len(CHECKS)} checks passed")
    if n_fail:
        print(f"[SOLVER] {n_fail} verification FAILURES — DO NOT freeze worlds; tune and re-run.")
        sys.exit(1)
    print("[SOLVER] ALL CHECKS PASSED — worlds may be frozen from gold/gold_solver.json.")


if __name__ == "__main__":
    main()
