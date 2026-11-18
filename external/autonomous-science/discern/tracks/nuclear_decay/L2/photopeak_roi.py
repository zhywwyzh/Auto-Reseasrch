"""
Canonical Nuclear Decay L2 mechanics for fixed_photopeak_roi_default.

This is a native tool-trap:
    - no counts are injected;
    - no spectra are shifted;
    - no detector calibration is altered.

The prepared baseline reduces the real Co-60 NaI spectra using fixed
channel-space photopeak regions established from the beginning of the
campaign.

Robust recovery reconstructs the full daily spectral integral from the
supplied spectra and measured live time.
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

from scipy.optimize import least_squares


HERE = Path(__file__).resolve().parent

sys.path.insert(
    0,
    str(HERE),
)

import l2_common as C


ASSETS = (
    HERE
    / "assets"
    / "multisource"
)

CO60_GAMMA_KEV = (
    1173.228,
    1332.492,
)

# Central rule selected before any named-model evaluation of this candidate.
BASELINE_DAYS = 14
FWHM_MULTIPLIER = 1.0

# Predeclared neighboring sensitivity checks.
SENSITIVITY_BASELINE_DAYS = (
    7,
    14,
    30,
)

SENSITIVITY_FWHM_MULTIPLIERS = (
    0.75,
    1.0,
    1.25,
)


def load_active():
    meta = pd.read_csv(
        ASSETS
        / "co60_daily_meta.csv.gz"
    ).copy()

    z = np.load(
        ASSETS
        / "co60_daily_spectra.npz",
        allow_pickle=False,
    )

    spectra_all = np.asarray(
        z["spectra"],
        dtype=float,
    )

    channels = np.asarray(
        z["channel_index"],
        dtype=float,
    )

    if (
        spectra_all.ndim != 2
        or spectra_all.shape[0] != len(meta)
        or spectra_all.shape[1] != len(channels)
    ):
        raise ValueError(
            "Co-60 spectrum dimensions do not match metadata"
        )

    clean = C.load_clean()

    row_for_date = {
        str(d): i
        for i, d in enumerate(
            meta["date"].astype(str)
        )
    }

    try:
        idx = np.asarray(
            [
                row_for_date[str(d)]
                for d in clean["date"].astype(str)
            ],
            dtype=int,
        )

    except KeyError as e:
        raise ValueError(
            f"clean-panel date missing from spectral asset: {e}"
        ) from e

    spectra = spectra_all[
        idx
    ]

    m = (
        meta.iloc[
            idx
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    spectral_meta = pd.DataFrame(
        {
            "date":
                clean["date"].astype(str),

            "elapsed_days":
                clean["elapsed_days"].astype(float),

            "total_live_time_s":
                m["total_live_time_s"].astype(float),

            "total_real_time_s":
                m["total_real_time_s"].astype(float),

            "n_acquisitions":
                m["n_acquisitions"].astype(int),

            "calibration_slope":
                m["mean_calibration_slope"].astype(float),

            "calibration_offset":
                m["mean_calibration_offset"].astype(float),
        }
    )

    if len(
        spectral_meta
    ) != 274:
        raise ValueError(
            f"expected 274 active spectral days, got {len(spectral_meta)}"
        )

    if (
        not np.all(
            np.isfinite(
                spectra
            )
        )
        or not np.all(
            spectra >= 0
        )
    ):
        raise ValueError(
            "invalid Co-60 spectrum counts"
        )

    return (
        spectra,
        spectral_meta,
        channels,
    )


def full_spectrum_series():
    spectra, meta, _ = (
        load_active()
    )

    counts = spectra.sum(
        axis=1
    )

    live = (
        meta[
            "total_live_time_s"
        ]
        .to_numpy(float)
    )

    return pd.DataFrame(
        {
            "date":
                meta["date"].astype(str),

            "elapsed_days":
                meta["elapsed_days"].astype(float),

            "total_counts":
                counts,

            "total_live_time_s":
                live,

            "total_real_time_s":
                meta["total_real_time_s"].astype(float),

            "rate_cps":
                counts
                / live,

            "sigma_rate_cps":
                np.sqrt(
                    counts
                )
                / live,

            "n_acquisitions":
                meta["n_acquisitions"].astype(int),
        }
    )


def _fit_peak(
    spectrum,
    expected_channel,
):
    c0 = float(
        expected_channel
    )

    lo = max(
        0,
        int(
            np.floor(
                c0
                - 70
            )
        ),
    )

    hi = min(
        len(spectrum),
        int(
            np.ceil(
                c0
                + 70
            )
        )
        + 1,
    )

    x = np.arange(
        lo,
        hi,
        dtype=float,
    )

    y = np.asarray(
        spectrum[
            lo:hi
        ],
        dtype=float,
    )

    mask = (
        (x >= c0 - 25)
        & (x <= c0 + 25)
    )

    xp = x[
        mask
    ]

    yp = y[
        mask
    ]

    j = int(
        np.argmax(
            yp
        )
    )

    mu0 = float(
        xp[j]
    )

    edge = np.r_[
        y[:20],
        y[-20:],
    ]

    b00 = float(
        np.median(
            edge
        )
    )

    amp0 = max(
        1.0,
        float(
            yp[j]
            - b00
        ),
    )

    def residual(
        p,
    ):
        amp, mu, sigma, b0, b1 = p

        pred = (
            amp
            * np.exp(
                -0.5
                * (
                    (
                        x
                        - mu
                    )
                    / sigma
                ) ** 2
            )
            + b0
            + b1
            * (
                x
                - c0
            )
        )

        return (
            pred
            - y
        ) / np.sqrt(
            np.maximum(
                y,
                1.0,
            )
        )

    fit = least_squares(
        residual,
        [
            amp0,
            mu0,
            18.0,
            b00,
            0.0,
        ],
        bounds=(
            [
                0.0,
                c0 - 30,
                2.0,
                0.0,
                -np.inf,
            ],
            [
                np.inf,
                c0 + 30,
                80.0,
                np.inf,
                np.inf,
            ],
        ),
        max_nfev=100000,
    )

    _, mu, sigma, _, _ = (
        fit.x
    )

    return {
        "success":
            bool(
                fit.success
            ),

        "mu_channel":
            float(
                mu
            ),

        "sigma_channels":
            float(
                abs(
                    sigma
                )
            ),

        "fwhm_channels":
            float(
                2.354820045
                * abs(
                    sigma
                )
            ),
    }


def fixed_roi_series(
    baseline_days=
        BASELINE_DAYS,
    fwhm_multiplier=
        FWHM_MULTIPLIER,
):
    spectra, meta, _ = (
        load_active()
    )

    baseline_days = int(
        baseline_days
    )

    fwhm_multiplier = float(
        fwhm_multiplier
    )

    if (
        baseline_days < 1
        or baseline_days
        > len(meta)
        or not np.isfinite(
            fwhm_multiplier
        )
        or fwhm_multiplier
        <= 0
    ):
        raise ValueError(
            "invalid fixed photopeak ROI setting"
        )

    slope = float(
        np.median(
            meta[
                "calibration_slope"
            ]
        )
    )

    offset = float(
        np.median(
            meta[
                "calibration_offset"
            ]
        )
    )

    expected_channels = [
        (
            energy
            - offset
        )
        / slope
        for energy
        in CO60_GAMMA_KEV
    ]

    baseline = spectra[
        :baseline_days
    ].sum(
        axis=0
    )

    peak_fits = [
        _fit_peak(
            baseline,
            expected,
        )
        for expected
        in expected_channels
    ]

    if not all(
        p["success"]
        for p in peak_fits
    ):
        raise RuntimeError(
            "baseline photopeak fit failed"
        )

    counts = np.zeros(
        len(meta),
        dtype=float,
    )

    roi_bounds = []

    for peak in peak_fits:
        center = int(
            round(
                peak[
                    "mu_channel"
                ]
            )
        )

        halfwidth = max(
            2,
            int(
                round(
                    fwhm_multiplier
                    * peak[
                        "fwhm_channels"
                    ]
                )
            ),
        )

        lo = max(
            0,
            center
            - halfwidth,
        )

        hi = min(
            spectra.shape[1],
            center
            + halfwidth
            + 1,
        )

        counts += spectra[
            :,
            lo:hi
        ].sum(
            axis=1
        )

        roi_bounds.append(
            {
                "center_channel":
                    center,

                "halfwidth_channels":
                    halfwidth,

                "lo":
                    lo,

                "hi_exclusive":
                    hi,
            }
        )

    live = (
        meta[
            "total_live_time_s"
        ]
        .to_numpy(float)
    )

    series = pd.DataFrame(
        {
            "date":
                meta["date"].astype(str),

            "elapsed_days":
                meta["elapsed_days"].astype(float),

            "total_counts":
                counts,

            "total_live_time_s":
                live,

            "total_real_time_s":
                meta["total_real_time_s"].astype(float),

            "rate_cps":
                counts
                / live,

            "sigma_rate_cps":
                np.sqrt(
                    counts
                )
                / live,

            "n_acquisitions":
                meta["n_acquisitions"].astype(int),
        }
    )

    full_counts = spectra.sum(
        axis=1
    )

    fraction = (
        counts
        / full_counts
    )

    t = (
        meta[
            "elapsed_days"
        ]
        .to_numpy(float)
    )

    info = {
        "native_no_injection":
            True,

        "baseline_days":
            baseline_days,

        "fwhm_multiplier":
            fwhm_multiplier,

        "co60_gamma_energies_keV":
            [
                float(x)
                for x
                in CO60_GAMMA_KEV
            ],

        "expected_channels":
            [
                float(x)
                for x
                in expected_channels
            ],

        "peak_fits":
            peak_fits,

        "roi_bounds":
            roi_bounds,

        "roi_fraction_relative_sd":
            float(
                np.std(
                    fraction,
                    ddof=1,
                )
                / np.mean(
                    fraction
                )
            ),

        "roi_fraction_time_correlation":
            float(
                np.corrcoef(
                    t,
                    fraction,
                )[0, 1]
            ),
    }

    return (
        series,
        info,
    )
