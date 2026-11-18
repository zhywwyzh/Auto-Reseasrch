#!/usr/bin/env python3
"""
Nuclear-decay L1 world builder.

Real clean substrate:
    Multi-year NaI(Tl) Co-60 radiation measurements.

The raw source contains:
    - acquisition date/time
    - live/real time and dead time
    - per-acquisition spectral calibration
    - reported integral counts
    - 2048-channel gamma spectrum

For L1 we canonicalize one long, naturally gap-free, single-calibration
Co-60 regime into an analysis-friendly measurement table.

L1 asks whether the radiation measurement table is internally valid BEFORE
decay-constant / half-life estimation.

Each challenge world is ONE controlled delta on the clean real substrate.

Agent-visible world directory:
    radiation.csv.gz
    measurement_meta.json

The abstention world is a REAL untouched Co-60 slice spanning the source's
natural calibration change. It is not an injected corruption.
"""

from __future__ import annotations

from pathlib import Path
import json
import shutil

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
TRACK = HERE.parent

RAW = (
    TRACK
    / "raw"
    / "Multi year radiation measurement data"
    / "NaI_Co-60_1Dec2014to1June2016.csv"
)

RUN = (
    HERE
    / "results"
    / "nuclear_decay_l1_run"
)

DATA_OUT = RUN / "data"

RNG_SEED = 20260827

# -------------------------------------------------------------------------
# Canonical real-data windows.
#
# Clean:
#   Raw row 7192 begins the longest uninterrupted calibration-stable block:
#   2015-05-03 13:38:55 onward, slope=1.583155, offset=-42.78.
#
#   We take 2048 consecutive acquisitions (~43.5 days), enough for robust
#   spectral/integrity QC while keeping each sandbox world manageable.
#
# Abstention:
#   Raw row 3340 is the real Feb-10-2015 calibration transition.
#   Use 256 acquisitions before and after it, untouched except for
#   representational canonicalization.
# -------------------------------------------------------------------------

CLEAN_START = 7192
CLEAN_N = 2048

CAL_TRANSITION = 3340
ABSTAIN_HALF = 256

N_CHANNELS = 2048


CLEAN_META = {
    "dataset": "Multi year radiation measurement data",
    "source_series": "NaI Co-60",
    "experiment": (
        "Long-term repeated NaI(Tl) gamma-spectrum measurements of a Co-60 "
        "source. This benchmark world is a real subset of the source series."
    ),
    "table": "radiation.csv.gz",
    "measurement_unit_notes": {
        "timestamp": "combined source acquisition date and acquisition time",
        "live_time_s": "detector live acquisition time in seconds",
        "real_time_s": "wall-clock acquisition time in seconds",
        "dead_time_fraction": (
            "detector dead-time fraction, canonicalized so 0.019 means 1.9%"
        ),
        "calibration_slope": (
            "source-provided per-acquisition linear spectral calibration slope"
        ),
        "calibration_offset": (
            "source-provided per-acquisition linear spectral calibration offset"
        ),
        "integral_counts": (
            "source-reported total spectrum counts. The source export stores "
            "this with finite precision, so small differences from the exact "
            "sum of channel counts are expected; large discrepancies are not."
        ),
        "n_channels": "number of spectral channels; expected 2048",
        "channel_0000...channel_2047": (
            "integer counts in the 2048-channel NaI spectrum"
        ),
    },
    "spectral_calibration_note": (
        "Calibration slope and offset are recorded per acquisition and must be "
        "respected when comparing spectral features across time. A change in "
        "recorded calibration coefficients is not by itself proof that the "
        "underlying radiation measurement is corrupt."
    ),
    "downstream_use": (
        "measurement validation before decay-rate, decay-constant, half-life, "
        "or long-term spectral-stability inference"
    ),
}


# =============================================================================
# Ground truth = grading contract
# =============================================================================

