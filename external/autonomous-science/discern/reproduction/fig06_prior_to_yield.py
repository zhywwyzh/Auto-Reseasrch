"""Figure 6 -- following evidence and generating hypotheses are DISTINCT capabilities.

The L3 story has two bottlenecks and the benchmark had been reporting only the second. A model must
(a) let the evidence move it off its prior at all, and (b) commit to a hypothesis that is actually
worth something. A model can pass either without the other, and the two panels here separate them.

WHY THIS FIGURE EXISTS. Figure 4's novelty row is CONDITIONAL on committing, because novelty is only
recorded when a model produces a hypothesis -- 52 of the 131 graded L3 outputs are an ABSTAIN-*
state with no N at all. Read alone, that row says GPT-5.6-sol (mean N 1.25 when committed) and Claude
(1.24) are near-identical. They are not: GPT-5.6-sol declined on 18 of 22 worlds and Claude on 4. The
hurdle plot puts commitment on one axis and conditional quality on the other so the dissociation is
unmissable, and the yield contours show what their product is worth.

PANEL A reuses the data-free prior baseline (BixBench Figure 4's most valuable element: a benchmark
that cannot beat pure recall is not measuring analysis). Every counterfactual world is a paired
comparison between what the model expected before seeing evidence and what it concluded after.

PANEL B is a hurdle plot: P(commit) horizontally, E[N | commit] vertically, with iso-yield contours.
Their product P(commit) x E[N | commit] is a DERIVED REPORTING STATISTIC, not a benchmark score --
nothing in grade_l3 computes it and it is not part of any track or overall number. It is drawn as
contours rather than as a bar precisely so it reads as a consequence of two measured quantities
rather than as a seventh axis.

WHY A CALIBRATED ABSTENTION IS NOT SCORED AS A BAD HYPOTHESIS. Declining is a legitimate act in this
benchmark -- the 2.5 abstention ceiling is deliberate -- so an abstention is never given N=0. It
lowers the horizontal axis and leaves the vertical one alone, which is exactly what it means.

PANEL C shows that novelty is CASE-dependent far more than model-dependent, which no model average can
show. Only 4 of the 130 aggregate-eligible outcomes earn N=3, three of them on the SAME world (hist_gene_exp
cf_bivalent_native, the DUSP4 bivalency flip) and the fourth on protein_ddg cf_stabilizing. Histone
carries 9 of the 22 outcomes with N>=2; ClinVar has none at all. Abstentions get their own glyph
rather than being silently rendered as N=0, and the two gate-excluded cells get an x.

THE THREE DENOMINATORS, because they are one apart and easy to mix up:
  132  cells             = 22 worlds x 6 models, the full grid.
  131  GRADED OUTPUTS    = what fig_data_l3.csv holds; bulk_rnaseq/cf_cytokine_flip/claude-opus-5 is
                           absent entirely.
  130  AGGREGATE-ELIGIBLE = graded minus cf_gwas/cf_GSTM1/kimi-k3, which carries a CONFOUNDED-EXCLUDED
                           state and is omitted from every mean.
Never write "of 131 eligible": 131 is the graded count, 130 is the eligible one.

TWO GATE EXCLUSIONS, TWO REPRESENTATIONS. cf_gwas/cf_GSTM1/kimi-k3 carries a CONFOUNDED-EXCLUDED state;
bulk_rnaseq/cf_cytokine_flip/claude-opus-5 is simply ABSENT from the extract. A denominator filtering
on the state label alone gets Claude wrong; one counting rows alone gets Kimi wrong. Both are handled.

LANGUAGE. "Valid novelty UNDER THE BENCHMARK RUBRIC" -- not "new scientific discoveries". Whether the
four N=3 cases are novel to the field needs a blinded prior-art audit that has not been run.

Caption draft, kept here so figure and caption stay in sync:

    Figure 6: Following evidence and generating hypotheses are distinct capabilities. (A) How often the
    counterfactual evidence moved a model off the prior it stated before seeing any data; an abstention
    is neither a move nor a defence and is shown as its own segment. (B) The discovery hurdle: the
    fraction of eligible worlds on which a model committed to a hypothesis, against the mean novelty of
    the hypotheses it did commit to. Contours are iso-yield, P(commit) x E[N | commit], a derived
    reporting statistic rather than a benchmark score. GPT-5.6-sol and Claude produce hypotheses of
    almost identical conditional quality, but Claude produces them four times as often. (C) Novelty per
    world, showing that it is case-dependent: 4 of 130 aggregate-eligible outcomes reach N=3, three on one world.
    Abstentions carry their own glyph and are never scored zero; x marks a prior-gate exclusion.

Run: .venv_bench/bin/python fig06_prior_to_yield.py
"""
import collections
import statistics
import matplotlib.pyplot as plt
import numpy as np
import fig_common as C

