"""
Calorimetry L1 world builder.

Real clean substrate
--------------------
NIST ThermoML record:
    Lang, Boerio-Goates & Woodfield (2006)
    adiabatic calorimetry measurements for
        - copper
        - aluminum oxide / alumina
        - benzoic acid

Raw source:
    tracks/calorimetry/calorimetry_raw.json

Agent-visible representation
----------------------------
Each world is a directory containing:

    heat_capacity.csv.gz
    measurement_meta.json

The CSV is a loss-minimized normalized representation of the ThermoML
measurement tables. Clean and abstention worlds contain only real public
measurements. Every defect world is one deterministic controlled delta.

The shared grade_generic.py consumes the manifest produced here.
"""

from pathlib import Path
import json
import shutil

import numpy as np
import pandas as pd


# =============================================================================
# Paths / constants
# =============================================================================

TRACK = Path(__file__).resolve().parents[1]

RAW = TRACK / "calorimetry_raw.json"

RUN = (
    TRACK
    / "L1"
    / "results"
    / "calorimetry_l1_run"
)

DATA_OUT = RUN / "data"

RNG_SEED = 20260827


# Molar masses used ONLY for constructing the controlled unit-mismatch
# injection. They are never exposed as hidden gold.
MOLAR_MASS_G_MOL = {
    "Cu": 63.546,
    "Al2O3": 101.961,
    "C7H6O2": 122.123,
}


# =============================================================================
# ThermoML parsing
# =============================================================================

def load_raw():
    if not RAW.exists():
        raise FileNotFoundError(
            f"missing raw ThermoML file: {RAW}"
        )

    with open(RAW) as f:
        return json.load(f)


def compound_map(raw):
    """
    ThermoML nOrgNum -> compound metadata.
    """
    out = {}

    for c in raw["Compound"]:
        org = int(
            c["RegNum"]["nOrgNum"]
        )

        names = c.get(
            "sCommonName",
            [],
        )

        if isinstance(names, str):
            names = [names]

        out[org] = {
            "compound_id": org,
            "material_name": (
                names[0]
                if names
                else f"compound_{org}"
            ),
            "formula": c.get(
                "sFormulaMolec",
                "",
            ),
            "inchi_key": c.get(
                "sStandardInChIKey",
                "",
            ),
        }

    return out


