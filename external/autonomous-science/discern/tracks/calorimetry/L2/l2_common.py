"""
Calorimetry L2 v2 — scientific core.

PRE-FREEZE implementation.

Design
------
One end-to-end thermodynamic analysis:

    Cp(T) construction
        ->
    prediction of withheld REAL ThermoML Cp measurements
        ->
    enthalpy integration
        ->
    multi-scenario equilibrium prediction
        ->
    uncertainty propagation

World definitions are NOT encoded here except for the single
heteroskedastic-input injection needed by the reference solver.

The final agent runtime will be gold-free and will NOT expose injection
parameters.
"""

from pathlib import Path

import json

import numpy as np
import pandas as pd

from scipy.interpolate import (
    LSQUnivariateSpline,
    PchipInterpolator,
)
from scipy.optimize import brentq


# =====================================================================
# Paths / fixed physical constants
# =====================================================================

HERE = Path(__file__).resolve().parent
TRACK = HERE.parent

L1_WORLD = (
    TRACK
    / "L1"
    / "results"
    / "calorimetry_l1_run"
    / "data"
    / "cell000"
)

L1_CLEAN = (
    L1_WORLD
    / "heat_capacity.csv.gz"
)

L1_META = (
    L1_WORLD
    / "measurement_meta.json"
)


MATERIALS = (
    "Cu",
    "Al2O3",
    "C7H6O2",
)


MOLAR_MASS_G_MOL = {
    "Cu": 63.546,
    "Al2O3": 101.961,
    "C7H6O2": 122.123,
}


FIT_T_MIN_K = 90.0
FIT_T_MAX_K = 310.0

KNOT_SPACING_K = 50.0

Z95 = 1.96


# Existing solver-validated DATA-CONFOUND intervention.
#
# These values remain builder/verifier-side. They will NOT be copied
# into the agent-visible runtime.
HETERO_T_MIN_K = 170.0
HETERO_T_MAX_K = 230.0
HETERO_CP_OFFSET_J_MOL_K = 6.0
HETERO_UNCERTAINTY_FACTOR = 20.0


SCENARIOS = [
    {
        "scenario_id": "cu_al_anchor",
        "hot_material": "Cu",
        "hot_mass_g": 100.0,
        "hot_temperature_k": 300.0,
        "cold_material": "Al2O3",
        "cold_mass_g": 100.0,
        "cold_temperature_k": 100.0,
    },
    {
        "scenario_id": "cu_al_hot_light",
        "hot_material": "Cu",
        "hot_mass_g": 60.0,
        "hot_temperature_k": 300.0,
        "cold_material": "Al2O3",
        "cold_mass_g": 140.0,
        "cold_temperature_k": 120.0,
    },
    {
        "scenario_id": "cu_al_hot_heavy",
        "hot_material": "Cu",
        "hot_mass_g": 160.0,
        "hot_temperature_k": 260.0,
        "cold_material": "Al2O3",
        "cold_mass_g": 40.0,
        "cold_temperature_k": 120.0,
    },
    {
        "scenario_id": "cu_al_narrow_span",
        "hot_material": "Cu",
        "hot_mass_g": 100.0,
        "hot_temperature_k": 250.0,
        "cold_material": "Al2O3",
        "cold_mass_g": 100.0,
        "cold_temperature_k": 150.0,
    },
    {
        "scenario_id": "cu_benzoic",
        "hot_material": "Cu",
        "hot_mass_g": 100.0,
        "hot_temperature_k": 300.0,
        "cold_material": "C7H6O2",
        "cold_mass_g": 100.0,
        "cold_temperature_k": 150.0,
    },
    {
        "scenario_id": "al_benzoic",
        "hot_material": "Al2O3",
        "hot_mass_g": 100.0,
        "hot_temperature_k": 300.0,
        "cold_material": "C7H6O2",
        "cold_mass_g": 100.0,
        "cold_temperature_k": 150.0,
    },
]


# =====================================================================
# Real substrate
# =====================================================================