FIG_W = 5.5
CATS = ["data", "mixed", "prior", "declined"]
LABEL = {"data": "moved to the data", "mixed": "partly retreated",
         "prior": "snapped back to the prior", "declined": "declined (neither)"}
FILL = {"data": "#1B6B50", "mixed": "#E8A33D", "prior": "#B03A2E", "declined": C.STATE_ABSTENTION}
NRAMP = {0: "#EDF3F9", 1: "#B9D2E6", 2: "#5E94C4", 3: "#123C63"}
FS = 7.5

l3_all = C.load("fig_data_l3.csv")
l3 = [r for r in l3_all if r["state"] != "CONFOUNDED-EXCLUDED"]
EXCLUDED = {(r["track"], r["world"], r["model"]) for r in l3_all
            if r["state"] == "CONFOUNDED-EXCLUDED"}
WORLDS = sorted({(r["track_display"], r["track"], r["world"], r["is_counterfactual"])
                 for r in l3_all}, key=lambda w: (w[0], w[3], w[2]))
for tr, t, w, cf in WORLDS:                      # a row missing entirely is also an exclusion
    for m in C.MODEL_ORDER:
        if not any(r["track"] == t and r["world"] == w and r["model"] == m for r in l3_all):
            EXCLUDED.add((t, w, m))


def bucket(label):
    if not label:
        return None
    u = str(label).upper()
    return ("data" if u.startswith("TRUSTS-DATA") else "prior" if u.startswith("TRUSTS-PRIOR")
            else "mixed" if u.startswith("MIXED") else None)


# ---- panel data ------------------------------------------------------------------------------------
PRIOR = collections.defaultdict(collections.Counter)
for r in l3:
    if not r["is_counterfactual"]:
        continue
    b = bucket(r["data_vs_prior"])
    if b is None and str(r["state"]).startswith("ABSTAIN"):
        b = "declined"
    if b:
        PRIOR[r["model"]][b] += 1

HURDLE = {}
for m in C.MODEL_ORDER:
    elig = [r for r in l3 if r["model"] == m]
    com = [r for r in elig if not str(r["state"]).startswith("ABSTAIN")]
    nov = [r["novelty"] for r in com if r["novelty"] is not None]
    HURDLE[m] = (len(com) / len(elig), statistics.mean(nov) if nov else 0.0, len(com), len(elig))

fig = plt.figure(figsize=(FIG_W, 5.35))
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.42], width_ratios=[1, 1],
                      # right=0.94, not 0.985: Panel B's contour labels and Panel C's rotated world
                      # labels sit slightly outside their axes, and the tight bbox adds that overhang to
                      # the emitted width. Reserving the margin INSIDE the canvas keeps the PDF at the
                      # 5.5 in column, where every glyph holds its authored size.
                      left=0.115, right=0.94, top=0.935, bottom=0.055, hspace=0.46, wspace=0.30)

# ---- A: did the evidence move the model? -----------------------------------------------------------
axA = fig.add_subplot(gs[0, 0])
for yi, m in enumerate(C.MODEL_ORDER):
    y = len(C.MODEL_ORDER) - 1 - yi
    tot = sum(PRIOR[m].values()) or 1
    x = 0.0
    for c in CATS:
        w = 100 * PRIOR[m][c] / tot
        if w:
            axA.barh(y, w, left=x, height=0.66, color=FILL[c], edgecolor="white", linewidth=0.6)
        x += w
axA.set_xlim(0, 100); axA.set_ylim(-0.6, len(C.MODEL_ORDER) - 0.4)
axA.set_yticks(range(len(C.MODEL_ORDER)))
axA.set_yticklabels([C.SHORT[m] for m in reversed(C.MODEL_ORDER)], fontsize=FS, color=C.INK)
axA.set_xticks([0, 50, 100]); axA.set_xticklabels(["0", "50", "100%"], fontsize=FS)
axA.tick_params(length=0)
for sp in ("top", "right", "left"):
    axA.spines[sp].set_visible(False)
axA.spines["bottom"].set_color(C.GRID)
# Keep this SHORT. "A evidence moved the model off its prior" is wider than Panel A's axes and ran
# straight into Panel B's title, rendering as "...priorB". The full sentence lives in the caption.
axA.set_title("A   evidence vs. stated prior", fontsize=8.0, color=C.INK,
              fontweight="bold", loc="left", pad=6)
axA.legend(handles=[plt.Line2D([], [], marker="s", ls="", markersize=5, color=FILL[c],
                               label=LABEL[c]) for c in CATS],
           loc="upper left", bbox_to_anchor=(-0.02, -0.16), ncol=2, fontsize=6.6,
           handletextpad=0.4, columnspacing=0.9, borderpad=0)

