"""hist_gene_exp L2 — grader validation (the clinvar 'perfect-agent simulation' pattern).

Simulates two agents from the SOLVER's own numbers and asserts the grader discriminates:
  PERFECT (robust pipeline, flags + golden values)  -> must score 3 on every world
  FOOLED  (naive defaults, no flags, declared usable)-> must score <=1 on every confound/trap world
    (clean worlds may legitimately score 2: the naive default is not wrong there by design)

usage: /workspace/home/miniconda3/envs/histl2/bin/python validate_grader.py
"""
import json, subprocess, sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
RES = HERE / "results"
GOLD = json.load(open(HERE / "gold" / "gold_solver.json"))
GQ = pd.read_csv(HERE / "gold" / "golden_quantify.csv")
PY = sys.executable

def W(run, cell, suf, obj):
    json.dump(obj, open(RES / run / f"out_cell{cell:03d}_{suf}.json", "w"), indent=1)

def csv_from(col, name):
    p = HERE / "gold" / "simwork" / name
    p.parent.mkdir(exist_ok=True)
    GQ[["gene_id", col]].rename(columns={col: "signal"}).to_csv(p, index=False)
    return str(p)

TRAJ = [{"step": "sim", "finding": "sim", "action": "sim"}]
g1, g2, g3 = GOLD["regression"], GOLD["quantify"], GOLD["effect_ranking"]

