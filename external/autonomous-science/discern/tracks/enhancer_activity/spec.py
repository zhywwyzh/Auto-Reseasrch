"""enhancer_activity (cross-species regulatory / enhancer-activity) track spec — loaded via task_spec.load('enhancer_activity').
Fills the shared build_l1 skeleton with this track's domain slots. Add a new track = drop tracks/<name>/spec.py.

Track 7 of the suite (TRACKS_PLAN.md). L1 = PURE QC on a RAW enhancer-activity table delivered in its ORIGINAL
.xlsx FORMAT (Klein 2018 Supp File 2, sheet 'S4 All ortholog scores'): the agent must PARSE the raw Excel (title
row before the header; one coordinate STRING '<chrom>:<start>-<end>_<assembly>' per row + a fetched sequence) and
run all sequence/coordinate/assembly integrity checks — NO activity prediction / conservation modelling (those need
the analysis -> L2). Substrate = the real Klein STARR-seq cross-species enhancer table (see build_substrate.py);
worlds injected by world_builder.py; graded by the shared grade_generic (manifest-driven). L2 / L3 in TRACKS_PLAN.md.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # repo root -> task_spec
from task_spec import BASE, build_l1, MODELS, EFFICIENCY

RES = f"{BASE}/tracks/enhancer_activity/data/resources"                       # read-only reference / instruments (ro mounts)
HG38REF = f"{RES}/hg38_reference_loci.tsv"                                     # orientation reference (named in prompt)
CHAIN = f"{RES}/hg19ToHg38.over.chain.gz"                                     # L2 liftOver instrument (mounted, NOT named)
GPN = f"{RES}/gpn_msa_variant_scores.jsonl"                                   # L2 GPN-MSA feature   (mounted, NOT named)
ORACLE = f"{RES}/vista_nt_logreg_oracle.joblib"                              # L2 activity oracle   (mounted, NOT named)
BENCH = "/workspace/newton_genomics_pilot/.venv_bench/bin/python"  # numpy/scipy/sklearn/pandas

# ---- L1: fill the SHARED L1 skeleton with enhancer-activity domain slots (a RAW .xlsx the agent must parse) --------
ENH_L1_SLOTS = dict(
    role="a regulatory-genomics analyst QC'ing a cross-species enhancer-activity table before an activity/conservation analysis",
    subject="a raw cross-species enhancer-activity table (a STARR-seq screen), delivered as an Excel (.xlsx) workbook",
    object="these enhancer activity rows (coordinates + sequences)",
    downstream=("downstream regulatory analysis (predicting enhancer activity from sequence, and comparing enhancer "
                "activity vs sequence conservation across species)"),
    input_line=("Dataset path: {path}   (an .xlsx workbook — the ORIGINAL Klein-2018 Supplementary File 2 format)\n"
                "The enhancer table is on sheet 'S4 All ortholog scores'. In that sheet ROW 0 is a title "
                "('Table S4. Ortholog Scores'), ROW 1 is the real header (['Enhancer Coordinates (hg19)', "
                "'Enrichment Score', 'sequence']), and the data start at ROW 2 — so read it with e.g. "
                "pandas.read_excel(path, sheet_name='S4 All ortholog scores', header=1) (openpyxl is installed).\n"
                "Each row is one species ORTHOLOG of an enhancer. The coordinate is a STRING "
                "'<chrom>:<start>-<end>_<assembly>' (0-based half-open; <assembly> = the ortholog genome, e.g. hg38, "
                "panTro5, gorGor3, ponAbe2, macFas5, rheMac3, papAnu2, chlSab2, calJac3, nomLeu3, saiBol1) — parse "
                "chrom/start/end/assembly out of it yourself. 'Enrichment Score' is log2 enhancer activity; 'sequence' "
                "is the forward (+) strand DNA fetched for that coordinate. Its directory may contain additional files."),
    resources=("\n\nA read-only reference is available (mounted at this absolute path):\n"
               f"  - {HG38REF}   (tab-separated: coordinate<TAB>sequence — the forward (+) strand reference sequence "
               "for the HUMAN (hg38) enhancer loci; use it to check sequence integrity / orientation for hg38 rows)."),
    sandbox=("Parse the .xlsx yourself with pandas.read_excel / openpyxl (pandas as pd, numpy as np, scipy.stats as "
             "stats; sklearn/pysam importable); you may also read the reference file above and any other files in the "
             "dataset's directory."))

ENHANCER_ACTIVITY = {
    "name": "enhancer_activity",
    "trait": "cross-species enhancer activity (Klein 2018 STARR-seq)",
    "reps": 1,                                                # n=1 per issue (one world per issue), like every track
    "models": MODELS,                                         # same 7-model roster
    "docs_dir": f"{BASE}/tracks/enhancer_activity/data",
    "docs": ["data_dictionary.json", "study_metadata.json"], # generic; copied into each sealed world dir (no leak)
    "efficiency": EFFICIENCY,
    "L1": {
        "run_dir": f"{BASE}/tracks/enhancer_activity/L1/results/enhancer_l1_run",
        "input_kind": "enhancer",                            # a RAW .xlsx the agent must parse -> run_level uses enhancer_hdr (path + parse hint) AND this track's tool_desc
        "ro_paths": [HG38REF, CHAIN, GPN, ORACLE],           # hg38 orientation ref (named) + liftOver chain / GPN-MSA / NT-logreg oracle (mounted for L2 / sealed-exec, NOT named in the prompt)
        "tool_desc": ("Execute Python on the raw enhancer-activity .xlsx at the dataset path (parse it yourself with "
                      "pandas.read_excel / openpyxl — sheet 'S4 All ortholog scores', header on row 1). The hg38 "
                      "forward-strand reference is readable at the absolute path given in the task. Print numeric summaries."),
        "prompt": build_l1(**ENH_L1_SLOTS),                 # shared skeleton, enhancer slots
        # 10 issue-types (clean + 8 + abstain). PURE QC: every defect below is visible from the raw table (+ the mounted
        # hg38 reference for orientation) WITHOUT activity prediction / conservation modelling (those are L2). Order
        # matches world_builder.py.
        "issues": ["clean",
                   "sequence_fetch_failure",     # missing sequences (real fetch_failed) + N-runs in the fetched DNA
                   "assembly_build_mismatch",    # wrong assembly suffix: a foreign build (hg19) / a species duplicated within one enhancer family
                   "liftover_failure",           # cross-species coords that cannot be lifted (unplaced-scaffold chromosomes)
                   "coordinate_off_by_one",      # 0-vs-1-based / start>end (span disagrees with sequence length by 1)
                   "strand_rc_inconsistency",    # sequence stored reverse-complemented vs the forward reference (wrong strand)
                   "duplicate_family_leakage",   # duplicate coordinates + cross-species family leakage (identical ortholog sequences)
                   "seqlen_span_mismatch",       # len(sequence) != coordinate span (end-start)
                   "abstain_repeat_rich"],       # ABSTAIN: genuinely repeat-rich / low-complexity but REAL active enhancers -> retain
        "variants_per_issue": 1,
        "expected_method": (
            "PARSE the raw .xlsx (skip the title row) into a table of coordinate-string + enrichment + sequence, then QC "
            "the SEQUENCES and COORDINATES BEFORE any activity/conservation analysis. Parse each coordinate string into "
            "chrom/start/end/assembly. Check SEQUENCE INTEGRITY (missing / empty sequences and runs of N — failed "
            "fetches); ASSEMBLY / BUILD (the assembly suffix must be one of the real ortholog genomes — flag foreign "
            "builds like hg19, and the same assembly appearing twice within one enhancer family / anchor); LIFTABILITY "
            "(coordinates on unplaced scaffolds / non-canonical chromosomes cannot be lifted across species); COORDINATE "
            "ARITHMETIC (start < end, and coordinate span end-start == sequence length — a 1-bp discrepancy is an "
            "off-by-one / 0-vs-1-based error, a larger discrepancy is a sequence-length/coord-span mismatch); SEQUENCE "
            "ORIENTATION (for hg38 rows, the sequence must match the forward-strand reference — a reverse-complemented "
            "sequence means the wrong strand was extracted); and DUPLICATES / LEAKAGE (duplicate coordinates, and "
            "identical ortholog sequences that would leak the same enhancer across a train/test split). Quantify how "
            "many rows are affected and recommend a PROPORTIONATE remedy (drop/refetch the failed sequences, correct "
            "the assembly label, drop unliftable coordinates, fix the coordinate arithmetic, reverse-complement back, "
            "de-duplicate) — never a blanket destructive edit on clean data. A genuinely REPEAT-RICH / LOW-COMPLEXITY "
            "sequence that is nonetheless a REAL, active enhancer is biology, not an artifact: do NOT discard it, and "
            "abstain from inventing a defect when the data is well-formed."),
    },
    # L2 — BUILT (minimal, DATA-CONFOUND-focused). Feasibility gate: FIMO/HOMER/liftOver not installed, the GPN-MSA
    # variant->enhancer mapping is missing, and (fire-checked) seq->activity has NO signal / per-species scales are
    # uniform / conservation~activity is null on this substrate -> the designed FIMO/liftOver/GPN tool-traps do not fire.
    # What DOES fire = input-integrity confounds that corrupt the cross-species DIVERGENCE conclusion (verify INPUT),
    # using numpy/scipy (no external tools). Every world solver-first fire-checked (L2/reference_solver.py 4/4) +
    # grader-validated (L2/validate_grader.py: perfect->3, fooled-><=1). Worlds by L2/world_builder.py; graded by
    # L2/grade_enhancer_l2.py. run_level dispatches via input_kind=="enhancer" L2 branch.
    "L2": {
        "divergence": {
            "run_dir": f"{BASE}/tracks/enhancer_activity/L2/results/enhancer_l2_divergence_run",
            "sandbox_py": BENCH, "persist": True, "call_timeout": 300, "dir_input": True, "ro_paths": [],
            "issues": ["clean", "species_batch_confound", "enrichment_outlier", "phylo_pseudoreplication", "species_duplicate"],
            "expected_method": (
                "Compute per-FAMILY cross-species activity divergence (family = coordinate minus the trailing "
                "_<assembly>; the suffix is the species) and call the families whose activity has diverged (turned "
                "over). VERIFY input integrity + the cross-species STRUCTURE first: (1) per-species SCALE — normalize "
                "per species (a globally-shifted species fabricates spurious divergence); (2) value PLAUSIBILITY — "
                "exclude implausible out-of-range values; (3) PHYLOGENETIC non-independence — the 11 primates are NOT "
                "independent; a range driven by a single species that disagrees with its phylo-neighbour is correlated "
                "noise, not turnover; (4) ONE-PER-SPECIES — a duplicated species inflates a family's range."),
            "info": dict(
                role="comparative-genomics analyst studying cross-species enhancer activity turnover",
                goal=("identify the enhancer FAMILIES whose activity diverged across species (operational "
                      "criterion: log2 enrichment range > 2.0 across >=4 species in the family); write them "
                      "to a CSV (column: family), report output_path, and verify your result is sound"),
                environment=("World directory: {path} — enhancer_table.csv (coordinate, enrichment_score, sequence; one "
                             "row per species-ortholog; family = coordinate minus the trailing _<assembly>) + meta.json."),
                sandbox=("Python sandbox: run_python(code). numpy / scipy / sklearn / pandas / Biopython importable. "
                         "Only printed text returns; write files to the working directory. VERIFY before trusting."),
                schema=('{{"output_path": "<absolute path to your divergent-family CSV (column: family)>",\n'
                        ' "method": {{"divergence": "<how measured>", "integrity_checks": "<input + cross-species checks>"}},\n'
                        ' "issues_found": ["<any confound detected and how handled, or empty>"],\n'
                        ' "analysis_usable": <true|false>,\n'
                        ' "trajectory": [{{"step": "...", "finding": "...", "action": "..."}}]}}'),
                rubric=(
                    "L2 ENHANCER divergence (0-3): turnover-family CSV value-checked vs the solver golden turnover set; "
                    "unusable caps at 1; 0 code cells caps at 1. CLEAN: 3 = F1>=0.7; 2 = >=0.55; 1 = >=0.35; 0 = worse. "
                    "species_batch_confound: 3 = per-species-normalized (precision>=0.7) AND named it; 2 = silently; "
                    "1 = flagged only; 0 = reported the ~178 spurious. enrichment_outlier: 3 = excluded the implausible "
                    "fakes AND named it; 2 = silently; 1 = flagged; 0 = reported fakes. phylo_pseudoreplication: 3 = "
                    "demoted single-sister-jump turnover (clade-consistency) AND named the non-independence; 2 = "
                    "silently; 1 = flagged; 0 = reported the phylo-noise families. species_duplicate: 3 = enforced "
                    "one-per-species (dedup) AND named it; 2 = silently; 1 = flagged; 0 = reported dup-inflated.")),
        },
        "conservation": {
            "run_dir": f"{BASE}/tracks/enhancer_activity/L2/results/enhancer_l2_conservation_run",
            "sandbox_py": BENCH, "persist": True, "call_timeout": 300, "dir_input": True, "ro_paths": [],
            "issues": ["clean", "gc_conservation_bias", "alignment_quality", "conservation_as_proxy"],
            "expected_method": (
                "Rank the most sequence-CONSERVED enhancer FAMILIES from their 11-species orthologs (a family's "
                "conservation = similarity among its ortholog sequences). Beware: (1) GC content BIASES a raw "
                "%-identity/k-mer conservation estimate — adjust for GC; (2) families with heterogeneous ortholog "
                "LENGTHS (poor alignment / truncations) give unreliable conservation — flag and exclude/repair them; "
                "(3) conservation is a SEQUENCE property — do NOT read it as activity: in this data conservation and "
                "activity are DECOUPLED (the turnover phenomenon), so 'conserved => active-here' is a false prior."),
            "info": dict(
                role="comparative-genomics analyst studying enhancer sequence conservation vs activity turnover",
                goal=("rank enhancer FAMILIES by sequence conservation and report the top ~25% most conserved; "
                      "write them to a CSV (column: family) and "
                      "report output_path, and verify your ranking is methodologically sound before trusting it"
                      "with activity"),
                environment=("World directory: {path} — enhancer_table.csv (coordinate, enrichment_score, sequence; one "
                             "row per species-ortholog; family = coordinate minus the trailing _<assembly>) + meta.json."),
                sandbox=("Python sandbox: run_python(code). numpy / scipy / sklearn / pandas / Biopython importable. "
                         "Only printed text returns; write files to the working directory. VERIFY before trusting."),
                schema=('{{"output_path": "<absolute path to your conserved-family CSV (column: family)>",\n'
                        ' "method": {{"conservation": "<how measured>", "gc": "<how adjusted>", "alignment": "<how checked>"}},\n'
                        ' "issues_found": ["<any confound detected and how handled, or empty>"],\n'
                        ' "analysis_usable": <true|false>,\n'
                        ' "trajectory": [{{"step": "...", "finding": "...", "action": "..."}}]}}'),
                rubric=(
                    "L2 ENHANCER conservation (0-3): conserved-family CSV value-checked vs the GC-adjusted golden "
                    "conserved set; unusable/0-code cap at 1. CLEAN: 3 = F1>=0.7; 2 = >=0.55; 1 = >=0.35; 0 = worse. "
                    "gc_conservation_bias (data clean; GC biases raw %-identity, corr -0.32): 3 = adjusted for GC AND "
                    "named it; 2 = named it; 1 = correct set without GC handling; 0 = neither. alignment_quality "
                    "(truncated orthologs drop true-conserved families): 3 = flagged bad alignments and kept them "
                    "conserved (recovered>=0.6) AND named it; 2 = recovered silently; 1 = flagged only; 0 = dropped "
                    "them. conservation_as_proxy (data clean; conservation~activity is null): 3 = reported conservation "
                    "as a SEQUENCE property / the decoupling AND named it; 2 = named it; 1 = correct set but imposed "
                    "the 'conserved=active' prior; 0 = neither.")),
        },
        "ranking": {
            "run_dir": f"{BASE}/tracks/enhancer_activity/L2/results/enhancer_l2_ranking_run",
            "sandbox_py": BENCH, "persist": True, "call_timeout": 300, "dir_input": True, "ro_paths": [],
            "issues": ["clean", "ortholog_family_leakage", "duplicate_contamination", "reference_species_bias"],
            "expected_method": (
                "Identify the most ACTIVE enhancer FAMILIES. The table has one row PER SPECIES-ortholog, so handle the "
                "cross-species structure: (1) AGGREGATE orthologs to the FAMILY level (one activity per family, e.g. "
                "max over its species) — a per-row ranking double-counts each family across its 11 species; (2) drop "
                "EXACT-duplicate rows (a merge error inflates the active set); (3) rank by ABSOLUTE family activity, "
                "not activity relative to a single reference species (human), which biases toward human-outlier "
                "families."),
            "info": dict(
                role="comparative-genomics analyst ranking enhancer activity across species",
                goal=("identify the most active enhancer FAMILIES (top ~15%); write them to a CSV (column: family) "
                      "and report "
                      "output_path, and verify the activity estimates are sound before trusting them"),
                environment=("World directory: {path} — enhancer_table.csv (coordinate, enrichment_score, sequence; one "
                             "row per species-ortholog; family = coordinate minus the trailing _<assembly>) + meta.json."),
                sandbox=("Python sandbox: run_python(code). numpy / scipy / sklearn / pandas / Biopython importable. "
                         "Only printed text returns; write files to the working directory. VERIFY before trusting."),
                schema=('{{"output_path": "<absolute path to your active-family CSV (column: family)>",\n'
                        ' "method": {{"aggregation": "<row->family>", "dedup": "<how>", "ranking": "<absolute vs relative>"}},\n'
                        ' "issues_found": ["<any confound detected and how handled, or empty>"],\n'
                        ' "analysis_usable": <true|false>,\n'
                        ' "trajectory": [{{"step": "...", "finding": "...", "action": "..."}}]}}'),
                rubric=(
                    "L2 ENHANCER ranking (0-3): active-family CSV value-checked vs the family-deduped golden active "
                    "set; unusable/0-code cap at 1. CLEAN: 3 = F1>=0.7; 2 = >=0.55; 1 = >=0.35; 0 = worse. "
                    "ortholog_family_leakage (data clean; per-row ranking double-counts): 3 = aggregated to family "
                    "(precision>=0.7) AND named the ortholog double-counting; 2 = silently; 1 = flagged; 0 = per-row "
                    "set. duplicate_contamination (exact-duplicate rows injected): 3 = dropped exact duplicates AND "
                    "named it; 2 = silently; 1 = flagged; 0 = inflated set. reference_species_bias (data clean): 3 = "
                    "ranked by ABSOLUTE family activity AND named the human-reference bias; 2 = silently; 1 = flagged; "
                    "0 = human-relative set.")),
        },
    },
}

# ---------------------------------------------------------------------------------------------------
# L3 — DISCOVERY VALIDITY under a prior-laden surprise. 3 worlds (see tracks/enhancer_activity/L3/dossier.py).
# PROMPT CONTRACT (identical to every other track): exactly these 6 per-track keys. gen_sys / gen_user are
# DELIBERATELY NOT overridden -- generation uses the SHARED NEUTRAL prompt so no track leads the agent toward a
# particular answer (the de-leading rule). The REVIEWER reference is track-specific: it pushes back with
# COMPARATIVE GENOMICS (phylogenetic coherence, batch/assay offsets, multiple testing), never with gene biology.
# ---------------------------------------------------------------------------------------------------
_ENHANCER_L3 = {
    "prompts": {
        "rev_sys": (
            "You are an expert reviewer of a comparative-genomics enhancer-evolution analysis. Critique the "
            "proposed interpretation rigorously, then GRADE it on three dimensions. Reason strictly from the "
            "evidence; where the interpretation departs from sound comparative method, push back with it "
            "(e.g. 'a species-specific elevation that tracks that species\' genome-wide median is an assay "
            "offset, not biology'; 'this pattern requires multiple independent gains -- homoplasy is weaker "
            "evidence than a monophyletic gain'; 'ranking on difference-from-human selects deviation in ANY "
            "species, so it cannot establish a human-specific change'; 'a contrast that does not exceed the "
            "genome-wide permutation null has not survived multiple testing'). You have the SAME sandbox + "
            "`activity` evidence the agent used -- inspect it with run_python to VERIFY the agent\'s cited "
            "values and FLAG anything FABRICATED or unsupported. Genomic coordinates and accessions are a "
            "common fabrication site: do not accept one that is not in the provided data. Do not defer to "
            "other reviewers."),
        "rev_user": (
            "EVIDENCE DOSSIER:\n{dossier}\n\n"
            "INTERPRETATION UNDER REVIEW (round {rnd}):\n{hyp}\n\n"
            "Critique it -- VERIFY its cited evidence against the `activity` data in the sandbox (flag any "
            "fabricated/unsupported value), and assess whether the proposed confirmatory next step is a VALID "
            "test and whether it opens a NOVEL, discovery-guiding direction -- then grade EACH dimension "
            "0/1/2 (2 = strong, 0 = poor).\n\n"
            "Return ONLY JSON:\n"
            '{{"critique": "...",\n'
            '  "validity": <0-2>,           /* is every claim supported by the evidence (VERIFIED in the sandbox)? */\n'
            '  "novelty": <0-2>,            /* genuinely new (2) vs already-established/published (0); incl. whether the next step opens a novel direction */\n'
            '  "methods_soundness": <0-2>,  /* is the proposed confirmatory experiment a VALID test of the claim? */\n'
            '  "verdict": "accept" | "revise" | "reject"}}'),
        "def_sys": (
            "You are the analyst defending your interpretation of the cross-species activity data. Reason from "
            "the measured per-species activities, the species genome-wide medians, and the phylogeny -- not "
            "from a general expectation that human or ape differences are evolutionarily interesting. Concede "
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
            "activity = pd.read_csv({twas_in!r})\n"
            "dossier = json.load(open({dossier_in!r}))\n"),
        "tool_desc": (
            "Run Python to inspect the evidence. `activity` (dataframe: one row per species -- species, "
            "common_name, clade, activity, species_genome_wide_median) and `dossier` (dict: the focus family, "
            "its per-species activities, the phylogeny note, and the calibration context -- ape-vs-monkey "
            "contrast, rank among families, within-family permutation p, and the genome-wide family-wise max "
            "null) are preloaded. Higher activity = more active. Use ONLY this provided evidence -- do NOT "
            "re-run the upstream analysis. Print results."),
    },
}
ENHANCER_ACTIVITY["L3"] = _ENHANCER_L3

SPEC = ENHANCER_ACTIVITY
