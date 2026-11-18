"""Figure 4A -- calibration under three kinds of pressure, as paired dumbbells.

REPLACES the retired F04A (L1 clean-vs-injected), F06A (L2 confound-vs-trap) and F08A (L3
real-vs-counterfactual), which each showed ONE stage's contrast in its own float. The comparison a
reader wants is ACROSS stages -- does a model that over-diagnoses clean data also over-trust a tool
default? -- and that needs the three contrasts on one row per model.

MODELLED ON BIOMNIBENCH FIGURE 4 (one grid, several evaluation conditions) and DISCOVERYWORLD TABLE 4
(an agent is never reduced to one number).

DUMBBELLS, NOT TILES. An earlier build drew value tiles plus a signed delta column. It was 4.5 in tall
and the delta labels crowded their cells. A dumbbell puts the CONTRAST in the geometry -- the gap
between dots IS the delta -- so the numbers do not have to be printed, and the panel drops to ~2.6 in.

WHY THESE CONTRASTS. Each stage has one contrast that isolates CALIBRATION rather than ability, with
both sides matched in difficulty and opposed in direction:

  L1  clean vs injected                    is the defect real? Scoring on both means being right twice
                                           in opposite directions.
  L2  data confound / tool-or-procedure-    must the INPUT be verified, or the OUTPUT of what you ran?
      output trap / statistical trap        The L2_DESIGN section 1 taxonomy, tagged benchmark-wide on
                                           2026-08-27 (36 / 34 / 8 worlds over all 8 tracks; before
                                           then only the graded records were read and this panel could
                                           not be drawn).
  L3  real vs counterfactual                does the evidence agree with the prior, or overturn it?

ALL THREE L2 CLASSES ARE SHOWN, including statistical traps at n=8. They are the HARDEST class for four
of six models -- DeepSeek falls to 0.703 there against 2.000 on data confounds -- so collapsing them into
the other two would hide the sharpest L2 result in the benchmark to save one dot.

THE CATEGORY LABEL IS "tool / procedure-output trap", not "tool trap". ClinVar's incomplete ranking and
reporting rules (phenotype_mismatch, inheritance_mismatch, out_of_scope, vus_overreport) belong here:
the data is correct and the agent had to distrust its own PROCEDURE. They are not statistical
properties, and adding a fourth class for them would weaken the input-vs-output construct that the
whole taxonomy rests on.

NO GOOD/BAD HUE ANYWHERE. Only L1 has an a-priori-correct direction (a clean control should not score
below an injected one). Dots take their stage's hue, light to dark in the order the conditions are
listed; the connecting line is neutral. Encoding a preference on L2 or L3 would be editorialising, and
the contract already forbids model colours standing in for states.

SOURCES. L1 from fig_data_l1.csv (per-world; the clean/injected split is unaffected by adjudication).
L2 from fig_data_l2.csv `score`, which since the 2026-08-27 migration is the meta score the canonical
L2 column derives from, so this panel aggregates to Table 2. L3 from fig_data_l3.csv `composite`, with
BOTH gate exclusions removed -- one carries a CONFOUNDED-EXCLUDED state, the other is simply absent, so
neither filter alone is correct.

AUTHORED AT FINAL SIZE: 5.5 in wide, every glyph >= 7.5 pt.

Caption draft, kept here so figure and caption stay in sync:

    Figure 4A: Calibration under three kinds of pressure. Each stage contributes contrasts whose sides
    are matched in difficulty and opposed in direction, so a model can only score well on all of them
    by being right in both directions. Dots are mean score on 0-3; the gap between them is the effect.
    Dot shade orders the conditions within a stage and carries no good/bad meaning, because only L1 has
    an a-priori-correct direction -- yet every model scores HIGHER on defective data than on clean
    data. L2's three classes are the benchmark-wide issue taxonomy (n=36 data confounds, 34
    tool/procedure-output traps, 8 statistical traps); statistical traps are the hardest class for four
    of six models. L3 omits the two gate-excluded cells rather than scoring them zero.

Run: .venv_bench/bin/python fig04A_stage_pressure.py
"""
import statistics
import matplotlib.pyplot as plt
import fig_common as C

FIG_W, FIG_H = 5.5, 3.05
SHADES = {"L1": ["#AFCCE4", "#255E92"],
          "L2": ["#F5D9AE", "#DFA24A", "#8A5A0C"],
          "L3": ["#AAD5BC", "#2A7A50"]}
FS = 7.5

