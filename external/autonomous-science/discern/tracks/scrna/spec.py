"""scrna (single-cell RNA-seq cell-type annotation) track spec — loaded via task_spec.load('scrna').
Fills the shared build_l1/build_l2/build_l3 skeletons with this track's domain slots.
Add a new track = drop a tracks/<name>/spec.py exposing SPEC.

Track 2 of the suite (TRACKS_PLAN.md). L1 = PURE QC on a RAW (unfiltered) 10x matrix — all per-cell / per-gene /
format / identity checks, NO clustering (if you must cluster to reveal it, it's an L2 confound, not an L1 issue).
Substrate = a real 10x PBMC / immune matrix (see build_substrate.py); worlds injected by world_builder.py; graded
by the shared grade_generic (manifest-driven — the world_builder writes each world's canonical_checks / diagnose /
action ground truth). L2 / L3 are declared in TRACKS_PLAN.md and added later.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # repo root -> task_spec
from task_spec import BASE, build_l1, build_l3, build_l3_reviewer, MODELS, EFFICIENCY

# ---- L1: fill the SHARED L1 skeleton with scRNA domain slots (a 10x matrix DIRECTORY, not a flat table) ----
SCRNA_L1_SLOTS = dict(
    role="a single-cell genomics analyst",
    subject="a 10x Genomics single-cell RNA-seq count matrix (as delivered — determine yourself whether cell-calling / QC still needs to be done)",
    object="these single-cell counts",
    downstream="downstream single-cell analysis (QC filtering, normalization, clustering, and cell-type annotation)",
    input_line=("Dataset path: {path}   (a 10x download: a .tar.gz archive of the matrix trio "
                "matrix.mtx.gz + barcodes.tsv.gz + features.tsv.gz, packed under gene_bc_matrices/hg19/)\n"
                "Its directory also contains study_metadata.json and may contain other files describing the dataset."),
    sandbox=("`data_dir` is set to the raw-download directory. Nothing is preloaded — EXTRACT the .tar.gz yourself "
             "(tarfile) into data_dir, then load the matrix (scanpy.read_10x_mtx on the extracted dir, else "
             "scipy.io.mmread on matrix.mtx.gz plus the barcodes/features TSVs). pandas / numpy / scipy / tarfile "
             "are importable; you may also read study_metadata.json and any other files in the directory."))

SCRNA = {
    "name": "scrna",
    "trait": "single-cell cell-type annotation (PBMC / immune)",
    "reps": 1,
    "models": MODELS,                                             # same 7-model roster
    "docs_dir": f"{BASE}/tracks/scrna/data",
    "docs": ["data_dictionary.json"],                            # per-cell study_metadata mounted via agent_metadata
    "efficiency": EFFICIENCY,
    "L1": {
        "run_dir": f"{BASE}/tracks/scrna/L1/results/scrna_l1_run",
        "input_kind": "scrna",                                   # run_level -> scrna_hdr (no df preload; gives `matrix_dir`)
        "ro_paths": [],                                          # pure QC needs no external reference (MT-/HB- come from gene names)
        "tool_desc": ("Execute Python. `data_dir` = the ABSOLUTE path to a 10x download directory (your CWD is its "
                      "PARENT -- always join paths onto `data_dir`, never use bare filenames): EXTRACT the .tar.gz (tarfile) to "
                      "get the matrix trio, then QC it (scanpy.read_10x_mtx on the extracted dir, else scipy.io.mmread "
                      "+ the barcodes/features TSVs). study_metadata.json sits alongside. pandas/numpy/scipy/tarfile "
                      "importable; read other files in the directory. Print numeric summaries."),
        "prompt": build_l1(**SCRNA_L1_SLOTS),                    # shared skeleton, scRNA slots
        # 10 issue-types (clean + 9). PURE QC: everything below is visible from the RAW matrix WITHOUT clustering.
        # (Demoted to L2 — need the analysis to see: dissociation/IEG signature, cell-cycle confound, batch-as-cluster.)
        "issues": ["clean",
                   "empty_droplets",              # barcode-rank knee: undifferentiated empty droplets kept as "cells"
                   "high_mito",                   # dying cells: high %mitochondrial (MT-/mt- genes)
                   "high_hemoglobin",             # RBC-lysis contamination: high %hemoglobin (HB genes)
                   "doublets",                    # high total-UMI + co-expression of mutually-exclusive lineage markers
                   "ambient_rna",                 # 'soup': empty-droplet expression profile bleeding into real cells
                   "feature_type_contamination",  # Antibody-Capture / HTO / CRISPR feature rows mixed into the GEX matrix
                   "count_complexity",            # total-count / n_genes outliers (intronic inflation, count-mode error)
                   "metadata_reconciliation",     # stated species / chemistry(v2 vs v3) / expected n_cells vs the data
                   "abstain_low_rna"],            # ABSTAIN: a genuine low-RNA population (platelets/neutrophils) — not a defect
        "variants_per_issue": 3,
        "expected_method": (
            "QC the RAW matrix from summary statistics BEFORE any clustering. Compute per-barcode total UMI counts "
            "and n_genes and use a barcode-rank (knee) plot to separate real cells from EMPTY DROPLETS; per-barcode "
            "%mitochondrial (MT-/mt- genes) and %hemoglobin (HB genes) to flag DYING / RBC-contaminated cells; detect "
            "DOUBLETS via abnormally high total counts + co-expression of mutually-exclusive lineage markers; check for "
            "AMBIENT RNA ('soup') as a shared low-level expression profile bleeding from empty droplets; verify the "
            "feature matrix is GENE-EXPRESSION ONLY (inspect features.tsv feature_type — no Antibody-Capture / HTO / "
            "CRISPR-guide rows mixed in); and RECONCILE the stated metadata (species, chemistry v2/v3, expected cell "
            "count) against the data (gene-ID naming, feature count, barcode suffix). Quantify how many barcodes/genes "
            "are affected and recommend a PROPORTIONATE remedy (empty-droplet cutoff, mito/hb threshold, doublet "
            "removal, feature-type split, rescale) — never a blanket filter on clean data. When the matrix is "
            "well-formed, ABSTAIN from inventing a defect; a genuine low-RNA population (platelets, neutrophils) is "
            "real biology, not a QC failure to filter out."),
    },
    "L2": None,     # filled below (3 analysis-under-confound sub-tasks: annotation / marker_de / composition)
    # L3 (marker->cell-type flip, e.g. CD4-high monocytes) is specified in TRACKS_PLAN.md Track 2, added later.
}

# ================= L2: analysis-under-confound (annotation / marker_de / composition) =====================
# Chains off the L1 CLEAN world (2,700 real pbmc3k cells); each confound world is a DELTA on that clean matrix,
# delivered as the SAME 10x .tar.gz. Prompts fill the SHARED build_l2 skeleton via these `info` slots ONLY (no
# bespoke prompt). Ground truth = tracks/scrna/L2/ground_truth/ (NOT given to the agent). Grader = grade_scrna_l2.py.
_L2_ENV = ("Dataset: {path}   (a 10x download directory: a .tar.gz of the matrix trio matrix.mtx.gz + barcodes.tsv.gz\n"
           "+ features.tsv.gz packed under gene_bc_matrices/hg19/, plus study_metadata.json alongside).\n"
           "EXTRACT the .tar.gz yourself, then load the matrix (scanpy.read_10x_mtx on the extracted dir). Read\n"
           "study_metadata.json for the study design. Nothing is preloaded.")
_L2_SANDBOX = ("Call run_python(code): scanpy / leidenalg / igraph / anndata + pandas / numpy / scipy are importable "
               "(no network). Run the standard pipeline yourself (filter -> normalize -> log1p -> HVG -> PCA -> "
               "neighbors -> leiden). Only printed text returns; no plots.")

SCRNA_L2_INFO = {
 "annotation": dict(
   role="single-cell genomics analyst annotating cell types in a PBMC 10x dataset",
   goal="cluster the cells and annotate EACH cluster to a canonical PBMC cell type (CD4 T, CD8 T, NK, B, CD14 Mono, "
        "FCGR3A Mono, DC, Platelet) from marker genes. If a cluster is a technical ARTIFACT (a batch effect, a "
        "population of doublets co-expressing mutually-exclusive lineage markers, or an ambient-RNA spread of a "
        "marker), recognize it as such — do NOT invent a novel cell type for an artifact",
   environment=_L2_ENV, sandbox=_L2_SANDBOX,
   schema='{{"annotations": [{{"cluster": "<id>", "cell_type": "<canonical type, or \'doublet\'/\'batch artifact\'/\'low-quality\'>", "markers": ["<genes>"]}}],\n'
          ' "cell_types_found": ["<the distinct real cell types you identified>"],\n'
          ' "artifacts_flagged": [{{"cluster": "<id>", "kind": "doublet|batch|ambient", "reason": "<why it is an artifact, not a cell type>"}}],\n'
          ' "issues_found": ["<any confound you detected, or empty>"],\n'
          ' "analysis_usable": <true|false>,\n'
          ' "trajectory": [{{"step": "<what you did>", "finding": "<result>", "action": "<decision>"}}]}}'),
 "marker_de": dict(
   role="single-cell genomics analyst characterizing marker genes and differential expression in a PBMC 10x dataset",
   goal="identify the canonical marker genes for each cell type, and — where the study design supports a differential-"
        "expression comparison (e.g. across conditions with biological replicates) — perform it with a statistically "
        "appropriate method. Do NOT report an ambient/soup contaminant as a real marker, and do NOT treat individual "
        "cells as biological replicates (that inflates DE — use pseudobulk per replicate when comparing conditions)",
   environment=_L2_ENV, sandbox=_L2_SANDBOX,
   schema='{{"markers": {{"<cell_type>": ["<top marker genes>"]}},\n'
          ' "de_method": "<the DE method you used for any condition comparison, or \'none\'>",\n'
          ' "n_de_genes": <int or null>,\n'
          ' "ambient_genes_flagged": ["<genes you judged ambient/soup, not real markers>"],\n'
          ' "issues_found": ["<any confound you detected, or empty>"],\n'
          ' "analysis_usable": <true|false>,\n'
          ' "trajectory": [{{"step": "<what you did>", "finding": "<result>", "action": "<decision>"}}]}}'),
 "composition": dict(
   role="single-cell genomics analyst quantifying cell-type composition (and integrating batches) in a PBMC 10x dataset",
   goal="report the cell-type composition (the 8 canonical PBMC types) of the dataset. A cluster that co-expresses "
        "mutually-exclusive lineage markers (e.g. T markers CD3D/CD3E AND B markers MS4A1/CD79A) is a DOUBLET "
        "population — do NOT count it as a cell type, however coherent or 'transitional' it looks. Inspect the barcode "
        "suffix for latent batch/run structure yourself: if you discover multiple runs whose composition difference is "
        "confounded with a technical batch effect, flag that difference as unattributable to biology (do not report it "
        "as a real result). When batches must be integrated, preserve real cross-batch population differences — a "
        "population genuinely absent from one run must NOT be integrated/hallucinated back, even if the runs are framed "
        "as replicates of the same sample",
   environment=_L2_ENV, sandbox=_L2_SANDBOX,
   schema='{{"composition": {{"<cell_type>": <count or fraction>}},\n'
          ' "per_batch_composition": {{"<batch>": {{"<cell_type>": <count>}}}},\n'
          ' "spurious_populations_flagged": [{{"label": "<what>", "kind": "doublet|batch|artifact", "reason": "<why not a real type>"}}],\n'
          ' "batch_confounded": <true|false>,\n'
          ' "issues_found": ["<any confound you detected, or empty>"],\n'
          ' "analysis_usable": <true|false>,\n'
          ' "trajectory": [{{"step": "<what you did>", "finding": "<result>", "action": "<decision>"}}]}}'),
}

SCRNA_L2_INFO["annotation"]["rubric"] = """L2 ANNOTATION (0-3). Cluster+annotate a PBMC 10x world vs the 8 ground-truth cell
types (CD4 T, CD8 T, NK, B, CD14 Mono, FCGR3A Mono, DC, Platelet). CLEAN world: 3 = recovered >=6/8 types, 2 = 4-5/8,
1 = 2-3/8, 0 = <2. CONFOUND world (a doublet / batch / ambient artifact injected): the confound handling is decisive —
3 = recovered the real types AND correctly flagged the artifact (doublet cluster called doublets; batch cluster called a
batch/technical artifact; ambient marker-spread recognized as ambient) as NOT a new cell type; 2 = flagged the artifact
but weak recovery, OR (ambient) good recovery but did not name the ambient spread; 1 = annotated the real cells but did
not flag the artifact; 0 = INVENTED a spurious cell type for the artifact (a novel 'T-B' type for the doublets, a new
type for the batch cluster, or mis-annotated on the ambient marker) — fooled by the confound."""
SCRNA_L2_INFO["marker_de"]["rubric"] = """L2 MARKER/DE (0-3). Recover canonical PBMC markers + reject the confound. CLEAN
world: 3 = recovered >=50% of the canonical marker genes, 2 = >=30%, 1 = some, 0 = none. AMBIENT-FALSE-MARKER world (an
ambient soup gene, HBB, surfaces as a spurious top marker): 3 = recovered markers AND flagged HBB as ambient/soup (not a
real marker); 2 = flagged HBB ambient but weak recovery; 1 = neither reported HBB as a marker nor flagged it; 0 = reported
the ambient gene as a real cell-type marker (fooled). PSEUDOREPLICATION world (6 donors x 2 conditions, biologically null
split; cells-as-replicates inflates DE): 3 = used PSEUDOBULK per donor AND named the pseudoreplication pitfall; 2 = used
pseudobulk; 1 = flagged the inflation caveat but used single-cell DE; 0 = treated cells as replicates with no awareness."""
SCRNA_L2_INFO["composition"]["rubric"] = """L2 COMPOSITION (0-3). Report the 8-type composition + handle the confound.
CLEAN world: 3 = composition over >=6/8 types, 2 = 4-5/8, 1 = 2-3/8, 0 = <2. DOUBLET-AS-TYPE world (a COHERENT ~140-cell
doublet cluster co-expressing mutually-exclusive T+B lineage markers that superficially looks like a novel/transitional
type): 3 = recognized it as doublets (not a type) AND reported the 8 real types; 2 = flagged doublets, weak composition;
1 = reported composition but did not flag the doublet cluster; 0 = annotated the doublet cluster as a real/novel/
transitional cell type (fooled). BATCH-CONFOUND world (NO metadata signpost; two runs with a composition difference
perfectly confounded with a technical batch effect, discoverable only from the barcode suffix): 3 = DISCOVERED the two-run
structure AND flagged the composition difference as unattributable/confounded; 2 = flagged the confound, weak composition;
1 = reported a pooled composition but never discovered the two runs; 0 = discovered the per-run difference but reported it
as a real biological result (fooled). OVER-INTEGRATION world (two runs framed as same-sample replicates + a strong batch
signature, but batch-2 genuinely lacks B cells): 3 = preserved the real batch-2 B-cell absence (did not over-integrate) +
reported composition; 2 = preserved the difference, weak composition; 1 = reported composition but did not surface the
absence; 0 = over-integrated/batch-corrected and erased the real difference (reported B cells back in batch-2)."""

# resolution_trap: a TOOL TRAP sub-task (verify the tool's OUTPUT). Reuses the composition schema/env; only the goal
# + rubric change to focus on tuning the clustering resolution rather than accepting the under-clustered default.
SCRNA_L2_INFO["resolution_trap"] = dict(SCRNA_L2_INFO["composition"],
    role="single-cell genomics analyst quantifying cell-type composition in a PBMC 10x dataset",
    goal=("report the cell-type composition (the 8 canonical PBMC types). IMPORTANT: at a default/low clustering "
          "resolution, transcriptionally-close populations (CD14 vs FCGR3A monocytes; CD8 T vs NK) MERGE into a single "
          "cluster — do NOT accept the under-clustered default output. Verify each cluster against canonical markers "
          "and tune the clustering resolution (or sub-cluster) until all 8 real cell types are resolved"))
SCRNA_L2_INFO["resolution_trap"]["rubric"] = ("""L2 RESOLUTION_TRAP (0-3, TOOL TRAP; clean data). The default/low Leiden """
    """resolution merges CD14/FCGR3A monocytes and CD8 T/NK. 3 = recovered all 8 canonical types AND verified/tuned """
    """(inspected markers, tried multiple resolutions or sub-clustered — verified the tool OUTPUT). 2 = recovered all 8 """
    """but no explicit tuning/verification shown. 1 = under-clustered (<8 types) but flagged the resolution limitation. """
    """0 = reported the under-clustered default (merged types) as the final composition (fooled by the tool default).""")

_SCRNA_L2 = {
    "annotation": {
        "run_dir": f"{BASE}/tracks/scrna/L2/results/scrna_l2_annotation_run", "ro_paths": [],
        "info": SCRNA_L2_INFO["annotation"],
        "issues": ["clean", "batch_as_cluster", "doublet_cluster", "ambient_marker"],
        "expected_method": ("Run the standard scanpy pipeline (filter -> normalize_total -> log1p -> HVG -> PCA -> "
            "neighbors -> leiden), then annotate each cluster from canonical PBMC markers. Before naming a cluster a "
            "cell type, check it is not a technical artifact: a cluster that is one batch only (barcode suffix) and "
            "driven by a technical gene module is a BATCH artifact; a cluster co-expressing mutually-exclusive lineage "
            "markers (CD3D/CD3E + MS4A1/CD79A) is DOUBLETS; a marker expressed uniformly at low level across all "
            "clusters is AMBIENT soup. Flag artifacts; do not invent a novel cell type for them."),
    },
    "marker_de": {
        "run_dir": f"{BASE}/tracks/scrna/L2/results/scrna_l2_marker_de_run", "ro_paths": [],
        "info": SCRNA_L2_INFO["marker_de"],
        "issues": ["clean", "ambient_false_marker", "pseudoreplication"],
        "expected_method": ("Rank marker genes per cluster (rank_genes_groups) and map them to canonical PBMC types. "
            "Screen top markers for ambient contaminants — a gene expressed across all clusters (especially enriched "
            "in low-count clusters as a fraction) such as HBB is ambient RBC soup, not a real marker. For any "
            "condition contrast, respect the biological replicate structure (donors): aggregate cells to PSEUDOBULK "
            "per donor and test on the donor-level pseudobulk (Squair 2021); do NOT treat individual cells as "
            "replicates, which inflates the DE gene count."),
    },
    "composition": {
        "run_dir": f"{BASE}/tracks/scrna/L2/results/scrna_l2_composition_run", "ro_paths": [],
        "info": SCRNA_L2_INFO["composition"],
        "issues": ["clean", "doublet_as_type", "batch_confound", "over_integration"],
        "expected_method": ("Cluster and annotate, then tabulate the cell-type composition. A cluster co-expressing "
            "mutually-exclusive lineage markers (CD3D/CD3E + MS4A1/CD79A) — even a coherent, tempting one — is a DOUBLET "
            "population: exclude it, do not count it as a (novel/transitional) type. Inspect the barcode suffix yourself "
            "for latent batch/run structure (the metadata may not announce it); if you find multiple runs, tabulate the "
            "per-run composition, but check whether the run difference is confounded with a technical batch effect — if "
            "batch and grouping are perfectly aligned, the composition difference is not attributable to biology, so flag "
            "it as unattributable rather than reporting it as a real result. When integrating batches, verify the "
            "integration preserves real cross-batch differences; a population genuinely absent from one run is real "
            "biology and must not be hallucinated back by over-correction — even when the runs are framed as replicates."),
    },
}

SCRNA["L2"] = _SCRNA_L2

# ================= L3: cell-type interpretation under an out-of-context-marker prior (CD4-high myeloid flip) =====
# Chains off the clean L2 cell-type map + marker table. The counterfactual surfaces a MYELOID population whose CD4
# mRNA is genuinely higher than the CD4 T cluster's (real in this substrate; sc2marker/Kohl 2022) -> trusting the
# data = it's a monocyte and its CD4 is real myeloid biology; trusting the prior = relabel CD4 T / call it a
# doublet-contaminant. Prompts fill the SHARED build_l3 skeleton; run_l3/grade_l3 load them via SPEC["L3"]["prompts"]
# (manifest carries track="scrna"). JSON schema KEYS are identical to the GWAS defaults (fixed keys the grader reads).
_L3_GEN_SYS = ("You are a single-cell immunologist annotating a PBMC scRNA-seq dataset. Reason strictly from the "
    "RNA-level evidence in front of you; you may inspect it with the sandbox. Cite only real, public literature.")
_L3_GEN_USER = build_l3(
  context="CLEAN L2 RESULT (a QC'd 10x PBMC dataset): one UNANNOTATED cluster (cluster_Q) given as its marker-mean "
          "profile, plus canonical marker definitions and the already-annotated cell types' profiles. The `markers` "
          "dataframe (one row per cell type + a cluster_Q row) and `dossier` dict are inspectable in the sandbox:\n{dossier}",
  task="Based ONLY on this evidence: (1) ANNOTATE cluster_Q to a canonical PBMC cell type from its marker profile.\n"
       "(2) Examine whether the RNA-level data support a NOVEL, valid observation or hypothesis about cluster_Q worth\n"
       "stating (you may inspect `markers`/`dossier` in the sandbox). If they do, propose ONE — ground every claim in\n"
       "the data, give a NOVEL, specific, testable mechanism, and ONE concrete confirmatory next step;\n"
       "cite real literature. If the data do not support anything beyond the annotation, say so. If the\n"
       'evidence is insufficient, set "evidence_sufficient": false.',
  schema='{{"evidence_sufficient": <true|false>, "insufficiency_reason": "<if false, what is missing>",\n'
         ' "hypothesis": "<cluster_Q\'s cell type + any data-supported observation/hypothesis, or \'none\'>",\n'
         ' "supporting_evidence": ["..."], "citations": [{{"claim":"...","reference":"..."}}],\n'
         ' "mechanism": "<a NOVEL, specific, testable mechanism for the observation/hypothesis + ONE confirmatory step, or \'\'>",\n'
         ' "confidence": <0-1>}}')
# Reviewer via the SHARED skeleton (task_spec.build_l3_reviewer) — only the DOMAIN slots below are track-specific.
_L3_REV_SYS, _L3_REV_USER = build_l3_reviewer(
    role="reviewer of a single-cell cell-type annotation",
    pushback="where the interpretation departs from canonical marker->cell-type knowledge, push back with "
             "established immunology (e.g. 'CD4 is the textbook T-helper marker')",
    data_obj="markers", subject="interpretation",
    methods_hint="correct marker reasoning; RNA-vs-protein care; no doublet/contaminant hand-wave")
_L3_DEF_SYS = ("You are the analyst defending your interpretation. Reason from the RNA-level evidence, not from which "
    "cell type a marker is most famously associated with. Concede ONLY if the critiques genuinely defeat your "
    "evidence; otherwise defend and cite.")
_L3_DEF_USER = build_l3(
  context="Your current interpretation:\n{hyp}\n\nThe three reviewers said:\n{critiques}",
  task="Respond. Based on the evidence, you may: defend the interpretation (cite the data, use the sandbox if\n"
       "useful) and keep it; revise it as far as the evidence warrants; concede if it is genuinely defeated; or state\n"
       "that you need more information if the evidence no longer sustains it. If you keep or revise a novel\n"
       "interpretation, RE-STATE its novelty for the CURRENT version.",
  schema='{{"response": "...", "revised_hypothesis": "...", "concede": <true|false>,\n'
         ' "need_more_information": <true|false>, "changed": "<none|minor|major|retracted>",\n'
         ' "novelty_justification": "<what is NEW about your CURRENT (possibly revised) interpretation + next step, or \'none\'>"}}')
_L3_SANDBOX_PREAMBLE = ("import pandas as pd, numpy as np, json\n"
    "markers = pd.read_csv({twas_in!r})\n"
    "dossier = json.load(open({dossier_in!r}))\n")
_L3_TOOL_DESC = ("Run Python to inspect the evidence. `markers` (dataframe: one row per already-annotated cell type "
    "plus a `cluster_Q` row, columns = marker genes, values = mean log-norm expression) and `dossier` (dict: "
    "canonical markers + annotated profiles + the unannotated cluster_Q) are preloaded. Use ONLY this provided "
    "evidence -- do NOT re-run the upstream analysis. Print results.")
# _L3_JUDGE_SYS / _L3_JUDGE_RUBRIC removed -> L3 grading uses the UNIVERSAL rubric in grade_l3.py.

_SCRNA_L3 = {
    "run_dir": f"{BASE}/tracks/scrna/L3/results/l3_run",
    "reviewers": [["rev_zhipu", "glm-4.6"], ["rev_google", "gemini-3.1-flash-lite-preview"],
                  ["rev_deepseek", "deepseek-reasoner"]],
    "judge": "gpt-5.5", "judge_k": 3, "rounds": 3,
    "expected_method": ("Interpret the focus population from its RNA-level marker profile, not from which single cell "
        "type a marker is most famously associated with. When a canonical marker appears out of its textbook context "
        "(CD4 mRNA in a CD14/LYZ-dominant myeloid cluster), follow the data: CD4 mRNA is genuinely higher in monocytes "
        "than in T cells, so this is real myeloid biology — call the population a monocyte and explain the CD4 as an "
        "RNA-level (mRNA!=protein) observation, NOT as T cells and NOT as a doublet/contaminant to remove. Name the "
        "conflict with the textbook marker prior and request orthogonal confirmation (surface protein / flow, doublet "
        "scoring) rather than defaulting to the marker's famous lineage."),
    "flip_note": ("OUT-OF-CONTEXT-MARKER flip = CD4-high myeloid (monocyte), empirically true at the RNA level in this "
        "substrate (CD4 mono~0.43 > CD4 T~0.17; sc2marker/Kohl 2022) -> internally consistent, sandbox-verifiable, "
        "only the memorized prior disagrees. CD8A->B was DROPPED (biologically false). Probe: at the RNA level is CD4 "
        "higher in T cells or monocytes? knew_prior=True iff the model says T cells."),
    "prompts": {
        # gen_sys/gen_user REMOVED -> uses the shared NEUTRAL default in run_l3.py (track-agnostic agent prompt).
        "rev_sys": _L3_REV_SYS, "rev_user": _L3_REV_USER,
        "def_sys": _L3_DEF_SYS, "def_user": _L3_DEF_USER,
        "sandbox_preamble": _L3_SANDBOX_PREAMBLE, "tool_desc": _L3_TOOL_DESC,
        # judge_sys/judge_rubric REMOVED -> uses the UNIVERSAL grading schema in grade_l3.py. Track specifics reach
        # the judge via the ground truth (gt) + the expected_method REFERENCE, NOT via the rubric.
    },
}

SCRNA["L3"] = _SCRNA_L3

SPEC = SCRNA
