from pathlib import Path
import csv
import json

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq


ROOT = Path("tracks/calorimetry")
L2 = ROOT / "L2"

LANG = ROOT / "calorimetry_raw.json"
HEP = ROOT / "candidate_data" / "bissengaliyeva_2011.json"

GOLD_DIR = L2 / "gold"
GOLD_DIR.mkdir(parents=True, exist_ok=True)

M_CU = 63.546
M_HEP = 100.205

# Frozen before benchmark-model evaluation.
REFERENCE_OFFSET = 0.500  # kJ/mol

# Frozen after the predeclared +6/+8 screen.
SLOPE_DRIFT_ALPHA_J_MOL_K = 6.0
SLOPE_DRIFT_REFERENCE_T_K = 0.0


THRESHOLDS = {
    "latent_heat_kj_mol": {
        "3": 0.08,
        "2": 0.20,
        "1": 0.60,
    },
    "temperature_k_max_abs": {
        "3": 0.25,
        "2": 0.75,
        "1": 2.00,
    },
    "liquid_fraction_max_abs": {
        "3": 0.004,
        "2": 0.020,
        "1": 0.50,
    },
    "regime_errors": {
        "3": 0,
        "2": 1,
        "1": 3,
    },
}


# partial_mid replaces the duplicate 100/50 scenario.
SCENARIOS = [
    {
        "scenario_id": "solid_low",
        "cu_mass_g": 100.0,
        "heptane_mass_g": 100.0,
        "cu_initial_temperature_k": 220.0,
        "heptane_initial_temperature_k": 150.0,
    },
    {
        "scenario_id": "solid_high",
        "cu_mass_g": 100.0,
        "heptane_mass_g": 100.0,
        "cu_initial_temperature_k": 260.0,
        "heptane_initial_temperature_k": 150.0,
    },
    {
        "scenario_id": "partial_low",
        "cu_mass_g": 100.0,
        "heptane_mass_g": 100.0,
        "cu_initial_temperature_k": 300.0,
        "heptane_initial_temperature_k": 175.0,
    },
    {
        "scenario_id": "partial_mid",
        "cu_mass_g": 150.0,
        "heptane_mass_g": 100.0,
        "cu_initial_temperature_k": 300.0,
        "heptane_initial_temperature_k": 175.0,
    },
    {
        "scenario_id": "partial_high",
        "cu_mass_g": 200.0,
        "heptane_mass_g": 100.0,
        "cu_initial_temperature_k": 300.0,
        "heptane_initial_temperature_k": 175.0,
    },
    {
        "scenario_id": "liquid",
        "cu_mass_g": 400.0,
        "heptane_mass_g": 100.0,
        "cu_initial_temperature_k": 300.0,
        "heptane_initial_temperature_k": 175.0,
    },
]


def table(block):
    T = []
    Y = []

    for row in block["NumValues"]:
        vv = row.get("VariableValue", [])
        pv = row.get("PropertyValue", [])

        if not vv or not pv:
            continue

        T.append(float(vv[0]["nVarValue"]))
        Y.append(float(pv[0]["nPropValue"]))

    T = np.asarray(T, float)
    Y = np.asarray(Y, float)

    order = np.argsort(T)
    return T[order], Y[order]


def scalar(block):
    return float(
        block["NumValues"][0]
        ["PropertyValue"][0]["nPropValue"]
    )


def local_poly_limit(T, Y, target, side, degree, n):
    if side == "left":
        tx = T[-n:]
        yx = Y[-n:]
    else:
        tx = T[:n]
        yx = Y[:n]

    degree = min(degree, len(tx) - 1)

    p = np.polyfit(
        tx,
        yx,
        degree,
    )

    return float(
        np.polyval(p, target)
    )


# ============================================================
# Load real public substrates
# ============================================================

DL = json.loads(LANG.read_text())
DH = json.loads(HEP.read_text())

BL = DL["PureOrMixtureData"]
BH = DH["PureOrMixtureData"]

TFUS = scalar(BH[9])
DIRECT_DHFUS = scalar(BH[8])

