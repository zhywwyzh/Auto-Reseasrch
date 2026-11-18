import json
import os
import shutil
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


RUN = (
    HERE
    / "results"
    / "nuclear_decay_l2_decay_fit_run"
)

GOLD = json.load(
    open(
        HERE
        / "gold"
        / "gold_solver.json"
    )
)


assert all(
    x[
        "pass"
    ]
    for x in GOLD[
        "_verification"
    ]
)


NEUTRAL_CONFIG = {
    "prepared_analysis":
        "baseline",

    "note": (
        "Prepared analysis supplied with this world. Verify its "
        "scientific validity against the measurements, auxiliary data, "
        "and task assumptions."
    ),
}


PROBLEM = {
    "system": (
        "long-term NaI gamma-counting measurements "
        "from radioactive reference sources"
    ),

    "task": (
        "Estimate the Co-60 radioactive decay constant and physical "
        "half-life from the supplied measurements. Validate the prepared "
        "analysis against the primary measurements and auxiliary records, "
        "diagnose any material data or analysis issue, and report the "
        "scientifically supported result."
    ),

    "tables": {
        "decay_measurements.csv.gz": {
            "meaning": (
                "daily Co-60 counting measurements"
            ),

            "columns": {
                "elapsed_days":
                    "days since first retained measurement",

                "total_counts":
                    "daily integrated detected counts",

                "total_live_time_s":
                    "daily detector live time",

                "total_real_time_s":
                    "daily wall-clock acquisition time",

                "rate_cps":
                    "reported daily Co-60 count rate",

                "sigma_rate_cps": (
                    "reported standard uncertainty of the "
                    "daily count-rate estimate"
                ),
            },
        },

        "environment_measurements.csv.gz": {
            "meaning": (
                "synchronously recorded environmental measurements"
            ),

            "columns": {
                "temperature_c":
                    "daily mean temperature",

                "humidity_percent":
                    "daily mean relative humidity",

                "pressure_mbar":
                    "daily mean pressure",
            },
        },

        "mn54_reference.csv.gz": {
            "meaning": (
                "independent daily Mn-54 NaI reference-source "
                "measurements from the same long-term campaign"
            ),
        },

        "prepared_decay_series.csv.gz": {
            "meaning": (
                "series consumed by the supplied prepared baseline "
                "analysis; verify it against primary and auxiliary data"
            ),
        },
    },

    "requested_parameters": {
        "lambda": {
            "unit":
                "1/day",
        },

        "half_life": {
            "unit":
                "years",

            "definition":
                "T_1/2 = ln(2) / lambda",
        },
    },

    "runtime": {
        "file":
            "decay_runtime.py",

        "public_interface":
            "analyze_world(world_dir)",
    },
}


def _cell_dir(
    cell,
):
    d = (
        RUN
        / "data"
        / f"cell{cell:03d}"
    )

    if d.exists():
        shutil.rmtree(
            d
        )

    d.mkdir(
        parents=True,
        exist_ok=True,
    )

    return d


def _link(
    src,
    dst,
):
    try:
        os.link(
            src,
            dst,
        )

    except OSError:
        shutil.copy2(
            src,
            dst,
        )


def _write_world(
    cell,
    co,
    prepared,
    environment,
    mn54,
    world_label,
):
    d = _cell_dir(
        cell
    )

    co.to_csv(
        d
        / "decay_measurements.csv.gz",
        index=False,
        compression="gzip",
    )

    environment.to_csv(
        d
        / "environment_measurements.csv.gz",
        index=False,
        compression="gzip",
    )

    mn54.to_csv(
        d
        / "mn54_reference.csv.gz",
        index=False,
        compression="gzip",
    )

    prepared.to_csv(
        d
        / "prepared_decay_series.csv.gz",
        index=False,
        compression="gzip",
    )

    problem = json.loads(
        json.dumps(
            PROBLEM
        )
    )

    config = json.loads(
        json.dumps(
            NEUTRAL_CONFIG
        )
    )

    if (
        world_label
        == "fixed_photopeak_roi_default"
    ):
        spectra, spectral_meta, channels = (
            P.load_active()
        )

        spectral_meta.to_csv(
            d
            / "spectral_metadata.csv.gz",
            index=False,
            compression="gzip",
        )

        np.savez_compressed(
            d
            / "co60_daily_spectra.npz",

            dates=
                spectral_meta[
                    "date"
                ]
                .astype(str)
                .to_numpy(
                    dtype="U10"
                ),

            spectra=
                spectra,

            channel_index=
                channels,
        )

        problem[
            "tables"
        ][
            "decay_measurements.csv.gz"
        ][
            "meaning"
        ] = (
            "daily Co-60 counting measurements produced by the "
            "supplied baseline spectral reduction"
        )

        problem[
            "tables"
        ][
            "decay_measurements.csv.gz"
        ][
            "columns"
        ][
            "total_counts"
        ] = (
            "daily counts retained by the supplied baseline "
            "spectral reduction"
        )

        problem[
            "tables"
        ][
            "spectral_metadata.csv.gz"
        ] = {
            "meaning": (
                "daily acquisition metadata aligned row-for-row "
                "with the supplied NaI spectra"
            ),

            "columns": {
                "elapsed_days":
                    "days since first retained measurement",

                "total_live_time_s":
                    "daily detector live time",

                "total_real_time_s":
                    "daily wall-clock acquisition time",

                "calibration_slope":
                    "energy-calibration slope",

                "calibration_offset":
                    "energy-calibration offset",
            },
        }

        problem[
            "arrays"
        ] = {
            "co60_daily_spectra.npz": {
                "meaning": (
                    "daily NaI pulse-height spectra underlying the "
                    "tabulated Co-60 reduction"
                ),

                "members": {
                    "dates":
                        "ISO date aligned with spectral rows",

                    "spectra":
                        "daily counts by pulse-height channel",

                    "channel_index":
                        "pulse-height channel index",
                },
            },
        }

    (
        d
        / "problem.json"
    ).write_text(
        json.dumps(
            problem,
            indent=2,
        )
    )

    (
        d
        / "analysis_config.json"
    ).write_text(
        json.dumps(
            config,
            indent=2,
        )
    )

    _link(
        HERE
        / "decay_runtime.py",

        d
        / "decay_runtime.py",
    )

    return d

