
"""
Calorimetry L3 common evidence mechanics for the final nano-Cu world pair.
"""

from pathlib import Path

import json
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent

TRACK = HERE.parent

L2 = (
    TRACK
    / "L2"
)

SHADOW = (
    HERE
    / "candidate_data"
    / "nano_cu_final_l2_shadow"
)

REAL_WORLD = (
    SHADOW
    / "worlds"
    / "real"
)

CF_WORLD = (
    SHADOW
    / "worlds"
    / "cf_nano_cu"
)

SHADOW_GOLD = (
    SHADOW
    / "shadow_gold.json"
)

SHADOW_REPORT = (
    SHADOW
    / "shadow_build_report.json"
)

GATE0 = (
    HERE
    / "physics_probe_results"
    / "nano_cu_gate0_adjudication.json"
)


ANCHOR = (
    "cu-cp-bulk-reuse"
)


WORLDS = (
    "real",
    "cf_nano_cu",
)


ALIASES = [
    "Cu heat capacity",
    "copper heat capacity",
    "Cu Cp",
    "Cp(T)",
    "bulk Cu",
    "bulk reference",
    "bulk reuse",
    "nanocrystalline Cu",
    "nano-Cu",
    "grain size",
    "8 nm",
    "grain boundary",
    "heat capacity",
]


def _json(
    path,
):
    return json.loads(
        Path(
            path
        ).read_text()
    )


def shadow_gold():
    return _json(
        SHADOW_GOLD
    )


def shadow_report():
    return _json(
        SHADOW_REPORT
    )


def gate0():
    return _json(
        GATE0
    )


def public_world(
    world,
):
    if world == "real":
        return REAL_WORLD

    if world == "cf_nano_cu":
        return CF_WORLD

    raise KeyError(
        world
    )


def specimen_metadata(
    world,
):
    if world == "real":

        return {
            "material":
                "Cu",

            "crystal_structure":
                "fcc",

            "description":
                (
                    "ordinary coarse-grained/polycrystalline "
                    "copper reference specimen"
                ),
        }

    if world == "cf_nano_cu":

        return {
            "material":
                "Cu",

            "crystal_structure":
                "fcc",

            "description":
                (
                    "same-composition crystalline copper "
                    "follow-up specimen"
                ),

            "mean_crystallite_size_nm":
                8.0,

            "phase_transition_reported_in_interval":
                False,
        }

    raise KeyError(
        world
    )


def cp_comparison_panel(
    world,
):
    bulk = pd.read_csv(
        REAL_WORLD
        / "heat_capacity.csv.gz"
    )

    specimen = pd.read_csv(
        public_world(
            world
        )
        / "heat_capacity.csv.gz"
    )

    if (
        list(
            bulk.columns
        )
        != list(
            specimen.columns
        )
        or len(
            bulk
        )
        != len(
            specimen
        )
    ):
        raise ValueError(
            "Cu Cp tables are not row-aligned"
        )

    fixed = [
        c
        for c
        in bulk.columns
        if c
        != "cp_j_mol_k"
    ]

    for c in fixed:

        if not bulk[
            c
        ].equals(
            specimen[
                c
            ]
        ):
            raise ValueError(
                f"non-Cp column changed: {c}"
            )

    mask = (
        bulk[
            "temperature_k"
        ].between(
            150.0,
            300.0,
            inclusive="both",
        )
    )

    out = pd.DataFrame(
        {
            "measurement_id":
                bulk.loc[
                    mask,
                    "measurement_id",
                ]
                .astype(str)
                .to_numpy(),

            "temperature_k":
                bulk.loc[
                    mask,
                    "temperature_k",
                ]
                .astype(float)
                .to_numpy(),

            "bulk_reference_cp_j_mol_k":
                bulk.loc[
                    mask,
                    "cp_j_mol_k",
                ]
                .astype(float)
                .to_numpy(),

            "specimen_cp_j_mol_k":
                specimen.loc[
                    mask,
                    "cp_j_mol_k",
                ]
                .astype(float)
                .to_numpy(),

            "cp_uncertainty_j_mol_k":
                specimen.loc[
                    mask,
                    "cp_uncertainty_j_mol_k",
                ]
                .astype(float)
                .to_numpy(),

            "source_id":
                specimen.loc[
                    mask,
                    "source_id",
                ]
                .astype(str)
                .to_numpy(),
        }
    )

    return out.reset_index(
        drop=True
    )


