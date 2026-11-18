"""clinvar_acmg track spec — loaded via task_spec.load('clinvar_acmg'). Fills the shared build_l1/build_l2/build_l3
skeletons with this track's domain slots. Add a new track = drop a tracks/<name>/spec.py exposing SPEC."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # repo root -> import task_spec
from task_spec import BASE, build_l1, build_l3, build_l3_reviewer, MODELS, EFFICIENCY

CLINVAR_L1_SLOTS = dict(
    role="a clinical genomics analyst", subject="a single-sample VCF (GRCh38)",
    object="these variant calls", downstream="downstream clinical interpretation (annotation, ACMG classification)",
    input_line="VCF path: {path}   (single-sample; its directory may contain additional files describing the sample)",
    resources=("\nA GRCh38 reference FASTA is available read-only at /data/anonymous/dna_token/hg38.fa "
               "(open with pysam.FastaFile) should you need it."),
    sandbox=("`vcf_path` is set to the VCF path; parse it yourself (pysam.VariantFile or plain text). "
             "pandas/numpy/pysam are importable; you may also read other files in the VCF's directory."))

# ---- Track 3: Clinical variant (ACMG / pathogenicity). L1 ONLY for now (L2/L3 TBD). Shares the variant tool
# image (bench venv + pysam) and mounts hg38.fa read-only as a resource. Substrate + worlds are built by
# tracks/clinvar_acmg/{build_substrate,world_builder}.py; L1 grades via grade_generic (unchanged).
_L2RES = f"{BASE}/tracks/clinvar_acmg/L2/l2/resources"
_CLINVAR_DB = f"{_L2RES}/clinvar.panel.vcf.gz"
_GNOMAD_DB  = f"{_L2RES}/gnomad.panel.vcf.gz"
_CADD_DB    = f"{_L2RES}/cadd.panel.tsv.gz"
_HG38 = "/data/anonymous/dna_token/hg38.fa"
_L2_RO = [_CLINVAR_DB, _CLINVAR_DB + ".tbi", _GNOMAD_DB, _GNOMAD_DB + ".tbi",
          _CADD_DB, _CADD_DB + ".tbi", _HG38, _HG38 + ".fai"]

# The agent is NOT handed annotations — it must SELECT + query these mounted references (tool-use is graded).
_L2_RESOURCES = (
    "You have a Python sandbox (pysam, pandas, numpy, scipy) and these READ-ONLY reference databases — decide\n"
    "which you need and query them yourself with pysam (no network):\n"
    f"  - gnomAD v4.1 sites (population AF): {_GNOMAD_DB}  [contigs are chr-prefixed, e.g. 'chr19'; INFO AF, AF_grpmax, FILTER]\n"
    f"  - ClinVar (prior classifications): {_CLINVAR_DB}  [contigs NOT chr-prefixed, e.g. '19'; INFO CLNSIG, CLNREVSTAT (review stars), MC (molecular consequence), GENEINFO]\n"
    f"  - CADD v1.7 (in-silico): {_CADD_DB}  [tabix TSV, no chr-prefix; columns: chrom pos ref alt rawscore PHRED]\n"
    f"  - GRCh38 reference: {_HG38}  [pysam.FastaFile]\n"
    "Variants you must assess are flagged with INFO/TARGET in the proband VCF. IMPORTANT: some annotations "
    "written IN the VCF INFO (CSQ, AF, REVEL, CLINVAR_ECHO) may be WRONG or misleading — VERIFY every "
    "decision-relevant value against the reference databases above; do not trust the in-VCF annotation blindly.")

# L2 prompt SLOTS for clinvar (fill run_level.L2_SKELETON via build_l2) — FULL-ALIGNED to the GWAS skeleton:
# explicit GOAL, issues_found + analysis_usable honesty fields, trajectory key `action`. Answer fields
# (classifications/ranking/reportable/top_pick + per-target evidence) preserved so the deterministic graders
# key on them unchanged. This CHANGES the clinvar L2 prompts -> clinvar L2 re-run.
_CV_SANDBOX = ("Call run_python(code) with pysam/pandas/numpy/scipy; query the reference DBs yourself with "
               "pysam.VariantFile / TabixFile / FastaFile (no network). Only printed text returns; no plots.")
CLINVAR_L2_INFO = {
 "classify": dict(
   role="clinical molecular geneticist applying the ACMG/AMP variant-classification guidelines",
   goal="classify EACH variant flagged INFO/TARGET in the proband VCF into one of three bins — pathogenic (P/LP), vus, or benign (LB/B) — applying the relevant ACMG criteria (PVS1, PM2, PP3, BS1, BA1, ...) using evidence you GATHER yourself",
   environment="Proband VCF: {path}\n\n" + _L2_RESOURCES,
   sandbox=_CV_SANDBOX,
   schema='{{"classifications": [{{"variant": "<chrom:posREF>ALT>", "class": "pathogenic|vus|benign", "criteria": ["<ACMG codes applied>"], "evidence": "<key evidence + sources you queried>"}}],\n "issues_found": ["<any in-VCF annotation (CSQ/AF/REVEL/CLINVAR_ECHO) you found to be WRONG or misleading vs the references, or empty>"],\n "analysis_usable": <true|false>,\n "trajectory": [{{"step": "<what you did>", "finding": "<result>", "action": "<criterion/decision>"}}]}}'),
 "prioritize": dict(
   role="clinical genomicist doing diagnostic variant prioritization for a proband",
   goal="rank the candidate variants (INFO/TARGET) by how likely each is the CAUSAL diagnosis for this proband's phenotype (see `phenotype_hpo` in study_metadata.json). Integrate consequence severity x rarity x phenotype-gene match x call quality x inheritance/zygosity consistency — NOT predicted impact alone; deprioritize likely artifacts and phenotype/inheritance-inconsistent calls",
   environment="Proband VCF: {path}\n\n" + _L2_RESOURCES,
   sandbox=_CV_SANDBOX,
   schema='{{"ranking": [{{"variant": "<chrom:posREF>ALT>", "rank": <1=most likely causal>, "reason": "<why>"}}],\n "top_pick": "<the single most likely causal variant>",\n "issues_found": ["<any in-VCF annotation you found WRONG/misleading vs the references, or empty>"],\n "analysis_usable": <true|false>,\n "trajectory": [{{"step": "<what you did>", "finding": "<result>", "action": "<decision>"}}]}}'),
 "secondary_findings": dict(
   role="clinical laboratory geneticist screening for ACMG SECONDARY FINDINGS (SF v3.2)",
   goal="return the variants that are REPORTABLE as secondary findings — pathogenic/likely-pathogenic ONLY, in ACMG-SF genes ONLY. Do NOT report VUS, benign/common variants, likely artifacts, or variants in non-SF genes; a false positive triggers an unnecessary clinical intervention. Scan all variants; verify pathogenicity + gene scope + call quality + AF against the references",
   environment="Proband VCF: {path}\n\n" + _L2_RESOURCES,
   sandbox=_CV_SANDBOX,
   schema='{{"reportable": [{{"variant": "<chrom:posREF>ALT>", "gene": "<gene>", "reason": "<why reportable>"}}],\n "issues_found": ["<any in-VCF annotation you found WRONG/misleading vs the references, or empty>"],\n "analysis_usable": <true|false>,\n "trajectory": [{{"step": "<what you did>", "finding": "<result>", "action": "<report/exclude + why>"}}]}}'),
}

CLINVAR_L2_INFO["classify"]["rubric"] = """L2 CLASSIFY (0-3). A proband gene panel; ONE target variant carries an INJECTED FALSE
annotation (the confound: a wrong AF / consequence / REVEL / ClinVar echo) that contradicts the mounted references
(gnomAD/ClinVar/CADD). Score the agent's call ON THE CONFOUND TARGET: 3 = correct ACMG bin AND explicitly flagged the
injected annotation as wrong / verified it against the reference (the flag may be in the target's evidence OR in
issues_found); 2 = correct bin but did NOT flag the lie (silently right); 1 = off by one adjacent bin (path<->vus or
vus<->benign); 0 = fooled (wrong non-adjacent bin / believed the lie) or never classified it. CLEAN world (no
confound): 3 = all panel targets correct, 2 = one off, else 1/0."""
CLINVAR_L2_INFO["prioritize"]["rubric"] = """L2 PRIORITIZE (0-3). Rank candidate variants for the proband's phenotype. 3 = ranked the
true CAUSAL variant #1, demoted the distractor(s), AND named WHY each distractor is not causal (artifact quality /
too-common AF / wrong-gene-for-phenotype / heterozygous-in-a-recessive-gene); 2 = causal #1 + distractor demoted but
reason not named; 1 = causal near top but not #1, or a distractor not demoted; 0 = a distractor ranked over the causal."""
CLINVAR_L2_INFO["secondary_findings"]["rubric"] = """L2 SECONDARY FINDINGS (0-3). Report EXACTLY the pathogenic/likely-pathogenic-in-
ACMG-SF-gene variants and nothing else. 3 = exact reportable set AND justified excluding the injected trap (a
sequencing artifact / a non-SF gene / a VUS / a benign-common variant; the justification may be in issues_found or a
reason field); 2 = exact set but no justification for the exclusion; 1 = one error (one false positive OR one miss);
0 = missed a true finding or reported the trap."""