GT = {
    "clean": dict(
        present=False,
        canonical_checks=[
            "duplicat|\\.duplicated",
            "timestamp|time|chronolog|monotonic|diff\\(",
            "live.?time|real.?time|dead.?time",
            "integral|sum.*channel|channel.*sum",
            "2048|n_channels|channel",
            "slope|offset|calibrat|spectrum|peak",
        ],
        diagnose_keywords=[],
        action_keywords=[],
        correct_action=(
            "No injected integrity defect. Retain the Co-60 acquisitions and "
            "their row-specific calibration metadata and proceed to decay-law "
            "or long-term spectral analysis."
        ),
        affected=[],
    ),

    "duplicate_acquisitions": dict(
        present=True,
        canonical_checks=[
            "duplicat|\\.duplicated|drop_duplicates",
            "acquisition_id|timestamp",
            "channel|spectrum|integral",
        ],
        diagnose_keywords=[
            "duplicate acquisition",
            "duplicated acquisition",
            "duplicate row",
            "duplicated row",
            "exact duplicate",
            "duplicate timestamp",
            "repeated acquisition",
            "repeated spectrum",
        ],
        action_keywords=[
            "de-?duplicate",
            "dedup",
            "remove.*duplicate",
            "drop.*duplicate",
            "retain one",
            "keep one",
            "drop_duplicates",
        ],
        correct_action=(
            "Identify the exact repeated Co-60 acquisitions and remove the "
            "duplicate copies before estimating a decay trend, retaining one "
            "copy of each genuine acquisition."
        ),
        affected=[],
    ),

    "dropped_acquisitions": dict(
        present=True,
        canonical_checks=[
            "acquisition_id|timestamp",
            "diff\\(|gap|cadence|missing",
            "sort|chronolog",
        ],
        diagnose_keywords=[
            "dropped acquisition",
            "missing acquisition",
            "missing block",
            "sampling gap",
            "time gap",
            "acquisition gap",
            "missing measurements",
            "missing spectra",
        ],
        action_keywords=[
            "flag.*gap",
            "account.*gap",
            "handle.*missing",
            "exclude.*gap",
            "do not.*assume.*uniform",
            "model.*irregular",
            "preserve.*timestamp",
        ],
        correct_action=(
            "Detect the injected contiguous missing-acquisition block from the "
            "timestamp/acquisition-id gap and account for the irregular sampling "
            "rather than treating the surrounding rows as consecutive regular "
            "measurements."
        ),
        affected=[],
    ),

    "timestamp_order_corruption": dict(
        present=True,
        canonical_checks=[
            "timestamp|time",
            "monotonic|is_monotonic",
            "sort|order",
            "acquisition_id",
        ],
        diagnose_keywords=[
            "timestamp order",
            "time order",
            "out of order",
            "non-?monotonic",
            "chronological order",
            "misordered block",
            "swapped block",
            "row order",
        ],
        action_keywords=[
            "sort.*timestamp",
            "sort.*time",
            "restore.*order",
            "reorder",
            "chronological",
            "correct.*order",
        ],
        correct_action=(
            "Two complete acquisition blocks are stored in the wrong row order. "
            "Restore chronological ordering before treating file order as the "
            "measurement time series."
        ),
        affected=[],
    ),

    "livetime_unit_mismatch": dict(
        present=True,
        require_positive_flag_evidence=True,
        canonical_checks=[
            "live.?time|real.?time",
            "second|minute|unit",
            "30|1800",
            "dead.?time",
        ],
        diagnose_keywords=[
            "live.?time.*unit",
            "unit mismatch",
            "seconds.*minutes",
            "minutes.*seconds",
            "live.?time.*30",
            "live.?time.*1800",
            "factor.*60",
            "60.*factor",
            "wrong.*live.?time",
        ],
        action_keywords=[
            "convert.*minute.*second",
            "multiply.*60",
            "restore.*1800",
            "correct.*live.?time",
            "rescale.*live.?time",
            "fix.*unit",
        ],
        correct_action=(
            "A contiguous block has live time numerically expressed as 30 "
            "minutes while the field remains labeled seconds. Convert that "
            "block back to 1800 seconds before normalizing count rates."
        ),
        affected=[],
    ),

    "integral_spectrum_mismatch": dict(
        present=True,
        require_positive_flag_evidence=True,
        canonical_checks=[
            "integral|integral_counts",
            "sum.*channel|channel.*sum|spectrum.*sum",
            "relative|percent|ratio|difference",
        ],
        diagnose_keywords=[
            "integral.*mismatch",
            "spectrum.*mismatch",
            "channel.*sum",
            "sum.*channel",
            "reported integral",
            "count.*inconsisten",
            "integral.*inconsisten",
            "total counts.*mismatch",
        ],
        action_keywords=[
            "recompute.*integral",
            "sum.*channel",
            "use.*spectrum",
            "exclude.*mismatch",
            "correct.*integral",
            "flag.*integral",
            "verify.*integral",
        ],
        correct_action=(
            "A contiguous acquisition block has reported integral counts shifted "
            "far beyond the source's harmless rounding differences while the "
            "2048-channel spectra are unchanged. Recompute/verify totals from "
            "the spectrum or exclude/correct the inconsistent summary field "
            "before count-rate analysis."
        ),
        affected=[],
    ),

    "spectral_channel_shift": dict(
        present=True,
        require_positive_flag_evidence=True,
        canonical_checks=[
            "spectrum|channel",
            "peak|argmax|centroid",
            "slope|offset|calibrat",
            "shift|align|drift",
        ],
        diagnose_keywords=[
            "channel shift",
            "spectral shift",
            "spectrum.*shift",
            "peak.*shift",
            "peak.*channel",
            "spectral misalign",
            "channel misalign",
            "energy.*shift",
            "calibration.*inconsisten",
        ],
        action_keywords=[
            "re-?align",
            "correct.*shift",
            "restore.*channel",
            "recalibrat",
            "exclude.*shift",
            "flag.*shift",
            "align.*spectrum",
        ],
        correct_action=(
            "A contiguous block of spectra is displaced by 25 channels while "
            "its recorded calibration metadata is unchanged. Flag and correct "
            "or exclude the spectrally misaligned block before comparing "
            "spectral features or fitting long-term decay behavior."
        ),
        affected=[],
    ),

    "abstain_calibration_change": dict(
        present=False,
        requires_external_evidence=True,
        abstention_question=(
            "This world is an untouched REAL Co-60 sequence spanning a recorded "
            "change in the source-provided spectral calibration slope/offset. "
            "Grade the analyst as recognizing the abstention control ONLY if BOTH "
            "conditions hold: (1) they do NOT claim that the coefficient change "
            "alone proves corrupted radiation measurements, because row-specific "
            "calibration metadata can legitimately change and corruption would "
            "require independent spectral/calibration evidence; AND (2) they do "
            "not declare the otherwise internally coherent measurements unusable "
            "solely because of that calibration update. Respecting the "
            "per-acquisition calibration and recommending verification is allowed. "
            "Answer strictly YES or NO."
        ),
        canonical_checks=[
            "slope|offset|calibrat",
            "spectrum|peak|channel",
            "timestamp|time",
            "integral|counts",
        ],
        diagnose_keywords=[
            "calibration change",
            "calibration update",
            "slope.*offset",
            "cannot.*conclude",
            "not.*proof",
            "insufficient.*evidence",
            "requires.*verification",
            "row-specific calibration",
        ],
        action_keywords=[
            "respect.*calibrat",
            "use.*row.*calibrat",
            "verify.*calibrat",
            "retain.*measurement",
            "proceed.*calibrat",
            "do not.*discard",
        ],
        correct_action=(
            "Do not infer corrupted Co-60 measurements solely from the real "
            "recorded calibration-coefficient transition. Preserve and apply "
            "the per-acquisition calibration; require independent evidence "
            "before declaring the radiation measurements invalid."
        ),
        affected=[],
    ),
}


