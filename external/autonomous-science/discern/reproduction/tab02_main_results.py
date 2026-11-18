"""Table 2 -- main results: the chain, uncollapsed.

ONE table, one column set, two row blocks -- models above, tracks below -- replacing what were three
separate artifacts. The blocks share columns because they ask the same question of different units:
how did the three stages of the chain go, and how far apart were they? A reader scans down the L3
column and sees both which model and which substrate the discovery stage is hardest for.

NO COST COLUMNS. Cost is a parallel axis with its own accounting protocol, pricing date and caveats
(COST_EFFICIENCY.md); folding dollar columns in here invites a reader to trade quality against cost
without any of that context. E1-E4 and F09-F10 carry it properly.

AUTHORED AT FINAL SIZE, emitting <= 5.5 in (the ICLR \textwidth), every glyph at 7.5 pt or larger, so the
PDF drops in at 1:1 and nothing is scaled down. An earlier 7.6-inch version rendered its values near
6.5 pt and its SDs near 5.3 pt once fitted to the column, which is below the plan's 7.5-pt floor.

PRESENTATION MODELLED ON NEWTONBENCH TABLE 2, whose devices were read off the published table rather
than its caption. Four are adopted:

  1. TWO-LEVEL COLUMN HEADERS. They span "easy/medium/hard" under "Vanilla Equation / Simple System /
     Complex System", then a separate "Average" span. Ours spans L1/L2/L3 under "chain stage" and the
     rest under "summary", so a reader sees the column structure before reading a number.
  2. DIRECTION ARROWS in the header (theirs: SA(%) up, RMSLE down). Ours marks the score columns up.
     Spread deliberately carries NO arrow -- a small spread is not a virtue, it is a description.
  3. MEAN (+-SD) IN EVERY CELL. Theirs is dispersion across 4 reruns. Ours cannot be: we have one run.
     It is dispersion across the 8 TRACKS a model was averaged over, or the 6 MODELS a track was
     averaged over -- heterogeneity, not run-to-run noise. It changes the reading: DeepSeek's L2 is
     1.84 +-0.60, so that mean is standing in for very unlike tracks.
  4. BEST BOLD, SECOND UNDERLINED, within each block and column. Theirs marks within each agent
     configuration; ours within each row block, since comparing a model against a track is meaningless.

COLOUR, in two strictly separated roles. TINT = magnitude: the stage cells carry a light sequential
tint keyed to the value, so the SHAPE of a row is visible before any number is read -- Claude's
2.56 / 2.39 / 1.89 fades along the chain while GPT-5.6-sol's stays flat. Tints stay in the light half
of the ramp so bold and underline still read. HUE = identity, and nothing else: model colour appears
only in the row chips and in the best-at-this-stage dot.

TIES ARE SHOWN, NOT HIDDEN. Three track-stage cells are exact ties and a bare max() would have
credited whichever model the dict happened to yield first: CRISPR L1 (DeepSeek and GLM, both 2.10),
Histone L1 and Histone L2 (GPT-5.6-sol and Claude, 2.30 and 2.50). Those cells carry TWO dots.

Caption draft, kept here so table and caption stay in sync. The title lives here rather than inside
the figure, for the same width reason as the fonts:

    Table 2: Chain performance, uncollapsed. Upper block: each model's mean score at the three chain
    stages, averaged over the eight tracks. Lower block: each track's mean at each stage, averaged over
    the six models. Cells report mean (+-SD) on the native 0-3 scale. THE SD IS HETEROGENEITY, NOT
    UNCERTAINTY: each task was run once, so it measures how much the tracks (upper block) or the models
    (lower block) being averaged differ from one another, and carries no rerun variance. Within each
    block and column, the best value is BOLD and the second is UNDERLINED. Cell tint encodes the score,
    so a row's shape along the chain can be read directly. In the lower block a coloured dot left of
    each value identifies the model that scored best at that stage, using the same colours as the model
    chips above; TIED WINNERS ARE SHOWN AS TWO DOTS, which occurs at CRISPR L1 (DeepSeek V4 Pro and
    GLM-5.2) and at Histone L1 and L2 (GPT-5.6-sol and Claude Opus 5). One colour across a row means a
    single model owned that track; different colours mean the chain came apart, which happens in seven
    of eight tracks. `overall` is the TRACK-LEVEL GEOMETRIC AGGREGATE (weakest-link, PAPER_NOTES 3b) --
    it is not the mean of the three displayed columns, and will not reproduce from them. `spread` is
    max - min across the three stages and is descriptive rather than good or bad; RED MARKS A SPREAD OF
    0.60 OR MORE, where one number cannot stand for the chain. Step budgets differ by stage and are
    part of a score's meaning: L1 and L2 run to max_steps=20, L3 to 3-6 steps plus three rounds of
    adversarial review. NO CELL IN THIS TABLE, AND NO MODEL-TRACK-LEVEL CELL BEHIND IT, REACHES THE
    3.0 CEILING: the maximum over all 144 is 2.947 (Claude Opus 5, scRNA L2). Figure 3 reports how
    often individual tasks reach it -- 55.5% at L1, 32.0% at L2, 0.8% at L3. Cost is reported
    separately (Figures E1-E4).

Run: .venv_bench/bin/python tab02_main_results.py
"""
import collections
import json
import os
import statistics
import matplotlib.pyplot as plt
import fig_common as C

