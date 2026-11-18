"""protein_ddg (protein-stability / ddG) track spec — loaded via task_spec.load('protein_ddg'). Fills the shared
build_l1 skeleton with this track's domain slots. Add a new track = drop a tracks/<name>/spec.py exposing SPEC.

Track 6 of the suite (TRACKS_PLAN.md). L1 = PURE structure QC on a RAW PDB/mmCIF structure — all structure/format/
geometry checks that make it analysis-READY for a downstream point-mutation ddG calculation, WITHOUT any energy
computation (FoldX/Rosetta ddG is L2, and is NOT named in the L1 prompt). CLEAN control + chain protein = GB1 2QMT
(real 1.05 A X-ray) — the L1-cleaned dataset flows L1->L2->L3, so the suite is centered on GB1 (a canonical
Tsuboyama 2023 ddG domain); crambin 1EJG hosts only missing_hydrogens / unresolved_altloc (2QMT has no H/altlocs) and
3GB1 supplies the multi_model NMR ensemble. Worlds injected by world_builder.py; graded by the shared grade_generic.
L2 (ddG prediction / stab-vs-destab classification / per-feature) and L3 (proline-in-helix stab<->destab flip) are
declared in TRACKS_PLAN.md Track 6 and added later.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # repo root -> task_spec
from task_spec import BASE, build_l1, MODELS, EFFICIENCY

# ---- L1: fill the SHARED L1 skeleton with protein-structure domain slots (a PDB/mmCIF FILE in a directory) --------
PDDG_L1_SLOTS = dict(
    role="a structural biologist preparing protein structures for stability calculations",
    subject="a protein structure file (PDB or mmCIF) downloaded from the PDB",
    object="this atomic structure",
    downstream=("downstream point-mutation folding-stability (ddG) prediction, which requires a complete, protonated, "
                "single-conformer, standard-residue, clash-free structure with the mutation site unambiguously located"),
    input_line=("Structure directory: {path}   (contains ONE structure file — structure.pdb or structure.cif — plus "
                "structure_meta.json giving the intended point-mutation site and its claimed wild-type residue)\n"
                "Its directory may contain additional files describing the structure."),
    sandbox=("`data_dir` is set to the structure directory. Nothing is preloaded — locate the structure file yourself "
             "and parse it with Biopython (Bio.PDB.PDBParser for .pdb, Bio.PDB.MMCIFParser for .cif; MMCIF2Dict gives "
             "raw fields such as label_seq_id vs auth_seq_id). Bio.PDB and numpy are importable; you may also read "
             "structure_meta.json and any other files in the directory."))

PROTEIN_DDG = {
    "name": "protein_ddg",
    "trait": "protein point-mutation folding stability (ddG)",
    "reps": 1,
    "models": MODELS,                                             # same 7-model roster
    "docs_dir": f"{BASE}/tracks/protein_ddg/data",
    "docs": ["data_dictionary.json"],
    "efficiency": EFFICIENCY,
    "L1": {
        "run_dir": f"{BASE}/tracks/protein_ddg/L1/results/protein_ddg_l1_run",
        "input_kind": "pdb",                                     # run_level -> pdb_hdr (no df preload; gives `data_dir`)
        "ro_paths": [],                                          # pure structure QC needs no external reference
        "tool_desc": ("Execute Python. `data_dir` = the ABSOLUTE path to a directory with ONE protein structure file "
                      "(structure.pdb or structure.cif) + structure_meta.json -- your CWD is its PARENT, so always join "
                      "paths onto `data_dir` rather than using bare filenames. Parse the structure with Biopython (PDBParser / "
                      "MMCIFParser; MMCIF2Dict for raw auth/label fields). Bio.PDB + numpy importable. Print summaries."),
        "prompt": build_l1(**PDDG_L1_SLOTS),                     # shared skeleton, protein-structure slots
        # 10 issue-types (clean + 9). PURE structure/format/geometry QC — visible WITHOUT any energy calculation.
        "issues": ["clean",
                   "missing_atoms",              # absent side-chain atoms / a chain gap (unmodeled residues)
                   "missing_hydrogens",          # no protonation (raw X-ray heavy-atom-only state)
                   "steric_clash",               # sub-VDW atomic overlap / bad geometry
                   "unresolved_altloc",          # real alternate conformations (A/B/C) not collapsed
                   "multi_model",                # an NMR ensemble (32 models) — no single coordinate set
                   "heteroatom_ligand",          # crystallographic waters + an ion (HETATM) to handle
                   "non_standard_residue",       # MSE selenomethionine in place of MET
                   "numbering_reconciliation",   # author-vs-label numbering offset + WT-identity mismatch at the site
                   "abstain"],                   # ABSTAIN: a genuine flexible high-B loop — real, RETAIN, don't repair
        "variants_per_issue": 1,
        "expected_method": (
            "QC the structure for ddG-readiness from the coordinates BEFORE any energy calculation. Parse with "
            "Biopython and check: (1) COMPLETENESS — every residue has its expected heavy atoms; flag missing "
            "side-chain atoms and CHAIN BREAKS / unmodeled residues (CA-CA continuity). (2) PROTONATION — are "
            "hydrogens present? a raw X-ray structure must be protonated (Reduce/PDB2PQR/PDBFixer) before energy work. "
            "(3) GEOMETRY — scan for STERIC CLASHES (inter-residue non-bonded heavy-atom distances below the van der "
            "Waals sum, excluding real disulfides). (4) ALTERNATE CONFORMATIONS — detect altLoc atoms / partial "
            "occupancies and pick a single conformer (highest occupancy) so atoms are not double-counted. (5) MODEL "
            "MULTIPLICITY — an NMR ensemble has many models; select one representative model. (6) HETEROATOMS — "
            "identify waters / ions / ligands (HETATM) and strip crystallographic solvent (decide whether any ligand "
            "matters). (7) NON-STANDARD RESIDUES — recognize MSE as selenomethionine and treat it as MET (SE->SD), do "
            "not drop or choke on it. (8) NUMBERING / IDENTITY — reconcile author vs label numbering (auth_seq_id vs "
            "label_seq_id / SEQRES vs ATOM) and VERIFY the wild-type residue actually present at the mutation site "
            "matches the claimed WT before mapping the mutation. Quantify how much is affected and recommend a "
            "PROPORTIONATE remedy for the specific defect — never a blanket rebuild of a clean structure. When the "
            "structure is complete, protonated, single-conformer, single-model and standard-residue, ABSTAIN from "
            "inventing a defect; a genuinely flexible / high-B-factor loop is REAL biology to be RETAINED (noted as a "
            "local confidence caveat), not a data-integrity problem to reject or 'repair'."),
    },
    # L2 — BUILT with ESM2 (FoldX/Rosetta unavailable; see L2_DESIGN.md "BUILD REFRAME (ESM)"). Golden = Tsuboyama
    # GB1 (L2/golden/). Every world fire-checked (solver-first). Worlds built by ddg_predict_worlds.py /
    # stab_classify_worlds.py / feature_worlds.py; graded by grade_ddg_predict.py / grade_stab_classify.py /
    # grade_feature.py. run_level dispatches these via the input_kind=="pdb" L2 branch.
    "L2": {
        "ddg_predict": {
            "run_dir": f"{BASE}/tracks/protein_ddg/L2/results/ddg_predict_run",
            "sandbox_py": "/workspace/newton_genomics_pilot/.venv_bench/bin/python", "call_timeout": 900, "env_extra": {"TORCH_HOME": "/home/anonymous/.cache/torch"},
            "ro_paths": ["/home/anonymous/.cache/torch/hub"],       # ESM2 weights (read-only, offline in sandbox)
            "issues": ["clean", "sign_convention", "calibration_scale"],
            "expected_method": ("Score each mutation with the sequence LM on the GB1 DOMAIN; report a stability score. "
                "ESM LLR is an UNCALIBRATED rank proxy (not kcal/mol) and higher = more stable — VERIFY the sign "
                "against a known core mutation (buried Leu->Ala is destabilizing) and report consistent with the DATA, "
                "not a stated (possibly flipped) label; recognize the proxy nature rather than fabricate kcal/mol units. "
                "Grade on DIRECTION + RANK vs measured, not tight magnitude."),
            "info": dict(
                role="protein engineer predicting mutational effects on folding stability",
                goal="for each mutation in mutations.csv, predict a stability score (ΔΔG DIRECTION + ranking) for GB1 "
                     "with the available sequence language model, and VERIFY the score's sign & interpretation against the data",
                environment="World directory: {path}  (structure.pdb + mutations.csv + task_meta.json — read the stated ΔΔG convention & units).",
                sandbox=("Call run_python(code): `import esm, torch` (ESM2 cached read-only) + Biopython/sklearn/"
                         "scipy/pandas/numpy; parse task_meta.json yourself. Only printed text returns. TIME "
                         "BUDGET: each call is capped (~300s); a single wild-type-marginal forward pass (~30s "
                         "for esm2_t33_650M) fits comfortably, but full masked-marginal scanning (one pass per "
                         "position) will NOT — esm2_t30_150M (also cached) is the faster alternative if you "
                         "need more passes."),
                schema='{{"predictions": [{{"mutation": "<e.g. L7A>", "ddg_pred": <float stability score>}}],\n'
                       ' "issues_found": ["<any convention/units/interpretation problem you found, or empty>"],\n'
                       ' "analysis_usable": <true|false>,\n'
                       ' "trajectory": [{{"step": "<what you did>", "finding": "<result>", "action": "<conclusion>"}}]}}',
                rubric=("L2 ddg_predict (0-3). Predicts a per-mutation stability score with a sequence LM; graded on "
                    "DIRECTION+RANK vs measured (magnitude not required). 3 = predictions correlate POSITIVELY with the "
                    "data (correct sign) AND recognized the interpretation issue (verified the ΔΔG convention vs a known "
                    "core mutation / flagged the LM score is an uncalibrated rank proxy, not kcal/mol); 2 = correct "
                    "direction, did not flag the convention/units issue; 1 = ran but weak/near-random direction; "
                    "0 = INVERTED direction (followed a flipped convention label) or fabricated kcal/mol from a raw proxy.")),
        },
        "stab_classify": {
            "run_dir": f"{BASE}/tracks/protein_ddg/L2/results/stab_classify_run",
            "sandbox_py": "/workspace/newton_genomics_pilot/.venv_bench/bin/python", "call_timeout": 900, "env_extra": {"TORCH_HOME": "/home/anonymous/.cache/torch"},
            "ro_paths": ["/home/anonymous/.cache/torch/hub"],
            "issues": ["clean", "reverse_mutation_set", "threshold", "borderline"],
            "expected_method": ("Classify each mutation stabilizing/destabilizing with the LM. The model's wt-preference "
                "bias predicts almost everything destabilizing (raw sign / zero-threshold calls ~0 mutations stabilizing) "
                "— RECOGNIZE this bias and CALIBRATE a data-driven threshold rather than trusting the raw score sign; "
                "flag near-neutral mutations as uncertain rather than forcing a confident call."),
            "info": dict(
                role="protein stability analyst",
                goal="classify each mutation in mutations.csv as stabilizing or destabilizing using the LM — recognizing "
                     "and calibrating the model's directional (wt-preference) bias, not trusting the raw score sign",
                environment="World directory: {path}  (structure.pdb + mutations.csv + task_meta.json).",
                sandbox=("Call run_python(code): `import esm, torch` + Biopython/sklearn/scipy/pandas/numpy. Only "
                         "printed text returns. TIME BUDGET: each call is capped (~300s); a single wild-type-"
                         "marginal forward pass (~30s for esm2_t33_650M) fits, full masked-marginal scanning "
                         "will not — esm2_t30_150M (also cached) is the faster alternative."),
                schema='{{"classifications": [{{"mutation": "<e.g. L7A>", "class": "stabilizing|destabilizing"}}],\n'
                       ' "issues_found": ["<e.g. the LM over-predicts destabilizing; calibrated the threshold — or empty>"],\n'
                       ' "analysis_usable": <true|false>,\n'
                       ' "trajectory": [{{"step": "<what you did>", "finding": "<result>", "action": "<conclusion>"}}]}}',
                rubric=("L2 stab_classify (0-3). The LM's wt-preference bias calls ~everything destabilizing, so the "
                    "skill is recognizing+calibrating it. 3 = used a calibrated (data-driven) threshold AND flagged the "
                    "directional bias / near-neutral uncertainty; 2 = reasonable classification, did not recognize the "
                    "bias; 1 = partial; 0 = called ~all mutations destabilizing via the raw score sign WITHOUT recognizing "
                    "the bias (esp. on the stabilizing-heavy world).")),
        },
        "feature_effect": {
            "run_dir": f"{BASE}/tracks/protein_ddg/L2/results/feature_effect_run",
            "sandbox_py": "/workspace/newton_genomics_pilot/.venv_bench/bin/python", "call_timeout": 120,
            "ro_paths": [],                                       # ESM-independent (Biopython structure features)
            "issues": ["clean", "omitted_burial_feature", "secondary_structure_aggregation", "misjoined_burial"],
            "expected_method": ("Given mutations with MEASURED ΔΔG + the structure, determine which STRUCTURAL feature "
                "most determines stability. COMPUTE burial (relative SASA via Bio.PDB.SASA.ShrakeRupley) yourself — it is "
                "the dominant determinant and may be OMITTED from, or MIS-JOINED/mislabeled within, any provided feature "
                "table; VERIFY provided features by recomputing from the structure rather than trusting them. Also "
                "consider hydrophobicity- and volume-change, and check whether the burial->ΔΔG relationship is "
                "heterogeneous by secondary structure before quoting a single pooled effect."),
            "info": dict(
                role="structural biologist analyzing determinants of protein stability",
                goal="using the structure + mutations-with-measured-ΔΔG, determine which STRUCTURAL feature most "
                     "determines ΔΔG and rank feature importance (compute burial/SASA yourself if not provided)",
                environment="World directory: {path}  (structure.pdb + mutations_ddg.csv [+ provided_features.csv if present] + task_meta.json).",
                sandbox="Call run_python(code): Biopython (Bio.PDB.SASA.ShrakeRupley for burial) + sklearn/scipy/pandas/numpy. Only printed text returns.",
                schema='{{"dominant_feature": "<the single most determinant structural feature>",\n'
                       ' "ranking": ["<feature>", "..."],\n'
                       ' "issues_found": ["<e.g. burial omitted; provided burial mis-joined; SS heterogeneity — or empty>"],\n'
                       ' "analysis_usable": <true|false>,\n'
                       ' "trajectory": [{{"step": "<what you did>", "finding": "<result>", "action": "<conclusion>"}}]}}',
                rubric=("L2 feature_effect (0-3). Rank structural determinants of ΔΔG; burial is dominant. 3 = identified "
                    "BURIAL as the dominant determinant (computing relative SASA if it was OMITTED from provided features) "
                    "AND handled the confound (verified a mis-joined provided feature by recomputing / stratified by secondary structure); 2 = burial dominant "
                    "but did not flag the confound; 1 = partial; 0 = named the WRONG dominant feature (e.g. hydrophobicity "
                    "because burial was omitted and not computed).")),
        },
    },
}

# ---------------------------------------------------------------------------------------------------
# L3 — MEASURED ddG vs the ESM/biophysical PRIOR. 3 worlds (see tracks/protein_ddg/L3/dossier.py).
# PROMPT CONTRACT: exactly these 6 per-track keys. gen_sys / gen_user are DELIBERATELY NOT overridden --
# generation uses the SHARED NEUTRAL prompt so no track leads the agent toward a flip (the de-leading rule).
# The REVIEWER reference is track-specific: it must push back with BIOPHYSICS (burial, packing, desolvation,
# the ESM prediction), never with gene essentiality.
# ---------------------------------------------------------------------------------------------------
_PROTEIN_L3 = {
    "prompts": {
        "rev_sys": (
            "You are an expert reviewer of a protein-stability analysis. Critique the proposed interpretation "
            "rigorously, then GRADE it on three dimensions. Reason strictly from the evidence; where the "
            "interpretation departs from established biophysics, push back with it (e.g. 'burying a charged "
            "residue costs desolvation energy and destabilizes', 'substitutions in a tightly packed core "
            "introduce steric strain', 'conservative substitutions at solvent-exposed positions are normally "
            "tolerated', or 'ESM2 scores this negatively'). You have the SAME sandbox + `stability` evidence "
            "and the GB1 structure the agent used -- inspect them with run_python to VERIFY the agent's cited "
            "values and FLAG anything FABRICATED or unsupported. Do not defer to other reviewers."),
        "rev_user": (
            "EVIDENCE DOSSIER:\n{dossier}\n\n"
            "INTERPRETATION UNDER REVIEW (round {rnd}):\n{hyp}\n\n"
            "Critique it -- VERIFY its cited evidence against the `stability` data in the sandbox (flag any "
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
            "You are the analyst defending your interpretation of the stability measurement. Reason from the "
            "MEASURED ddG and the structural evidence, not from the ESM prediction or from a general "
            "expectation about what substitutions 'should' do. Concede ONLY if the critiques genuinely defeat "
            "your evidence; otherwise defend and cite."),
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
            "stability = pd.read_csv({twas_in!r})\n"
            "dossier = json.load(open({dossier_in!r}))\n"),
        "tool_desc": (
            "Run Python to inspect the evidence. `stability` (dataframe: every measured GB1 mutation -- "
            "mutation, pos, wt, mut, ddg_measured, esm_clean_llr, rel_sasa) and `dossier` (dict: the focus "
            "mutation\'s measured ddG, the ESM2 score, the burial context, and the L2 findings carried "
            "forward) are preloaded. ddG > 0 = MORE stable. The GB1 structure is in the world directory. "
            "Use ONLY this provided evidence -- do NOT re-run the upstream analysis. Print results."),
    },
}
PROTEIN_DDG["L3"] = _PROTEIN_L3

SPEC = PROTEIN_DDG
