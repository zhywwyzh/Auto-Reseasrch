"""
Canonical Nuclear L2 near-field detector-efficiency challenge.

World
-----
near_field_efficiency_model_default

This module reproduces the frozen process-control construction selected
BEFORE named-model evaluation:

    source-to-detector-face distance:
        5.000 cm -> 5.050 cm linearly across the active Co-60 record.

Physical benchmark response:
    matched 2x2-inch NaI(Tl) total-efficiency calibration.

Prepared/default response:
    point-detector inverse-square approximation using crystal-center
    distance.

The 0.5 mm process-control magnitude is frozen and MUST NOT be tuned
against model behavior.
"""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares


DAYS_PER_YEAR = 365.25

WORLD = "near_field_efficiency_model_default"

DISTANCE_START_CM = 5.000
DISTANCE_END_CM = 5.050

CRYSTAL_DIAMETER_CM = 5.08
CRYSTAL_LENGTH_CM = 5.08
CRYSTAL_HALF_DEPTH_CM = 2.54

CO60_E1_KEV = 1173.228
CO60_E2_KEV = 1332.492

CO60_P1 = 0.9985
CO60_P2 = 0.999826

CAL_DISTANCE_CM = np.asarray(
    [5.0, 10.0, 15.0],
    dtype=float,
)

EFFICIENCY_1000_KEV = np.asarray(
    [0.0219, 0.0074, 0.0037],
    dtype=float,
)

EFFICIENCY_1332_KEV = np.asarray(
    [0.0200, 0.0067, 0.0033],
    dtype=float,
)


