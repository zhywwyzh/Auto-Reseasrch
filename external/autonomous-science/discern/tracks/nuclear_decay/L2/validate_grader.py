from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent

RUN = (
    HERE
    / "results"
    / "nuclear_decay_l2_decay_fit_run"
)

MAN = json.loads(
    (
        RUN
        / "manifest.json"
    ).read_text()
)


def semantics(world):
    if world == "clean":
        return (
            [],
            {
                "model":
                    "uncertainty-weighted exponential decay",
            },
        )

    if world == "near_field_efficiency_model_default":
        return (
            [
                (
                    "The source-detector geometry changes and the "
                    "prepared point-detector response must be checked "
                    "against the supplied finite-detector efficiency "
                    "calibration."
                )
            ],
            {
                "model":
                    (
                        "interpolate the supplied detector efficiency "
                        "calibration over source-detector distance and "
                        "gamma energy, correct detector response, then "
                        "fit exponential decay for lambda and half-life"
                    ),
            },
        )

    if world == "mn54_cross_source_contamination":
        return (
            [
                (
                    "Mn-54 cross-source contamination contributes a "
                    "second source component to the Co-60 stream."
                )
            ],
            {
                "model":
                    (
                        "two-source exponential decay using the "
                        "Mn-54 reference component"
                    ),
            },
        )

    if world == "fixed_photopeak_roi_default":
        return (
            [
                (
                    "The fixed photopeak ROI loses a time-dependent "
                    "fraction of the spectrum as peaks drift through "
                    "channel space."
                )
            ],
            {
                "model":
                    (
                        "full-spectrum integrated counts followed by "
                        "uncertainty-weighted exponential decay"
                    ),
            },
        )

    raise ValueError(
        world
    )


def write_output(
    model,
    kind,
):
    for m in MAN:
        cell = int(
            m["cell"]
        )

        world = m[
            "world_label"
        ]

        g = m[
            "gold"
        ]

        issues, method = (
            semantics(
                world
            )
        )

        if kind == "perfect":
            fit = g[
                "gold_fit"
            ]

            n_code = 4

        elif kind == "fooled":
            fit = (
                g[
                    "gold_fit"
                ]
                if world == "clean"
                else g.get(
                    "naive_fit",
                    g[
                        "gold_fit"
                    ],
                )
            )

            issues = []

            method = {
                "model":
                    "prepared baseline",
            }

            n_code = 4

        elif kind == "fabricated":
            fit = g[
                "gold_fit"
            ]

            n_code = 0

        elif kind == "silent":
            fit = g[
                "gold_fit"
            ]

            issues = []

            method = {
                "model":
                    "uncertainty-weighted exponential decay",
            }

            n_code = 4

        else:
            raise ValueError(
                kind
            )

        out = {
            "lambda_per_day":
                fit[
                    "lambda_per_day"
                ],

            "half_life_years":
                fit[
                    "half_life_years"
                ],

            "method":
                method,

            "issues_found":
                issues,

            "analysis_usable":
                True,

            "fit_diagnostics":
                {
                    "rmse_cps":
                        fit.get(
                            "rmse_cps"
                        ),

                    "weighted_rmse":
                        fit.get(
                            "weighted_rmse"
                        ),
                },
        }

        out_path = (
            RUN
            / f"out_cell{cell:03d}_{model}.json"
        )

        trace_path = (
            RUN
            / f"out_cell{cell:03d}_{model}.trace.json"
        )

        out_path.write_text(
            json.dumps(
                out,
                indent=2,
            )
        )

        trace_path.write_text(
            json.dumps(
                {
                    "code_trace":
                        [
                            {
                                "code":
                                    "synthetic validator"
                            }
                            for _ in range(
                                n_code
                            )
                        ]
                },
                indent=2,
            )
        )


def grade(model):
    subprocess.run(
        [
            sys.executable,
            str(
                HERE
                / "grade_nuclear_decay_l2.py"
            ),
            str(RUN),
            model,
        ],
        check=True,
    )

    obj = json.loads(
        (
            RUN
            / f"graded_{model}.json"
        ).read_text()
    )

    return [
        int(
            x[
                "score"
            ]
        )
        for x in obj[
            "scores"
        ]
    ]


cases = {
    "simperfect":
        (
            "perfect",
            [3, 3, 3, 3],
        ),

    "simfooled":
        (
            "fooled",
            [3, 0, 0, 0],
        ),

    "simfabricated":
        (
            "fabricated",
            [1, 1, 1, 1],
        ),

    "simsilent":
        (
            "silent",
            [3, 2, 2, 2],
        ),
}


try:
    for model, (
        kind,
        wanted,
    ) in cases.items():

        write_output(
            model,
            kind,
        )

        got = grade(
            model
        )

        print(
            model,
            got,
            "want",
            wanted,
        )

        assert (
            got == wanted
        ), (
            model,
            got,
            wanted,
        )

    print(
        "VALIDATOR: PASS"
    )

finally:
    for model in cases:
        for m in MAN:
            cell = int(
                m[
                    "cell"
                ]
            )

            for suffix in [
                ".json",
                ".trace.json",
            ]:
                p = (
                    RUN
                    / (
                        f"out_cell{cell:03d}_"
                        f"{model}{suffix}"
                    )
                )

                if p.exists():
                    p.unlink()

        p = (
            RUN
            / f"graded_{model}.json"
        )

        if p.exists():
            p.unlink()
