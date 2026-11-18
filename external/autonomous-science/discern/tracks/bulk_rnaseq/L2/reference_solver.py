"""bulk_rnaseq L2 — REFERENCE SOLVER (run END-TO-END at build time, BEFORE worlds are frozen).

The benchmark-wide L2 rule: golden truth is PRODUCED by actually running the correct analysis on
the real substrate (proving each clean world solvable with the mounted toolset), and every
confound/trap world must be VERIFIED TO FIRE (naive default != golden; robust move ~= golden)
before it ships. Grader thresholds are calibrated against gold/gold_solver.json, never a priori.
Exits non-zero if ANY check fails — world_builder.py refuses to run on a failing gold file.

usage: /workspace/home/miniconda3/envs/bulkl2/bin/python reference_solver.py
"""
import json, sys, warnings
warnings.filterwarnings("ignore")
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import l2_common as C

GOLD_DIR = Path(__file__).parent / "gold"
GOLD_DIR.mkdir(exist_ok=True)

CHECKS = []
def check(name, ok, detail):
    CHECKS.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def canonical_markers(res, gm, n=50):
    top = set(res.nsmallest(n, "padj").join(gm[["symbol"]]).symbol.dropna())
    canon = {"MKI67", "TK1", "PLK1", "RRM2", "MZB1", "IGHG1", "CCNA2", "UBE2C"}
    return len(top & canon), sorted(top & canon)


