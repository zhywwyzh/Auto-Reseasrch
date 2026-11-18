"""F06 extended to EIGHT models: the discovery hurdle with glm-5.3 and gpt-6-astra.

WHY A SEPARATE BUILDER (same pattern as fig03_extended_landscape.py). fig_data_l3.csv is the FROZEN
six-model denominator every published six-model figure reads; the two later models live in
results/new_models/. This script merges them for the hurdle view and leaves F06_prior_to_yield.pdf
untouched.

WHY IT MATTERS. Panel B's claim is that commitment and conditional novelty DISSOCIATE. Among the frozen
six, GPT-5.6-sol was the low-commitment extreme at 18.2%. gpt-6-astra commits on 1 of 20 eligible worlds
-- 5.0%, less than a third of sol -- while the one hypothesis it does commit scores N=2. Its derived
yield is 0.10 against Claude's 1.00, a tenfold spread that the six-model figure cannot show. glm-5.3
sits mid-field (68.2%, E[N|commit] 1.20).

Panel A (evidence vs stated prior) reads data_vs_prior from the new models' graded_l3 files, since the
extension CSVs do not carry that column.

Run: .venv_bench/bin/python fig06_extended_prior_to_yield.py
"""
import collections
import csv
import json
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import fig_common as C

ROOT = Path(__file__).resolve().parent
NEW = ["glm-5.3", "gpt-6-astra"]
MODELS = [*C.MODEL_ORDER, *NEW]
SHORT = {**C.SHORT, "glm-5.3": "GLM-5.3", "gpt-6-astra": "GPT-6 Astra"}
COLOR = {**C.COLOR, "glm-5.3": "#7B4FA8", "gpt-6-astra": "#146B63"}
TRACKS = ["cf_gwas", "clinvar_acmg", "scrna", "hist_gene_exp",
          "bulk_rnaseq", "crispr_screen", "protein_ddg", "enhancer_activity"]
FS = 7.5
CATS = ["data", "mixed", "prior", "declined"]
LABEL = {"data": "moved to the data", "mixed": "partly retreated",
         "prior": "snapped back to the prior", "declined": "declined (neither)"}
FILL = {"data": "#1B6B50", "mixed": "#E8A33D", "prior": "#B03A2E", "declined": C.STATE_ABSTENTION}


def bucket(label):
    if not label:
        return None
    u = str(label).upper()
    return ("data" if u.startswith("TRUSTS-DATA") else "prior" if u.startswith("TRUSTS-PRIOR")
            else "mixed" if u.startswith("MIXED") else None)


# ---- frozen six, from the published figure table ----------------------------------------------------
l3_all = C.load("fig_data_l3.csv")
l3 = [r for r in l3_all if r["state"] != "CONFOUNDED-EXCLUDED"]
PRIOR = collections.defaultdict(collections.Counter)
HURDLE = {}
for m in C.MODEL_ORDER:
    for r in (x for x in l3 if x["model"] == m and x["is_counterfactual"]):
        b = bucket(r["data_vs_prior"])
        if b is None and str(r["state"]).startswith("ABSTAIN"):
            b = "declined"
        if b:
            PRIOR[m][b] += 1
    elig = [r for r in l3 if r["model"] == m]
    com = [r for r in elig if not str(r["state"]).startswith("ABSTAIN")]
    nov = [r["novelty"] for r in com if r["novelty"] is not None]
    HURDLE[m] = (len(com) / len(elig), statistics.mean(nov) if nov else 0.0, len(com), len(elig))

# ---- the two later models, from results/new_models/ -------------------------------------------------
for m in NEW:
    rows = list(csv.DictReader(open(ROOT / f"results/new_models/{m}_l3.csv")))
    elig = [r for r in rows if r["state"] != "CONFOUNDED-EXCLUDED"]
    com = [r for r in elig if not r["state"].startswith("ABSTAIN")]
    nov = [float(r["N"]) for r in com if r.get("N") not in (None, "")]
    HURDLE[m] = (len(com) / len(elig), statistics.mean(nov) if nov else 0.0, len(com), len(elig))
    for t in TRACKS:                                   # panel A needs data_vs_prior -> graded files
        for r in json.loads((ROOT / f"tracks/{t}/L3/results/l3_run/graded_l3_{m}.json").read_text()):
            if r.get("condition") != "counterfactual" or r.get("state") == "CONFOUNDED-EXCLUDED":
                continue
            b = bucket(r.get("data_vs_prior"))
            if b is None and str(r.get("state", "")).startswith("ABSTAIN"):
                b = "declined"
            if b:
                PRIOR[m][b] += 1

fig = plt.figure(figsize=(5.5, 2.75))
gs = fig.add_gridspec(1, 2, width_ratios=[1, 1], left=0.135, right=0.955, top=0.86, bottom=0.20,
                      wspace=0.34)

# ---- A: evidence vs stated prior --------------------------------------------------------------------
axA = fig.add_subplot(gs[0, 0])
for yi, m in enumerate(MODELS):
    y = len(MODELS) - 1 - yi
    tot = sum(PRIOR[m].values()) or 1
    x = 0.0
    for c in CATS:
        w = 100 * PRIOR[m][c] / tot
        if w:
            axA.barh(y, w, left=x, height=0.66, color=FILL[c], edgecolor="white", linewidth=0.6)
        x += w
