"""hist_gene_exp L2 — world builder. RUN ONLY AFTER reference_solver.py exits 0 (all fire checks).

Freezes the three sub-task run dirs from the solver-verified parameterization (l2_common.py is the
single source of truth for every injection/materialization; gold/gold_solver.json supplies the
golden numbers written into each manifest cell). On-disk layout per world CONFORMS TO THE PROMISES
in tracks/hist_gene_exp/spec.py SPEC["L2"] info texts:

  regression: agent_input = gene_table.csv            (df preloaded by run_level's table header)
  quantify  : agent_input = the world DIR             (meta.json + genes.csv + alignments/{mark,input}.bam[.bai])
  ranking   : agent_input = gene_table.csv, EXCEPT omitted_confounder where agent_input =
              model_matrix.csv and the full gene_table.csv rides along as manifest `agent_metadata`
              (run_level copies it into the sealed workdir — the robust move must be POSSIBLE).

Every cell carries: sub_task, world_label, issue_type (none|data-confound|tool-trap|statistical),
gold (the solver's numbers for THIS world), correct_action, and confound tells for verify_grades.
Golden values are NEVER placed inside the agent-visible dirs.

usage: /workspace/home/miniconda3/envs/histl2/bin/python world_builder.py
"""
import gzip, json, os, shutil, sys
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

REG_COLS = ["gene_id", "gene_name", "chrom", C.TARGET_MARK, "gc_content", "cpg_oe",
            "gene_expression", "gene_length"]


def _cell_dir(run, cell):
    d = run / "data" / f"cell{cell:03d}"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d


def _link(src, dst):
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def _gene_spans():
    """gene_id -> (start, end) from the GENCODE v29 GTF (for genes.csv start/end columns)."""
    spans = {}
    with gzip.open(C.TRACK / "data" / "raw" / "reference" / "gencode.v29.gtf.gz", "rt") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            f = line.split("\t")
            if f[2] != "gene":
                continue
            gid = f[8].split('gene_id "')[1].split('"')[0]
            spans[gid] = (int(f[3]), int(f[4]))
    return spans


# ================================================================ (1) regression
def build_regression():
    run = RES / "hist_l2_regression_run"
    df = pd.read_csv(C.GENE_TABLE)
    g = GOLD["regression"]
    worlds = [
        ("clean", None, "none",
         {"gold": g["clean"],
          "correct_action": "quantify the mark-expression association (Pearson + a rank-based and/or "
                            "GC/CpG-adjusted estimate); report the canonical positive relation"}),
        ("gc_cpg_confound", "gc", "data-confound",
         {"gold": g["gc_cpg_confound"],
          "confound_tell": "expression carries an injected GC/CpG-composite component (RNA-seq GC "
                           "quantification bias, Benjamini&Speed-2012 class); the naive Pearson is "
                           "INFLATED (+0.543 -> +0.648); the GC/CpG-adjusted estimate recovers the clean "
                           "association (partial r exactly; adjusted std beta to ~0.45)",
          "correct_action": "adjust for the provided gc_content/cpg_oe covariates (multiple regression / "
                            "partial correlation); report the adjusted association and flag the GC "
                            "dependence of expression"}),
        ("outlier_leverage", "outlier", "statistical",
         {"gold": g["outlier_leverage"], "outlier_gene_ids": g["outlier_leverage"]["outlier_gene_ids"],
          "confound_tell": "60 extreme-signal promoters at silent genes drag the Pearson down ~0.10 "
                           "(0.543 -> 0.440) while Spearman is stable (0.550 -> 0.536)",
          "correct_action": "detect the leverage outliers; report a rank-based/robust estimate and flag "
                            "the outlier promoters rather than reporting the naive Pearson"}),
        ("nonlinearity_saturation", "sat", "statistical",
         {"gold": g["nonlinearity_saturation"],
          "confound_tell": "the mark signal is saturated (monotone but nonlinear); the linear Pearson "
                           "understates (0.543 -> 0.485) while Spearman preserves (0.550)",
          "correct_action": "check linearity (residuals / Pearson-vs-Spearman gap); report the monotone "
                            "(rank) association and note the saturation"}),
    ]
    manifest = []
    for cell, (label, inj, itype, extra) in enumerate(worlds):
        d = _cell_dir(run, cell)
        if inj is None:
            out = df[REG_COLS]
        elif inj == "gc":
            out = C.inj_gc_cpg_confound(df)[REG_COLS]
        elif inj == "outlier":
            out, _ids = C.inj_outlier_leverage(df)
            assert _ids == extra["outlier_gene_ids"], "outlier injection drifted from the solver run"
            out = out[REG_COLS]
        elif inj == "sat":
            out = C.inj_nonlinearity_saturation(df)[REG_COLS]
        out.to_csv(d / "gene_table.csv", index=False)
        manifest.append({"cell": cell, "task": "hist_regression", "sub_task": "regression",
                         "world_label": label, "issue_type": itype,
                         "agent_input": str(d / "gene_table.csv"),
                         "agent_output": str(run / f"out_cell{cell:03d}.json"), **extra})
    json.dump(manifest, open(run / "manifest.json", "w"), indent=1)
    print(f"[regression] {len(manifest)} worlds -> {run}/manifest.json")


