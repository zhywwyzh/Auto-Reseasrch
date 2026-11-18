from pathlib import Path
import hashlib
import sys


ROOT = Path(
    sys.argv[1]
)


def sha(p):
    return hashlib.sha256(
        p.read_bytes()
    ).hexdigest()


def must_replace(
    text,
    old,
    new,
    label,
):
    n = text.count(
        old
    )

    if n != 1:
        raise RuntimeError(
            f"{label}: expected exactly one match, found {n}"
        )

    return text.replace(
        old,
        new,
        1,
    )


def splice(
    text,
    start_marker,
    end_marker,
    replacement,
    label,
):
    a = text.find(
        start_marker
    )

    if a < 0:
        raise RuntimeError(
            f"{label}: start marker missing"
        )

    b = text.find(
        end_marker,
        a,
    )

    if b < 0:
        raise RuntimeError(
            f"{label}: end marker missing"
        )

    return (
        text[:a]
        + replacement
        + text[b:]
    )


def write(
    rel,
    text,
):
    p = ROOT / rel

    compile(
        text,
        str(p),
        "exec",
    )

    tmp = p.with_suffix(
        p.suffix
        + ".tmp_photopeak"
    )

    tmp.write_text(
        text
    )

    tmp.replace(
        p
    )

    print(
        "[PATCH]",
        rel,
        sha(p),
    )


###############################################################################
# l2_common.py
###############################################################################

p = ROOT / "l2_common.py"
s = p.read_text()

s = must_replace(
    s,
    "dead_time_correction_default              tool-trap",
    "fixed_photopeak_roi_default              tool-trap",
    "l2_common world list",
)

s = must_replace(
    s,
    "Frozen before named-model evaluation.",
    (
        "Temperature-response and Mn-54 settings were frozen before named-model\n"
        "evaluation. The fixed-photopeak-ROI replacement was selected and\n"
        "sensitivity-frozen without consulting model output on that candidate."
    ),
    "l2_common provenance note",
)

s = must_replace(
    s,
    "\nPREPARED_DEAD_TIME_US = 20.0\n",
    "\n",
    "remove deadtime setting",
)

start = (
    "# =====================================================================\n"
    "# TOOL TRAP — BAD PREPARED DEAD-TIME CORRECTION\n"
    "# ====================================================================="
)

a = s.find(
    start
)

if a < 0:
    raise RuntimeError(
        "l2_common deadtime section missing"
    )

s = (
    s[:a]
    + '''# =====================================================================
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
'''
)

write(
    "l2_common.py",
    s,
)


###############################################################################
# reference_solver.py
###############################################################################

p = ROOT / "reference_solver.py"
s = p.read_text()

s = must_replace(
    s,
    "from pathlib import Path\n\n\nHERE",
    "from pathlib import Path\n\nimport numpy as np\n\n\nHERE",
    "solver numpy import",
)

s = must_replace(
    s,
    "import l2_common as C\n",
    "import l2_common as C\nimport photopeak_roi as P\n",
    "solver photopeak import",
)

computation = '''photopeak_prepared, photopeak_meta = (
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
'''

s = splice(
    s,
    "deadtime_prepared = (",
    "checks = []\n",
    computation,
    "solver computation block",
)

check_block = '''checks.append(
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


'''

s = splice(
    s,
    '''checks.append(
    check(
        "empirical_dead_time_sane"''',
    "\n\nworlds = {",
    check_block,
    "solver old deadtime checks",
)

a = s.find(
    '    "dead_time_correction_default": {'
)

if a < 0:
    raise RuntimeError(
        "solver old deadtime world missing"
    )

end_marker = (
    "\n    },\n}\n\n\npayload = {"
)

b = s.find(
    end_marker,
    a,
)

if b < 0:
    raise RuntimeError(
        "solver world end missing"
    )

b += len(
    "\n    },"
)

new_world = '''    "fixed_photopeak_roi_default": {
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
    },'''

s = (
    s[:a]
    + new_world
    + s[b:]
)

s = must_replace(
    s,
    '''        "prepared_dead_time_us":
            C.PREPARED_DEAD_TIME_US,

''',
    '''        "photopeak_roi_baseline_days":
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

''',
    "solver frozen settings",
)

s = must_replace(
    s,
    '"dead_time_correction_default",',
    '"fixed_photopeak_roi_default",',
    "solver fire matrix",
)

write(
    "reference_solver.py",
    s,
)


###############################################################################
# world_builder.py
###############################################################################

p = ROOT / "world_builder.py"
s = p.read_text()

s = must_replace(
    s,
    "from pathlib import Path\n\n\nHERE",
    "from pathlib import Path\n\nimport numpy as np\n\n\nHERE",
    "builder numpy import",
)

