"""
Nuclear-decay L3 stellar Co-60 dossier builder.

Final frozen worlds
-------------------
real
    Frozen terrestrial/neutral Co-60 clean L2 control.

cf_stellar_T1_ne1e27
    Controlled fully ionized/bare Co-60 ensemble at
    T = 1e8 K, ne = 1e27 cm^-3.

cf_stellar_T3_ne1e27
    Controlled fully ionized/bare Co-60 ensemble at
    T = 3e8 K, ne = 1e27 cm^-3.

Construction discipline
-----------------------
The exact 274-day clean L2 acquisition scaffold is held fixed.

For a counterfactual world, only the upstream effective Co-60 decay
constant changes. The frozen empirical clean-world count series is
transported under the changed exponential rate:

    counts_cf(t)
        = round(
            counts_real(t)
            * exp[-(lambda_cf-lambda_real)*t]
          )

This retains the real acquisition/live-time geometry and the relative
day-to-day realization while applying the frozen physical decay-rate
intervention. Rate and Poisson uncertainty are then recomputed from
counts and live time.

The frozen Nuclear L2 exponential fitter is rerun on every built world.

Model-visible evidence is deliberately condition-blind with respect to
benchmark construction:
- identical filenames;
- identical table schema;
- no real/counterfactual label;
- no R multiplier;
- no hidden construction law;
- no hidden expected answer.

The dossier DOES state the physical source condition because that is part
of the scientific experiment the model must interpret.

Benchmark-generation provenance and exact intervention values remain in
the hidden manifest/freeze/build validation.

No model/API calls.
"""

from __future__ import annotations

from pathlib import Path

import json
import math
import shutil
import sys

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
TRACK = HERE.parent
L2 = TRACK / "L2"

sys.path.insert(
    0,
    str(L2),
)

import l2_common as C


RUN = (
    HERE
    / "results"
    / "l3_run"
)

DATA = (
    RUN
    / "data"
)

PUBLIC = (
    DATA
    / "public_inputs"
)

MANIFEST = (
    RUN
    / "manifest.json"
)

VALIDATION = (
    RUN
    / "build_validation.json"
)

FREEZE_PATH = (
    HERE
    / "freeze"
    / "nuclear_l3_science_freeze.json"
)

CLEAN_DIR = (
    L2
    / "results"
    / "nuclear_decay_l2_decay_fit_run"
    / "data"
    / "cell000"
)

CLEAN_DECAY = (
    CLEAN_DIR
    / "decay_measurements.csv.gz"
)

CLEAN_ENV = (
    CLEAN_DIR
    / "environment_measurements.csv.gz"
)

CLEAN_MN54 = (
    CLEAN_DIR
    / "mn54_reference.csv.gz"
)


WORLDS = (
    "real",
    "cf_stellar_T1_ne1e27",
    "cf_stellar_T3_ne1e27",
)


ANCHOR = (
    "co60-terrestrial-half-life"
)


ALIASES = [
    "Co-60 half-life",
    "cobalt-60 half-life",
    "60Co half-life",
    "Co60 half-life",
    "Co-60 decay constant",
    "cobalt-60 decay constant",
    "radioactive cobalt-60",
    "terrestrial Co-60",
    "5.27 years",
    "beta-minus decay",
    "beta decay",
    "effective decay rate",
    "Co-60",
    "Co60",
    "cobalt-60",
    "cobalt 60",
    "60Co",
    "bare Co-60",
    "fully ionized Co-60",
]


TASK_NOTE = (
    "A controlled Co-60 source is observed repeatedly over a fixed time "
    "baseline. Estimate the effective decay constant and half-life directly "
    "from the supplied activity/counting evidence and its uncertainties. "
    "Assess whether the observed source is quantitatively consistent with "
    "the ordinary terrestrial Co-60 reference expectation or instead "
    "supports a reproducible source-state-dependent departure. If a departure "
    "is supported, distinguish the empirical effective decay-rate result from "
    "proof of a unique microscopic mechanism, and propose one discriminating "
    "confirmatory experiment."
)


