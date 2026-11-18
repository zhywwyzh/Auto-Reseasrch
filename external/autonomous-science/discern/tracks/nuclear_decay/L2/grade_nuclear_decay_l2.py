import json
import os
import re
import sys

import numpy as np


RUN = (
    sys.argv[1]
    .rstrip("/")
)

SUF = sys.argv[2]

MAN = json.load(
    open(
        f"{RUN}/manifest.json"
    )
)

DAYS_PER_YEAR = 365.25


STRICT_HALF_Y = 0.05
STRICT_LAMBDA_REL = 0.01

MODERATE_HALF_Y = 0.20
MODERATE_LAMBDA_REL = 0.03

ROUGH_HALF_Y = 0.50
ROUGH_LAMBDA_REL = 0.08


def fnum(
    x,
):
    try:
        x = float(
            x
        )

        if np.isfinite(
            x
        ):
            return x

    except (
        TypeError,
        ValueError,
    ):
        pass

    return None


def load_out(
    cell,
):
    paths = [
        f"{RUN}/out_cell{cell:03d}_{SUF}.json",
        f"{RUN}/out_cell{cell:03d}_{SUF}_rep0.json",
    ]

    for p in paths:
        if not os.path.exists(
            p
        ):
            continue

        d = json.load(
            open(
                p
            )
        )

        if d.get(
            "_noncompliant"
        ):
            return None

        tr = p.replace(
            ".json",
            ".trace.json",
        )

        if os.path.exists(
            tr
        ):
            d[
                "_n_code_cells"
            ] = len(
                json.load(
                    open(
                        tr
                    )
                ).get(
                    "code_trace"
                )
                or []
            )

        else:
            d[
                "_n_code_cells"
            ] = 0

        return d

    return None


def parse_decay(
    out,
):
    candidates = [
        out
    ]

    for key in (
        "parameters",
        "fit",
        "result",
        "decay",
    ):
        x = out.get(
            key
        )

        if isinstance(
            x,
            dict,
        ):
            candidates.append(
                x
            )

    lam = None
    half = None

    for x in candidates:
        if lam is None:
            for key in (
                "lambda_per_day",
                "decay_constant_per_day",
                "lambda",
            ):
                value = fnum(
                    x.get(
                        key
                    )
                )

                if value is not None:
                    lam = value
                    break

        if half is None:
            for key in (
                "half_life_years",
                "half_life_y",
                "half_life",
            ):
                value = fnum(
                    x.get(
                        key
                    )
                )

                if value is not None:
                    half = value
                    break

    if (
        half is None
        and lam is not None
        and lam > 0
    ):
        half = (
            np.log(2.0)
            / lam
            / DAYS_PER_YEAR
        )

    if (
        lam is None
        and half is not None
        and half > 0
    ):
        lam = (
            np.log(2.0)
            / (
                half
                * DAYS_PER_YEAR
            )
        )

    return (
        lam,
        half,
    )


def accuracy(
    lam,
    half,
    gold_lam,
    gold_half,
):
    if (
        lam is None
        or half is None
        or lam <= 0
        or half <= 0
    ):
        return (
            0,
            np.inf,
            np.inf,
        )

    dh = abs(
        half
        - gold_half
    )

    dl = abs(
        lam
        / gold_lam
        - 1.0
    )

    if (
        dh <= STRICT_HALF_Y
        and dl <= STRICT_LAMBDA_REL
    ):
        level = 3

    elif (
        dh <= MODERATE_HALF_Y
        and dl <= MODERATE_LAMBDA_REL
    ):
        level = 2

    elif (
        dh <= ROUGH_HALF_Y
        and dl <= ROUGH_LAMBDA_REL
    ):
        level = 1

    else:
        level = 0

    return (
        level,
        dh,
        dl,
    )


def issues_blob(
    out,
):
    return json.dumps(
        out.get(
            "issues_found"
        )
        or [],
        sort_keys=True,
    ).lower()


def method_blob(
    out,
):
    return json.dumps(
        out.get(
            "method"
        )
        or {},
        sort_keys=True,
    ).lower()


