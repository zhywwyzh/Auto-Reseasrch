"""
Calorimetry L2 deterministic 0-3 grader.

Accuracy is evaluated against:
  - hidden real ThermoML fusion enthalpy;
  - hidden solver-produced equilibrium temperatures;
  - hidden liquid fractions;
  - hidden equilibrium regimes.

Challenge handling is separate from accuracy.

Final challenge behavior:
  3 = accurate + explicit world-specific diagnosis + correct handling
  2 = accurate result with incomplete/silent diagnosis
  1 = issue recognized but recovery materially incomplete
  0 = materially wrong naive result accepted unqualified

Guards:
  - analysis_usable=false -> score <= 1
  - zero executed code cells -> score <= 1
  - malformed/missing scientific result -> score 0

Handling cue search is restricted to VALUES in:
  - issues_found
  - method

Never trajectory text, schema keys, manifest confound_tell, or grader metadata.

usage:
    grade_calorimetry_l2.py <RUN_DIR> <model_suffix>
"""

from pathlib import Path
import json
import re
import sys

import numpy as np


RUN = Path(sys.argv[1]).resolve()
SUF = sys.argv[2]

MAN = json.load(
    open(RUN / "manifest.json")
)

if not MAN:
    raise SystemExit("empty manifest")

GOLD = json.load(
    open(MAN[0]["gold"])
)

THRESHOLDS = GOLD["thresholds"]

GOLD_LATENT = float(
    GOLD["direct_thermoml_latent_heat_kj_mol"]
)

GOLD_PANEL = {
    row["scenario_id"]: row
    for row in GOLD["scenarios"]
}

EXPECTED_IDS = set(GOLD_PANEL)


def fnum(x):
    try:
        v = float(x)
        return v if np.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _values_only(obj):
    if isinstance(obj, dict):
        out = []
        for value in obj.values():
            out.extend(_values_only(value))
        return out

    if isinstance(obj, (list, tuple)):
        out = []
        for value in obj:
            out.extend(_values_only(value))
        return out

    if isinstance(obj, str):
        return [obj]

    return []


def _blob(obj):
    text = " ".join(
        _values_only(obj)
    ).lower()

    text = (
        text
        .replace("_", " ")
        .replace("-", " ")
        .replace("δ", "delta ")
    )

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def _has(text, phrases):
    return any(
        p in text
        for p in phrases
    )


def load_out(cell):
    paths = [
        RUN / f"out_cell{cell:03d}_{SUF}.json",
        RUN / f"out_cell{cell:03d}_{SUF}_rep0.json",
    ]

    for p in paths:
        if not p.exists():
            continue

        try:
            d = json.load(open(p))
        except Exception:
            return None

        if (
            not isinstance(d, dict)
            or d.get("_noncompliant")
        ):
            return None

        trace_path = p.with_suffix(
            ".trace.json"
        )

        n_cells = 0

        if trace_path.exists():
            try:
                tr = json.load(
                    open(trace_path)
                )

                n_cells = len(
                    tr.get("code_trace")
                    or []
                )
            except Exception:
                n_cells = 0

        d["_n_code_cells"] = n_cells
        d["_source_path"] = str(p)

        return d

    return None


