"""Figure E4 -- Declining is 4.9-6.6x cheaper than committing, for every model.

Proposed slot: appendix (cost and efficiency). Directly answers PAPER_OUTLINE section 6.4's
"abstention-adjusted efficiency, so cheap refusal is not rewarded as scientific success."

Claim: at L3 a declared-insufficient world costs a fraction of a committed one, and the ratio is stable
across six very different models -- consistent with the task structure: a committed
hypothesis must survive three rounds of adversarial review, a declared-insufficient one exits early.
This prices the 2.50 abstention ceiling (against 3.00 on the committed path), which was adopted as a
design decision about what the benchmark rewards, before this measurement existed.

Second, quieter claim: the pooled L3 cost per model is composition-dependent and must not be quoted
alone. Abstention rates run from 4/21 (Claude) to 18/22 (GPT-5.6-sol), so L3 cost comparisons are made
commit-only. The rate is printed under each model rather than drawn on a second y-axis.

Form: grouped bars, log token axis. These are SCIENTIFIC STATES, not models, so no model colour appears:
abstention takes the reserved purple state colour and the committed bar a neutral ink.

Run: .venv_bench/bin/python fig_E4_abstain_vs_commit.py
"""
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import fig_common as C

E = C.efficiency()
BM = E["by_model"]
S = {m: BM[m]["l3_split"] for m in C.MODEL_ORDER}

order = sorted(C.MODEL_ORDER, key=lambda m: -S[m]["median_commit"])
ab = [S[m]["median_abstain"] for m in order]
co = [S[m]["median_commit"] for m in order]

fig, ax = plt.subplots(figsize=(3.6, 2.9))
x = list(range(len(order)))
w = 0.36
ax.bar([i - w / 2 for i in x], ab, w, color=C.STATE_ABSTENTION, edgecolor="white", linewidth=1.2,
       label="Abstained", zorder=3)
ax.bar([i + w / 2 for i in x], co, w, color=C.NEUTRAL_INK, edgecolor="white", linewidth=1.2,
       label="Committed", zorder=3)

for i, m in enumerate(order):
    ax.text(i, max(ab[i], co[i]) * 1.45, f"{S[m]['commit_over_abstain']:.1f}×", ha="center",
            fontsize=7.5, color=C.INK, fontweight="bold")

ax.set_yscale("log")
ax.set_ylim(900, 1_100_000)
ax.set_yticks([1000, 10000, 100000])
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/1000:g}k"))
ax.set_xticks(x)
# The abstention rate rides in the tick label -- a second y-axis for it would break the one-axis rule.
ax.set_xticklabels([f"{C.SHORT[m]}\n{S[m]['n_abstain']}/{S[m]['n']}" for m in order],
                   fontsize=7, color=C.INK, linespacing=1.5)
ax.set_xlim(-0.72, len(order) - 0.28)
ax.set_ylabel("Median L3 tokens per world (log scale)")
lo = min(S[m]["commit_over_abstain"] for m in C.MODEL_ORDER)
hi = max(S[m]["commit_over_abstain"] for m in C.MODEL_ORDER)
ax.set_title(f"Declining is {lo:.1f}–{hi:.1f}× cheaper than committing", loc="left")
ax.legend(loc="upper right", ncol=2, handlelength=1.0, columnspacing=1.0)
C.footnote(ax, "Second tick row: worlds abstained on, out of graded outputs. The repeated gap is\n"
               "consistent with the task structure: commitment continues through review. Abstention\n"
               "rates range 19–82%, so pooled L3 cost is composition-dependent.", y=-0.30)
C.tidy(ax)

C.save(fig, "E4_abstain_vs_commit",
       [{"model": C.FULL[m], "n_l3_worlds": S[m]["n"], "n_abstain": S[m]["n_abstain"],
         "n_commit": S[m]["n_commit"], "abstain_rate": S[m]["abstain_rate"],
         "median_tokens_abstain": S[m]["median_abstain"],
         "median_tokens_commit": S[m]["median_commit"],
         "median_tokens_all": S[m]["median_all"],
         "commit_over_abstain": S[m]["commit_over_abstain"]} for m in order],
       ["model", "n_l3_worlds", "n_abstain", "n_commit", "abstain_rate", "median_tokens_abstain",
        "median_tokens_commit", "median_tokens_all", "commit_over_abstain"])
