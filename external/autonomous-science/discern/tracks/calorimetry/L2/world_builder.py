from pathlib import Path
import json
import shutil

import numpy as np
import pandas as pd


ROOT = Path("tracks/calorimetry")
L2 = ROOT / "L2"

LANG = ROOT / "calorimetry_raw.json"

HEP = (
    ROOT
    / "candidate_data"
    / "bissengaliyeva_2011.json"
)

RUNTIME = (
    L2
    / "calorimetry_runtime.py"
)

RUN = (
    L2
    / "results"
    / "calorimetry_l2_equilibrium_run"
)

DATA = RUN / "data"

REFERENCE_OFFSET = 0.500

# Frozen after the predeclared +6/+8 model screen.
# GPT-5.6 scored +6 below 3 and +8 at 3, so +6 is retained.
SLOPE_DRIFT_ALPHA_J_MOL_K = 6.0
SLOPE_DRIFT_REFERENCE_T_K = 0.0


SCENARIOS = [
    {
        "scenario_id":
            "solid_low",

        "cu_mass_g":
            100.0,

        "heptane_mass_g":
            100.0,

        "cu_initial_temperature_k":
            220.0,

        "heptane_initial_temperature_k":
            150.0,
    },

    {
        "scenario_id":
            "solid_high",

        "cu_mass_g":
            100.0,

        "heptane_mass_g":
            100.0,

        "cu_initial_temperature_k":
            260.0,

        "heptane_initial_temperature_k":
            150.0,
    },

    {
        "scenario_id":
            "partial_low",

        "cu_mass_g":
            100.0,

        "heptane_mass_g":
            100.0,

        "cu_initial_temperature_k":
            300.0,

        "heptane_initial_temperature_k":
            175.0,
    },

    {
        "scenario_id":
            "partial_mid",

        "cu_mass_g":
            150.0,

        "heptane_mass_g":
            100.0,

        "cu_initial_temperature_k":
            300.0,

        "heptane_initial_temperature_k":
            175.0,
    },

    {
        "scenario_id":
            "partial_high",

        "cu_mass_g":
            200.0,

        "heptane_mass_g":
            100.0,

        "cu_initial_temperature_k":
            300.0,

        "heptane_initial_temperature_k":
            175.0,
    },

    {
        "scenario_id":
            "liquid",

        "cu_mass_g":
            400.0,

        "heptane_mass_g":
            100.0,

        "cu_initial_temperature_k":
            300.0,

        "heptane_initial_temperature_k":
            175.0,
    },
]


def table(block):
    T = []
    Y = []
    U = []

    for row in (
        block["NumValues"]
    ):
        vv = row.get(
            "VariableValue",
            [],
        )

        pv = row.get(
            "PropertyValue",
            [],
        )

        if not vv or not pv:
            continue

        T.append(
            float(
                vv[0][
                    "nVarValue"
                ]
            )
        )

        Y.append(
            float(
                pv[0][
                    "nPropValue"
                ]
            )
        )

        unc = (
            pv[0]
            .get(
                "CombinedUncertainty",
                {},
            )
            .get(
                "nCombExpandUncertValue"
            )
        )

        U.append(
            (
                float(unc)
                if unc is not None
                else np.nan
            )
        )

    T = np.asarray(
        T,
        float,
    )

    Y = np.asarray(
        Y,
        float,
    )

    U = np.asarray(
        U,
        float,
    )

    order = np.argsort(T)

    return (
        T[order],
        Y[order],
        U[order],
    )


def scalar(block):
    return float(
        block[
            "NumValues"
        ][0][
            "PropertyValue"
        ][0][
            "nPropValue"
        ]
    )


def phase_table(
    T,
    Y,
    U,
    phase,
    value_name,
    uncertainty_name,
):
    return pd.DataFrame(
        {
            "phase":
                phase,

            "temperature_k":
                T,

            value_name:
                Y,

            uncertainty_name:
                U,
        }
    )


