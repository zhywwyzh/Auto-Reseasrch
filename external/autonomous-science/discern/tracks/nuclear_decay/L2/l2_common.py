"""
Nuclear Decay L2 — canonical multisource mechanics.

Temperature-response and Mn-54 settings were frozen before named-model
evaluation. The fixed-photopeak-ROI replacement was selected and
sensitivity-frozen without consulting model output on that candidate.

Final worlds
------------
clean
near_field_efficiency_model_default       tool-trap
mn54_cross_source_contamination           data-confound
fixed_photopeak_roi_default              tool-trap

Shared clean substrate
----------------------
Real Co-60 daily counting measurements,
synchronous environmental measurements,
and an independent real Mn-54 reference series.

The physical Co-60 decay constant remains unchanged across all worlds.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from scipy.optimize import least_squares


HERE = Path(__file__).resolve().parent

ASSETS = (
    HERE
    / "assets"
    / "multisource"
)

DAYS_PER_YEAR = 365.25

START_DATE = "2015-05-04"
END_DATE = "2016-02-01"


# ---------------------------------------------------------------------
# FROZEN PRE-MODEL SETTINGS
# ---------------------------------------------------------------------

TEMP_RESPONSE_PER_C = -0.003

MN54_COUPLING = 0.0025



def _read(name):
    p = ASSETS / name

    if not p.exists():
        raise FileNotFoundError(
            p
        )

    return pd.read_csv(
        p
    )


# =====================================================================
# AUXILIARY STREAMS
# =====================================================================

def load_environment():
    env = _read(
        "environment_daily.csv.gz"
    )

    env = env[
        (
            env["date"]
            >= START_DATE
        )
        & (
            env["date"]
            <= END_DATE
        )
    ].copy()

    return (
        env.sort_values(
            "date"
        )
        .reset_index(
            drop=True
        )
    )


def load_mn54_reference():
    m = _read(
        "mn54_daily_meta.csv.gz"
    ).copy()

    m = m[
        m["date"]
        >= START_DATE
    ].copy()

    m = (
        m.sort_values(
            "date"
        )
        .reset_index(
            drop=True
        )
    )

    m["elapsed_days"] = (
        pd.to_datetime(
            m["date"]
        )
        - pd.Timestamp(
            START_DATE
        )
    ).dt.days.astype(float)

    return pd.DataFrame(
        {
            "date":
                m[
                    "date"
                ].astype(str),

            "elapsed_days":
                m[
                    "elapsed_days"
                ].astype(float),

            "rate_cps":
                m[
                    "live_normalized_rate_cps"
                ].astype(float),

            "sigma_rate_cps":
                m[
                    "sigma_live_rate_cps"
                ].astype(float),

            "n_acquisitions":
                m[
                    "n_acquisitions"
                ].astype(int),
        }
    )


# =====================================================================
# CLEAN CO-60 SUBSTRATE
# =====================================================================

def load_clean():
    co = _read(
        "co60_daily_meta.csv.gz"
    ).copy()

    env = load_environment()

    co = co[
        (
            co["date"]
            >= START_DATE
        )
        & (
            co["date"]
            <= END_DATE
        )
    ].copy()

    co = (
        co.merge(
            env[
                [
                    "date",
                ]
            ],
            on="date",
            how="inner",
        )
        .sort_values(
            "date"
        )
        .reset_index(
            drop=True
        )
    )

    co["elapsed_days"] = (
        pd.to_datetime(
            co["date"]
        )
        - pd.Timestamp(
            START_DATE
        )
    ).dt.days.astype(float)

    counts = (
        co[
            "total_integral_counts"
        ]
        .astype(float)
        .to_numpy()
    )

    live = (
        co[
            "total_live_time_s"
        ]
        .astype(float)
        .to_numpy()
    )

    return pd.DataFrame(
        {
            "date":
                co[
                    "date"
                ].astype(str),

            "elapsed_days":
                co[
                    "elapsed_days"
                ].astype(float),

            "total_counts":
                counts,

            "total_live_time_s":
                live,

            "total_real_time_s":
                co[
                    "total_real_time_s"
                ].astype(float),

            "rate_cps":
                counts
                / live,

            "sigma_rate_cps":
                np.sqrt(
                    counts
                )
                / live,

            "n_acquisitions":
                co[
                    "n_acquisitions"
                ].astype(int),
        }
    )


def _recompute_from_counts(
    df,
    counts,
):
    out = df.copy()

    counts = np.asarray(
        counts,
        dtype=float,
    )

    if not np.all(
        counts > 0
    ):
        raise ValueError(
            "nonpositive count total"
        )

    live = (
        out[
            "total_live_time_s"
        ]
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


# =====================================================================
# DATA CONFOUND 1 — TEMPERATURE-DEPENDENT DETECTOR RESPONSE
# =====================================================================

def inject_temperature_response(
    clean,
):
    out = clean.copy()

    env = load_environment()

    x = (
        out[
            [
                "date",
            ]
        ]
        .merge(
            env[
                [
                    "date",
                    "temperature_c",
                ]
            ],
            on="date",
            how="left",
        )
    )

    temperature = (
        x[
            "temperature_c"
        ]
        .to_numpy(float)
    )

    if not np.all(
        np.isfinite(
            temperature
        )
    ):
        raise ValueError(
            "missing temperature"
        )

    center = float(
        np.mean(
            temperature
        )
    )

    response = (
        1.0
        + TEMP_RESPONSE_PER_C
        * (
            temperature
            - center
        )
    )

    if not np.all(
        response > 0
    ):
        raise ValueError(
            "nonphysical detector response"
        )

    counts = np.rint(
        out[
            "total_counts"
        ].to_numpy(float)
        * response
    )

    out = _recompute_from_counts(
        out,
        counts,
    )

    meta = {
        "temperature_response_per_c":
            float(
                TEMP_RESPONSE_PER_C
            ),

        "temperature_reference_c":
            center,

        "response_min":
            float(
                response.min()
            ),

        "response_max":
            float(
                response.max()
            ),
    }

    return (
        out,
        meta,
    )


# =====================================================================
# NUMERICAL FITS
# =====================================================================

def fit_exponential(
    df,
):
    t = (
        df[
            "elapsed_days"
        ]
        .to_numpy(float)
    )

    y = (
        df[
            "rate_cps"
        ]
        .to_numpy(float)
    )

    sigma = (
        df[
            "sigma_rate_cps"
        ]
        .to_numpy(float)
    )

    if (
        len(t) < 10
        or not np.all(
            np.isfinite(
                t
            )
        )
        or not np.all(
            y > 0
        )
        or not np.all(
            sigma > 0
        )
    ):
        raise ValueError(
            "invalid decay table"
        )

    slope, intercept = np.polyfit(
        t,
        np.log(
            y
        ),
        1,
    )

    def residual(
        p,
    ):
        logA, lam = p

        pred = np.exp(
            logA
            - lam * t
        )

        return (
            pred - y
        ) / sigma

    fit = least_squares(
        residual,
        [
            float(
                intercept
            ),

            max(
                1e-8,
                -float(
                    slope
                ),
            ),
        ],
        bounds=(
            [
                -np.inf,
                1e-10,
            ],
            [
                np.inf,
                0.1,
            ],
        ),
        max_nfev=50000,
    )

    A = float(
        np.exp(
            fit.x[0]
        )
    )

    lam = float(
        fit.x[1]
    )

    pred = (
        A
        * np.exp(
            -lam * t
        )
    )

    return {
        "A_cps":
            A,

        "lambda_per_day":
            lam,

        "half_life_days":
            float(
                np.log(2.0)
                / lam
            ),

        "half_life_years":
            float(
                np.log(2.0)
                / lam
                / DAYS_PER_YEAR
            ),

        "mean_lifetime_days":
            float(
                1.0
                / lam
            ),

        "mean_lifetime_years":
            float(
                1.0
                / lam
                / DAYS_PER_YEAR
            ),

        "rmse_cps":
            float(
                np.sqrt(
                    np.mean(
                        (
                            pred
                            - y
                        ) ** 2
                    )
                )
            ),

        "weighted_rmse":
            float(
                np.sqrt(
                    np.mean(
                        (
                            (
                                pred
                                - y
                            )
                            / sigma
                        ) ** 2
                    )
                )
            ),

        "model":
            "exponential",

        "weighting":
            "uncertainty",

        "timescale":
            "half_life",
    }


def fit_temperature_response(
    df,
):
    env = load_environment()

    x = df.merge(
        env[
            [
                "date",
                "temperature_c",
            ]
        ],
        on="date",
        how="left",
    )

    t = (
        x[
            "elapsed_days"
        ]
        .to_numpy(float)
    )

    y = (
        x[
            "rate_cps"
        ]
        .to_numpy(float)
    )

    sigma = (
        x[
            "sigma_rate_cps"
        ]
        .to_numpy(float)
    )

    temperature = (
        x[
            "temperature_c"
        ]
        .to_numpy(float)
    )

    dt = (
        temperature
        - np.mean(
            temperature
        )
    )

    slope, intercept = np.polyfit(
        t,
        np.log(
            y
        ),
        1,
    )

    def residual(
        p,
    ):
        logA, lam, beta = p

        pred = (
            np.exp(
                logA
                - lam * t
            )
            * (
                1.0
                + beta * dt
            )
        )

        return (
            pred - y
        ) / sigma

    fit = least_squares(
        residual,
        [
            float(
                intercept
            ),

            max(
                1e-8,
                -float(
                    slope
                ),
            ),

            0.0,
        ],
        bounds=(
            [
                -np.inf,
                1e-10,
                -0.05,
            ],
            [
                np.inf,
                0.1,
                0.05,
            ],
        ),
        max_nfev=50000,
    )

    A = float(
        np.exp(
            fit.x[0]
        )
    )

    lam = float(
        fit.x[1]
    )

    beta = float(
        fit.x[2]
    )

    pred = (
        A
        * np.exp(
            -lam * t
        )
        * (
            1.0
            + beta * dt
        )
    )

    return {
        "A_cps":
            A,

        "lambda_per_day":
            lam,

        "half_life_days":
            float(
                np.log(2.0)
                / lam
            ),

        "half_life_years":
            float(
                np.log(2.0)
                / lam
                / DAYS_PER_YEAR
            ),

        "mean_lifetime_days":
            float(
                1.0
                / lam
            ),

        "mean_lifetime_years":
            float(
                1.0
                / lam
                / DAYS_PER_YEAR
            ),

        "rmse_cps":
            float(
                np.sqrt(
                    np.mean(
                        (
                            pred
                            - y
                        ) ** 2
                    )
                )
            ),

        "weighted_rmse":
            float(
                np.sqrt(
                    np.mean(
                        (
                            (
                                pred
                                - y
                            )
                            / sigma
                        ) ** 2
                    )
                )
            ),

        "model":
            "exponential+temperature_response",

        "weighting":
            "uncertainty",

        "timescale":
            "half_life",

        "temperature_response_per_c":
            beta,
    }


# =====================================================================
# DATA CONFOUND 2 — Mn-54 CROSS-SOURCE COMPONENT
# =====================================================================

def fit_mn54_reference():
    return fit_exponential(
        load_mn54_reference()
    )


def mn54_template_for_times(
    t,
):
    fit = fit_mn54_reference()

    t = np.asarray(
        t,
        dtype=float,
    )

    template = (
        fit[
            "A_cps"
        ]
        * np.exp(
            -fit[
                "lambda_per_day"
            ]
            * t
        )
    )

    return (
        template,
        fit,
    )


def inject_mn54_contamination(
    clean,
):
    out = clean.copy()

    t = (
        out[
            "elapsed_days"
        ]
        .to_numpy(float)
    )

    template, ref_fit = (
        mn54_template_for_times(
            t
        )
    )

    live = (
        out[
            "total_live_time_s"
        ]
        .to_numpy(float)
    )

    extra_counts = (
        MN54_COUPLING
        * template
        * live
    )

    counts = np.rint(
        out[
            "total_counts"
        ].to_numpy(float)
        + extra_counts
    )

    out = _recompute_from_counts(
        out,
        counts,
    )

    meta = {
        "mn54_reference_coupling":
            float(
                MN54_COUPLING
            ),

        "initial_contaminant_cps":
            float(
                MN54_COUPLING
                * template[0]
            ),

        "initial_contaminant_fraction_of_co":
            float(
                MN54_COUPLING
                * template[0]
                / clean[
                    "rate_cps"
                ].iloc[0]
            ),

        "mn54_reference_half_life_years":
            float(
                ref_fit[
                    "half_life_years"
                ]
            ),
    }

    return (
        out,
        meta,
    )


def fit_two_source(
    df,
):
    t = (
        df[
            "elapsed_days"
        ]
        .to_numpy(float)
    )

    y = (
        df[
            "rate_cps"
        ]
        .to_numpy(float)
    )

    sigma = (
        df[
            "sigma_rate_cps"
        ]
        .to_numpy(float)
    )

    ref, _ = (
        mn54_template_for_times(
            t
        )
    )

    slope, intercept = np.polyfit(
        t,
        np.log(
            y
        ),
        1,
    )

    def residual(
        p,
    ):
        logA, lam, coupling = p

        pred = (
            np.exp(
                logA
                - lam * t
            )
            + coupling
            * ref
        )

        return (
            pred - y
        ) / sigma

    fit = least_squares(
        residual,
        [
            float(
                intercept
            ),

            max(
                1e-8,
                -float(
                    slope
                ),
            ),

            MN54_COUPLING,
        ],
        bounds=(
            [
                -np.inf,
                1e-10,
                0.0,
            ],
            [
                np.inf,
                0.1,
                1.0,
            ],
        ),
        max_nfev=50000,
    )

    A = float(
        np.exp(
            fit.x[0]
        )
    )

    lam = float(
        fit.x[1]
    )

    coupling = float(
        fit.x[2]
    )

    pred = (
        A
        * np.exp(
            -lam * t
        )
        + coupling
        * ref
    )

    return {
        "A_cps":
            A,

        "lambda_per_day":
            lam,

        "half_life_days":
            float(
                np.log(2.0)
                / lam
            ),

        "half_life_years":
            float(
                np.log(2.0)
                / lam
                / DAYS_PER_YEAR
            ),

        "mean_lifetime_days":
            float(
                1.0
                / lam
            ),

        "mean_lifetime_years":
            float(
                1.0
                / lam
                / DAYS_PER_YEAR
            ),

        "rmse_cps":
            float(
                np.sqrt(
                    np.mean(
                        (
                            pred
                            - y
                        ) ** 2
                    )
                )
            ),

        "weighted_rmse":
            float(
                np.sqrt(
                    np.mean(
                        (
                            (
                                pred
                                - y
                            )
                            / sigma
                        ) ** 2
                    )
                )
            ),

        "model":
            "two_source_exponential",

        "weighting":
            "uncertainty",

        "timescale":
            "half_life",

        "mn54_reference_coupling":
            coupling,
    }


# =====================================================================
# PREPARED BASELINE SERIES
# =====================================================================

def prepared_series(
    df,
    world_label,
):
    """
    Return the tabular series consumed by the public prepared baseline.

    World-specific construction occurs upstream. The native spectral
    tool-trap is constructed by photopeak_roi.py before this generic
    table reduction is applied.
    """
    return df[
        [
            "date",
            "elapsed_days",
            "rate_cps",
            "sigma_rate_cps",
        ]
    ].copy()
