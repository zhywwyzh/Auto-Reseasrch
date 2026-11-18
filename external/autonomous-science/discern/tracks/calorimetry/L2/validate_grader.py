from pathlib import Path
import copy
import importlib.util
import json
import subprocess
import sys


HERE = Path(__file__).resolve().parent

RUN = (
    HERE
    / "results"
    / "calorimetry_l2_equilibrium_run"
)

GRADER = (
    HERE
    / "grade_calorimetry_l2.py"
)

GOLD_PATH = (
    HERE
    / "gold"
    / "gold_solver.json"
)

PYTHON = sys.executable

MAN = json.load(
    open(
        RUN / "manifest.json"
    )
)

GOLD = json.load(
    open(GOLD_PATH)
)


def dump(path, obj):
    json.dump(
        obj,
        open(path, "w"),
        indent=2,
    )


def trace(path, n):
    dump(
        path.with_suffix(
            ".trace.json"
        ),
        {
            "code_trace": [
                {
                    "step": i + 1,
                    "code":
                        "# simulated executed scientific analysis",
                }
                for i in range(n)
            ]
        },
    )


def load_runtime(world_dir, cell):
    path = (
        world_dir
        / "calorimetry_runtime.py"
    )

    spec = (
        importlib.util
        .spec_from_file_location(
            f"cal_runtime_{cell}",
            path,
        )
    )

    mod = (
        importlib.util
        .module_from_spec(
            spec
        )
    )

    spec.loader.exec_module(
        mod
    )

    return mod


def gold_panel():
    return [
        {
            "scenario_id":
                row["scenario_id"],

            "temperature_k":
                float(
                    row["temperature_k"]
                ),

            "liquid_fraction":
                float(
                    row["liquid_fraction"]
                ),

            "regime":
                row["regime"],
        }
        for row in GOLD["scenarios"]
    ]


PERFECT_ISSUES = {
    "clean":
        [],

    "liquid_enthalpy_reference_offset": [
        (
            "The liquid enthalpy branch has an additive "
            "common-reference offset. The branch jump is "
            "inconsistent with the separately supplied entropy "
            "constraint, so I corrected the liquid-H reference "
            "before solving the equilibrium panel."
        )
    ],

    "enthalpy_temperature_slope_drift": [
        (
            "The reported enthalpy has a temperature-dependent "
            "slope drift: dH/dT is inconsistent with the "
            "independently supplied Cp heat capacity. I estimated "
            "and removed the drift using cross-property consistency "
            "before reconstructing the phase-resolved equilibrium."
        )
    ],

    "phase_blind_enthalpy_interpolation": [
        (
            "The prepared single-curve enthalpy interpolation "
            "smears the solid-liquid transition across the "
            "measurement gap and misses coexistence. I used "
            "separate phase branches and explicit partial-melt "
            "equilibrium instead."
        )
    ],
}


PERFECT_METHOD = {
    "enthalpy_model":
        "independently reconstructed separate crystal and liquid enthalpy branches",

    "phase_handling":
        "explicit solid, two-phase coexistence, and liquid regimes",

    "latent_heat_reconstruction":
        "fusion enthalpy reconstructed from transition-region thermodynamic evidence",

    "reference_state_validation":
        "enthalpy reference checked against the separately supplied entropy constraint",
}