# =============================================================================
# Raw loading / canonicalization
# =============================================================================

def _canonical_dead_time(series):
    s = series.astype(str)
    has_pct = s.str.contains("%", regex=False)

    x = pd.to_numeric(
        s.str.replace("%", "", regex=False),
        errors="coerce",
    )

    out = np.where(
        has_pct,
        x / 100.0,
        x,
    )

    return np.asarray(out, dtype=float)


def _canonicalize(raw):
    if raw.shape[1] != 9 + N_CHANNELS:
        raise RuntimeError(
            f"Expected 9 metadata + {N_CHANNELS} spectral columns; "
            f"found {raw.shape[1]} columns."
        )

    timestamp = pd.to_datetime(
        raw["Acq Date"].astype(str)
        + " "
        + raw["Acq Time"].astype(str),
        errors="raise",
    )

    out = pd.DataFrame({
        "acquisition_id": np.arange(len(raw), dtype=int),
        "timestamp": timestamp.dt.strftime("%Y-%m-%d %H:%M:%S"),
        "live_time_s": pd.to_numeric(
            raw["LiveTime"], errors="raise"
        ).to_numpy(float),
        "real_time_s": pd.to_numeric(
            raw["RealTime"], errors="raise"
        ).to_numpy(float),
        "dead_time_fraction": _canonical_dead_time(
            raw["DeadTime"]
        ),
        "calibration_slope": pd.to_numeric(
            raw["Slope"], errors="raise"
        ).to_numpy(float),
        "calibration_offset": pd.to_numeric(
            raw["Offset"], errors="raise"
        ).to_numpy(float),
        "integral_counts": pd.to_numeric(
            raw["Integral"], errors="raise"
        ).to_numpy(float),
        "n_channels": pd.to_numeric(
            raw["NoOfChannels"], errors="raise"
        ).to_numpy(int),
    })

    spec = raw.iloc[:, 9:].apply(
        pd.to_numeric,
        errors="raise",
    )

    spec.columns = [
        f"channel_{i:04d}"
        for i in range(N_CHANNELS)
    ]

    spec = spec.reset_index(drop=True)

    return pd.concat(
        [out.reset_index(drop=True), spec],
        axis=1,
    )