# Lang 2006 Cu Cp: longitudinal L1 -> L2 substrate.
Tcu, Cpcu = table(BL[0])

# Bissengaliyeva 2011 heptane.
THs0, Hs0 = table(BH[14])
THl0, Hl0 = table(BH[15])

TSs0, Ss0 = table(BH[16])
TSl0, Sl0 = table(BH[17])

TCps0, Cps0 = table(BH[10])
TCpl0, Cpl0 = table(BH[11])


# ============================================================
# Hidden real transition endpoints
# ============================================================

i_hs = int(
    np.argmin(
        np.abs(THs0 - TFUS)
    )
)

i_hl = int(
    np.argmin(
        np.abs(THl0 - TFUS)
    )
)

H_SOLID_GOLD = float(
    Hs0[i_hs]
)

H_LIQUID_GOLD = float(
    Hl0[i_hl]
)

ENDPOINT_DHFUS = (
    H_LIQUID_GOLD
    - H_SOLID_GOLD
)


# ============================================================
# Agent-visible masked rows
#
# Explicit transition H endpoints are hidden.
# Exact S transition endpoints are hidden too if present.
# ============================================================

keep_hs = (
    THs0
    < TFUS - 1e-8
)

keep_hl = (
    THl0
    > TFUS + 1e-8
)

keep_ss = (
    TSs0
    < TFUS - 1e-8
)

keep_sl = (
    TSl0
    > TFUS + 1e-8
)

THs = THs0[keep_hs]
Hs = Hs0[keep_hs]

THl = THl0[keep_hl]
Hl = Hl0[keep_hl]

TSs = TSs0[keep_ss]
Ss = Ss0[keep_ss]

TSl = TSl0[keep_sl]
Sl = Sl0[keep_sl]


# ============================================================
# Lang Cu sensible enthalpy
# ============================================================

CP_CU = PchipInterpolator(
    Tcu,
    Cpcu,
    extrapolate=False,
)

INT_CU = CP_CU.antiderivative()

CU_REF_T = float(
    Tcu.min()
)


def Hcu(T):
    return float(
        (
            INT_CU(T)
            - INT_CU(CU_REF_T)
        )
        / 1000.0
    )


# ============================================================
# Gold vs visible phase branches
# ============================================================

# Hidden gold uses the ACTUAL full real branches.
GOLD_HS = PchipInterpolator(
    THs0,
    Hs0,
    extrapolate=False,
)

GOLD_HL = PchipInterpolator(
    THl0,
    Hl0,
    extrapolate=False,
)

# Agent-visible reconstruction uses only masked rows.
BASE_HS = PchipInterpolator(
    THs,
    Hs,
    extrapolate=True,
)

BASE_HL = PchipInterpolator(
    THl,
    Hl,
    extrapolate=True,
)


# ============================================================
# Entropy consistency
#
# At phase equilibrium:
#
#   dH_fus = T_fus * dS_fus
# ============================================================

S_SOLID = PchipInterpolator(
    TSs,
    Ss,
    extrapolate=True,
)

S_LIQUID = PchipInterpolator(
    TSl,
    Sl,
    extrapolate=True,
)

DELTA_S_VISIBLE = float(
    S_LIQUID(TFUS)
    - S_SOLID(TFUS)
)

DHFUS_FROM_TS = (
    TFUS
    * DELTA_S_VISIBLE
    / 1000.0
)


# Canonical robust clean reconstruction.
REFERENCE_HSF = local_poly_limit(
    THs,
    Hs,
    TFUS,
    side="left",
    degree=2,
    n=8,
)

REFERENCE_HLF = (
    REFERENCE_HSF
    + DHFUS_FROM_TS
)


def make_model(
    HS,
    HL,
    Hsf,
    Hlf,
):
    return {
        "HS": HS,
        "HL": HL,
        "Hsf": float(Hsf),
        "Hlf": float(Hlf),
        "latent_heat_kj_mol": float(
            Hlf - Hsf
        ),
    }