# ================================================================ (1) de
def solve_de():
    print("== (1) de — PyDESeq2 COVID-19 vs Healthy ==", flush=True)
    counts, meta, gm = C.load_all()
    Xde, Mde = C.de_cohort(counts, meta)
    g = {}

    golden, sf_gold = C.run_deseq(Xde, Mde, ["condition"])
    n_sig = int((golden.padj < 0.05).sum())
    n_can, canon = canonical_markers(golden, gm)
    g["clean"] = {"n_de_padj05": n_sig,
                  "n_up": int(((golden.padj < 0.05) & (golden.log2FoldChange > 0)).sum()),
                  "canonical_in_top50": canon}
    print(f"  clean golden: {n_sig} DE genes; canonical markers in top50: {canon}")
    check("de/clean solvable", n_sig > 2000 and n_can >= 3,
          f"{n_sig} DE genes with canonical COVID-PBMC biology on top ({n_can}/8 canonical markers)")
    golden.join(gm[["symbol", "exon_union_bp", "biotype"]]).to_csv(GOLD_DIR / "golden_de.csv")

    # ---- batch_confound (TT, injected discoverable batch)
    Xb, Mb, batch_b, _ = C.inj_batch_confound(counts, meta)
    naive_b, _ = C.run_deseq(Xb, Mb, ["condition"])
    adj_b, _ = C.run_deseq(Xb, Mb, ["batch", "condition"])
    con_naive = C.de_concordance(naive_b, golden)
    con_adj = C.de_concordance(adj_b, golden)
    lc = C.logcpm(Xb)
    pcs, _p = C.pca_axes(lc.T.values, n=4)
    bvec = np.array([1.0 if s in set(batch_b) else 0.0 for s in Xb.columns])
    disc = max(abs(float(np.corrcoef(pcs[:, i], bvec)[0, 1])) for i in range(4))
    g["batch_confound"] = {"batch_b_samples": batch_b, "naive": con_naive, "adjusted": con_adj,
                           "batch_pc_discoverability": disc}
    print(f"  batch: naive jac={con_naive['top500_jaccard']:.2f} lfc_r={con_naive['lfc_corr']:.2f} | "
          f"adjusted jac={con_adj['top500_jaccard']:.2f} lfc_r={con_adj['lfc_corr']:.2f} | PC-discover {disc:.2f}")
    check("batch_confound fires",
          con_naive["top500_jaccard"] <= 0.70 and con_adj["top500_jaccard"] >= con_naive["top500_jaccard"] + 0.15
          and disc >= 0.8,
          f"naive `~condition` degrades to top500-jac {con_naive['top500_jaccard']:.2f}; `~batch+condition` "
          f"recovers {con_adj['top500_jaccard']:.2f}; batch axis discoverable in PCA (|corr|={disc:.2f})")

    # ---- normalization_default (TT, prepared-CPM artifact on the FULL cohort — v1 selection
    # DEFEATED itself: the median-of-ratios pseudo-reference shifted with the IG-heavy selection)
    naive_lfc = C.naive_cpm_lfc(counts, meta)
    jn = golden[["log2FoldChange", "padj"]].copy()
    jn["naive"] = naive_lfc
    jn = jn.dropna()
    offset = float((jn.naive - jn.log2FoldChange).median())
    null = jn[jn.padj > 0.5]
    shifted = int((np.abs(null.naive - null.log2FoldChange) >= 0.3).sum())
    lib = Xde.sum(axis=0)
    tc = lib / np.exp(np.log(lib).mean())
    sf_ratio = float((sf_gold / tc).min())
    top_naive = set(jn.assign(a=np.abs(jn.naive)).nlargest(500, "a").index)
    top_gold = set(jn.nsmallest(500, "padj").index)
    g["normalization_default"] = {"naive_minus_golden_lfc_median_offset": offset,
                                  "null_genes_shifted_ge_0.3": shifted, "n_null": int(len(null)),
                                  "min_sizefactor_over_totalcount": sf_ratio}
    print(f"  normalization: median lfc offset {offset:+.3f}; null-shifted {shifted}/{len(null)}; "
          f"min SF/TC {sf_ratio:.2f}")
    check("normalization_default fires", abs(offset) >= 0.10 and shifted >= 50 and sf_ratio <= 0.85,
          f"the prepared total-count-CPM path is globally offset {offset:+.2f} and shifts {shifted} "
          f"truly-null genes by >=0.3 logFC (plasmablast/IG skew; SF/TC down to {sf_ratio:.2f}); "
          f"median-of-ratios on raw counts is the robust move")

    # ---- hidden_covariate (DC, amplified RIN-coupled degradation; strength scan-locked at 1.8)
    Xh, Mh = C.inj_hidden_covariate(counts, meta)
    naive_h, _ = C.run_deseq(Xh, Mh, ["condition"])
    Mh2 = Mh.copy()
    Mh2["rin_group"] = np.where(Mh2.rin <= Mh2.rin.median(), "low", "high")
    adj_grp, _ = C.run_deseq(Xh, Mh2, ["rin_group", "condition"])
    try:
        adj_cont, _ = C.run_deseq(Xh, Mh, ["rin", "condition"])       # continuous rin if supported
    except Exception as e:
        adj_cont = None
        print(f"  (continuous-rin design unsupported: {type(e).__name__})")
    con_naive_h = C.de_concordance(naive_h, golden)
    con_grp = C.de_concordance(adj_grp, golden)
    con_cont = C.de_concordance(adj_cont, golden) if adj_cont is not None else None
    best = max([c for c in (con_grp, con_cont) if c], key=lambda c: c["top500_jaccard"])
    jl = naive_h.join(gm[["exon_union_bp"]]).dropna(subset=["exon_union_bp", "stat"])
    len_corr = float(np.corrcoef(np.log10(jl.exon_union_bp), jl.stat)[0, 1])
    g["hidden_covariate"] = {"naive": con_naive_h, "adjusted_rin_group": con_grp,
                             "adjusted_rin_continuous": con_cont, "best_adjusted": best,
                             "naive_stat_length_corr": len_corr}
    print(f"  hidden: naive jac={con_naive_h['top500_jaccard']:.2f} | grp-adj {con_grp['top500_jaccard']:.2f}"
          + (f" | cont-adj {con_cont['top500_jaccard']:.2f}" if con_cont else "")
          + f" | len tell {len_corr:+.2f}")
    check("hidden_covariate fires",
          con_naive_h["top500_jaccard"] <= 0.72 and
          best["top500_jaccard"] >= con_naive_h["top500_jaccard"] + 0.07 and abs(len_corr) >= 0.25,
          f"RIN-coupled degradation contaminates naive DE (jac {con_naive_h['top500_jaccard']:.2f}); "
          f"modeling rin recovers ({best['top500_jaccard']:.2f}); length-coupled tell corr {len_corr:+.2f}")
    return g


# ================================================================ (2) gsea    return g