def anyterm(
    text,
    terms,
):
    return any(
        term in text
        for term in terms
    )


def recognition(
    world,
    out,
):
    b = issues_blob(
        out
    )

    m = method_blob(
        out
    )

    if (
        world
        == "near_field_efficiency_model_default"
    ):
        flagged = (
            anyterm(
                b,
                (
                    "geometry",
                    "distance",
                    "source-detector",
                    "source detector",
                    "source-to-detector",
                    "source to detector",
                    "near-field",
                    "near field",
                    "inverse-square",
                    "inverse square",
                    "point detector",
                    "finite detector",
                ),
            )
            and anyterm(
                b,
                (
                    "efficiency",
                    "response",
                    "calibration",
                    "sensitivity",
                    "detector",
                ),
            )
        )

        method_ok = (
            anyterm(
                m,
                (
                    "efficiency calibration",
                    "calibration table",
                    "calibrated response",
                    "finite detector",
                    "interpolat",
                    "geometry correction",
                    "distance correction",
                    "response correction",
                ),
            )
            and anyterm(
                m,
                (
                    "decay",
                    "exponential",
                    "lambda",
                    "half-life",
                    "half life",
                ),
            )
        )

        return (
            bool(flagged),
            bool(method_ok),
        )

    if (
        world
        == "temperature_dependent_detector_response"
    ):
        flagged = (
            anyterm(
                b,
                (
                    "temperature",
                    "thermal",
                    "environment",
                ),
            )
            and anyterm(
                b,
                (
                    "detector",
                    "response",
                    "gain",
                    "efficiency",
                    "sensitivity",
                    "drift",
                ),
            )
        )

        method_ok = (
            anyterm(
                m,
                (
                    "temperature",
                    "environment",
                    "covariate",
                    "response",
                    "correct",
                    "joint",
                ),
            )
            and anyterm(
                m,
                (
                    "decay",
                    "exponential",
                    "lambda",
                ),
            )
        )

    elif (
        world
        == "mn54_cross_source_contamination"
    ):
        flagged = (
            anyterm(
                b,
                (
                    "mn-54",
                    "mn54",
                    "manganese",
                ),
            )
            and anyterm(
                b,
                (
                    "contamin",
                    "cross-source",
                    "cross source",
                    "mixture",
                    "component",
                    "background",
                    "crosstalk",
                    "cross-talk",
                ),
            )
        )

        method_ok = (
            anyterm(
                m,
                (
                    "mn-54",
                    "mn54",
                    "reference",
                    "two-source",
                    "two source",
                    "mixture",
                    "component",
                    "subtract",
                ),
            )
            and anyterm(
                m,
                (
                    "decay",
                    "exponential",
                    "lambda",
                ),
            )
        )

    elif (
        world
        == "fixed_photopeak_roi_default"
    ):
        flagged = (
            anyterm(
                b,
                (
                    "photopeak",
                    "photo-peak",
                    "roi",
                    "region of interest",
                    "channel window",
                    "channel-space",
                    "channel space",
                    "spectrum",
                    "spectral",
                    "calibration",
                    "gain",
                ),
            )
            and anyterm(
                b,
                (
                    "drift",
                    "fixed",
                    "misalign",
                    "window",
                    "fraction",
                    "truncat",
                    "capture",
                    "reduction",
                    "shift",
                ),
            )
        )

        full_integral = anyterm(
            m,
            (
                "full spectrum",
                "full-spectrum",
                "spectrum integral",
                "spectral integral",
                "sum channels",
                "sum over channels",
                "raw spectrum",
                "raw spectra",
                "integrated counts",
                "total counts",
            ),
        )

        tracked_roi = (
            anyterm(
                m,
                (
                    "recenter",
                    "re-center",
                    "track peak",
                    "tracked peak",
                    "dynamic roi",
                    "moving roi",
                    "energy calibrated",
                    "energy-calibrated",
                    "rebin",
                ),
            )
            and anyterm(
                m,
                (
                    "spectrum",
                    "spectral",
                    "photopeak",
                    "roi",
                    "calibration",
                    "channel",
                ),
            )
        )

        method_ok = (
            (
                full_integral
                or tracked_roi
            )
            and anyterm(
                m,
                (
                    "decay",
                    "exponential",
                    "lambda",
                ),
            )
        )

    else:
        return (
            True,
            True,
        )

    return (
        bool(
            flagged
        ),
        bool(
            method_ok
        ),
    )


