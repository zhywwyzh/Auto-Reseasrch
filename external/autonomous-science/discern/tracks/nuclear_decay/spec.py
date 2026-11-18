"""
Nuclear-decay discovery track.

Long-term NaI(Tl) Co-60 radiation measurements -> decay-law inference.
"""

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

sys.path.insert(
    0,
    str(ROOT),
)

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


NUCLEAR_L1_SLOTS = dict(
    role=(
        "an experimental nuclear-physics researcher"
    ),

    subject=(
        "real long-term NaI(Tl) gamma-spectrum measurements "
        "of a Co-60 radioactive source"
    ),

    object=(
        "the acquisition timestamps, live/real/dead time metadata, "
        "reported integral counts, per-acquisition spectral calibration, "
        "and 2048-channel gamma spectra"
    ),

    downstream=(
        "radioactive decay-rate, decay-constant, half-life, and "
        "long-term spectral-stability inference"
    ),

    input_line=(
        "Dataset path: {path}   "
        "(directory containing a Co-60 radiation measurement table "
        "and measurement metadata)"
    ),

    sandbox=(
        "No analysis-ready dataframe is preloaded. Inspect the files in "
        "`world_dir` yourself using pandas, numpy, scipy, json, and ordinary "
        "filesystem operations. `radiation.csv.gz` contains the acquisition "
        "metadata and 2048-channel spectra; `measurement_meta.json` documents "
        "the canonicalized fields and measurement conventions."
    ),
)


