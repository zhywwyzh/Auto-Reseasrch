"""Figure 9 -- task-type difficulty, hardest to easiest: which kinds of scientific work defeat everyone?

Modelled on BiomniBench Figure 4(a), "Mean rubric score by task type for the six configurations
(categories with at least 3 tasks, sorted hardest to easiest)", which reports two universally hard
categories -- GWAS-eQTL Analysis (best 65) and Pathway Enrichment (best 67).

This is the one cut our figure set did not have. Figure 3 ranks TRACKS, Figure 5 orders families by
conceptual workflow so the within-track contrast survives. Neither answers "which task types are hard
for EVERY model", because neither sorts by difficulty across the whole benchmark.

Result, the direct parallel to BiomniBench's two: **two categories are universally hard here, and both
are harder than anything in their set** -- Enhancer conservation (best model 17 of 100) and CRISPR
scoring (best 44). A ceiling that low is a property of the task, not of a model.

Categories = the 8 L1 QC task sets (one per track, 9-10 tasks each) + the 24 L2 analysis families
(4-6 tasks each). All clear the >=3-task floor. Scores are POST-adjudication, so this reconciles with
Figures 2 and 4.

Run: .venv_bench/bin/python fig08_task_difficulty.py
"""
import collections
import statistics
import matplotlib.pyplot as plt
import fig_common as C

FAM_LABEL = {"signal-eda": "signal EDA", "locus": "locus analysis", "twas": "TWAS",
             "prioritize": "prioritization", "classify": "classification", "sf": "secondary findings",
             "marker_de": "marker DE", "ddg_predict": "ddG prediction",
             "feature_effect": "feature effect", "stab_classify": "stability classification",
             "de": "differential expression", "gsea": "GSEA"}
HARD_CEILING = 50          # "universally hard" = even the BEST model stays below this

lev = C.load("fig_data_levels.csv")
cat = collections.defaultdict(dict)
for r in lev:
    if r["level"] == "L1":
        key = (r["track_display"], "QC / data integrity", "L1")
    elif r["level"] == "L2" and r["family"]:
        key = (r["track_display"], FAM_LABEL.get(r["family"], r["family"]), "L2")
    else:
        continue
    cat[key][r["model"]] = r["score_pct"]

rank = sorted(cat.items(), key=lambda kv: statistics.mean(kv[1].values()))

# ICLR text width is 5.5 in, SINGLE COLUMN (figure* does not widen anything). Labels and
# footnotes outside the axes are added on top of figsize by the tight bbox and do not scale
# with it, so author narrower than the target. Verified by check_figure_contract.py.
fig, ax = plt.subplots(figsize=(4.35, 7.4))
for i, (key, vals) in enumerate(rank):
    lo, hi = min(vals.values()), max(vals.values())
    ax.plot([lo, hi], [i, i], color=C.GRID, lw=1.1, zorder=2)
    for m in C.MODEL_ORDER:
        if m in vals:
            ax.scatter(vals[m], i, s=26, color=C.COLOR[m], zorder=4,
                       label=C.FULL[m] if i == 0 else None)
    ax.scatter(statistics.mean(vals.values()), i, marker="D", s=26, color="black", zorder=5,
               label="across-model mean" if i == 0 else None)
    if hi < HARD_CEILING:
        ax.text(hi + 2.5, i, f"best {hi:.0f}", fontsize=6.8, color="#B03A2E", va="center",
                fontweight="bold")

# The universally-hard categories are NOT adjacent in the ranking -- sorting is by MEAN, and a category
# can have a low mean with one model at ceiling (CRISPR context: mean 30, best 100). So each qualifying
# row is banded on its own; a contiguous band would have swept in a category that one model solves.
hard = [i for i, (_, v) in enumerate(rank) if max(v.values()) < HARD_CEILING]
for i in hard:
    ax.axhspan(i - 0.45, i + 0.45, color="#FBEDEA", zorder=0)
ax.text(99, hard[0] - 0.05, "universally hard: no model clears 50", fontsize=6.8, color="#B03A2E",
        ha="right", va="center", fontweight="bold")

ax.set_yticks(range(len(rank)))
ax.set_yticklabels([f"{k[0]} · {k[1]}" for k, _ in rank], fontsize=7, color=C.INK)
ax.set_ylim(len(rank) - 0.4, -0.7)
ax.set_xlim(0, 100); ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0", "25", "50", "75", "100%"])
ax.set_xlabel("Mean normalized score across that category's tasks")
ax.set_title("Two task types defeat every model", loc="left", pad=10)
ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.05), ncol=4, handlelength=1.0,
          columnspacing=1.2, fontsize=7)
C.footnote(ax, "32 task categories — 8 L1 QC sets (9–10 tasks each) and 24 L2 analysis families (4–6 "
               "each), all above the ≥3-task floor —\nsorted hardest to easiest by across-model mean. "
               "Grey line spans model min–max; it is a range, not an uncertainty interval.\n"
               "Post-adjudication scores, so this reconciles with Figures 2 and 4.", y=-0.10)
C.tidy(ax, axis="x")

C.save(fig, "F09_task_difficulty",
       [{"track": k[0], "category": k[1], "level": k[2], "model": C.FULL[m], "score_pct": v[m],
         "category_mean_pct": round(statistics.mean(v.values()), 2),
         "category_best_pct": max(v.values()),
         "universally_hard": max(v.values()) < HARD_CEILING}
        for k, v in rank for m in C.MODEL_ORDER if m in v],
       ["track", "category", "level", "model", "score_pct", "category_mean_pct",
        "category_best_pct", "universally_hard"])