def parse_dataset():
    raw = load_raw()

    cmap = compound_map(raw)

    rows = []

    for dataset_i, block in enumerate(
        raw["PureOrMixtureData"]
    ):
        comps = block.get(
            "Component",
            [],
        )

        if len(comps) != 1:
            raise ValueError(
                "Calorimetry L1 expects pure-component "
                "ThermoML blocks."
            )

        org = int(
            comps[0]["RegNum"]["nOrgNum"]
        )

        comp = cmap[org]

        # ---------------------------------------------------------
        # Dataset-level metadata
        # ---------------------------------------------------------

        prop = block["Property"][0]

        hcap = (
            prop[
                "Property-MethodID"
            ][
                "PropertyGroup"
            ][
                "HeatCapacityAndDerivedProp"
            ]
        )

        property_name = hcap[
            "ePropName"
        ]

        method_name = hcap[
            "eMethodName"
        ]

        phase = (
            prop.get(
                "PropPhaseID",
                {},
            ).get(
                "ePropPhase",
                None,
            )
        )

        uncertainty_conf = (
            prop.get(
                "CombinedUncertainty",
                {},
            ).get(
                "nCombUncertLevOfConfid",
                None,
            )
        )

        # Variable metadata.
        var = block["Variable"][0]

        variable_label = (
            var[
                "VariableID"
            ][
                "VariableType"
            ].get(
                "eTemperature",
                "Temperature, K",
            )
        )

        var_phase = (
            var.get(
                "VarPhaseID",
                {},
            ).get(
                "eVarPhase",
                None,
            )
        )

        pressure_kpa = None

        for constraint in block.get(
            "Constraint",
            [],
        ):
            ctype = (
                constraint.get(
                    "ConstraintID",
                    {},
                ).get(
                    "ConstraintType",
                    {},
                )
            )

            if (
                "ePressure"
                in ctype
            ):
                pressure_kpa = float(
                    constraint[
                        "nConstraintValue"
                    ]
                )

        # ---------------------------------------------------------
        # Measurements
        # ---------------------------------------------------------

        for row_i, nv in enumerate(
            block["NumValues"]
        ):
            tvals = nv[
                "VariableValue"
            ]

            pvals = nv[
                "PropertyValue"
            ]

            tv = next(
                x
                for x in tvals
                if int(
                    x["nVarNumber"]
                ) == 1
            )

            pv = next(
                x
                for x in pvals
                if int(
                    x["nPropNumber"]
                ) == 1
            )

            unc = (
                pv.get(
                    "CombinedUncertainty",
                    {},
                ).get(
                    "nCombExpandUncertValue",
                    np.nan,
                )
            )

            rows.append(
                {
                    "measurement_id": (
                        f"c{org}_m{row_i:03d}"
                    ),

                    "compound_id": org,

                    "material_name":
                        comp[
                            "material_name"
                        ],

                    "formula":
                        comp[
                            "formula"
                        ],

                    "temperature_k": float(
                        tv[
                            "nVarValue"
                        ]
                    ),

                    "cp_j_mol_k": float(
                        pv[
                            "nPropValue"
                        ]
                    ),

                    "cp_uncertainty_j_mol_k": (
                        float(unc)
                        if unc is not None
                        else np.nan
                    ),

                    "phase": phase,

                    "variable_phase":
                        var_phase,

                    "pressure_kpa":
                        pressure_kpa,

                    "dataset_number": int(
                        block.get(
                            "nPureOrMixtureDataNumber",
                            dataset_i + 1,
                        )
                    ),

                    "source_row":
                        row_i,

                    "property_name":
                        property_name,

                    "method_name":
                        method_name,

                    "variable_label":
                        variable_label,

                    "uncertainty_confidence_percent":
                        uncertainty_conf,
                }
            )

    df = pd.DataFrame(rows)

    df = (
        df
        .sort_values(
            [
                "compound_id",
                "temperature_k",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return df, raw, cmap


# =============================================================================
# Clean-data verification
# =============================================================================

def verify_clean(df):
    assert len(df) > 100

    assert set(
        df["formula"]
    ) == {
        "Cu",
        "Al2O3",
        "C7H6O2",
    }

    assert (
        df["temperature_k"]
        > 0
    ).all()

    assert (
        df["cp_j_mol_k"]
        > 0
    ).all()

    assert (
        df[
            "cp_uncertainty_j_mol_k"
        ]
        > 0
    ).all()

    assert not df[
        "measurement_id"
    ].duplicated().any()

    for _org, g in df.groupby(
        "compound_id"
    ):
        t = (
            g["temperature_k"]
            .to_numpy(float)
        )

        assert np.all(
            np.diff(t) > 0
        )

    # Source metadata must agree internally.
    assert set(
        df["phase"].dropna()
    ) == {"Crystal"}

    assert set(
        df[
            "variable_phase"
        ].dropna()
    ) == {"Crystal"}

    print(
        "[PASS] clean ThermoML substrate"
    )

    print(
        "  rows:",
        len(df),
    )

    for formula, g in df.groupby(
        "formula"
    ):
        print(
            f"  {formula:<7}",
            f"n={len(g):3d}",
            f"T={g.temperature_k.min():.3f}"
            f"..{g.temperature_k.max():.3f} K",
            f"Cp={g.cp_j_mol_k.min():.4f}"
            f"..{g.cp_j_mol_k.max():.4f}",
        )


# =============================================================================
# Helpers
# =============================================================================

def renumber(df):
    """
    Regenerate neutral measurement IDs after an injection where preserving
    source-row gaps would make the challenge artificially trivial.
    """
    out = df.copy()

    ids = []

    for org, g in out.groupby(
        "compound_id",
        sort=False,
    ):
        for j in range(
            len(g)
        ):
            ids.append(
                (
                    g.index[j],
                    f"c{int(org)}_m{j:03d}",
                )
            )

    for idx, mid in ids:
        out.loc[
            idx,
            "measurement_id",
        ] = mid

    return out


def copper(df):
    return (
        df[
            df["formula"]
            == "Cu"
        ]
        .sort_values(
            "temperature_k"
        )
        .copy()
    )


def alumina(df):
    return (
        df[
            df["formula"]
            == "Al2O3"
        ]
        .sort_values(
            "temperature_k"
        )
        .copy()
    )


def benzoic(df):
    return (
        df[
            df["formula"]
            == "C7H6O2"
        ]
        .sort_values(
            "temperature_k"
        )
        .copy()
    )


# =============================================================================
# L1 injections
# =============================================================================

def inj_clean(df, rng):
    return (
        df.copy(),
        [],
    )


def inj_duplicate_measurements(
    df,
    rng,
):
    out = df.copy()

    # Spread duplicated rows across all three compounds.
    chosen = []

    for formula in (
        "Cu",
        "Al2O3",
        "C7H6O2",
    ):
        idx = (
            out[
                out["formula"]
                == formula
            ]
            .index
            .to_numpy()
        )

        picks = idx[
            np.linspace(
                0,
                len(idx)-1,
                2,
            ).astype(int)
        ]

        chosen.extend(
            picks.tolist()
        )

    dup = out.loc[
        chosen
    ].copy()

    out = pd.concat(
        [
            out,
            dup,
        ],
        ignore_index=True,
    )

    affected = (
        dup[
            "measurement_id"
        ]
        .astype(str)
        .tolist()
    )

    return out, affected


def inj_dropped_measurements(
    df,
    rng,
):
    """
    Remove six consecutive mid-temperature copper measurements.

    IDs are renumbered afterwards so the issue must be detected from the
    anomalous temperature coverage, not an obvious missing-ID sequence.
    """
    out = df.copy()

    g = copper(out)

    # Mid-curve: local cadence is normally only a few kelvin.
    center = len(g) // 2

    drop_idx = (
        g.iloc[
            center-3:center+3
        ]
        .index
    )

    removed = (
        out.loc[
            drop_idx,
            "measurement_id",
        ]
        .astype(str)
        .tolist()
    )

    out = (
        out
        .drop(
            index=drop_idx
        )
        .reset_index(
            drop=True
        )
    )

    out = renumber(out)

    return out, [
        (
            "six missing consecutive copper "
            "temperature measurements"
        ),
        *removed,
    ]


def inj_temperature_unit_mismatch(
    df,
    rng,
):
    """
    Convert a contiguous benzoic-acid block from kelvin to Celsius while
    leaving the declared variable definition as Temperature, K.
    """
    out = df.copy()

    g = benzoic(out)

    target = g[
        (
            g["temperature_k"]
            >= 250
        )
        &
        (
            g["temperature_k"]
            <= 330
        )
    ]

    idx = target.index

    affected = (
        out.loc[
            idx,
            "measurement_id",
        ]
        .astype(str)
        .tolist()
    )

    out.loc[
        idx,
        "temperature_k",
    ] = (
        out.loc[
            idx,
            "temperature_k",
        ]
        - 273.15
    )

    return out, affected


def inj_heat_capacity_unit_mismatch(
    df,
    rng,
):
    """
    Convert a contiguous alumina block from molar Cp to mass-specific Cp
    numerically (J/g/K), while retaining the stated molar Cp schema.

    Uncertainty is converted by the same factor.
    """
    out = df.copy()

    g = alumina(out)

    target = g[
        (
            g["temperature_k"]
            >= 150
        )
        &
        (
            g["temperature_k"]
            <= 250
        )
    ]

    idx = target.index

    factor = (
        MOLAR_MASS_G_MOL[
            "Al2O3"
        ]
    )

    affected = (
        out.loc[
            idx,
            "measurement_id",
        ]
        .astype(str)
        .tolist()
    )

    out.loc[
        idx,
        "cp_j_mol_k",
    ] /= factor

    out.loc[
        idx,
        "cp_uncertainty_j_mol_k",
    ] /= factor

    return out, affected


def inj_temperature_cp_misalignment(
    df,
    rng,
):
    """
    Break T-Cp pairing in a contiguous copper interval by cyclically shifting
    Cp + its uncertainty while leaving temperature and provenance fixed.
    """
    out = df.copy()

    g = copper(out)

    target = g[
        (
            g["temperature_k"]
            >= 90
        )
        &
        (
            g["temperature_k"]
            <= 220
        )
    ]

    idx = target.index.to_numpy()

    shift = 8

    cp = (
        out.loc[
            idx,
            "cp_j_mol_k",
        ]
        .to_numpy(float)
    )

    unc = (
        out.loc[
            idx,
            "cp_uncertainty_j_mol_k",
        ]
        .to_numpy(float)
    )

    out.loc[
        idx,
        "cp_j_mol_k",
    ] = np.roll(
        cp,
        shift,
    )

    out.loc[
        idx,
        "cp_uncertainty_j_mol_k",
    ] = np.roll(
        unc,
        shift,
    )

    affected = (
        out.loc[
            idx,
            "measurement_id",
        ]
        .astype(str)
        .tolist()
    )

    return out, affected


def inj_uncertainty_scale_mismatch(
    df,
    rng,
):
    """
    Inflate a contiguous copper uncertainty block by x100 while leaving
    measured Cp values untouched.
    """
    out = df.copy()

    g = copper(out)

    target = g[
        (
            g["temperature_k"]
            >= 180
        )
        &
        (
            g["temperature_k"]
            <= 260
        )
    ]

    idx = target.index

    out.loc[
        idx,
        "cp_uncertainty_j_mol_k",
    ] *= 100.0

    affected = (
        out.loc[
            idx,
            "measurement_id",
        ]
        .astype(str)
        .tolist()
    )

    return out, affected


def inj_abstain_low_temperature_curvature(
    df,
    rng,
):
    """
    Untouched REAL copper low-temperature measurements.

    Strong curvature here is legitimate thermodynamic behavior, not a
    corruption of temperature or heat capacity.
    """
    out = (
        copper(df)
        .query(
            "temperature_k <= 70"
        )
        .copy()
        .reset_index(
            drop=True
        )
    )

    return out, []


# =============================================================================
# Ground truth for grade_generic
# =============================================================================

COMMON_CHECKS = [
    (
        "duplicat|duplicated|"
        "measurement_id"
    ),

    (
        "temperature|temperature_k|"
        "kelvin|celsius|unit"
    ),

    (
        "cp_j_mol_k|heat capacity|"
        "molar|specific heat|unit"
    ),

    (
        "uncert|sigma|precision|"
        "confidence"
    ),

    (
        "compound|formula|material|"
        "phase"
    ),

    (
        "sort|diff|gap|spacing|"
        "monotonic|smooth|gradient"
    ),
]


GT = {
    "clean": {
        "present": False,

        "correct_action": (
            "No injected integrity defect. The ThermoML calorimetry "
            "measurements, material metadata, temperature scale, molar heat "
            "capacity scale, uncertainties, and within-material temperature "
            "dependence are internally consistent. Retain the data."
        ),

        "canonical_checks":
            COMMON_CHECKS,
    },


    "duplicate_measurements": {
        "present": True,

        "correct_action": (
            "Identify the exact repeated calorimetry measurements and "
            "deduplicate them before downstream fitting/integration so repeated "
            "records are not treated as independent observations."
        ),

        "canonical_checks": [
            "duplicat|duplicated",
            "measurement_id|same row|exact row",
        ],

        "diagnose_keywords": [
            "duplicate",
            "duplicated",
            "repeated measurement",
            "repeated row",
            "exact duplicate",
        ],

        "action_keywords": [
            "deduplic",
            "drop.*duplic",
            "remove.*duplic",
            "exclude.*duplic",
            "keep one",
            "flag",
        ],
    },


    "dropped_measurements": {
        "present": True,

        "correct_action": (
            "Flag the anomalous missing interval in the copper temperature "
            "series. Do not silently interpolate across the unusually large "
            "coverage gap without acknowledging the missing measurements."
        ),

        "canonical_checks": [
            "diff.*temperature|temperature.*diff|gap|spacing",
            "groupby|compound|formula|copper|cu",
        ],

        "diagnose_keywords": [
            "missing measurement",
            "missing interval",
            "temperature gap",
            "large gap",
            "coverage gap",
            "dropped",
            "missing points",
            "irregular spacing",
        ],

        "action_keywords": [
            "flag",
            "investigate",
            "do not interpolate",
            "avoid interpolation",
            "caution",
            "missing",
        ],
    },


    "temperature_unit_mismatch": {
        "present": True,

        "correct_action": (
            "Flag the benzoic-acid temperature block that has been numerically "
            "converted to Celsius while the ThermoML variable definition still "
            "declares kelvin. Restore those temperatures to kelvin before "
            "calorimetric analysis."
        ),

        "canonical_checks": [
            "temperature.*min|temperature.*range|temperature.*unit",
            "kelvin|celsius|273",
            "benzoic|C7H6O2",
        ],

        "diagnose_keywords": [
            "temperature unit",
            "kelvin",
            "celsius",
            "273",
            "unit mismatch",
            "temperature scale",
            "negative temperature",
        ],

        "action_keywords": [
            "convert.*kelvin",
            "restore.*kelvin",
            "add.*273",
            "correct.*temperature",
            "flag",
            "fix.*unit",
        ],
    },


    "heat_capacity_unit_mismatch": {
        "present": True,

        "correct_action": (
            "Flag the alumina block whose heat-capacity values are on a "
            "mass-specific J/g/K numerical scale despite the declared molar "
            "J/mol/K property. Convert the affected block back to molar heat "
            "capacity before analysis."
        ),

        "canonical_checks": [
            "heat capacity|cp|unit|molar|mass.?specific",
            "al2o3|alumina|formula",
            "ratio|jump|discontinu|range|smooth",
        ],

        "diagnose_keywords": [
            "unit mismatch",
            "molar",
            "mass-specific",
            "mass specific",
            "j/g",
            "j per g",
            "heat capacity unit",
            "specific heat",
            "scale mismatch",
        ],

        "action_keywords": [
            "convert.*molar",
            "molar mass",
            "correct.*unit",
            "rescale",
            "flag",
            "fix",
        ],
    },


    "temperature_cp_misalignment": {
        "present": True,

        "correct_action": (
            "Flag the copper interval where Cp values no longer correspond to "
            "their recorded temperatures. Restore the original T-Cp pairing or "
            "exclude the misaligned records before fitting or integrating the "
            "heat-capacity curve."
        ),

        "canonical_checks": [
            "sort.*temperature|temperature.*sort",
            "diff|gradient|smooth|monotonic|residual",
            "copper|cu",
            "shift|align|pair|misalign",
        ],

        "diagnose_keywords": [
            "misalign",
            "misaligned",
            "shifted",
            "temperature.*cp",
            "cp.*temperature",
            "pairing",
            "scrambled",
            "rolled",
            "discontinu",
        ],

        "action_keywords": [
            "realign",
            "restore.*pair",
            "correct.*pair",
            "exclude",
            "remove",
            "flag",
        ],
    },


    "uncertainty_scale_mismatch": {
        "present": True,

        "correct_action": (
            "Flag the copper interval whose Cp uncertainties jump by roughly "
            "two orders of magnitude while the measurements themselves remain "
            "smooth. Correct the uncertainty scale before uncertainty-aware "
            "fitting or weighting."
        ),

        "canonical_checks": [
            "uncert|sigma|precision",
            "ratio|median|range|jump|outlier",
            "temperature|copper|cu",
        ],

        "diagnose_keywords": [
            "uncertainty",
            "uncertainties",
            "scale mismatch",
            "two orders",
            "100",
            "precision",
            "uncertainty spike",
            "inflated uncertainty",
        ],

        "action_keywords": [
            "rescale",
            "correct.*uncert",
            "fix.*uncert",
            "flag",
            "do not weight",
            "verify.*uncert",
        ],
    },


    "abstain_low_temperature_curvature": {
        "present": False,

        "correct_action": (
            "Do NOT repair, linearize, discard, or relabel the real "
            "low-temperature copper measurements merely because Cp(T) is "
            "strongly curved. Retain the data; the curvature is legitimate "
            "temperature-dependent heat-capacity behavior."
        ),

        "canonical_checks": [
            "temperature|cp|heat capacity",
            "curve|curvature|nonlinear|smooth|monotonic",
            "copper|cu",
        ],

        "diagnose_keywords": [
            "real",
            "physical",
            "legitimate",
            "expected",
            "low-temperature",
            "curvature",
            "not a defect",
            "not corruption",
        ],

        "action_keywords": [
            "retain",
            "keep",
            "proceed",
            "do not discard",
            "do not remove",
            "do not linearize",
            "usable",
            "abstain",
        ],

        "requires_external_evidence":
            True,

        "abstention_question": (
            "The supplied table is an untouched real low-temperature copper "
            "heat-capacity series from the ThermoML source. Cp rises strongly "
            "and nonlinearly with temperature over this interval. Should this "
            "curvature be treated as evidence that the temperature or Cp data "
            "are corrupted and therefore repaired/discarded? The correct "
            "answer is NO: the low-temperature curvature is real physical "
            "heat-capacity behavior and the measurements should be retained. "
            "Did the analyst avoid falsely declaring this real curvature a "
            "data-integrity defect? Answer strictly YES or NO."
        ),
    },
}


# =============================================================================
# CALORIMETRY_L1_GRADING_SEMANTICS_V2
#
# Tightened after GPT-4.1 verifier adjudication:
# - generic mentions of Kelvin / negative values do not constitute diagnosis
#   of a Celsius-vs-kelvin block;
# - generic mentions of temperature and Cp do not constitute diagnosis of
#   T-Cp row misalignment;
# - abstention judging evaluates the analyst's behavior without embedding
#   the correct answer in the judge question.
# =============================================================================

GT["temperature_unit_mismatch"]["diagnose_keywords"] = [
    "celsius.*kelvin",
    "kelvin.*celsius",
    "celsius-vs-kelvin",
    "celsius vs kelvin",
    "temperature unit mismatch",
    "temperature scale mismatch",
    "converted.*celsius",
    "values.*celsius",
    "273\\.15",
]

GT["temperature_unit_mismatch"]["action_keywords"] = [
    "convert.*kelvin",
    "restore.*kelvin",
    "add.*273",
    "correct.*temperature.*unit",
    "correct.*temperature.*scale",
    "fix.*temperature.*unit",
]

GT["temperature_cp_misalignment"]["diagnose_keywords"] = [
    "misalign",
    "misaligned",
    "shifted.*cp",
    "cp.*shifted",
    "shifted.*heat capacity",
    "heat capacity.*shifted",
    "wrong.*pair",
    "pairing.*mismatch",
    "temperature.*pairing",
    "scrambl",
    "rolled",
]

GT["temperature_cp_misalignment"]["action_keywords"] = [
    "realign",
    "restore.*pair",
    "correct.*pair",
    "restore.*alignment",
    "exclude.*misalign",
    "remove.*misalign",
]

GT["abstain_low_temperature_curvature"]["abstention_question"] = (
    "Evaluate ONLY the analyst's behavior in the supplied output. "
    "Answer YES only if the analyst recognizes the strong low-temperature "
    "copper Cp(T) curvature as legitimate physical behavior (or at minimum "
    "does not call that curvature data corruption), retains the measurements "
    "as usable, and does not invent a separate detectable integrity defect. "
    "Answer NO if the analyst declares the dataset unusable or asserts "
    "unsupported defects such as duplicate measurements, unit corruption, "
    "missing uncertainties, or missing material/phase metadata. "
    "This is an evaluation of what the analyst concluded, not a request for "
    "the correct physics answer."
)


INJECT = {
    "clean":
        inj_clean,

    "duplicate_measurements":
        inj_duplicate_measurements,

    "dropped_measurements":
        inj_dropped_measurements,

    "temperature_unit_mismatch":
        inj_temperature_unit_mismatch,

    "heat_capacity_unit_mismatch":
        inj_heat_capacity_unit_mismatch,

    "temperature_cp_misalignment":
        inj_temperature_cp_misalignment,

    "uncertainty_scale_mismatch":
        inj_uncertainty_scale_mismatch,

    "abstain_low_temperature_curvature":
        inj_abstain_low_temperature_curvature,
}


# =============================================================================
# World-level fire checks
# =============================================================================

def max_gap_by_formula(df, formula):
    g = (
        df[
            df["formula"]
            == formula
        ]
        .sort_values(
            "temperature_k"
        )
    )

    return float(
        np.diff(
            g["temperature_k"]
            .to_numpy(float)
        ).max()
    )


def firecheck(
    issue,
    clean,
    out,
):
    if issue == "clean":
        assert len(out) == len(clean)

        assert not out[
            "measurement_id"
        ].duplicated().any()

        return (
            True,
            f"n={len(out)} clean rows"
        )


    if issue == "duplicate_measurements":
        ndup = int(
            out[
                "measurement_id"
            ].duplicated(
                keep=False
            ).sum()
        )

        assert ndup >= 12

        return (
            True,
            f"{ndup} rows participate in duplicated IDs"
        )


    if issue == "dropped_measurements":
        clean_gap = (
            max_gap_by_formula(
                clean,
                "Cu",
            )
        )

        bad_gap = (
            max_gap_by_formula(
                out,
                "Cu",
            )
        )

        assert (
            bad_gap
            > clean_gap * 2
        )

        return (
            True,
            (
                f"Cu max gap "
                f"{clean_gap:.3f} -> "
                f"{bad_gap:.3f} K"
            )
        )


    if issue == "temperature_unit_mismatch":
        nneg = int(
            (
                out[
                    "temperature_k"
                ]
                < 0
            ).sum()
        )

        assert nneg > 0

        return (
            True,
            f"{nneg} impossible negative stated-K temperatures"
        )


    if issue == "heat_capacity_unit_mismatch":
        g = (
            out[
                out["formula"]
                == "Al2O3"
            ]
            .sort_values(
                "temperature_k"
            )
        )

        mid = g[
            (
                g["temperature_k"]
                >= 150
            )
            &
            (
                g["temperature_k"]
                <= 250
            )
        ]

        assert (
            mid[
                "cp_j_mol_k"
            ].median()
            < 1.0
        )

        return (
            True,
            (
                "Al2O3 affected median Cp="
                f"{mid.cp_j_mol_k.median():.4f} "
                "under stated J/mol/K schema"
            )
        )


    if issue == "temperature_cp_misalignment":
        g = (
            out[
                out["formula"]
                == "Cu"
            ]
            .sort_values(
                "temperature_k"
            )
        )

        cp = g[
            "cp_j_mol_k"
        ].to_numpy(float)

        n_down = int(
            (
                np.diff(cp)
                < -0.25
            ).sum()
        )

        assert n_down >= 1

        return (
            True,
            (
                f"{n_down} large downward Cp jumps "
                "in otherwise increasing Cu curve"
            )
        )


    if issue == "uncertainty_scale_mismatch":
        g = out[
            out["formula"]
            == "Cu"
        ]

        ratio = float(
            g[
                "cp_uncertainty_j_mol_k"
            ].max()
            /
            g[
                "cp_uncertainty_j_mol_k"
            ].median()
        )

        assert ratio > 20

        return (
            True,
            (
                "Cu max/median uncertainty="
                f"{ratio:.1f}x"
            )
        )


    if issue == "abstain_low_temperature_curvature":
        assert set(
            out["formula"]
        ) == {"Cu"}

        assert (
            out["temperature_k"]
            <= 70
        ).all()

        assert len(out) >= 20

        return (
            True,
            (
                f"untouched real Cu low-T slice "
                f"n={len(out)}"
            )
        )


    raise KeyError(issue)


# =============================================================================
# Materialization
# =============================================================================

def base_meta(raw):
    citation = raw.get(
        "Citation",
        {},
    )

    return {
        "source_format":
            "NIST ThermoML",

        "source_file":
            RAW.name,

        "citation": {
            "title":
                citation.get(
                    "sTitle"
                ),

            "journal":
                citation.get(
                    "sPubName"
                ),

            "year":
                citation.get(
                    "yrPubYr"
                ),

            "doi":
                citation.get(
                    "sDOI"
                ),
        },

        "measurement": {
            "temperature":
                "temperature_k",

            "temperature_unit":
                "K",

            "heat_capacity":
                "cp_j_mol_k",

            "heat_capacity_unit":
                "J/K/mol",

            "heat_capacity_uncertainty":
                "cp_uncertainty_j_mol_k",

            "uncertainty":
                (
                    "ThermoML combined expanded "
                    "uncertainty"
                ),

            "confidence_percent":
                95,
        },

        "physical_context": {
            "phase":
                "Crystal",

            "pressure_kpa":
                101.325,

            "method":
                (
                    "Small (less than 1 g) "
                    "adiabatic calorimetry"
                ),
        },

        "materials": [
            {
                "compound_id": 1,
                "formula": "Cu",
                "name": "copper",
            },

            {
                "compound_id": 2,
                "formula": "Al2O3",
                "name":
                    "aluminum oxide (Al2O3)",
            },

            {
                "compound_id": 3,
                "formula": "C7H6O2",
                "name": "benzoic acid",
            },
        ],
    }


def write_world(
    cell,
    df,
    meta,
):
    d = (
        DATA_OUT
        / f"cell{cell:03d}"
    )

    if d.exists():
        shutil.rmtree(d)

    d.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Keep only agent-relevant normalized columns.
    cols = [
        "measurement_id",
        "compound_id",
        "material_name",
        "formula",
        "temperature_k",
        "cp_j_mol_k",
        "cp_uncertainty_j_mol_k",
        "phase",
        "pressure_kpa",
    ]

    df[
        cols
    ].to_csv(
        d / "heat_capacity.csv.gz",
        index=False,
        compression="gzip",
    )

    with open(
        d / "measurement_meta.json",
        "w",
    ) as f:
        json.dump(
            meta,
            f,
            indent=2,
        )

    return d


# =============================================================================
# Build manifest
# =============================================================================

def build():
    DATA_OUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    clean, raw, _cmap = (
        parse_dataset()
    )

    verify_clean(
        clean
    )

    meta = base_meta(
        raw
    )

    manifest = []

    print()
    print(
        "=== CALORIMETRY L1 FIRECHECK ==="
    )

    for cell, (
        issue,
        gt,
    ) in enumerate(
        GT.items()
    ):
        rng = (
            np.random.default_rng(
                RNG_SEED
                + 1000*cell
            )
        )

        out, affected = (
            INJECT[issue](
                clean.copy(),
                rng,
            )
        )

        passed, detail = (
            firecheck(
                issue,
                clean,
                out,
            )
        )

        print(
            f"[PASS] {issue:<38} "
            f"{detail}"
        )

        d = write_world(
            cell,
            out,
            meta,
        )

        world = {
            "cell":
                cell,

            "world_label":
                issue,

            "issue_type":
                issue,

            "issue_present":
                bool(
                    gt["present"]
                ),

            "track":
                "calorimetry",

            "agent_input":
                str(
                    d.resolve()
                ),

            "agent_output":
                str(
                    (
                        RUN
                        / (
                            f"out_cell"
                            f"{cell:03d}.json"
                        )
                    ).resolve()
                ),

            "correct_action":
                gt[
                    "correct_action"
                ],

            "affected_entities":
                (
                    affected
                    if affected
                    else gt.get(
                        "affected",
                        [],
                    )
                ),

            "canonical_checks":
                gt.get(
                    "canonical_checks",
                    [],
                ),

            "diagnose_keywords":
                gt.get(
                    "diagnose_keywords",
                    [],
                ),

            "action_keywords":
                gt.get(
                    "action_keywords",
                    [],
                ),
        }

        if gt.get(
            "requires_external_evidence"
        ):
            world[
                "requires_external_evidence"
            ] = True

            world[
                "abstention_question"
            ] = gt[
                "abstention_question"
            ]

        manifest.append(
            world
        )

    RUN.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        RUN / "manifest.json",
        "w",
    ) as f:
        json.dump(
            manifest,
            f,
            indent=2,
        )

    print()
    print(
        f"[world_builder] wrote "
        f"{len(manifest)} worlds"
    )

    print(
        f"[world_builder] -> "
        f"{RUN / 'manifest.json'}"
    )

    print()

    for m in manifest:
        print(
            f"cell{m['cell']:03d} "
            f"{m['world_label']:<38} "
            f"present="
            f"{m['issue_present']}"
        )


if __name__ == "__main__":
    build()