l1 = C.load("fig_data_l1.csv")
l2 = C.load("fig_data_l2.csv")
l3 = C.load("fig_data_l3.csv")
# Both gate exclusions: one is a state label, the other a missing row. Filtering the state alone leaves
# Claude's denominator wrong; counting rows alone leaves Kimi's wrong.
l3 = [r for r in l3 if r["state"] != "CONFOUNDED-EXCLUDED"]

PANELS = [
    ("L1", [("clean", lambda m: [r["score"] for r in l1
                                 if r["model"] == m and r["is_clean"] and r["score"] is not None]),
            ("injected", lambda m: [r["score"] for r in l1
                                    if r["model"] == m and not r["is_clean"]
                                    and r["score"] is not None])]),
    ("L2", [("data confound", lambda m: [r["score"] for r in l2 if r["model"] == m
                                         and r["issue_type"] == "data-confound"]),
            ("tool / procedure", lambda m: [r["score"] for r in l2 if r["model"] == m
                                                   and r["issue_type"] == "tool-trap"]),
            ("statistical", lambda m: [r["score"] for r in l2 if r["model"] == m
                                       and r["issue_type"] == "statistical"])]),
    ("L3", [("real", lambda m: [r["composite"] for r in l3 if r["model"] == m
                                and not r["is_counterfactual"] and r["composite"] is not None]),
            ("counterfactual", lambda m: [r["composite"] for r in l3 if r["model"] == m
                                          and r["is_counterfactual"] and r["composite"] is not None])]),
]

fig, axes = plt.subplots(1, 3, figsize=(FIG_W, FIG_H),
                         gridspec_kw={"width_ratios": [1, 1, 1], "wspace": 0.10,
                                      "left": 0.135, "right": 0.995, "top": 0.905, "bottom": 0.155})
rows_out = []
for ax, (stage, conds) in zip(axes, PANELS):
    ns = []
    for ci, (lab, fn) in enumerate(conds):
        ns.append(max(len(fn(m)) for m in C.MODEL_ORDER))
    for yi, m in enumerate(C.MODEL_ORDER):
        y = len(C.MODEL_ORDER) - 1 - yi
        vals = []
        for ci, (lab, fn) in enumerate(conds):
            v = fn(m)
            vals.append(statistics.mean(v) if v else None)
            if v:
                rows_out.append({"stage": stage, "model": C.FULL[m], "condition": lab,
                                 "mean_score": round(statistics.mean(v), 3), "n": len(v)})
        got = [v for v in vals if v is not None]
        if len(got) > 1:
            ax.plot([min(got), max(got)], [y, y], color=C.GRID, lw=1.6, zorder=1,
                    solid_capstyle="round")
        for ci, v in enumerate(vals):
            if v is None:
                continue
            ax.scatter([v], [y], s=30, facecolor=SHADES[stage][ci], edgecolor="white", linewidth=0.7,
                       zorder=3)
    # Headroom for the condition key. The model rows occupy y=0..5, so the key must live above y=5.5 or
    # it prints straight through the top row -- which is what an earlier build did to GPT-4.1.
    ax.set_xlim(0, 3); ax.set_ylim(-0.75, len(C.MODEL_ORDER) + 2.5)
    ax.set_xticks([0, 1, 2, 3]); ax.tick_params(length=0, labelsize=FS)
    ax.set_yticks([])
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(C.GRID)
    ax.set_axisbelow(True); ax.grid(True, axis="x", alpha=0.85)
    ax.set_title(stage, fontsize=8.2, color=C.INK, fontweight="bold", pad=4)
    # condition key inside the panel: the dot, its label and its denominator
    for ci, ((lab, _fn), n) in enumerate(zip(conds, ns)):
        yk = len(C.MODEL_ORDER) + 2.05 - ci * 0.62
        ax.scatter([0.075], [yk], s=26, facecolor=SHADES[stage][ci], edgecolor="white",
                   linewidth=0.6, clip_on=False, zorder=4)
        ax.text(0.24, yk, f"{lab}  n={n}", va="center", fontsize=7.2, color=C.INK2)

for yi, m in enumerate(C.MODEL_ORDER):
    axes[0].text(-0.11, len(C.MODEL_ORDER) - 1 - yi, C.SHORT[m], transform=axes[0].get_yaxis_transform(),
                 ha="right", va="center", fontsize=FS, color=C.INK)
axes[1].set_xlabel("mean score (0–3)", fontsize=FS, color=C.INK2, labelpad=2)
# Panel letter: 4A and 4B are stacked as one float, so each half needs to announce itself.
fig.text(0.004, 0.985, "A.  Calibration pressure", fontsize=8.6, fontweight="bold", color=C.INK,
         va="top")

C.save(fig, "F04A_stage_pressure", rows_out, ["stage", "model", "condition", "mean_score", "n"])