def _scenario_map(
    rows,
):
    return {
        row[
            "scenario_id"
        ]:
            row

        for row
        in rows
    }


def equilibrium_panel(
    world,
):
    gold = (
        shadow_gold()
    )

    # Immutable experimental inputs belong to the frozen L2 scenario
    # definition, not to the downstream runtime output rows.
    #
    # The promotion provenance audit asserts these four input fields are
    # identical in:
    #   - real_exact_l2_gold["scenarios"]
    #   - worlds/real/problem.json
    #   - worlds/cf_nano_cu/problem.json
    #
    # Runtime equilibrium rows remain the source of downstream solver
    # outputs only.
    inputs = _scenario_map(
        gold[
            "real_exact_l2_gold"
        ][
            "scenarios"
        ]
    )

    bulk = _scenario_map(
        gold[
            "public_runtime"
        ][
            "real"
        ][
            "equilibrium_panel"
        ]
    )

    observed = _scenario_map(
        gold[
            "public_runtime"
        ][
            world
        ][
            "equilibrium_panel"
        ]
    )

    rows = []

    for sid in (
        "solid_low",
        "solid_high",
        "partial_low",
        "partial_mid",
        "partial_high",
        "liquid",
    ):
        inp = inputs[
            sid
        ]

        b = bulk[
            sid
        ]

        o = observed[
            sid
        ]

        rows.append(
            {
                "scenario_id":
                    sid,

                "cu_mass_g":
                    float(
                        inp[
                            "cu_mass_g"
                        ]
                    ),

                "heptane_mass_g":
                    float(
                        inp[
                            "heptane_mass_g"
                        ]
                    ),

                "cu_initial_temperature_k":
                    float(
                        inp[
                            "cu_initial_temperature_k"
                        ]
                    ),

                "heptane_initial_temperature_k":
                    float(
                        inp[
                            "heptane_initial_temperature_k"
                        ]
                    ),

                "bulk_reference_temperature_k":
                    float(
                        b[
                            "temperature_k"
                        ]
                    ),

                "specimen_temperature_k":
                    float(
                        o[
                            "temperature_k"
                        ]
                    ),

                "bulk_reference_liquid_fraction":
                    float(
                        b[
                            "liquid_fraction"
                        ]
                    ),

                "specimen_liquid_fraction":
                    float(
                        o[
                            "liquid_fraction"
                        ]
                    ),

                "bulk_reference_regime":
                    b[
                        "regime"
                    ],

                "specimen_regime":
                    o[
                        "regime"
                    ],
            }
        )

    return pd.DataFrame(
        rows
    )


def exact_scenarios(
    world,
):
    gold = (
        shadow_gold()
    )

    key = (
        "real_exact_l2_gold"
        if world
        == "real"
        else
        "cf_nano_cu_exact_l2_gold"
    )

    return gold[
        key
    ][
        "scenarios"
    ]


def data_supported_direction(
    world,
):
    if world == "real":

        return (
            "follow-up Cu Cp is consistent with the carried-forward "
            "bulk-Cu reference, and the six phase-resolved Cu-heptane "
            "equilibrium outcomes match the bulk-Cu prediction"
        )

    if world == "cf_nano_cu":

        return (
            "the approximately 8 nm same-composition fcc Cu specimen "
            "has materially higher Cp than the bulk-Cu reference over "
            "150-300 K, with coherent warmer single-phase equilibria "
            "and larger liquid fractions in the partial-melt scenarios"
        )

    raise KeyError(
        world
    )


def textbook_direction():

    return (
        "same-composition fcc Cu with no phase transition should remain "
        "close to ordinary bulk Cu Cp(T); nanocrystallinity may permit "
        "a small excess, but a roughly ten-percent-scale enhancement "
        "would be surprising"
    )


