"""
Finalize Calorimetry L2 agent-visible worlds.

The scientific substrate/world injection is produced by world_builder.py.

This finalization step changes ONLY the public software surface:
  - all worlds receive the same neutral analysis_config.json;
  - problem metadata does not directly announce a first-order-vs-continuous
    contradiction;
  - each world exposes exactly ONE prepared analyze_world(world_dir)
    implementation;
  - robust alternative solver implementations are NOT bundled with the
    prepared software.

Agents remain free to inspect the prepared implementation and implement an
independent scientific analysis from the supplied H/S/Cp measurements.
"""

from pathlib import Path
import json


HERE = Path(__file__).resolve().parent
RUN = HERE / "results" / "calorimetry_l2_equilibrium_run"


COMMON = r'''
from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq


M_CU_G_MOL = 63.546
M_HEPTANE_G_MOL = 100.205


def _load(world_dir):
    d = Path(world_dir)

    problem = json.load(
        open(d / "problem.json")
    )

    cu = pd.read_csv(
        d / "heat_capacity.csv.gz"
    )

    h = pd.read_csv(
        d / "heptane_enthalpy.csv.gz"
    )

    s = pd.read_csv(
        d / "heptane_entropy.csv.gz"
    )

    cp = pd.read_csv(
        d / "heptane_heat_capacity.csv.gz"
    )

    return problem, cu, h, s, cp


def _pchip_phase(df, phase, value_col):
    x = (
        df.loc[
            df["phase"] == phase,
            "temperature_k",
        ]
        .to_numpy(float)
    )

    y = (
        df.loc[
            df["phase"] == phase,
            value_col,
        ]
        .to_numpy(float)
    )

    order = np.argsort(x)

    return PchipInterpolator(
        x[order],
        y[order],
        extrapolate=True,
    )


def _prepare(world_dir):
    problem, cu, h, s, cp = _load(
        world_dir
    )

    t_f = float(
        problem["transition_temperature_k"]
    )

    tc = cu["temperature_k"].to_numpy(float)
    cc = cu["cp_j_mol_k"].to_numpy(float)

    order = np.argsort(tc)
    tc = tc[order]
    cc = cc[order]

    cp_cu = PchipInterpolator(
        tc,
        cc,
        extrapolate=True,
    )

    antiderivative = cp_cu.antiderivative()
    t_ref = float(tc[0])

    def h_cu(T):
        return float(
            (
                antiderivative(float(T))
                - antiderivative(t_ref)
            )
            / 1000.0
        )

    h_s = _pchip_phase(
        h,
        "crystal",
        "molar_enthalpy_kj_mol",
    )

    h_l = _pchip_phase(
        h,
        "liquid",
        "molar_enthalpy_kj_mol",
    )

    s_s = _pchip_phase(
        s,
        "crystal",
        "molar_entropy_j_mol_k",
    )

    s_l = _pchip_phase(
        s,
        "liquid",
        "molar_entropy_j_mol_k",
    )

    h_sf = float(h_s(t_f))
    h_lf = float(h_l(t_f))

    raw_jump = h_lf - h_sf

    s_sf = float(s_s(t_f))
    s_lf = float(s_l(t_f))

    tds = (
        t_f
        * (s_lf - s_sf)
        / 1000.0
    )

    return {
        "problem": problem,
        "h_table": h,
        "t_f": t_f,
        "h_cu": h_cu,
        "h_s": h_s,
        "h_l": h_l,
        "h_sf": h_sf,
        "h_lf": h_lf,
        "raw_jump": raw_jump,
        "tds": tds,
    }


def _amounts(scenario):
    return (
        float(scenario["cu_mass_g"])
        / M_CU_G_MOL,
        float(scenario["heptane_mass_g"])
        / M_HEPTANE_G_MOL,
    )


def _initial_energy(scenario, h_cu, h_s):
    n_cu, n_h = _amounts(
        scenario
    )

    return (
        n_cu
        * h_cu(
            scenario[
                "cu_initial_temperature_k"
            ]
        )
        + n_h
        * float(
            h_s(
                scenario[
                    "heptane_initial_temperature_k"
                ]
            )
        )
    )


def _bounds(scenario, t_f):
    lo = min(
        float(
            scenario[
                "cu_initial_temperature_k"
            ]
        ),
        float(
            scenario[
                "heptane_initial_temperature_k"
            ]
        ),
    )

    hi = max(
        float(
            scenario[
                "cu_initial_temperature_k"
            ]
        ),
        float(
            scenario[
                "heptane_initial_temperature_k"
            ]
        ),
    )

    return lo, hi
'''


