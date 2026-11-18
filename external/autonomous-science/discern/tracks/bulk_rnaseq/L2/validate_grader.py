"""bulk_rnaseq L2 — grader validation (perfect/fooled discrimination sim, hist pattern).

PERFECT (robust pipeline, flags, golden values)      -> must score 3 on every world
FOOLED  (the ACTUAL naive paths: naive DESeq designs re-run live, prepared artifacts used as-is,
         no flags, declared usable)                  -> must score <=1 on every confound/trap world
(clean worlds may score 2: the naive default is not always wrong there by design)

usage: /workspace/home/miniconda3/envs/bulkl2/bin/python validate_grader.py
"""
import json, subprocess, sys, warnings
warnings.filterwarnings("ignore")
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import l2_common as C

HERE = Path(__file__).parent
RES = HERE / "results"
GOLD = json.load(open(HERE / "gold" / "gold_solver.json"))
SIM = HERE / "gold" / "simwork"
SIM.mkdir(exist_ok=True)
PY = sys.executable
TRAJ = [{"step": "sim", "finding": "sim", "action": "sim"}]
golden = pd.read_csv(HERE / "gold" / "golden_de.csv", index_col=0)


def W(run, cell, suf, obj):
    json.dump(obj, open(RES / run / f"out_cell{cell:03d}_{suf}.json", "w"), indent=1)


def de_csv(df, name, lfc_col="log2FoldChange"):
    p = SIM / name
    d = df.reset_index().rename(columns={"index": "gene_id", "gene_id": "gene_id", lfc_col: "log2FoldChange"})
    d[["gene_id", "log2FoldChange", "pvalue", "padj"]].to_csv(p, index=False)
    return str(p)


print("[sim] generating naive DE tables (live naive pipelines) ...", flush=True)
counts, meta, gm = C.load_all()
Xde, Mde = C.de_cohort(counts, meta)
Xb, Mb, _, _ = C.inj_batch_confound(counts, meta)
naive_batch, _ = C.run_deseq(Xb, Mb, ["condition"])
Xh, Mh = C.inj_hidden_covariate(counts, meta)
naive_hidden, _ = C.run_deseq(Xh, Mh, ["condition"])
from scipy.stats import ttest_ind
lib = Xde.sum(axis=0)
lcpm = np.log2(Xde / lib * 1e6 + 1)
grp = (Mde.condition == "COVID-19").values
t, pv = ttest_ind(lcpm.loc[:, grp], lcpm.loc[:, ~grp], axis=1)
from statsmodels.stats.multitest import multipletests
naive_cpm = pd.DataFrame({"log2FoldChange": lcpm.loc[:, grp].mean(axis=1) - lcpm.loc[:, ~grp].mean(axis=1),
                          "pvalue": pv, "padj": multipletests(pv, method="fdr_bh")[1]}, index=Xde.index)