_CLASSIFY_PROMPT = f"""You are a clinical molecular geneticist applying the ACMG/AMP variant-classification guidelines.
Proband VCF: {{path}}

Classify EACH variant flagged INFO/TARGET into one of three bins: pathogenic (P/LP), vus, or benign (LB/B).
Apply the relevant ACMG criteria (PVS1, PM2, PP3, BS1, BA1, ...) using evidence you GATHER yourself.
{_L2_RESOURCES}

Record every check in `trajectory` (which database you queried, what it returned, which ACMG criterion it set).
Return ONLY JSON:
{{{{"classifications": [{{{{"variant": "<chrom:posREF>ALT>", "class": "pathogenic|vus|benign",
                       "criteria": ["<ACMG codes applied>"], "evidence": "<key evidence + sources you queried>"}}}}],
 "trajectory": [{{{{"step": "<what you did>", "finding": "<result>", "conclusion": "<criterion/decision>"}}}}]}}}}"""

_PRIORITIZE_PROMPT = f"""You are a clinical genomicist doing diagnostic variant prioritization for a proband.
Phenotype (from study_metadata.json): see `phenotype_hpo`.  Proband VCF: {{path}}

Rank the candidate variants (INFO/TARGET) by how likely each is the CAUSAL diagnosis for this phenotype.
Integrate consequence severity x rarity x phenotype-gene match x call quality x inheritance/zygosity consistency
— NOT predicted impact alone. Deprioritize likely artifacts and phenotype/inheritance-inconsistent calls.
{_L2_RESOURCES}

Record every check in `trajectory`. Return ONLY JSON:
{{{{"ranking": [{{{{"variant": "<chrom:posREF>ALT>", "rank": <1=most likely causal>, "reason": "<why>"}}}}],
 "top_pick": "<the single most likely causal variant>",
 "trajectory": [{{{{"step": "<what you did>", "finding": "<result>", "conclusion": "<decision>"}}}}]}}}}"""