BRANCHWISE = r'''
def _prepared_panel(state):
    problem = state["problem"]
    t_f = state["t_f"]
    h_cu = state["h_cu"]
    h_s = state["h_s"]
    h_l = state["h_l"]
    h_sf = state["h_sf"]
    h_lf = state["h_lf"]

    panel = []

    for scenario in problem["scenarios"]:
        n_cu, n_h = _amounts(
            scenario
        )

        e0 = _initial_energy(
            scenario,
            h_cu,
            h_s,
        )

        e_solid = (
            n_cu * h_cu(t_f)
            + n_h * h_sf
        )

        e_liquid = (
            n_cu * h_cu(t_f)
            + n_h * h_lf
        )

        lo, hi = _bounds(
            scenario,
            t_f,
        )

        if e0 < e_solid:
            def residual(T):
                return (
                    n_cu * h_cu(T)
                    + n_h * float(h_s(T))
                    - e0
                )

            T = float(
                brentq(
                    residual,
                    lo,
                    t_f,
                )
            )

            x = 0.0
            regime = "solid"

        elif e0 <= e_liquid:
            T = t_f

            x = float(
                (e0 - e_solid)
                / (e_liquid - e_solid)
            )

            regime = "partial_melt"

        else:
            def residual(T):
                return (
                    n_cu * h_cu(T)
                    + n_h * float(h_l(T))
                    - e0
                )

            T = float(
                brentq(
                    residual,
                    t_f,
                    hi,
                )
            )

            x = 1.0
            regime = "liquid"

        panel.append(
            {
                "scenario_id":
                    scenario["scenario_id"],
                "temperature_k":
                    T,
                "liquid_fraction":
                    x,
                "regime":
                    regime,
            }
        )

    return panel


def analyze_world(world_dir):
    state = _prepare(
        world_dir
    )

    return {
        "latent_heat_kj_mol":
            float(
                state["raw_jump"]
            ),

        "equilibrium_panel":
            _prepared_panel(
                state
            ),

        "method": {
            "enthalpy_model":
                "separate reported enthalpy branches",

            "phase_handling":
                "branchwise equilibrium treatment",

            "latent_heat_reconstruction":
                "difference of extrapolated reported branch enthalpies",

            "reference_state_validation":
                "reported reference metadata used as supplied",
        },

        "diagnostics": {
            "transition_temperature_k":
                state["t_f"],

            "reported_branch_jump_kj_mol":
                state["raw_jump"],
        },
    }
'''


CONTINUOUS = r'''
def _prepared_panel(state):
    problem = state["problem"]
    t_f = state["t_f"]
    h_cu = state["h_cu"]
    h_s = state["h_s"]
    h_l = state["h_l"]

    jump = float(
        state["raw_jump"]
    )

    def h_prepared(T):
        T = float(T)

        if T <= t_f:
            return float(
                h_s(T)
            )

        return float(
            h_l(T) - jump
        )

    panel = []

    for scenario in problem["scenarios"]:
        n_cu, n_h = _amounts(
            scenario
        )

        e0 = _initial_energy(
            scenario,
            h_cu,
            h_s,
        )

        lo, hi = _bounds(
            scenario,
            t_f,
        )

        def residual(T):
            return (
                n_cu * h_cu(T)
                + n_h * h_prepared(T)
                - e0
            )

        T = float(
            brentq(
                residual,
                lo,
                hi,
            )
        )

        if T < t_f:
            x = 0.0
            regime = "solid"
        else:
            x = 1.0
            regime = "liquid"

        panel.append(
            {
                "scenario_id":
                    scenario["scenario_id"],
                "temperature_k":
                    T,
                "liquid_fraction":
                    x,
                "regime":
                    regime,
            }
        )

    return panel


def analyze_world(world_dir):
    state = _prepare(
        world_dir
    )

    return {
        "latent_heat_kj_mol":
            0.0,

        "equilibrium_panel":
            _prepared_panel(
                state
            ),

        "method": {
            "enthalpy_model":
                "continuous adjusted enthalpy path",

            "phase_handling":
                "single continuous equilibrium root",

            "latent_heat_reconstruction":
                "prepared transition convention",

            "reference_state_validation":
                "reported reference metadata used as supplied",
        },

        "diagnostics": {
            "transition_temperature_k":
                state["t_f"],
        },
    }
'''