TRACKS = ["GWAS", "ClinVar", "scRNA", "CRISPR", "Enhancer", "Histone", "Protein", "Bulk RNA"]
LEVELS = ["L1", "L2", "L3"]
WIDE_SPREAD = 0.60          # at or above this, one number cannot stand for the chain
TINT = ["#F5F8FB", "#E8F0F7", "#D8E7F2", "#C6DBEC", "#B2CEE5", "#9CC0DE"]   # light half only
EPS = 1e-9                  # exact ties only; these are means of exact rationals, not noisy estimates

FS_VAL, FS_SD, FS_HEAD, FS_BLOCK = 7.8, 7.5, 7.6, 7.5      # nothing below the 7.5 pt floor

lev = [r for r in C.load("fig_data_levels.csv") if not r["family"]]
score = collections.defaultdict(dict)
for r in lev:
    score[(r["track_display"], r["level"])][r["model"]] = r["score"]

_fs = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "results/final_scores.json")))
_TA = _fs["track_aggregation"]
_KEY = {"GWAS": "GWAS", "ClinVar": "clinvar", "scRNA": "scRNA", "CRISPR": "crispr_screen",
        "Enhancer": "enhancer_activity", "Histone": "hist_gene_exp", "Protein": "protein_ddg",
        "Bulk RNA": "bulk_rnaseq"}
geo = {(t, m): _TA[_KEY[t]][m]["track_geo"] for t in TRACKS for m in C.MODEL_ORDER}


def tint(v):
    return TINT[min(len(TINT) - 1, max(0, int(v / 3 * len(TINT))))]


def winners(d):
    """EVERY model at the maximum, not whichever one max() reached first."""
    hi = max(d.values())
    return [m for m in C.MODEL_ORDER if abs(d[m] - hi) < EPS]


ROWS = []          # (label, kind, {L: (mean, sd)}, overall, {L: [best models]}, model id)
for m in C.MODEL_ORDER:
    vals = {L: (statistics.mean(score[(t, L)][m] for t in TRACKS),
                statistics.stdev([score[(t, L)][m] for t in TRACKS])) for L in LEVELS}
    ROWS.append((C.FULL[m], "model", vals, statistics.mean(geo[(t, m)] for t in TRACKS),
                 {L: [] for L in LEVELS}, m))
for t in TRACKS:
    vals = {L: (statistics.mean(score[(t, L)].values()),
                statistics.stdev(list(score[(t, L)].values()))) for L in LEVELS}
    ROWS.append((t, "track", vals, statistics.mean(geo[(t, m)] for m in C.MODEL_ORDER),
                 {L: winners(score[(t, L)]) for L in LEVELS}, None))

# best / second within each block and column; ties share the mark rather than one row taking it
RANK = {}
for kind in ("model", "track"):
    blk = [r for r in ROWS if r[1] == kind]
    for key, get in [(L, (lambda r, L=L: r[2][L][0])) for L in LEVELS] + [("overall",
                                                                          lambda r: r[3])]:
        vs = sorted({round(get(r), 12) for r in blk}, reverse=True)
        for r in blk:
            v = round(get(r), 12)
            if v == vs[0]:
                RANK[(kind, key, r[0])] = "best"
            elif len(vs) > 1 and v == vs[1]:
                RANK[(kind, key, r[0])] = "second"

fig, ax = plt.subplots(figsize=(5.5, 5.0))          # authored at the ICLR column width
ax.set_position([0.0, 0.0, 1.0, 1.0])               # axes fills the canvas, so the trimmed PDF really
ax.axis("off")                                      # IS 5.5 in and nothing is rescaled on import
ax.set_xlim(0, 1); ax.set_ylim(0, 1)

XL = 0.225                                    # row-label column
CW, XO, XS = 0.185, 0.115, 0.100              # stage, overall, spread (sums to ~0.995)
xs = [XL + i * CW for i in range(3)]
x_over, x_spr = XL + 3 * CW, XL + 3 * CW + XO
head_y, rh = 0.845, 0.0530

# --- two-level header ------------------------------------------------------------------------------
ax.plot([xs[0], xs[0] + 3 * CW], [head_y + 0.108] * 2, color=C.INK2, lw=0.8)
ax.text(xs[0] + 1.5 * CW, head_y + 0.119, "chain stage  (0–3) ↑", ha="center", va="bottom",
        fontsize=FS_HEAD, color=C.INK, fontweight="bold")
ax.plot([x_over, x_spr + XS], [head_y + 0.108] * 2, color=C.INK2, lw=0.8)
ax.text((x_over + x_spr + XS) / 2, head_y + 0.119, "summary", ha="center", va="bottom",
        fontsize=FS_HEAD, color=C.INK, fontweight="bold")