def _load_raw():
    if not RAW.exists():
        raise SystemExit(
            f"[world_builder] missing Co-60 CSV: {RAW}"
        )

    return pd.read_csv(
        RAW,
        low_memory=False,
    )


def load_clean():
    raw = _load_raw()

    sub = raw.iloc[
        CLEAN_START:CLEAN_START + CLEAN_N
    ].copy()

    return _canonicalize(sub)


def load_abstention_real():
    raw = _load_raw()

    lo = CAL_TRANSITION - ABSTAIN_HALF
    hi = CAL_TRANSITION + ABSTAIN_HALF

    sub = raw.iloc[lo:hi].copy()

    return _canonicalize(sub)


# =============================================================================
# Clean invariants
# =============================================================================

def channel_columns(df):
    return [
        c for c in df.columns
        if c.startswith("channel_")
    ]


def spectrum_sum(df):
    return (
        df[channel_columns(df)]
        .to_numpy(dtype=np.float64)
        .sum(axis=1)
    )


def timestamps(df):
    return pd.to_datetime(
        df["timestamp"],
        errors="raise",
    )


def verify_clean(df):
    print(
        "[clean]",
        f"rows={len(df)}",
        f"channels={len(channel_columns(df))}",
    )

    if len(df) != CLEAN_N:
        raise RuntimeError(
            f"Clean window length {len(df)} != {CLEAN_N}"
        )

    if len(channel_columns(df)) != N_CHANNELS:
        raise RuntimeError(
            "Clean spectrum does not contain 2048 channels."
        )

    if df.duplicated().any():
        raise RuntimeError(
            "Clean substrate unexpectedly contains exact duplicate rows."
        )

    ts = timestamps(df)
    dt_min = (
        ts.diff()
        .dt.total_seconds()
        .div(60)
        .dropna()
    )

    print(
        "[clean]",
        f"cadence_min={dt_min.min():.4f}..{dt_min.max():.4f}",
    )

    if not ts.is_monotonic_increasing:
        raise RuntimeError(
            "Clean timestamps are not monotonic."
        )

    if float(dt_min.max()) > 40.0:
        raise RuntimeError(
            f"Clean window contains >40 min gap: {dt_min.max()}"
        )

    ids = df["acquisition_id"].to_numpy(int)

    if not np.array_equal(
        np.diff(ids),
        np.ones(len(ids) - 1, dtype=int),
    ):
        raise RuntimeError(
            "Clean acquisition IDs are not contiguous."
        )

    if not np.allclose(
        df["live_time_s"].to_numpy(float),
        1800.0,
        rtol=0,
        atol=1e-12,
    ):
        raise RuntimeError(
            "Clean live time is not uniformly 1800 s."
        )

    if not np.all(
        df["n_channels"].to_numpy(int)
        == N_CHANNELS
    ):
        raise RuntimeError(
            "Clean n_channels != 2048."
        )

    if df["calibration_slope"].nunique() != 1:
        raise RuntimeError(
            "Clean window spans multiple calibration slopes."
        )

    if df["calibration_offset"].nunique() != 1:
        raise RuntimeError(
            "Clean window spans multiple calibration offsets."
        )

    summed = spectrum_sum(df)
    reported = df["integral_counts"].to_numpy(float)

    rel = np.abs(summed - reported) / np.maximum(
        np.abs(reported),
        1.0,
    )

    print(
        "[clean]",
        f"max_integral_rel_error={rel.max():.6g}",
        f"median={np.median(rel):.6g}",
    )

    # Source-reported Integral is rounded; profiling showed <~0.11%.
    if float(rel.max()) > 0.002:
        raise RuntimeError(
            f"Clean integral mismatch unexpectedly large: {rel.max()}"
        )

    peaks = np.argmax(
        df[channel_columns(df)].to_numpy(float),
        axis=1,
    )

    print(
        "[clean]",
        f"peak_channel median={np.median(peaks):.1f}",
        f"range={peaks.min()}..{peaks.max()}",
    )

    if int(peaks.max() - peaks.min()) > 20:
        raise RuntimeError(
            "Clean dominant spectral peak is unexpectedly unstable."
        )

    print("[clean] invariants PASS")


