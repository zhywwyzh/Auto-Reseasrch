"""bulk_rnaseq L2 — world builder. RUN ONLY AFTER reference_solver.py exits 0 (all fire checks).

Freezes the three sub-task run dirs from the solver-verified parameterization (l2_common.py is the
single source of truth; gold/gold_solver.json supplies the golden numbers frozen into each manifest
cell). Worlds are DIRECTORIES: meta.json (task + layout) + inputs (+ prepared 'convenience'
artifacts implementing the naive path — the hist model_matrix pattern). Golden values are NEVER
placed inside agent-visible dirs.

  results/bulk_l2_de_run/         (1) clean / batch_confound / normalization_default / hidden_covariate
  results/bulk_l2_gsea_run/       (2) clean / ranking_metric_default / wrong_background_universe / geneset_size_bias
  results/bulk_l2_structure_run/  (3) clean / pca_on_raw_counts / composition_confound
                                      (over_cluster_default DROPPED — every k bootstrap-stable; solver v2)

usage: /workspace/home/miniconda3/envs/bulkl2/bin/python world_builder.py
"""
import json, shutil, sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import l2_common as C

HERE = Path(__file__).parent
RES = HERE / "results"
GOLD = json.load(open(HERE / "gold" / "gold_solver.json"))
assert all(c["pass"] for c in GOLD["_verification"]), \
    "gold_solver.json contains FAILED fire checks — re-run reference_solver.py until all pass."


def cell_dir(run, cell):
    d = run / "data" / f"cell{cell:03d}"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d


def write_counts(d, counts, name="counts.tsv.gz"):
    counts.to_csv(d / name, sep="\t", compression="gzip")


def base_meta(task, layout, extra=None):
    m = {"task": task, "layout": layout,
         "context": "GSE152418 human PBMC bulk RNA-seq (real cohort); COVID-19 vs Healthy"}
    if extra:
        m.update(extra)
    return m


# ================================================================ (1) de
def build_de():
    run = RES / "bulk_l2_de_run"
    counts, meta, gm = C.load_all()
    Xde, Mde = C.de_cohort(counts, meta)
    g = GOLD["de"]
    gold_csv = str(HERE / "gold" / "golden_de.csv")
    task = ("Differential expression, COVID-19 vs Healthy: produce a per-gene DE result "
            "(log2FoldChange, pvalue, padj) with a defensible method and verify it.")
    manifest = []

    def add(cell, label, itype, X, M, extra_files, meta_extra, gold, tell=None, note=None):
        d = cell_dir(run, cell)
        write_counts(d, X)
        M.reset_index()[["sample_id", "condition", "sex", "rin", "pct_intronic",
                         "three_prime_bias"]].to_csv(d / "sample_metadata.tsv", sep="\t", index=False)
        for fname, frame in (extra_files or {}).items():
            frame.to_csv(d / fname, sep="\t" if fname.endswith((".tsv", ".tsv.gz")) else ",",
                         compression="gzip" if fname.endswith(".gz") else None)
        layout = {"counts": "counts.tsv.gz (raw integer counts, genes x samples)",
                  "metadata": "sample_metadata.tsv (condition + per-sample QC covariates)"}
        layout.update(meta_extra or {})
        json.dump(base_meta(task, layout), open(d / "meta.json", "w"), indent=1)
        row = {"cell": cell, "task": "bulk_de", "sub_task": "de", "world_label": label,
               "issue_type": itype, "agent_input": str(d),
               "agent_output": str(run / f"out_cell{cell:03d}.json"), "gold": gold}
        if tell:
            row["confound_tell"] = tell
        if note:
            row["note"] = note
        row["correct_action"] = {
            "clean": "count-based DE with median-of-ratios size factors (~condition); verify canonical markers",
            "batch_confound": "discover the latent batch axis (PCA/correlation), fit ~batch+condition",
            "normalization_default": "return to the RAW counts with proper size factors; do not analyze the prepared CPM",
            "hidden_covariate": "notice the rin/three_prime_bias QC axis co-varying with DE; model rin",
        }[label]
        manifest.append(row)

    add(0, "clean", "none", Xde, Mde, None, None,
        {**g["clean"], "golden_csv": gold_csv})
    Xb, Mb, batch_b, _ = C.inj_batch_confound(counts, meta)
    add(1, "batch_confound", "tool-trap", Xb, Mb.drop(columns=["batch"]), None, None,
        {**g["batch_confound"], "golden_csv": gold_csv},
        tell="an injected 2-batch structure (9 COVID + 6 Healthy = batch B; per-gene ~3.3x factors on "
             "40% of genes) is DISCOVERABLE in PCA (|corr|=0.99); the default ~condition design absorbs "
             "it (top500-jac degrades to 0.68; ~batch+condition recovers 0.89)")
    cpm = C.prep_cpm_matrix(Xde)
    add(2, "normalization_default", "tool-trap", Xde, Mde,
        {"cpm_normalized.tsv.gz": cpm},
        {"prepared": "cpm_normalized.tsv.gz (CPM-normalized matrix, prepared for convenience)"},
        {**g["normalization_default"], "golden_csv": gold_csv},
        tell="the prepared total-count CPM inherits the real plasmablast/IG composition skew (SF/TC "
             "down to 0.76): analyzing it offsets logFC globally (-0.14) and shifts 102 truly-null "
             "genes by >=0.3; raw counts + median-of-ratios is the robust move")
    Xh, Mh = C.inj_hidden_covariate(counts, meta)
    add(3, "hidden_covariate", "data-confound", Xh, Mh, None, None,
        {**g["hidden_covariate"], "golden_csv": gold_csv},
        tell="RIN-coupled, length-coupled degradation (amplifying the real rin~condition axis, corr "
             "-0.29): naive ~condition DE contaminated (jac 0.71); modeling rin recovers (0.84); the "
             "rin / three_prime_bias metadata columns + the stat~length correlation (-0.32) are the tells")
    json.dump(manifest, open(run / "manifest.json", "w"), indent=1)
    print(f"[de] {len(manifest)} worlds -> {run}/manifest.json")


