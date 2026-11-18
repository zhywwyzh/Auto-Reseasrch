"""Figure 3 -- the chain landscape: every model, every track, all three stages.

Was an L1-only heat map. Now every cell is split into three sub-cells laid out LEFT TO RIGHT --
L1 | L2 | L3 -- so the figure answers what the single-stage version could not: a track or a model can
be strong at one stage of the chain and weak at another, invisible when only one stage is shown.
Horizontal beats stacked here because the chain itself runs left to right, so a cell is read in the
same direction as Figure 1, and each row stays one band tall.

COLOUR CARRIES TWO THINGS, KEPT SEPARATE. HUE = which stage (blue L1, amber L2, green L3), so a
sub-cell's identity is fixed wherever it appears. INTENSITY = the score within that stage's own
sequential ramp, all three fixed to 0-100 so a light band means the same thing in every ramp. Three
one-hue ramps rather than one rainbow: magnitude reads within a hue, identity reads across hues.

Ordering does real work. Rows are ordered by the TRACK GEOMETRIC CHAIN SCORE -- the benchmark's own
weakest-link aggregate -- not by the mean of the three stages, because a track weak at any one stage is
a weak track and the arithmetic mean hides exactly that. Columns stay in the FROZEN model order, never
by rank, so the figure cannot be read as a leaderboard -- which is the reading it exists to complicate.
The main-text figure is restricted to the eight-track molecular-life-science core. The initial
physics extension is reported separately in the appendix, so an incomplete transfer probe cannot be
mistaken for part of the core leaderboard or its 203-task denominator.

ONE MARGIN, NOT TWO. The bottom margin used to give each model's mean at each stage; Table 1 now
reports those same 18 numbers WITH their SD across tracks, so the margin was strictly less information
in a second place. What remains is what only this figure can show: the individual cells, and a right
margin carrying each track's three stage means plus a neutral tick at its geometric chain score. The
tick sits at or below the lowest stage mean by construction, so the gap between it and the stage dots
IS the discontinuity, read directly. SD whiskers across models were considered and rejected: they span
23.4-103.3, which would force the margin axis back to about 20-105 and undo the 1.4x resolution the
30-90 range exists to buy.

SOURCE: results/fig_data_levels.csv -- the POST-adjudication track_aggregation values, not raw graded
means. The two differ in 36 of 48 L1 model-track cells by up to 0.9 on the 0-3 scale, so this figure
and F04A (which must use graded per-world scores, since per-world detail exists nowhere else) will not
reconcile cell for cell. Both say so.

AUTHORED AT FINAL SIZE: 5.5 in wide, primary text >= 7.5 pt and secondary annotations >= 6.0 pt,
canvas sized to the drawn content.

Caption draft, kept here so figure and caption stay in sync:

    Figure 3: The chain landscape for the eight-track molecular-life-science core. Each cell holds three
    sub-cells read LEFT TO RIGHT -- L1 (blue),
    L2 (amber), L3 (green) -- giving that model's mean normalized score on that track at each stage, so
    a cell is read in the same direction as the chain in Figure 1 and its shape is the model's
    trajectory on that substrate. Colour carries two things kept separate: HUE is the stage, INTENSITY
    is the score within that stage's own sequential ramp, all three fixed to 0-100 so a light band
    means the same in every ramp. Rows are ordered by each track's GEOMETRIC CHAIN SCORE — the
    weakest-link aggregate — not by the mean of the three stages; columns are in a frozen model order,
    NOT by rank. The right margin gives each track's mean at each
    stage on a 30-90 axis (every track-stage mean lies in 43.2-85.6, so a full-range axis would
    compress the real spread into its middle third), plus a neutral tick at the track's geometric
    chain score: it lies at or below the lowest stage mean by construction, so the distance between
    them is the chain's discontinuity. There is no bottom margin — Table 1 reports each model's stage
    means with their SD across tracks. Values are
    descriptive means over controlled benchmark worlds, post-adjudication, and are not independent
    biological studies; the three annotations on the weakest tracks are assay-specific contamination
    (scRNA), reference/input signal quality (Histone) and baseline library plus screen QC (CRISPR).
    The strip beneath converts the grid into the claim it supports: how often a model reaches
    the TOP of the scale. Its rates are LIFE-SCIENCE ONLY and stay that way: pooling task-level ceiling
    rates across domains would weight the larger corpus more heavily. Perfect task scores are ordinary at L1, halve at L2 and all but disappear at
    L3, and NO model-track-level cell in the grid above reaches 100. The three rates are not the same bar:
    at L1 and L2 the maximum is a defined rubric rung, whereas the L3 composite is the mean of D,
    aggregate Q and N, so 100 there requires all seven axes at their maxima simultaneously -- which happened
    once. Bar length encodes the task-level ceiling rate. Per-world detail is in Figure 4.

Run: .venv_bench/bin/python fig03_chain_landscape.py
"""
import argparse
import csv
import json
import os
from pathlib import Path
import statistics
import matplotlib.pyplot as plt
import fig_common as C

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--include-glm53", action="store_true",
                    help="Add the audited leaderboard extension; preserve six-model reference inputs")