GOLD_MODEL = make_model(
    GOLD_HS,
    GOLD_HL,
    H_SOLID_GOLD,
    H_LIQUID_GOLD,
)

REFERENCE_MODEL = make_model(
    BASE_HS,
    BASE_HL,
    REFERENCE_HSF,
    REFERENCE_HLF,
)


# ============================================================
# Correct phase-resolved equilibrium solver
# ============================================================

def solve_phase_resolved(
    phase_model,
    scenario,
):
    HS = phase_model["HS"]
    HL = phase_model["HL"]

    Hsf = phase_model["Hsf"]
    Hlf = phase_model["Hlf"]

    ncu = (
        scenario["cu_mass_g"]
        / M_CU
    )

    nh = (
        scenario["heptane_mass_g"]
        / M_HEP
    )

    Tcu0 = (
        scenario[
            "cu_initial_temperature_k"
        ]
    )

    Thep0 = (
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
        ncu * Hcu(TFUS)
        +
        nh * Hsf
    )

    Eliquid = (
        ncu * Hcu(TFUS)
        +
        nh * Hlf
    )

    # -----------------------------
    # Solid equilibrium
    # -----------------------------

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
                Tcu.min()
            ),
            float(
                THs.min()
            ),
        )

        T = brentq(
            f,
            lo,
            TFUS,
        )

        return {
            "temperature_k": float(T),
            "liquid_fraction": 0.0,
            "regime": "solid",
        }

    # -----------------------------
    # Two-phase equilibrium
    # -----------------------------

    if E0 <= Eliquid:

        x = (
            E0 - Esolid
        ) / (
            Eliquid - Esolid
        )

        return {
            "temperature_k": float(TFUS),
            "liquid_fraction": float(x),
            "regime": "partial_melt",
        }

    # -----------------------------
    # Liquid equilibrium
    # -----------------------------

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
            Tcu.max()
        ),
        float(
            THl.max()
        ),
    )

    T = brentq(
        f,
        TFUS,
        hi,
    )

    return {
        "temperature_k": float(T),
        "liquid_fraction": 1.0,
        "regime": "liquid",
    }


def panel(phase_model):
    return {
        scenario["scenario_id"]:
        solve_phase_resolved(
            phase_model,
            scenario,
        )
        for scenario
        in SCENARIOS
    }


GOLD_PANEL = panel(
    GOLD_MODEL
)

REFERENCE_PANEL = panel(
    REFERENCE_MODEL
)


# ============================================================
# DATA CONFOUND SCREEN:
# temperature-dependent reported-enthalpy slope drift
#
# H_reported(T) = H_true(T) + alpha * (T - 0 K) / 1000
#
# The 0 K pivot preserves the stated crystal reference origin and
# keeps all reported H values positive/monotone for these settings.
# The same drift is applied to both visible phase branches, so the
# same-temperature fusion jump stays approximately intact while
# dH/dT disagrees with independently measured Cp(T).
# ============================================================


def _dedupe_xy(T, Y):
    T = np.asarray(T, float)
    Y = np.asarray(Y, float)
    order = np.argsort(T)
    T = T[order]
    Y = Y[order]
    uniq, inv = np.unique(T, return_inverse=True)
    sums = np.zeros(len(uniq), float)
    counts = np.zeros(len(uniq), int)
    for i, j in enumerate(inv):
        sums[j] += Y[i]
        counts[j] += 1
    return uniq, sums / counts


def estimate_phase_drift_alpha(TH, Hvals, TCp, Cpvals):
    TCp, Cpvals = _dedupe_xy(TCp, Cpvals)
    cp_interp = PchipInterpolator(TCp, Cpvals, extrapolate=True)
    cp_int = cp_interp.antiderivative()
    t0 = float(TH[0])
    integrated_cp = np.asarray([
        (cp_int(float(T)) - cp_int(t0)) / 1000.0
        for T in TH
    ], float)
    residual_h = np.asarray(Hvals, float) - integrated_cp
    x = np.asarray(TH, float) - t0
    slope, _ = np.polyfit(x, residual_h, 1)
    return float(slope * 1000.0)


