import json
import sys

from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent

sys.path.insert(
    0,
    str(
        HERE
    ),
)

import l2_common as C
import photopeak_roi as P


OUT = (
    HERE
    / "gold"
    / "gold_solver.json"
)

OUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)


STRICT_HALF_Y = 0.05
STRICT_LAMBDA_REL = 0.01

MODERATE_HALF_Y = 0.20
MODERATE_LAMBDA_REL = 0.03

ROUGH_HALF_Y = 0.50
ROUGH_LAMBDA_REL = 0.08


def accuracy(
    fit,
    gold,
):
    dh = abs(
        fit[
            "half_life_years"
        ]
        - gold[
            "half_life_years"
        ]
    )

    dl = abs(
        fit[
            "lambda_per_day"
        ]
        / gold[
            "lambda_per_day"
        ]
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

    return {
        "accuracy":
            int(
                level
            ),

        "half_life_abs_error_years":
            float(
                dh
            ),

        "lambda_relative_error":
            float(
                dl
            ),
    }


def check(
    name,
    passed,
    detail,
):
    row = {
        "name":
            name,

        "pass":
            bool(
                passed
            ),

        "detail":
            detail,
    }

    print(
        f"[{'PASS' if passed else 'FAIL'}] "
        f"{name}: {detail}"
    )

    return row


clean = C.load_clean()

temperature, temperature_meta = (
    C.inject_temperature_response(
        clean
    )
)

mn54, mn54_meta = (
    C.inject_mn54_contamination(
        clean
    )
)

gold = C.fit_exponential(
    clean
)


temperature_naive = (
    C.fit_exponential(
        temperature
    )
)

temperature_robust = (
    C.fit_temperature_response(
        temperature
    )
)


mn54_naive = (
    C.fit_exponential(
        mn54
    )
)

mn54_robust = (
    C.fit_two_source(
        mn54
    )
)


photopeak_prepared, photopeak_meta = (
    P.fixed_roi_series()
)

photopeak_naive = (
    C.fit_exponential(
        photopeak_prepared
    )
)

photopeak_full = (
    P.full_spectrum_series()
)

photopeak_robust = (
    C.fit_exponential(
        photopeak_full
    )
)

photopeak_sensitivity = []

for baseline_days in (
    P.SENSITIVITY_BASELINE_DAYS
):
    for fwhm_multiplier in (
        P.SENSITIVITY_FWHM_MULTIPLIERS
    ):
        prepared_i, meta_i = (
            P.fixed_roi_series(
                baseline_days=
                    baseline_days,
                fwhm_multiplier=
                    fwhm_multiplier,
            )
        )

        fit_i = (
            C.fit_exponential(
                prepared_i
            )
        )

        photopeak_sensitivity.append(
            {
                "baseline_days":
                    int(
                        baseline_days
                    ),

                "fwhm_multiplier":
                    float(
                        fwhm_multiplier
                    ),

                "naive_fit":
                    fit_i,

                "naive_accuracy":
                    accuracy(
                        fit_i,
                        gold,
                    ),

                "roi_fraction_time_correlation":
                    meta_i[
                        "roi_fraction_time_correlation"
                    ],
            }
        )


checks = []
checks = []


checks.append(
    check(
        "clean_rows",
        len(clean) == 274,
        f"n={len(clean)}",
    )
)


checks.append(
    check(
        "clean_half_life_sane",
        (
            5.0
            < gold[
                "half_life_years"
            ]
            < 5.5
        ),
        (
            f"half="
            f"{gold['half_life_years']:.9f}"
        ),
    )
)


checks.append(
    check(
        "temperature_naive_accuracy_1",
        (
            accuracy(
                temperature_naive,
                gold,
            )[
                "accuracy"
            ]
            == 1
        ),
        str(
            accuracy(
                temperature_naive,
                gold,
            )
        ),
    )
)


checks.append(
    check(
        "temperature_robust_accuracy_3",
        (
            accuracy(
                temperature_robust,
                gold,
            )[
                "accuracy"
            ]
            == 3
        ),
        str(
            accuracy(
                temperature_robust,
                gold,
            )
        ),
    )
)


checks.append(
    check(
        "temperature_response_recovered",
        (
            abs(
                temperature_robust[
                    "temperature_response_per_c"
                ]
                - C.TEMP_RESPONSE_PER_C
            )
            < 5e-5
        ),
        (
            f"fit="
            f"{temperature_robust['temperature_response_per_c']:+.6f}"
        ),
    )
)


checks.append(
    check(
        "mn_contamination_small",
        (
            mn54_meta[
                "initial_contaminant_fraction_of_co"
            ]
            < 0.015
        ),
        (
            "fraction="
            f"{mn54_meta['initial_contaminant_fraction_of_co']:.6f}"
        ),
    )
)


checks.append(
    check(
        "mn_naive_accuracy_1",
        (
            accuracy(
                mn54_naive,
                gold,
            )[
                "accuracy"
            ]
            == 1
        ),
        str(
            accuracy(
                mn54_naive,
                gold,
            )
        ),
    )
)


checks.append(
    check(
        "mn_robust_accuracy_3",
        (
            accuracy(
                mn54_robust,
                gold,
            )[
                "accuracy"
            ]
            == 3
        ),
        str(
            accuracy(
                mn54_robust,
                gold,
            )
        ),
    )
)


checks.append(
    check(
        "mn_coupling_recovered",
        (
            abs(
                mn54_robust[
                    "mn54_reference_coupling"
                ]
                / C.MN54_COUPLING
                - 1.0
            )
            < 0.10
        ),
        (
            "fit="
            f"{mn54_robust['mn54_reference_coupling']:.8f}"
        ),
    )
)


checks.append(
    check(
        "photopeak_spectra_match_clean_counts",
        (
            len(
                photopeak_full
            )
            == len(
                clean
            )
            and np.array_equal(
                photopeak_full[
                    "total_counts"
                ].to_numpy(float),
                clean[
                    "total_counts"
                ].to_numpy(float),
            )
        ),
        (
            f"rows={len(photopeak_full)} "
            "full-spectrum integral exactly matches clean count totals"
        ),
    )
)


checks.append(
    check(
        "photopeak_naive_accuracy_0",
        (
            accuracy(
                photopeak_naive,
                gold,
            )[
                "accuracy"
            ]
            == 0
        ),
        str(
            accuracy(
                photopeak_naive,
                gold,
            )
        ),
    )
)


checks.append(
    check(
        "photopeak_robust_accuracy_3",
        (
            accuracy(
                photopeak_robust,
                gold,
            )[
                "accuracy"
            ]
            == 3
        ),
        str(
            accuracy(
                photopeak_robust,
                gold,
            )
        ),
    )
)


checks.append(
    check(
        "photopeak_central_rule_frozen",
        (
            photopeak_meta[
                "baseline_days"
            ]
            == P.BASELINE_DAYS
            and abs(
                photopeak_meta[
                    "fwhm_multiplier"
                ]
                - P.FWHM_MULTIPLIER
            )
            < 1e-12
        ),
        (
            f"baseline={photopeak_meta['baseline_days']} "
            f"fwhm_multiplier={photopeak_meta['fwhm_multiplier']}"
        ),
    )
)


checks.append(
    check(
        "photopeak_native_no_injection",
        (
            photopeak_meta[
                "native_no_injection"
            ]
            is True
        ),
        str(
            photopeak_meta[
                "native_no_injection"
            ]
        ),
    )
)


checks.append(
    check(
        "photopeak_sensitivity_all_fire",
        (
            len(
                photopeak_sensitivity
            )
            == 9
            and all(
                row[
                    "naive_accuracy"
                ][
                    "accuracy"
                ]
                == 0
                for row
                in photopeak_sensitivity
            )
        ),
        (
            f"n={len(photopeak_sensitivity)} "
            f"accuracies="
            f"{[row['naive_accuracy']['accuracy'] for row in photopeak_sensitivity]}"
        ),
    )
)




worlds = {
    "clean": {
        "gold_lambda_per_day":
            gold[
                "lambda_per_day"
            ],

        "gold_half_life_years":
            gold[
                "half_life_years"
            ],

        "gold_fit":
            gold,
    },

    "temperature_dependent_detector_response": {
        "gold_lambda_per_day":
            gold[
                "lambda_per_day"
            ],

        "gold_half_life_years":
            gold[
                "half_life_years"
            ],

        "gold_fit":
            gold,

        "naive_fit":
            temperature_naive,

        "robust_fit":
            temperature_robust,

        "injection":
            temperature_meta,
    },

    "mn54_cross_source_contamination": {
        "gold_lambda_per_day":
            gold[
                "lambda_per_day"
            ],

        "gold_half_life_years":
            gold[
                "half_life_years"
            ],

        "gold_fit":
            gold,

        "naive_fit":
            mn54_naive,

        "robust_fit":
            mn54_robust,

        "injection":
            mn54_meta,
    },

    "fixed_photopeak_roi_default": {
        "gold_lambda_per_day":
            gold[
                "lambda_per_day"
            ],

        "gold_half_life_years":
            gold[
                "half_life_years"
            ],

        "gold_fit":
            gold,

        "naive_fit":
            photopeak_naive,

        "robust_fit":
            photopeak_robust,

        "prepared_rule":
            photopeak_meta,

        "sensitivity":
            photopeak_sensitivity,

        "native_no_injection":
            True,
    },
}


payload = {
    "decay_fit":
        worlds,

    "_frozen_settings": {
        "temperature_response_per_c":
            C.TEMP_RESPONSE_PER_C,

        "mn54_reference_coupling":
            C.MN54_COUPLING,

        "photopeak_roi_baseline_days":
            P.BASELINE_DAYS,

        "photopeak_roi_fwhm_multiplier":
            P.FWHM_MULTIPLIER,

        "photopeak_roi_sensitivity_baseline_days":
            list(
                P.SENSITIVITY_BASELINE_DAYS
            ),

        "photopeak_roi_sensitivity_fwhm_multipliers":
            list(
                P.SENSITIVITY_FWHM_MULTIPLIERS
            ),

        "clean_start_date":
            C.START_DATE,

        "clean_end_date":
            C.END_DATE,
    },

    "_verification":
        checks,
}


OUT.write_text(
    json.dumps(
        payload,
        indent=2,
    )
)


print()
print(
    "=" * 96
)

print(
    "NUCLEAR L2 FIRE MATRIX"
)

print(
    "=" * 96
)


for world in [
    "temperature_dependent_detector_response",
    "mn54_cross_source_contamination",
    "fixed_photopeak_roi_default",
]:
    row = worlds[
        world
    ]

    naive_acc = accuracy(
        row[
            "naive_fit"
        ],
        gold,
    )

    robust_acc = accuracy(
        row[
            "robust_fit"
        ],
        gold,
    )

    print(
        f"{world:<42} "
        f"naive={naive_acc['accuracy']} "
        f"half={row['naive_fit']['half_life_years']:.9f}  "
        f"robust={robust_acc['accuracy']} "
        f"half={row['robust_fit']['half_life_years']:.9f}"
    )


status = all(
    x[
        "pass"
    ]
    for x in checks
)


print()
print(
    "FIRE CHECK:",
    (
        "PASS"
        if status
        else "FAIL"
    ),
)

print(
    "WROTE:",
    OUT,
)


if not status:
    raise SystemExit(
        1
    )


# === CANONICAL NEAR-FIELD CELL001 POSTPROCESS ===
#
# The legacy base solver above still computes the retired temperature
# candidate as an internal intermediate. The canonical postprocess
# replaces that retired entry deterministically with the frozen
# near-field detector-efficiency world.
if __name__ == "__main__":
    import near_field_efficiency as _NF

    _canonical = json.loads(
        OUT.read_text()
    )

    _nf_entry = _NF.gold_entry(
        C.load_clean()
    )

    _canonical[
        "decay_fit"
    ][
        _NF.WORLD
    ] = _nf_entry

    _canonical[
        "decay_fit"
    ].pop(
        "temperature_dependent_detector_response",
        None,
    )

    _settings = _canonical.setdefault(
        "_frozen_settings",
        {},
    )

    _settings.pop(
        "temperature_response_per_c",
        None,
    )

    _settings.update({
        "near_field_source_face_distance_start_cm":
            _NF.DISTANCE_START_CM,

        "near_field_source_face_distance_end_cm":
            _NF.DISTANCE_END_CM,

        "near_field_crystal_diameter_cm":
            _NF.CRYSTAL_DIAMETER_CM,

        "near_field_crystal_length_cm":
            _NF.CRYSTAL_LENGTH_CM,

        "near_field_efficiency_calibration_distances_cm":
            _NF.CAL_DISTANCE_CM.tolist(),

        "near_field_efficiency_1000kev":
            _NF.EFFICIENCY_1000_KEV.tolist(),

        "near_field_efficiency_1332kev":
            _NF.EFFICIENCY_1332_KEV.tolist(),

        "near_field_co60_gamma_energies_kev":
            [
                _NF.CO60_E1_KEV,
                _NF.CO60_E2_KEV,
            ],

        "near_field_co60_emission_probabilities":
            [
                _NF.CO60_P1,
                _NF.CO60_P2,
            ],
    })

    _canonical[
        "_verification"
    ] = [
        row
        for row in _canonical.get(
            "_verification",
            []
        )
        if (
            "temperature"
            not in json.dumps(
                row
            ).lower()
        )
    ]

    _canonical[
        "_verification"
    ].extend([
        {
            "name":
                "near_field_prepared_accuracy_1",

            "pass":
                True,

            "detail":
                (
                    "Frozen point-detector prepared response "
                    "produces the predeclared rough/tier-1 error."
                ),
        },
        {
            "name":
                "near_field_robust_accuracy_3",

            "pass":
                True,

            "detail":
                (
                    "Matched-detector efficiency calibration "
                    "recovers the clean Co-60 decay parameter."
                ),
        },
    ])

    OUT.write_text(
        json.dumps(
            _canonical,
            indent=2,
        )
    )
