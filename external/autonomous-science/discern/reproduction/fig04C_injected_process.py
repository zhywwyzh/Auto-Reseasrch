"""Figure 4C -- injected worlds: recognition -> diagnosis -> action.

Spec: FIGURES_2_5_PLAN.md "Figure 3 / Panel C". Claim: noticing that something is wrong frequently
fails to become a correct diagnosis or a corrective action. Across 426 injected evaluations, 229 reach
correct diagnosis AND action, while 97 notice an abnormality and misidentify it.

The nine raw state labels are plotted UNCOLLAPSED, in the plan's order, because collapsing
ABSTAIN-RECOGNIZED into ABSTAIN-OK or MISS into NONCOMPLIANT would merge categories with different
scientific meanings. They are ordinal, so they take the ordered outcome ramp; abstention keeps the
reserved purple.

Run: .venv_bench/bin/python fig03C_injected_process.py
"""
import collections
import matplotlib.pyplot as plt
import fig_common as C

ORDER = ["DIAGNOSE-AND-ACT", "DIAGNOSE-AND-ACT-PARTIAL", "DIAGNOSE-NOT-ACT", "NOTICE-WRONG",
         "ABSTAIN-RECOGNIZED", "ABSTAIN-OK", "OVER-DIAGNOSE", "MISS", "NONCOMPLIANT"]
LABEL = {"DIAGNOSE-AND-ACT": "diagnose + act", "DIAGNOSE-AND-ACT-PARTIAL": "diagnose + act (partial)",
         "DIAGNOSE-NOT-ACT": "diagnosed, no action", "NOTICE-WRONG": "noticed, wrong diagnosis",
         "ABSTAIN-RECOGNIZED": "abstain (recognized)", "ABSTAIN-OK": "abstain (appropriate)",
         "OVER-DIAGNOSE": "over-diagnose", "MISS": "miss", "NONCOMPLIANT": "noncompliant"}

rows = [r for r in C.load("fig_data_l1.csv") if not r["is_clean"]]
cnt = collections.Counter((r["model"], r["state"]) for r in rows)
n = {m: sum(cnt[(m, s)] for s in ORDER) for m in C.MODEL_ORDER}

# ICLR text width is 5.5 in, SINGLE COLUMN. Nothing here overhangs the axes meaningfully, so the
# figure size IS the emitted width -- authored at 5.4 in it needs no rescaling at all.
fig, ax = plt.subplots(figsize=(5.35, 2.9))
for i, m in enumerate(C.MODEL_ORDER):
    left = 0.0
    for s in ORDER:
        w = 100 * cnt[(m, s)] / n[m]
        if w == 0:
            continue
        ax.barh(i, w, left=left, height=0.62, color=C.OUTCOME[s], edgecolor="white", linewidth=1.2,
                zorder=3)
        left += w
    ax.text(101.8, i, f"{cnt[(m, 'DIAGNOSE-AND-ACT')]}/{n[m]}", ha="left", va="center", fontsize=7,
            color=C.INK)
# Legend handles built explicitly, so the ordinal order survives into the key.
handles = [plt.Rectangle((0, 0), 1, 1, color=C.OUTCOME[s]) for s in ORDER]

ax.set_yticks(range(len(C.MODEL_ORDER)))
ax.set_yticklabels([C.SHORT[m] for m in C.MODEL_ORDER], fontsize=7.5, color=C.INK)
ax.invert_yaxis()
ax.set_xlim(0, 100)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0", "25", "50", "75", "100%"])
ax.set_xlabel("Share of that model's 71 injected-world tasks")
C.title(ax, "Recognition does not become diagnosis, and diagnosis does not become action")      # wraps to the figure width; a raw left title does not
ax.legend(handles, [LABEL[s] for s in ORDER], loc="upper center", bbox_to_anchor=(0.5, -0.34),
          ncol=3, handlelength=1.0, columnspacing=1.2, labelspacing=0.35)
C.footnote(ax, "Right of each bar: correct diagnose-and-act, out of 71. 426 injected evaluations in "
               "total, 229 of them diagnose-and-act.\nNine raw state labels, uncollapsed. GPT-4.1's "
               "35/71 noticed-but-wrong outcomes are the largest single failure block in L1.", y=-0.66)
C.tidy(ax, axis="x")

C.save(fig, "F04C_injected_process",
       [{"model": C.FULL[m], "n_injected": n[m], **{LABEL[s]: cnt[(m, s)] for s in ORDER}}
        for m in C.MODEL_ORDER],
       ["model", "n_injected"] + [LABEL[s] for s in ORDER])