# ---------------- (1) de ----------------
g1 = GOLD["de"]
perfect_csv = de_csv(golden, "p_de.csv")
meth_good = {"tool": "PyDESeq2", "normalization": "median-of-ratios size factors", "design": "~condition"}
W("bulk_l2_de_run", 0, "simperfect", {"output_path": perfect_csv, "method": meth_good,
  "n_de_padj05": g1["clean"]["n_de_padj05"], "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_de_run", 1, "simperfect", {"output_path": perfect_csv,
  "method": {**meth_good, "design": "~batch+condition"},
  "n_de_padj05": g1["clean"]["n_de_padj05"],
  "issues_found": ["a latent 2-group batch structure dominates PC2 (|corr|~0.99); modeled it as ~batch+condition"],
  "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_de_run", 2, "simperfect", {"output_path": perfect_csv, "method": meth_good,
  "n_de_padj05": g1["clean"]["n_de_padj05"],
  "issues_found": ["the prepared CPM matrix inherits the plasmablast/IG composition skew (size factors "
                   "diverge from total-count by up to 24%); used raw counts with median-of-ratios"],
  "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_de_run", 3, "simperfect", {"output_path": perfect_csv,
  "method": {**meth_good, "design": "~rin+condition"},
  "n_de_padj05": g1["clean"]["n_de_padj05"],
  "issues_found": ["DE stat correlates with gene length and the rin metadata column (RNA degradation "
                   "axis); modeled rin in the design"], "analysis_usable": True, "trajectory": TRAJ})
for cell, tab, name in ((0, golden, "f_clean.csv"), (1, naive_batch, "f_batch.csv"),
                        (2, naive_cpm, "f_cpm.csv"), (3, naive_hidden, "f_hidden.csv")):
    W("bulk_l2_de_run", cell, "simfooled", {"output_path": de_csv(tab, name),
      "method": {"tool": "DE", "normalization": "CPM" if cell == 2 else "default", "design": "~condition"},
      "n_de_padj05": 5000, "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})

# ---------------- (2) gsea ----------------
g2 = GOLD["gsea"]
gold_top = [s for s in g2["clean"]["top10_signed_sets"]]
gold_down = g2["ranking_metric_default"]["golden_top_down"]
GO = C.load_gmt(C.GMT["gobp"])
small_sets = [n for n, s in GO.items() if 20 <= len(s) <= 80][:10]
giant_sets = sorted(GO, key=lambda n: -len(GO[n]))[:10]
meth_signed = {"approach": "prerank", "ranking_metric": "signed Wald statistic", "universe": "none",
               "direction_aware": True}
W("bulk_l2_gsea_run", 0, "simperfect", {"method": meth_signed,
  "top_enriched": [{"set": s, "direction": "up"} for s in gold_top],
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_gsea_run", 1, "simperfect", {"method": meth_signed,
  "top_enriched": [{"set": s, "direction": "up"} for s in gold_top[:5]]
                 + [{"set": s, "direction": "down"} for s in gold_down[:5]],
  "issues_found": ["the prepared gene_ranking.rnk is UNSIGNED -log10(p) — direction is lost; rebuilt a "
                   "signed metric from de_stats.csv to recover the down-regulated modules"],
  "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_gsea_run", 2, "simperfect", {
  "method": {**meth_signed, "approach": "ORA", "universe": "expressed genes (the DE table)"},
  "top_enriched": [{"set": s, "direction": "mixed"} for s in gold_top],
  "issues_found": ["the prepared background_genes.txt is a genome-wide universe; ORA against it "
                   "fabricates spurious hits — used the expressed-gene background instead"],
  "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_gsea_run", 3, "simperfect", {
  "method": {**meth_signed, "approach": "ORA + fold-enrichment"},
  "top_enriched": [{"set": s, "direction": "mixed"} for s in small_sets],
  "issues_found": ["raw-p ORA ranking is dominated by giant sets (median size 422 vs corpus 44); "
                   "used size-normalized fold-enrichment scoring"],
  "analysis_usable": True, "trajectory": TRAJ})
meth_unsigned = {"approach": "prerank", "ranking_metric": "-log10(p) from gene_ranking.rnk",
                 "universe": "none", "direction_aware": False}
W("bulk_l2_gsea_run", 0, "simfooled", {"method": meth_unsigned,
  "top_enriched": [{"set": s, "direction": "up"} for s in gold_top],
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_gsea_run", 1, "simfooled", {"method": meth_unsigned,
  "top_enriched": [{"set": s, "direction": "up"} for s in gold_top],
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_gsea_run", 2, "simfooled", {
  "method": {**meth_unsigned, "approach": "ORA", "universe": "all annotated genes (background_genes.txt)"},
  "top_enriched": [{"set": "GOBP_" + s, "direction": "mixed"} for s in g2["wrong_background_universe"]["spurious_examples"][:6]]
                 + [{"set": s, "direction": "mixed"} for s in gold_top[:4]],
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_gsea_run", 3, "simfooled", {
  "method": {**meth_unsigned, "approach": "ORA ranked by p"},
  "top_enriched": [{"set": s, "direction": "mixed"} for s in giant_sets],
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})

# ---------------- (3) structure ----------------
g3 = GOLD["structure"]
W("bulk_l2_structure_run", 0, "simperfect", {"transform": "log2-CPM (variance-stabilized)",
  "main_axis": {"interpretation": "COVID-19 vs Healthy condition axis", "condition_association": 0.90},
  "composition_assessment": "PC1 carries a strong plasmablast/proliferation composition component "
                            "(IG-fraction corr 0.74; MKI67/proliferation signature corr 0.88)",
  "n_clusters": 4, "clustering_confidence": "bootstrap co-assignment 0.96 at k=4",
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_structure_run", 1, "simperfect", {"transform": "log2-CPM (recomputed; the prepared PCA was on raw counts)",
  "main_axis": {"interpretation": "condition axis after transform", "condition_association": 0.90},
  "composition_assessment": "checked",
  "n_clusters": 4, "clustering_confidence": "bootstrap-stable",
  "issues_found": ["the prepared pca_scores.csv is a raw-count PCA: its PC1 loadings are dominated by "
                   "extreme-abundance genes (HBB, S100A8/9, immunoglobulins) and lose the condition axis"],
  "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_structure_run", 2, "simperfect", {"transform": "log2-CPM",
  "main_axis": {"interpretation": "condition axis, substantially composition-driven", "condition_association": 0.90},
  "composition_assessment": "the dominant axis is largely a cell-type composition shift: immunoglobulin/"
                            "plasmablast fraction correlates 0.74 and the proliferation (MKI67) signature "
                            "0.88 with PC1 — not a pure per-cell expression program",
  "n_clusters": 4, "clustering_confidence": "bootstrap co-assignment",
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_structure_run", 0, "simfooled", {"transform": "",
  "main_axis": {"interpretation": "largest variance direction", "condition_association": None},
  "composition_assessment": "", "n_clusters": 6, "clustering_confidence": "default KMeans",
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_structure_run", 1, "simfooled", {"transform": "",
  "main_axis": {"interpretation": "dominant expression variation across samples (from pca_scores.csv)",
                "condition_association": 0.48},
  "composition_assessment": "", "n_clusters": 3, "clustering_confidence": "visual",
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("bulk_l2_structure_run", 2, "simfooled", {"transform": "log2-CPM",
  "main_axis": {"interpretation": "the COVID-19 disease expression program", "condition_association": 0.90},
  "composition_assessment": "PC1 is the per-cell COVID-19 transcriptional program",
  "n_clusters": 2, "clustering_confidence": "clear separation",
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})

# ---------------- grade both sims ----------------
fail = 0
for suf in ("simperfect", "simfooled"):
    for run in ("bulk_l2_de_run", "bulk_l2_gsea_run", "bulk_l2_structure_run"):
        r = subprocess.run([PY, str(HERE / "grade_bulk_l2.py"), str(RES / run), suf],
                           capture_output=True, text=True)
        print(r.stdout.strip())
        if r.returncode:
            print(r.stderr[-600:]); fail += 1; continue
        graded = json.load(open(RES / run / f"graded_{suf}.json"))
        man = json.load(open(RES / run / "manifest.json"))
        for g_row, m in zip(graded, man):
            s, trap = g_row["score"], m["issue_type"] != "none"
            if suf == "simperfect" and s != 3:
                print(f"  !! PERFECT {run}/{g_row['world']} scored {s} != 3"); fail += 1
            if suf == "simfooled" and trap and s is not None and s > 1:
                print(f"  !! FOOLED {run}/{g_row['world']} scored {s} > 1"); fail += 1
print(f"\n[validate] {'ALL DISCRIMINATION CHECKS PASSED' if not fail else f'{fail} FAILURES'}")
sys.exit(1 if fail else 0)
