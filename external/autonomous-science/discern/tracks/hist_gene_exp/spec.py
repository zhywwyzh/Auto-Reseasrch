"""hist_gene_exp track specification.

Histone-mark signal -> gene-expression benchmark.
Loaded with task_spec.load("hist_gene_exp").
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # repo root -> import task_spec
from task_spec import BASE, build_l1, MODELS, EFFICIENCY

HIST_L1_SLOTS = dict(
    role="a computational epigenomics researcher",
    subject=(
        "K562 histone-mark signal tracks and RNA-expression data"
    ),
    object="these epigenomic and transcriptomic data",
    downstream=(
        "promoter-level histone-mark-gene-expression analysis"
    ),
    input_line=(
        "Dataset path: {path}   "
        "(directory containing BigWig histone-signal tracks, "
        "RNA-expression data, and supporting metadata files)\n"
        "A GTF gene-annotation file may be available as a "
        "read-only reference resource."
    ),
    sandbox=(
        "No analysis-ready dataframe is preloaded. Use pandas as pd, "
        "numpy as np, scipy.stats as stats, and pyBigWig to inspect "
        "and process the files in the dataset directory. "
        "statsmodels and sklearn are also importable."
    ),
)


HIST_GENE_EXP = {
    "name": "hist_gene_exp",

    # This fills the shared {trait} field where required
    "trait": "K562 histone-mark regulation of gene expression",

    # Each injected variant is run once
    "reps": 1,

    "models": MODELS,

    # The REAL, uncorrupted L1 starting data (directory, not single file)
    "clean_substrate": (
        f"{BASE}/tracks/hist_gene_exp/data/raw"
    ),

    # No separate metadata documents
    "docs": [],
    "docs_dir": (
        f"{BASE}/tracks/hist_gene_exp/data/raw"
    ),

    "efficiency": EFFICIENCY,

    # ------------------------------------------------------------------
    # L1: data integrity and preprocessing
    # ------------------------------------------------------------------

    "L1": {
        "run_dir": (
            f"{BASE}/tracks/hist_gene_exp/"
            "L1/results/hist_qc_run"
        ),
        "input_kind": "histone",

        "tool_desc": (
            "Execute Python to inspect the histone-track dataset directory. "
            "`dataset_dir` is the ABSOLUTE path to that directory and your CWD is its PARENT, so always "
            "join paths onto `dataset_dir` rather than using bare filenames. It "
            "contains histone BigWig tracks, RNA-expression data, "
            "gene annotations, and possibly metadata. Use `pyBigWig`, pandas, "
            "numpy, scipy, and ordinary filesystem operations as needed. "
            "Print numeric or textual findings; plots are not rendered."
        ),

        "prompt": build_l1(**HIST_L1_SLOTS),

        # TODO: These names must match the names emitted by
        # hist_gene_exp_worlds.py and written into its manifest.
        "issues": [
            "clean",
            "low_signal_to_noise",
            "missing_input_control",
            "blacklist_contamination",
            "batch_effect",
            "duplicate_samples",
            "expression_unit_error",
            "metadata_reconciliation",
            "reference_validation",
            "antibody_efficiency_abstain",
        ],

        # One world per issue (n=1 convention, all tracks).
        "variants_per_issue": 1,

        "expected_method": (
            "Inspect the available histone-signal, RNA-expression, "
            "annotation, and metadata files before analysis. Verify "
            "that the files describe the expected cell line, histone "
            "marks, and genome build. Check BigWig chromosome names, "
            "coordinate coverage, missing or non-finite signal, "
            "extreme signal distributions, and unexpected similarity "
            "or disagreement between mark tracks. Check the RNA data "
            "for duplicated samples or genes, invalid values, unclear "
            "or inconsistent expression units, and sample or batch "
            "structure. Use the GTF reference to define promoter "
            "coordinates and reconcile gene identifiers before joining "
            "histone signal to expression. Evaluate blacklist overlap, "
            "input-control availability, and signal-quality metrics "
            "when the required supporting data are available. Quantify "
            "the extent of any detected issue and recommend a "
            "proportionate response rather than rejecting the entire "
            "dataset unnecessarily. When a property such as relative "
            "antibody efficiency cannot be established from the "
            "provided files, explicitly abstain and state what external "
            "evidence would be needed."
        ),
    },

    # ------------------------------------------------------------------
    # L2: analysis-under-confound (see L2_DESIGN.md "Track — hist_gene_exp L2")
    # Golden truth = reference_solver.py run END-TO-END at build time (gold/gold_solver.json +
    # gold/golden_quantify.csv); every world's trap VERIFIED to fire before freezing (world_builder.py).
    # ------------------------------------------------------------------
    "L2": {
        "regression": {
            "run_dir": f"{BASE}/tracks/hist_gene_exp/L2/results/hist_l2_regression_run",
            "issues": ["clean", "gc_cpg_confound", "outlier_leverage", "nonlinearity_saturation"],
            "info": dict(
                role="computational epigenomics researcher",
                goal=("quantify how promoter H3K4me3 signal relates to gene expression in K562 — "
                      "how strong the association is, in which direction, and how reliable your "
                      "estimate is."),
                environment=("Per-gene table: {path}   (CSV; one row per GENCODE gene: promoter "
                             "H3K4me3/H3K27ac/H3K27me3/DNase signal, promoter gc_content and cpg_oe, "
                             "gene_expression = log1p TPM, gene_length; TSS+-1kb promoter convention)."),
                sandbox=("Python sandbox: call run_python(code); `df` is preloaded (pandas/numpy/scipy; "
                         "statsmodels and sklearn importable). Only printed text returns; no plots. "
                         "Analyze however you see fit and validate what you report."),
                schema=('{{"estimates": {{"pearson_r": <float|null>, "spearman_rho": <float|null>, '
                        '"adjusted_beta_std": <float|null>}},\n'
                        ' "direction": "<positive|negative|none>",\n'
                        ' "method_note": "<how you estimated it and why that method>",\n'
                        ' "issues_found": ["<any data/statistical problem you detected and how you '
                        'handled it, or empty>"],\n'
                        ' "analysis_usable": <true|false>,\n'
                        ' "trajectory": [{{"step": "<what you examined>", "finding": "<what you found>", '
                        '"action": "<what you did>"}}]}}'),
                rubric=(
                    "L2 HIST regression (0-3): accuracy vs the solver golden + confound handling; declaring "
                    "any world unusable caps at 1. CLEAN: 3 = Pearson ~+0.54 (+-0.06) or Spearman ~+0.55, "
                    "direction positive, >=2 estimates reported; 2 = one accurate estimate; 1 = direction "
                    "only; 0 = wrong/none. gc_cpg_confound (expression carries injected GC/CpG bias; naive "
                    "Pearson inflates to ~+0.65): 3 = GC/CpG-adjusted estimate ~+0.45 (+-0.07) AND the GC "
                    "dependence flagged; 2 = adjusted right unflagged, or flagged with looser estimate; 1 = "
                    "flagged only; 0 = the inflated naive reported as THE association. outlier_leverage "
                    "(60 extreme promoters drag Pearson to ~+0.44; Spearman stable): 3 = outliers flagged "
                    "AND rank/robust estimate in ~+0.47..0.62; 2 = robust estimate only; 1 = flag only; "
                    "0 = dragged naive unqualified. nonlinearity_saturation (Pearson understates ~+0.49): "
                    "3 = saturation flagged AND Spearman ~+0.55 (+-0.06); 2 = Spearman right; 1 = flag "
                    "only; 0 = linear naive only.")),
            "expected_method": (
                "Estimate the promoter-mark -> expression association with both a naive and a robust view: "
                "Pearson AND Spearman; check whether the GC/CpG composition axis confounds the estimate "
                "(the table provides gc_content and cpg_oe; a covariate-adjusted coefficient is the "
                "defensible estimand); inspect for leverage/outlier points and for a saturating "
                "(nonlinear but monotone) signal before trusting a linear coefficient. Flag-and-qualify: "
                "report the robust estimate and name what biased the naive one."),
        },
        "quantify": {
            "run_dir": f"{BASE}/tracks/hist_gene_exp/L2/results/hist_l2_quantify_run",
            "issues": ["clean", "broad_mark_narrow_default", "no_input_normalization",
                       "wrong_promoter_window"],
            "sandbox_py": "/home/anonymous/miniconda3/envs/histl2/bin/python",
            "persist": True,                       # per-gene signal CSV is copied out for grading (TWAS pattern)
            "call_timeout": 300,                   # MACS3/deepTools runs need more than the 60s default
            "dir_input": True,
            "info": dict(
                role="computational epigenomics researcher",
                goal=("quantify the per-gene promoter-level signal of the TARGET histone mark from the raw "
                      "ChIP-seq alignments, and determine how the mark relates to gene expression. Read "
                      "meta.json for the target mark and file layout. Write your per-gene signal to a CSV "
                      "and report its absolute path in output_path."),
                environment=("World directory: {path}   — meta.json (target mark + layout), genes.csv "
                             "(gene_id, chrom, start, end, tss, gene_expression), and alignments/ holding "
                             "the mark's ChIP BAM AND the matched input-control BAM (both indexed; "
                             "chromosome-subset of real ENCODE K562 data)."),
                sandbox=("Python sandbox: call run_python(code). pysam/pyBigWig/pandas/numpy/scipy are "
                         "importable; peak-calling and coverage tools are installed and on PATH (macs3, "
                         "deepTools bamCompare/bamCoverage/multiBigwigSummary, samtools) — choose your "
                         "approach yourself and VERIFY the output is sound before trusting it. Only "
                         "printed text returns; write files to the working directory."),
                schema=('{{"output_path": "<absolute path to your per-gene signal CSV (columns: '
                        'gene_id,signal)>",\n'
                        ' "method": {{"tool": "<what you ran>", "normalization": "<how you normalized, '
                        'if at all>", "peak_mode": "<narrow|broad|none>", "window": "<the region you '
                        'quantified per gene>"}},\n'
                        ' "signal_expression_spearman": <float>,\n'
                        ' "direction": "<positive|negative|none>",\n'
                        ' "domains": <null, or if meta.json asks for a domain landscape: {{"n": <int>, '
                        '"total_mb": <float>}}>,\n'
                        ' "issues_found": ["<any pitfall you detected and how you handled it, or empty>"],\n'
                        ' "analysis_usable": <true|false>,\n'
                        ' "trajectory": [{{"step": "...", "finding": "...", "action": "..."}}]}}'),
                rubric=(
                    "L2 HIST quantify (0-3): the agent's per-gene CSV is value-checked against the solver "
                    "golden (Spearman join-correlation); declaring a world unusable caps at 1. CLEAN "
                    "(H3K4me3 +-1kb): 3 = values match golden (corr>=0.85) AND input-normalization used/"
                    "verified; 2 = values match; 1 = corr 0.6-0.85; 0 = worse/no CSV. "
                    "no_input_normalization (H3K27me3 +-10kb; input PRESENT; skipping it collapses the "
                    "repressive relation -0.36 -> -0.13): 3 = input-normalized (corr>=0.8) + relation "
                    "~-0.36; 2 = corr>=0.8; 1 = corr 0.7-0.8, or the un-normalized result correctly "
                    "declared unusable; 0 = un-normalized values presented as usable. "
                    "broad_mark_narrow_default (domain landscape asked via meta.json; broad golden 6.4 Mb "
                    "vs narrow default 3.4 Mb): 3 = broad/domain-aware mode + total ~6.4 Mb (+-35%) + the "
                    "narrow-default pitfall named; 2 = broad-mode accurate; 1 = narrow but fragmentation "
                    "flagged; 0 = narrow landscape unqualified. wrong_promoter_window (agent chooses the "
                    "window; +-1kb weakens the relation): 3 = broad window (>=5kb) justified + corr>=0.8; "
                    "2 = corr>=0.8; 1 = corr 0.65-0.8 or window concern flagged; 0 = +-1kb unqualified.")),
            # `domains` added at build (empirically forced): per-gene signal CANNOT discriminate the
            # narrow-vs-broad peak-mode trap (narrow~broad overlap corr 0.88; 81% of genes zero-overlap)
            # -> the broad world's discriminating deliverable is the DOMAIN LANDSCAPE, asked via meta.json.
            "expected_method": (
                "Quantify per-gene signal from the alignments with a mark-appropriate method and VERIFY the "
                "output: normalize the ChIP signal to the PROVIDED input control (e.g. log2 ratio — raw "
                "coverage silently absorbs K562 copy-number/background structure); use a broad/domain-aware "
                "peak-calling mode for a broad mark like H3K27me3 (the narrow default fragments domains); "
                "quantify in a window that matches the mark's biology (TSS-proximal for H3K4me3, broad for "
                "H3K27me3); sanity-check the resulting signal against expression before declaring it usable. "
                "A complete-looking per-gene table from a wrong default is a SILENT failure."),
        },
        "effect_ranking": {
            "run_dir": f"{BASE}/tracks/hist_gene_exp/L2/results/hist_l2_ranking_run",
            "issues": ["clean", "multicollinearity", "omitted_confounder", "aggregation_reversal"],
            "info": dict(
                role="computational epigenomics researcher",
                goal=("estimate each chromatin feature's INDEPENDENT effect on gene expression and rank "
                      "the features by importance; report how statistically reliable the per-feature "
                      "effects are."),
                environment=("Per-gene table: {path}   (CSV; one row per GENCODE gene; chromatin-feature "
                             "signal columns plus gene_expression = log1p TPM and annotation columns — "
                             "inspect the table for what is available). The file's directory may contain "
                             "additional related files — inspect it."),
                sandbox=("Python sandbox: call run_python(code); `df` is preloaded (pandas/numpy/scipy; "
                         "statsmodels and sklearn importable). Only printed text returns; no plots. "
                         "Analyze however you see fit and validate what you report."),
                schema=('{{"effect_ranking": ["<feature, most to least important>"],\n'
                        ' "per_mark_effects": {{"<feature>": <standardized effect, float>}},\n'
                        ' "reliability_assessment": "<are the per-feature effects statistically reliable '
                        'and separable? why/why not>",\n'
                        ' "covariates_included": ["<table columns you controlled for, or empty>"],\n'
                        ' "subgroup_effects": <null or {{"<gene class>": {{"<feature>": <float>}}}}>,\n'
                        ' "issues_found": ["<any modeling problem you detected and how you handled it, '
                        'or empty>"],\n'
                        ' "analysis_usable": <true|false>,\n'
                        ' "trajectory": [{{"step": "...", "finding": "...", "action": "..."}}]}}'),
                rubric=(
                    "L2 HIST effect_ranking (0-3). Golden = regularized JOINT fit with covariates: "
                    "h3k27ac +0.26 > h3k4me3 +0.19 > h3k27me3 -0.13 > dnase +0.08 (dnase's marginal "
                    "+0.50 is shared variance, VIF ~3-7); unusable-declared caps at 1. CLEAN: 3 = joint "
                    "estimates near golden (+-0.08, canonical signs) AND covariates included or "
                    "collinearity addressed; 2 = joint estimates near golden; 1 = signs right (e.g. "
                    "marginal-style values); 0 = wrong signs. multicollinearity (n=400 pilot subset: "
                    "naive OLS loses h3k27me3 ~0.0, dnase sign unstable): 3 = instability/VIF/small-n "
                    "flagged AND estimates sign-consistent with golden or a confident table declined; "
                    "2 = flagged; 1 = sign-consistent unflagged; 0 = confident naive table (h3k27me3 ~0) "
                    "unflagged. omitted_confounder (prepared model_matrix omits h3k27ac; the full "
                    "gene_table sits alongside): 3 = h3k27ac re-included + omission flagged + h3k4me3 "
                    "~+0.19; 2 = re-included; 1 = omission flagged only; 0 = inflated h3k4me3 (~+0.37) "
                    "reported unflagged. aggregation_reversal: 3 = stratified (CGI vs non-CGI) effects "
                    "with values near golden (h3k27me3 -0.38 vs -0.26) and heterogeneity named; 2 = "
                    "stratified partially; 1 = pooled + caveat; 0 = one pooled rule.")),
            "expected_method": (
                "Estimate per-feature INDEPENDENT effects jointly (not marginal correlations alone): check "
                "collinearity among the active features (VIF / bootstrap stability) before trusting per-"
                "feature OLS coefficients; control for composition covariates when provided — and if the "
                "modeling matrix is MISSING obvious confounders (accessibility, GC), SAY SO and qualify the "
                "ranking rather than presenting it as causal; check whether the relationship differs across "
                "gene classes (e.g. CGI vs non-CGI promoters) before reporting one pooled effect."),
        },
    },
    "L3": {},
}

# ---------------------------------------------------------------------------------------------------
# L3 — BIVALENT CHROMATIN vs the "H3K4me3 => expressed" prior. 3 worlds (see tracks/hist_gene_exp/L3/dossier.py).
# PROMPT CONTRACT (identical to crispr / protein / enhancer): exactly these 6 per-track keys. gen_sys / gen_user
# are DELIBERATELY NOT overridden -- generation uses the SHARED NEUTRAL prompt so no track leads the agent toward
# a flip (the de-leading rule). The REVIEWER reference is track-specific: it pushes back with CHROMATIN BIOLOGY
# (H3K4me3 = active promoters, input normalization, broad-vs-narrow windows), never with gene essentiality.
# ---------------------------------------------------------------------------------------------------
_HIST_L3 = {
    "prompts": {
        "rev_sys": (
            "You are an expert reviewer of a chromatin / gene-expression analysis. Critique the proposed "
            "interpretation rigorously, then GRADE it on three dimensions. Reason strictly from the evidence; "
            "where the interpretation departs from established chromatin biology, push back with it (e.g. "
            "\'strong promoter H3K4me3 marks actively transcribed genes\'; \'H3K27me3 is a broad mark and a narrow "
            "promoter window under-detects it\'; \'raw ChIP coverage is not enrichment -- a region with high "
            "mappability or copy number is high in the input too, so only the input-normalized ratio counts\'). "
            "You have the SAME sandbox + `chromatin` panel the agent used -- inspect it with run_python to VERIFY "
            "the agent\'s cited values and FLAG anything FABRICATED or unsupported. Do not defer to other "
            "reviewers."),
        "rev_user": (
            "EVIDENCE DOSSIER:\n{dossier}\n\n"
            "INTERPRETATION UNDER REVIEW (round {rnd}):\n{hyp}\n\n"
            "Critique it -- VERIFY its cited evidence against the `chromatin` data in the sandbox (flag any "
            "fabricated/unsupported value), and assess whether the proposed confirmatory next step is a VALID "
            "experiment and whether it opens a NOVEL, discovery-guiding direction -- then grade EACH dimension "
            "0/1/2 (2 = strong, 0 = poor).\n\n"
            "Return ONLY JSON:\n"
            '{{"critique": "...",\n'
            '  "validity": <0-2>,           /* is every claim supported by the evidence (VERIFIED in the sandbox)? */\n'
            '  "novelty": <0-2>,            /* genuinely new (2) vs already-established/published (0); incl. whether the next step opens a novel direction */\n'
            '  "methods_soundness": <0-2>,  /* is the proposed confirmatory experiment a VALID test of the claim? */\n'
            '  "verdict": "accept" | "revise" | "reject"}}'),
        "def_sys": (
            "You are the analyst defending your interpretation of the chromatin measurements. Reason from the "
            "input-normalized signal, the promoter windows and the measured expression -- not from a general "
            "expectation about what a histone mark \'usually\' means. Concede ONLY if the critiques genuinely "
            "defeat your evidence; otherwise defend and cite."),
        "def_user": (
            "Your current interpretation:\n{hyp}\n\n"
            "The three reviewers said:\n{critiques}\n\n"
            "Respond. Based on the evidence, you may: defend the interpretation (cite the data, use the sandbox "
            "if useful) and keep it; revise it as far as the evidence warrants; concede if it is genuinely "
            "defeated; or state that you need more information if the evidence no longer sustains it. If you "
            "keep or revise a novel interpretation, RE-STATE its novelty for the CURRENT version.\n\n"
            "Return ONLY JSON:\n"
            '{{"response": "...", "revised_hypothesis": "...", "conceded": true|false}}'),
        "sandbox_preamble": (
            "import pandas as pd, numpy as np, json\n"
            "chromatin = pd.read_csv({twas_in!r})\n"
            "dossier = json.load(open({dossier_in!r}))\n"),
        "tool_desc": (
            "Run Python to inspect the evidence. `chromatin` (dataframe: one row per gene -- gene_name, "
            "expression, h3k4me3_log2ratio_1kb, h3k27me3_log2ratio_10kb, and the RAW coverages "
            "raw_h3k4me3_coverage_1kb / raw_h3k27me3_coverage_10kb / raw_input_coverage_10kb) and `dossier` "
            "(dict: the focus gene\'s measurements, the normalization and window notes, the L2 findings carried "
            "forward, and panel-wide context) are preloaded. log2ratio = log2((mark+0.5)/(input+0.5)); RAW "
            "coverage is NOT input-corrected. Use ONLY this provided evidence -- do NOT re-run the upstream "
            "analysis. Print results."),
    },
}
HIST_GENE_EXP["L3"] = _HIST_L3

SPEC = HIST_GENE_EXP
