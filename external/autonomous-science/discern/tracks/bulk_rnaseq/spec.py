"""bulk_rnaseq (bulk RNA-seq differential-expression + pathway) track spec — loaded via task_spec.load('bulk_rnaseq').
Fills the shared build_l1 skeleton with this track's domain slots. Add a new track = drop tracks/<name>/spec.py.

Track 4 of the suite (TRACKS_PLAN.md). L1 = PURE QC on a RAW gene x sample read-count matrix (+ a sample
metadata table) — all per-sample / per-gene / format / identity checks, NO differential expression, normalization
modeling, or pathway analysis (those need the analysis -> L2). Substrate = a real human PBMC bulk RNA-seq screen
(GEO GSE152418, Arunachalam et al. Science 2020; see build_substrate.py); worlds injected by world_builder.py;
graded by the shared grade_generic (manifest-driven — the world_builder writes each world's canonical_checks /
diagnose / action ground truth). L2 / L3 are declared in TRACKS_PLAN.md and added later.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # repo root -> task_spec
from task_spec import BASE, build_l1, MODELS, EFFICIENCY

RES = f"{BASE}/tracks/bulk_rnaseq/data/resources"                        # read-only reference (mounted ro_paths)
ANNOT = f"{RES}/gene_annotation.tsv"

# ---- L1: fill the SHARED L1 skeleton with bulk-RNA-seq domain slots (a raw count MATRIX, preloaded as `df`) ----
BULKRNA_L1_SLOTS = dict(
    role="a computational biologist QC'ing a bulk RNA-seq experiment before differential-expression analysis",
    subject="a raw gene x sample read-count matrix (plus a companion sample metadata table) from a bulk RNA-seq study",
    object="these counts and their sample metadata",
    downstream="downstream differential-expression and pathway analysis (low-count filtering, normalization, "
               "DE testing, and gene-set enrichment)",
    input_line=("Dataset path: {path}   (tab-separated, gzip-compressed; one row per gene, one column per sample)\n"
                "Columns: gene_id (Ensembl gene identifier), followed by one raw-integer read-count column per sample.\n"
                "A companion sample metadata table 'sample_metadata.tsv' is in the same directory: it describes each "
                "sample (experimental condition, annotated sex, dataset provenance fields, and per-sample "
                "sequencing / QC summary metrics). Its directory may contain additional files describing the dataset."),
    resources=("\n\nA read-only reference is available (mounted at this absolute path):\n"
               f"  - {ANNOT}   (gene annotation: gene_id -> symbol, chromosome, biotype; tab-separated).\n"
               "You may read it to map gene ids to symbols / chromosomes / biotypes."),
    sandbox=("The count matrix is preloaded as `df` (pandas as pd, numpy as np, scipy.stats as stats; "
             "statsmodels/sklearn importable); you may also read the sample metadata table, the gene annotation "
             "above, and any other files in the dataset's directory."))

BULK_RNASEQ = {
    "name": "bulk_rnaseq",
    "trait": "bulk RNA-seq gene expression (human PBMC, COVID-19 vs healthy)",
    "reps": 1,                                                # n=1 per issue (one world per issue), like every track
    "models": MODELS,                                         # same 7-model roster
    "docs_dir": f"{BASE}/tracks/bulk_rnaseq/data",
    "docs": ["data_dictionary.json", "study_metadata.json"], # generic, issue-neutral; copied into each sealed world dir (no leak)
    "efficiency": EFFICIENCY,
    "L1": {
        "run_dir": f"{BASE}/tracks/bulk_rnaseq/L1/results/bulkrna_l1_run",
        "input_kind": "bulkrna",                              # a flat gene x sample tab-gz matrix -> run_level uses std_hdr (preloads `df`) AND honors this track's tool_desc
        "ro_paths": [ANNOT],                                  # gene annotation -> sealed read-only mount
        "tool_desc": ("Execute Python on the count matrix `df` (raw bulk RNA-seq gene x sample counts). The sample "
                      "metadata table 'sample_metadata.tsv' is in the working directory and the gene annotation is "
                      "readable at the absolute path given in the task. Print numeric summaries."),
        "prompt": build_l1(**BULKRNA_L1_SLOTS),               # shared skeleton, bulk-RNA-seq slots
        # 10 issue-types (clean + 8 defects + 1 abstention). PURE QC: every defect is visible from the RAW counts /
        # sample metadata (+ the mounted annotation) WITHOUT running DE / normalization / GSEA (those are L2).
        # Order matches world_builder.py.
        "issues": ["clean",
                   "library_size_outlier",      # one sample's total depth is a gross outlier
                   "low_count_genes_unfiltered", # pathological excess of all-zero / near-zero genes (unfiltered)
                   "rrna_depletion_failure",    # rRNA-depletion failure -> rRNA/Mt_rRNA dominate some libraries
                   "globin_contamination",      # globin (HBA/HBB) bleed -> hemoglobin genes dominate some libraries
                   "rna_degradation",           # degraded RNA: low RIN + 3' bias + collapsed transcriptome complexity
                   "gdna_contamination",        # genomic-DNA carry-over: high intronic fraction + broad low-level background
                   "sample_sex_swap",           # stated sex contradicts XIST/RPS4Y expression (sample-identity QC)
                   "metadata_reconciliation",   # provenance labels (organism/build) contradict the gene-id namespace
                   "abstain_divergent_sample"], # ABSTAIN: a real severe-COVID sample is a genuine outlier -> retain, don't drop
        "variants_per_issue": 1,
        "expected_method": (
            "QC the RAW count matrix + sample metadata from summary statistics BEFORE any filtering, normalization, "
            "or DE. Check LIBRARY SIZE / DEPTH per sample (total counts; flag gross depth outliers); the LOW-COUNT "
            "GENE burden (fraction of all-zero / near-zero genes, genes detected above a CPM threshold — an excess "
            "must be filtered before median-of-ratios normalization); rRNA / GLOBIN CONTAMINATION (fraction of each "
            "library's counts in rRNA/Mt_rRNA and hemoglobin (HBA/HBB) genes — a failed rRNA depletion or globin "
            "bleed inflates it in some samples); RNA DEGRADATION / 3' BIAS (low RIN, high 3'/5' bias, collapsed "
            "transcriptome complexity — fewer detected genes, counts concentrated in few genes); gDNA CONTAMINATION "
            "(high intronic-read fraction + a broad low-level count background across normally-silent genes / "
            "pseudogenes); SAMPLE IDENTITY (infer sex from XIST vs Y-genes RPS4Y1/DDX3Y and reconcile with the "
            "STATED sex — a mismatch is a sample swap/mislabel); and METADATA RECONCILIATION (the provenance labels "
            "organism / genome build must agree with the gene-id namespace — human ENSG ids contradict a non-human "
            "organism claim). Quantify how many samples/genes are affected and recommend a PROPORTIONATE remedy "
            "(flag / re-sequence / drop or down-weight the offending samples, filter low-count genes, correct the "
            "labels) — never a blanket destructive edit on clean data. A single sample that is genuinely divergent "
            "for BIOLOGICAL reasons (e.g. a severe-disease transcriptome) is REAL signal, not a defect: do NOT drop "
            "it as an outlier, and abstain from inventing a problem when the data is well-formed."),
    },
    # ------------------------------------------------------------------
    # L2: analysis-under-confound (see L2_DESIGN.md "Track — bulk_rnaseq L2" + its BUILD ADDENDUM).
    # Golden truth = reference_solver.py run END-TO-END at build time (L2/gold/gold_solver.json +
    # golden_de*.csv); every world's trap VERIFIED to fire before freezing (world_builder.py).
    # Worlds are DIRECTORIES (meta.json describes the task inputs; prepared 'convenience' artifacts
    # implement the naive path where data would otherwise equal clean — the hist model_matrix pattern).
    # ------------------------------------------------------------------
    "L2": {
        "de": {
            "run_dir": f"{BASE}/tracks/bulk_rnaseq/L2/results/bulk_l2_de_run",
            "issues": ["clean", "batch_confound", "normalization_default", "hidden_covariate"],
            "sandbox_py": "/home/anonymous/miniconda3/envs/bulkl2/bin/python",
            "persist": True,                       # the agent's DE CSV is copied out for value-grading
            "call_timeout": 300,                   # PyDESeq2 fits need more than the 60s default
            "dir_input": True,
            "info": dict(
                role="computational biologist analyzing a bulk RNA-seq case-control cohort",
                goal=("perform the differential-expression analysis described in meta.json (COVID-19 vs "
                      "Healthy PBMC) with a defensible method, verify your result is sound, write the "
                      "per-gene result to a CSV, and report its absolute path in output_path."),
                environment=("World directory: {path}   — meta.json (task + file layout), the raw count "
                             "matrix, sample_metadata.tsv (condition plus per-sample QC covariates), and "
                             "possibly additional prepared files. Inspect the directory yourself."),
                sandbox=("Python sandbox: call run_python(code). pydeseq2 / statsmodels / sklearn / "
                         "scipy / pandas are importable. Only printed text returns; write files to the "
                         "working directory. Choose your approach yourself and VERIFY the output before "
                         "trusting it."),
                schema=('{{"output_path": "<absolute path to your DE CSV (columns: gene_id,'
                        'log2FoldChange,pvalue,padj)>",\n'
                        ' "method": {{"tool": "<what you ran>", "normalization": "<how counts were '
                        'normalized>", "design": "<the model/covariates you fit>"}},\n'
                        ' "n_de_padj05": <int>,\n'
                        ' "issues_found": ["<any confound/pitfall you detected and how you handled it, '
                        'or empty>"],\n'
                        ' "analysis_usable": <true|false>,\n'
                        ' "trajectory": [{{"step": "...", "finding": "...", "action": "..."}}]}}'),
                rubric=(
                    "L2 BULK de (0-3): the agent's per-gene DE CSV is value-checked against the solver golden (logFC corr + "
                    'top-500 jaccard); declaring a world unusable caps at 1; a 0-code-cells numeric answer caps at 1 '
                    '(fabrication). CLEAN: 3 = matches golden (top500-jac >= 0.75) with a sound method; 2 = matches; 1 = jac '
                    '0.5-0.75; 0 = worse/no CSV. batch_confound (injected discoverable batch partially aligned with '
                    'condition): 3 = discovered + modeled the batch (matches golden) AND flagged it; 2 = matches golden '
                    'silently; 1 = naive `~condition` but latent structure flagged; 0 = naive result unqualified. '
                    'normalization_default (a prepared CPM matrix rides along; total-count normalization inherits the '
                    'plasmablast/IG composition bias): 3 = raw-counts + proper size factors (matches golden) AND the '
                    'composition/normalization issue named; 2 = matches; 1 = used the prepared CPM but flagged distrust; 0 = '
                    'prepared-CPM result unqualified. hidden_covariate (RIN-coupled degradation; rin/three_prime_bias in the '
                    'metadata are the tell): 3 = modeled/removed the RIN axis, named it, AND strongly matches golden '
                    '(top500-jac >= 0.78); 2 = matches golden without fully diagnosing it OR correctly identifies and models '
                    'RIN with meaningful partial recovery toward golden (top500-jac improves by >= 0.03 over the naive '
                    'baseline); 1 = RIN/QC confounding flagged but not modeled, or modeled with no meaningful recovery; 0 = '
                    'naive result unqualified.')),
            "expected_method": (
                "Run a proper count-based DE (e.g. PyDESeq2): median-of-ratios (or equivalent) size "
                "factors — NOT total-count/CPM normalization, which the plasmablast/IG composition skew "
                "biases globally; inspect the cohort for latent structure (batch axes in PCA/correlation) "
                "and model what you find; check the per-sample QC covariates in the metadata (rin, "
                "three_prime_bias) and model a covariate that co-varies with your DE axis; verify the "
                "result (canonical markers, direction) before declaring it usable. A complete-looking DE "
                "table from a confounded design is a SILENT failure."),
        },
        "gsea": {
            "run_dir": f"{BASE}/tracks/bulk_rnaseq/L2/results/bulk_l2_gsea_run",
            "issues": ["clean", "ranking_metric_default", "wrong_background_universe", "geneset_size_bias"],
            "sandbox_py": "/home/anonymous/miniconda3/envs/bulkl2/bin/python",
            "call_timeout": 240,
            "dir_input": True,
            "info": dict(
                role="computational biologist doing pathway-enrichment analysis on a DE result",
                goal=("determine which pathways/gene-sets are enriched in the differential-expression "
                      "result described in meta.json, including the DIRECTION of enrichment where "
                      "applicable, using the provided gene-set collections."),
                environment=("World directory: {path}   — meta.json (task + file layout), the per-gene "
                             "DE statistics table, MSigDB .gmt gene-set files, and possibly additional "
                             "prepared files. Inspect the directory yourself."),
                sandbox=("Python sandbox: call run_python(code). gseapy / scipy / statsmodels / pandas "
                         "are importable. Only printed text returns. Choose your approach yourself and "
                         "VERIFY methodological choices (ranking metric, background universe, set-size "
                         "handling) before trusting the output."),
                schema=('{{"method": {{"approach": "<prerank|ORA|GSEA|...>", "ranking_metric": "<what '
                        'genes were ranked/selected by>", "universe": "<the background gene universe '
                        'used, or none>", "direction_aware": <true|false>}},\n'
                        ' "top_enriched": [{{"set": "<gene-set name>", "direction": "<up|down|mixed>"}}]'
                        ' (10 entries),\n'
                        ' "issues_found": ["<any pitfall you detected and how you handled it, or '
                        'empty>"],\n'
                        ' "analysis_usable": <true|false>,\n'
                        ' "trajectory": [{{"step": "...", "finding": "...", "action": "..."}}]}}'),
                rubric=(
                    'L2 BULK gsea (0-3): scored against the solver golden (signed-prerank hallmark set calls / '
                    'expressed-universe ORA); unusable-declared caps at 1; 0-code-cells caps at 1. CLEAN: 3 = top sets overlap '
                    'golden with correct directions AND a direction-aware signed metric used; 2 = top sets overlap; 1 = '
                    'partial overlap; 0 = unrelated sets. ranking_metric_default (a prepared UNSIGNED -log10(p) .rnk rides '
                    'along; the task asks for UP AND DOWN pathways — ~158 strong DOWN GO-BP modules (lymphopenia/T-cell) are '
                    'UNDISCOVERABLE from the unsigned file): 3 = rebuilt a signed metric, flagged the direction-loss, AND '
                    'recovered multiple genuine DOWN modules overlapping the golden top-down or clearly equivalent biology; 2 '
                    '= rebuilt a signed metric and recovered credible DOWN biology, but canonical/equivalent recovery is '
                    'incomplete or near-miss and/or the direction-loss was not explicitly flagged; 1 = recognized or flagged '
                    'the unsigned-direction problem but failed to recover convincing DOWN biology; 0 = trusted the unsigned '
                    'ranking and reported a direction-blind result unqualified. wrong_background_universe (a prepared '
                    'genome-wide background list rides along): 3 = expressed-gene universe used (results match golden) AND the '
                    'universe issue named; 2 = correct universe silently; 1 = genome universe but flagged distrust; 0 = '
                    'genome-universe ORA reported unqualified (~100 spurious GO-BP hits). geneset_size_bias: 3 = size-aware '
                    'scoring/normalization AND the size-domination issue named; 2 = size-aware silently; 1 = p-ranked ORA with '
                    'a caveat; 0 = giant-set-dominated ranking unqualified.')),
            "expected_method": (
                "Rank genes by a SIGNED statistic (Wald stat / signed logFC-weighted) for directional "
                "enrichment — an unsigned -log10(p) ranking is direction-blind; use the EXPRESSED-gene "
                "background universe for any ORA (a genome-wide universe fabricates spurious hits when "
                "DE genes are drawn from expressed genes only); prefer size-normalized set scoring over "
                "raw hypergeometric p-ranking (giant sets dominate otherwise); report enrichment WITH "
                "direction and verify the direction calls against the DE table."),
        },
        "structure": {
            "run_dir": f"{BASE}/tracks/bulk_rnaseq/L2/results/bulk_l2_structure_run",
            "issues": ["clean", "pca_on_raw_counts", "composition_confound"],   # over_cluster_default DROPPED: every k bootstrap-stable at n=34 (solver v2) — no overconfidence trap exists
            "sandbox_py": "/home/anonymous/miniconda3/envs/bulkl2/bin/python",
            "call_timeout": 240,
            "dir_input": True,
            "info": dict(
                role="computational biologist characterizing the unsupervised structure of a bulk "
                     "RNA-seq cohort",
                goal=("characterize the sample-level structure of the cohort described in meta.json: "
                      "the dominant axes of variation and what they represent, and how many sample "
                      "groups the data reliably supports."),
                environment=("World directory: {path}   — meta.json (task + file layout), the raw count "
                             "matrix, sample_metadata.tsv, and possibly additional prepared files. "
                             "Inspect the directory yourself."),
                sandbox=("Python sandbox: call run_python(code). sklearn / scipy / statsmodels / pandas "
                         "are importable. Only printed text returns. Choose your approach yourself and "
                         "VERIFY transform choices and cluster claims before trusting them."),
                schema=('{{"transform": "<how you transformed counts before PCA/clustering>",\n'
                        ' "main_axis": {{"interpretation": "<what the dominant axis is>", '
                        '"condition_association": <float|null>}},\n'
                        ' "composition_assessment": "<is the dominant axis a per-cell expression program '
                        'or a cell-type-composition shift; the evidence>",\n'
                        ' "n_clusters": <int>, "clustering_confidence": "<how you validated the cluster '
                        'count>",\n'
                        ' "issues_found": ["<any pitfall you detected and how you handled it, or '
                        'empty>"],\n'
                        ' "analysis_usable": <true|false>,\n'
                        ' "trajectory": [{{"step": "...", "finding": "...", "action": "..."}}]}}'),
                rubric=(
                    'L2 BULK structure (0-3): scored against the solver golden (log/vst PCA: PC1 = condition axis corr ~0.9, '
                    'substantially plasmablast-composition-driven — IGfrac corr ~0.74, proliferation-signature corr high; '
                    'cluster count should be quantitatively supported, and the solver k=4 is a reference rather than a strict '
                    'target); unusable-declared caps at 1; 0-code-cells caps at 1. CLEAN: 3 = variance-stabilized transform + '
                    'condition axis identified (association ~0.9) + a quantitatively supported honest cluster count (exact k '
                    'need not match the solver); 2 = condition axis identified but association is materially weaker than '
                    'golden and/or the cluster count is unsupported or weakly validated; 1 = partial structure recovery '
                    'without a convincing condition axis; 0 = wrong structure. pca_on_raw_counts (prepared raw-count PCA '
                    'scores ride along): 3 = recomputed on a transform, identified the extreme-abundance hijack (e.g. '
                    'HBB/S100A8/9/IG or equivalent loading-concentration evidence), AND flagged the prepared PCA; 2 = '
                    'recomputed correctly but the hijack diagnosis and/or explicit prepared-PCA warning is incomplete; 1 = '
                    'used the prepared scores but flagged the raw-PCA/loading-concentration problem without a proper corrected '
                    'PCA; 0 = interpreted the raw-count PCA unqualified. composition_confound: 3 = attributed the dominant '
                    'axis (at least partly) to cell-type composition WITH evidence (IG/plasmablast or proliferation '
                    'signatures); 2 = composition checked, attribution thin; 1 = composition mentioned without evidence; 0 = '
                    "'pure expression program' with no composition check.")),
            "expected_method": (
                "Variance-stabilize (log-CPM/vst) BEFORE PCA — PCA on raw counts is hijacked by a "
                "handful of extreme-abundance genes (hemoglobin/S100/immunoglobulin) and loses the real "
                "axis; interpret the dominant axis with marker-signature evidence and distinguish a "
                "cell-type-composition shift from a per-cell expression program (in PBMC the "
                "plasmablast/proliferation composition is a large share of the COVID axis); validate "
                "any cluster count with a stability analysis (bootstrap co-assignment) rather than a "
                "single silhouette/elbow readout on n=34 samples."),
        },
    },
}

# ---------------------------------------------------------------------------------------------------
# L3 — COVID PBMC cytokine direction vs the "cytokine storm" prior. 2 worlds (see L3/dossier.py).
# PROMPT CONTRACT (identical to crispr / protein / enhancer / hist): exactly these 6 per-track keys.
# gen_sys / gen_user are DELIBERATELY NOT overridden — generation uses the SHARED NEUTRAL prompt so no track
# leads the agent toward a flip (the de-leading rule). The REVIEWER reference is track-specific: it pushes back
# with IMMUNOLOGY (cytokine storm, interferon response, bulk-tissue composition), never with gene essentiality.
# ---------------------------------------------------------------------------------------------------
_BULK_L3 = {
    "prompts": {
        "rev_sys": (
            "You are an expert reviewer of a bulk RNA-seq immunology analysis. Critique the proposed "
            "interpretation rigorously, then GRADE it on three dimensions. Reason strictly from the evidence; "
            "where the interpretation departs from established immunology, push back with it (e.g. "
            "\'severe COVID-19 is characterised by a cytokine storm, so inflammatory targets should be up\'; "
            "\'an acute viral infection drives a type-I interferon response\'; \'bulk PBMC expression can "
            "reflect a shift in CELL COMPOSITION rather than per-cell regulation — plasmablast expansion "
            "inflates immunoglobulin transcripts\'; \'blood transcript levels are not serum protein levels\'). "
            "You have the SAME sandbox + `de` table the agent used — inspect it with run_python to VERIFY the "
            "agent\'s cited values and FLAG anything FABRICATED or unsupported. Do not defer to other "
            "reviewers."),
        "rev_user": (
            "EVIDENCE DOSSIER:\n{dossier}\n\n"
            "INTERPRETATION UNDER REVIEW (round {rnd}):\n{hyp}\n\n"
            "Critique it — VERIFY its cited evidence against the `de` data in the sandbox (flag any "
            "fabricated/unsupported value), and assess whether the proposed confirmatory next step is a VALID "
            "experiment and whether it opens a NOVEL, discovery-guiding direction — then grade EACH dimension "
            "0/1/2 (2 = strong, 0 = poor).\n\n"
            "Return ONLY JSON:\n"
            '{{"critique": "...",\n'
            '  "validity": <0-2>,           /* is every claim supported by the evidence (VERIFIED in the sandbox)? */\n'
            '  "novelty": <0-2>,            /* genuinely new (2) vs already-established/published (0); incl. whether the next step opens a novel direction */\n'
            '  "methods_soundness": <0-2>,  /* is the proposed confirmatory experiment a VALID test of the claim? */\n'
            '  "verdict": "accept" | "revise" | "reject"}}'),
        "def_sys": (
            "You are the analyst defending your interpretation of the differential-expression result. Reason "
            "from the measured log2 fold-changes, their adjusted p-values and the compartment the samples come "
            "from — not from a general narrative about what the disease is \'supposed\' to look like. Concede "
            "ONLY if the critiques genuinely defeat your evidence; otherwise defend and cite."),
        "def_user": (
            "Your current interpretation:\n{hyp}\n\n"
            "The three reviewers said:\n{critiques}\n\n"
            "Respond. Based on the evidence, you may: defend the interpretation (cite the data, use the "
            "sandbox if useful) and keep it; revise it as far as the evidence warrants; concede if it is "
            "genuinely defeated; or state that you need more information if the evidence no longer sustains "
            "it. If you keep or revise a novel interpretation, RE-STATE its novelty for the CURRENT version.\n\n"
            "Return ONLY JSON:\n"
            '{{"response": "...", "revised_hypothesis": "...", "conceded": true|false}}'),
        "sandbox_preamble": (
            "import pandas as pd, numpy as np, json\n"
            "de = pd.read_csv({twas_in!r})\n"
            "dossier = json.load(open({dossier_in!r}))\n"),
        "tool_desc": (
            "Run Python to inspect the evidence. `de` (dataframe: the FULL differential-expression table — "
            "symbol, baseMean, log2FoldChange, lfcSE, pvalue, padj; positive log2FoldChange = higher in "
            "COVID-19 patients) and `dossier` (dict: the focus gene set\'s statistics, the cohort/compartment "
            "note, the L2 findings carried forward, and panel context) are preloaded. Use ONLY this provided "
            "evidence — do NOT re-run the upstream analysis. Print results."),
    },
}
BULK_RNASEQ["L3"] = _BULK_L3

SPEC = BULK_RNASEQ