# ---------------- PERFECT ----------------
W("hist_l2_regression_run", 0, "simperfect", {
  "estimates": {"pearson_r": g1["clean"]["pearson_r"], "spearman_rho": g1["clean"]["spearman_rho"],
                "adjusted_beta_std": 0.555},
  "direction": "positive", "method_note": "Pearson + Spearman + GC-adjusted OLS",
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("hist_l2_regression_run", 1, "simperfect", {
  "estimates": {"pearson_r": g1["gc_cpg_confound"]["naive_pearson"],
                "spearman_rho": g1["gc_cpg_confound"]["spearman_rho"],
                "adjusted_beta_std": g1["gc_cpg_confound"]["adjusted_beta_std"]},
  "direction": "positive",
  "method_note": "covariate-adjusted regression on gc_content and cpg_oe",
  "issues_found": ["expression shows GC/CpG-dependent inflation; naive Pearson is confounded — "
                   "reported the GC/CpG-adjusted coefficient"],
  "analysis_usable": True, "trajectory": TRAJ})
W("hist_l2_regression_run", 2, "simperfect", {
  "estimates": {"pearson_r": g1["outlier_leverage"]["naive_pearson"],
                "spearman_rho": g1["outlier_leverage"]["spearman_rho"], "adjusted_beta_std": None},
  "direction": "positive", "method_note": "rank-based (Spearman) due to leverage points",
  "issues_found": ["~60 extreme-signal promoters at silent genes are leverage outliers dragging the "
                   "Pearson; rank-based estimate reported"],
  "analysis_usable": True, "trajectory": TRAJ})
W("hist_l2_regression_run", 3, "simperfect", {
  "estimates": {"pearson_r": g1["nonlinearity_saturation"]["naive_pearson"],
                "spearman_rho": g1["nonlinearity_saturation"]["spearman_rho"], "adjusted_beta_std": None},
  "direction": "positive", "method_note": "Spearman (signal saturates; linear fit understates)",
  "issues_found": ["mark signal is saturating: monotone but nonlinear; Pearson understates the association"],
  "analysis_usable": True, "trajectory": TRAJ})

W("hist_l2_quantify_run", 0, "simperfect", {
  "output_path": csv_from("golden_k4me3_log2ratio_1kb", "p_clean.csv"),
  "method": {"tool": "pysam window counts", "normalization": "log2 ratio to input control",
             "peak_mode": "none", "window": "TSS +-1kb"},
  "signal_expression_spearman": g2["clean"]["golden_rho_vs_expr"], "direction": "positive",
  "domains": None, "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("hist_l2_quantify_run", 1, "simperfect", {
  "output_path": csv_from("golden_k27me3_log2ratio_10kb", "p_noinput.csv"),
  "method": {"tool": "pysam window counts", "normalization": "log2 ratio to the provided input control",
             "peak_mode": "none", "window": "TSS +-10kb"},
  "signal_expression_spearman": g2["no_input_normalization"]["golden_rho_vs_expr"],
  "direction": "negative", "domains": None,
  "issues_found": ["raw coverage is biased by background/copy-number — normalized to the input control"],
  "analysis_usable": True, "trajectory": TRAJ})
W("hist_l2_quantify_run", 2, "simperfect", {
  "output_path": csv_from("golden_k27me3_log2ratio_10kb", "p_broad.csv"),
  "method": {"tool": "macs3 callpeak --broad", "normalization": "log2 ratio to input control",
             "peak_mode": "broad", "window": "TSS +-10kb"},
  "signal_expression_spearman": g2["no_input_normalization"]["golden_rho_vs_expr"],
  "direction": "negative",
  "domains": {"n": g2["broad_mark_narrow_default"]["broad"]["n_peaks"],
              "total_mb": g2["broad_mark_narrow_default"]["broad"]["total_bp"] / 1e6},
  "issues_found": ["H3K27me3 is a broad mark — the narrow default fragments domains; used --broad"],
  "analysis_usable": True, "trajectory": TRAJ})
W("hist_l2_quantify_run", 3, "simperfect", {
  "output_path": csv_from("golden_k27me3_log2ratio_10kb", "p_window.csv"),
  "method": {"tool": "pysam window counts", "normalization": "log2 ratio to input control",
             "peak_mode": "none", "window": "TSS +-10kb (broad mark spreads beyond the promoter)"},
  "signal_expression_spearman": g2["wrong_promoter_window"]["golden_rho_10kb"],
  "direction": "negative", "domains": None,
  "issues_found": ["+-1kb TSS window mis-captures the broad mark; chose a domain-scale window"],
  "analysis_usable": True, "trajectory": TRAJ})

ridge = g3["clean"]["ridge_with_covariates"]
W("hist_l2_ranking_run", 0, "simperfect", {
  "effect_ranking": g3["clean"]["golden_ranking"], "per_mark_effects": ridge,
  "reliability_assessment": "active marks are collinear (VIF 3-7); effects estimated jointly with "
                            "covariates and regularization — separable with care",
  "covariates_included": ["gc_content", "cpg_oe"], "subgroup_effects": None,
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("hist_l2_ranking_run", 1, "simperfect", {
  "effect_ranking": g3["clean"]["golden_ranking"], "per_mark_effects": ridge,
  "reliability_assessment": "n=400 with VIF ~6.5: per-predictor OLS is UNSTABLE (bootstrap sign flips); "
                            "reported regularized estimates with wide confidence intervals",
  "covariates_included": ["gc_content", "cpg_oe"], "subgroup_effects": None,
  "issues_found": ["small sample + collinearity: naive OLS not reliable here"],
  "analysis_usable": True, "trajectory": TRAJ})
W("hist_l2_ranking_run", 2, "simperfect", {
  "effect_ranking": [p for p in g3["clean"]["golden_ranking"] if p != "dnase"],
  "per_mark_effects": {"h3k4me3": ridge["h3k4me3"], "h3k27ac": ridge["h3k27ac"],
                       "h3k27me3": ridge["h3k27me3"], "dnase": ridge["dnase"]},
  "reliability_assessment": "prepared matrix omitted h3k27ac — re-included from the full table",
  "covariates_included": ["gc_content", "cpg_oe"], "subgroup_effects": None,
  "issues_found": ["model_matrix.csv omits h3k27ac (present in gene_table.csv) — omitted-variable bias "
                   "would inflate h3k4me3; re-included it"],
  "analysis_usable": True, "trajectory": TRAJ})
st = g3["aggregation_reversal"]["strata"]
W("hist_l2_ranking_run", 3, "simperfect", {
  "effect_ranking": g3["clean"]["golden_ranking"], "per_mark_effects": ridge,
  "reliability_assessment": "pooled slopes hide promoter-class heterogeneity — stratified by CGI status",
  "covariates_included": ["gc_content", "cpg_oe"],
  "subgroup_effects": {"CGI": {"h3k4me3": st["CGI"]["h3k4me3"], "h3k27me3": st["CGI"]["h3k27me3"]},
                       "nonCGI": {"h3k4me3": st["nonCGI"]["h3k4me3"], "h3k27me3": st["nonCGI"]["h3k27me3"]}},
  "issues_found": ["h3k27me3-expression slope differs CGI vs non-CGI — one pooled rule misleads"],
  "analysis_usable": True, "trajectory": TRAJ})

# ---------------- FOOLED ----------------
for cell, w in enumerate(["clean", "gc_cpg_confound", "outlier_leverage", "nonlinearity_saturation"]):
    W("hist_l2_regression_run", cell, "simfooled", {
      "estimates": {"pearson_r": g1[w].get("naive_pearson", g1[w].get("pearson_r")),
                    "spearman_rho": None, "adjusted_beta_std": None},
      "direction": "positive", "method_note": "Pearson correlation",
      "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("hist_l2_quantify_run", 0, "simfooled", {
  "output_path": csv_from("naive_k4me3_coverage_1kb", "f_clean.csv"),
  "method": {"tool": "pysam window counts", "normalization": "none", "peak_mode": "none",
             "window": "TSS +-1kb"},
  "signal_expression_spearman": g2["clean"]["naive_rho_vs_expr"], "direction": "positive",
  "domains": None, "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("hist_l2_quantify_run", 1, "simfooled", {
  "output_path": csv_from("naive_k27me3_coverage_10kb", "f_noinput.csv"),
  "method": {"tool": "pysam window counts", "normalization": "none", "peak_mode": "none",
             "window": "TSS +-10kb"},
  "signal_expression_spearman": g2["no_input_normalization"]["naive_rho_vs_expr"],
  "direction": "negative", "domains": None, "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("hist_l2_quantify_run", 2, "simfooled", {
  "output_path": csv_from("naive_k27me3_coverage_10kb", "f_broad.csv"),
  "method": {"tool": "macs3 callpeak (default)", "normalization": "macs3 uses the control lambda",
             "peak_mode": "narrow (default)", "window": "TSS +-10kb"},
  "signal_expression_spearman": -0.23, "direction": "negative",
  "domains": {"n": g2["broad_mark_narrow_default"]["narrow"]["n_peaks"],
              "total_mb": g2["broad_mark_narrow_default"]["narrow"]["total_bp"] / 1e6},
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("hist_l2_quantify_run", 3, "simfooled", {
  "output_path": csv_from("naive_k27me3_log2ratio_1kb", "f_window.csv"),
  "method": {"tool": "pysam window counts", "normalization": "log2 ratio to input control",
             "peak_mode": "none", "window": "TSS +-1kb (standard promoter definition)"},
  "signal_expression_spearman": g2["wrong_promoter_window"]["naive_rho_1kb"],
  "direction": "negative", "domains": None, "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
marg = g3["clean"]["marginal_r"]
W("hist_l2_ranking_run", 0, "simfooled", {
  "effect_ranking": g3["clean"]["marginal_ranking"], "per_mark_effects": marg,
  "reliability_assessment": "strong correlations across the genome; effects are solid",
  "covariates_included": [], "subgroup_effects": None,
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
ols400 = g3["multicollinearity"]["ols_marks_only"]
W("hist_l2_ranking_run", 1, "simfooled", {
  "effect_ranking": sorted(ols400, key=lambda p: -abs(ols400[p])), "per_mark_effects": ols400,
  "reliability_assessment": "OLS fit converged; coefficients reported",
  "covariates_included": [], "subgroup_effects": None,
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
prep = g3["omitted_confounder"]["ols_prepared"]
W("hist_l2_ranking_run", 2, "simfooled", {
  "effect_ranking": sorted(prep, key=lambda p: -abs(prep[p])), "per_mark_effects": prep,
  "reliability_assessment": "OLS on the provided modeling matrix",
  "covariates_included": [], "subgroup_effects": None,
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})
W("hist_l2_ranking_run", 3, "simfooled", {
  "effect_ranking": g3["clean"]["marginal_ranking"], "per_mark_effects": marg,
  "reliability_assessment": "one genome-wide effect per mark; reliable at n=19k",
  "covariates_included": [], "subgroup_effects": None,
  "issues_found": [], "analysis_usable": True, "trajectory": TRAJ})

# ---------------- grade both simulated agents ----------------
fail = 0
for suf, expect in (("simperfect", "3s"), ("simfooled", "traps<=1")):
    for run in ("hist_l2_regression_run", "hist_l2_quantify_run", "hist_l2_ranking_run"):
        r = subprocess.run([PY, str(HERE / "grade_hist_l2.py"), str(RES / run), suf],
                           capture_output=True, text=True)
        print(r.stdout.strip())
        if r.returncode:
            print(r.stderr[-500:]); fail += 1; continue
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