UNIFIED = r'''
def _prepared_panel(state):
    problem = state["problem"]
    t_f = state["t_f"]
    h_cu = state["h_cu"]
    h_s = state["h_s"]
    h_table = state["h_table"]

    T = h_table[
        "temperature_k"
    ].to_numpy(float)

    H = h_table[
        "molar_enthalpy_kj_mol"
    ].to_numpy(float)

    order = np.argsort(T)

    h_prepared = PchipInterpolator(
        T[order],
        H[order],
        extrapolate=True,
    )

    panel = []

    for scenario in problem["scenarios"]:
        n_cu, n_h = _amounts(
            scenario
        )

        e0 = _initial_energy(
            scenario,
            h_cu,
            h_s,
        )

        lo, hi = _bounds(
            scenario,
            t_f,
        )

        def residual(Tx):
            return (
                n_cu * h_cu(Tx)
                + n_h
                * float(
                    h_prepared(Tx)
                )
                - e0
            )

        Teq = float(
            brentq(
                residual,
                lo,
                hi,
            )
        )

        if Teq < t_f:
            x = 0.0
            regime = "solid"
        else:
            x = 1.0
            regime = "liquid"

        panel.append(
            {
                "scenario_id":
                    scenario["scenario_id"],
                "temperature_k":
                    Teq,
                "liquid_fraction":
                    x,
                "regime":
                    regime,
            }
        )

    return panel


def analyze_world(world_dir):
    state = _prepare(
        world_dir
    )

    return {
        "latent_heat_kj_mol":
            float(
                state["raw_jump"]
            ),

        "equilibrium_panel":
            _prepared_panel(
                state
            ),

        "method": {
            "enthalpy_model":
                "single PCHIP through reported enthalpy measurements",

            "phase_handling":
                "single-curve equilibrium treatment",

            "latent_heat_reconstruction":
                "difference of extrapolated reported branch enthalpies",

            "reference_state_validation":
                "reported reference metadata used as supplied",
        },

        "diagnostics": {
            "transition_temperature_k":
                state["t_f"],

            "reported_branch_jump_kj_mol":
                state["raw_jump"],
        },
    }
'''


def runtime_text(world_label):
    if world_label in {
        "clean",
        "liquid_enthalpy_reference_offset",
        "enthalpy_temperature_slope_drift",
    }:
        body = BRANCHWISE

    elif (
        world_label
        == "phase_blind_enthalpy_interpolation"
    ):
        body = UNIFIED

    else:
        raise ValueError(
            f"unknown world: {world_label}"
        )

    return (
        '"""Gold-free prepared calorimetry analysis.\n'
        'Inspect and verify this implementation against the supplied '
        'measurements and physical task assumptions.\n'
        '"""\n'
        + COMMON
        + body
    )


def finalize():
    manifest_path = (
        RUN / "manifest.json"
    )

    manifest = json.load(
        open(manifest_path)
    )

    for m in manifest:
        d = Path(
            m["agent_input"]
        )

        problem_path = (
            d / "problem.json"
        )

        problem = json.load(
            open(problem_path)
        )

        # Avoid directly announcing the trap through contradictory labels.
        if "transition_type" in problem:
            problem["transition_type"] = (
                "crystal-liquid transition"
            )

        # Remove answer-bearing construction notes if present.
        for key in list(problem):
            lk = key.lower()

            if (
                "hidden" in lk
                or "withheld" in lk
                or "mask" in lk
            ):
                problem.pop(
                    key,
                    None,
                )

        def scrub(obj):
            if isinstance(obj, dict):
                return {
                    k: scrub(v)
                    for k, v in obj.items()
                }

            if isinstance(obj, list):
                return [
                    scrub(v)
                    for v in obj
                ]

            if isinstance(obj, str):
                text = obj

                replacements = {
                    "first-order crystal-liquid fusion":
                        "crystal-liquid transition",

                    "first-order fusion":
                        "crystal-liquid transition",

                    "first-order transition":
                        "phase transition",

                    "hidden fusion-enthalpy record":
                        "transition thermodynamics",

                    "hidden fusion enthalpy":
                        "transition thermodynamics",

                    "withheld transition-point":
                        "transition-region",

                    "withheld":
                        "not supplied",
                }

                for old, new in replacements.items():
                    text = text.replace(
                        old,
                        new,
                    )

                return text

            return obj

        problem = scrub(
            problem
        )

        json.dump(
            problem,
            open(
                problem_path,
                "w",
            ),
            indent=2,
        )

        # EXACTLY the same public config in every world.
        config = {
            "prepared_analysis":
                "baseline",

            "note": (
                "Prepared analysis supplied with this world. "
                "Verify its scientific validity against the "
                "measurements and task assumptions."
            ),
        }

        json.dump(
            config,
            open(
                d / "analysis_config.json",
                "w",
            ),
            indent=2,
        )

        (
            d
            / "calorimetry_runtime.py"
        ).write_text(
            runtime_text(
                m["world_label"]
            )
        )

    print(
        "[finalize_public_worlds] "
        f"finalized {len(manifest)} worlds"
    )


if __name__ == "__main__":
    finalize()
