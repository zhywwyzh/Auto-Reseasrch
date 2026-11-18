"""Figure 8C -- typed abstention: what a model actually DID when the evidence conflicted with its prior.

Spec: PAPER_OUTLINE.md "Figure 7", planned panel "typed abstention". Claim: abstention is not one
behaviour and must not be scored as one. A CALIBRATED_HOLD (declining while naming the conflict) and an
ARTIFACT call (declining because the evidence is a measurement artifact) are scientific acts;
INSUFFICIENT is a bare refusal. The benchmark types them, and the types are distributed very unevenly
across models.

Real and counterfactual worlds are pooled here on purpose -- this panel is about the DISTRIBUTION of
acts, and Figure 8A already separates the conditions on the score axes.

Run: .venv_bench/bin/python fig07C_l3_states.py
"""
import collections
import matplotlib.pyplot as plt
import fig_common as C

ORDER = ["STRONG", "SOLID", "WEAK", "POOR", "ABSTAIN-CALIBRATED_HOLD", "ABSTAIN-ARTIFACT",
         "ABSTAIN-INSUFFICIENT", "CONFOUNDED-EXCLUDED"]
LABEL = {"STRONG": "strong", "SOLID": "solid", "WEAK": "weak", "POOR": "poor",
         "ABSTAIN-CALIBRATED_HOLD": "abstain: calibrated hold",
         "ABSTAIN-ARTIFACT": "abstain: artifact called",
         "ABSTAIN-INSUFFICIENT": "abstain: insufficient",
         "CONFOUNDED-EXCLUDED": "excluded (prior gate)"}
FILL = {"STRONG": "#1B6B50", "SOLID": "#4E9C7D", "WEAK": "#93C4AC", "POOR": "#E07B5A",
        "ABSTAIN-CALIBRATED_HOLD": C.STATE_ABSTENTION, "ABSTAIN-ARTIFACT": "#A97FD0",
        "ABSTAIN-INSUFFICIENT": "#D9C6EB", "CONFOUNDED-EXCLUDED": "#9B9B9B"}

rows = C.load("fig_data_l3.csv")
cnt = collections.Counter((r["model"], r["state"]) for r in rows)
n = {m: sum(cnt[(m, s)] for s in ORDER) for m in C.MODEL_ORDER}

# ICLR text width is 5.5 in, SINGLE COLUMN. Nothing here overhangs the axes meaningfully, so the
# figure size IS the emitted width -- authored at 5.4 in it needs no rescaling at all.
fig, ax = plt.subplots(figsize=(5.42, 2.6))
for i, m in enumerate(C.MODEL_ORDER):
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
ax.set_yticks(range(len(C.MODEL_ORDER)))
ax.set_yticklabels([C.SHORT[m] for m in C.MODEL_ORDER], fontsize=7.5, color=C.INK)
ax.invert_yaxis()
ax.set_xlim(0, 100); ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0", "25", "50", "75", "100%"])
ax.set_xlabel("Share of that model's L3 worlds")
ax.set_title("Abstention is not one behaviour", loc="left")
ax.legend(handles, [LABEL[s] for s in ORDER], loc="upper center", bbox_to_anchor=(0.5, -0.34),
          ncol=3, handlelength=1.0, columnspacing=1.2, labelspacing=0.35, fontsize=7)
C.footnote(ax, "Right of each bar: abstentions out of worlds attempted. A calibrated hold and an "
               "artifact call are scientific ACTS;\n'insufficient' is a bare refusal. The one "
               "prior-gate exclusion is shown, not hidden — it is a measurement, not missing data.",
           y=-0.72)
C.tidy(ax, axis="x")

C.save(fig, "F08C_l3_states",
       [{"model": C.FULL[m], "n_worlds": n[m], **{LABEL[s]: cnt[(m, s)] for s in ORDER}}
        for m in C.MODEL_ORDER],
       ["model", "n_worlds"] + [LABEL[s] for s in ORDER])