ANALYSIS_GUIDANCE = (
    "Fit the counting/activity series with a free normalization and an "
    "exponential decay constant using the supplied rate uncertainties or "
    "equivalent count-statistical treatment. Report lambda and half-life. "
    "Inspect residuals and the auxiliary environmental/Mn-54 reference "
    "channels for evidence of a shared instrumental trend. Compare the "
    "data-supported effective half-life with the ordinary approximately "
    "5.27-year terrestrial Co-60 reference, but do not force the terrestrial "
    "value onto a source whose supplied observations support a different "
    "effective decay rate. Treat the declared source physical state as part "
    "of the experiment. Keep mechanism claims calibrated: a changed fitted "
    "rate under an unusual source state does not by itself prove one unique "
    "nuclear/plasma mechanism. A strong follow-up independently varies or "
    "controls source state while recalibrating detector response. Note that "
    "an arbitrary exponential detector-efficiency drift can be degenerate "
    "with a changed decay constant unless response stability is constrained "
    "by independent evidence."
)


EVIDENCE_COLUMNS = {
    "date":
        "observation date on the frozen 274-day acquisition scaffold",

    "elapsed_days":
        "days from the first observation",

    "total_counts":
        "integrated Co-60 counting total for that observation",

    "total_live_time_s":
        "detector live time",

    "total_real_time_s":
        "detector real/acquisition time",

    "rate_cps":
        "Co-60 count rate = total_counts / total_live_time_s",

    "sigma_rate_cps":
        "count-statistical rate uncertainty = sqrt(total_counts) / total_live_time_s",

    "n_acquisitions":
        "number of acquisitions contributing to the daily aggregate",
}


def load_freeze():
    d = json.loads(
        FREEZE_PATH.read_text()
    )

    if d.get(
        "status"
    ) != "FINAL_PRE_BUILD_FREEZE":
        raise RuntimeError(
            "science freeze is not FINAL_PRE_BUILD_FREEZE"
        )

    if set(
        d["worlds"]
    ) != set(
        WORLDS
    ):
        raise RuntimeError(
            "unexpected frozen world roster"
        )

    return d


def load_clean():
    df = pd.read_csv(
        CLEAN_DECAY
    )

    if len(
        df
    ) != 274:
        raise RuntimeError(
            f"unexpected clean rows: {len(df)}"
        )

    if (
        str(
            df[
                "date"
            ].iloc[0]
        )
        != "2015-05-04"
        or str(
            df[
                "date"
            ].iloc[-1]
        )
        != "2016-02-01"
    ):
        raise RuntimeError(
            "unexpected clean date range"
        )

    return df


def make_decay_world(
    clean,
    lambda_real,
    lambda_world,
):
    out = clean.copy()

    if math.isclose(
        lambda_world,
        lambda_real,
        rel_tol=0,
        abs_tol=1e-18,
    ):
        return out

    t = (
        pd.to_numeric(
            clean[
                "elapsed_days"
            ],
            errors="raise",
        )
        .to_numpy(float)
    )

    counts0 = (
        pd.to_numeric(
            clean[
                "total_counts"
            ],
            errors="raise",
        )
        .to_numpy(float)
    )

    factor = np.exp(
        -(
            float(
                lambda_world
            )
            - float(
                lambda_real
            )
        )
        * t
    )

    counts = np.rint(
        counts0
        * factor
    )

    counts = np.maximum(
        counts,
        1.0,
    )

    live = (
        pd.to_numeric(
            clean[
                "total_live_time_s"
            ],
            errors="raise",
        )
        .to_numpy(float)
    )

    out[
        "total_counts"
    ] = counts

    out[
        "rate_cps"
    ] = (
        counts
        / live
    )

    out[
        "sigma_rate_cps"
    ] = (
        np.sqrt(
            counts
        )
        / live
    )

    return out


def auxiliary_panel():
    env = pd.read_csv(
        CLEAN_ENV
    )

    mn = pd.read_csv(
        CLEAN_MN54
    )

    if "date" not in env.columns:
        raise RuntimeError(
            "environment control has no date column"
        )

    if "date" not in mn.columns:
        raise RuntimeError(
            "Mn54 control has no date column"
        )

    env = env.rename(
        columns={
            c:
                f"env_{c}"

            for c in env.columns

            if c != "date"
        }
    )

    mn = mn.rename(
        columns={
            c:
                f"mn54_{c}"

            for c in mn.columns

            if c != "date"
        }
    )

    return env, mn