# ================================================================ (2) gsea
def build_gsea():
    run = RES / "bulk_l2_gsea_run"
    counts, meta, gm = C.load_all()
    res = pd.read_csv(HERE / "gold" / "golden_de.csv", index_col=0)
    de_table = res[["symbol", "log2FoldChange", "stat", "pvalue", "padj"]].dropna(subset=["symbol"])
    GO = C.load_gmt(C.GMT["gobp"])
    g = GOLD["gsea"]
    manifest = []
    base_task = ("Pathway enrichment on the provided DE result (COVID-19 vs Healthy PBMC): determine "
                 "the enriched gene-sets INCLUDING the direction of regulation (up- AND down-regulated "
                 "pathways).")

    def add(cell, label, itype, extra_files, meta_extra, gold, tell=None, note=None):
        d = cell_dir(run, cell)
        de_table.to_csv(d / "de_stats.csv")
        for gmt in ("hallmark", "gobp"):
            shutil.copy2(C.GMT[gmt], d / C.GMT[gmt].name)
        for fname, obj in (extra_files or {}).items():
            if isinstance(obj, pd.DataFrame):
                obj.to_csv(d / fname, sep="\t", index=False, header=False)
            else:
                open(d / fname, "w").write("\n".join(obj))
        layout = {"de_stats": "de_stats.csv (per-gene: symbol, log2FoldChange, stat, pvalue, padj)",
                  "gene_sets": "MSigDB .gmt files (hallmark + GO-BP)"}
        layout.update(meta_extra or {})
        json.dump(base_meta(base_task, layout), open(d / "meta.json", "w"), indent=1)
        row = {"cell": cell, "task": "bulk_gsea", "sub_task": "gsea", "world_label": label,
               "issue_type": itype, "agent_input": str(d),
               "agent_output": str(run / f"out_cell{cell:03d}.json"), "gold": gold}
        if tell:
            row["confound_tell"] = tell
        if note:
            row["note"] = note
        row["correct_action"] = {
            "clean": "signed-statistic ranking; directional enrichment on the provided sets",
            "ranking_metric_default": "rebuild a SIGNED metric from de_stats.csv; do not trust the prepared unsigned ranking",
            "wrong_background_universe": "use the EXPRESSED-gene universe (the DE table's genes), not the prepared genome-wide list",
            "geneset_size_bias": "size-aware set scoring; do not report the raw-p ORA ranking dominated by giant sets",
        }[label]
        manifest.append(row)

    add(0, "clean", "none", None, None, g["clean"])
    rnk = C.prep_unsigned_rnk(res)
    add(1, "ranking_metric_default", "tool-trap", {"gene_ranking.rnk": rnk},
        {"prepared": "gene_ranking.rnk (a prepared gene ranking, prepared for convenience)"},
        g["ranking_metric_default"],
        tell="the prepared .rnk is UNSIGNED -log10(p): the ~158 strong DOWN GO-BP modules "
             "(lymphopenia/T-cell biology) are undiscoverable from it (0/15 golden top-down sets in "
             "its top-100); a signed metric rebuilt from de_stats.csv recovers them")
    sym_expressed = de_table.symbol.tolist()
    bg = C.prep_genome_background(GO, sym_expressed)
    add(2, "wrong_background_universe", "tool-trap", {"background_genes.txt": bg},
        {"prepared": "background_genes.txt (background gene universe: all annotated genes)"},
        g["wrong_background_universe"],
        tell="ORA against the prepared genome-wide background fabricates 101 spurious Bonferroni-"
             "significant GO-BP sets (135 vs 36 with the correct EXPRESSED-gene universe)")
    add(3, "geneset_size_bias", "statistical", None, None, g["geneset_size_bias"],
        tell="raw-p ORA ranking is dominated by giant sets (top-10 median size 422 vs corpus 44, "
             "9.6x); a size-aware scoring produces a disjoint top-10 (jac 0.00)",
        note="task-framed world: data identical to clean; the probed deliverable (a top-10 most-"
             "enriched ranking) is what makes the size-blind answer naive")
    json.dump(manifest, open(run / "manifest.json", "w"), indent=1)
    print(f"[gsea] {len(manifest)} worlds -> {run}/manifest.json")