# =============================================================================
# Controlled injections
# =============================================================================

def inj_clean(df, rng):
    return df.copy(), []


def inj_duplicate_acquisitions(df, rng):
    pick = np.sort(
        rng.choice(
            np.arange(150, len(df) - 150),
            size=20,
            replace=False,
        )
    )

    base = df.copy()
    base["__world_order"] = (
        np.arange(len(base), dtype=float) * 2.0
    )

    copies = df.iloc[pick].copy()
    copies["__world_order"] = (
        pick.astype(float) * 2.0 + 1.0
    )

    out = (
        pd.concat(
            [base, copies],
            ignore_index=True,
        )
        .sort_values("__world_order", kind="stable")
        .drop(columns="__world_order")
        .reset_index(drop=True)
    )

    affected = [
        f"acquisition_id={int(x)}"
        for x in copies["acquisition_id"]
    ]

    return out, affected


def inj_dropped_acquisitions(df, rng):
    start = 900
    stop = start + 48

    out = (
        df[
            ~df["acquisition_id"].between(
                start,
                stop - 1,
            )
        ]
        .copy()
        .reset_index(drop=True)
    )

    return (
        out,
        [f"acquisition_id={start}..{stop-1}"],
    )


def inj_timestamp_order_corruption(df, rng):
    out = df.copy()

    a0, a1 = 450, 514
    b0, b1 = 1050, 1114

    order = np.arange(len(out))

    block_a = order[a0:a1].copy()
    block_b = order[b0:b1].copy()

    order[a0:a1] = block_b
    order[b0:b1] = block_a

    out = (
        out.iloc[order]
        .reset_index(drop=True)
    )

    return (
        out,
        [
            f"row_block={a0}..{a1-1}",
            f"row_block={b0}..{b1-1}",
        ],
    )


def inj_livetime_unit_mismatch(df, rng):
    out = df.copy()

    start = 700
    stop = start + 128

    mask = out["acquisition_id"].between(
        start,
        stop - 1,
    )

    # 1800 seconds == 30 minutes, but field remains labeled seconds.
    out.loc[
        mask,
        "live_time_s",
    ] = (
        out.loc[
            mask,
            "live_time_s",
        ].to_numpy(float)
        / 60.0
    )

    return (
        out,
        [f"acquisition_id={start}..{stop-1}:live_time_s"],
    )


def inj_integral_spectrum_mismatch(df, rng):
    out = df.copy()

    start = 1200
    stop = start + 128

    mask = out["acquisition_id"].between(
        start,
        stop - 1,
    )

    # Strongly exceed harmless source rounding while preserving spectra.
    out.loc[
        mask,
        "integral_counts",
    ] = np.round(
        out.loc[
            mask,
            "integral_counts",
        ].to_numpy(float)
        * 1.08
    )

    return (
        out,
        [f"acquisition_id={start}..{stop-1}:integral_counts"],
    )


def inj_spectral_channel_shift(df, rng):
    out = df.copy()

    start = 1450
    stop = start + 128
    shift = 25

    mask = out["acquisition_id"].between(
        start,
        stop - 1,
    )

    cols = channel_columns(out)

    arr = out.loc[
        mask,
        cols,
    ].to_numpy(dtype=np.int64)

    # Shift the complete stored spectrum while preserving its total count.
    # Calibration metadata remains unchanged: this is the controlled defect.
    arr = np.roll(
        arr,
        shift=shift,
        axis=1,
    )

    out.loc[
        mask,
        cols,
    ] = arr

    return (
        out,
        [
            f"acquisition_id={start}..{stop-1}:"
            f"spectrum_shift=+{shift}_channels"
        ],
    )