# ---- B: the discovery hurdle -----------------------------------------------------------------------
axB = fig.add_subplot(gs[0, 1])
gx, gy = np.meshgrid(np.linspace(0.02, 1.0, 200), np.linspace(0.02, 1.6, 200))
cs = axB.contour(gx, gy, gx * gy, levels=[0.25, 0.5, 0.75, 1.0], colors=C.GRID, linewidths=0.7)
# Label the contours along the TOP EDGE (y=1.52), where nothing is plotted. Automatic placement put the
# "1" label directly under Claude's dot -- Claude's yield IS 1.00, so it sits exactly on that contour.
# Hand-placed, one point per contour, each chosen to be ON its own curve and clear of every model dot.
# Automatic placement put "1" under Claude (whose yield IS 1.00, so it sits exactly on that contour);
# a uniform top-edge rule then put "0.25" on top of GPT-5.6-sol. 0.25 is the only one routed to the
# empty bottom-right instead of the empty top edge.
_CLAB = {0.25: 0.92, 0.5: 0.333, 0.75: 0.5, 1.0: 0.667}
axB.clabel(cs, fmt=lambda v: f"{v:g}", fontsize=6.2, colors=C.INK3, inline_spacing=2,
           manual=[(x, lv / x) for lv, x in _CLAB.items()])
# Per-model label placement. Claude (0.81, 1.24) and Kimi (0.76, 0.94) are close in x, and Claude sits
# on the 1.0 contour, so neither can take the default "above, centred".
OFF = {"claude-opus-5": ((9, 4), "left"), "kimi-k3": ((-9, 1), "right"),
       "glm-5.2": ((-9, 1), "right"), "deepseek-v4-pro": ((-9, 1), "right"),
       "gpt-4.1": ((9, -1), "left"), "gpt-5.6-sol": ((0, -13), "center")}
for m in C.MODEL_ORDER:
    p, n, *_ = HURDLE[m]
    axB.scatter([p], [n], s=42, color=C.COLOR[m], edgecolor="white", linewidth=0.8, zorder=3)
    xy, ha = OFF[m]
    axB.annotate(C.SHORT[m], (p, n), textcoords="offset points", xytext=xy, ha=ha, va="center",
                 fontsize=6.8, color=C.INK)
axB.set_xlim(0, 1.0); axB.set_ylim(0, 1.6)
axB.set_xticks([0, 0.25, 0.5, 0.75, 1.0]); axB.set_xticklabels(["0", "", "50", "", "100%"], fontsize=FS)
axB.set_yticks([0, 0.5, 1.0, 1.5]); axB.tick_params(length=0, labelsize=FS)
axB.set_xlabel("worlds with a committed hypothesis", fontsize=7.5, color=C.INK2, labelpad=1)
axB.set_ylabel("mean novelty | committed", fontsize=7.5, color=C.INK2, labelpad=1)
for sp in ("top", "right"):
    axB.spines[sp].set_visible(False)
axB.spines["left"].set_color(C.GRID); axB.spines["bottom"].set_color(C.GRID)
axB.set_axisbelow(True)
axB.set_title("B   the discovery hurdle", fontsize=8.0, color=C.INK, fontweight="bold", loc="left",
              pad=6)
# Lower-LEFT, not upper-right: the upper-right is where Claude sits, and the note was printing across
# its label. Nothing is plotted below y=0.4 to the left of x=0.5.
axB.text(0.03, 0.30, "contours = yield\nP(commit) × E[N|commit]", ha="left", va="top", fontsize=6.2,
         color=C.INK3, linespacing=1.35)

# ---- C: world-level novelty ------------------------------------------------------------------------
axC = fig.add_subplot(gs[1, :])
by = {(r["track"], r["world"], r["model"]): r for r in l3}
for xi, (tr, t, w, cf) in enumerate(WORLDS):
    for yi, m in enumerate(C.MODEL_ORDER):
        y = len(C.MODEL_ORDER) - 1 - yi
        if (t, w, m) in EXCLUDED:
            axC.text(xi + 0.5, y + 0.5, "×", ha="center", va="center", fontsize=7.2, color=C.INK3)
            continue
        r = by.get((t, w, m))
        if r is None or r["novelty"] is None:      # abstained: its own glyph, never N=0
            axC.add_patch(plt.Rectangle((xi + .06, y + .06), .88, .88, facecolor="white",
                                        edgecolor=C.STATE_ABSTENTION, linewidth=0.8, ls=(0, (1.6, 1.2))))
            continue
        n = int(round(r["novelty"]))
        axC.add_patch(plt.Rectangle((xi + .06, y + .06), .88, .88, facecolor=NRAMP[n],
                                    edgecolor="none"))
        if n == 3:
            axC.text(xi + 0.5, y + 0.5, "3", ha="center", va="center", fontsize=6.8, color="white",
                     fontweight="bold")