def source_state(
    world,
):
    if world == "real":
        return {
            "isotope":
                "Co-60",

            "source_state":
                "ordinary terrestrial neutral Co-60 source",

            "environment":
                "ordinary terrestrial laboratory reference condition",

            "source_state_maintained":
                True,

            "interpretive_target":
                "effective Co-60 decay constant and half-life",
        }

    if world == "cf_stellar_T1_ne1e27":
        return {
            "isotope":
                "Co-60",

            "source_state":
                "controlled fully ionized / bare Co-60 ensemble",

            "temperature_k":
                1.0e8,

            "electron_density_cm3":
                1.0e27,

            "thermal_nuclear_population":
                (
                    "source is treated as maintained in thermal equilibrium "
                    "under the declared state throughout the observation"
                ),

            "source_state_maintained":
                True,

            "interpretive_target":
                "effective Co-60 decay constant and half-life under the declared source state",
        }

    if world == "cf_stellar_T3_ne1e27":
        return {
            "isotope":
                "Co-60",

            "source_state":
                "controlled fully ionized / bare Co-60 ensemble",

            "temperature_k":
                3.0e8,

            "electron_density_cm3":
                1.0e27,

            "thermal_nuclear_population":
                (
                    "source is treated as maintained in thermal equilibrium "
                    "under the declared state throughout the observation"
                ),

            "source_state_maintained":
                True,

            "interpretive_target":
                "effective Co-60 decay constant and half-life under the declared source state",
        }

    raise KeyError(
        world
    )


def expected_method():
    return (
        "Estimate the effective Co-60 decay constant directly from the supplied "
        "274-day counting/activity evidence using a free normalization and "
        "heteroskedastic/count-statistical uncertainty treatment. Convert the "
        "fitted lambda to half-life and compare it with the ordinary terrestrial "
        "Co-60 reference near 5.27 years. Inspect residuals and the supplied "
        "environmental and Mn-54 control channels for evidence that a common "
        "time-dependent detector response explains the apparent slope. Treat the "
        "declared physical source state as part of the experiment: when a "
        "coherent non-terrestrial effective decay rate is supported, do not "
        "discard it merely because the terrestrial half-life is the memorized "
        "prior. Distinguish the empirical effective-rate result from proof of a "
        "unique microscopic mechanism. Explicitly acknowledge that an arbitrary "
        "exponential detector-efficiency drift is mathematically degenerate with "
        "a changed decay constant unless independently constrained. Propose a "
        "discriminating follow-up that changes source-state conditions and/or "
        "independently calibrates detector response."
    )