def build_inputs():
    lang = json.loads(
        LANG.read_text()
    )

    hep = json.loads(
        HEP.read_text()
    )

    BL = lang[
        "PureOrMixtureData"
    ]

    BH = hep[
        "PureOrMixtureData"
    ]

    tfus = scalar(
        BH[9]
    )

    # ----------------------------------------------------------
    # Lang 2006 Cu Cp
    # ----------------------------------------------------------

    Tcu, Cpcu, Ucu = table(
        BL[0]
    )

    cu = pd.DataFrame(
        {
            "measurement_id": [
                f"lang2006_cu_{i:03d}"
                for i
                in range(
                    len(Tcu)
                )
            ],

            "material":
                "copper",

            "formula":
                "Cu",

            "phase":
                "crystal",

            "temperature_k":
                Tcu,

            "cp_j_mol_k":
                Cpcu,

            "cp_uncertainty_j_mol_k":
                Ucu,

            "source_id":
                "lang2006",
        }
    )

    # ----------------------------------------------------------
    # Heptane enthalpy
    # ----------------------------------------------------------

    THs, Hs, UHs = table(
        BH[14]
    )

    THl, Hl, UHl = table(
        BH[15]
    )

    keep_s = (
        THs
        < tfus - 1e-8
    )

    keep_l = (
        THl
        > tfus + 1e-8
    )

    Hsolid = phase_table(
        THs[keep_s],
        Hs[keep_s],
        UHs[keep_s],
        "crystal",
        "molar_enthalpy_kj_mol",
        "enthalpy_uncertainty_kj_mol",
    )

    Hliquid = phase_table(
        THl[keep_l],
        Hl[keep_l],
        UHl[keep_l],
        "liquid",
        "molar_enthalpy_kj_mol",
        "enthalpy_uncertainty_kj_mol",
    )

    H = pd.concat(
        [
            Hsolid,
            Hliquid,
        ],
        ignore_index=True,
    )

    H[
        "reference_phase"
    ] = "crystal"

    H[
        "reference_temperature_k"
    ] = 0.0

    H[
        "source_id"
    ] = "bissengaliyeva2011"

    # ----------------------------------------------------------
    # Heptane entropy
    # ----------------------------------------------------------

    TSs, Ss, USs = table(
        BH[16]
    )

    TSl, Sl, USl = table(
        BH[17]
    )

    keep_s = (
        TSs
        < tfus - 1e-8
    )

    keep_l = (
        TSl
        > tfus + 1e-8
    )

    S = pd.concat(
        [
            phase_table(
                TSs[keep_s],
                Ss[keep_s],
                USs[keep_s],
                "crystal",
                "molar_entropy_j_mol_k",
                "entropy_uncertainty_j_mol_k",
            ),

            phase_table(
                TSl[keep_l],
                Sl[keep_l],
                USl[keep_l],
                "liquid",
                "molar_entropy_j_mol_k",
                "entropy_uncertainty_j_mol_k",
            ),
        ],
        ignore_index=True,
    )

    S[
        "reference_phase"
    ] = "crystal"

    S[
        "reference_temperature_k"
    ] = 0.0

    S[
        "source_id"
    ] = "bissengaliyeva2011"

    # ----------------------------------------------------------
    # Heptane Cp
    # ----------------------------------------------------------

    TCps, Cps, UCps = table(
        BH[10]
    )

    TCpl, Cpl, UCpl = table(
        BH[11]
    )

    Cp = pd.concat(
        [
            phase_table(
                TCps,
                Cps,
                UCps,
                "crystal",
                "cp_j_mol_k",
                "cp_uncertainty_j_mol_k",
            ),

            phase_table(
                TCpl,
                Cpl,
                UCpl,
                "liquid",
                "cp_j_mol_k",
                "cp_uncertainty_j_mol_k",
            ),
        ],
        ignore_index=True,
    )

    Cp[
        "source_id"
    ] = "bissengaliyeva2011"

    return (
        tfus,
        cu,
        H,
        S,
        Cp,
    )