def expected_method(
    world,
):
    base = (
        "Start from the supplied measurements rather than the textbook "
        "expectation. Quantify specimen Cp(T) against the carried-forward "
        "bulk-Cu reference across 150-300 K, including the scale and "
        "temperature coherence of any difference relative to the reported "
        "uncertainty. Then check whether the same signed thermal change "
        "coherently explains the six phase-resolved Cu-heptane outcomes: "
        "increased Cu heat capacity should shift single-phase equilibrium "
        "temperatures upward and, at the fixed heptane transition "
        "temperature, increase the predicted liquid fraction. Distinguish "
        "an empirical specimen-specific heat-capacity departure from proof "
        "of a unique microscopic mechanism. Consider calibration/"
        "normalization, composition or oxide/impurity differences, "
        "unrecognized phase changes, and microstructure/grain-boundary "
        "contributions. A strong next test would vary grain size or anneal/"
        "coarsen the same material while repeating direct calorimetry and "
        "the equilibrium check with composition/oxide controls."
    )

    if world == "real":

        return (
            base
            +
            " In the real control, do not manufacture a nanocrystalline "
            "heat-capacity anomaly when the specimen and downstream "
            "equilibrium agree with the bulk reference."
        )

    return (
        base
        +
        " In the follow-up world, do not reject a coherent large departure "
        "merely because ordinary bulk-reuse is the stronger prior; report "
        "the evidence while keeping the microscopic explanation bounded."
    )


# === CALORIMETRY L3 FINAL THREE-WORLD ROUTING + PROVENANCE ===
#
# The numerical mechanics below remain those already defined above.
# This section only:
#   1. routes to the validated 3-world shadow;
#   2. exposes the third 50-nm world;
#   3. restores the canonical provenance-repair schema on every public
#      Cp evidence panel.
#
# It does NOT implement an equilibrium solver.

SHADOW = (
    HERE
    / "candidate_data"
    / "nano_cu_50nm_final_l2_shadow"
)

REAL_WORLD = (
    SHADOW
    / "worlds"
    / "real"
)

CF_WORLD = (
    SHADOW
    / "worlds"
    / "cf_nano_cu"
)

CF_50NM_WORLD = (
    SHADOW
    / "worlds"
    / "cf_nano_cu_50nm"
)

SHADOW_GOLD = (
    SHADOW
    / "shadow_gold.json"
)

WORLDS = (
    "real",
    "cf_nano_cu",
    "cf_nano_cu_50nm",
)


def public_world(
    world,
):

    mapping = {
        "real":
            REAL_WORLD,

        "cf_nano_cu":
            CF_WORLD,

        "cf_nano_cu_50nm":
            CF_50NM_WORLD,
    }

    if world not in mapping:
        raise KeyError(world)

    return mapping[world]


# Save the existing numerical panel constructor.
_cp_comparison_panel_numeric = cp_comparison_panel


def _apply_public_provenance(
    df,
    world,
):

    df = df.copy()

    # These values are the canonical mapping from
    # repair_nano_cu_provenance.py.
    if world == "real":

        df["measurement_id"] = [
            f"benchmark_real_bulk_control_cp_{i:03d}"
            for i in range(len(df))
        ]

        df["source_id"] = (
            "benchmark_real_control"
        )

        df["bulk_reference_source_id"] = (
            "lang2006"
        )

        df["specimen_value_origin"] = (
            "benchmark_control_equal_to_frozen_bulk_reference"
        )

        df["historical_specimen_measurement"] = (
            False
        )

        df["counterfactual_world"] = (
            False
        )


    elif world == "cf_nano_cu":

        df["measurement_id"] = [
            f"benchmark_cf_nano_cu_cp_{i:03d}"
            for i in range(len(df))
        ]

        df["source_id"] = (
            "benchmark_process_control"
        )

        df["bulk_reference_source_id"] = (
            "lang2006"
        )

        df["specimen_value_origin"] = (
            "benchmark_upstream_process_control_1p10_times_bulk_reference"
        )

        df["historical_specimen_measurement"] = (
            False
        )

        df["counterfactual_world"] = (
            True
        )


    elif world == "cf_nano_cu_50nm":

        df["measurement_id"] = [
            f"benchmark_cf_nano_cu_50nm_cp_{i:03d}"
            for i in range(len(df))
        ]

        df["source_id"] = (
            "benchmark_process_control"
        )

        df["bulk_reference_source_id"] = (
            "lang2006"
        )

        df["specimen_value_origin"] = (
            "benchmark_upstream_process_control_1p045_times_bulk_reference"
        )

        df["historical_specimen_measurement"] = (
            False
        )

        df["counterfactual_world"] = (
            True
        )


    else:

        raise KeyError(world)


    cols = [
        "measurement_id",
        "temperature_k",
        "bulk_reference_cp_j_mol_k",
        "specimen_cp_j_mol_k",
        "cp_uncertainty_j_mol_k",
        "source_id",
        "bulk_reference_source_id",
        "specimen_value_origin",
        "historical_specimen_measurement",
        "counterfactual_world",
    ]

    return df[cols]