_SF_PROMPT = f"""You are a clinical laboratory geneticist screening for ACMG SECONDARY FINDINGS (SF v3.2).
Proband VCF: {{path}}

Return the variants that are REPORTABLE as secondary findings: pathogenic/likely-pathogenic ONLY, in ACMG-SF
genes ONLY. Do NOT report: VUS, benign/common variants, likely artifacts, or variants in non-SF genes — a false
positive triggers an unnecessary clinical intervention. Scan all variants; verify pathogenicity + gene scope +
call quality + AF against the references.
{_L2_RESOURCES}

Record every check in `trajectory`. Return ONLY JSON:
{{{{"reportable": [{{{{"variant": "<chrom:posREF>ALT>", "gene": "<gene>", "reason": "<why reportable>"}}}}],
 "trajectory": [{{{{"step": "<what you did>", "finding": "<result>", "conclusion": "<report/exclude + why>"}}}}]}}}}"""

_CLINVAR_L2 = {
    "classify": {
        "run_dir": f"{BASE}/tracks/clinvar_acmg/L2/results/clinvar_l2_classify_run", "ro_paths": _L2_RO, "info": CLINVAR_L2_INFO["classify"],
        "issues": ["clean", "af_confound", "consequence_confound", "splice_pvs1", "insilico_confound", "clinvar_echo"],
        "expected_method": ("Apply ACMG/AMP: gather consequence (ClinVar MC), population AF (gnomAD; check "
            "popmax-vs-global + FILTER), in-silico (CADD PHRED) yourself; VERIFY any in-VCF annotation against "
            "these; classify into path/VUS/benign. Do not let a corrupted single field flip the call."),
    },
    "prioritize": {
        "run_dir": f"{BASE}/tracks/clinvar_acmg/L2/results/clinvar_l2_prioritize_run", "ro_paths": _L2_RO, "info": CLINVAR_L2_INFO["prioritize"],
        "issues": ["clean", "artifact_highimpact", "af_distractor", "phenotype_mismatch", "inheritance_mismatch"],
        "expected_method": ("Rank by consequence x rarity x phenotype-gene match x call quality x inheritance; "
            "deprioritize artifact-signature calls, common variants, wrong-gene-for-phenotype, and single hits "
            "in recessive genes."),
    },
    "secondary_findings": {
        "run_dir": f"{BASE}/tracks/clinvar_acmg/L2/results/clinvar_l2_sf_run", "ro_paths": _L2_RO, "info": CLINVAR_L2_INFO["secondary_findings"],
        "issues": ["clean", "artifact_lof", "out_of_scope", "vus_overreport", "af_benign"],
        "expected_method": ("Report P/LP ONLY, in ACMG-SF genes ONLY; exclude VUS, benign/common, artifacts, and "
            "non-SF genes. Verify pathogenicity + scope + AF + call quality."),
    },
}

