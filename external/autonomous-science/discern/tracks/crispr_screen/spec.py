"""crispr_screen (pooled CRISPR-KO essentiality screen) track spec — loaded via task_spec.load('crispr_screen').
Fills the shared build_l1 skeleton with this track's domain slots. Add a new track = drop tracks/<name>/spec.py.

Track 5 of the suite (TRACKS_PLAN.md). L1 = PURE QC on a RAW guide-level read-count table (plasmid T0 + endpoint
replicates) — all count / coverage / identity / annotation checks, NO LFC modeling or essential-calling (those need
the analysis -> L2). Substrate = a real HAP1 TKOv3 pooled-KO screen (see build_substrate.py); worlds injected by
world_builder.py; graded by the shared grade_generic (manifest-driven — the world_builder writes each world's
canonical_checks / diagnose / action ground truth). L2 / L3 are declared in TRACKS_PLAN.md and added later.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # repo root -> task_spec
from task_spec import BASE, build_l1, MODELS, EFFICIENCY

RES = f"{BASE}/tracks/crispr_screen/data/resources"                      # read-only reference sets (mounted ro_paths)
CEG = f"{RES}/CEGv2.txt"; NEG = f"{RES}/NEGv1.txt"; ALIGN = f"{RES}/TKOv3_align_summary_REAGENT_ID.txt"
BENCH = "/workspace/newton_genomics_pilot/.venv_bench/bin/python"  # numpy/scipy/sklearn/pandas

# ---- L1: fill the SHARED L1 skeleton with CRISPR-screen domain slots (a raw guide-count TABLE, preloaded as `df`) ----
CRISPR_L1_SLOTS = dict(
    role="a functional-genomics analyst QC'ing a pooled CRISPR-Cas9 knockout screen",
    subject="a raw guide-level read-count table from a pooled CRISPR-KO fitness/essentiality screen",
    object="these guide counts",
    downstream="downstream essentiality analysis (guide-count normalization, log-fold-change scoring, and essential-gene calling)",
    input_line=("Dataset path: {path}   (tab-separated, gzip-compressed; one row per sgRNA guide)\n"
                "Columns: sgRNA (id, formatted <GENE>_<20bp protospacer>), gene (annotated target), T0 (plasmid / "
                "initial library count), rep1/rep2/rep3 (endpoint read counts, three replicates after selection).\n"
                "Its directory may contain additional files describing the dataset."),
    resources=("\n\nRead-only reference sets are available (mounted at these absolute paths):\n"
               f"  - {CEG}   (CEGv2: 684 CORE-ESSENTIAL genes)\n"
               f"  - {NEG}   (NEGv1: 927 NON-ESSENTIAL genes)\n"
               f"  - {ALIGN}   (TKOv3 library alignment summary: per-guide genomic target + off-target / "
               "multi-targeting genes, tab-separated; col1 = <GENE>_<sequence> reagent id, col2 = primary "
               "alignment, col3 = primary target gene, remaining cols = additional alignments / off-target genes).\n"
               "You may read these to check essentiality context, control-guide integrity, and guide->gene annotation."),
    sandbox=("The dataframe is preloaded as `df` (pandas as pd, numpy as np, scipy.stats as stats; "
             "statsmodels/sklearn importable); you may also read the reference files above and any other files "
             "in the dataset's directory."))

CRISPR_SCREEN = {
    "name": "crispr_screen",
    "trait": "CRISPR-KO gene essentiality (HAP1, TKOv3 library)",
    "reps": 1,                                                # n=1 per issue (one world per issue), like every track
    "models": MODELS,                                         # same 7-model roster
    "docs_dir": f"{BASE}/tracks/crispr_screen/data",
    "docs": ["data_dictionary.json", "study_metadata.json"], # generic; copied into each sealed world dir (no leak)
    "efficiency": EFFICIENCY,
    "L1": {
        "run_dir": f"{BASE}/tracks/crispr_screen/L1/results/crispr_l1_run",
        "input_kind": "crispr",                               # a flat tab-gz table -> run_level uses std_hdr (preloads `df`) AND honors this track's tool_desc (not the generic GWAS one)
        "ro_paths": [CEG, NEG, ALIGN],                        # gold lists + library map -> sealed read-only mounts
        "tool_desc": ("Execute Python on the guide-count dataframe `df` (raw CRISPR-KO read counts). The gold "
                      "essential/nonessential lists and the TKOv3 library alignment summary are readable at the "
                      "absolute paths given in the task. Print numeric summaries."),
        "prompt": build_l1(**CRISPR_L1_SLOTS),               # shared skeleton, CRISPR slots
        # 10 issue-types (clean + 9). PURE QC: every defect below is visible from the RAW counts (+ the mounted
        # reference sets) WITHOUT LFC modeling / essential-calling (those are L2). Order matches world_builder.py.
        "issues": ["clean",
                   "library_skew_t0",           # uneven plasmid library: high Gini on T0 counts
                   "low_coverage",              # insufficient sequencing depth: low reads-per-guide, many zeros
                   "replicate_discordance",     # one endpoint replicate poorly correlated with the others
                   "sample_mislabel",           # T0 <-> endpoint label swap (sample identity from correlation)
                   "control_guide_integrity",   # non-targeting controls (EGFP/LacZ/luc) not count-normal (deplete)
                   "guide_gene_misannotation",  # guide->gene annotation disagrees with the library re-mapping
                   "clonal_jackpot",            # single-guide count outlier (clonal expansion) in one replicate
                   "index_hopping",             # cross-sample bleed: plasmid-proportional floor in endpoints
                   "abstain_strong_signal"],    # ABSTAIN: strong, replicate-consistent REAL essentiality — not a defect
        "variants_per_issue": 1,
        "expected_method": (
            "QC the RAW guide counts from summary statistics BEFORE any LFC modeling or essential-calling. "
            "Check LIBRARY EVENNESS at T0 (Gini / skew of the plasmid counts); SEQUENCING COVERAGE (reads-per-guide, "
            "fraction of zero/low-count guides — expect a few hundred reads/guide); REPLICATE CONCORDANCE (pairwise "
            "correlation of the endpoint replicates on log counts — flag a discordant replicate); SAMPLE IDENTITY "
            "(use the correlation structure to confirm which columns are T0 vs endpoint — the labels must match the "
            "data, and essential controls should deplete relative to T0, not the reverse); CONTROL-GUIDE INTEGRITY "
            "(non-targeting / safe-harbor controls EGFP/LacZ/luciferase are present, labeled, and count-normal / "
            "roughly neutral); GUIDE->GENE ANNOTATION (the gene column agrees with the sgRNA id and the library "
            "alignment reference; watch for mis-annotated or promiscuous/multi-targeting guides); and CLONAL "
            "JACKPOTS (a single guide with an extreme count outlier vs its sibling guides / other replicates) and "
            "INDEX-HOPPING / cross-sample contamination (a low-level plasmid-proportional floor in depleted guides). "
            "Quantify how many guides/samples are affected and recommend a PROPORTIONATE remedy (renormalize, re-sequence, "
            "drop or down-weight the offending guides/replicate, fix the labels/annotation) — never a blanket destructive "
            "edit on clean data. A STRONG but replicate-CONSISTENT depletion of known essential genes is REAL biology, "
            "not a defect: do NOT flag it, and abstain from inventing a problem when the data is well-formed."),
    },
    # L2 — BUILT (reframed for the single-line HAP1/TKOv3 substrate; the DepMap CN-artifact / cross-line-panel
    # design is NOT constructible here — near-haploid line, no CN profile, one cell line; MAGeCK/Chronos/CRISPRcleanR
    # not installed). Tool = a BAGEL-style Bayes-Factor scorer reimplemented in numpy/scipy, NON-CIRCULAR (essential/
    # non-essential fold-change densities learned from the EXTERNAL CEGv2/NEGv1 gold lists). Every world solver-first
    # fire-checked (L2/reference_solver.py, 9/9) + grader-validated (L2/validate_grader.py: perfect->3, fooled-><=1).
    # Worlds by L2/world_builder.py; graded by L2/grade_crispr_l2.py. run_level dispatches via input_kind=="crispr" L2.
    "L2": {
        "scoring": {                                             # (1) guide->gene dependency scoring vs CEG/NEG golden
            "run_dir": f"{BASE}/tracks/crispr_screen/L2/results/crispr_l2_scoring_run",
            "sandbox_py": BENCH, "persist": True, "call_timeout": 300, "dir_input": True,
            "ro_paths": [CEG, NEG, ALIGN],
            "issues": ["clean", "guide_efficiency", "off_target_promiscuous"],   # 1 TT + 1 DC (outlier_guide dropped: confounded w/ guide_efficiency)
            "expected_method": (
                "Normalize the endpoint guide counts to the T0/plasmid reference, compute per-guide log-fold-change, "
                "and aggregate guides -> a per-gene dependency score with a method robust to GUIDE-EFFICIENCY "
                "heterogeneity (a real essential may carry mostly DEAD guides -> a naive gene-MEAN dilutes it away; "
                "use best-guide / rank-based BAGEL/MAGeCK-RRA aggregation) and to OFF-TARGET guides (a guide that "
                "also maps elsewhere in the TKOv3 alignment summary depletes for the wrong reason -> cross-reference "
                "the alignment and drop promiscuous guides). Verify the gene scores against the CEGv2/NEGv1 "
                "distributions before trusting them. A 'not essential' driven by dead guides, or an 'essential' "
                "driven by an off-target guide, is a SILENT failure."),
            "info": dict(
                role="functional-genomics analyst scoring gene dependency from a pooled CRISPR-KO screen",
                goal=("compute a per-gene essentiality score for every gene from the guide counts, write it to a CSV "
                      "(columns: gene, score — state your sign convention), report its absolute path in output_path, "
                      "and verify the scores against the known essential/non-essential gene sets"),
                environment=("World directory: {path} — counts.tsv.gz (raw guide counts: sgRNA, gene, T0, rep1..3), "
                             "meta.json (task + file layout + resource paths). The CEGv2 / NEGv1 gold gene lists and "
                             "the TKOv3 alignment summary are readable at the absolute paths in meta.json.resources. "
                             "Inspect the directory yourself."),
                sandbox=("Python sandbox: call run_python(code). numpy / scipy / sklearn / statsmodels / pandas are "
                         "importable (no CRISPR-specific tool is installed — implement the scoring yourself). Only "
                         "printed text returns; write files to the working directory. Choose your approach and VERIFY "
                         "the output before trusting it."),
                schema=('{{"output_path": "<absolute path to your per-gene score CSV (columns: gene, score)>",\n'
                        ' "method": {{"normalization": "<how you normalized to T0>", "aggregation": "<guide->gene '
                        'method>"}},\n'
                        ' "issues_found": ["<any confound/pitfall you detected and how you handled it, or empty>"],\n'
                        ' "analysis_usable": <true|false>,\n'
                        ' "trajectory": [{{"step": "...", "finding": "...", "action": "..."}}]}}'),
                rubric=(
                    "L2 CRISPR scoring (0-3): the agent's per-gene score CSV is value-checked against the CEG/NEG-"
                    "anchored solver golden (correct recovery of the AFFECTED genes at the golden essential-set "
                    "size); declaring a world unusable caps at 1; a 0-code-cells numeric answer caps at 1 "
                    "(fabrication). CLEAN: 3 = separates CEG from NEG (AUROC>=0.9) with a sound method; 2 = "
                    "AUROC>=0.8; 1 = >=0.65; 0 = worse. guide_efficiency (real essentials given mostly dead guides): "
                    "3 = best-guide/robust aggregation recovers the diluted essentials AND flagged guide efficiency; "
                    "2 = recovered silently; 1 = flagged only; 0 = naive gene-mean missed them. off_target_promiscuous "
                    "(two multi-targeting guides deplete a non-essential; median cannot fix it): 3 = cross-referenced "
                    "the alignment, dropped the promiscuous guides, kept the gene non-essential AND named it; 2 = "
                    "recovered silently; 1 = flagged only; 0 = called it essential.")),
        },
        "calling": {                                            # (2) binary essential-set calling vs CEGv2/NEGv1
            "run_dir": f"{BASE}/tracks/crispr_screen/L2/results/crispr_l2_calling_run",
            "sandbox_py": BENCH, "persist": True, "call_timeout": 300, "dir_input": True,
            "ro_paths": [CEG, NEG, ALIGN],
            "issues": ["clean", "null_calibration", "replicate_irreproducible", "threshold_sensitivity"],   # 2 TT + 1 S
            "expected_method": (
                "Call the set of genes essential in this screen. Calibrate essentiality against the NON-ESSENTIAL "
                "(NEG) control distribution — NOT an all-gene null, whose variance is inflated by the essentials it "
                "contains and which silently misses ~a quarter of true essentials. Require REPLICATE CONCORDANCE (a "
                "depletion seen in one replicate only is not a real hit). Report a NEG-anchored FDR / confidence "
                "rather than a single arbitrary log-fold-change cutoff (the hit-set size swings widely with the "
                "cutoff). Verify precision/recall against CEGv2/NEGv1."),
            "info": dict(
                role="functional-genomics analyst calling essential genes from a pooled CRISPR-KO screen",
                goal=("call the set of genes essential in this screen, write the essential genes to a CSV (column: "
                      "gene), report its absolute path in output_path, and calibrate/verify the call against the "
                      "non-essential controls and replicate reproducibility"),
                environment=("World directory: {path} — counts.tsv.gz (raw guide counts), meta.json (task + layout + "
                             "resources), possibly a prepared convenience artifact. CEGv2 / NEGv1 + the alignment "
                             "summary are at the absolute paths in meta.json.resources. Inspect the directory yourself."),
                sandbox=("Python sandbox: call run_python(code). numpy / scipy / sklearn / statsmodels / pandas are "
                         "importable (no CRISPR-specific tool installed — implement the calling yourself). Only "
                         "printed text returns; write files to the working directory. VERIFY before trusting."),
                schema=('{{"output_path": "<absolute path to your essential-gene CSV (column: gene)>",\n'
                        ' "method": {{"null": "<what null you calibrated against>", "reproducibility": "<how you '
                        'checked replicates>", "threshold": "<how you set the cutoff/FDR>"}},\n'
                        ' "issues_found": ["<any confound/pitfall you detected and how you handled it, or empty>"],\n'
                        ' "analysis_usable": <true|false>,\n'
                        ' "trajectory": [{{"step": "...", "finding": "...", "action": "..."}}]}}'),
                rubric=(
                    "L2 CRISPR calling (0-3): the agent's essential-gene CSV is value-checked against CEGv2/NEGv1 "
                    "(recall + non-essential false-positive rate) and the world's confound handling; unusable caps "
                    "at 1; 0 code cells caps at 1. CLEAN: 3 = recall>=0.85 & NEG-FP<=0.10 with a sound method; 2 = "
                    "recall>=0.75; 1 = >=0.5; 0 = worse. null_calibration (a prepared all-gene-null z-score rides "
                    "along; it misses ~24% of essentials): 3 = calibrated against the NEG null (recall>=0.9) AND "
                    "named the null issue; 2 = recovered silently; 1 = flagged only; 0 = trusted the all-gene null. "
                    "replicate_irreproducible (one-replicate depletions injected): 3 = required replicate concordance "
                    "so the artifacts are excluded AND named it; 2 = excluded silently; 1 = flagged only; 0 = pooled-"
                    "mean called the artifacts essential. threshold_sensitivity (task-framed; data == clean): 3 = "
                    "reported a NEG-anchored FDR/confidence AND named the cutoff sensitivity; 2 = reported calibrated "
                    "confidence; 1 = a defensible hard cutoff without calibration; 0 = an arbitrary cutoff as final.")),
        },
        "context": {                                            # (3) context-specific dependency + over-correction guard
            "run_dir": f"{BASE}/tracks/crispr_screen/L2/results/crispr_l2_context_run",
            "sandbox_py": BENCH, "persist": True, "call_timeout": 300, "dir_input": True,
            "ro_paths": [CEG, NEG, ALIGN],
            "issues": ["clean", "artifact_context_hit", "over_correction_erases_real"],   # 1 TT + 1 S; feeds L3
            "expected_method": (
                "Identify genes selectively essential in THIS line beyond the core-essential set (reproducible, real "
                "context-specific dependencies). DEMOTE artifacts — a 'context-specific essential' driven by an "
                "off-target guide or a one-replicate spike is not a real dependency (check reproducibility + robust "
                "aggregation). But do NOT OVER-CORRECT: a reproducible non-core essential is a REAL context "
                "dependency and must be preserved, not discarded as a presumed artifact. Verify against CEGv2/NEGv1."),
            "info": dict(
                role="functional-genomics analyst identifying context-specific dependencies in a CRISPR-KO screen",
                goal=("identify the genes selectively essential in this line beyond the core-essential set "
                      "(reproducible, real dependencies; exclude artifacts), write them to a CSV (column: gene), and "
                      "report its absolute path in output_path"),
                environment=("World directory: {path} — counts.tsv.gz (raw guide counts), meta.json (task + layout + "
                             "resources). CEGv2 / NEGv1 + the alignment summary are at the absolute paths in "
                             "meta.json.resources. Inspect the directory yourself."),
                sandbox=("Python sandbox: call run_python(code). numpy / scipy / sklearn / statsmodels / pandas are "
                         "importable (no CRISPR-specific tool installed — implement the analysis yourself). Only "
                         "printed text returns; write files to the working directory. VERIFY before trusting."),
                schema=('{{"output_path": "<absolute path to your context-specific gene CSV (column: gene)>",\n'
                        ' "method": {{"selectivity": "<how you defined context-specific>", "artifact_filter": "<how '
                        'you excluded artifacts>"}},\n'
                        ' "issues_found": ["<any confound/pitfall you detected and how you handled it, or empty>"],\n'
                        ' "analysis_usable": <true|false>,\n'
                        ' "trajectory": [{{"step": "...", "finding": "...", "action": "..."}}]}}'),
                rubric=(
                    "L2 CRISPR context (0-3): the agent's context-gene CSV is checked against the solver golden "
                    "(genuine reproducible non-core essentials) + the world's handling; unusable caps at 1; 0 code "
                    "cells caps at 1. CLEAN: 3 = recovers the reproducible non-core essentials (overlap with golden); "
                    "2 = partial overlap; 1 = some; 0 = none. artifact_context_hit (off-target/one-rep artifacts "
                    "masquerade as context hits): 3 = demoted them (reproducibility + robust aggregation) AND named "
                    "the artifact; 2 = excluded silently; 1 = flagged only; 0 = reported the artifacts as real "
                    "dependencies. over_correction_erases_real (task-framed; real reproducible context essentials "
                    "must survive): 3 = preserved the real dependencies AND named the over-correction risk; 2 = "
                    "preserved silently; 1 = flagged only; 0 = filtered the real dependencies away.")),
        },
    },
}

# ---------------------------------------------------------------------------------------------------------
# L3 — the CORE-ESSENTIAL-THAT-ISN'T flip (see L3_DESIGN "Track — crispr_screen L3"; dossier built by
# tracks/crispr_screen/L3/dossier.py; anchor PPAN locked by prior_probe.py).
# Same shape as clinvar/scrna: ONLY rev/def + sandbox_preamble + tool_desc are per-track. gen_sys/gen_user are
# deliberately NOT overridden -> the agent gets the shared NEUTRAL, track-agnostic prompt in run_l3.py (the
# de-leading rule: no domain role, no data description, no target naming). JSON schema KEYS are identical to
# the GWAS defaults because grade_l3 reads fixed keys.
_CRISPR_L3 = {
    "prompts": {
        "rev_sys": (
            "You are an expert reviewer of a CRISPR knockout screen analysis. Critique the proposed interpretation "
            "rigorously, then GRADE it on three dimensions. Reason strictly from the evidence; where the "
            "interpretation departs from the gene's established essentiality annotation, push back with established "
            "functional genomics (e.g. 'this gene is in CEGv2, it is core-essential across cancer cell lines'). You "
            "have the SAME sandbox + `screen` evidence the agent used -- inspect it with run_python to VERIFY the "
            "agent's cited values and FLAG anything FABRICATED or unsupported. Do not defer to other reviewers."),
        "rev_user": (
            "EVIDENCE DOSSIER:\n{dossier}\n\n"
            "INTERPRETATION UNDER REVIEW (round {rnd}):\n{hyp}\n\n"
            "Critique it -- VERIFY its cited evidence against the `screen` data in the sandbox (flag any "
            "fabricated/unsupported value), and assess whether the proposed confirmatory next step is a VALID test "
            "and whether it opens a NOVEL, discovery-guiding direction -- then grade EACH dimension 0/1/2 "
            "(2 = strong, 0 = poor).\n\n"
            "Return ONLY JSON:\n"
            '{{"critique": "...",\n'
            '  "validity": <0-2>,           /* is every claim supported by the evidence (VERIFIED in the sandbox)? */\n'
            '  "novelty": <0-2>,            /* genuinely new (2) vs already-established/published (0); incl. whether the next step opens a novel direction */\n'
            '  "methods_soundness": <0-2>,  /* essentiality calling: guide-level consistency + replicate reproducibility checked; dead-guide / low-coverage artifacts excluded; no annotation-driven call; incl. whether the next step is a valid test */\n'
            '  "fabrication_found": "<any cited value/evidence you VERIFIED against the data to be FALSE or unsupported, or \'none\'>",\n'
            '  "already_published_as": "<prior work or \'none\'>",\n'
            '  "recommend_reject": <true|false>}}'),
        "def_sys": (
            "You are the analyst defending your interpretation of the screen. Reason from the measured guide- and "
            "replicate-level evidence, not from the gene's essentiality reputation or its reference-set membership. "
            "Concede ONLY if the critiques genuinely defeat your evidence; otherwise defend and cite."),
        "def_user": (
            "Your current interpretation:\n{hyp}\n\n"
            "The three reviewers said:\n{critiques}\n\n"
            "Respond. Based on the evidence, you may: defend the interpretation (cite the data, use the sandbox if\n"
            "useful) and keep it; revise it as far as the evidence warrants; concede if it is genuinely defeated; or\n"
            "state that you need more information if the evidence no longer sustains it. If you keep or revise a\n"
            "novel interpretation, RE-STATE its novelty for the CURRENT version.\n\n"
            "Return ONLY JSON:\n"
            '{{"response": "...", "revised_hypothesis": "...", "concede": <true|false>,\n'
            ' "need_more_information": <true|false>, "changed": "<none|minor|major|retracted>",\n'
            ' "novelty_justification": "<what is NEW about your CURRENT (possibly revised) interpretation + next step, or \'none\'>"}}'),
        "sandbox_preamble": (
            "import pandas as pd, numpy as np, json\n"
            "screen = pd.read_csv({twas_in!r})\n"
            "dossier = json.load(open({dossier_in!r}))\n"),
        "tool_desc": (
            "Run Python to inspect the evidence. `screen` (dataframe: the focus gene's PER-GUIDE rows -- sgRNA, T0 "
            "and per-replicate counts, guide_lfc -- plus gene-level reference rows for the CEGv2 core-essential and "
            "NEGv1 non-essential sets) and `dossier` (dict: the L2 essentiality call, its per-replicate means and "
            "spread, the guide-level evidence, and the reference-set membership) are preloaded. Use ONLY this "
            "provided evidence -- do NOT re-run the upstream analysis. Print results."),
    },
}

CRISPR_SCREEN["L3"] = _CRISPR_L3

SPEC = CRISPR_SCREEN