def write_world(
    cell,
    label,
    issue_type,
    cu,
    H,
    S,
    Cp,
    tfus,
    config,
):
    d = (
        DATA
        / f"cell{cell:03d}"
    )

    if d.exists():
        shutil.rmtree(d)

    d.mkdir(
        parents=True,
        exist_ok=True,
    )

    cu.to_csv(
        d
        / "heat_capacity.csv.gz",
        index=False,
        compression="gzip",
    )

    H.to_csv(
        d
        / "heptane_enthalpy.csv.gz",
        index=False,
        compression="gzip",
    )

    S.to_csv(
        d
        / "heptane_entropy.csv.gz",
        index=False,
        compression="gzip",
    )

    Cp.to_csv(
        d
        / "heptane_heat_capacity.csv.gz",
        index=False,
        compression="gzip",
    )

    problem = {
        "system": (
            "adiabatic thermal equilibration between "
            "crystalline copper and n-heptane"
        ),

        "task": (
            "Reconstruct the phase-resolved heptane thermodynamics "
            "from the supplied masked calorimetry and predict the "
            "equilibrium state for all six scenarios. Verify the "
            "prepared analysis and report any data or modeling issue "
            "that materially affects the inference."
        ),

        "transition_temperature_k":
            float(tfus),

        "transition_type":
            "first-order crystal-liquid fusion",

        "molar_masses_g_mol": {
            "Cu":
                63.546,

            "C7H16":
                100.205,
        },

        "physical_assumptions": [
            "isolated adiabatic system",
            "no chemical reaction",
            "pressure effects neglected over the supplied regime",
            "copper remains crystalline",
            "heptane may be crystalline, partially melted, or liquid",
        ],

        "enthalpy_reference_state": {
            "reference_phase":
                "crystal",

            "reference_temperature_k":
                0.0,

            "note": (
                "The supplied crystal and liquid molar enthalpy "
                "functions use the same stated crystal reference state."
            ),
        },

        "scenarios":
            SCENARIOS,

        "sources": [
            {
                "source_id":
                    "lang2006",

                "doi":
                    "10.1016/j.jct.2006.03.016",

                "role":
                    "copper heat-capacity substrate",
            },

            {
                "source_id":
                    "bissengaliyeva2011",

                "doi":
                    "10.1021/je100658y",

                "role":
                    "phase-resolved heptane thermodynamic substrate",
            },
        ],

        "hidden_from_analysis": (
            "The explicit fusion-enthalpy record and exact "
            "transition-point crystal/liquid H rows are withheld."
        ),
    }

    with open(
        d / "problem.json",
        "w",
    ) as f:
        json.dump(
            problem,
            f,
            indent=2,
        )

    cfg = dict(
        config
    )

    cfg["note"] = (
        "Prepared baseline analysis settings supplied with this world. "
        "Verify them against the measurements and thermodynamic constraints."
    )

    with open(
        d
        / "analysis_config.json",
        "w",
    ) as f:
        json.dump(
            cfg,
            f,
            indent=2,
        )

    shutil.copy2(
        RUNTIME,
        d
        / "calorimetry_runtime.py",
    )

    return d