# ================= L3: molecular-diagnosis under textbook-gene prior (diagnosis-flip) =====================
# Chains off the L2-clean classified panel. The counterfactual makes the EVIDENCE point to a non-classic PARTNER
# gene, contradicting the phenotype's famous gene. Prompts fill the SHARED build_l3 skeleton (clinical wording);
# the root run_l3/grade_l3 load these via SPEC["L3"]["prompts"] (manifest carries track="clinvar_acmg"). JSON
# schema KEYS are identical to the GWAS defaults (the grader/runner read fixed keys); only the prose changes.
_L3_GEN_SYS = ("You are a clinical molecular geneticist doing diagnostic variant interpretation for a proband. "
    "Reason strictly from the provided evidence; you may inspect it with the sandbox. Cite only real, public "
    "literature and guidelines (e.g. ACMG/AMP).")
_L3_GEN_USER = build_l3(
  context="VARIANT PANEL + EVIDENCE DOSSIER (a proband's candidate variants, each already classified by an upstream "
          "ACMG pipeline; the phenotype and per-variant evidence are in the dossier):\n{dossier}",
  task="Based ONLY on this evidence, determine the MOLECULAR DIAGNOSIS: which single variant/gene best explains the\n"
       "proband's phenotype. Re-verify the handed classifications against the evidence (you may inspect `panel`/\n"
       "`dossier` in the sandbox: population frequency, in-silico scores, molecular consequence, ClinVar, review\n"
       "status), weighing ACMG evidence. Then propose a NOVEL, SPECIFIC, TESTABLE mechanistic hypothesis for HOW that\n"
       "variant produces the phenotype — a genuinely new molecular/cellular mechanism at the protein/pathway level\n"
       "that goes BEYOND restating the known gene-disease label — and propose ONE concrete confirmatory next step\n"
       "(e.g. segregation, functional assay, orthogonal test). Cite the literature/guidelines you rely on. If the\n"
       'evidence is insufficient for a confident diagnosis, set "evidence_sufficient": false and explain what is missing.',
  schema='{{"evidence_sufficient": <true|false>, "insufficiency_reason": "<if false, what is missing>",\n'
         ' "hypothesis": "<molecular diagnosis: causal gene + variant, or \'none\'>",\n'
         ' "supporting_evidence": ["..."], "citations": [{{"claim":"...","reference":"..."}}],\n'
         ' "mechanism": "<a NOVEL, specific, testable molecular/cellular mechanism (protein/pathway level) + ONE confirmatory next step>",\n'
         ' "confidence": <0-1>}}')