def make_slope_drift_case(alpha):
    hs_bad = Hs + alpha / 1000.0 * (THs - SLOPE_DRIFT_REFERENCE_T_K)
    hl_bad = Hl + alpha / 1000.0 * (THl - SLOPE_DRIFT_REFERENCE_T_K)

    hs_bad_interp = PchipInterpolator(THs, hs_bad, extrapolate=True)
    hl_bad_interp = PchipInterpolator(THl, hl_bad, extrapolate=True)

    naive_hsf = float(hs_bad_interp(TFUS))
    naive_hlf = float(hl_bad_interp(TFUS))
    naive_model = make_model(
        hs_bad_interp, hl_bad_interp, naive_hsf, naive_hlf
    )

    alpha_s = estimate_phase_drift_alpha(THs, hs_bad, TCps0, Cps0)
    alpha_l = estimate_phase_drift_alpha(THl, hl_bad, TCpl0, Cpl0)
    alpha_est = float(0.5 * (alpha_s + alpha_l))

    hs_corrected = hs_bad - alpha_est / 1000.0 * (
        THs - SLOPE_DRIFT_REFERENCE_T_K
    )
    hl_corrected = hl_bad - alpha_est / 1000.0 * (
        THl - SLOPE_DRIFT_REFERENCE_T_K
    )

    hs_corrected_interp = PchipInterpolator(
        THs, hs_corrected, extrapolate=True
    )
    hl_corrected_interp = PchipInterpolator(
        THl, hl_corrected, extrapolate=True
    )

    corrected_hsf = local_poly_limit(
        THs, hs_corrected, TFUS, side="left", degree=2, n=8
    )
    corrected_hlf = corrected_hsf + DHFUS_FROM_TS
    robust_model = make_model(
        hs_corrected_interp,
        hl_corrected_interp,
        corrected_hsf,
        corrected_hlf,
    )

    return {
        "alpha_injected_j_mol_k": float(alpha),
        "alpha_est_crystal_j_mol_k": float(alpha_s),
        "alpha_est_liquid_j_mol_k": float(alpha_l),
        "alpha_est_common_j_mol_k": float(alpha_est),
        "naive_model": naive_model,
        "naive_panel": panel(naive_model),
        "robust_model": robust_model,
        "robust_panel": panel(robust_model),
    }


SLOPE_DRIFT_CASE = make_slope_drift_case(
    SLOPE_DRIFT_ALPHA_J_MOL_K
)


# ============================================================
# TOOL TRAP 1:
# omit latent heat
# ============================================================

BASE_HSF = float(
    BASE_HS(TFUS)
)

BASE_HLF = float(
    BASE_HL(TFUS)
)

BASE_JUMP = (
    BASE_HLF
    - BASE_HSF
)


def H_no_latent(T):
    if T <= TFUS:
        return float(
            BASE_HS(T)
        )

    return float(
        BASE_HL(T)
    ) - BASE_JUMP