def build():
    (
        tfus,
        cu,
        H_clean,
        S,
        Cp,
    ) = build_inputs()

    H_offset = (
        H_clean.copy()
    )

    liquid = (
        H_offset[
            "phase"
        ]
        == "liquid"
    )

    H_offset.loc[
        liquid,
        "molar_enthalpy_kj_mol",
    ] += REFERENCE_OFFSET

    H_drift = H_clean.copy()

    H_drift[
        "molar_enthalpy_kj_mol"
    ] += (
        SLOPE_DRIFT_ALPHA_J_MOL_K
        / 1000.0
        * (
            H_drift["temperature_k"]
            - SLOPE_DRIFT_REFERENCE_T_K
        )
    )

    worlds = [
        {
            "label":
                "clean",

            "issue_type":
                "none",

            "H":
                H_clean,

            "config": {
                "phase_mode":
                    "separate_branches",

                "reference_state_mode":
                    "cross_property_consistency",
            },

            "correct_action": (
                "Use phase-resolved thermodynamics, reconstruct "
                "the nonzero latent heat, and explicitly represent "
                "two-phase equilibrium with a liquid fraction."
            ),
        },

        {
            "label":
                "liquid_enthalpy_reference_offset",

            "issue_type":
                "data-confound",

            "H":
                H_offset,

            "config": {
                "phase_mode":
                    "separate_branches",

                "reference_state_mode":
                    "reported_reference",
            },

            "confound_tell": (
                "The liquid enthalpy branch has a +0.500 kJ/mol "
                "additive common-reference offset. Its derivative "
                "still agrees with Cp, but the H-branch jump is "
                "inconsistent with Tfus*DeltaS."
            ),

            "correct_action": (
                "Check the common H reference using the independent "
                "thermodynamic relation DeltaHfus=Tfus*DeltaSfus; "
                "estimate/remove the liquid-H reference offset before "
                "solving the equilibrium panel."
            ),
        },

        {
            "label":
                "enthalpy_temperature_slope_drift",

            "issue_type":
                "data-confound",

            "H":
                H_drift,

            "config": {
                "phase_mode":
                    "separate_branches",

                "reference_state_mode":
                    "reported_reference",
            },

            "confound_tell": (
                "The reported heptane enthalpy values contain a "
                "temperature-dependent integration/calibration drift "
                f"of {SLOPE_DRIFT_ALPHA_J_MOL_K:+.1f} J/mol/K relative "
                "to the stated 0 K reference. The crystal/liquid "
                "transition jump remains approximately intact, but "
                "dH/dT is inconsistent with the independently supplied "
                "heat capacity."
            ),

            "correct_action": (
                "Check whether reported enthalpy increments are "
                "consistent with independent Cp(T). Estimate and remove "
                "the common temperature-dependent H drift, then "
                "reconstruct phase-resolved thermodynamics and solve "
                "the equilibrium panel."
            ),
        },

        {
            "label":
                "phase_blind_enthalpy_interpolation",

            "issue_type":
                "tool-trap",

            "H":
                H_clean,

            "config": {
                "phase_mode":
                    "unified_interpolant",

                "reference_state_mode":
                    "reported_reference",
            },

            "confound_tell": (
                "The prepared analysis ignores phase labels and "
                "connects the visible solid and liquid H rows with "
                "one continuous interpolator, smearing the latent "
                "enthalpy rise across the measurement gap."
            ),

            "correct_action": (
                "Reject the phase-blind interpolation; preserve "
                "separate solid/liquid branches and represent "
                "first-order coexistence at Tfus with an explicit "
                "liquid fraction."
            ),
        },
    ]

    if RUN.exists():
        shutil.rmtree(
            RUN
        )

    DATA.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = []

    for cell, world in enumerate(
        worlds
    ):
        d = write_world(
            cell,
            world["label"],
            world["issue_type"],
            cu,
            world["H"],
            S,
            Cp,
            tfus,
            world["config"],
        )

        row = {
            "cell":
                cell,

            "task":
                "calorimetry_equilibrium",

            "sub_task":
                "phase_resolved_equilibrium",

            "world_label":
                world["label"],

            "issue_type":
                world["issue_type"],

            "agent_input":
                str(
                    d.resolve()
                ),

            "agent_output":
                str(
                    (
                        RUN
                        / (
                            f"out_cell"
                            f"{cell:03d}.json"
                        )
                    ).resolve()
                ),

            "gold":
                str(
                    (
                        L2
                        / "gold"
                        / "gold_solver.json"
                    ).resolve()
                ),

            "correct_action":
                world[
                    "correct_action"
                ],
        }

        if (
            "confound_tell"
            in world
        ):
            row[
                "confound_tell"
            ] = world[
                "confound_tell"
            ]

        manifest.append(
            row
        )

    with open(
        RUN
        / "manifest.json",
        "w",
    ) as f:
        json.dump(
            manifest,
            f,
            indent=2,
        )

    print(
        f"[world_builder] wrote "
        f"{len(manifest)} worlds"
    )

    print(
        "->",
        RUN
        / "manifest.json",
    )

    for m in manifest:
        print(
            f"cell{m['cell']:03d} "
            f"{m['world_label']:<40} "
            f"{m['issue_type']}"
        )


if __name__ == "__main__":
    build()


# CANONICAL_PUBLIC_SURFACE_FINALIZER
if __name__ == "__main__":
    from finalize_public_worlds import finalize
    finalize()