# Reviewer via the SHARED skeleton (task_spec.build_l3_reviewer) — only the DOMAIN slots below are track-specific.
_L3_REV_SYS, _L3_REV_USER = build_l3_reviewer(
    role="member of a clinical variant-classification / molecular tumor-board committee reviewing a proband's "
         "proposed molecular diagnosis",
    pushback="where the proposed diagnosis departs from the classic gene for the phenotype or from ClinVar "
             "consensus, push back with established clinical genetics",
    data_obj="panel", subject="proposed molecular diagnosis",
    methods_hint="ACMG evidence weighting; consequence/AF/in-silico use; no reputation-driven call")
_L3_DEF_SYS = ("You are the clinician defending your molecular diagnosis before the committee. Reason from the "
    "evidence, not from a gene's reputation. Concede ONLY if the critiques genuinely defeat your evidence; otherwise "
    "defend and cite.")
_L3_DEF_USER = build_l3(
  context="Your current molecular diagnosis:\n{hyp}\n\nThe three committee reviewers said:\n{critiques}",
  task="Respond. Based on the evidence, you may: defend the diagnosis (cite the evidence, use the sandbox if useful)\n"
       "and keep it; revise it as far as the evidence warrants; concede if it is genuinely defeated; or state that\n"
       "you need more information if the evidence no longer sustains it. If you keep or revise a novel diagnosis,\n"
       "RE-STATE its novelty for the CURRENT version.",
  schema='{{"response": "...", "revised_hypothesis": "...", "concede": <true|false>,\n'
         ' "need_more_information": <true|false>, "changed": "<none|minor|major|retracted>",\n'
         ' "novelty_justification": "<what is NEW about your CURRENT (possibly revised) diagnosis + next step, or \'none\'>"}}')
_L3_SANDBOX_PREAMBLE = ("import pandas as pd, numpy as np, json\n"
    "panel = pd.read_csv({twas_in!r})\n"
    "dossier = json.load(open({dossier_in!r}))\n")
_L3_TOOL_DESC = ("Run Python to inspect the evidence. `panel` (dataframe: one row per candidate variant with its "
    "ACMG evidence) and `dossier` (dict: phenotype + per-variant evidence + the upstream classifications) are "
    "preloaded. Use ONLY this provided evidence -- do NOT re-run the upstream analysis. Print results.")
# _L3_JUDGE_SYS / _L3_JUDGE_RUBRIC removed -> L3 grading uses the UNIVERSAL rubric in grade_l3.py.