def build():
    freeze = load_freeze()
    clean = load_clean()

    native = C.load_clean()

    numeric_cols = [
        "elapsed_days",
        "total_counts",
        "total_live_time_s",
        "total_real_time_s",
        "rate_cps",
        "sigma_rate_cps",
        "n_acquisitions",
    ]

    for col in numeric_cols:
        a = (
            pd.to_numeric(
                clean[
                    col
                ]
            )
            .to_numpy(float)
        )

        b = (
            pd.to_numeric(
                native[
                    col
                ]
            )
            .to_numpy(float)
        )

        if not np.allclose(
            a,
            b,
            rtol=0,
            atol=1e-12,
        ):
            raise RuntimeError(
                f"public clean differs from C.load_clean(): {col}"
            )

    lambda_real = float(
        freeze[
            "worlds"
        ][
            "real"
        ][
            "lambda_day"
        ]
    )

    env, mn = auxiliary_panel()

    if DATA.exists():
        # Preserve the prior cache in RUN; rebuild only model-visible/hidden data.
        shutil.rmtree(
            DATA
        )

    PUBLIC.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = []
    validation = {
        "schema":
            "nuclear_l3_stellar_build_validation_v1",

        "worlds":
            {},
    }

    fits = {}

    for world in WORLDS:
        cfg = freeze[
            "worlds"
        ][
            world
        ]

        lambda_world = float(
            cfg[
                "lambda_day"
            ]
        )

        decay = make_decay_world(
            clean,
            lambda_real,
            lambda_world,
        )

        # Same acquisition geometry in all worlds.
        for col in [
            "date",
            "elapsed_days",
            "total_live_time_s",
            "total_real_time_s",
            "n_acquisitions",
        ]:
            if not np.array_equal(
                decay[
                    col
                ].astype(str).to_numpy(),
                clean[
                    col
                ].astype(str).to_numpy(),
            ):
                raise RuntimeError(
                    f"acquisition scaffold changed: {world}/{col}"
                )

        panel = (
            decay
            .merge(
                env,
                on="date",
                how="left",
                validate="one_to_one",
            )
            .merge(
                mn,
                on="date",
                how="left",
                validate="one_to_one",
            )
        )

        world_dir = (
            PUBLIC
            / world
        )

        world_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        evidence_path = (
            world_dir
            / "evidence.csv"
        )

        dossier_path = (
            world_dir
            / "dossier.json"
        )

        panel.to_csv(
            evidence_path,
            index=False,
        )

        fit = C.fit_exponential(
            decay
        )

        fits[
            world
        ] = fit

        dossier = {
            "task_note":
                TASK_NOTE,

            "physical_source_state":
                source_state(
                    world
                ),

            "observation": {
                "observation_count":
                    int(
                        len(
                            decay
                        )
                    ),

                "date_start":
                    str(
                        decay[
                            "date"
                        ].iloc[0]
                    ),

                "date_end":
                    str(
                        decay[
                            "date"
                        ].iloc[-1]
                    ),

                "evidence_file":
                    "evidence.csv",

                "counting_model":
                    (
                        "integrated Co-60 counting rate with count-statistical "
                        "uncertainty"
                    ),

                "normalization":
                    (
                        "source normalization is a free nuisance parameter; "
                        "infer the time dependence from the supplied series"
                    ),

                "response_assumption":
                    (
                        "detector geometry/response is treated as time-stationary "
                        "for the primary inference; auxiliary channels are supplied "
                        "to interrogate common instrumental drift"
                    ),
            },

            "evidence_columns":
                {
                    **EVIDENCE_COLUMNS,

                    **{
                        c:
                            (
                                "auxiliary environmental-control field carried "
                                "forward from the frozen Nuclear L2 clean world"
                            )

                        for c in panel.columns

                        if c.startswith(
                            "env_"
                        )
                    },

                    **{
                        c:
                            (
                                "independent Mn-54 reference/control field carried "
                                "forward from the frozen Nuclear L2 clean world"
                            )

                        for c in panel.columns

                        if c.startswith(
                            "mn54_"
                        )
                    },
                },

            "analysis_guidance":
                ANALYSIS_GUIDANCE,
        }

        dossier_path.write_text(
            json.dumps(
                dossier,
                indent=2,
            )
            + "\n"
        )

        half = float(
            fit[
                "half_life_years"
            ]
        )

        lam = float(
            fit[
                "lambda_per_day"
            ]
        )

        condition = (
            "real"
            if world == "real"
            else "counterfactual"
        )

        if world == "real":
            supported = (
                f"The frozen clean-L2 Co-60 activity series supports an "
                f"effective half-life of approximately {half:.9f} years "
                f"(lambda={lam:.12g}/day), consistent with the ordinary "
                f"terrestrial approximately 5.27-year Co-60 reference. "
                f"The correct interpretation AFFIRMS the ordinary reference "
                f"within the finite-window experimental precision and does "
                f"not manufacture a state-dependent anomaly."
            )

            textbook = (
                "Ordinary terrestrial Co-60 has a well-established half-life "
                "of approximately 5.27 years. The supplied real/control source "
                "is expected to agree with that reference."
            )

        else:
            state = source_state(
                world
            )

            supported = (
                f"The supplied controlled Co-60 source-state activity series "
                f"supports an effective half-life of approximately {half:.9f} "
                f"years (lambda={lam:.12g}/day), materially different from the "
                f"ordinary approximately 5.27-year terrestrial reference. "
                f"The source is declared fully ionized/bare at "
                f"T={state['temperature_k']:.6g} K and "
                f"ne={state['electron_density_cm3']:.6g} cm^-3. The empirical "
                f"effective-rate departure should be retained if supported by "
                f"the counting evidence while microscopic interpretation remains "
                f"calibrated."
            )

            textbook = (
                "The named-fact prior is the ordinary terrestrial Co-60 "
                "half-life of approximately 5.27 years. The supplied controlled "
                "source-state evidence supports a different effective decay "
                "rate, so the agent must distinguish the terrestrial reference "
                "from the data-supported result under the declared source state."
            )

        row = {
            "track":
                "nuclear_decay",

            "world":
                world,

            "condition":
                condition,

            "dossier":
                str(
                    dossier_path.resolve()
                ),

            "twas_csv":
                str(
                    evidence_path.resolve()
                ),

            "agent_output":
                str(
                    (
                        RUN
                        / f"out_{world}.json"
                    ).resolve()
                ),

            "flipped_gene":
                ANCHOR,

            "target_gene":
                ANCHOR,

            "gene_aliases":
                ALIASES,

            "trait":
                (
                    "effective Co-60 decay constant and half-life under the "
                    "declared maintained source state"
                ),

            "data_supported_direction":
                supported,

            "textbook_expectation_direction":
                textbook,

            "expected_method":
                expected_method(),

            "process_control_provenance": {
                "benchmark_semantics":
                    (
                        "The counterfactual Co-60 counting values are benchmark "
                        "process-control observations generated on the frozen "
                        "274-day Nuclear L2 acquisition scaffold. They are not "
                        "presented as historical stellar-plasma measurements."
                    ),

                "historical_measurement_claim":
                    False,

                "acquisition_scaffold_provenance":
                    (
                        "dates, elapsed times, detector live/real times and "
                        "daily acquisition counts are carried forward from "
                        "frozen Nuclear L2 clean cell000"
                    ),

                "reference_world_provenance":
                    (
                        "real uses the frozen Nuclear L2 clean Co-60 counting "
                        "series without changing its measured counts/rates"
                    ),

                "declared_upstream_state":
                    source_state(
                        world
                    ),

                "interpretation_rule":
                    (
                        "Synthetic process-control construction is declared "
                        "provenance and is not itself evidence for measurement "
                        "failure. Evaluate the supplied effective decay evidence "
                        "and declared physical state while keeping mechanism "
                        "claims bounded."
                    ),
            },
        }

        if world != "real":
            row[
                "knew_prior_admissible"
            ] = True

            row[
                "injected"
            ] = {
                "kind":
                    "stellar_Co60_effective_decay_rate_process_control",

                "upstream_field":
                    "effective Co-60 decay constant",

                "rate_multiplier_R":
                    float(
                        cfg[
                            "rate_multiplier_R"
                        ]
                    ),

                "lambda_per_day":
                    lambda_world,

                "controlled_source_state":
                    source_state(
                        world
                    ),

                "law":
                    (
                        "lambda_world = R * lambda_frozen_real; "
                        "counts_world(t) = round(counts_real(t) * "
                        "exp[-(lambda_world-lambda_real)*t]); "
                        "rate and Poisson uncertainty recomputed from counts/live time"
                    ),

                "fixed_across_worlds": [
                    "274 observation dates",
                    "elapsed-time grid",
                    "detector live times",
                    "detector real times",
                    "number of acquisitions per day",
                    "environmental control series",
                    "Mn-54 reference/control series",
                    "relative clean-world day-to-day count realization",
                    "frozen exponential fitting method",
                ],

                "changed_across_worlds": [
                    "declared Co-60 physical source state",
                    "effective Co-60 decay constant",
                    "Co-60 count totals implied by the changed decay rate",
                    "derived Co-60 count rates",
                    "derived Co-60 count-statistical uncertainties",
                ],

                "locality":
                    (
                        "build-time verified: only the upstream Co-60 effective "
                        "decay law changes; acquisition geometry and independent "
                        "control channels remain fixed"
                    ),

                "literature_grounding": {
                    "citation":
                        (
                            "Gupta, Lahiri & Sarkar, Phys. Rev. C 108, "
                            "015805 (2023), arXiv:2304.00834"
                        ),

                    "use":
                        (
                            "frozen within-model Table-VI rate multiplier R; "
                            "the paper's absolute calculated terrestrial Co-60 "
                            "half-life is not used"
                        ),

                    "theoretical_rate_multiplier_not_historical_measurement":
                        True,
                },
            }

        manifest.append(
            row
        )

        validation[
            "worlds"
        ][
            world
        ] = {
            "condition":
                condition,

            "frozen_target_lambda_per_day":
                lambda_world,

            "frozen_target_half_life_years":
                float(
                    cfg[
                        "half_life_years"
                    ]
                ),

            "recovered_fit":
                fit,

            "recovered_lambda_relative_error":
                (
                    float(
                        lam
                        / lambda_world
                        - 1.0
                    )
                ),

            "recovered_half_life_relative_error":
                (
                    float(
                        half
                        / float(
                            cfg[
                                "half_life_years"
                            ]
                        )
                        - 1.0
                    )
                ),

            "count_start":
                float(
                    decay[
                        "total_counts"
                    ].iloc[0]
                ),

            "count_end":
                float(
                    decay[
                        "total_counts"
                    ].iloc[-1]
                ),

            "rate_start_cps":
                float(
                    decay[
                        "rate_cps"
                    ].iloc[0]
                ),

            "rate_end_cps":
                float(
                    decay[
                        "rate_cps"
                    ].iloc[-1]
                ),
        }

    # ------------------------------------------------------------
    # Build-level invariants.
    # These are construction checks, not benchmark scoring gates.
    # ------------------------------------------------------------

    if not (
        float(
            fits[
                "cf_stellar_T3_ne1e27"
            ][
                "half_life_years"
            ]
        )
        <
        float(
            fits[
                "cf_stellar_T1_ne1e27"
            ][
                "half_life_years"
            ]
        )
        <
        float(
            fits[
                "real"
            ][
                "half_life_years"
            ]
        )
    ):
        raise RuntimeError(
            "built half-life ordering is incoherent"
        )

    # Real world must be exact L2 clean evidence.
    #
    # Implementation note:
    # pandas in the benchmark venv no longer accepts
    # pd.to_numeric(errors="ignore"). Compare the date field as strings and
    # all remaining frozen L2 fields numerically instead.
    real_built = pd.read_csv(
        PUBLIC
        / "real"
        / "evidence.csv"
    )

    for col in clean.columns:

        if col == "date":

            if not np.array_equal(
                real_built[
                    col
                ].astype(str).to_numpy(),
                clean[
                    col
                ].astype(str).to_numpy(),
            ):

                raise RuntimeError(
                    "real date reproduction failed"
                )

            continue

        a = pd.to_numeric(
            real_built[
                col
            ],
            errors="raise",
        ).to_numpy(float)

        b = pd.to_numeric(
            clean[
                col
            ],
            errors="raise",
        ).to_numpy(float)

        if not np.allclose(
            a,
            b,
            rtol=0,
            atol=1e-12,
        ):

            raise RuntimeError(
                f"real reproduction failed: {col}"
            )

    RUN.mkdir(
        parents=True,
        exist_ok=True,
    )

    MANIFEST.write_text(
        json.dumps(
            manifest,
            indent=2,
        )
        + "\n"
    )

    validation[
        "world_order"
    ] = list(
        WORLDS
    )

    validation[
        "real_reproduction"
    ] = "PASS"

    validation[
        "construction_note"
    ] = (
        "Recovery errors are reported as diagnostics. No new arbitrary "
        "benchmark nuisance threshold is introduced here."
    )

    VALIDATION.write_text(
        json.dumps(
            validation,
            indent=2,
        )
        + "\n"
    )

    print(
        "[dossier] built Nuclear L3:"
    )

    for world in WORLDS:
        fit = fits[
            world
        ]

        print(
            f"  {world:<28} "
            f"lambda={fit['lambda_per_day']:.12g}/day "
            f"half={fit['half_life_years']:.9f} y"
        )

    print()
    print(
        "[dossier] manifest ->",
        MANIFEST,
    )

    print(
        "[dossier] validation ->",
        VALIDATION,
    )


if __name__ == "__main__":
    build()