# ================================================================ (2) quantify
def build_quantify():
    run = RES / "hist_l2_quantify_run"
    genes = C.panel_genes()
    spans = _gene_spans()
    genes["start"] = [spans.get(g, (None, None))[0] for g in genes.gene_id]
    genes["end"] = [spans.get(g, (None, None))[1] for g in genes.gene_id]
    g = GOLD["quantify"]
    gq = str(HERE / "gold" / "golden_quantify.csv")

    worlds = [
        ("clean", "h3k4me3", "none",
         dict(meta_extra={"promoter_window": "TSS +-1kb"},
              gold={**g["clean"], "golden_csv": gq, "golden_col": "golden_k4me3_log2ratio_1kb"},
              correct_action="quantify per-gene promoter signal (TSS+-1kb) from the alignments — input-"
                             "normalized is best practice, though the sharp strong mark survives a naive "
                             "coverage quantification here — and report the positive relation to expression")),
        ("no_input_normalization", "h3k27me3", "tool-trap",
         dict(meta_extra={"promoter_window": "TSS +-10kb"},
              gold={**g["no_input_normalization"], "golden_csv": gq,
                    "golden_col": "golden_k27me3_log2ratio_10kb"},
              confound_tell="an input control BAM is PRESENT in alignments/; skipping input normalization "
                            "on this low-S/N broad mark silently collapses the repressive relation "
                            "(-0.364 -> -0.129) and decorrelates per-gene values (corr 0.61 vs golden)",
              correct_action="normalize the mark to the PROVIDED input control (log2 ratio / bamCompare-"
                             "style) before interpreting; verify the repressive relation against expression")),
        ("broad_mark_narrow_default", "h3k27me3", "tool-trap",
         dict(meta_extra={"promoter_window": "TSS +-10kb",
                          "additional_deliverable":
                              "ALSO call enriched regions/domains for this mark from the alignments and "
                              "report the domain landscape in the `domains` field (number of enriched "
                              "regions and their total Mb). Choose the calling mode yourself."},
              gold=g["broad_mark_narrow_default"],
              confound_tell="MACS3 DEFAULT (narrow) mode fragments the broad H3K27me3 domains: 3.4 Mb "
                            "recovered vs 6.4 Mb broad-mode; repressed (silent-decile) genes lose domain "
                            "coverage (34.6% vs 42.6%). Per-gene signal CANNOT catch this (narrow~broad "
                            "overlap corr 0.88, 81% of genes zero-overlap) — the domain landscape is the "
                            "discriminating deliverable",
              correct_action="call domains in a broad-appropriate mode (macs3 --broad or equivalent "
                             "domain-aware aggregation) and verify the called landscape against the "
                             "mark's broad character before reporting it")),
        ("wrong_promoter_window", "h3k27me3", "tool-trap",
         dict(meta_extra={"promoter_window":
                              "choose a quantification window appropriate to the mark and justify it"},
              gold={**g["wrong_promoter_window"], "golden_csv": gq,
                    "golden_col": "golden_k27me3_log2ratio_10kb"},
              confound_tell="the +-1kb TSS convention (fine for sharp promoter marks) mis-captures the "
                            "broad mark and weakens the repressive relation (-0.364 -> -0.293)",
              correct_action="choose a mark-appropriate BROAD window (e.g. TSS+-10kb or domain-scale), "
                             "justify it, input-normalize, and report the recovered repressive relation")),
    ]
    manifest = []
    for cell, (label, mark, itype, meta) in enumerate(worlds):
        d = _cell_dir(run, cell)
        aln = d / "alignments"
        aln.mkdir()
        for stem in (mark, "input"):
            _link(C._bam(stem), aln / f"{stem}.panel.bam")
            _link(C._bam(stem) + ".bai", aln / f"{stem}.panel.bam.bai")
        genes[["gene_id", "gene_name", "chrom", "start", "end", "tss", "strand",
               "gene_expression"]].to_csv(d / "genes.csv", index=False)
        meta_json = {"target_mark": {"h3k4me3": "H3K4me3", "h3k27me3": "H3K27me3"}[mark],
                     "layout": {"chip_bam": f"alignments/{mark}.panel.bam",
                                "input_control_bam": "alignments/input.panel.bam",
                                "genes": "genes.csv (gene_id, chrom, start, end, tss, strand, "
                                         "gene_expression = log1p TPM)"},
                     "context": "K562; hg38; chromosome panel chr8+9+11+17+22; real ENCODE filtered "
                                "alignments (both BAMs indexed)",
                     **meta["meta_extra"]}
        json.dump(meta_json, open(d / "meta.json", "w"), indent=1)
        row = {"cell": cell, "task": "hist_quantify", "sub_task": "quantify",
               "world_label": label, "issue_type": itype, "target_mark": meta_json["target_mark"],
               "agent_input": str(d), "agent_output": str(run / f"out_cell{cell:03d}.json"),
               "gold": meta["gold"], "correct_action": meta["correct_action"]}
        if "confound_tell" in meta:
            row["confound_tell"] = meta["confound_tell"]
        manifest.append(row)
    json.dump(manifest, open(run / "manifest.json", "w"), indent=1)
    print(f"[quantify] {len(manifest)} worlds -> {run}/manifest.json")