def cp_comparison_panel(
    world,
):

    return _apply_public_provenance(
        _cp_comparison_panel_numeric(
            world
        ),
        world,
    )


def exact_l2_gold(
    world,
):

    mapping = {
        "real":
            "real_exact_l2_gold",

        "cf_nano_cu":
            "cf_nano_cu_exact_l2_gold",

        "cf_nano_cu_50nm":
            "cf_nano_cu_50nm_exact_l2_gold",
    }

    if world not in mapping:
        raise KeyError(world)

    return shadow_gold()[
        mapping[world]
    ]


def data_supported_direction(
    world,
):

    if world == "real":

        return (
            "follow-up Cu Cp is consistent with the carried-forward "
            "bulk-Cu reference, and all six phase-resolved equilibrium "
            "outcomes match the bulk-Cu prediction"
        )


    if world == "cf_nano_cu":

        return (
            "the approximately 8 nm same-composition fcc Cu specimen "
            "shows a coherent approximately 10% Cp excess over the "
            "bulk reference, with warmer single-phase equilibria and "
            "larger partial-melt liquid fractions"
        )


    if world == "cf_nano_cu_50nm":

        return (
            "the approximately 50 nm nanocrystalline Cu specimen state "
            "shows a coherent approximately 4.5% Cp excess over the "
            "bulk reference, with warmer single-phase equilibria and "
            "larger partial-melt liquid fractions"
        )


    raise KeyError(world)


def textbook_direction(
    world,
):

    if world == "cf_nano_cu_50nm":

        return (
            "same-composition approximately 50-nm nanocrystalline fcc Cu "
            "should ordinarily remain close to bulk Cu Cp(T), with at most "
            "a small sub-percent to few-percent excess as the natural "
            "zeroth-order expectation; a coherent 4.5% specimen-level "
            "departure is therefore a moderate evidence-over-prior test"
        )


    return (
        "same-composition fcc Cu with no phase transition should remain "
        "close to ordinary bulk Cu Cp(T); nanocrystallinity may permit "
        "a small excess, while a roughly ten-percent-scale enhancement "
        "would be surprising"
    )


ALIASES = list(
    dict.fromkeys(
        list(ALIASES)
        + [
            "50 nm",
            "50-nm",
            "50 nm nanocrystalline Cu",
            "50-nm nanocrystalline Cu",
            "nanocrystalline copper",
        ]
    )
)


# === CALORIMETRY L3 CLEAN MODEL-VISIBLE EVIDENCE VIEW ===
#
# IMPORTANT:
# Hidden construction provenance remains in the manifest / freeze / audits.
# The benchmarked agent receives only scientific evidence.  The public view
# therefore contains no real-vs-CF label, no construction-status field, and
# no claim that the supplied specimen series is an independent historical
# measurement.
#
# Numeric scientific values are untouched.

_cp_comparison_panel_hidden_provenance = cp_comparison_panel


def cp_comparison_panel(
    world,
):

    import pandas as _pd

    internal = (
        _cp_comparison_panel_hidden_provenance(
            world
        )
        .copy()
        .reset_index(
            drop=True
        )
    )

    n = len(
        internal
    )

    public = _pd.DataFrame(
        {
            "measurement_id": [
                f"specimen_cp_{i:03d}"
                for i in range(
                    n
                )
            ],

            "temperature_k":
                internal[
                    "temperature_k"
                ].to_numpy(),

            "bulk_reference_cp_j_mol_k":
                internal[
                    "bulk_reference_cp_j_mol_k"
                ].to_numpy(),

            "specimen_cp_j_mol_k":
                internal[
                    "specimen_cp_j_mol_k"
                ].to_numpy(),

            "cp_uncertainty_j_mol_k":
                internal[
                    "cp_uncertainty_j_mol_k"
                ].to_numpy(),

            # Same reference provenance in every public world.
            # This describes only the carried-forward bulk reference,
            # not the origin/status of the follow-up specimen series.
            "bulk_reference_source_id": [
                "lang2006"
                for _ in range(
                    n
                )
            ],
        }
    )

    return public

