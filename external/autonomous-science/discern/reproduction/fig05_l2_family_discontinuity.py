"""Figure 5 -- L2 analysis-family discontinuity (Cleveland dot plot over all 24 families).

Spec: FIGURES_2_5_PLAN.md "Figure 4". Claim: there is no single general "tool-use ability". Within one
track and one scientific domain, models can be near-ceiling on one analysis and near-floor on another.

SOURCE: results/fig_data_l2.csv, aggregated per family from the L2 META-REVIEW LEDGER (post-adjudication
per-world scores). It previously read the `<track> L2 <family>` entries of fig_data_levels.csv, which are
the LEGACY family means and were never updated by the meta-review -- so after the 2026-08-26 L2 migration
this figure would have contradicted Figure 3 and Table 2. Aggregating the ledger reproduces the canonical
per-track L2 to <=0.0001, so all three now agree by construction.

Tracks are ordered by conceptual workflow, NOT by score, and families are never globally sorted by
outcome -- the within-track contrast is the scientific point, and sorting globally would destroy it.

Run: .venv_bench/bin/python fig04_l2_family_discontinuity.py
"""
import collections
import matplotlib.pyplot as plt
import fig_common as C

TRACK_SEQ = ["cf_gwas", "clinvar_acmg", "scrna", "crispr_screen", "enhancer_activity",
             "hist_gene_exp", "protein_ddg", "bulk_rnaseq"]
FAM_LABEL = {"signal-eda": "signal EDA", "locus": "locus analysis", "twas": "TWAS",
             "prioritize": "prioritization", "classify": "classification", "sf": "secondary findings",
             "annotation": "annotation", "marker_de": "marker DE", "composition": "composition",
             "scoring": "scoring", "calling": "calling", "context": "context",
             "divergence": "divergence", "conservation": "conservation", "ranking": "ranking",
             "quantify": "quantify", "regression": "regression", "de": "differential expression",
             "gsea": "GSEA", "structure": "structure", "ddg_predict": "ddG prediction",
             "feature_effect": "feature effect", "stab_classify": "stability classification"}

_cells = collections.defaultdict(list)
for r in C.load("fig_data_l2.csv"):
    _cells[(r["track"], r["family"], r["model"])].append(r["score"])
val = collections.defaultdict(dict)
for (tr, fam, m), v in _cells.items():
    val[(tr, fam)][m] = round(100 * (sum(v) / len(v)) / 3, 2)

# Issue-design glyph from the structured tags; '·' where a track carries no per-task issue_type field.
tags = collections.defaultdict(set)
for r in C.load("fig_data_l2.csv"):
    if r.get("issue_type") and r["issue_type"] != "none":
        tags[(r["track"], r["family"])].add(r["issue_type"])
GLYPH = {"data-confound": "D", "tool-trap": "T", "statistical": "S"}

TRACK_NAME = {"cf_gwas": "GWAS", "clinvar_acmg": "ClinVar", "scrna": "scRNA",
              "crispr_screen": "CRISPR", "enhancer_activity": "Enhancer",
              "hist_gene_exp": "Histone", "protein_ddg": "Protein",
              "bulk_rnaseq": "Bulk RNA"}

rows = []
for t in TRACK_SEQ:
    for (tr, fam) in [k for k in val if k[0] == t]:
        rows.append((tr, fam))
rows.sort(key=lambda k: (TRACK_SEQ.index(k[0]), k[1]))

# 5.95, not 6.8: the emitted PDF ran to 8.11 in -- past even a two-column span -- because the family
# labels, the "mean vs mean" annotations at x=104.5 and the track group labels all sit OUTSIDE the axes
# and the tight bbox adds them on top of the figure size. At 8.11 in LaTeX scales the float down to the
# ICLR is SINGLE-COLUMN, \textwidth 5.5 in, and `figure*` does not widen anything -- so this float has
# to fit 5.5 in like every other one. It used to emit 7.21 in and would have been scaled to 77%, taking
# its 7.5 pt family names down to 5.7 pt. Shrinking figsize did NOT help: the track names were drawn at
# x=-31 in DATA coordinates on a 0-100 axis, i.e. a margin 31% as wide as the plot itself, and text
# outside the axes does not scale with the figure. Moving them INSIDE the axes is what actually fixed
# the width.
fig, ax = plt.subplots(figsize=(5.02, 6.6))
ypos, ylabels, seps = [], [], []
y = 0
for i, (tr, fam) in enumerate(rows):
    if i and rows[i - 1][0] != tr:
        seps.append(y - 0.5)
        y += 0.9
    vals = val[(tr, fam)]
    for m in C.MODEL_ORDER:
        if m in vals:
            ax.scatter(vals[m], y, s=26, color=C.COLOR[m], zorder=4,
                       label=C.FULL[m] if i == 0 else None)
    mean = sum(vals.values()) / len(vals)
    ax.plot([min(vals.values()), max(vals.values())], [y, y], color=C.GRID, lw=1.0, zorder=2)
    ax.scatter(mean, y, marker="D", s=26, color="black", zorder=5,
               label="across-model mean" if i == 0 else None)
    g = "".join(sorted(GLYPH[x] for x in tags[(tr, fam)])) or "·"
    ax.text(100.8, y, g, fontsize=6.6, color=C.INK3, va="center", ha="left")
    ypos.append(y); ylabels.append(FAM_LABEL.get(fam, fam)); y += 1

