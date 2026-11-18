"""cf_gwas (GWAS) track spec — loaded via task_spec.load('cf_gwas'). Fills the shared build_l1/build_l2/build_l3
skeletons with this track's domain slots. Add a new track = drop a tracks/<name>/spec.py exposing SPEC."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # repo root -> import task_spec
from task_spec import BASE, build_l1, MODELS, EFFICIENCY

GWAS_L1_SLOTS = dict(
    role="a statistical geneticist", subject="a GWAS summary-statistics file",
    object="these summary statistics", downstream="downstream analysis (e.g. TWAS)",
    input_line=("Dataset path: {path}   (tab-separated, gzip-compressed; one row per variant)\n"
                "Its directory may contain additional files describing the dataset."),
    sandbox=("The dataframe is preloaded as `df` (pandas as pd, numpy as np, scipy.stats as stats; "
             "statsmodels/sklearn importable); you may also read other files in the dataset's directory."))
# =========================================================================================================

# L2 prompt SLOTS for GWAS (fill run_level.L2_SKELETON via build_l2). Content is the SAME information as the
# former SIG/LOCUS/TWAS strings, just factored into role/goal/environment/sandbox/schema -> no re-run needed.
GWAS_L2_INFO = {
 "signaleda": dict(
   role="statistical geneticist doing exploratory QC on a GWAS BEFORE any downstream analysis",
   goal="decide whether this GWAS's association signal for {trait} is trustworthy for downstream analysis; inspect the signal however you see fit and report what you find",
   environment="Dataset path: {path}   (tab-separated, gzip; one row per variant)\nIts directory may contain additional files describing the dataset.",
   sandbox="Python sandbox: call run_python(code); `df` is preloaded (pandas/numpy/scipy); you may also read other files in the dataset's directory. Only printed text returns; no plots.",
   schema='{{"findings": "<your assessment of whether the signal is statistically sound and trustworthy for downstream analysis, with the specific evidence you found>",\n "usable_for_downstream": <true|false>,\n "trajectory": [{{"step": "<what you examined>", "finding": "<what you found>", "action": "<conclusion>"}}]}}'),
 "locus": dict(
   role="statistical geneticist analyzing GWAS summary statistics for {trait}",
   goal="identify the genome-wide-significant lead SNPs and group nearby variants into candidate loci. Genome-wide significance threshold: p < 5e-8. Distance-based locus rule: group significant variants within +-500kb of a lead SNP on the same chromosome. For each locus report the lead SNP and how many significant variants fall in it (is it one variant or many?)",
   environment="Dataset path: {path}   (tab-separated, gzip; one row per variant)\nIts directory may contain additional files describing the dataset.",
   sandbox="Python sandbox: call run_python(code); `df` is preloaded (pandas/numpy/scipy); you may also read other files in the dataset's directory. Only printed text returns; no plots. Run whatever you consider appropriate.",
   schema='{{"loci": [{{"chromosome": <int>, "lead_variant_id": "<id>", "lead_pos": <int>, "lead_pval": <float>, "n_variants_in_locus": <int>}}],\n "n_genome_wide_significant": <int>,\n "data_quality_flags": ["<any integrity problem you found and acted on, or empty>"],\n "analysis_usable": <true|false>,\n "notes": "<brief: is signal concentrated/broad; did corruption affect it>",\n "trajectory": [{{"step": "<what you examined>", "finding": "<what you found>", "action": "<what you did>"}}]}}'),
 "twas": dict(
   role="statistical geneticist",
   goal="run a transcriptome-wide association study (TWAS) for {trait} in {tissue} tissue — produce gene-level associations between genetically-predicted expression and the trait",
   environment="Available in the environment:\n- GWAS summary statistics: {path}   (tab-separated, gzip; also preloaded as the dataframe `df`)\n- A GTEx {tissue} gene-expression prediction model: {model_db}\n  and its SNP covariance file: {cov}\n- TWAS software is installed under: {software}   (choose the appropriate tool yourself)",
   sandbox="Prepare the GWAS as your chosen tool requires, run the TWAS, and verify the result is sound. You have a Python sandbox (run_python) with subprocess access — write files and run commands as needed. Your only writable location is the current working directory (`.`); write all outputs there. CRITICAL: only the interpreter you are already running in (`sys.executable`) has the tools' dependencies — always invoke Python tools as `[sys.executable, \"<tool>.py\", ...]`. Do NOT use \"/usr/bin/python3\", \"python3\" or \"python\" (they lack the dependencies and will fail).",
   schema='{{"output_path": "<absolute path to your final TWAS output CSV>", "tool_used": "<tool / command you ran>",\n "n_snps_used_total": <int or null>, "mapping_method": "<how you matched the GWAS SNPs to the model>",\n "issues_found": ["<any data problem you detected and had to fix, or empty>"],\n "analysis_usable": <true|false>,\n "trajectory": [{{"step": "<what you did>", "finding": "<what you found>", "action": "<what you concluded/did>"}}]}}'),
}

# verify RUBRICS live WITH the task info (relocated from verify_grades.py so verify_grades is a pure engine;
# stamp_methods stamps info["rubric"] -> manifest["verify_rubric"], which verify_grades reads). Mirrors build_l2.
GWAS_L2_INFO["signaleda"]["rubric"] = """L2 SIGNAL-EDA (0-3) = sum of THREE 0/1 axes (use the GROUND TRUTH block: true_lambda,
signal_status/correct_usability, implausible_top_region):
 AXIS 1 lambda_ok (0/1): did the agent estimate genomic inflation lambda_GC and land close to the TRUE lambda
   (inflated >~1.1 / deflated <~0.9 / ~1.0 clean)?
 AXIS 2 assess_ok (0/1): did its verbal assessment match the true signal status? inflated->'inflated/genomic control';
   deflated->'deflated/over-corrected'; null->'no real signal/uniform'; reasonable->'well-behaved/not inflated';
   suspicious->'artifact/spurious/batch/implausible'.
 AXIS 3 (category-dependent):
   - SUSPICIOUS world (an implausible_top_region like CFTR/gene-desert, or batch_concentration): 1 if it BOTH flagged
     that region/pattern AND qualified it (caution/verify/don't-green-light); 0.5 if only one; 0 if neither.
   - CLEAN world: 1 unless it WRONGLY declared the clean scan unusable (then 0).
   - OBJECTIVE corruption (inflation/deflation/null): 1 if its usable_for_downstream verdict matches correct_usability, else 0.
 SCORE = round(axis1 + axis2 + axis3) in 0-3. Do NOT force 'declare unusable' on suspicious/interpretive worlds."""
GWAS_L2_INFO["locus"]["rubric"] = """L2 LOCUS (0-3) = execution(0-2) + interpretation(0-1). EXECUTION: did the agent report the
correct genome-wide-significant lead SNPs/loci (recall+precision vs the reference leads, correct locus count, the
+/-500kb rule) AND handle this world's confound (detect the masked secondary signal / not fragment a long-range-LD
mega-locus / recover the true lead under p=0 underflow / NOT call the p~1e-6 suggestive decoy / avoid scattered
inflation fake loci)? 2=leads right + confound handled, 1=partially matched the reference, 0=leads wrong/missed.
INTERPRETATION(+1): explicitly named/flagged this world's issue. score = exec + interp."""
GWAS_L2_INFO["twas"]["rubric"] = """L2 TWAS (0-3). The agent ran a TWAS; score whether its gene-level output REPRODUCES the reference
S-PrediXcan result. 3 = high z-score correlation with the reference + proper model-SNP usage (correctly harmonized)
+ correct effect direction; 2 = reproduced but hand-rolled / partial; 1 = weak correlation; 0 = empty or SILENT-FAIL
(ran but ~0 model SNPs matched, or signs flipped). Near-binary: correct harmonization -> reproduce = 3, silent-fail = 0."""