args = parser.parse_args()
ROOT = Path(__file__).resolve().parent
extension = None
if args.include_glm53:
    extension = json.loads((ROOT / "results/new_models/ROLLUP_glm-5.3.json").read_text())
    # Process-local display configuration only. Do not extend fig_common or frozen extracts.
    C.MODEL_ORDER = [*C.MODEL_ORDER, "glm-5.3"]
    C.SHORT = {**C.SHORT, "glm-5.2": "GLM-5.2", "glm-5.3": "GLM-5.3"}
    C.FULL = {**C.FULL, "glm-5.3": "GLM-5.3"}

# ---- distance from the ceiling ------------------------------------------------------------------
# The grid below shows how models SCORE. This shows how often they reach the top of the scale at all,
# which is the claim the grid supports but cannot state: no cell in it reaches 100.
# The three rates are NOT measuring the same object and the caption says so -- at L1 and L2 the maximum
# is a defined rubric rung, whereas the L3 composite is mean(D, aggregate Q, N), so 100 needs all SEVEN
# axes at their maxima at once. Bar length encodes the ceiling rate.
_l1 = C.load("fig_data_l1.csv")
_l2 = C.load("fig_data_l2.csv")
_l3 = [r for r in C.load("fig_data_l3.csv") if r["state"] != "CONFOUNDED-EXCLUDED"]
CEIL = {}
for _L, _rows, _col in (("L1", _l1, "score"), ("L2", _l2, "score"), ("L3", _l3, "composite")):
    _v = [r[_col] for r in _rows if r[_col] is not None]
    CEIL[_L] = (sum(1 for x in _v if x >= 3.0), len(_v))

FIG_W, UNIT_IN, TOP_U, BOT_U = 5.5, 6.21, 1.0, -0.55
LEVELS = ["L1", "L2", "L3"]
# one sequential ramp per stage: hue = stage, intensity = score, all three fixed to 0-100
RAMP = {
    "L1": ["#EDF3F9", "#D3E3F0", "#AFCCE4", "#7FAED2", "#4F87BC", "#255E92", "#123C63"],
    "L2": ["#FDF4E7", "#F8E3C3", "#F0CB93", "#E4AC5C", "#CE8A2E", "#A5670F", "#6F4408"],
    "L3": ["#EDF6F0", "#D2E9DA", "#AAD5BC", "#7CBB97", "#4C9C71", "#2A7A50", "#14532D"],
}
DARK_FROM = 4                      # ramp index at which cell text flips to white
FS_VAL, FS_LAB, FS_HEAD, FS_KEY = 7.5, 7.6, 7.6, 7.5

lev = [r for r in C.load("fig_data_levels.csv") if not r["family"]]
if extension:
    with (ROOT / "results/new_models/glm-5.3_levels.csv").open() as handle:
        extra = list(csv.DictReader(handle))
    assert len(extra) == 24 and all(r["model"] == "glm-5.3" for r in extra)
    for row in extra:
        row["score_pct"] = float(row["score_pct"])
    lev += extra
val = {(r["track_display"], r["level"], r["model"]): r["score_pct"] for r in lev
       if r["level"] in LEVELS}