axA.set_xlim(0, 100); axA.set_ylim(-0.6, len(MODELS) - 0.4)
axA.set_yticks(range(len(MODELS)))
axA.set_yticklabels([SHORT[m] for m in reversed(MODELS)], fontsize=6.8, color=C.INK)
axA.set_xticks([0, 50, 100]); axA.set_xticklabels(["0", "50", "100%"], fontsize=FS)
axA.tick_params(length=0)
for sp in ("top", "right", "left"):
    axA.spines[sp].set_visible(False)
axA.spines["bottom"].set_color(C.GRID)
axA.set_title("A   evidence vs. stated prior", fontsize=8.0, color=C.INK, fontweight="bold",
              loc="left", pad=6)
axA.legend(handles=[plt.Line2D([], [], marker="s", ls="", markersize=5, color=FILL[c],
                               label=LABEL[c]) for c in CATS],
           loc="upper left", bbox_to_anchor=(-0.02, -0.13), ncol=2, fontsize=6.0,
           handletextpad=0.4, columnspacing=0.9, borderpad=0, frameon=False)

# ---- B: the discovery hurdle ------------------------------------------------------------------------
axB = fig.add_subplot(gs[0, 1])
gx, gy = np.meshgrid(np.linspace(0.02, 1.0, 200), np.linspace(0.02, 1.6, 200))
cs = axB.contour(gx, gy, gx * gy, levels=[0.25, 0.5, 0.75, 1.0], colors=C.GRID, linewidths=0.7)
_CLAB = {0.25: 0.92, 0.5: 0.333, 0.75: 0.5, 1.0: 0.667}
axB.clabel(cs, fmt=lambda v: f"{v:g}", fontsize=6.2, colors=C.INK3, inline_spacing=2,
           manual=[(x, lv / x) for lv, x in _CLAB.items()])
# astra sits at (0.05, 2.0) -- ABOVE the frozen y-limit of 1.6, because its single committed
# hypothesis scored N=2. The axis is raised to 2.15 so the point is inside the canvas, and its label
# goes to the RIGHT: there is nothing plotted along the left edge above y=1.6.
OFF = {"claude-opus-5": ((9, 4), "left"), "kimi-k3": ((-9, 1), "right"),
       "glm-5.2": ((-9, 1), "right"), "deepseek-v4-pro": ((-9, 1), "right"),
       "gpt-4.1": ((9, -1), "left"), "gpt-5.6-sol": ((0, -13), "center"),
       # glm-5.3 (0.68, 1.20) sits just left of Kimi (0.76, 0.94); a centred label below ran straight
       # through Kimi's dot, so it goes ABOVE-LEFT where the 0.75 contour leaves a gap.
       "glm-5.3": ((-8, 7), "right"), "gpt-6-astra": ((10, 0), "left")}
for m in MODELS:
    p, n, *_ = HURDLE[m]
    new = m in NEW
    axB.scatter([p], [n], s=46 if new else 42, color=COLOR[m], edgecolor="white",
                linewidth=0.9 if new else 0.8, zorder=4 if new else 3,
                marker="D" if new else "o")
    xy, ha = OFF[m]
    axB.annotate(SHORT[m], (p, n), textcoords="offset points", xytext=xy, ha=ha, va="center",
                 fontsize=6.8, color=C.INK)
axB.set_xlim(0, 1.0); axB.set_ylim(0, 2.15)
axB.set_xticks([0, 0.25, 0.5, 0.75, 1.0]); axB.set_xticklabels(["0", "", "50", "", "100%"], fontsize=FS)
axB.set_yticks([0, 0.5, 1.0, 1.5, 2.0]); axB.tick_params(length=0, labelsize=FS)
axB.set_xlabel("worlds with a committed hypothesis", fontsize=7.5, color=C.INK2, labelpad=1)
axB.set_ylabel("mean novelty | committed", fontsize=7.5, color=C.INK2, labelpad=1)
for sp in ("top", "right"):
    axB.spines[sp].set_visible(False)
axB.spines["left"].set_color(C.GRID); axB.spines["bottom"].set_color(C.GRID)
axB.set_axisbelow(True)
axB.set_title("B   the discovery hurdle", fontsize=8.0, color=C.INK, fontweight="bold", loc="left",
              pad=6)
# Both notes were at the bottom and printed over each other. The contour note moves to the upper-left
# band (y 1.55-1.75), empty now that astra's label runs right from x=0.05 at y=2.0; the roster note is
# shortened and kept bottom-right, where the 0.25 contour has already left the axes.
# The upper-left band is where clabel() puts "0.5" and "0.75" (both land at y=1.5 under _CLAB), so the
# note goes to the bottom-left quadrant instead: nothing is plotted below y=0.45 left of x=0.5.
axB.text(0.02, 0.40, "contours = yield\nP(commit) × E[N|commit]", ha="left", va="top", fontsize=6.2,
         color=C.INK3, linespacing=1.35)
axB.text(0.985, 0.03, "◆ post-freeze", ha="right", va="bottom", fontsize=6.0,
         color=C.INK3, transform=axB.transAxes)

C.save(fig, "F06_prior_to_yield_8models",
       [{"model": m, "p_commit": round(HURDLE[m][0], 4), "mean_novelty_given_commit": round(HURDLE[m][1], 3),
         "n_committed": HURDLE[m][2], "n_eligible": HURDLE[m][3],
         "derived_yield": round(HURDLE[m][0] * HURDLE[m][1], 3),
         "frozen_roster": m not in NEW,
         **{f"prior_{c}": PRIOR[m][c] for c in CATS}} for m in MODELS],
       ["model", "p_commit", "mean_novelty_given_commit", "n_committed", "n_eligible",
        "derived_yield", "frozen_roster", *[f"prior_{c}" for c in CATS]])