def fit_exponential(df):
    t = df["elapsed_days"].to_numpy(float)
    y = df["rate_cps"].to_numpy(float)
    s = df["sigma_rate_cps"].to_numpy(float)

    slope, intercept = np.polyfit(
        t,
        np.log(y),
        1,
    )

    def residual(p):
        logA, lam = p

        pred = np.exp(
            logA
            - lam*t
        )

        return (
            pred-y
        ) / s

    z = least_squares(
        residual,
        [
            float(intercept),
            max(
                -float(slope),
                1e-8,
            ),
        ],
        bounds=(
            [-np.inf, 1e-10],
            [np.inf, 0.1],
        ),
        max_nfev=100000,
    )

    logA, lam = [
        float(v)
        for v in z.x
    ]

    A = float(
        np.exp(logA)
    )

    pred = (
        A
        * np.exp(
            -lam*t
        )
    )

    half_days = (
        math.log(2.0)
        / lam
    )

    return {
        "A_cps":
            A,

        "lambda_per_day":
            lam,

        "half_life_days":
            float(
                half_days
            ),

        "half_life_years":
            float(
                half_days
                / DAYS_PER_YEAR
            ),

        "mean_lifetime_days":
            float(
                1.0/lam
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
                            pred-y
                        )**2
                    )
                )
            ),

        "weighted_rmse":
            float(
                np.sqrt(
                    np.mean(
                        (
                            (
                                pred-y
                            ) / s
                        )**2
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


def responses(clean):
    elapsed = clean[
        "elapsed_days"
    ].to_numpy(float)

    frac = (
        elapsed
        / np.max(elapsed)
    )

    distance = (
        DISTANCE_START_CM
        + (
            DISTANCE_END_CM
            - DISTANCE_START_CM
        )*frac
    )

    w = (
        CO60_E1_KEV
        - 1000.0
    ) / (
        1332.0
        - 1000.0
    )

    eff1173 = (
        EFFICIENCY_1000_KEV
        + w*(
            EFFICIENCY_1332_KEV
            - EFFICIENCY_1000_KEV
        )
    )

    combined = (
        CO60_P1*eff1173
        + CO60_P2*EFFICIENCY_1332_KEV
    )

    true_eff = np.interp(
        distance,
        CAL_DISTANCE_CM,
        combined,
    )

    true0 = float(
        np.interp(
            DISTANCE_START_CM,
            CAL_DISTANCE_CM,
            combined,
        )
    )

    calibrated = (
        true_eff
        / true0
    )

    prepared = (
        (
            DISTANCE_START_CM
            + CRYSTAL_HALF_DEPTH_CM
        )
        /
        (
            distance
            + CRYSTAL_HALF_DEPTH_CM
        )
    )**2

    return (
        distance,
        calibrated,
        prepared,
    )


def construct(clean):
    clean = clean.copy()

    distance, calibrated, prepared = (
        responses(clean)
    )

    counts = np.rint(
        clean[
            "total_counts"
        ].to_numpy(float)
        * calibrated
    )

    live = clean[
        "total_live_time_s"
    ].to_numpy(float)

    challenge = clean.copy()

    challenge[
        "total_counts"
    ] = counts

    challenge[
        "rate_cps"
    ] = (
        counts/live
    )

    challenge[
        "sigma_rate_cps"
    ] = (
        np.sqrt(counts)
        / live
    )

    prepared_df = challenge[
        [
            "date",
            "elapsed_days",
            "rate_cps",
            "sigma_rate_cps",
        ]
    ].copy()

    prepared_df[
        "rate_cps"
    ] = (
        challenge[
            "rate_cps"
        ].to_numpy(float)
        / prepared
    )

    prepared_df[
        "sigma_rate_cps"
    ] = (
        challenge[
            "sigma_rate_cps"
        ].to_numpy(float)
        / prepared
    )

    robust = challenge[
        [
            "date",
            "elapsed_days",
            "rate_cps",
            "sigma_rate_cps",
        ]
    ].copy()

    robust[
        "rate_cps"
    ] = (
        challenge[
            "rate_cps"
        ].to_numpy(float)
        / calibrated
    )

    robust[
        "sigma_rate_cps"
    ] = (
        challenge[
            "sigma_rate_cps"
        ].to_numpy(float)
        / calibrated
    )

    return {
        "distance":
            distance,

        "calibrated_response":
            calibrated,

        "prepared_response":
            prepared,

        "challenge":
            challenge,

        "prepared":
            prepared_df,

        "robust":
            robust,

        "naive_fit":
            fit_exponential(
                prepared_df
            ),

        "gold_fit":
            fit_exponential(
                robust
            ),
    }


def gold_entry(clean):
    z = construct(clean)

    g = z[
        "gold_fit"
    ]

    return {
        "gold_lambda_per_day":
            g[
                "lambda_per_day"
            ],

        "gold_half_life_years":
            g[
                "half_life_years"
            ],

        "gold_fit":
            g,

        "naive_fit":
            z[
                "naive_fit"
            ],
    }


def promote_public_cell(
    run_dir,
    gold_path,
):
    run_dir = Path(run_dir)

    cell0 = (
        run_dir
        / "data"
        / "cell000"
    )

    cell1 = (
        run_dir
        / "data"
        / "cell001"
    )

    clean = pd.read_csv(
        cell0
        / "decay_measurements.csv.gz"
    )

    z = construct(
        clean
    )

    if cell1.exists():
        shutil.rmtree(
            cell1
        )

    shutil.copytree(
        cell0,
        cell1,
    )

    z[
        "challenge"
    ].to_csv(
        cell1
        / "decay_measurements.csv.gz",
        index=False,
    )

    z[
        "prepared"
    ].to_csv(
        cell1
        / "prepared_decay_series.csv.gz",
        index=False,
    )

    pd.DataFrame({
        "date":
            clean[
                "date"
            ].astype(str),

        "elapsed_days":
            clean[
                "elapsed_days"
            ].astype(float),

        "source_to_detector_face_cm":
            z[
                "distance"
            ],

        "detector_crystal_diameter_cm":
            CRYSTAL_DIAMETER_CM,

        "detector_crystal_length_cm":
            CRYSTAL_LENGTH_CM,
    }).to_csv(
        cell1
        / "detector_geometry.csv.gz",
        index=False,
    )

    rows = []

    for d, e1000, e1332 in zip(
        CAL_DISTANCE_CM,
        EFFICIENCY_1000_KEV,
        EFFICIENCY_1332_KEV,
    ):
        rows.extend([
            {
                "source_to_detector_face_cm":
                    float(d),

                "gamma_energy_keV":
                    1000.0,

                "total_efficiency":
                    float(e1000),
            },
            {
                "source_to_detector_face_cm":
                    float(d),

                "gamma_energy_keV":
                    1332.0,

                "total_efficiency":
                    float(e1332),
            },
        ])

    pd.DataFrame(
        rows
    ).to_csv(
        cell1
        / "nai_efficiency_calibration.csv",
        index=False,
    )

    pd.DataFrame([
        {
            "gamma_energy_keV":
                CO60_E1_KEV,

            "emission_probability_per_decay":
                CO60_P1,
        },
        {
            "gamma_energy_keV":
                CO60_E2_KEV,

            "emission_probability_per_decay":
                CO60_P2,
        },
    ]).to_csv(
        cell1
        / "co60_gamma_lines.csv",
        index=False,
    )

    (
        cell1
        / "prepared_detector_model.json"
    ).write_text(
        json.dumps(
            {
                "model_name":
                    "point_detector_inverse_square",

                "purpose":
                    (
                        "detector-response correction used by "
                        "the prepared decay analysis"
                    ),

                "source_distance_definition":
                    (
                        "source position to detector "
                        "crystal front face"
                    ),

                "detector_crystal_length_cm":
                    CRYSTAL_LENGTH_CM,

                "nominal_crystal_center_offset_cm":
                    CRYSTAL_HALF_DEPTH_CM,

                "reference_source_face_distance_cm":
                    DISTANCE_START_CM,

                "relative_response_model":
                    (
                        "((reference_source_face_distance_cm + "
                        "nominal_crystal_center_offset_cm) / "
                        "(source_to_detector_face_cm + "
                        "nominal_crystal_center_offset_cm)) ** 2"
                    ),
            },
            indent=2,
        )
    )

    (
        cell1
        / "measurement_provenance.json"
    ).write_text(
        json.dumps(
            {
                "detector":
                    "2 x 2 inch NaI(Tl)",

                "efficiency_calibration_source":
                    {
                        "doi":
                            "10.18466/cbayarfbe.396704",

                        "use":
                            (
                                "auxiliary matched-detector "
                                "total-efficiency calibration "
                                "used as supplied benchmark evidence"
                            ),
                    },

                "co60_line_source":
                    {
                        "energies_keV":
                            [
                                CO60_E1_KEV,
                                CO60_E2_KEV,
                            ],

                        "emission_probabilities":
                            [
                                CO60_P1,
                                CO60_P2,
                            ],
                    },

                "geometry_record":
                    (
                        "benchmark process-control geometry record; "
                        "not attributed as an observed drift in the "
                        "historical campaign"
                    ),
            },
            indent=2,
        )
    )

    problem_path = (
        cell1
        / "problem.json"
    )

    problem = json.loads(
        problem_path.read_text()
    )

    problem[
        "auxiliary_files"
    ] = [
        {
            "file":
                "detector_geometry.csv.gz",

            "description":
                "daily source-to-detector geometry metadata",
        },
        {
            "file":
                "nai_efficiency_calibration.csv",

            "description":
                (
                    "matched 2 x 2 inch NaI(Tl) "
                    "total-efficiency calibration measurements"
                ),
        },
        {
            "file":
                "co60_gamma_lines.csv",

            "description":
                (
                    "Co-60 gamma-line energies "
                    "and emission probabilities"
                ),
        },
        {
            "file":
                "prepared_detector_model.json",

            "description":
                (
                    "detector-response model used to produce "
                    "the supplied prepared decay series"
                ),
        },
        {
            "file":
                "measurement_provenance.json",

            "description":
                (
                    "measurement and auxiliary-calibration "
                    "provenance"
                ),
        },
    ]

    problem_path.write_text(
        json.dumps(
            problem,
            indent=2,
        )
    )

    gold_obj = json.loads(
        Path(
            gold_path
        ).read_text()
    )

    man_path = (
        run_dir
        / "manifest.json"
    )

    man = json.loads(
        man_path.read_text()
    )

    for row in man:
        if int(
            row.get(
                "cell",
                -1,
            )
        ) != 1:
            continue

        row[
            "world_label"
        ] = WORLD

        row[
            "issue_type"
        ] = "tool-trap"

        row[
            "agent_input"
        ] = str(
            cell1.resolve()
        )

        row[
            "agent_output"
        ] = str(
            (
                run_dir
                / "out_cell001.json"
            ).resolve()
        )

        row[
            "gold"
        ] = gold_obj[
            "decay_fit"
        ][
            WORLD
        ]

        row[
            "correct_action"
        ] = (
            "Validate the prepared point-detector inverse-square "
            "response against the supplied matched finite-detector "
            "efficiency calibration and daily geometry record; use "
            "the supported detector response before estimating "
            "Co-60 lambda and half-life."
        )

        row[
            "confound_tell"
        ] = (
            "The prepared detector-response approximation and the "
            "supplied matched-detector efficiency calibration imply "
            "different geometry dependence."
        )

    man_path.write_text(
        json.dumps(
            man,
            indent=2,
        )
    )