# Rows are ordered by the TRACK GEOMETRIC CHAIN SCORE, not by the mean of the three stages. The two
# disagree, and the geometric one is the benchmark's own aggregate: a track weak at any single stage
# is a weak track, which is the whole weakest-link argument. Ordering by the arithmetic mean let a
# track with one collapsed stage sit above one that was merely even.
_fs = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "results/final_scores.json")))["track_aggregation"]
_KEY = {"GWAS": "GWAS", "ClinVar": "clinvar", "scRNA": "scRNA", "CRISPR": "crispr_screen",
        "Enhancer": "enhancer_activity", "Histone": "hist_gene_exp", "Protein": "protein_ddg",
        "Bulk RNA": "bulk_rnaseq"}
if extension:
    for record in extension["tracks"].values():
        _fs[record["canonical_key"]]["glm-5.3"] = record
tgeo = {t: statistics.mean(_fs[_KEY[t]][m]["track_geo"] for m in C.MODEL_ORDER) * 100 / 3
        for t in {r["track_display"] for r in lev}}
# The main-text landscape contains only the frozen molecular-life-science core. Physics is an initial
# two-track transfer probe and is reported separately in the appendix; it has no placeholder rows here
# and does not enter the core aggregation.
DOMAINS = [("MOLECULAR LIFE SCIENCES", sorted(tgeo, key=lambda t: -tgeo[t]), [])]
tracks = [t for _d, live, _res in DOMAINS for t in live]
tmean = {(t, L): statistics.mean(val[(t, L, m)] for m in C.MODEL_ORDER)
         for t in tracks for L in LEVELS}
mmean = {(m, L): statistics.mean(val[(t, L, m)] for t in tracks)
         for m in C.MODEL_ORDER for L in LEVELS}


def shade(L, v):
    r = RAMP[L]
    i = min(len(r) - 1, max(0, int(v / 100 * len(r))))
    return r[i], ("white" if i >= DARK_FROM else C.INK)


XL, CW = 0.128, 0.121              # row-label column ("Bulk RNA" bold needs 0.70 in), model column
GAP = 0.005                        # gap BETWEEN model groups, so the 18 sub-cells do not run together
if extension:
    XL, CW, GAP = 0.118, 0.111, 0.002
SW = (CW - GAP) / 3                # one sub-cell's width -- 0.21 in, fits "100" at 7.5 pt
RH = 0.021                         # one track row's height
XR = 0.122                         # right margin (track means)
if extension:
    XR = 0.084
# The track-mean axis runs 30-90, not 0-100: every track-stage mean lies in 43.2-85.6, so a full-range
# axis spent nearly half its width on empty space and squeezed the real spread into the middle third.
TM_LO, TM_HI = 30, 90
xs = [XL + i * CW for i in range(len(C.MODEL_ORDER))]
x_marg = XL + len(C.MODEL_ORDER) * CW + (0.008 if extension else 0.012)

fig, ax = plt.subplots(figsize=(FIG_W, UNIT_IN * (TOP_U - BOT_U)))
ax.set_position([0.0, 0.0, 1.0, 1.0])
ax.axis("off")
ax.patch.set_visible(False)
ax.set_xlim(0, 1); ax.set_ylim(BOT_U, TOP_U)

top = TOP_U - 0.030
for m, x in zip(C.MODEL_ORDER, xs):
    ax.text(x + CW / 2, top + 0.006, C.SHORT[m], ha="center", va="bottom", fontsize=FS_HEAD,
            color=C.INK)
# stage key, in the row-label column so it reads before the first cell
for k, L in enumerate(LEVELS):
    ax.add_patch(plt.Rectangle((XL + k * 0.048, top + 0.034), 0.013, 0.013,
                               facecolor=RAMP[L][4], edgecolor="none"))
    ax.text(XL + 0.017 + k * 0.048, top + 0.040, L, ha="left", va="center", fontsize=FS_KEY,
            color=C.INK2)