# ================================================================ (2) gsea
def solve_gsea():
    print("== (2) gsea — enrichment on the golden DE ==", flush=True)
    counts, meta, gm = C.load_all()
    res = pd.read_csv(GOLD_DIR / "golden_de.csv", index_col=0)
    H = C.load_gmt(C.GMT["hallmark"])
    GO = C.load_gmt(C.GMT["gobp"])
    g = {}

    rnk_signed = C.prerank_scores(res, gm, signed=True)
    calls_signed = C.set_direction_calls(rnk_signed, H)
    topsets = calls_signed.abs().nlargest(10)
    g["clean"] = {"top10_signed_sets": {k: round(float(calls_signed[k]), 3) for k in topsets.index}}
    print("  clean golden top sets:", ", ".join(s.replace("HALLMARK_", "") for s in topsets.index[:6]))
    check("gsea/clean solvable", topsets.abs().min() > 0.2 and len(calls_signed) >= 40,
          f"signed prerank produces strong directional hallmark calls ({len(calls_signed)} sets scored)")

    # ---- ranking_metric_default (TT, prepared unsigned rnk; REFRAMED on the GO-BP down-modules:
    # the UP-dominated hallmark landscape gave the direction-blindness nothing to misrank in v2)
    calls_s_go = C.set_direction_calls(C.prerank_scores(res, gm, signed=True), GO, min_size=25)
    calls_u_go = C.set_direction_calls(C.prerank_scores(res, gm, signed=False), GO, min_size=25)
    down = calls_s_go[calls_s_go <= -0.3]
    top_down_gold = list(down.nsmallest(15).index)
    unsigned_top100 = set(calls_u_go.nlargest(100).index)
    findable = sum(1 for s in top_down_gold if s in unsigned_top100)
    g["ranking_metric_default"] = {"n_strong_down_gobp": int(len(down)),
                                   "golden_top_down": [s for s in top_down_gold[:10]],
                                   "golden_down_findable_in_unsigned_top100": findable}
    print(f"  unsigned rnk: {len(down)} strong DOWN GO-BP modules exist; {findable}/15 golden top-down "
          f"sets appear in the unsigned top-100")
    check("ranking_metric_default fires", len(down) >= 50 and findable <= 1,
          f"the DOWN-regulated biology ({len(down)} strong GO-BP modules — lymphopenia/T-cell) is "
          f"UNDISCOVERABLE from the prepared unsigned -log10(p) ranking ({findable}/15 golden top-down "
          f"sets in its top-100); a signed metric is required")

    # ---- wrong_background_universe (TT; GO-BP; REPLACES gene_length_bias — see addendum)
    sym = res.dropna(subset=["symbol"])
    de = set(sym[sym.padj < 0.05].symbol)
    expressed = set(sym.symbol)
    genome = set().union(*GO.values()) | expressed
    oe = C.ora(de, expressed, GO)
    og = C.ora(de, genome, GO)
    a = 0.05 / len(GO)
    sig_e, sig_g = set(oe[oe.p < a]["set"]), set(og[og.p < a]["set"])
    spur = sig_g - sig_e
    g["wrong_background_universe"] = {"n_sig_expressed_universe": len(sig_e),
                                      "n_sig_genome_universe": len(sig_g), "n_spurious": len(spur),
                                      "spurious_examples": sorted(s.replace("GOBP_", "") for s in spur)[:8]}
    print(f"  universe: expressed {len(sig_e)} sig vs genome {len(sig_g)} — {len(spur)} spurious")
    check("wrong_background_universe fires", len(spur) >= 50 and len(sig_e) >= 15,
          f"genome-background ORA fabricates {len(spur)} spurious Bonferroni-significant GO-BP sets "
          f"(vs {len(sig_e)} with the correct expressed-gene universe)")

    # ---- geneset_size_bias (S): naive p-ranked ORA is dominated by giant sets
    med_all = float(oe.K.median())
    med_top = float(oe.head(10).K.median())
    fe = oe.assign(fold=lambda d: (d.k / (d.K + 1e-9)) /
                   (len(de & expressed) / len(expressed))).query("k >= 5")
    top_fe = set(fe.nlargest(10, "fold")["set"])
    jac = len(top_fe & set(oe.head(10)["set"])) / len(top_fe | set(oe.head(10)["set"]))
    g["geneset_size_bias"] = {"median_K_all": med_all, "median_K_top10_by_p": med_top,
                              "top10_jaccard_p_vs_foldenrich": jac}
    print(f"  size bias: median K top10-by-p {med_top:.0f} vs all {med_all:.0f}; top10 p-vs-fold jac {jac:.2f}")
    check("geneset_size_bias fires", med_top >= 4 * med_all and jac <= 0.4,
          f"p-ranked ORA top-10 median set size {med_top:.0f} vs corpus median {med_all:.0f} "
          f"({med_top/med_all:.1f}x); size-aware (fold-enrichment) top-10 differs (jac {jac:.2f})")
    return g