def solve_no_latent(
    scenario,
):
    ncu = (
        scenario["cu_mass_g"]
        / M_CU
    )

    nh = (
        scenario["heptane_mass_g"]
        / M_HEP
    )

    Tcu0 = (
        scenario[
            "cu_initial_temperature_k"
        ]
    )

    Thep0 = (
        scenario[
            "heptane_initial_temperature_k"
        ]
    )

    E0 = (
        ncu * Hcu(Tcu0)
        +
        nh * H_no_latent(
            Thep0
        )
    )

    def f(T):
        return (
            ncu * Hcu(T)
            +
            nh * H_no_latent(T)
            -
            E0
        )

    lo = max(
        min(
            Tcu0,
            Thep0,
        ),
        float(
            Tcu.min()
        ),
        float(
            THs.min()
        ),
    )

    hi = min(
        max(
            Tcu0,
            Thep0,
        ),
        float(
            Tcu.max()
        ),
        float(
            THl.max()
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
        "temperature_k": T,
        "liquid_fraction":
            0.0
            if T < TFUS
            else 1.0,
        "regime":
            "solid"
            if T < TFUS
            else "liquid",
    }


NO_LATENT_PANEL = {
    scenario["scenario_id"]:
    solve_no_latent(
        scenario
    )
    for scenario
    in SCENARIOS
}


# ============================================================
# TOOL TRAP 2:
# phase-blind H(T) interpolation
# ============================================================

Tblind = np.r_[
    THs,
    THl,
]

Hblind_values = np.r_[
    Hs,
    Hl,
]

order = np.argsort(
    Tblind
)

Tblind = Tblind[order]
Hblind_values = (
    Hblind_values[order]
)

HBLIND = PchipInterpolator(
    Tblind,
    Hblind_values,
    extrapolate=False,
)


def solve_phase_blind(
    scenario,
):
    ncu = (
        scenario["cu_mass_g"]
        / M_CU
    )

    nh = (
        scenario["heptane_mass_g"]
        / M_HEP
    )

    Tcu0 = (
        scenario[
            "cu_initial_temperature_k"
        ]
    )

    Thep0 = (
        scenario[
            "heptane_initial_temperature_k"
        ]
    )

    E0 = (
        ncu * Hcu(Tcu0)
        +
        nh * float(
            HBLIND(Thep0)
        )
    )

    def f(T):
        return (
            ncu * Hcu(T)
            +
            nh * float(
                HBLIND(T)
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
            Tcu.min()
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
            Tcu.max()
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
        "temperature_k": T,
        "liquid_fraction":
            0.0
            if T < TFUS
            else 1.0,
        "regime":
            "solid"
            if T < TFUS
            else "liquid",
    }


PHASE_BLIND_PANEL = {
    scenario["scenario_id"]:
    solve_phase_blind(
        scenario
    )
    for scenario
    in SCENARIOS
}


# ============================================================
# DATA CONFOUND:
# +0.500 kJ/mol liquid-H reference offset
# ============================================================

Hl_bad = (
    Hl
    + REFERENCE_OFFSET
)

BAD_HL = PchipInterpolator(
    THl,
    Hl_bad,
    extrapolate=True,
)

BAD_HSF = BASE_HSF

BAD_HLF = float(
    BAD_HL(TFUS)
)

BAD_MODEL = make_model(
    BASE_HS,
    BAD_HL,
    BAD_HSF,
    BAD_HLF,
)


# Thermodynamic repair from H/S consistency.
observed_jump = (
    BAD_HLF
    - BAD_HSF
)

estimated_reference_offset = (
    observed_jump
    - DHFUS_FROM_TS
)

Hl_corrected = (
    Hl_bad
    - estimated_reference_offset
)

CORRECTED_HL = (
    PchipInterpolator(
        THl,
        Hl_corrected,
        extrapolate=True,
    )
)

CORRECTED_HSF = (
    BASE_HSF
)

CORRECTED_HLF = float(
    CORRECTED_HL(TFUS)
)

CORRECTED_MODEL = (
    make_model(
        BASE_HS,
        CORRECTED_HL,
        CORRECTED_HSF,
        CORRECTED_HLF,
    )
)

BAD_PANEL = panel(
    BAD_MODEL
)

CORRECTED_PANEL = panel(
    CORRECTED_MODEL
)


# ============================================================
# Accuracy scoring
# ============================================================

def component_score(
    error,
    cuts,
):
    if error <= cuts["3"]:
        return 3

    if error <= cuts["2"]:
        return 2

    if error <= cuts["1"]:
        return 1

    return 0


def regime_score(
    n_errors,
):
    cuts = (
        THRESHOLDS[
            "regime_errors"
        ]
    )

    if n_errors <= cuts["3"]:
        return 3

    if n_errors <= cuts["2"]:
        return 2

    if n_errors <= cuts["1"]:
        return 1

    return 0


def score_accuracy(
    latent_heat_kj_mol,
    candidate_panel,
):
    dH_error = abs(
        latent_heat_kj_mol
        - DIRECT_DHFUS
    )

    max_dt = 0.0
    max_dx = 0.0
    regime_errors = 0

    for sid, gold in (
        GOLD_PANEL.items()
    ):
        cand = (
            candidate_panel[sid]
        )

        max_dt = max(
            max_dt,
            abs(
                cand["temperature_k"]
                - gold["temperature_k"]
            ),
        )

        max_dx = max(
            max_dx,
            abs(
                cand["liquid_fraction"]
                - gold["liquid_fraction"]
            ),
        )

        regime_errors += (
            cand["regime"]
            != gold["regime"]
        )

    scores = {
        "latent_heat":
            component_score(
                dH_error,
                THRESHOLDS[
                    "latent_heat_kj_mol"
                ],
            ),
        "temperature":
            component_score(
                max_dt,
                THRESHOLDS[
                    "temperature_k_max_abs"
                ],
            ),
        "liquid_fraction":
            component_score(
                max_dx,
                THRESHOLDS[
                    "liquid_fraction_max_abs"
                ],
            ),
        "regime":
            regime_score(
                regime_errors
            ),
    }

    return {
        "accuracy":
            min(
                scores.values()
            ),
        "components":
            scores,
        "latent_heat_abs_error_kj_mol":
            dH_error,
        "max_temperature_abs_error_k":
            max_dt,
        "max_liquid_fraction_abs_error":
            max_dx,
        "regime_errors":
            int(
                regime_errors
            ),
    }


# ============================================================
# Solver fire checks
# ============================================================

checks = {
    "clean_robust":
        score_accuracy(
            REFERENCE_MODEL[
                "latent_heat_kj_mol"
            ],
            REFERENCE_PANEL,
        ),

    "reference_offset_naive":
        score_accuracy(
            BAD_MODEL[
                "latent_heat_kj_mol"
            ],
            BAD_PANEL,
        ),

    "reference_offset_robust":
        score_accuracy(
            CORRECTED_MODEL[
                "latent_heat_kj_mol"
            ],
            CORRECTED_PANEL,
        ),

    "slope_drift_naive":
        score_accuracy(
            SLOPE_DRIFT_CASE[
                "naive_model"
            ]["latent_heat_kj_mol"],
            SLOPE_DRIFT_CASE[
                "naive_panel"
            ],
        ),

    "slope_drift_robust":
        score_accuracy(
            SLOPE_DRIFT_CASE[
                "robust_model"
            ]["latent_heat_kj_mol"],
            SLOPE_DRIFT_CASE[
                "robust_panel"
            ],
        ),

    # Deliberately give this trap its inferred latent heat.
    # The failure being tested is phase handling, not failure
    # to estimate the size of the enthalpy rise.
    "phase_blind_naive":
        score_accuracy(
            BASE_JUMP,
            PHASE_BLIND_PANEL,
        ),

    "phase_blind_robust":
        score_accuracy(
            REFERENCE_MODEL[
                "latent_heat_kj_mol"
            ],
            REFERENCE_PANEL,
        ),
}


expected = {
    "clean_robust": 3,
    "reference_offset_naive": 1,
    "reference_offset_robust": 3,
    "slope_drift_naive": 1,
    "slope_drift_robust": 3,
    "phase_blind_naive": 1,
    "phase_blind_robust": 3,
}


# ============================================================
# Audit output
# ============================================================

print(
    "=" * 100
)

print(
    "CALORIMETRY L2 — "
    "PHASE TRANSITION REFERENCE SOLVER"
)

print(
    "=" * 100
)

print(
    f"Tfus                 = "
    f"{TFUS:.6f} K"
)

print(
    f"hidden endpoint dH   = "
    f"{ENDPOINT_DHFUS:.6f} kJ/mol"
)

print(
    f"direct ThermoML dH   = "
    f"{DIRECT_DHFUS:.6f} kJ/mol"
)

print(
    f"reference T*dS dH    = "
    f"{DHFUS_FROM_TS:.6f} kJ/mol"
)

print(
    f"data-confound offset = "
    f"{REFERENCE_OFFSET:+.6f} kJ/mol"
)

print(
    f"recovered offset     = "
    f"{estimated_reference_offset:+.6f} kJ/mol"
)

case = SLOPE_DRIFT_CASE
print(
    f"slope drift selected  = "
    f"injected {case['alpha_injected_j_mol_k']:+.3f}, "
    f"estimated crystal {case['alpha_est_crystal_j_mol_k']:+.3f}, "
    f"liquid {case['alpha_est_liquid_j_mol_k']:+.3f}, "
    f"common {case['alpha_est_common_j_mol_k']:+.3f} J/mol/K"
)

print()


for name, result in (
    checks.items()
):
    print(
        f"{name:<32} "
        f"acc={result['accuracy']} "
        f"dH={result['latent_heat_abs_error_kj_mol']:.6f} "
        f"maxT={result['max_temperature_abs_error_k']:.6f} "
        f"maxx={result['max_liquid_fraction_abs_error']:.6f} "
        f"regerr={result['regime_errors']} "
        f"components={result['components']}"
    )


failures = []

for key, want in (
    expected.items()
):
    got = (
        checks[key]["accuracy"]
    )

    if got != want:
        failures.append(
            f"{key}: "
            f"expected {want}, "
            f"got {got}"
        )


print()
print(
    "=" * 100
)

if failures:
    print(
        "FIRE CHECK: FAIL"
    )

    for failure in failures:
        print(
            "  -",
            failure,
        )

    raise SystemExit(1)


print(
    "FIRE CHECK: PASS"
)

print(
    "Expected accuracy separation "
    "achieved for clean + all three "
    "challenge families."
)


# ============================================================
# Write canonical gold only AFTER fire checks pass
# ============================================================

gold_json = {
    "analysis":
        "phase_resolved_adiabatic_equilibrium",

    "transition_temperature_k":
        TFUS,

    "hidden_crystal_enthalpy_at_transition_kj_mol":
        H_SOLID_GOLD,

    "hidden_liquid_enthalpy_at_transition_kj_mol":
        H_LIQUID_GOLD,

    "hidden_endpoint_latent_heat_kj_mol":
        ENDPOINT_DHFUS,

    "direct_thermoml_latent_heat_kj_mol":
        DIRECT_DHFUS,

    "reference_visible_delta_s_j_mol_k":
        DELTA_S_VISIBLE,

    "reference_visible_t_delta_s_kj_mol":
        DHFUS_FROM_TS,

    "data_confound_liquid_enthalpy_offset_kj_mol":
        REFERENCE_OFFSET,

    "data_confound_enthalpy_slope_drift_j_mol_k":
        SLOPE_DRIFT_ALPHA_J_MOL_K,

    "data_confound_enthalpy_slope_reference_temperature_k":
        SLOPE_DRIFT_REFERENCE_T_K,

    "thresholds":
        THRESHOLDS,

    "scenarios": [
        {
            **scenario,
            **GOLD_PANEL[
                scenario[
                    "scenario_id"
                ]
            ],
        }
        for scenario
        in SCENARIOS
    ],

    "fire_checks":
        checks,
}


with open(
    GOLD_DIR / "gold_solver.json",
    "w",
) as f:
    json.dump(
        gold_json,
        f,
        indent=2,
    )


with open(
    GOLD_DIR / "equilibrium_scenarios.csv",
    "w",
    newline="",
) as f:

    fields = [
        "scenario_id",
        "cu_mass_g",
        "heptane_mass_g",
        "cu_initial_temperature_k",
        "heptane_initial_temperature_k",
        "temperature_k",
        "liquid_fraction",
        "regime",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
    )

    writer.writeheader()

    for scenario in SCENARIOS:
        sid = (
            scenario[
                "scenario_id"
            ]
        )

        writer.writerow(
            {
                **scenario,
                **GOLD_PANEL[sid],
            }
        )


print()

print(
    "WROTE:",
    GOLD_DIR
    / "gold_solver.json",
)

print(
    "WROTE:",
    GOLD_DIR
    / "equilibrium_scenarios.csv",
)