NUCLEAR_DECAY = {
    "name": "nuclear_decay",

    "trait": (
        "long-term experimental radioactive-decay measurements"
    ),

    "reps": 1,

    "models": MODELS,

    "agent_system": (
        "You are a careful computational physicist. "
        "Do the task with the sandbox and return ONLY "
        "the requested JSON."
    ),

    "clean_substrate": (
        f"{BASE}/tracks/nuclear_decay/raw/"
        "Multi year radiation measurement data/"
        "NaI_Co-60_1Dec2014to1June2016.csv"
    ),

    "docs": [],

    "docs_dir": (
        f"{BASE}/tracks/nuclear_decay/raw/"
        "Multi year radiation measurement data"
    ),

    "efficiency": EFFICIENCY,

    "L1": {
        "run_dir": (
            f"{BASE}/tracks/nuclear_decay/"
            "L1/results/nuclear_decay_l1_run"
        ),

        "input_kind": "nuclear_decay",

        "sandbox_py": BENCH_PY,

        "tool_desc": (
            "Execute Python to inspect the supplied radiation-data world "
            "directory. `world_dir` is its absolute path. pandas/numpy/scipy "
            "are available. Inspect `radiation.csv.gz` and "
            "`measurement_meta.json`; print numeric/textual QC findings, "
            "not plots."
        ),

        "prompt": build_l1(
            **NUCLEAR_L1_SLOTS
        ),

        "issues": [
            "clean",
            "duplicate_acquisitions",
            "dropped_acquisitions",
            "timestamp_order_corruption",
            "livetime_unit_mismatch",
            "integral_spectrum_mismatch",
            "spectral_channel_shift",
            "abstain_calibration_change",
        ],

        "variants_per_issue": 1,

        "expected_method": (
            "Validate the long-term Co-60 NaI measurement table before "
            "decay-law inference: check exact duplicate acquisitions; missing "
            "acquisitions and timestamp/acquisition-id gaps; chronological row "
            "ordering; acquisition live-time units and consistency with "
            "real/dead time; 2048-channel spectral structure; agreement between "
            "reported integral counts and summed channel counts up to source "
            "rounding; and temporal stability/alignment of spectral features "
            "relative to the row-specific calibration slope and offset. Do not "
            "infer corrupted radiation measurements solely because the recorded "
            "per-acquisition spectral calibration coefficients change; use the "
            "supplied calibration and require independent evidence before "
            "declaring a real calibration update invalid."
        ),
    },

    "L2": {
        "decay_fit": {
            "run_dir": (
                f"{BASE}/tracks/nuclear_decay/"
                "L2/results/nuclear_decay_l2_decay_fit_run"
            ),

            "sandbox_py":
                BENCH_PY,

            "call_timeout":
                180,

            "issues": [
                "clean",
                "near_field_efficiency_model_default",
                "mn54_cross_source_contamination",
                "dead_time_correction_default",
            ],

            "expected_method": (
                "Estimate the Co-60 radioactive decay constant lambda and "
                "physical half-life from the supplied long-term counting "
                "measurements. Validate the prepared analysis against the "
                "primary Co-60 table and auxiliary records, distinguish "
                "detector or measurement effects from nuclear decay, and "
                "report any material data-integration or prepared-analysis "
                "issue that changes the inference."
            ),

            "info": {
                "role": (
                    "experimental nuclear-physics researcher analyzing "
                    "long-term gamma-counting measurements"
                ),

                "goal": (
                    "estimate the Co-60 decay constant lambda and physical "
                    "half-life while validating the prepared analysis and "
                    "auxiliary measurement records."
                ),

                "environment": (
                    "World directory: {path}\\n"
                    "It contains:\\n"
                    "  - decay_measurements.csv.gz : daily Co-60 counts, "
                    "live/real times, rate and uncertainty\\n"
                    "  - environment_measurements.csv.gz : synchronous "
                    "temperature, humidity and pressure\\n"
                    "  - mn54_reference.csv.gz : independent Mn-54 "
                    "reference-source measurements\\n"
                    "  - prepared_decay_series.csv.gz : series consumed "
                    "by the prepared baseline\\n"
                    "  - problem.json\\n"
                    "  - analysis_config.json\\n"
                    "  - decay_runtime.py"
                ),

                "sandbox": (
                    "Call run_python(code). The sandbox PRELOADS `df`, "
                    "`problem`, `analysis_config`, and `decay_runtime`. "
                    "`df` is the primary Co-60 measurement table. You may "
                    "read the auxiliary CSV files with pandas and inspect "
                    "the runtime source/interface as needed. No network is "
                    "available. Print numeric diagnostics rather than plots."
                ),

                "schema": (
                    '{{"lambda_per_day": <float>, '
                    '"half_life_years": <float>,\\n'
                    ' "method": {{"model": "<model used>", '
                    '"weighting": "<weighting used>", '
                    '"timescale": "<timescale>", '
                    '"handling": "<corrective analysis>"}},\\n'
                    ' "fit_diagnostics": {{"rmse_cps": <float or null>, '
                    '"weighted_rmse": <float or null>}},\\n'
                    ' "issues_found": ["<material issue or empty>"],\\n'
                    ' "analysis_usable": <true|false>,\\n'
                    ' "trajectory": [{{"step": "<step>", '
                    '"finding": "<finding>", '
                    '"action": "<action>"}}]}}'
                ),

                "rubric": (
                    "L2 NUCLEAR DECAY decay_fit (0-3): strict numerical "
                    "accuracy is |delta half-life|<=0.05 years AND relative "
                    "|delta lambda|<=1%; moderate is <=0.20 years AND <=3%; "
                    "rough is <=0.50 years AND <=8%. CLEAN: 3=strict, "
                    "2=moderate, 1=rough, 0=wrong/no valid estimate. "
                    "CHALLENGES: 3=strict result plus explicit correct "
                    "diagnosis in issues_found and appropriate corrective "
                    "analysis; 2=accurate but silent/incomplete handling; "
                    "1=issue recognized but poor recovery; 0=trusts the "
                    "misleading data/prepared analysis or gives a wrong "
                    "result without diagnosis. Zero executed code cells "
                    "caps score at 1. analysis_usable=false caps score at 1."
                ),
            },
        },
    },

    "L3": {},
}


SPEC = NUCLEAR_DECAY

# =============================================================================
# NUCLEAR_L3_STELLAR_CO60_BEGIN
# Frozen stellar-state Co-60 evidence-over-prior capstone.
#
# IMPORTANT:
#   Generation intentionally uses run_l3.py's UNIVERSAL neutral GEN prompt.
#   The scientific task is inferred from the self-describing dossier.
#
# Gate-0:
#   co60-terrestrial-half-life
#
# Scientific freeze:
#   tracks/nuclear_decay/L3/freeze/nuclear_l3_science_freeze.json
#
# World source of truth:
#   tracks/nuclear_decay/L3/dossier.py
#
# Built manifest:
#   tracks/nuclear_decay/L3/results/l3_run/manifest.json
# =============================================================================

