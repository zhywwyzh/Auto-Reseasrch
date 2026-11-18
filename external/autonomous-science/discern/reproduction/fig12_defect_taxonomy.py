"""Figure 12 -- coverage of the data-integrity taxonomy: 65 distinct defect classes, 8 substrates.

Modelled on BixBench Figure 2, "Histogram of counts for capsules in a broad set of self-selected
categories. BixBench covers a wide array of analysis types." Their figure establishes breadth before any
score is shown; this is the same argument for the axis DISCERN actually claims -- not breadth of
analysis type (T01 covers that) but breadth of DATA DEFECT.

The number worth stating: the 71 injected L1 tasks carry **65 distinct defect classes**, and only three
of them recur across more than one track. This is not one defect re-skinned eight ways.

Classes are grouped into families by a documented keyword rule over the world name, listed in FAMILIES
below and applied in order. The rule is transparent rather than clever: a reader can check any
assignment against the world name in the companion CSV, which lists every class individually.

Run: .venv_bench/bin/python fig11_defect_taxonomy.py
"""
import collections
import re
import matplotlib.pyplot as plt
import fig_common as C

# first match wins; the order encodes precedence, not importance
FAMILIES = [
    ("abstention-warranted", r"abstain"),
    ("reference / coordinate", r"reference|liftover|build|coordinate|strand|assembly|numbering|"
                              r"seqlen|palindromic|allele|id_version|multi_model"),
    ("contamination / carry-over", r"contamination|globin|hemoglobin|ambient|rrna|gdna|mito|"
                                   r"blacklist|heteroatom|index_hopping"),
    ("sample / metadata integrity", r"metadata|mislabel|sex_swap|misannotation|duplicate|duplication|"
                                    r"sample|feature_type"),
    ("batch / technical artefact", r"batch|jackpot|library|skew|discordance|degradation|depletion|"
                                   r"complexity|doublet|empty_droplet"),
    ("distributional / outlier", r"outlier|scale|impossible|sign_swap|bias|low_coverage|low_count|"
                                 r"low_signal|unit_error"),
    ("structure integrity", r"missing_atoms|missing_hydrogens|steric|altloc|non_standard|"
                            r"missing_input|control_guide"),
]
FILL = {"abstention-warranted": C.STATE_ABSTENTION, "reference / coordinate": "#20618F",
        "contamination / carry-over": "#5E94C4", "sample / metadata integrity": "#8AB4D6",
        "batch / technical artefact": "#E8A33D", "distributional / outlier": "#E07B5A",
        "structure integrity": "#1B6B50", "other": "#9B9B9B"}
TRACK_ORDER = ["GWAS", "ClinVar", "scRNA", "CRISPR", "Enhancer", "Histone", "Protein", "Bulk RNA"]


def family(world):
    for name, pat in FAMILIES:
        if re.search(pat, world):
            return name
    return "other"


rows = C.load("fig_data_l1.csv")
n_models = len(C.MODEL_ORDER)
seen = {}
for r in rows:
    if r["world"] == "clean":
        continue
    seen[(r["track_display"], r["world"])] = family(r["world"])

cnt = collections.Counter(seen.values())
by_track = collections.Counter((f, t) for (t, _w), f in seen.items())
order = [f for f, _ in FAMILIES] + (["other"] if cnt["other"] else [])
order = [f for f in order if cnt[f]]

# ICLR text width is 5.5 in, SINGLE COLUMN (figure* does not widen anything). Labels and
# footnotes outside the axes are added on top of figsize by the tight bbox and do not scale
# with it, so author narrower than the target. Verified by check_figure_contract.py.
fig, ax = plt.subplots(figsize=(4.28, 3.0))
for i, f in enumerate(order):
    left = 0
    for t in TRACK_ORDER:
        v = by_track[(f, t)]
        if not v:
            continue
        ax.barh(i, v, left=left, height=0.62, color=FILL[f], edgecolor="white", linewidth=1.2,
                alpha=0.45 + 0.55 * (TRACK_ORDER.index(t) % 2), zorder=3)
        left += v
    ax.text(left + 0.35, i, f"{cnt[f]}", va="center", fontsize=7.2, color=C.INK, fontweight="bold")
    ax.text(left + 1.6, i, f"{len({t for (t, _w), ff in seen.items() if ff == f})} tracks",
            va="center", fontsize=6.6, color=C.INK3)

ax.set_yticks(range(len(order)))
ax.set_yticklabels(order, fontsize=7.5, color=C.INK)
ax.invert_yaxis()
ax.set_xlim(0, 26)
ax.set_xticks([0, 5, 10, 15, 20])
ax.set_xlabel("Injected L1 tasks (one per track × defect class)")
C.title(ax, "65 distinct defect classes, only three shared across tracks")      # wraps to the figure width; a raw left title does not
C.footnote(ax, "One bar segment per track, alternating shade within a family; at the right, the "
               "family total in tasks and how many of the\neight substrates contribute to it. "
               "71 injected tasks carry 65 distinct class names — only three recur across tracks.\n"
               "Families come from a documented first-match keyword rule over the world name; every "
               "individual class is listed in the\ncompanion CSV, so any assignment can be checked.",
           y=-0.30)
C.tidy(ax, axis="x")

C.save(fig, "F12_defect_taxonomy",
       sorted([{"track": t, "defect_class": w, "family": f, "n_tasks_per_model": 1}
               for (t, w), f in seen.items()], key=lambda r: (r["family"], r["track"])),
       ["track", "defect_class", "family", "n_tasks_per_model"])