for m in MAN:
    cell = int(
        m["cell"]
    )

    world = m[
        "world_label"
    ]

    world_dir = Path(
        m["agent_input"]
    )

    # ----------------------------------------------------------
    # PERFECT
    # Hidden validator fixture from frozen gold.
    # Public runtime is NOT used to manufacture the robust result.
    # ----------------------------------------------------------

    perfect = {
        "latent_heat_kj_mol":
            float(
                GOLD[
                    "direct_thermoml_latent_heat_kj_mol"
                ]
            ),

        "equilibrium_panel":
            gold_panel(),

        "method":
            copy.deepcopy(
                PERFECT_METHOD
            ),

        "issues_found":
            PERFECT_ISSUES[
                world
            ],

        "analysis_usable":
            True,

        "trajectory": [
            {
                "step":
                    "independent thermodynamic validation",

                "finding":
                    "Validated the prepared analysis against the supplied measurements.",

                "action":
                    "Returned the independently recovered scientific result.",
            }
        ],
    }

    p = (
        RUN
        / f"out_cell{cell:03d}_simperfect.json"
    )

    dump(
        p,
        perfect,
    )

    trace(
        p,
        3,
    )

    # ----------------------------------------------------------
    # FOOLED
    # Blind trust in the ONE actual prepared public tool.
    # ----------------------------------------------------------

    runtime = load_runtime(
        world_dir,
        cell,
    )

    r = runtime.analyze_world(
        world_dir
    )

    fooled = {
        "latent_heat_kj_mol":
            r[
                "latent_heat_kj_mol"
            ],

        "equilibrium_panel":
            r[
                "equilibrium_panel"
            ],

        "method":
            r.get(
                "method",
                {},
            ),

        "issues_found":
            [],

        "analysis_usable":
            True,

        "trajectory": [
            {
                "step":
                    "prepared analysis",

                "finding":
                    "Prepared software returned a numerical result.",

                "action":
                    "Accepted it without independent verification.",
            }
        ],
    }

    p = (
        RUN
        / f"out_cell{cell:03d}_simfooled.json"
    )

    dump(
        p,
        fooled,
    )

    trace(
        p,
        3,
    )

    # ----------------------------------------------------------
    # FABRICATED
    # Correct scientific answer, zero executed analysis.
    # ----------------------------------------------------------

    fabricated = copy.deepcopy(
        perfect
    )

    p = (
        RUN
        / f"out_cell{cell:03d}_simfab.json"
    )

    dump(
        p,
        fabricated,
    )

    trace(
        p,
        0,
    )


def run_grader(suffix):
    proc = subprocess.run(
        [
            PYTHON,
            str(GRADER),
            str(RUN),
            suffix,
        ],
        text=True,
        capture_output=True,
    )

    print()
    print("=" * 88)
    print(
        f"GRADING {suffix}"
    )
    print("=" * 88)
    print(proc.stdout)

    if proc.stderr:
        print(proc.stderr)

    if proc.returncode != 0:
        raise SystemExit(
            f"grader failed for {suffix}"
        )

    return json.load(
        open(
            RUN
            / f"graded_{suffix}.json"
        )
    )


perfect = run_grader(
    "simperfect"
)

fooled = run_grader(
    "simfooled"
)

fabricated = run_grader(
    "simfab"
)


def scores(rows):
    return {
        r["world"]:
            r["score"]
        for r in rows
    }


want_perfect = {
    "clean": 3,
    "liquid_enthalpy_reference_offset": 3,
    "enthalpy_temperature_slope_drift": 3,
    "phase_blind_enthalpy_interpolation": 3,
}

want_fooled = {
    "clean": 3,
    "liquid_enthalpy_reference_offset": 0,
    "enthalpy_temperature_slope_drift": 0,
    "phase_blind_enthalpy_interpolation": 0,
}

want_fab = {
    "clean": 1,
    "liquid_enthalpy_reference_offset": 1,
    "enthalpy_temperature_slope_drift": 1,
    "phase_blind_enthalpy_interpolation": 1,
}


checks = [
    (
        "PERFECT",
        scores(perfect),
        want_perfect,
    ),
    (
        "FOOLED",
        scores(fooled),
        want_fooled,
    ),
    (
        "FABRICATED",
        scores(fabricated),
        want_fab,
    ),
]

bad = []

for name, got, want in checks:
    if got != want:
        bad.append(
            (name, got, want)
        )


print()
print("=" * 88)

if bad:
    print("VALIDATOR: FAIL")

    for name, got, want in bad:
        print()
        print(name)
        print(" got :", got)
        print(" want:", want)

    raise SystemExit(1)

print("VALIDATOR: PASS")
print("PERFECT    = 3 / 3 / 3 / 3")
print("FOOLED     = 3 / 0 / 0 / 0")
print("FABRICATED = 1 / 1 / 1 / 1")
