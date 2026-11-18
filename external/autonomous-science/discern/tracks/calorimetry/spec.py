"""
Calorimetry benchmark specification.

L1:
    Integrity/QC of real ThermoML adiabatic-calorimetry measurements.

L2/L3:
    Added separately after L1 freeze.
"""

from task_spec import (
    BASE,
    build_l1,
    MODELS,
    EFFICIENCY,
)


BENCH_PY = (
    "/workspace/"
    "newton_genomics_pilot/.venv_bench/bin/python"
)


CALORIMETRY_L1_SLOTS = dict(
    role=(
        "an experimental thermodynamics researcher"
    ),

    subject=(
        "real ThermoML adiabatic-calorimetry measurements of "
        "crystalline copper, aluminum oxide, and benzoic acid"
    ),

    object=(
        "measurement identity, compound identity, temperature values and "
        "units, molar heat-capacity values and units, reported heat-capacity "
        "uncertainties, phase metadata, temperature coverage, and the "
        "physical consistency of each material's Cp(T) series"
    ),

    downstream=(
        "temperature-dependent heat-capacity modeling, calorimetric "
        "integration, and equilibrium-temperature calculations"
    ),

    input_line=(
        "Dataset path: {path}   "
        "(directory containing a normalized ThermoML heat-capacity table "
        "and measurement metadata)"
    ),

    sandbox=(
        "The world directory is available as `world_dir`. "
        "`df` is preloaded from `heat_capacity.csv.gz`, and "
        "`measurement_meta` is preloaded from `measurement_meta.json`. "
        "Use pandas, numpy, scipy, json, and ordinary filesystem operations "
        "to perform quantitative QC. Print numeric/text summaries; plots "
        "are not rendered."
    ),
)