def load_clean():
    if not L1_CLEAN.exists():
        raise FileNotFoundError(
            f"missing frozen L1 clean substrate: {L1_CLEAN}"
        )

    df = pd.read_csv(
        L1_CLEAN
    )

    required = {
        "measurement_id",
        "formula",
        "temperature_k",
        "cp_j_mol_k",
        "cp_uncertainty_j_mol_k",
    }

    missing = (
        required
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            f"missing required columns: {sorted(missing)}"
        )

    out = df[
        df["formula"].isin(
            MATERIALS
        )
    ].copy()

    out = out[
        out["temperature_k"].between(
            FIT_T_MIN_K,
            FIT_T_MAX_K,
        )
    ].copy()

    out = (
        out
        .sort_values(
            [
                "formula",
                "temperature_k",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return out


def load_measurement_meta():
    if not L1_META.exists():
        raise FileNotFoundError(
            f"missing measurement metadata: {L1_META}"
        )

    with open(L1_META) as f:
        return json.load(f)


# =====================================================================
# Deterministic blocked real-data holdout
# =====================================================================

def split_clean(
    df,
):
    """
    Hide two contiguous temperature blocks PER MATERIAL.

    Selection is based only on temperature ordering, never on Cp value.
    """

    train = []
    test = []

    for material in MATERIALS:

        d = (
            df[
                df["formula"]
                == material
            ]
            .sort_values(
                "temperature_k"
            )
            .reset_index(
                drop=True
            )
        )

        n = len(d)

        frac = (
            np.arange(n)
            + 0.5
        ) / n

        hold = (
            (
                (frac >= 0.30)
                &
                (frac < 0.40)
            )
            |
            (
                (frac >= 0.65)
                &
                (frac < 0.75)
            )
        )

        train.append(
            d.loc[
                ~hold
            ].copy()
        )

        test.append(
            d.loc[
                hold
            ].copy()
        )

    train = pd.concat(
        train,
        ignore_index=True,
    )

    test = pd.concat(
        test,
        ignore_index=True,
    )

    return train, test


# =====================================================================
# DATA CONFOUND
# =====================================================================

def inject_heteroskedastic_segment(
    train,
):
    """
    Existing validated controlled delta.

    The hidden target remains the UNCORRUPTED real ThermoML data.
    """

    out = train.copy()

    mask = (
        (
            out["formula"]
            == "Al2O3"
        )
        &
        out[
            "temperature_k"
        ].between(
            HETERO_T_MIN_K,
            HETERO_T_MAX_K,
        )
    )

    out.loc[
        mask,
        "cp_j_mol_k",
    ] += (
        HETERO_CP_OFFSET_J_MOL_K
    )

    out.loc[
        mask,
        "cp_uncertainty_j_mol_k",
    ] *= (
        HETERO_UNCERTAINTY_FACTOR
    )

    return out


# =====================================================================
# Cp(T) representations
# =====================================================================

def _knots(
    x,
):
    lo = float(
        np.min(x)
    )

    hi = float(
        np.max(x)
    )

    knots = np.arange(
        100.0,
        301.0,
        KNOT_SPACING_K,
    )

    return knots[
        (
            knots
            > lo + 10.0
        )
        &
        (
            knots
            < hi - 10.0
        )
    ]


def fit_spline(
    d,
    weighting="uncertainty",
):
    d = (
        d
        .sort_values(
            "temperature_k"
        )
    )

    x = d[
        "temperature_k"
    ].to_numpy(
        float
    )

    y = d[
        "cp_j_mol_k"
    ].to_numpy(
        float
    )

    u = d[
        "cp_uncertainty_j_mol_k"
    ].to_numpy(
        float
    )

    kwargs = {}

    if weighting == "uncertainty":
        kwargs["w"] = (
            1.0
            /
            u
        )

    elif weighting == "equal":
        pass

    else:
        raise KeyError(
            f"unknown weighting: {weighting}"
        )

    return LSQUnivariateSpline(
        x,
        y,
        _knots(x),
        k=3,
        **kwargs,
    )


def fit_curves(
    train,
    weighting="uncertainty",
):
    curves = {}

    for material in MATERIALS:

        d = train[
            train["formula"]
            == material
        ]

        curves[
            material
        ] = fit_spline(
            d,
            weighting=weighting,
        )

    return curves


def fit_pchip_curves(
    train,
):
    out = {}

    for material in MATERIALS:

        d = (
            train[
                train["formula"]
                == material
            ]
            .sort_values(
                "temperature_k"
            )
        )

        out[material] = (
            PchipInterpolator(
                d[
                    "temperature_k"
                ].to_numpy(float),
                d[
                    "cp_j_mol_k"
                ].to_numpy(float),
                extrapolate=False,
            )
        )

    return out


# =====================================================================
# Prediction
# =====================================================================

def predict_targets(
    curves,
    targets,
):
    rows = []

    for _, r in (
        targets
        .iterrows()
    ):
        material = (
            r["formula"]
        )

        temp = float(
            r[
                "temperature_k"
            ]
        )

        pred = float(
            curves[
                material
            ](
                temp
            )
        )

        rows.append(
            {
                "measurement_id":
                    r[
                        "measurement_id"
                    ],

                "predicted_cp_j_mol_k":
                    pred,
            }
        )

    return pd.DataFrame(
        rows
    )


# =====================================================================
# Equilibrium physics
# =====================================================================

def _curve_integral(
    curve,
    a,
    b,
):
    """
    Integrate any supported Cp(T) representation.

    LSQUnivariateSpline uses .integral(a, b).
    PchipInterpolator uses .integrate(a, b).
    """

    if hasattr(
        curve,
        "integral",
    ):
        return float(
            curve.integral(
                a,
                b,
            )
        )

    if hasattr(
        curve,
        "integrate",
    ):
        return float(
            curve.integrate(
                a,
                b,
            )
        )

    raise TypeError(
        "Cp(T) curve has no supported "
        "integration method"
    )


def _solve_integrated(
    curves,
    scenario,
):
    hot = scenario[
        "hot_material"
    ]

    cold = scenario[
        "cold_material"
    ]

    th = float(
        scenario[
            "hot_temperature_k"
        ]
    )

    tc = float(
        scenario[
            "cold_temperature_k"
        ]
    )

    nh = (
        float(
            scenario[
                "hot_mass_g"
            ]
        )
        /
        MOLAR_MASS_G_MOL[
            hot
        ]
    )

    nc = (
        float(
            scenario[
                "cold_mass_g"
            ]
        )
        /
        MOLAR_MASS_G_MOL[
            cold
        ]
    )

    def residual(t):

        q_hot = (
            nh
            * _curve_integral(
                curves[
                    hot
                ],
                t,
                th,
            )
        )

        q_cold = (
            nc
            * _curve_integral(
                curves[
                    cold
                ],
                tc,
                t,
            )
        )

        return (
            q_hot
            - q_cold
        )

    return float(
        brentq(
            residual,
            tc + 1e-8,
            th - 1e-8,
        )
    )


def _solve_constant_initial_cp(
    curves,
    scenario,
):
    """
    Prepared TOOL-TRAP path.

    Cp of each body is evaluated at that body's INITIAL temperature
    and then treated as constant through the entire thermal path.
    """

    hot = scenario[
        "hot_material"
    ]

    cold = scenario[
        "cold_material"
    ]

    th = float(
        scenario[
            "hot_temperature_k"
        ]
    )

    tc = float(
        scenario[
            "cold_temperature_k"
        ]
    )

    nh = (
        float(
            scenario[
                "hot_mass_g"
            ]
        )
        /
        MOLAR_MASS_G_MOL[
            hot
        ]
    )

    nc = (
        float(
            scenario[
                "cold_mass_g"
            ]
        )
        /
        MOLAR_MASS_G_MOL[
            cold
        ]
    )

    cp_hot = float(
        curves[
            hot
        ](
            th
        )
    )

    cp_cold = float(
        curves[
            cold
        ](
            tc
        )
    )

    numerator = (
        nh
        * cp_hot
        * th
        +
        nc
        * cp_cold
        * tc
    )

    denominator = (
        nh
        * cp_hot
        +
        nc
        * cp_cold
    )

    return float(
        numerator
        /
        denominator
    )


def solve_panel(
    curves,
    scenarios=SCENARIOS,
    equilibrium_mode="integrated",
):
    rows = []

    for s in scenarios:

        if (
            equilibrium_mode
            == "integrated"
        ):
            teq = (
                _solve_integrated(
                    curves,
                    s,
                )
            )

        elif (
            equilibrium_mode
            == "constant_initial_cp"
        ):
            teq = (
                _solve_constant_initial_cp(
                    curves,
                    s,
                )
            )

        else:
            raise KeyError(
                "unknown equilibrium_mode: "
                f"{equilibrium_mode}"
            )

        rows.append(
            {
                "scenario_id":
                    s[
                        "scenario_id"
                    ],

                "equilibrium_temperature_k":
                    teq,
            }
        )

    return rows


# =====================================================================
# Uncertainty propagation
# =====================================================================

def _sigma_from_reported(
    u95,
    semantics,
):
    if (
        semantics
        == "expanded_95"
    ):
        return (
            u95
            /
            Z95
        )

    if (
        semantics
        == "reported_values_are_1sigma"
    ):
        return u95

    raise KeyError(
        "unknown uncertainty semantics: "
        f"{semantics}"
    )


def propagate_panel_uncertainty(
    train,
    scenarios=SCENARIOS,
    weighting="uncertainty",
    equilibrium_mode="integrated",
    uncertainty_semantics="expanded_95",
    n_mc=300,
    seed=20260830,
):
    """
    Deterministic Monte-Carlo propagation.

    The Gaussian treatment is a benchmark working approximation.

    It is not a claim that the ThermoML experiment established independent
    Gaussian errors.
    """

    rng = (
        np.random.default_rng(
            seed
        )
    )

    material_data = {}

    for material in MATERIALS:

        d = (
            train[
                train["formula"]
                == material
            ]
            .sort_values(
                "temperature_k"
            )
            .reset_index(
                drop=True
            )
        )

        material_data[
            material
        ] = d

    zdraw = {
        material:
            rng.normal(
                size=(
                    n_mc,
                    len(d),
                )
            )

        for material, d
        in material_data.items()
    }

    sims = {
        s["scenario_id"]:
            []

        for s in scenarios
    }

    for i in range(
        n_mc
    ):

        pieces = []

        for material, d in (
            material_data.items()
        ):

            x = d.copy()

            u95 = x[
                "cp_uncertainty_j_mol_k"
            ].to_numpy(
                float
            )

            sigma = (
                _sigma_from_reported(
                    u95,
                    uncertainty_semantics,
                )
            )

            x[
                "cp_j_mol_k"
            ] = (
                x[
                    "cp_j_mol_k"
                ].to_numpy(
                    float
                )
                +
                sigma
                * zdraw[
                    material
                ][i]
            )

            pieces.append(
                x
            )

        sampled = pd.concat(
            pieces,
            ignore_index=True,
        )

        curves = fit_curves(
            sampled,
            weighting=weighting,
        )

        panel = solve_panel(
            curves,
            scenarios=scenarios,
            equilibrium_mode=
                equilibrium_mode,
        )

        for row in panel:

            sims[
                row[
                    "scenario_id"
                ]
            ].append(
                row[
                    "equilibrium_temperature_k"
                ]
            )

    out = []

    for s in scenarios:

        sid = s[
            "scenario_id"
        ]

        values = np.asarray(
            sims[sid],
            dtype=float,
        )

        q025, q50, q975 = (
            np.quantile(
                values,
                [
                    0.025,
                    0.50,
                    0.975,
                ],
            )
        )

        out.append(
            {
                "scenario_id":
                    sid,

                "ci95_low_k":
                    float(q025),

                "median_k":
                    float(q50),

                "ci95_high_k":
                    float(q975),

                "ci95_width_k":
                    float(
                        q975
                        - q025
                    ),
            }
        )

    return out


def analyze(
    train,
    targets,
    scenarios=SCENARIOS,
    weighting="uncertainty",
    equilibrium_mode="integrated",
    uncertainty_semantics="expanded_95",
    n_mc=300,
    seed=20260830,
):
    curves = fit_curves(
        train,
        weighting=weighting,
    )

    cp = predict_targets(
        curves,
        targets,
    )

    point = solve_panel(
        curves,
        scenarios=scenarios,
        equilibrium_mode=
            equilibrium_mode,
    )

    uncertainty = (
        propagate_panel_uncertainty(
            train,
            scenarios=scenarios,
            weighting=weighting,
            equilibrium_mode=
                equilibrium_mode,
            uncertainty_semantics=
                uncertainty_semantics,
            n_mc=n_mc,
            seed=seed,
        )
    )

    unc = {
        r[
            "scenario_id"
        ]:
            r
        for r in uncertainty
    }

    panel = []

    for row in point:

        sid = row[
            "scenario_id"
        ]

        panel.append(
            {
                **row,
                "ci95_low_k":
                    unc[
                        sid
                    ][
                        "ci95_low_k"
                    ],

                "ci95_high_k":
                    unc[
                        sid
                    ][
                        "ci95_high_k"
                    ],

                "ci95_width_k":
                    unc[
                        sid
                    ][
                        "ci95_width_k"
                    ],
            }
        )

    return {
        "cp_predictions":
            cp,

        "equilibrium_panel":
            panel,
    }


# =====================================================================
# Verifier metrics
# =====================================================================

def cp_relative_rmse(
    predicted,
    truth,
):
    z = truth[
        [
            "measurement_id",
            "cp_j_mol_k",
        ]
    ].merge(
        predicted,
        on="measurement_id",
        how="inner",
    )

    if (
        len(z)
        != len(truth)
    ):
        return np.inf

    obs = z[
        "cp_j_mol_k"
    ].to_numpy(float)

    pred = z[
        "predicted_cp_j_mol_k"
    ].to_numpy(float)

    return float(
        np.sqrt(
            np.mean(
                (
                    (
                        pred
                        - obs
                    )
                    /
                    obs
                )
                ** 2
            )
        )
    )


def _panel_map(
    panel,
):
    return {
        r[
            "scenario_id"
        ]:
            r
        for r in panel
    }


def panel_mae_k(
    predicted,
    gold,
):
    p = _panel_map(
        predicted
    )

    g = _panel_map(
        gold
    )

    errs = []

    for sid in g:

        if sid not in p:
            return np.inf

        errs.append(
            abs(
                float(
                    p[sid][
                        "equilibrium_temperature_k"
                    ]
                )
                -
                float(
                    g[sid][
                        "equilibrium_temperature_k"
                    ]
                )
            )
        )

    return float(
        np.mean(
            errs
        )
    )


def panel_anchor_error_k(
    predicted,
    gold,
):
    p = _panel_map(
        predicted
    )

    g = _panel_map(
        gold
    )

    sid = "cu_al_anchor"

    return abs(
        float(
            p[sid][
                "equilibrium_temperature_k"
            ]
        )
        -
        float(
            g[sid][
                "equilibrium_temperature_k"
            ]
        )
    )


def interval_width_relative_error(
    predicted,
    gold,
):
    p = _panel_map(
        predicted
    )

    g = _panel_map(
        gold
    )

    vals = []

    for sid in g:

        if sid not in p:
            return np.inf

        gw = float(
            g[sid][
                "ci95_width_k"
            ]
        )

        pw = float(
            p[sid][
                "ci95_width_k"
            ]
        )

        vals.append(
            abs(
                pw
                - gw
            )
            /
            gw
        )

    return float(
        np.median(
            vals
        )
    )


def interval_width_ratio(
    predicted,
    gold,
):
    p = _panel_map(
        predicted
    )

    g = _panel_map(
        gold
    )

    vals = []

    for sid in g:

        vals.append(
            float(
                p[sid][
                    "ci95_width_k"
                ]
            )
            /
            float(
                g[sid][
                    "ci95_width_k"
                ]
            )
        )

    return float(
        np.median(
            vals
        )
    )
