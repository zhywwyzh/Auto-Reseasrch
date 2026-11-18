"""Figure 4B -- clean-control specificity: what models do with data that has nothing wrong with it.

Spec: FIGURES_2_5_PLAN.md "Figure 3 / Panel B". Claim: only 16 of 48 clean controls are accepted
correctly; the rest are judged over-cautiously or declared falsely unusable. Inventing a defect on clean
data is a failure of scientific judgment, not an excess of rigor.

Raw fractions are printed rather than percentages: each model sees exactly EIGHT clean worlds, and n=8
percentages look more precise than they are.

Categories are ordinal (desirable -> severe), so they take the ordered outcome ramp with abstention's
reserved purple untouched -- not three arbitrary categorical hues.

Run: .venv_bench/bin/python fig03B_clean_outcomes.py
"""
import collections
import matplotlib.pyplot as plt
import fig_common as C

ORDER = ["CLEAN-CORRECT", "OVER-CAUTIOUS", "FALSE-UNUSABLE"]
LABEL = {"CLEAN-CORRECT": "clean-correct", "OVER-CAUTIOUS": "over-cautious",
         "FALSE-UNUSABLE": "false-unusable"}

rows = [r for r in C.load("fig_data_l1.csv") if r["is_clean"]]
cnt = collections.Counter((r["model"], r["state"]) for r in rows)
n = {m: sum(cnt[(m, s)] for s in ORDER) for m in C.MODEL_ORDER}
tot = collections.Counter(r["state"] for r in rows)
N = sum(tot.values())

bars = [(C.SHORT[m], [cnt[(m, s)] for s in ORDER], n[m]) for m in C.MODEL_ORDER]
bars.append(("all models", [tot[s] for s in ORDER], N))

fig, ax = plt.subplots(figsize=(4.6, 2.7))
for i, (name, vals, denom) in enumerate(bars):
    left = 0.0
    for s, v in zip(ORDER, vals):
        w = 100 * v / denom
        ax.barh(i, w, left=left, height=0.62, color=C.OUTCOME[s], edgecolor="white", linewidth=1.3,
                zorder=3, label=LABEL[s] if i == 0 else None)
        if w > 9:
            ax.text(left + w / 2, i, f"{v}/{denom}", ha="center", va="center", fontsize=7,
                    color="white" if s != "OVER-CAUTIOUS" else C.INK)
        left += w

ax.set_yticks(range(len(bars)))
ax.set_yticklabels([b[0] for b in bars], fontsize=7.5, color=C.INK)
ax.get_yticklabels()[-1].set_fontweight("bold")
ax.axhline(len(bars) - 1.5, color=C.GRID, lw=0.8)
ax.invert_yaxis()
ax.set_xlim(0, 100)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0", "25", "50", "75", "100%"])
ax.set_xlabel("Share of that model's eight clean control worlds")
ax.set_title("Only 16 of 48 clean controls are accepted correctly", loc="left")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=3, handlelength=1.0,
          columnspacing=1.4)
C.footnote(ax, "Eight clean worlds per model, one per track. Raw fractions, not percentages: n = 8\n"
               "per row. State labels are unaffected by score adjudication.", y=-0.52)
C.tidy(ax, axis="x")

C.save(fig, "F04B_clean_outcomes",
       [{"model": name, "n_clean_worlds": denom,
         **{LABEL[s]: v for s, v in zip(ORDER, vals)}} for name, vals, denom in bars],
       ["model", "n_clean_worlds"] + [LABEL[s] for s in ORDER])