for L, x in zip(LEVELS, xs):
    ax.text(x + CW / 2, head_y + 0.010, {"L1": "L1\nintegrity", "L2": "L2\nanalysis",
                                         "L3": "L3\ndiscovery"}[L],
            ha="center", va="bottom", fontsize=FS_HEAD, color=C.INK, linespacing=1.45)
ax.text(x_over + XO / 2, head_y + 0.010, "overall ↑\ngeo", ha="center", va="bottom",
        fontsize=FS_HEAD, color=C.INK, linespacing=1.45)
ax.text(x_spr + XS / 2, head_y + 0.010, "spread\nmax−min", ha="center", va="bottom",
        fontsize=FS_HEAD, color=C.INK3, linespacing=1.45)
ax.plot([0, x_spr + XS], [head_y - 0.008] * 2, color=C.INK2, lw=1.1)

BLOCK_LABEL = {"model": "by model  ·  mean (±SD) over the 8 tracks",
               "track": "by track  ·  mean (±SD) over the 6 models"}
y = head_y - 0.030
for i, (label, kind, vals, over, best, m) in enumerate(ROWS):
    if i and ROWS[i - 1][1] != kind:
        ax.plot([0, x_spr + XS], [y + 0.030] * 2, color=C.INK2, lw=1.1)
        y -= 0.012
    if i == 0 or ROWS[i - 1][1] != kind:
        ax.text(0.004, y, BLOCK_LABEL[kind], fontsize=FS_BLOCK, color=C.INK3, style="italic",
                va="center")
        y -= 0.036
    if kind == "model":
        ax.scatter([0.014], [y], s=26, color=C.COLOR[m])
        ax.text(0.038, y, label, ha="left", va="center", fontsize=FS_VAL, color=C.INK)
    else:
        ax.text(0.004, y, label, ha="left", va="center", fontsize=FS_VAL, color=C.INK,
                fontweight="bold")
    for L, x in zip(LEVELS, xs):
        mu, sd = vals[L]
        cx = x + CW / 2
        ax.add_patch(plt.Rectangle((x + 0.004, y - rh / 2 + 0.006), CW - 0.008, rh - 0.012,
                                   facecolor=tint(mu), edgecolor="none", zorder=1))
        # who was best here, in the same cell as how well it went; two dots when tied
        w = best[L]
        if len(w) == 1:
            ax.scatter([cx - 0.052], [y], s=26, color=C.COLOR[w[0]], zorder=3)
        elif len(w) > 1:
            for j, mm in enumerate(w[:2]):
                ax.scatter([cx - 0.064 + j * 0.019], [y], s=22, color=C.COLOR[mm], zorder=3)
        mark = RANK.get((kind, L, label))
        ax.text(cx + 0.010, y, f"{mu:.2f}", ha="right", va="center", fontsize=FS_VAL, color=C.INK,
                fontweight="bold" if mark == "best" else "normal", zorder=3)
        if mark == "second":
            ax.plot([cx - 0.026, cx + 0.010], [y - 0.017] * 2, color=C.INK, lw=0.8, zorder=3)
        ax.text(cx + 0.017, y, f"±{sd:.2f}", ha="left", va="center", fontsize=FS_SD, color=C.INK3,
                zorder=3)
    mark = RANK.get((kind, "overall", label))
    ax.text(x_over + XO / 2, y, f"{over:.2f}", ha="center", va="center", fontsize=FS_VAL,
            color=C.INK, fontweight="bold" if mark == "best" else "normal")
    if mark == "second":
        ax.plot([x_over + XO / 2 - 0.017, x_over + XO / 2 + 0.017], [y - 0.017] * 2, color=C.INK,
                lw=0.8)
    s = max(v[0] for v in vals.values()) - min(v[0] for v in vals.values())
    ax.text(x_spr + XS / 2, y, f"{s:.2f}", ha="center", va="center", fontsize=FS_VAL,
            color="#B03A2E" if s >= WIDE_SPREAD else C.INK3,
            fontweight="bold" if s >= WIDE_SPREAD else "normal")
    y -= rh
ax.plot([0, x_spr + XS], [y + 0.030] * 2, color=C.INK2, lw=1.1)

C.save(fig, "T02_main_results",
       [{"block": kind, "row": label,
         **{f"{L}_mean": round(vals[L][0], 3) for L in LEVELS},
         **{f"{L}_sd": round(vals[L][1], 3) for L in LEVELS},
         "overall_track_geo": round(over, 3),
         "stage_spread": round(max(v[0] for v in vals.values())
                               - min(v[0] for v in vals.values()), 3),
         "best_model_per_stage": "" if not best["L1"] else
         "; ".join(f"{L}=" + "|".join(C.FULL[x] for x in best[L]) for L in LEVELS)}
        for label, kind, vals, over, best, m in ROWS],
       ["block", "row"] + [f"{L}_mean" for L in LEVELS] + [f"{L}_sd" for L in LEVELS]
       + ["overall_track_geo", "stage_spread", "best_model_per_stage"])