CF_GWAS = {
    "name": "cf_gwas",
    "trait": "cystic fibrosis lung-disease severity",
    "reps": 1,                                   # n=1 per task: worlds are BUILT at 3 variants, then select_n1.py
                                                 # freezes ONE instantiation per issue (same cell for every model).
                                                 # Error bars come from the spread ACROSS tasks within a level
                                                 # (L1 mean +/- SD over 10 issue-types), not within a task. This
                                                 # cuts L1/L2 to 27 worlds/model and reuses already-run cells as-is.
                                                 # (manifest_full.json keeps the n=3 set; re-run select_n1.py to redo.)
    # BENCHMARKED models (7, weak->strong across 6 families). Exact API ids may need adjusting per provider;
    # available()-guarded so any without a key are skipped. Non-OpenAI route via models.OPENAI_COMPAT (+ Claude SDK).
    # 7 benchmarked models across 6 families. NOTE: gemini-3-pro-preview was RETIRED -> the live frontier
    # Gemini id is `gemini-3.1-pro-preview` (validated chat+agent). Reviewer Gemini is the distinct
    # gemini-3.1-flash-lite-preview, so no exact self-review.
    "models": MODELS,                 # Moonshot
    "clean_substrate": f"{BASE}/tracks/cf_gwas/data/gwas_cys_fib/bench_gwas_csfb_sample.tsv.gz",
    "docs": ["study_metadata.json", "data_dictionary.json"],   # discoverable, copied into each sealed world dir
    "docs_dir": f"{BASE}/tracks/cf_gwas/data/gwas_cys_fib",

    # ---- EFFICIENCY: every task records {in,out,total tokens, calls, wall_s, by_model} in its output `_meta`
    # (models.reset_meter/get_meter). Reported as a SEPARATE axis (quality-vs-cost Pareto) — NOT folded into
    # the quality rubric, so the rubric stays domain-neutral (the old text said "C/M/K/I/T" — never
    # implemented; see PAPER_NOTES section 3). token_budget = a SOFT cap per level:
    # over-budget sets an efficiency flag at aggregation time (never a hard mid-run stop; max_steps bounds the
    # loop). Budgets are PLACEHOLDERS to be recalibrated from the first fully-instrumented run's medians.
    "efficiency": EFFICIENCY,

    # ---- L1: QC / data integrity — inject ONE known defect per world; agent detects->diagnoses->acts ----
    # expected_method: what a competent analyst's PROCESS should look like (the deterministic graders +
    # verify_grades cross-check score the agent's actions/method against this per-task rubric, not a generic fallback).
    "L1": {
        "run_dir": f"{BASE}/tracks/cf_gwas/L1/results/gwas_qc_run",
        "prompt": build_l1(**GWAS_L1_SLOTS),                 # shared skeleton, GWAS slots (was a standalone string)
        "variants_per_world": 5000,
        "issues": ["clean", "duplication", "beta_outlier", "eaf_scale", "impossible_values",
                   "allele_invalid", "id_version_dup", "effect_sign_swap", "palindromic_high_maf",
                   "metadata_reconciliation"],   # 10 L1 issue-types (names match gwas_worlds.py / manifest)
        "variants_per_issue": 3,                 # 3 injected VARIANTS of each issue (distinct from reps)
        "expected_method": ("Systematically validate each column against its valid domain (p-value in [0,1]; "
            "EAF in [0,1]; chromosome in 1-22/X/Y; base-pair position > 0; alleles in {A,C,G,T}; check for "
            "duplicate rows and duplicate variant IDs; check the allele-frequency scale). Quantify how many "
            "rows are affected. Recommend a PROPORTIONATE remedy (rescale, flag, or drop the specific "
            "offending rows) — never a blanket destructive edit on clean data. When a defect is undetectable "
            "from the table alone (e.g. flipped effect signs), ABSTAIN and state that external evidence is "
            "needed rather than inventing a detectable defect."),
    },

    # ---- L2: analysis, robust to an injected confound — 3 sub-tasks, each its own worlds ----
    "L2": {
        "signaleda": {"run_dir": f"{BASE}/tracks/cf_gwas/L2/results/gwas_signaleda_run", "variants_per_world": 20000,
                      "info": GWAS_L2_INFO["signaleda"],
                      "issues": ["clean", "inflation", "deflation", "null_signal",
                                 "CFTR_artifact", "wrong_locus", "batch_concentration"],
                      "expected_method": ("Compute genomic inflation lambda_GC = median(chi2)/0.4549; inspect "
                          "the p-value distribution (QQ vs uniform); count genome-wide-significant hits; and "
                          "sanity-check the top region for biological plausibility. Distinguish true inflation "
                          "from a single artefactual peak or a batch/technical concentration. Give a calibrated "
                          "usability verdict and FLAG (not necessarily discard) suspicious-but-not-impossible "
                          "signals, stating what cannot be resolved from summary stats alone.")},
        "locus":     {"run_dir": f"{BASE}/tracks/cf_gwas/L2/results/gwas_task2_run", "info": GWAS_L2_INFO["locus"],
                      "issues": ["clean", "masked_secondary", "mega_locus", "pvalue_underflow",
                                 "threshold_edge", "scattered_fake_loci"],
                      "reference_loci": ["chr5", "chr11p13 (EHF/APIP)"],
                      "expected_method": ("Apply the stated threshold (p<5e-8) and the +/-500kb distance rule to "
                          "define loci and lead SNPs, reporting per-locus significant-variant counts. Recognize "
                          "the rule's LIMITS: a >1Mb signal may be one long-range-LD region OR several "
                          "independent signals (needs LD / conditional analysis), and isolated singleton 'hits' "
                          "are suspicious. Handle p-value underflow (ties at p=0) by ranking on the statistic. "
                          "Keep faithful algorithm execution separate from scientific interpretation.")},
        "twas":      {"run_dir": f"{BASE}/tracks/cf_gwas/L2/results/gwas_twas_run", "tissue": "Lung", "info": GWAS_L2_INFO["twas"],
                      "issues": ["clean", "build_mismatch", "allele_order_swap", "id_only"],
                      "golden_truth": f"{BASE}/tracks/cf_gwas/L2/twas_cys_fib/csfb_Lung_spredixcan_varid.csv",
                      "model_db": f"{BASE}/tracks/cf_gwas/L2/predictdb_gtex_v8/eqtl/mashr/mashr_Lung.db",
                      "cov": f"{BASE}/tracks/cf_gwas/L2/predictdb_gtex_v8/eqtl/mashr/mashr_Lung.txt.gz",
                      "software": f"{BASE}/tracks/cf_gwas/L2/MetaXcan/software",
                      "sandbox_py": "/home/anonymous/miniconda3/envs/metaxcan/bin/python",
                      "expected_method": ("HARMONIZE the GWAS to the model's variant IDs BEFORE running "
                          "(genome build, GTEx varID chr_pos_ref_alt_b38, allele order / effect-allele "
                          "orientation). Choose an appropriate tool (e.g. S-PrediXcan / MetaXcan). CRITICALLY "
                          "VERIFY the run actually used a non-trivial number of model SNPs — a complete-looking "
                          "12k-gene result built from ~0 matched SNPs is a SILENT FAILURE — and sanity-check "
                          "gene z-scores/directions before declaring the result usable.")},
    },

    # ---- L3: hypothesis + adversarial review; 1 real world + a COUNTERFACTUAL PANEL of flipped genes ----
    "L3": {
        "run_dir": f"{BASE}/tracks/cf_gwas/L3/results/l3_run",
        # 3 cross-family reviewers, each grading ALL dimensions (avg across models); DIFFERENT models than
        # both the judge and the benchmarked set (same-family overlap OK). judge = GPT-5.5 (OpenAI, independent).
        # NONE are Anthropic -> L3 runs without ANTHROPIC_API_KEY (glm-4.6 replaced claude-sonnet-5).
        "reviewers": [["rev_zhipu", "glm-4.6"], ["rev_google", "gemini-3.1-flash-lite-preview"],
                      ["rev_deepseek", "deepseek-reasoner"]],
        "judge": "gpt-5.5", "judge_k": 3, "rounds": 3,
        "expected_method": ("Ground every claim in the supplied evidence; treat a TWAS/association result as "
            "ASSOCIATION, not causation. When the data conflicts with established literature, acknowledge the "
            "conflict explicitly, PRESERVE the data-supported direction, lower confidence, and request "
            "colocalization / replication / sensitivity analysis — rather than flipping to match the prior or "
            "fabricating support. Concede only to evidence, not to authority."),
        # each screened with the prior probe (both benchmarked models must KNOW the direction, else confounded)
        # NOTE: the AUTHORITATIVE panel lives in l3_dossier.py `PANEL` (re-selected via screen_cf_genes.py; the old
        # TGFB1/TNF/SLC26A9 1-2-SNP panel was REJECTED). This list is documentation only — kept in sync with PANEL.
        "counterfactual_panel": [
            {"gene": "GSTM1", "cf_z": +5.58, "direction": "deleterious", "textbook": "protective"},
            {"gene": "TGFB1", "cf_z": -5.49, "direction": "protective", "textbook": "deleterious"},
        ],  # SFTPD removed (failed knew_prior for kimi+glm). GSTM1 has a residual kimi exclusion (per-model handled).
    },
}

SPEC = CF_GWAS