_CLINVAR_L3 = {
    "run_dir": f"{BASE}/tracks/clinvar_acmg/L3/results/l3_run",
    "reviewers": [["rev_zhipu", "glm-4.6"], ["rev_google", "gemini-3.1-flash-lite-preview"],
                  ["rev_deepseek", "deepseek-reasoner"]],
    "judge": "gpt-5.5", "judge_k": 3, "rounds": 3,
    "expected_method": ("Integrate ACMG/AMP evidence for each candidate variant — population frequency (BA1/BS1 vs "
        "PM2), computational/in-silico (PP3/BP4), molecular consequence (PVS1 for LOF), review status, and "
        "phenotype–gene fit + inheritance — and re-verify the handed classifications against the raw evidence. "
        "Determine the causal molecular diagnosis from the EVIDENCE, not from which gene is most famously associated "
        "with the phenotype; when the data points to a non-classic gene, follow it, name the conflict with the "
        "textbook expectation, and request confirmatory segregation/functional studies rather than defaulting to the "
        "reputation gene or over-calling pathogenicity. Answer VUS only when the evidence is genuinely mixed, not to "
        "avoid a decisive call."),
    # diagnosis-flip target pairs (all locus-heterogeneous, both genes in the L2 panel). anchor = phenotype's classic
    # gene (made benign in the flip); partner = the data-supported causal gene (the correct answer).
    "pairs": [
        {"world": "cf_FH",    "phenotype": "familial hypercholesterolemia (markedly elevated LDL-C, tendon xanthomas, premature coronary artery disease)",
         "anchor": "LDLR",  "partner": "APOB"},
        {"world": "cf_Lynch", "phenotype": "Lynch syndrome (early-onset colorectal and endometrial cancer, MSI-high / mismatch-repair-deficient tumors)",
         "anchor": "MLH1",  "partner": "MSH2"},
        {"world": "cf_HBOC",  "phenotype": "hereditary breast and ovarian cancer syndrome (early-onset / bilateral breast cancer, ovarian cancer, strong family history)",
         "anchor": "BRCA1", "partner": "BRCA2"},
    ],
    "prompts": {
        # gen_sys/gen_user REMOVED -> uses the shared NEUTRAL default in run_l3.py (track-agnostic agent prompt).
        "rev_sys": _L3_REV_SYS, "rev_user": _L3_REV_USER,
        "def_sys": _L3_DEF_SYS, "def_user": _L3_DEF_USER,
        "sandbox_preamble": _L3_SANDBOX_PREAMBLE, "tool_desc": _L3_TOOL_DESC,
        # judge_sys/judge_rubric REMOVED -> uses the UNIVERSAL grading schema in grade_l3.py. Track specifics reach
        # the judge via the ground truth (gt) + the expected_method REFERENCE, NOT via the rubric.
    },
}

CLINVAR_ACMG = {
    "name": "clinvar_acmg",
    "trait": "clinical germline variant interpretation",
    "reps": 1,
    "models": MODELS,                              # same 7-model roster
    "docs_dir": f"{BASE}/tracks/clinvar_acmg/L1/data",
    "docs": ["data_dictionary.json"],                         # per-cell study_metadata is mounted via agent_metadata
    "efficiency": EFFICIENCY,
    "L1": {
        "run_dir": f"{BASE}/tracks/clinvar_acmg/L1/results/clinvar_l1_run",
        "input_kind": "vcf",                                  # run_level -> vcf_hdr (no df preload) + ro mount
        "ro_paths": ["/data/anonymous/dna_token/hg38.fa", "/data/anonymous/dna_token/hg38.fa.fai"],
        "tool_desc": ("Execute Python. `vcf_path` = the VCF to QC; the GRCh38 reference FASTA is read-only at "
                      "/data/anonymous/dna_token/hg38.fa (open with pysam.FastaFile). Print results."),
        "prompt": build_l1(**CLINVAR_L1_SLOTS),              # shared skeleton, clinvar slots
        "issues": ["clean", "low_coverage", "strand_bias", "contamination", "build_mismatch", "af_scale",
                   "duplicate_variants", "metadata_reconciliation", "reference_validation", "abstain_vus"],
        "variants_per_issue": 3,
        "expected_method": ("Validate the VCF systematically: check each record's REF allele against the GRCh38 "
            "reference (pysam); verify coordinates/build; confirm alleles are in {A,C,G,T} and indels are "
            "left-aligned/normalized; inspect per-genotype depth (DP), genotype quality (GQ), strand bias (FS) "
            "and allele-balance (het AD ratio); check INFO/AF is a FRACTION in [0,1]; detect duplicate records; "
            "and reconcile the metadata (sample id, sample count, build) against the file. Quantify how many "
            "records are affected and recommend a PROPORTIONATE remedy (flag/filter/normalize/rescale the "
            "specific offending records) — never a blanket edit on clean data. When the VCF is well-formed and "
            "QC-clean, ABSTAIN from inventing a defect; a variant being of uncertain significance is a "
            "downstream interpretation question, not an L1 data-integrity problem."),
    },
    "L2": _CLINVAR_L2,     # defined below (3 analysis-under-confound sub-tasks: classify / prioritize / secondary_findings)
    "L3": _CLINVAR_L3,     # molecular-diagnosis diagnosis-flip (defined above)
}

SPEC = CLINVAR_ACMG