ax.text(0.004, top + 0.040, "each cell:", ha="left", va="center", fontsize=FS_KEY, color=C.INK3)
_kx = XL + len(LEVELS) * 0.048 + 0.018
ax.plot([_kx, _kx], [top + 0.034, top + 0.047], color=C.INK2, lw=1.1, solid_capstyle="butt")
ax.text(_kx + 0.008, top + 0.040, "track chain score", ha="left", va="center", fontsize=FS_KEY,
        color=C.INK2)
# The chain-score key belongs in the top-left legend, NOT over the margin column: the margin's own
# 30/50/70/90 tick labels already sit on that line, and a second label there landed on top of them.
ax.text(x_marg + XR / 2, top + 0.034, "track mean", ha="center", va="bottom",
        fontsize=FS_HEAD, color=C.INK3)

y = top
_grid_top = top
for _di, (_dom, _live, _reserved) in enumerate(DOMAINS):
    y -= 0.020 if _di == 0 else 0.034      # a header following rows needs clearance the first does not
    ax.text(0.004, y + 0.005, _dom, ha="left", va="bottom", fontsize=FS_KEY, color=C.INK3,
            fontweight="bold")
    _note = "" if not _reserved else "  ·  pending registry freeze"
    ax.text(XL + len(C.MODEL_ORDER) * CW, y + 0.005,
            f"{len(_live) + len(_reserved)} tracks{_note}", ha="right", va="bottom",
            fontsize=FS_KEY, color=C.INK3)
    for t in _live:
        y -= RH + 0.005
        cy = y + RH / 2
        ax.text(0.004, cy, t, ha="left", va="center", fontsize=FS_LAB, color=C.INK,
                fontweight="bold")
        for m, x in zip(C.MODEL_ORDER, xs):
            for k, L in enumerate(LEVELS):
                v = val[(t, L, m)]
                face, ink = shade(L, v)
                sx = x + GAP / 2 + k * SW
                ax.add_patch(plt.Rectangle((sx + 0.0008, y + 0.0012), SW - 0.0016, RH - 0.0024,
                                           facecolor=face, edgecolor="none"))
                ax.text(sx + SW / 2, cy, f"{v:.0f}", ha="center", va="center", fontsize=FS_VAL,
                        color=ink)
        # A NEUTRAL TICK for the track's geometric chain score, on the same axis as the three stage
        # means. The geometric aggregate penalizes imbalance; it is not the minimum stage score
        # and need not sit below every stage mean.
        # A tick and not a marker: a filled or open glyph large enough to see sat on top of the stage
        # dots it is meant to be compared against, and a vertical rule has no area to occlude with.
        # SD WHISKERS ACROSS MODELS ARE DELIBERATELY ABSENT: they span 23.4-103.3, which would force
        # this axis back to roughly 20-105 and undo the 1.4x resolution the 30-90 range buys.
        _gx = x_marg + XR * (tgeo[t] - TM_LO) / (TM_HI - TM_LO)
        ax.plot([_gx, _gx], [cy - RH * 0.42, cy + RH * 0.42], color=C.INK2, lw=1.1, zorder=4,
                solid_capstyle="butt")
        for L in LEVELS:                               # track means, three dots on one line
            ax.scatter([x_marg + XR * (tmean[(t, L)] - TM_LO) / (TM_HI - TM_LO)], [cy], s=15,
                       color=RAMP[L][5], edgecolor="white", linewidth=0.5, zorder=3)
for gx in (30, 50, 70, 90):
    gxp = x_marg + XR * (gx - TM_LO) / (TM_HI - TM_LO)
    ax.plot([gxp] * 2, [y - 0.002, _grid_top], color=C.GRID, lw=0.6, zorder=1)
    ax.text(gxp, top + 0.006, str(gx), ha="center", va="bottom", fontsize=6.6, color=C.INK3)

# THE BOTTOM MODEL-STAGE MARGIN WAS REMOVED. Table 1 now reports each model's L1/L2/L3 mean AND its
# SD across tracks, on the same 0-100 scale; the margin was the same 18 numbers without the SD. What
# stays here is what only this figure can say: the individual cells, and the per-track margin.
# ---- ceiling strip -------------------------------------------------------------------------------
ax.plot([0, XL + len(C.MODEL_ORDER) * CW], [y] * 2, color=C.GRID, lw=0.7)
y -= 0.026
ax.text(0.004, y, ("Six-model reference: task outcomes at the 100-point ceiling" if extension else
                  "life-science model–task outcomes at the 100-point ceiling"), fontsize=FS_LAB, color=C.INK,
        fontweight="bold",
        va="center")