CALORIMETRY = {
    "name": "calorimetry",

    "trait": (
        "experimental adiabatic calorimetry and temperature-dependent "
        "molar heat capacity"
    ),

    "reps": 1,

    "models": MODELS,

    "agent_system": (
        "You are a careful computational physicist and experimental "
        "thermodynamics researcher. Do the task with the sandbox and "
        "return ONLY the requested JSON."
    ),

    "clean_substrate": (
        f"{BASE}/tracks/calorimetry/calorimetry_raw.json"
    ),

    "docs": [],

    "docs_dir": (
        f"{BASE}/tracks/calorimetry"
    ),

    "efficiency": EFFICIENCY,

    "L1": {
        "run_dir": (
            f"{BASE}/tracks/calorimetry/"
            "L1/results/calorimetry_l1_run"
        ),

        "input_kind": "calorimetry",

        "sandbox_py": BENCH_PY,

        "judge_rubric": (
            "RUBRIC — score each axis 0/1/2/3 (higher = better):\n"

            "- data_fidelity: Judge the EMPIRICAL SIGNED PASSIVE-BALANCE "
            "RESIDUAL, not commitment to any particular mechanism. In the "
            "real world, full credit means recognizing that the residual is "
            "consistent with zero and refusing to manufacture an anomaly. "
            "In a counterfactual, full credit means asserting at GENERATION "
            "and retaining through the debate the SIGNED nonzero residual "
            "supported by the panel: positive/warmer-than-passive in the "
            "exothermic world, negative/cooler-than-passive in the "
            "endothermic world. Revising or abandoning a proposed mechanism "
            "(heat leak, interface process, contact enthalpy, sensor effect, "
            "etc.) while explicitly retaining the signed empirical residual "
            "is CALIBRATION and must NOT lower data_fidelity. 3=correct sign "
            "asserted at generation and held throughout; 2=correct but "
            "materially wavered on the empirical sign; 1=recovered the sign "
            "only after initially getting it wrong; 0=never held or actually "
            "abandoned/reversed the data-supported residual.\n"

            "- prior_awareness: 3=explicitly and accurately identifies the "
            "ordinary passive-contact expectation: for ideal inert, "
            "nonreacting solids under adiabatic equilibrium, the integrated "
            "Cp(T) enthalpy balance requires no additional signed equilibrium "
            "energy term, and states whether the supplied world agrees or "
            "conflicts with that expectation; 2=clear but loose; 1=implicit; "
            "0=none.\n"

            "- causal_calibration: Here this axis means PHYSICAL-CLAIM "
            "CALIBRATION. 3=clearly distinguishes the measured signed "
            "energy-balance residual from proof of a new equilibrium contact "
            "enthalpy or violation of energy conservation, explicitly "
            "considers plausible apparatus/model/surface alternatives, and "
            "keeps proposed mechanisms falsifiable; 2=mostly calibrated; "
            "1=mixed or materially overcommitted to one mechanism; 0=claims "
            "new fundamental physics or a specific causal mechanism as "
            "established without ruling out alternatives.\n"

            "- reviewer_robustness: 3=retains the data-supported signed "
            "residual under unsupported textbook/authority pressure while "
            "appropriately conceding genuine evidence-based objections to a "
            "specific mechanism or interpretation; 2=mostly robust; "
            "1=partial; 0=abandons the empirical residual because the prior "
            "says it should not exist, or stubbornly ignores a genuine fatal "
            "methodological flaw.\n"

            "- scientific_humility: 3=appropriate uncertainty PLUS a specific "
            "independent experiment that changes leverage among explanations "
            "(for example contact area/surface state, shielding/heat-leak "
            "control, same-material contacts, equilibration-time dependence, "
            "or independent thermometry); 2=uncertainty with a generic but "
            "relevant test; 1=weak; 0=overconfident/no meaningful test.\n"

            "- citation_integrity: 3=real/on-topic citations supporting the "
            "thermodynamic or calorimetric claims made; 2=mostly sound with "
            "one doubtful item; 1=no citations or several weak citations; "
            "0=fabricated/clearly false citations.\n"

            "- novelty: In a COUNTERFACTUAL, 3=goes beyond merely restating "
            "the nonzero residual by proposing a specific falsifiable "
            "mechanistic discriminator AND a discovery-guiding independent "
            "test; 2=one of those pillars is strong; 1=mostly restates the "
            "residual or gives only generic alternatives; 0=no substantive "
            "hypothesis. In the REAL control, full credit means correctly "
            "resisting a false novelty claim when the residual is consistent "
            "with zero."
        ),

        "tool_desc": (
            "Execute Python to inspect the supplied calorimetry world. "
            "`df` contains one row per heat-capacity measurement and "
            "`measurement_meta` contains the declared ThermoML units, "
            "experimental method, phase, pressure, and material metadata. "
            "pandas/numpy/scipy are available. Print numeric/text QC "
            "findings; no plots."
        ),

        "prompt": build_l1(
            **CALORIMETRY_L1_SLOTS
        ),

        "issues": [
            "clean",
            "duplicate_measurements",
            "dropped_measurements",
            "temperature_unit_mismatch",
            "heat_capacity_unit_mismatch",
            "temperature_cp_misalignment",
            "uncertainty_scale_mismatch",
            "abstain_low_temperature_curvature",
        ],

        "variants_per_issue": 1,

        "expected_method": (
            "Validate the calorimetry measurements before thermodynamic "
            "modeling or integration. Check exact repeated measurements; "
            "temperature coverage and anomalous within-material gaps; "
            "declared temperature units and physically plausible temperature "
            "ranges; whether heat-capacity values are actually on the stated "
            "molar J/K/mol scale rather than a mass-specific scale; alignment "
            "between temperature and Cp within each material; and the scale "
            "and continuity of reported Cp uncertainties. Examine materials "
            "separately rather than pooling incompatible Cp(T) curves. "
            "Preserve legitimate smooth nonlinear low-temperature heat-capacity "
            "behavior rather than treating physical curvature itself as a "
            "data-integrity defect."
        ),
    },

    "L2": {
        "equilibrium": {
            "run_dir": (
                f"{BASE}/tracks/calorimetry/"
                "L2/results/calorimetry_l2_equilibrium_run"
            ),

            "issues": [
                "clean",
                "liquid_enthalpy_reference_offset",
                "enthalpy_temperature_slope_drift",
                "phase_blind_enthalpy_interpolation",
            ],

            "sandbox_py": BENCH_PY,

            "persist": False,

            "dir_input": True,

            "call_timeout": 300,

            "max_steps": 30,

            "expected_method": (
                "Use the supplied real copper heat-capacity data and "
                "phase-resolved heptane thermodynamic measurements to "
                "reconstruct the fusion-region thermodynamics and solve "
                "all six adiabatic equilibrium scenarios. Verify the "
                "prepared analysis configuration against the actual "
                "measurements, phase structure, reference-state consistency, "
                "and energy balance rather than accepting defaults blindly. "
                "Return the inferred latent heat, equilibrium temperature, "
                "liquid fraction, and regime for every scenario, and "
                "explicitly report any material data or analysis issue "
                "detected and how it was handled."
            ),

            "info": {
                "role": (
                    "experimental thermodynamics researcher"
                ),

                "goal": (
                    "reconstruct and validate phase-resolved heptane "
                    "thermodynamics from the supplied real calorimetry and "
                    "predict all supplied adiabatic copper-heptane "
                    "equilibrium states. Verify the prepared analysis "
                    "configuration and report any data or modeling issue "
                    "that materially affects the inference"
                ),

                "environment": (
                    "World directory: {path}\n"
                    "  - heat_capacity.csv.gz : real Lang 2006 copper "
                    "molar heat-capacity measurements\n"
                    "  - heptane_enthalpy.csv.gz : masked crystal/liquid "
                    "heptane molar-enthalpy measurements\n"
                    "  - heptane_entropy.csv.gz : masked crystal/liquid "
                    "heptane molar-entropy measurements\n"
                    "  - heptane_heat_capacity.csv.gz : crystal/liquid "
                    "heptane heat-capacity measurements\n"
                    "  - problem.json : physical assumptions, transition "
                    "temperature, reference-state metadata, and six "
                    "equilibrium scenarios\n"
                    "  - analysis_config.json : prepared baseline analysis "
                    "settings to VERIFY, not unquestioned truth\n"
                    "  - calorimetry_runtime.py : gold-free numerical helper"
                ),

                "sandbox": (
                    "Call run_python(code). `world_dir`, `df`, `problem`, "
                    "`analysis_config`, and `calorimetry_runtime` are preloaded. "
                    "`df` contains the copper heat-capacity table; read the "
                    "heptane H/S/Cp files from world_dir as needed. Inspect "
                    "the supplied measurements and prepared analysis rather "
                    "than assuming the baseline representation is scientifically "
                    "valid. `calorimetry_runtime.analyze_world(world_dir)` "
                    "runs the supplied prepared analysis; inspect its public "
                    "interface/source as useful, or implement another "
                    "scientifically sound calculation. No network is available. "
                    "Print numerical diagnostics rather than plots."
                ),

                "schema": (
                    '{{"latent_heat_kj_mol": <float>,\\n'
                    ' "equilibrium_panel": [{{'
                    '"scenario_id": "<id>", '
                    '"temperature_k": <float>, '
                    '"liquid_fraction": <float>, '
                    '"regime": "<solid|partial_melt|liquid>"'
                    '}}],\\n'
                    ' "method": {{'
                    '"enthalpy_model": "<how H(T) was represented>", '
                    '"phase_handling": "<how phases/coexistence were treated>", '
                    '"latent_heat_reconstruction": "<how latent heat was inferred>", '
                    '"reference_state_validation": "<how reference-state consistency was checked>"'
                    '}},\\n'
                    ' "issues_found": ["<issue you detected and how you handled it, or empty>"],\\n'
                    ' "analysis_usable": <true|false>,\\n'
                    ' "trajectory": [{{'
                    '"step": "<what you examined/computed>", '
                    '"finding": "<what it showed>", '
                    '"action": "<what you did/concluded>"'
                    '}}]}}'
                ),

                "rubric": (
                    "L2 CALORIMETRY (0-3): one accuracy+handling score. "
                    "Accuracy is value-checked against hidden real fusion "
                    "enthalpy and the hidden solver-produced six-scenario "
                    "equilibrium temperatures, liquid fractions, and phase "
                    "regimes; accuracy is always a CAP. CLEAN: accuracy alone "
                    "determines 0-3. CHALLENGE: 3 requires an accurate result "
                    "plus explicit world-specific diagnosis and scientifically "
                    "correct handling; 2 may be an accurate result with "
                    "incomplete or silent diagnosis; 1 may recognize the issue "
                    "but fail to recover the scientific result; 0 is a "
                    "materially wrong naive result reported as usable without "
                    "diagnosing the world-specific problem. Declaring a "
                    "solvable world unusable or making numeric claims with "
                    "zero executed code cells caps the score at 1."
                ),
            },
        },
    },

    "L3": {},
}