# ================================================================ (3) structure
def build_structure():
    run = RES / "bulk_l2_structure_run"
    counts, meta, gm = C.load_all()
    g = GOLD["structure"]
    manifest = []
    task = ("Characterize the sample-level structure of the full 34-sample cohort: the dominant axes "
            "of variation and what they represent (per-cell expression program vs cell-type "
            "composition), and how many sample groups the data reliably supports.")

    def add(cell, label, itype, extra_files, meta_extra, gold, tell=None, note=None):
        d = cell_dir(run, cell)
        write_counts(d, counts)
        meta.reset_index()[["sample_id", "condition", "sex", "rin", "pct_intronic",
                            "three_prime_bias"]].to_csv(d / "sample_metadata.tsv", sep="\t", index=False)
        gm.reset_index().rename(columns={"index": "gene_id"})[["gene_id", "symbol", "biotype"]].to_csv(
            d / "gene_symbols.tsv", sep="\t", index=False)
        for fname, frame in (extra_files or {}).items():
            frame.to_csv(d / fname)
        layout = {"counts": "counts.tsv.gz (raw integer counts, genes x samples)",
                  "metadata": "sample_metadata.tsv", "gene_symbols": "gene_symbols.tsv"}
        layout.update(meta_extra or {})
        json.dump(base_meta(task, layout), open(d / "meta.json", "w"), indent=1)
        row = {"cell": cell, "task": "bulk_structure", "sub_task": "structure", "world_label": label,
               "issue_type": itype, "agent_input": str(d),
               "agent_output": str(run / f"out_cell{cell:03d}.json"), "gold": gold}
        if tell:
            row["confound_tell"] = tell
        if note:
            row["note"] = note
        row["correct_action"] = {
            "clean": "variance-stabilize before PCA; PC1 = condition axis (corr ~0.90); stability-backed cluster count",
            "pca_on_raw_counts": "recompute PCA on transformed counts; identify the extreme-abundance hijack in the prepared scores",
            "composition_confound": "attribute the dominant axis (partly) to plasmablast composition with signature evidence",
        }[label]
        manifest.append(row)

    add(0, "clean", "none", None, None, g["clean"])
    sc, ld = C.prep_raw_pca(counts)
    add(1, "pca_on_raw_counts", "tool-trap", {"pca_scores.csv": sc, "pca_loadings.csv": ld},
        {"prepared": "pca_scores.csv + pca_loadings.csv (a precomputed sample PCA of the count matrix)"},
        g["pca_on_raw_counts"],
        tell="the prepared PCA was computed on UNTRANSFORMED counts: its PC1 is hijacked by extreme-"
             "abundance genes (HBB/S100A8/9/IG; top-10 loading share 0.26 vs 0.01 transformed) and "
             "loses the condition axis (corr 0.48 vs 0.90)")
    add(2, "composition_confound", "data-confound", None, None, g["composition_confound"],
        tell="the dominant axis is substantially a plasmablast-composition axis (IGfrac corr 0.74, "
             "proliferation-signature corr 0.88): reading it as a pure per-cell 'COVID expression "
             "program' is the naive error",
        note="task-framed world: data identical to clean; graded on composition attribution with evidence")
    json.dump(manifest, open(run / "manifest.json", "w"), indent=1)
    print(f"[structure] {len(manifest)} worlds -> {run}/manifest.json")


def main():
    RES.mkdir(exist_ok=True)
    build_de()
    build_gsea()
    build_structure()
    n_trap = 0
    for r in ("bulk_l2_de_run", "bulk_l2_gsea_run", "bulk_l2_structure_run"):
        n_trap += sum(1 for m in json.load(open(RES / r / "manifest.json")) if m["issue_type"] == "tool-trap")
    assert n_trap >= 1, "L2 must contain at least ONE tool trap"
    print(f"[world_builder] done — {n_trap} tool-trap worlds across the track")


if __name__ == "__main__":
    main()
