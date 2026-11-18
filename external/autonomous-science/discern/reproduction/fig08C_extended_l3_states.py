"""F08C extended to EIGHT models: typed abstention, with glm-5.3 and gpt-6-astra.

WHY A SEPARATE BUILDER (same pattern as fig03_extended_landscape.py / fig06_extended_prior_to_yield.py).
fig_data_l3.csv is the FROZEN six-model denominator; the two later models live in results/new_models/.
F08C_l3_states.pdf is left untouched.

WHY IT MATTERS. The panel's claim is that abstention is not ONE behaviour. gpt-6-astra makes that point
more sharply than any frozen model: 19 of its 20 eligible worlds are abstentions, and they are
overwhelmingly CALIBRATED_HOLD (14) rather than bare INSUFFICIENT (4) -- i.e. it declines while naming
the conflict, a scientific act, on nearly every world. glm-5.3 sits mid-field (7/22 abstentions).
Read with F06's hurdle panel, astra is the extreme case of high abstention quality at near-zero yield.

Run: .venv_bench/bin/python fig08C_extended_l3_states.py
"""
import collections
import csv
from pathlib import Path

import matplotlib.pyplot as plt

import fig_common as C

ROOT = Path(__file__).resolve().parent
NEW = ["glm-5.3", "gpt-6-astra"]
MODELS = [*C.MODEL_ORDER, *NEW]
SHORT = {**C.SHORT, "glm-5.3": "GLM-5.3", "gpt-6-astra": "GPT-6 Astra"}
FULL = {**C.FULL, "glm-5.3": "GLM-5.3", "gpt-6-astra": "GPT-6 Astra"}

ORDER = ["STRONG", "SOLID", "WEAK", "POOR", "ABSTAIN-CALIBRATED_HOLD", "ABSTAIN-ARTIFACT",
         "ABSTAIN-INSUFFICIENT", "CONFOUNDED-EXCLUDED"]
LABEL = {"STRONG": "strong", "SOLID": "solid", "WEAK": "weak", "POOR": "poor",
         "ABSTAIN-CALIBRATED_HOLD": "abstain: calibrated hold",
         "ABSTAIN-ARTIFACT": "abstain: artifact called",
         "ABSTAIN-INSUFFICIENT": "abstain: insufficient",
         "CONFOUNDED-EXCLUDED": "excluded (prior eligibility)"}
FILL = {"STRONG": "#1B6B50", "SOLID": "#4E9C7D", "WEAK": "#93C4AC", "POOR": "#E07B5A",
        "ABSTAIN-CALIBRATED_HOLD": C.STATE_ABSTENTION, "ABSTAIN-ARTIFACT": "#A97FD0",
        "ABSTAIN-INSUFFICIENT": "#D9C6EB", "CONFOUNDED-EXCLUDED": "#9B9B9B"}

cnt = collections.Counter((r["model"], r["state"]) for r in C.load("fig_data_l3.csv"))
for m in NEW:                                     # the later models, from their own extension table
    for r in csv.DictReader(open(ROOT / f"results/new_models/{m}_l3.csv")):
        cnt[(m, r["state"])] += 1
n = {m: sum(cnt[(m, s)] for s in ORDER) for m in MODELS}

# Two extra rows over the frozen figure: 2.6 -> 3.05 in so the BAR HEIGHT is unchanged; only the
# plotting area grows. The legend/footnote anchors are axes FRACTIONS, so the taller axes turned the
# same fractions into a much larger absolute gap -- they are scaled down to hold the printed spacing.
fig, ax = plt.subplots(figsize=(5.42, 3.05))
for i, m in enumerate(MODELS):
    left = 0.0
    for s in ORDER:
        if not cnt[(m, s)]:
            continue
        w = 100 * cnt[(m, s)] / n[m]
        ax.barh(i, w, left=left, height=0.62, color=FILL[s], edgecolor="white", linewidth=1.2,
                zorder=3)
        left += w
    ab = sum(cnt[(m, s)] for s in ORDER if s.startswith("ABSTAIN"))
    ax.text(101.8, i, f"{ab}/{n[m]}", va="center", ha="left", fontsize=7, color=C.INK)

handles = [plt.Rectangle((0, 0), 1, 1, color=FILL[s]) for s in ORDER]
ax.set_yticks(range(len(MODELS)))
ax.set_yticklabels([SHORT[m] for m in MODELS], fontsize=7.5, color=C.INK)
ax.invert_yaxis()
ax.set_xlim(0, 100); ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0", "25", "50", "75", "100%"])
ax.set_xlabel("Share of that model's L3 worlds")
ax.set_title("Abstention is not one behaviour", loc="left")
ax.legend(handles, [LABEL[s] for s in ORDER], loc="upper center", bbox_to_anchor=(0.5, -0.21),
          ncol=3, handlelength=1.0, columnspacing=1.2, labelspacing=0.35, fontsize=7)
C.footnote(ax, "Right of each bar: abstentions / graded outputs, including recorded exclusions.\n"
               "Opus has 21 outputs: one pre-task exclusion is absent. State labels describe\n"
               "the recorded response, not independently validated scientific correctness.",
           y=-0.44)
C.tidy(ax, axis="x")

C.save(fig, "F08C_l3_states_8models",
       [{"model": FULL[m], "n_worlds": n[m], "frozen_roster": m not in NEW,
         **{LABEL[s]: cnt[(m, s)] for s in ORDER}} for m in MODELS],
       ["model", "n_worlds", "frozen_roster"] + [LABEL[s] for s in ORDER])
