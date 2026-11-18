"""
Gold-free prepared-analysis helper.

Public interface
----------------
analyze_world(world_dir)

The prepared series is not guaranteed to be scientifically valid.
Researchers must validate it against the supplied primary and
auxiliary measurements.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from scipy.optimize import least_squares


DAYS_PER_YEAR = 365.25


def analyze_world(
    world_dir,
):
    p = (
        Path(
            world_dir
        )
        / "prepared_decay_series.csv.gz"
    )

    df = pd.read_csv(
        p
    )

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
            "prepared decay series is invalid"
        )

    slope, intercept = np.polyfit(
        t,
        np.log(
            y
        ),
        1,
    )

    def residual(
        z,
    ):
        logA, lam = z

        return (
            np.exp(
                logA
                - lam * t
            )
            - y
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
        max_nfev=20000,
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

    resid = (
        pred - y
    )

    return {
        "lambda_per_day":
            lam,

        "half_life_years":
            float(
                np.log(2.0)
                / lam
                / DAYS_PER_YEAR
            ),

        "fit_diagnostics": {
            "rmse_cps":
                float(
                    np.sqrt(
                        np.mean(
                            resid ** 2
                        )
                    )
                ),

            "weighted_rmse":
                float(
                    np.sqrt(
                        np.mean(
                            (
                                resid
                                / sigma
                            ) ** 2
                        )
                    )
                ),
        },

        "method": {
            "model":
                "prepared baseline",

            "weighting":
                "prepared baseline",

            "timescale":
                "half_life",
        },
    }