def inj_abstain_calibration_change(df, rng):
    # Ignore the normal clean slice. Return a real, untouched source window
    # spanning the documented change in row-specific calibration metadata.
    sub = load_abstention_real()

    return sub, []


INJECT = {
    "clean": inj_clean,
    "duplicate_acquisitions": inj_duplicate_acquisitions,
    "dropped_acquisitions": inj_dropped_acquisitions,
    "timestamp_order_corruption": inj_timestamp_order_corruption,
    "livetime_unit_mismatch": inj_livetime_unit_mismatch,
    "integral_spectrum_mismatch": inj_integral_spectrum_mismatch,
    "spectral_channel_shift": inj_spectral_channel_shift,
    "abstain_calibration_change": inj_abstain_calibration_change,
}


# =============================================================================
# Solver / fire checks
# =============================================================================

def fire_check(issue, df):
    if issue == "clean":
        verify_clean(df)

    elif issue == "duplicate_acquisitions":
        ndup = int(
            df.duplicated(
                subset=[
                    "acquisition_id",
                    "timestamp",
                ]
            ).sum()
        )

        print(
            f"[fire] {issue}: duplicate_acquisitions={ndup}"
        )

        assert ndup >= 20

    elif issue == "dropped_acquisitions":
        ids = (
            df["acquisition_id"]
            .to_numpy(int)
        )

        gap_id = int(
            np.max(np.diff(ids))
        )

        ts = timestamps(df)

        gap_min = float(
            ts.diff()
            .dt.total_seconds()
            .div(60)
            .max()
        )

        print(
            f"[fire] {issue}: "
            f"max_id_gap={gap_id} "
            f"max_time_gap_min={gap_min:.2f}"
        )

        assert gap_id >= 49
        assert gap_min > 1000

    elif issue == "timestamp_order_corruption":
        ts = timestamps(df)

        n_backward = int(
            (
                ts.diff()
                .dt.total_seconds()
                < 0
            ).sum()
        )

        print(
            f"[fire] {issue}: backward_steps={n_backward}"
        )

        assert n_backward >= 2

    elif issue == "livetime_unit_mismatch":
        x = df["live_time_s"].to_numpy(float)

        n_30 = int(
            np.isclose(
                x,
                30.0,
                atol=1e-12,
            ).sum()
        )

        n_1800 = int(
            np.isclose(
                x,
                1800.0,
                atol=1e-12,
            ).sum()
        )

        print(
            f"[fire] {issue}: "
            f"n_30={n_30} "
            f"n_1800={n_1800}"
        )

        assert n_30 == 128
        assert n_1800 == len(df) - 128

    elif issue == "integral_spectrum_mismatch":
        summed = spectrum_sum(df)
        reported = df["integral_counts"].to_numpy(float)

        rel = np.abs(
            summed - reported
        ) / np.maximum(
            np.abs(summed),
            1.0,
        )

        n_big = int(
            (rel > 0.05).sum()
        )

        print(
            f"[fire] {issue}: "
            f"n_rel_error_gt_5pct={n_big} "
            f"max={rel.max():.4f}"
        )

        assert n_big == 128
        assert float(rel.max()) > 0.07

    elif issue == "spectral_channel_shift":
        cols = channel_columns(df)

        peaks = np.argmax(
            df[cols].to_numpy(float),
            axis=1,
        )

        affected = df["acquisition_id"].between(
            1450,
            1577,
        ).to_numpy()

        p_bad = float(
            np.median(
                peaks[affected]
            )
        )

        p_good = float(
            np.median(
                peaks[~affected]
            )
        )

        delta = p_bad - p_good

        print(
            f"[fire] {issue}: "
            f"good_peak={p_good:.1f} "
            f"bad_peak={p_bad:.1f} "
            f"delta={delta:.1f}"
        )

        assert delta >= 20.0

    elif issue == "abstain_calibration_change":
        ts = timestamps(df)

        if not ts.is_monotonic_increasing:
            raise RuntimeError(
                "Abstention real slice is not chronological."
            )

        slopes = (
            df["calibration_slope"]
            .drop_duplicates()
            .to_numpy(float)
        )

        offsets = (
            df["calibration_offset"]
            .drop_duplicates()
            .to_numpy(float)
        )

        max_gap = float(
            ts.diff()
            .dt.total_seconds()
            .div(60)
            .max()
        )

        print(
            f"[fire] {issue}: "
            f"slopes={slopes.tolist()} "
            f"offsets={offsets.tolist()} "
            f"max_gap_min={max_gap:.3f}"
        )

        assert len(slopes) >= 2
        assert len(offsets) >= 2
        assert max_gap < 40.0

        # The spectrum itself should remain finite/coherent across the real
        # transition; the mere coefficient update is not a corruption proof.
        cols = channel_columns(df)
        peaks = np.argmax(
            df[cols].to_numpy(float),
            axis=1,
        )

        print(
            f"[fire] {issue}: "
            f"raw_peak_range={peaks.min()}..{peaks.max()}"
        )

    else:
        raise KeyError(issue)