# The count and the percentage are placed on separate anchors, not a shared offset: at 6.9 pt a
# left-aligned "263/474" is wide enough to run straight through a right-aligned "55.5%".
BAR_X, BAR_W, BAR_H = XL, 0.40, 0.016
y -= 0.030
for _i, _L in enumerate(LEVELS):
    _n, _d = CEIL[_L]
    _yy = y - _i * 0.028
    ax.text(BAR_X - 0.012, _yy, _L, ha="right", va="center", fontsize=6.9, color=RAMP[_L][5],
            fontweight="bold")
    ax.add_patch(plt.Rectangle((BAR_X, _yy - BAR_H / 2), BAR_W, BAR_H, facecolor="#F2F4F7",
                               edgecolor="none"))
    ax.add_patch(plt.Rectangle((BAR_X, _yy - BAR_H / 2), BAR_W * _n / _d, BAR_H,
                               facecolor=RAMP[_L][5], edgecolor="none"))
    ax.text(BAR_X + BAR_W + 0.012, _yy, f"{_n}/{_d}", ha="left", va="center", fontsize=6.9,
            color=C.INK2)
    ax.text(BAR_X + BAR_W + 0.150, _yy, f"{100 * _n / _d:.1f}%", ha="right", va="center",
            fontsize=6.9, color=RAMP[_L][5], fontweight="bold")
y -= 2 * 0.028 + 0.026
_best = max((val[(t, L, m)], t, L, m) for t in tracks for L in LEVELS for m in C.MODEL_ORDER)
_n144 = sum(1 for t in tracks for L in LEVELS for m in C.MODEL_ORDER if val[(t, L, m)] >= 100)
ax.text(0.004, y, f"{_n144} of {len(tracks) * len(LEVELS) * len(C.MODEL_ORDER)} "
        f"model\u00d7track\u00d7level cells reach 100   \u00b7   highest "
        f"{_best[0]:.1f} ({C.SHORT[_best[3]]}, {_best[1]} {_best[2]})",
        fontsize=6.8, color=C.INK3, va="center")
y -= 0.016

_y_end = y - 0.010
ax.set_ylim(_y_end, TOP_U)
fig.set_size_inches(FIG_W, UNIT_IN * (TOP_U - _y_end))

_csv_rows = [
    {"row_type": "level_cell", "track": t, "model": C.FULL[m], "level": L,
     "score_pct": val[(t, L, m)], "track_stage_mean_pct": round(tmean[(t, L)], 2),
     "model_stage_mean_pct": round(mmean[(m, L)], 2)}
    for t in tracks for L in LEVELS for m in C.MODEL_ORDER
]
for _L in LEVELS:
    _n, _d = CEIL[_L]
    _csv_rows.append({
        "row_type": "task_ceiling", "level": _L, "ceiling_n": _n, "ceiling_d": _d,
        "ceiling_rate_pct": round(100 * _n / _d, 1),
        "note": "six-model reference outcomes at the 100-point ceiling (native score/composite 3.0)",
    })
_csv_rows.append({
    "row_type": "level_ceiling_summary", "track": _best[1], "model": C.FULL[_best[3]],
    "level": _best[2], "score_pct": _best[0], "ceiling_n": _n144,
    "ceiling_d": len(tracks) * len(LEVELS) * len(C.MODEL_ORDER),
    "ceiling_rate_pct": 100 * _n144 / (len(tracks) * len(LEVELS) * len(C.MODEL_ORDER)),
    "note": "numerator/denominator count whole model×track×level means at 100; "
            "track/model/level/score identify the highest observed cell",
})
C.save(fig, "F03_chain_landscape_7models" if extension else "F03_chain_landscape", _csv_rows,
       ["row_type", "track", "model", "level", "score_pct", "track_stage_mean_pct",
        "model_stage_mean_pct", "ceiling_n", "ceiling_d", "ceiling_rate_pct", "note"])