axC.set_xlim(0, len(WORLDS)); axC.set_ylim(0, len(C.MODEL_ORDER))
axC.set_yticks([len(C.MODEL_ORDER) - 1 - i + 0.5 for i in range(len(C.MODEL_ORDER))])
axC.set_yticklabels([C.SHORT[m] for m in C.MODEL_ORDER], fontsize=FS, color=C.INK)
axC.set_xticks([i + 0.5 for i in range(len(WORLDS))])
axC.set_xticklabels([("· " if cf else "▪ ") + w.replace("cf_", "").replace("_", " ")
                     for _tr, _t, w, cf in WORLDS], rotation=90, fontsize=6.8, color=C.INK2)
axC.tick_params(length=0)
for sp in axC.spines.values():
    sp.set_visible(False)
prev, start = None, 0
for i, (tr, *_x) in enumerate(WORLDS + [(None, None, None, None)]):
    if tr != prev:
        if prev is not None:
            axC.plot([start, i], [len(C.MODEL_ORDER) + 0.16] * 2, color=C.INK2, lw=1.0,
                     clip_on=False)
            axC.text((start + i) / 2, len(C.MODEL_ORDER) + 0.30, prev, ha="center", va="bottom",
                     fontsize=6.4, color=C.INK)
        prev, start = tr, i
# Keep this title SHORT. A left-aligned title extends right from the axes' left edge and does not wrap,
# so a long one overhangs the canvas and the tight bbox widens the emitted PDF -- which was this
# figure's whole width problem (5.66 in, 7.3 pt at column). The real/counterfactual key moved to the
# glyph row below.
axC.set_title("C   valid novelty per world, under the benchmark rubric", fontsize=8.0, color=C.INK,
              fontweight="bold", loc="left", pad=17)
# The key is drawn MANUALLY in axes coordinates rather than as a legend. A matplotlib legend sizes
# itself to its content and overhung the axes by 0.26 in on the right, which the tight bbox then added
# to the emitted width -- and because text does not scale with figsize, shrinking the figure only made
# the overhang grow to compensate. Placing the glyphs at fixed axes fractions removes the overhang.
# -0.48. The rotated world labels are the constraint and they are LONG ("tmprss15 essential"): -0.75
# and -0.60 left a dead band almost as tall as the matrix, but -0.36 ran the key straight through the
# labels. -0.48 clears the longest label with a small margin.
_ky = -0.48
for _i, (_lab, _fc, _ec, _mk) in enumerate(
        [(f"N={i}", NRAMP[i], C.GRID, "s") for i in (0, 1, 2, 3)]
        + [("abstained", "white", C.STATE_ABSTENTION, "s"), ("excluded", C.INK3, "none", "x")]):
    _x = (0.015, 0.115, 0.215, 0.315, 0.415, 0.585)[_i]   # explicit: "abstained" needs more room
    if _mk == "x":                                   # an unfilled marker takes no edgecolor
        axC.scatter([_x], [_ky], s=26, marker="x", color=C.INK3, linewidth=0.9,
                    transform=axC.transAxes, clip_on=False, zorder=5)
    else:
        axC.scatter([_x], [_ky], s=26, marker="s", facecolor=_fc, edgecolor=_ec, linewidth=0.7,
                    transform=axC.transAxes, clip_on=False, zorder=5)
    axC.text(_x + 0.022, _ky, _lab, transform=axC.transAxes, va="center", fontsize=6.4,
             color=C.INK2)
axC.text(0.775, _ky, "▪ real    · counterfactual", transform=axC.transAxes, va="center",
         fontsize=6.4, color=C.INK2)

rows_out = []
for m in C.MODEL_ORDER:
    p, n, nc, ne = HURDLE[m]
    rows_out.append({"panel": "B", "model": C.FULL[m], "world": "", "track": "",
                     "commit_rate": round(p, 4), "mean_novelty_given_commit": round(n, 3),
                     "yield": round(p * n, 3), "n_committed": nc, "n_eligible": ne, "novelty": ""})
for tr, t, w, cf in WORLDS:
    for m in C.MODEL_ORDER:
        r = by.get((t, w, m))
        st = ("excluded" if (t, w, m) in EXCLUDED else
              "abstained" if (r is None or r["novelty"] is None) else str(int(round(r["novelty"]))))
        rows_out.append({"panel": "C", "model": C.FULL[m], "world": w, "track": tr,
                         "commit_rate": "", "mean_novelty_given_commit": "", "yield": "",
                         "n_committed": "", "n_eligible": "", "novelty": st})
C.save(fig, "F06_prior_to_yield", rows_out,
       ["panel", "model", "track", "world", "commit_rate", "mean_novelty_given_commit", "yield",
        "n_committed", "n_eligible", "novelty"])