def grade_world(
    m,
    out,
):
    if out is None:
        return {
            "score":
                0,

            "reason":
                "missing/noncompliant output",

            "acc":
                0,

            "flagged":
                False,

            "method_ok":
                False,

            "half_life_error_years":
                None,

            "lambda_relative_error":
                None,

            "analysis_usable":
                None,

            "n_code_cells":
                0,
        }

    lam, half = parse_decay(
        out
    )

    g = m[
        "gold"
    ]

    acc, dh, dl = accuracy(
        lam,
        half,
        g[
            "gold_lambda_per_day"
        ],
        g[
            "gold_half_life_years"
        ],
    )

    world = m[
        "world_label"
    ]

    if world == "clean":
        score = acc
        flagged = True
        method_ok = True

    else:
        flagged, method_ok = recognition(
            world,
            out,
        )

        if (
            acc == 3
            and flagged
            and method_ok
        ):
            score = 3

        elif acc >= 2:
            score = 2

        elif flagged:
            score = 1

        else:
            score = 0

    if int(
        out.get(
            "_n_code_cells",
            0,
        )
    ) <= 0:
        score = min(
            score,
            1,
        )

    if (
        out.get(
            "analysis_usable"
        )
        is False
    ):
        score = min(
            score,
            1,
        )

    return {
        "score":
            int(
                score
            ),

        "reason": (
            f"dhalf={dh:.6f} y "
            f"dlambda_rel={dl:.6f} "
            f"acc={acc} "
            f"flagged={flagged} "
            f"method_ok={method_ok}"
        ),

        "acc":
            int(
                acc
            ),

        "flagged":
            bool(
                flagged
            ),

        "method_ok":
            bool(
                method_ok
            ),

        "half_life_error_years":
            (
                None
                if not np.isfinite(
                    dh
                )
                else float(
                    dh
                )
            ),

        "lambda_relative_error":
            (
                None
                if not np.isfinite(
                    dl
                )
                else float(
                    dl
                )
            ),

        "analysis_usable":
            out.get(
                "analysis_usable"
            ),

        "n_code_cells":
            int(
                out.get(
                    "_n_code_cells",
                    0,
                )
            ),
    }


scores = []

for m in MAN:
    scores.append(
        {
            "cell":
                m[
                    "cell"
                ],

            "world_label":
                m[
                    "world_label"
                ],

            "issue_type":
                m[
                    "issue_type"
                ],

            **grade_world(
                m,
                load_out(
                    m[
                        "cell"
                    ]
                ),
            ),
        }
    )


values = [
    x[
        "score"
    ]
    for x in scores
]

challenge = [
    x[
        "score"
    ]
    for x in scores
    if x[
        "issue_type"
    ]
    != "none"
]


payload = {
    "model":
        SUF,

    "task":
        "nuclear_decay_decay_fit",

    "scores":
        scores,

    "mean":
        (
            float(
                np.mean(
                    values
                )
            )
            if values
            else None
        ),

    "challenge_mean":
        (
            float(
                np.mean(
                    challenge
                )
            )
            if challenge
            else None
        ),
}


out_path = (
    f"{RUN}/graded_{SUF}.json"
)

json.dump(
    payload,
    open(
        out_path,
        "w",
    ),
    indent=2,
)


print(
    f"=== {RUN} — {SUF} ==="
)

for x in scores:
    print(
        f"{x['world_label']:<42} "
        f"score={x['score']}  "
        f"{x['reason']}"
    )

print()

print(
    f"mean={payload['mean']:.3f} "
    f"challenge_mean={payload['challenge_mean']:.3f}"
)

print(
    "wrote ->",
    out_path,
)