s = must_replace(
    s,
    "import l2_common as C\n",
    "import l2_common as C\nimport photopeak_roi as P\n",
    "builder photopeak import",
)

new_writer = '''def _write_world(
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
'''

s = splice(
    s,
    "def _write_world(",
    "\ndef main():",
    new_writer,
    "builder writer",
)

insert_marker = '''    g = GOLD[
        "decay_fit"
    ]
'''

insert_text = '''    photopeak, photopeak_meta = (
        P.fixed_roi_series()
    )

'''

if insert_marker not in s:
    raise RuntimeError(
        "builder GOLD marker missing"
    )

s = s.replace(
    insert_marker,
    insert_text
    + insert_marker,
    1,
)

world_marker = "    worlds = ["

idx = s.find(
    world_marker
)

if idx < 0:
    raise RuntimeError(
        "builder worlds marker missing"
    )

assertion = '''    assert (
        photopeak_meta
        == g[
            "fixed_photopeak_roi_default"
        ][
            "prepared_rule"
        ]
    )

'''

s = (
    s[:idx]
    + assertion
    + s[idx:]
)

a = s.find(
    '''        {
            "label":
                "dead_time_correction_default"'''
)

if a < 0:
    raise RuntimeError(
        "builder old deadtime world missing"
    )

b = s.find(
    "        },\n    ]",
    a,
)

if b < 0:
    raise RuntimeError(
        "builder world-list end missing"
    )

b += len(
    "        },"
)

new_world = '''        {
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
        },'''

s = (
    s[:a]
    + new_world
    + s[b:]
)

s = must_replace(
    s,
    '''            environment,
            mn54_reference,
        )''',
    '''            environment,
            mn54_reference,
            world[
                "label"
            ],
        )''',
    "builder writer invocation",
)

write(
    "world_builder.py",
    s,
)


###############################################################################
# grader recognition
###############################################################################

p = ROOT / "grade_nuclear_decay_l2.py"
s = p.read_text()

a = s.find(
    '''    elif (
        world
        == "dead_time_correction_default"
    ):'''
)

if a < 0:
    raise RuntimeError(
        "grader deadtime recognition branch missing"
    )

b = s.find(
    "\n    else:\n        return (",
    a,
)

if b < 0:
    raise RuntimeError(
        "grader branch end missing"
    )

new_branch = '''    elif (
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
'''

s = (
    s[:a]
    + new_branch
    + s[b:]
)

write(
    "grade_nuclear_decay_l2.py",
    s,
)


###############################################################################
# validator fixtures
###############################################################################

p = ROOT / "validate_grader.py"
s = p.read_text()

s = must_replace(
    s,
    '''                issue = [
                    (
                        "The prepared normalization uses an unsupported "
                        "dead-time correction inconsistent with measured "
                        "live time and real time."
                    )
                ]

                method = {
                    "model": (
                        "exponential decay from raw counts normalized "
                        "by measured live time"
                    ),

                    "weighting":
                        "uncertainty",

                    "timescale":
                        "half-life",
                }
''',
    '''                issue = [
                    (
                        "The prepared fixed photopeak ROI reduction loses "
                        "a time-dependent fraction of the Co-60 spectrum "
                        "as the peaks drift through channel space."
                    )
                ]

                method = {
                    "model": (
                        "exponential decay from the full-spectrum "
                        "integrated counts reconstructed from raw spectra"
                    ),

                    "weighting":
                        "uncertainty",

                    "timescale":
                        "half-life",
                }
''',
    "validator perfect fixture",
)

s = must_replace(
    s,
    '''                issue = [
                    (
                        "prepared dead-time correction conflicts with "
                        "live time and real time"
                    )
                ]

                method = {
                    "model":
                        "live-time raw count exponential decay"
                }
''',
    '''                issue = [
                    (
                        "fixed photopeak ROI spectral drift issue"
                    )
                ]

                method = {
                    "model":
                        "full-spectrum integrated counts exponential decay"
                }
''',
    "validator fabricated fixture",
)

write(
    "validate_grader.py",
    s,
)


###############################################################################
# Canonical stale-label guard
###############################################################################

for rel in (
    "l2_common.py",
    "photopeak_roi.py",
    "reference_solver.py",
    "world_builder.py",
    "grade_nuclear_decay_l2.py",
    "validate_grader.py",
):
    p = ROOT / rel

    if (
        "dead_time_correction_default"
        in p.read_text()
    ):
        raise RuntimeError(
            f"stale retired world label remains in {rel}"
        )


print()
print("SOURCE PATCH: PASS")