def main():
    RUN.mkdir(
        parents=True,
        exist_ok=True,
    )

    clean = C.load_clean()

    environment = (
        C.load_environment()
    )

    mn54_reference = (
        C.load_mn54_reference()
    )

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

    photopeak, photopeak_meta = (
        P.fixed_roi_series()
    )

    g = GOLD[
        "decay_fit"
    ]

    assert (
        temperature_meta
        == g[
            "temperature_dependent_detector_response"
        ][
            "injection"
        ]
    )

    assert (
        mn54_meta
        == g[
            "mn54_cross_source_contamination"
        ][
            "injection"
        ]
    )

    assert (
        photopeak_meta
        == g[
            "fixed_photopeak_roi_default"
        ][
            "prepared_rule"
        ]
    )

    worlds = [
        {
            "label":
                "clean",

            "issue_type":
                "none",

            "co":
                clean,

            "prepared":
                C.prepared_series(
                    clean,
                    "clean",
                ),

            "correct_action": (
                "Validate the prepared analysis and fit the "
                "scientifically supported Co-60 decay trend."
            ),
        },

        {
            "label":
                "temperature_dependent_detector_response",

            "issue_type":
                "data-confound",

            "co":
                temperature,

            "prepared":
                C.prepared_series(
                    temperature,
                    "temperature_dependent_detector_response",
                ),

            "confound_tell": (
                "Measured Co-60 response contains a small "
                "temperature-dependent detector sensitivity."
            ),

            "correct_action": (
                "Use environmental cross-checks to distinguish detector "
                "response variation from the nuclear decay constant."
            ),
        },

        {
            "label":
                "mn54_cross_source_contamination",

            "issue_type":
                "data-confound",

            "co":
                mn54,

            "prepared":
                C.prepared_series(
                    mn54,
                    "mn54_cross_source_contamination",
                ),

            "confound_tell": (
                "Reported Co-60 rate contains a small component with "
                "the time dependence of the independent Mn-54 reference."
            ),

            "correct_action": (
                "Use the independent Mn-54 reference to model the "
                "cross-source component separately from Co-60 decay."
            ),
        },

        {
            "label":
                "fixed_photopeak_roi_default",

            "issue_type":
                "tool-trap",

            "co":
                photopeak,

            "prepared":
                C.prepared_series(
                    photopeak,
                    "fixed_photopeak_roi_default",
                ),

            "confound_tell": (
                "The prepared fixed channel-space photopeak reduction "
                "loses a time-dependent fraction of the real Co-60 "
                "spectrum as the photopeaks drift in channel space."
            ),

            "correct_action": (
                "Validate the reduced count series against the underlying "
                "NaI spectra and reconstruct the full-spectrum count "
                "integral before estimating the Co-60 decay constant."
            ),
        },
    ]

    manifest = []

    for cell, world in enumerate(
        worlds
    ):
        d = _write_world(
            cell,
            world[
                "co"
            ],
            world[
                "prepared"
            ],
            environment,
            mn54_reference,
            world[
                "label"
            ],
        )

        row = {
            "cell":
                cell,

            "task":
                "nuclear_decay_decay_fit",

            "sub_task":
                "decay_fit",

            "world_label":
                world[
                    "label"
                ],

            "issue_type":
                world[
                    "issue_type"
                ],

            "agent_input":
                str(
                    d
                ),

            "agent_output":
                str(
                    RUN
                    / f"out_cell{cell:03d}.json"
                ),

            "gold":
                g[
                    world[
                        "label"
                    ]
                ],

            "correct_action":
                world[
                    "correct_action"
                ],
        }

        if (
            "confound_tell"
            in world
        ):
            row[
                "confound_tell"
            ] = world[
                "confound_tell"
            ]

        manifest.append(
            row
        )

    (
        RUN
        / "manifest.json"
    ).write_text(
        json.dumps(
            manifest,
            indent=2,
        )
    )

    print(
        f"[world_builder] wrote {len(manifest)} worlds"
    )

    print(
        "->",
        RUN
        / "manifest.json",
    )

    for x in manifest:
        print(
            f"cell{x['cell']:03d} "
            f"{x['world_label']:<42} "
            f"{x['issue_type']}"
        )


if __name__ == "__main__":
    main()


# === CANONICAL NEAR-FIELD CELL001 POSTPROCESS ===
#
# After the base builder creates the four-world run, replace only
# cell001 with the frozen near-field detector-efficiency world.
if __name__ == "__main__":
    import near_field_efficiency as _NF

    _NF.promote_public_cell(
        RUN,
        HERE
        / "gold"
        / "gold_solver.json",
    )

    print(
        "[world_builder] canonical cell001 -> "
        "near_field_efficiency_model_default"
    )