_NUCLEAR_L3_EXPECTED_METHOD = (
    "Estimate the effective Co-60 decay constant directly from the supplied "
    "274-day counting/activity evidence using a free normalization and "
    "heteroskedastic or count-statistical uncertainty treatment. Convert the "
    "fitted decay constant to half-life and compare it with the ordinary "
    "terrestrial Co-60 reference near 5.27 years. Inspect residuals and the "
    "supplied environmental and Mn-54 reference/control channels for evidence "
    "that a common time-dependent detector response explains the apparent "
    "slope. Treat the declared physical source state as part of the experiment: "
    "when coherent evidence supports a non-terrestrial effective decay rate, "
    "do not discard that result merely because the terrestrial half-life is "
    "the memorized prior. Distinguish the empirical effective-rate result from "
    "proof of a unique microscopic mechanism. Explicitly acknowledge that an "
    "arbitrary exponential detector-efficiency drift is mathematically "
    "degenerate with a changed decay constant unless independently constrained. "
    "Propose a discriminating follow-up varying source-state conditions and/or "
    "independently calibrating detector response."
)


_NUCLEAR_L3 = {
    "run_dir": (
        f"{BASE}/tracks/nuclear_decay/"
        "L3/results/l3_run"
    ),

    "expected_method":
        _NUCLEAR_L3_EXPECTED_METHOD,

    # DO NOT override gen_sys/gen_user.
    # run_l3.py's universal neutral generation prompt is authoritative.
    "prompts": {

        "rev_sys": (
            "You are an expert peer reviewer of a scientific hypothesis "
            "involving long-term Co-60 counting evidence. Critique the "
            "interpretation rigorously. The ordinary terrestrial Co-60 "
            "reference half-life is approximately 5.27 years, so examine "
            "detector response, background, normalization, source-state "
            "assumptions and analysis systematics when a departure is claimed. "
            "Do not reject quantitatively coherent supplied evidence merely "
            "because it differs from the ordinary terrestrial reference. "
            "Use the same sealed evidence available to the agent to verify "
            "quantitative claims, and keep microscopic mechanism claims bounded."
        ),

        "rev_user": (
            "EVIDENCE DOSSIER:\n"
            "{dossier}\n\n"
            "HYPOTHESIS UNDER REVIEW (round {rnd}):\n"
            "{hyp}\n\n"
            "Critique it. VERIFY quantitative claims against the supplied "
            "evidence in the sandbox. Assess whether the effective decay-rate "
            "inference is supported, whether alternative instrumental or "
            "analysis explanations are handled appropriately, whether mechanism "
            "claims are calibrated, and whether the proposed next experiment "
            "genuinely discriminates among live explanations. Grade EACH "
            "dimension 0/1/2.\n\n"
            "Return ONLY JSON:\n"
            "{{\"critique\": \"...\",\n"
            "  \"validity\": <0-2>,\n"
            "  \"novelty\": <0-2>,\n"
            "  \"methods_soundness\": <0-2>,\n"
            "  \"fabrication_found\": \"<false/unsupported evidence or none>\",\n"
            "  \"already_published_as\": \"<prior work or none>\",\n"
            "  \"recommend_reject\": <true|false>}}"
        ),

        "def_sys": (
            "You are the author defending a scientific hypothesis in peer "
            "review. Reason from the supplied evidence rather than authority. "
            "Concede genuine methodological problems; otherwise retain an "
            "empirically supported result while keeping causal and microscopic "
            "claims appropriately calibrated."
        ),

        "def_user": (
            "Your current hypothesis:\n"
            "{hyp}\n\n"
            "The three reviewers said:\n"
            "{critiques}\n\n"
            "Defend or revise the hypothesis. Preserve a data-supported "
            "effective decay-rate result if it survives the critiques, but "
            "explicitly bound what the evidence does not uniquely establish "
            "and propose a discriminating independent test."
        ),

        # Explicit shared-harness preload.
        #
        # `twas` is the historical generic variable name required by the
        # universal runner. `panel` is a neutral alias for this physics track.
        "sandbox_preamble": (
            "import pandas as pd, numpy as np, json\n"
            "twas = pd.read_csv({twas_in!r})\n"
            "panel = twas\n"
            "dossier = json.load(open({dossier_in!r}))\n"
        ),

        "tool_desc": (
            "Run Python to inspect the supplied evidence. `panel` and `twas` "
            "refer to the same preloaded Co-60 evidence dataframe; `dossier` "
            "is the preloaded evidence dossier. Use only the supplied sealed "
            "files and ordinary numerical/statistical analysis. Print numeric "
            "or textual diagnostics; plots are not rendered."
        ),
    },
}


SPEC["L3"] = _NUCLEAR_L3

# NUCLEAR_L3_STELLAR_CO60_END
# =============================================================================