# ================================================================ (3) structure
def solve_structure():
    print("== (3) structure — all 34 samples ==", flush=True)
    counts, meta, gm = C.load_all()
    condn = (meta.condition == "COVID-19").astype(float).values
    g = {}

    lc = C.logcpm(counts)
    pcs, pl = C.pca_axes(lc.T.values, n=4)
    cc = abs(float(np.corrcoef(pcs[:, 0], condn)[0, 1]))
    load_share_log = float(np.sort(np.abs(pl.components_[0]))[-10:].sum() / np.abs(pl.components_[0]).sum())
    g["clean"] = {"pc1_condition_corr": cc, "pc1_var": float(pl.explained_variance_ratio_[0]),
                  "pc1_top10_loading_share": load_share_log}
    print(f"  clean golden: logCPM PC1 var {pl.explained_variance_ratio_[0]:.2f}, condition corr {cc:.2f}")
    check("structure/clean solvable", cc >= 0.8,
          f"variance-stabilized PCA puts the real (condition) axis on PC1 (corr {cc:.2f})")

    # ---- pca_on_raw_counts (TT, REFRAMED: extreme-abundance hijack, not libsize)
    pcs_r, pr = C.pca_axes(counts.T.values, n=2)
    cc_raw = abs(float(np.corrcoef(pcs_r[:, 0], condn)[0, 1]))
    load_share_raw = float(np.sort(np.abs(pr.components_[0]))[-10:].sum() / np.abs(pr.components_[0]).sum())
    top_raw = [str(gm.loc[gid, "symbol"]) for gid in
               counts.index[np.argsort(-np.abs(pr.components_[0]))[:10]] if gid in gm.index]
    g["pca_on_raw_counts"] = {"pc1_condition_corr_raw": cc_raw, "pc1_top10_loading_share_raw": load_share_raw,
                              "raw_pc1_top_loadings": top_raw,
                              "clean_pc1_condition_corr": cc, "clean_top10_loading_share": load_share_log}
    print(f"  raw PCA: condition corr {cc_raw:.2f} (vs {cc:.2f}); top10 loading share {load_share_raw:.2f} "
          f"(vs {load_share_log:.2f}); hijackers: {', '.join(top_raw[:5])}")
    check("pca_on_raw_counts fires", (cc - cc_raw) >= 0.3 and load_share_raw >= 3 * load_share_log,
          f"untransformed PCA is hijacked by extreme-abundance genes (top-10 loading share "
          f"{load_share_raw:.2f} vs {load_share_log:.2f}) and loses the condition axis "
          f"({cc_raw:.2f} vs {cc:.2f})")

    # ---- composition_confound (DC, attribution): PC1 is substantially composition
    igf = C.ig_fraction(counts, gm)
    ig_pc1 = abs(float(np.corrcoef(pcs[:, 0], igf.values)[0, 1]))
    prolif = {"MKI67", "TK1", "PLK1", "RRM2", "CCNA2", "UBE2C", "BIRC5", "TPX2"}
    pg = gm[gm.symbol.isin(prolif)].index
    prolif_score = lc.loc[lc.index.intersection(pg)].mean(axis=0)
    pr_pc1 = abs(float(np.corrcoef(pcs[:, 0], prolif_score.values)[0, 1]))
    g["composition_confound"] = {"pc1_igfrac_corr": ig_pc1, "pc1_proliferation_corr": pr_pc1,
                                 "igfrac_covid_mean": float(igf[meta.condition == "COVID-19"].mean()),
                                 "igfrac_healthy_mean": float(igf[meta.condition == "Healthy"].mean())}
    print(f"  composition: PC1~IGfrac {ig_pc1:.2f}, PC1~proliferation-signature {pr_pc1:.2f}")
    check("composition_confound fires (attribution evidence exists)", ig_pc1 >= 0.6 and pr_pc1 >= 0.6,
          f"the main axis is substantially a plasmablast-composition axis (IGfrac corr {ig_pc1:.2f}, "
          f"proliferation-signature corr {pr_pc1:.2f}) — naive 'expression program' reading is wrong")

    # ---- cluster-count golden (over_cluster_default DROPPED: every k is bootstrap-stable
    # 0.89-0.96 at n=34 and the silhouette argmax k=4 IS the stable answer — no overconfidence
    # trap exists on this cohort; the stability profile becomes CLEAN's n_clusters golden)
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    sil, stab = {}, {}
    for k in range(2, 7):
        lab = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(pcs[:, :4])
        sil[k] = float(silhouette_score(pcs[:, :4], lab))
        stab[k] = C.bootstrap_coassignment(pcs[:, :4], k)
    k_gold = max(sil, key=sil.get)
    g["clean"]["n_clusters_golden"] = k_gold
    g["clean"]["silhouette"] = sil
    g["clean"]["bootstrap_coassignment"] = stab
    print(f"  cluster golden: k={k_gold} (sil {sil[k_gold]:.2f}, stability {stab[k_gold]:.2f})")
    check("structure/cluster golden stable", stab[k_gold] >= 0.9,
          f"the silhouette-selected k={k_gold} is bootstrap-stable ({stab[k_gold]:.2f}) — a defensible "
          f"n_clusters golden for the clean world")

    return g


def main():
    gold = {"de": solve_de(), "gsea": solve_gsea(), "structure": solve_structure()}
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