# =============================================================================
# World writing
# =============================================================================

EXPECTED_METHOD = (
    "Validate the long-term Co-60 NaI measurement table before decay-law "
    "inference: check exact duplicate acquisitions; missing acquisitions and "
    "timestamp/acquisition-id gaps; chronological row ordering; acquisition "
    "live-time units and consistency with real/dead time; 2048-channel spectral "
    "structure; agreement between reported integral counts and summed channel "
    "counts up to source rounding; and temporal stability/alignment of spectral "
    "features relative to the row-specific calibration slope and offset. "
    "Do not infer corrupted radiation measurements solely because the recorded "
    "per-acquisition spectral calibration coefficients change; use the supplied "
    "calibration and require independent evidence before declaring a real "
    "calibration update invalid."
)


def write_world(cell, issue, clean, rng):
    world_dir = DATA_OUT / f"cell{cell:03d}"

    if world_dir.exists():
        shutil.rmtree(world_dir)

    world_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    out, affected = INJECT[issue](
        clean.copy(),
        rng,
    )

    fire_check(
        issue,
        out,
    )

    data_path = world_dir / "radiation.csv.gz"

    out.to_csv(
        data_path,
        index=False,
        compression="gzip",
    )

    meta = dict(CLEAN_META)
    meta["rows"] = int(len(out))
    meta["spectral_channels"] = N_CHANNELS

    (world_dir / "measurement_meta.json").write_text(
        json.dumps(
            meta,
            indent=2,
        )
        + "\n"
    )

    gt = GT[issue]

    row = {
        "cell": cell,
        "world_label": issue,
        "issue_type": (
            "clean"
            if not gt["present"]
            else issue
        ),
        "issue_present": bool(
            gt["present"]
        ),
        "track": "nuclear_decay",
        "agent_input": str(
            world_dir.resolve()
        ),
        "agent_output": str(
            (
                RUN
                / f"out_cell{cell:03d}.json"
            ).resolve()
        ),
        "correct_action": gt[
            "correct_action"
        ],
        "affected_entities": list(
            affected
        ),
        "canonical_checks": list(
            gt["canonical_checks"]
        ),
        "diagnose_keywords": list(
            gt["diagnose_keywords"]
        ),
        "action_keywords": list(
            gt["action_keywords"]
        ),
        "expected_method": EXPECTED_METHOD,
    }

    for optional in [
        "requires_external_evidence",
        "abstention_question",
        "require_positive_flag_evidence",
    ]:
        if optional in gt:
            row[optional] = gt[optional]

    return row


def main():
    clean = load_clean()

    verify_clean(
        clean
    )

    if RUN.exists():
        # Preserve source code, but rebuild generated results deterministically.
        if DATA_OUT.exists():
            shutil.rmtree(DATA_OUT)

    DATA_OUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    rng = np.random.default_rng(
        RNG_SEED
    )

    issues = list(
        INJECT.keys()
    )

    manifest = []

    for cell, issue in enumerate(
        issues
    ):
        print()
        print(
            f"=== cell{cell:03d} {issue} ==="
        )

        row = write_world(
            cell,
            issue,
            clean,
            rng,
        )

        manifest.append(
            row
        )

    manifest_path = RUN / "manifest.json"

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
        )
        + "\n"
    )

    print()
    print(
        f"wrote {len(manifest)} worlds -> {manifest_path}"
    )


if __name__ == "__main__":
    main()
