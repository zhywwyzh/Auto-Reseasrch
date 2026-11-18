"""
Gold-free Calorimetry L2 runtime.

The helper exposes scientifically meaningful candidate analyses for the
phase-transition task. It contains no hidden transition enthalpy, no hidden
endpoint values, and no grader thresholds.

Public entry point:

    analyze_world(
        world_dir,
        phase_mode=None,
        reference_state_mode=None,
    )

phase_mode:
    "separate_branches"
    "continuous_transition"
    "unified_interpolant"

reference_state_mode:
    "reported_reference"
    "cross_property_consistency"

If an option is None, the prepared value in analysis_config.json is used.
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq


M_CU = 63.546
M_HEP = 100.205


def _read(world_dir):
    world_dir = Path(world_dir)

    problem = json.load(
        open(world_dir / "problem.json")
    )

    config = json.load(
        open(world_dir / "analysis_config.json")
    )

    cu = pd.read_csv(
        world_dir / "heat_capacity.csv.gz"
    )

    H = pd.read_csv(
        world_dir / "heptane_enthalpy.csv.gz"
    )

    S = pd.read_csv(
        world_dir / "heptane_entropy.csv.gz"
    )

    Cp_hep = pd.read_csv(
        world_dir / "heptane_heat_capacity.csv.gz"
    )

    return problem, config, cu, H, S, Cp_hep


def _branch(df, phase, value_col):
    z = (
        df.loc[
            df["phase"] == phase,
            ["temperature_k", value_col],
        ]
        .dropna()
        .sort_values("temperature_k")
    )

    T = z["temperature_k"].to_numpy(float)
    Y = z[value_col].to_numpy(float)

    if len(T) < 4:
        raise ValueError(
            f"insufficient {phase} rows for {value_col}"
        )

    return T, Y


def _local_poly_limit(
    T,
    Y,
    target,
    side,
    degree=2,
    n=8,
):
    if side == "left":
        tx = T[-n:]
        yx = Y[-n:]
    else:
        tx = T[:n]
        yx = Y[:n]

    degree = min(
        degree,
        len(tx) - 1,
    )

    p = np.polyfit(
        tx,
        yx,
        degree,
    )

    return float(
        np.polyval(
            p,
            target,
        )
    )


def _cu_enthalpy(cu):
    z = (
        cu[
            [
                "temperature_k",
                "cp_j_mol_k",
            ]
        ]
        .dropna()
        .sort_values(
            "temperature_k"
        )
    )

    T = z[
        "temperature_k"
    ].to_numpy(float)

    Cp = z[
        "cp_j_mol_k"
    ].to_numpy(float)

    f = PchipInterpolator(
        T,
        Cp,
        extrapolate=False,
    )

    F = f.antiderivative()

    tref = float(
        T.min()
    )

    def Hcu(temp):
        return float(
            (
                F(temp)
                - F(tref)
            )
            / 1000.0
        )

    return Hcu, T


def _visible_phase_model(
    H,
    S,
    tfus,
    reference_state_mode,
):
    THs, Hs = _branch(
        H,
        "crystal",
        "molar_enthalpy_kj_mol",
    )

    THl, Hl = _branch(
        H,
        "liquid",
        "molar_enthalpy_kj_mol",
    )

    TSs, Ss = _branch(
        S,
        "crystal",
        "molar_entropy_j_mol_k",
    )

    TSl, Sl = _branch(
        S,
        "liquid",
        "molar_entropy_j_mol_k",
    )

    HS = PchipInterpolator(
        THs,
        Hs,
        extrapolate=True,
    )

    HL_raw = PchipInterpolator(
        THl,
        Hl,
        extrapolate=True,
    )

    SS = PchipInterpolator(
        TSs,
        Ss,
        extrapolate=True,
    )

    SL = PchipInterpolator(
        TSl,
        Sl,
        extrapolate=True,
    )

    raw_hsf = float(
        HS(tfus)
    )

    raw_hlf = float(
        HL_raw(tfus)
    )

    raw_jump = (
        raw_hlf
        - raw_hsf
    )

    delta_s = float(
        SL(tfus)
        - SS(tfus)
    )

    tdeltas = (
        tfus
        * delta_s
        / 1000.0
    )

    correction = 0.0

    if (
        reference_state_mode
        == "cross_property_consistency"
    ):
        correction = (
            raw_jump
            - tdeltas
        )

    elif (
        reference_state_mode
        != "reported_reference"
    ):
        raise ValueError(
            "reference_state_mode must be "
            "'reported_reference' or "
            "'cross_property_consistency'"
        )

    corrected_Hl = (
        Hl
        - correction
    )

    HL = PchipInterpolator(
        THl,
        corrected_Hl,
        extrapolate=True,
    )

    # For entropy-consistent reconstruction, use a stable local
    # solid-phase extrapolation and enforce the phase-equilibrium
    # thermodynamic identity dH = T dS.
    if (
        reference_state_mode
        == "cross_property_consistency"
    ):
        hsf = _local_poly_limit(
            THs,
            Hs,
            tfus,
            side="left",
            degree=2,
            n=min(
                8,
                len(THs),
            ),
        )

        hlf = (
            hsf
            + tdeltas
        )

    else:
        hsf = float(
            HS(tfus)
        )

        hlf = float(
            HL(tfus)
        )

    return {
        "THs":
            THs,

        "Hs":
            Hs,

        "THl":
            THl,

        "Hl":
            corrected_Hl,

        "HS":
            HS,

        "HL":
            HL,

        "Hsf":
            float(hsf),

        "Hlf":
            float(hlf),

        "latent_heat_kj_mol":
            float(
                hlf - hsf
            ),

        "delta_s_j_mol_k":
            delta_s,

        "t_delta_s_kj_mol":
            tdeltas,

        "reference_offset_correction_kj_mol":
            float(correction),

        "raw_h_jump_kj_mol":
            float(raw_jump),
    }


def _solve_separate_branches(
    model,
    Hcu,
    Tcu_domain,
    tfus,
    scenario,
):
    HS = model["HS"]
    HL = model["HL"]

    Hsf = model["Hsf"]
    Hlf = model["Hlf"]

    ncu = (
        float(
            scenario["cu_mass_g"]
        )
        / M_CU
    )

    nh = (
        float(
            scenario[
                "heptane_mass_g"
            ]
        )
        / M_HEP
    )

    Tcu0 = float(
        scenario[
            "cu_initial_temperature_k"
        ]
    )

    Thep0 = float(
        scenario[
            "heptane_initial_temperature_k"
        ]
    )

    E0 = (
        ncu * Hcu(Tcu0)
        +
        nh * float(
            HS(Thep0)
        )
    )

    Esolid = (
        ncu * Hcu(tfus)
        +
        nh * Hsf
    )

    Eliquid = (
        ncu * Hcu(tfus)
        +
        nh * Hlf
    )

    if E0 < Esolid:

        def f(T):
            return (
                ncu * Hcu(T)
                +
                nh * float(
                    HS(T)
                )
                -
                E0
            )

        lo = max(
            min(
                Tcu0,
                Thep0,
            ),
            float(
                Tcu_domain.min()
            ),
            float(
                model["THs"].min()
            ),
        )

        T = brentq(
            f,
            lo,
            tfus,
        )

        return {
            "temperature_k":
                float(T),

            "liquid_fraction":
                0.0,

            "regime":
                "solid",
        }

    if E0 <= Eliquid:
        x = (
            E0 - Esolid
        ) / (
            Eliquid - Esolid
        )

        return {
            "temperature_k":
                float(tfus),

            "liquid_fraction":
                float(x),

            "regime":
                "partial_melt",
        }

    def f(T):
        return (
            ncu * Hcu(T)
            +
            nh * float(
                HL(T)
            )
            -
            E0
        )

    hi = min(
        max(
            Tcu0,
            Thep0,
        ),
        float(
            Tcu_domain.max()
        ),
        float(
            model["THl"].max()
        ),
    )

    T = brentq(
        f,
        tfus,
        hi,
    )

    return {
        "temperature_k":
            float(T),

        "liquid_fraction":
            1.0,

        "regime":
            "liquid",
    }


def _solve_no_latent(
    model,
    Hcu,
    Tcu_domain,
    tfus,
    scenario,
):
    HS = model["HS"]
    HL = model["HL"]

    observed_jump = (
        float(
            HL(tfus)
        )
        -
        float(
            HS(tfus)
        )
    )

    def Hhep(T):
        if T <= tfus:
            return float(
                HS(T)
            )

        return (
            float(
                HL(T)
            )
            -
            observed_jump
        )

    ncu = (
        float(
            scenario["cu_mass_g"]
        )
        / M_CU
    )

    nh = (
        float(
            scenario[
                "heptane_mass_g"
            ]
        )
        / M_HEP
    )

    Tcu0 = float(
        scenario[
            "cu_initial_temperature_k"
        ]
    )

    Thep0 = float(
        scenario[
            "heptane_initial_temperature_k"
        ]
    )

    E0 = (
        ncu * Hcu(Tcu0)
        +
        nh * Hhep(
            Thep0
        )
    )

    def f(T):
        return (
            ncu * Hcu(T)
            +
            nh * Hhep(T)
            -
            E0
        )

    lo = max(
        min(
            Tcu0,
            Thep0,
        ),
        float(
            Tcu_domain.min()
        ),
        float(
            model["THs"].min()
        ),
    )

    hi = min(
        max(
            Tcu0,
            Thep0,
        ),
        float(
            Tcu_domain.max()
        ),
        float(
            model["THl"].max()
        ),
    )

    T = float(
        brentq(
            f,
            lo,
            hi,
        )
    )

    return {
        "temperature_k":
            T,

        "liquid_fraction":
            (
                0.0
                if T < tfus
                else 1.0
            ),

        "regime":
            (
                "solid"
                if T < tfus
                else "liquid"
            ),
    }


def _solve_unified_interpolant(
    model,
    Hcu,
    Tcu_domain,
    tfus,
    scenario,
):
    Tblind = np.r_[
        model["THs"],
        model["THl"],
    ]

    Hblind_values = np.r_[
        model["Hs"],
        model["Hl"],
    ]

    order = np.argsort(
        Tblind
    )

    Tblind = Tblind[
        order
    ]

    Hblind_values = (
        Hblind_values[
            order
        ]
    )

    Hblind = PchipInterpolator(
        Tblind,
        Hblind_values,
        extrapolate=False,
    )

    ncu = (
        float(
            scenario["cu_mass_g"]
        )
        / M_CU
    )

    nh = (
        float(
            scenario[
                "heptane_mass_g"
            ]
        )
        / M_HEP
    )

    Tcu0 = float(
        scenario[
            "cu_initial_temperature_k"
        ]
    )

    Thep0 = float(
        scenario[
            "heptane_initial_temperature_k"
        ]
    )

    E0 = (
        ncu * Hcu(Tcu0)
        +
        nh * float(
            Hblind(Thep0)
        )
    )

    def f(T):
        return (
            ncu * Hcu(T)
            +
            nh * float(
                Hblind(T)
            )
            -
            E0
        )

    lo = max(
        min(
            Tcu0,
            Thep0,
        ),
        float(
            Tcu_domain.min()
        ),
        float(
            Tblind.min()
        ),
    )

    hi = min(
        max(
            Tcu0,
            Thep0,
        ),
        float(
            Tcu_domain.max()
        ),
        float(
            Tblind.max()
        ),
    )

    T = float(
        brentq(
            f,
            lo,
            hi,
        )
    )

    return {
        "temperature_k":
            T,

        "liquid_fraction":
            (
                0.0
                if T < tfus
                else 1.0
            ),

        "regime":
            (
                "solid"
                if T < tfus
                else "liquid"
            ),
    }


def analyze_world(
    world_dir,
    phase_mode=None,
    reference_state_mode=None,
):
    (
        problem,
        config,
        cu,
        H,
        S,
        Cp_hep,
    ) = _read(
        world_dir
    )

    del Cp_hep

    if phase_mode is None:
        phase_mode = config[
            "phase_mode"
        ]

    if reference_state_mode is None:
        reference_state_mode = (
            config[
                "reference_state_mode"
            ]
        )

    tfus = float(
        problem[
            "transition_temperature_k"
        ]
    )

    model = _visible_phase_model(
        H,
        S,
        tfus,
        reference_state_mode,
    )

    Hcu, Tcu_domain = (
        _cu_enthalpy(
            cu
        )
    )

    panel = []

    for scenario in (
        problem["scenarios"]
    ):
        if (
            phase_mode
            == "separate_branches"
        ):
            ans = (
                _solve_separate_branches(
                    model,
                    Hcu,
                    Tcu_domain,
                    tfus,
                    scenario,
                )
            )

        elif (
            phase_mode
            == "continuous_transition"
        ):
            ans = (
                _solve_no_latent(
                    model,
                    Hcu,
                    Tcu_domain,
                    tfus,
                    scenario,
                )
            )

        elif (
            phase_mode
            == "unified_interpolant"
        ):
            ans = (
                _solve_unified_interpolant(
                    model,
                    Hcu,
                    Tcu_domain,
                    tfus,
                    scenario,
                )
            )

        else:
            raise ValueError(
                "phase_mode must be "
                "'separate_branches', "
                "'continuous_transition', or "
                "'unified_interpolant'"
            )

        panel.append(
            {
                "scenario_id":
                    scenario[
                        "scenario_id"
                    ],

                **ans,
            }
        )

    reported_latent = (
        model[
            "latent_heat_kj_mol"
        ]
    )

    if (
        phase_mode
        == "continuous_transition"
    ):
        reported_latent = 0.0

    return {
        "latent_heat_kj_mol":
            float(
                reported_latent
            ),

        "equilibrium_panel":
            panel,

        "method": {
            "phase_mode":
                phase_mode,

            "reference_state_mode":
                reference_state_mode,

            "enthalpy_model":
                (
                    "phase-resolved PCHIP branches"
                    if phase_mode
                    == "separate_branches"
                    else
                    (
                        "continuous enthalpy transition path"
                        if phase_mode
                        == "continuous_transition"
                        else
                        "single unified PCHIP enthalpy interpolator"
                    )
                ),

            "latent_heat_reconstruction":
                (
                    "cross-property thermodynamic reconstruction"
                    if reference_state_mode
                    == "cross_property_consistency"
                    else
                    "difference of reported-reference extrapolated H branches"
                ),

            "reference_state_validation":
                (
                    "cross-property thermodynamic consistency"
                    if reference_state_mode
                    == "cross_property_consistency"
                    else
                    "none"
                ),

            "reference_offset_correction_kj_mol":
                float(
                    model[
                        "reference_offset_correction_kj_mol"
                    ]
                ),
        },

        "diagnostics": {
            "raw_h_jump_kj_mol":
                float(
                    model[
                        "raw_h_jump_kj_mol"
                    ]
                ),

            "t_delta_s_kj_mol":
                float(
                    model[
                        "t_delta_s_kj_mol"
                    ]
                ),

            "delta_s_j_mol_k":
                float(
                    model[
                        "delta_s_j_mol_k"
                    ]
                ),
        },

        "prepared_config":
            config,
    }