def panel_map(panel):
    if not isinstance(panel, list):
        return None

    out = {}

    for row in panel:
        if not isinstance(row, dict):
            return None

        sid = row.get("scenario_id")

        if not isinstance(sid, str):
            return None

        if sid in out:
            return None

        T = fnum(
            row.get(
                "temperature_k",
                row.get(
                    "equilibrium_temperature_k"
                ),
            )
        )

        x = fnum(
            row.get("liquid_fraction")
        )

        regime = row.get("regime")

        if (
            T is None
            or x is None
            or not isinstance(regime, str)
        ):
            return None

        regime = (
            regime.lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if regime not in {
            "solid",
            "partial_melt",
            "liquid",
        }:
            return None

        out[sid] = {
            "temperature_k": T,
            "liquid_fraction": x,
            "regime": regime,
        }

    if set(out) != EXPECTED_IDS:
        return None

    return out


def component_score(error, cuts):
    if error <= float(cuts["3"]):
        return 3

    if error <= float(cuts["2"]):
        return 2

    if error <= float(cuts["1"]):
        return 1

    return 0


def regime_component(n_errors):
    cuts = THRESHOLDS["regime_errors"]

    if n_errors <= int(cuts["3"]):
        return 3

    if n_errors <= int(cuts["2"]):
        return 2

    if n_errors <= int(cuts["1"]):
        return 1

    return 0


def accuracy(out):
    if not out:
        return None

    latent = fnum(
        out.get("latent_heat_kj_mol")
    )

    panel = panel_map(
        out.get("equilibrium_panel")
    )

    if latent is None or panel is None:
        return None

    dH = abs(
        latent - GOLD_LATENT
    )

    max_dt = 0.0
    max_dx = 0.0
    regime_errors = 0

    for sid, gold in GOLD_PANEL.items():
        got = panel[sid]

        max_dt = max(
            max_dt,
            abs(
                got["temperature_k"]
                - float(
                    gold["temperature_k"]
                )
            ),
        )

        max_dx = max(
            max_dx,
            abs(
                got["liquid_fraction"]
                - float(
                    gold["liquid_fraction"]
                )
            ),
        )

        regime_errors += (
            got["regime"]
            != gold["regime"]
        )

    components = {
        "latent_heat":
            component_score(
                dH,
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
            regime_component(
                regime_errors
            ),
    }

    return {
        "accuracy":
            min(
                components.values()
            ),

        "components":
            components,

        "latent_heat_abs_error_kj_mol":
            dH,

        "max_temperature_abs_error_k":
            max_dt,

        "max_liquid_fraction_abs_error":
            max_dx,

        "regime_errors":
            int(regime_errors),
    }


def handling_state(world, out, acc):
    """
    Returns:
      3 = full explicit world-specific handling
      2 = incomplete/silent but accurate enough
      1 = issue recognized but poor recovery
      0 = naive/unhandled and inaccurate
    """

    if world == "clean":
        return 3

    issues = _blob(
        out.get(
            "issues_found",
            [],
        )
    )

    method = _blob(
        out.get(
            "method",
            {},
        )
    )

    both = (
        issues
        + " "
        + method
    )

    full = False
    partial = False

    if (
        world
        == "liquid_enthalpy_reference_offset"
    ):
        diagnosis = (
            "enthalpy" in issues
            and "reference" in issues
            and _has(
                issues,
                [
                    "offset",
                    "baseline",
                    "zero",
                    "shift",
                    "inconsisten",
                ],
            )
        )

        correction = _has(
            both,
            [
                "cross property",
                "thermodynamic consistency",
                "entropy",
                "t delta s",
                "tdeltas",
                "delta s",
                "gibbs",
                "common reference",
            ],
        )

        full = (
            diagnosis
            and correction
        )

        partial = (
            "enthalpy" in issues
            and _has(
                issues,
                [
                    "reference",
                    "offset",
                    "inconsisten",
                    "entropy",
                    "thermodynamic",
                ],
            )
        )

    elif (
        world
        == "enthalpy_temperature_slope_drift"
    ):
        diagnosis = (
            "enthalpy" in issues
            and _has(issues, [
                "slope",
                "temperature dependent",
                "drift",
                "derivative",
                "dh/dt",
                "dh dt",
                "d h/d t",
            ])
            and _has(issues, [
                "cp",
                "heat capacity",
                "d h",
                "derivative",
                "inconsisten",
            ])
        )

        correction = _has(both, [
            "integrat",
            "heat capacity",
            "cp",
            "reconstruct",
            "correct",
            "remove drift",
            "thermodynamic consistency",
            "cross property",
        ])

        full = diagnosis and correction

        partial = (
            "enthalpy" in issues
            and _has(issues, [
                "slope",
                "drift",
                "derivative",
                "cp",
                "heat capacity",
                "inconsisten",
            ])
        )

    elif (
        world
        == "phase_blind_enthalpy_interpolation"
    ):
        diagnosis = _has(
            issues,
            [
                "phase blind",
                "unified interpol",
                "single interpol",
                "smear",
                "phase labels",
                "phase distinction",
                "continuous interpol",
            ],
        )

        correction = _has(
            both,
            [
                "separate branches",
                "phase resolved",
                "phase coexist",
                "partial melt",
                "two phase",
            ],
        )

        full = (
            diagnosis
            and correction
        )

        partial = _has(
            issues,
            [
                "interpol",
                "phase",
                "coexist",
                "partial melt",
            ],
        )

    if full:
        return 3

    if partial:
        return (
            2
            if acc >= 2
            else 1
        )

    # Correct but silent/incomplete diagnosis.
    if acc >= 2:
        return 2

    # Materially wrong naive result, accepted unqualified.
    return 0


rows = []

for m in MAN:
    cell = int(m["cell"])
    world = m["world_label"]

    out = load_out(cell)

    if out is None:
        rows.append(
            {
                "cell": cell,
                "world": world,
                "score": 0,
                "accuracy": 0,
                "handling": 0,
                "reason":
                    "missing_or_noncompliant_output",
            }
        )
        continue

    # Required scientific artifact.
    if (
        not isinstance(
            out.get("method"),
            dict,
        )
        or not isinstance(
            out.get("issues_found"),
            list,
        )
        or not isinstance(
            out.get("analysis_usable"),
            bool,
        )
    ):
        rows.append(
            {
                "cell": cell,
                "world": world,
                "score": 0,
                "accuracy": 0,
                "handling": 0,
                "reason":
                    "malformed_scientific_artifact",
            }
        )
        continue

    a = accuracy(out)

    if a is None:
        rows.append(
            {
                "cell": cell,
                "world": world,
                "score": 0,
                "accuracy": 0,
                "handling": 0,
                "reason":
                    "missing_or_malformed_numeric_result",
            }
        )
        continue

    acc = int(
        a["accuracy"]
    )

    hand = (
        3
        if world == "clean"
        else handling_state(
            world,
            out,
            acc,
        )
    )

    score = (
        acc
        if world == "clean"
        else min(
            acc,
            hand,
        )
    )

    guards = []

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

        guards.append(
            "analysis_usable_false"
        )

    if int(
        out.get(
            "_n_code_cells",
            0,
        )
    ) == 0:
        score = min(
            score,
            1,
        )

        guards.append(
            "zero_code_cells"
        )

    rows.append(
        {
            "cell":
                cell,

            "world":
                world,

            "score":
                int(score),

            "accuracy":
                acc,

            "handling":
                int(hand),

            "latent_heat_abs_error_kj_mol":
                a[
                    "latent_heat_abs_error_kj_mol"
                ],

            "max_temperature_abs_error_k":
                a[
                    "max_temperature_abs_error_k"
                ],

            "max_liquid_fraction_abs_error":
                a[
                    "max_liquid_fraction_abs_error"
                ],

            "regime_errors":
                a[
                    "regime_errors"
                ],

            "accuracy_components":
                a[
                    "components"
                ],

            "guards":
                guards,
        }
    )


out_path = (
    RUN
    / f"graded_{SUF}.json"
)

json.dump(
    rows,
    open(
        out_path,
        "w",
    ),
    indent=2,
)


print(
    f"=== {RUN} — {SUF} ==="
)

print(
    f"{'world':40} "
    f"{'score':>5} "
    f"{'dHerr':>9} "
    f"{'maxT':>9} "
    f"{'maxx':>9} "
    f"{'reg':>4} "
    f"{'acc':>4} "
    f"{'hand':>5}"
)

for r in rows:
    print(
        f"{r['world']:<40} "
        f"{r['score']:>5} "
        f"{r.get('latent_heat_abs_error_kj_mol', float('nan')):>9.4f} "
        f"{r.get('max_temperature_abs_error_k', float('nan')):>9.3f} "
        f"{r.get('max_liquid_fraction_abs_error', float('nan')):>9.4f} "
        f"{r.get('regime_errors', -1):>4} "
        f"{r['accuracy']:>4} "
        f"{r['handling']:>5}"
    )

scores = [
    r["score"]
    for r in rows
]

challenge = [
    r["score"]
    for r in rows
    if r["world"] != "clean"
]

print()
print(
    "mean:",
    float(
        np.mean(scores)
    ),
)

print(
    "challenge_mean:",
    float(
        np.mean(challenge)
    ),
)