for i, (tr, fam) in enumerate(rows):
    if i == 0 or rows[i - 1][0] != tr:
        # INSIDE the axes, on the separator row. Drawn at x=-31 this label created a left margin 31%
        # as wide as the plot and pushed the emitted PDF past the 5.5 in text width.
        ax.text(1.0, ypos[i] - 0.80, TRACK_NAME[tr], fontsize=7.8, color=C.INK,
                fontweight="bold", va="center", ha="left")
for s in seps:
    ax.axhline(s, color=C.GRID, lw=0.7)

# The three within-track contrasts the plan requires, computed rather than hard-coded.
for (tr, a, b) in [("clinvar_acmg", "prioritize", "sf"), ("enhancer_activity", "ranking",
                                                          "conservation"),
                   ("cf_gwas", "locus", "twas")]:
    ia, ib = rows.index((tr, a)), rows.index((tr, b))
    ma = sum(val[(tr, a)].values()) / len(val[(tr, a)])
    mb = sum(val[(tr, b)].values()) / len(val[(tr, b)])
    ya, yb = ypos[ia], ypos[ib]
    # INSIDE the axes. These brackets used to be drawn at x=112..115 on a 0-100 axis with
    # clip_on=False, i.e. a right margin 15% as wide as the plot, and they were the single largest
    # contributor to this float exceeding the 5.5 in text width. The highest plotted value is 91.7%,
    # so x=99.5 is clear of every dot.
    # A plotted value reaches 100.0, so the bracket cannot go inside the axes. Kept just outside and
    # the label ROTATED: rotated text is only as wide as its cap height, so the right overhang is ~0.3
    # in instead of the ~1.1 in the old horizontal label at x=115 produced.
    x = 102.0
    ax.plot([x, x + 1.4, x + 1.4, x], [ya, ya, yb, yb], color=C.INK3, lw=0.8, clip_on=False)
    ax.text(x + 3.6, (ya + yb) / 2, f"{ma:.0f} vs {mb:.0f}", fontsize=6.6, color=C.INK2,
            va="center", ha="center", rotation=90, clip_on=False)

ax.set_yticks(ypos); ax.set_yticklabels(ylabels, fontsize=7.5, color=C.INK)          # family names identify the rows
ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_ylim(y - 0.4, -1.4)
ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(["0", "25", "50", "75", "100%"])
ax.set_xlabel("Mean normalized L2 score")
# Two lines, hard-wrapped. A loc="left" title extends right from the axes and never wraps, so this one
# ran 0.89 in past the figure and was the single largest contributor to the emitted width. "scientific
# analysis tracks" is also the vocabulary the rest of the paper uses; "domains" was ours alone.
ax.set_title("Analytical competence is discontinuous\nwithin scientific analysis tracks", loc="left",
             pad=8, linespacing=1.35)
ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.055), ncol=4, handlelength=1.0,
          columnspacing=1.2, fontsize=7)
# Hard-wrapped to ~62 characters. C.footnote does not wrap, and at 6.8 pt a 110-character line ran
# ~1.2 in past the axes -- text outside the axes does not shrink with figsize, so this, not the plot,
# was setting the emitted width.
C.footnote(ax, "24 analysis families, eight tracks, six models. Tracks in\n"
               "conceptual workflow order; families never sorted by score.\n"
               "Glyphs: D data confound · T tool/procedure trap · S statistical\n"
               "trap · '·' no per-task issue tag in that track's schema.\n"
               "Grey line spans the model min–max: a range, not an interval.",
           y=-0.145)   # clears the legend, which now wraps to two rows in a 4.4 in figure
C.tidy(ax, axis="x")

C.save(fig, "F05_l2_family_discontinuity",
       [{"track": tr, "family": fam, "model": C.FULL[m], "score_pct": val[(tr, fam)][m],
         "family_mean_pct": round(sum(val[(tr, fam)].values()) / len(val[(tr, fam)]), 2),
         "issue_glyph": "".join(sorted(GLYPH[x] for x in tags[(tr, fam)])) or "."}
        for (tr, fam) in rows for m in C.MODEL_ORDER if m in val[(tr, fam)]],
       ["track", "family", "model", "score_pct", "family_mean_pct", "issue_glyph"])