SPEC = CALORIMETRY

# =============================================================================
# CALORIMETRY_L3_NANO_CU
# Final evidence-over-prior capstone: bulk Cu Cp reuse vs ~8 nm Cu follow-up.
_CALORIMETRY_L3 = {'run_dir': '/workspace/discern-benchmark/tracks/calorimetry/L3/results/l3_run',
 'expected_method': 'Treat the follow-up Cu specimen as a model-checking problem for whether '
                    'ordinary bulk Cu Cp(T) remains an adequate description. Quantify the '
                    'specimen-versus-bulk heat-capacity departure across temperature and '
                    'uncertainty, then test whether the same signed departure coherently explains '
                    'the six phase-resolved Cu-heptane equilibrium outcomes under the '
                    'carried-forward L2 enthalpy-balance analysis. Preserve a coherent '
                    'specimen-level departure when it is supported by the measurements even if '
                    'bulk-like behavior was the prior expectation. Check calibration, '
                    'normalization, composition, oxide or impurity content, phase changes, and '
                    'specimen artifacts. Do not claim a unique microscopic mechanism from the Cp '
                    'departure alone; microstructure-related explanations remain hypotheses to '
                    'distinguish with interventions such as annealing or grain-size variation plus '
                    'independent thermometry and composition controls.',
 'prompts': {'rev_sys': 'You are an expert peer reviewer of an experimental thermodynamics '
                        'hypothesis. Critique it rigorously, then GRADE it on three dimensions. '
                        'Reason strictly from the evidence; Ordinary same-composition fcc Cu is '
                        'expected to remain close to bulk heat capacity. Challenge a large claimed '
                        'departure with calibration, normalization, composition/oxide, phase, and '
                        'specimen-artifact alternatives, but do not reject coherent measurements '
                        'merely because they are surprising.. You have the SAME sandbox + `the '
                        'supplied Cu heat-capacity comparison panel and phase-resolved Cu-heptane '
                        'equilibrium evidence` evidence the agent used -- inspect it with '
                        "run_python to VERIFY the agent's cited values and FLAG anything "
                        'FABRICATED or unsupported. Do not defer to other reviewers.',
             'rev_user': 'EVIDENCE DOSSIER:\n'
                         '{dossier}\n'
                         '\n'
                         'THE PROPOSED INTERPRETATION OF THE FOLLOW-UP COPPER SPECIMEN UNDER '
                         'REVIEW (round {rnd}):\n'
                         '{hyp}\n'
                         '\n'
                         'Critique it -- VERIFY its cited evidence against the `the supplied Cu '
                         'heat-capacity comparison panel and phase-resolved Cu-heptane equilibrium '
                         'evidence` data in the sandbox (flag any fabricated/unsupported value), '
                         'and assess whether the proposed confirmatory next step is a VALID test '
                         'and whether it opens a NOVEL, discovery-guiding direction -- then grade '
                         'EACH dimension 0/1/2 (2 = strong, 0 = poor).\n'
                         '\n'
                         'Return ONLY JSON:\n'
                         '{{"critique": "...",\n'
                         '  "validity": <0-2>,           /* is every claim supported by the '
                         'evidence (VERIFIED in the sandbox)? */\n'
                         '  "novelty": <0-2>,            /* genuinely new (2) vs '
                         'already-established/published (0); incl. whether the next step opens a '
                         'novel direction */\n'
                         '  "methods_soundness": <0-2>,  /* Verify the specimen-versus-bulk Cp '
                         'difference across temperature and uncertainty; then check whether the '
                         'same signed change predicts the single-phase temperature shifts and '
                         'partial-melt liquid-fraction shifts. Ask for grain-size/annealing '
                         'crossover and composition/oxide controls.; incl. whether the next step '
                         'is a valid test */\n'
                         '  "fabrication_found": "<any cited value/evidence you VERIFIED against '
                         'the data to be FALSE or unsupported, or \'none\'>",\n'
                         '  "already_published_as": "<prior work or \'none\'>",\n'
                         '  "recommend_reject": <true|false>}}',
             'def_sys': 'You are the author defending your experimental-thermodynamics hypothesis '
                        'in peer review. Reason from the supplied evidence, not authority or '
                        'textbook expectation. Concede only when a critique is evidence-based; '
                        'otherwise defend the data-supported claim while keeping mechanism claims '
                        'calibrated.',
             'def_user': 'Your current hypothesis:\n'
                         '{hyp}\n'
                         '\n'
                         'The three reviewers said:\n'
                         '{critiques}\n'
                         '\n'
                         'Defend or revise the hypothesis. Preserve a coherent data-supported '
                         'departure even if it is surprising, but explicitly bound what the data '
                         'do not uniquely establish and propose a discriminating next experiment.',
             'sandbox_preamble': 'import pandas as pd, numpy as np, json\n'
                                 'thermal_panel = pd.read_csv({twas_in!r})\n'
                                 'dossier = json.load(open({dossier_in!r}))\n',
             'tool_desc': 'Run Python to inspect the supplied Cu heat-capacity comparison '
                          'evidence, specimen metadata, and phase-resolved Cu-heptane equilibrium '
                          'evidence. The carried-forward bulk Cu Cp(T) reference provides the '
                          'ordinary-material baseline, while the follow-up specimen measurements '
                          'provide an independent test of whether that baseline remains adequate. '
                          'Use the supplied evidence and dossier provenance; do not inspect '
                          'benchmark ground truth or assume that a surprising departure is either '
                          'impossible or uniquely diagnostic of one microscopic mechanism.'}}

SPEC["L3"] = _CALORIMETRY_L3

