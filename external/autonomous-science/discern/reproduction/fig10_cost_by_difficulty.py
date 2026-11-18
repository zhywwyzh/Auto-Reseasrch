"""Figure 10 -- inference cost across difficulty levels: does spend follow difficulty?

Modelled on NewtonBench Figure 4, "Inference cost among difficulty levels", and on its appendix
Tables 9-10 (average total tokens / tokens per round across difficulty levels).

The question is adaptive effort: a scientist spends longer on the hard problem. A model that spends the
same everywhere is not allocating effort, it is running a fixed procedure.

Difficulty is not assumed -- it is MEASURED from the benchmark itself: the track x level task categories
are ranked by across-model mean score and split into tertiles, so difficulty is defined by how every
model actually did, not by design intent.

L3 IS EXCLUDED, and that exclusion is the whole reason this figure is trustworthy. L1 and L2 share
max_steps=20; L3 runs at 3-6 steps and is structurally cheap. Including it put 4 of 8 "medium"
categories and only 1 "easy" category at L3, so the tertile spend differences measured LEVEL
COMPOSITION, not difficulty. Restricted to L1+L2 the 16 categories split 2/3 L1-L2 in the hard band,
3/3 in medium and 3/2 in easy -- balanced, so a spend difference can be read as a difficulty response.

Run: .venv_bench/bin/python fig09_cost_by_difficulty.py
"""
import collections
import statistics
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import fig_common as C

LEVELS = ["L1", "L2"]        # NOT L3 -- see the docstring; its step budget differs
BINS = ["hard", "medium", "easy"]
FILL = {"hard": "#B03A2E", "medium": "#E8A33D", "easy": "#1B6B50"}

lev = C.load("fig_data_levels.csv")
score = collections.defaultdict(dict)
for r in lev:
    if r["level"] in LEVELS and not r["family"]:
        score[(r["track_display"], r["level"])][r["model"]] = r["score_pct"]

cats = sorted(score, key=lambda k: statistics.mean(score[k].values()))
n, third = len(cats), len(cats) // 3
band = {c: ("hard" if i < third else "easy" if i >= n - third else "medium")
        for i, c in enumerate(cats)}

eff = C.load("efficiency_by_cell.csv")
DISPLAY = {"protein_ddg": "Protein", "enhancer_activity": "Enhancer", "bulk_rnaseq": "Bulk RNA",
           "cf_gwas": "GWAS", "clinvar_acmg": "ClinVar", "scrna": "scRNA",
           "hist_gene_exp": "Histone", "crispr_screen": "CRISPR"}
tok = collections.defaultdict(list)
for r in eff:
    key = (DISPLAY[r["track"]], r["level"])
    if key in band:
        tok[(r["model"], band[key])].append(r["median_tokens"])
med = {k: statistics.median(v) for k, v in tok.items() if v}

fig, ax = plt.subplots(figsize=(5.6, 3.0))
w = 0.26
for j, b in enumerate(BINS):
    xs = [i + (j - 1) * w for i in range(len(C.MODEL_ORDER))]
    ys = [med.get((m, b), 0) for m in C.MODEL_ORDER]
    ax.bar(xs, ys, w, color=FILL[b], edgecolor="white", linewidth=1.1, zorder=3,
           label=f"{b} third")

for i, m in enumerate(C.MODEL_ORDER):
    h, e = med.get((m, "hard")), med.get((m, "easy"))
    if h and e:
        ax.text(i, max(med.get((m, b), 0) for b in BINS) * 1.35, f"{h / e:.2f}×",
                ha="center", fontsize=7, color=C.INK, fontweight="bold")

ax.set_yscale("log"); ax.set_ylim(4000, 2_000_000)
ax.set_yticks([10000, 100000, 1000000])
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/1000:g}k"))
ax.set_xticks(range(len(C.MODEL_ORDER)))
ax.set_xticklabels([C.SHORT[m] for m in C.MODEL_ORDER], fontsize=7.5, color=C.INK)
ax.set_ylabel("Median bench tokens per task (log scale)")
ax.set_title("Only half the roster spends more on harder work", loc="left")
ax.legend(loc="upper right", ncol=3, handlelength=1.0, columnspacing=1.0, fontsize=7)
C.footnote(ax, "Difficulty is measured, not assumed: 16 L1/L2 track × level categories ranked by "
               "across-model mean score, split into tertiles.\nL3 is excluded — its 3–6 step budget "
               "against L1/L2's 20 would make this a level-composition artifact.\nAbove each model: "
               "hard ÷ easy median spend. A ratio near 1 means effort is not allocated to difficulty.",
           y=-0.30)
C.tidy(ax)

C.save(fig, "F10_cost_by_difficulty",
       [{"model": C.FULL[m], "difficulty_band": b, "median_tokens_per_task": med.get((m, b)),
         "n_categories": len([c for c in cats if band[c] == b])}
        for m in C.MODEL_ORDER for b in BINS] +
       [{"model": "", "difficulty_band": f"{k[0]} {k[1]}", "median_tokens_per_task": "",
         "n_categories": band[k]} for k in cats],
       ["model", "difficulty_band", "median_tokens_per_task", "n_categories"])