# ================================================================ (3) effect_ranking
def build_ranking():
    run = RES / "hist_l2_ranking_run"
    df = pd.read_csv(C.GENE_TABLE)
    g = GOLD["effect_ranking"]
    manifest = []

    def add(cell, label, itype, files, agent_input_name, extra, metadata=None):
        d = _cell_dir(run, cell)
        for fname, frame in files.items():
            frame.to_csv(d / fname, index=False)
        row = {"cell": cell, "task": "hist_ranking", "sub_task": "effect_ranking",
               "world_label": label, "issue_type": itype,
               "agent_input": str(d / agent_input_name),
               "agent_output": str(run / f"out_cell{cell:03d}.json"), **extra}
        if metadata:
            row["agent_metadata"] = str(d / metadata)
        manifest.append(row)

    add(0, "clean", "none", {"gene_table.csv": df}, "gene_table.csv",
        {"gold": g["clean"],
         "correct_action": "estimate each predictor's INDEPENDENT association jointly (multiple "
                           "regression with the covariates), not marginal correlations; note dnase's "
                           "marginal r (+0.50) is mostly shared variance (joint +0.08, VIF ~3-7); rank "
                           "by joint effect with canonical signs"})
    add(1, "multicollinearity", "tool-trap",
        {"gene_table.csv": C.sub_multicollinearity(df)}, "gene_table.csv",
        {"gold": g["multicollinearity"],
         "confound_tell": "n=400 pilot subset (real rows) + VIF~6.5: default OLS produces a complete-"
                          "looking per-mark effect table that silently loses H3K27me3 (-0.01 vs golden "
                          "-0.134) and coin-flips dnase's sign (bootstrap stability 0.51)",
         "correct_action": "check collinearity (VIF/correlations) and estimate stability (bootstrap/CI) "
                           "at this n; regularize or qualify; do NOT report confident per-predictor "
                           "effects the sample cannot support"})
    add(2, "omitted_confounder", "data-confound",
        {"model_matrix.csv": C.prepared_matrix_omit(df), "gene_table.csv": df}, "model_matrix.csv",
        {"gold": g["omitted_confounder"],
         "confound_tell": "the prepared model_matrix.csv OMITS h3k27ac (and the GC covariates); the "
                          "FULL gene_table.csv sits alongside in the working directory; fitting the "
                          "prepared matrix as-is inflates h3k4me3's apparent effect ~2x (0.374 vs 0.185)",
         "correct_action": "verify the prepared INPUT against the full table alongside; re-include the "
                           "omitted co-varying predictor (h3k27ac) before estimating independent effects"},
        metadata="gene_table.csv")
    add(3, "aggregation_reversal", "statistical", {"gene_table.csv": df}, "gene_table.csv",
        {"gold": g["aggregation_reversal"],
         "confound_tell": "the pooled mark-expression slope hides CGI vs non-CGI promoter heterogeneity "
                          "(h3k27me3: -0.376 vs -0.264); a single genome-wide rule misleads",
         "note": "task-framed world: the DATA is identical to clean; the probed deliverable (per-class "
                 "reliability of one pooled rule) is what makes the pooled answer naive — graded on "
                 "stratification (subgroup_effects)",
         "correct_action": "check heterogeneity across promoter classes (CGI-like vs non, from "
                           "gc_content/cpg_oe); report stratified associations, not one pooled number"})
    json.dump(manifest, open(run / "manifest.json", "w"), indent=1)
    print(f"[ranking] {len(manifest)} worlds -> {run}/manifest.json")


def main():
    RES.mkdir(exist_ok=True)
    build_regression()
    build_quantify()
    build_ranking()
    n_trap = 0
    for r in ("hist_l2_regression_run", "hist_l2_quantify_run", "hist_l2_ranking_run"):
        n_trap += sum(1 for m in json.load(open(RES / r / "manifest.json")) if m["issue_type"] == "tool-trap")
    assert n_trap >= 1, "L2 must contain at least ONE tool trap"
    print(f"[world_builder] done — {n_trap} tool-trap worlds across the track")


if __name__ == "__main__":
    main()
