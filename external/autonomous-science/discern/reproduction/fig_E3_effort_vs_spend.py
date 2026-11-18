"""Figure E3 -- Two ways to be cheap: taking fewer steps, or taking none.

Proposed slot: appendix (cost and efficiency).

Claim: a cost axis alone cannot distinguish efficiency from non-performance. GPT-5.6-sol is cheap
because it reaches an answer in 8 executed code cells where GLM takes 20; GPT-4.1 is cheap because on 20
of 181 assigned L1/L2 tasks it executed ZERO code and answered anyway (the fabrication guard). Only the quality
axis separates them -- which is the argument for never reporting cost on its own.

Also records the one censored measurement in the benchmark: GLM-5.2's median L1 step count EQUALS
max_steps=20, so its L1 token figure is a lower bound and PAPER_NOTES section 1's claim that the ceiling
"leaves capable behavior unconstrained" does not hold for GLM at L1.

Form: scatter in effort-vs-spend space, two points per model (L1 filled, L2 hollow) joined by a thin
line. Frozen model colours plus direct labels.

Run: .venv_bench/bin/python fig_E3_effort_vs_spend.py
"""
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import fig_common as C

E = C.efficiency()
BM = E["by_model"]
MAX_STEPS = 20

fig, ax = plt.subplots(figsize=(3.4, 3.4))

for m in C.MODEL_ORDER:
    b1, b2 = BM[m]["by_level"]["L1"], BM[m]["by_level"]["L2"]
    ax.plot([b1["median_code_cells"], b2["median_code_cells"]],
            [b1["median_tokens"], b2["median_tokens"]], lw=0.9, color=C.COLOR[m], alpha=0.45, zorder=2)
    ax.scatter(b1["median_code_cells"], b1["median_tokens"], s=42, color=C.COLOR[m],
               edgecolor=C.COLOR[m], linewidth=1.3, zorder=3)
    ax.scatter(b2["median_code_cells"], b2["median_tokens"], s=42, color="white",
               edgecolor=C.COLOR[m], linewidth=1.3, zorder=3)

# Labels are pushed apart by hand: Claude/Kimi/DeepSeek sit within one log-decade of each other.
lab = {"gpt-4.1": (9, 3, "left"), "gpt-5.6-sol": (0, 10, "center"), "claude-opus-5": (-8, 7, "right"),
       "deepseek-v4-pro": (0, -17, "center"), "glm-5.2": (0, 11, "center"),
       "kimi-k3": (0, -16, "center")}
for m in C.MODEL_ORDER:
    b1 = BM[m]["by_level"]["L1"]
    dx, dy, ha = lab[m]
    ax.annotate(C.SHORT[m], (b1["median_code_cells"], b1["median_tokens"]),
                textcoords="offset points", xytext=(dx, dy), ha=ha, fontsize=7.5, color=C.INK)

ax.axvline(MAX_STEPS, color=C.INK3, lw=0.9, ls=(0, (3, 3)), zorder=1)
ax.text(MAX_STEPS - 0.45, 4600, "max_steps = 20", rotation=90, va="bottom", ha="right",
        fontsize=7, color=C.INK3)

# Both annotations are parked in empty axes-fraction space, so neither can cross a data point.
g = BM["glm-5.2"]["by_level"]["L1"]
ax.annotate("censored: median = ceiling,\nso this is a lower bound",
            xy=(g["median_code_cells"], g["median_tokens"]), xycoords="data",
            xytext=(0.60, 0.36), textcoords="axes fraction",
            fontsize=7, color=C.COLOR["glm-5.2"], linespacing=1.4, ha="center", va="center",
            arrowprops=dict(arrowstyle="->", color=C.COLOR["glm-5.2"], lw=0.8, shrinkA=3, shrinkB=5))

z = (BM["gpt-4.1"]["by_level"]["L1"]["n_zero_code_cells"]
     + BM["gpt-4.1"]["by_level"]["L2"]["n_zero_code_cells"])
ax.annotate(f"{z} tasks ran zero code",
            xy=(BM["gpt-4.1"]["by_level"]["L1"]["median_code_cells"],
                BM["gpt-4.1"]["by_level"]["L1"]["median_tokens"]), xycoords="data",
            xytext=(0.30, 0.13), textcoords="axes fraction",
            fontsize=7, color=C.COLOR["gpt-4.1"], ha="left", va="center",
            arrowprops=dict(arrowstyle="->", color=C.COLOR["gpt-4.1"], lw=0.8, shrinkA=3, shrinkB=5))

ax.set_yscale("log")
ax.set_ylim(4200, 760000)
ax.set_xlim(0, 23.5)
ax.set_yticks([10000, 30000, 100000, 300000])
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/1000:g}k"))
ax.set_xlabel("Median executed code cells per task")
ax.set_ylabel("Median tokens per task (log scale)")
ax.set_title("Two ways to be cheap", loc="left")
C.footnote(ax, "Filled = L1, hollow = L2, joined per model. Cheapness has two distinct\n"
               "causes and only the quality axis tells them apart.")
C.tidy(ax)

C.save(fig, "E3_effort_vs_spend",
       [{"model": C.FULL[m], "level": L,
         "median_code_cells": BM[m]["by_level"][L]["median_code_cells"],
         "max_code_cells": BM[m]["by_level"][L]["max_code_cells"],
         "median_tokens_per_task": BM[m]["by_level"][L]["median_tokens"],
         "n_zero_code_cell_tasks": BM[m]["by_level"][L]["n_zero_code_cells"],
         "censored_at_max_steps": BM[m]["by_level"][L]["median_code_cells"] == MAX_STEPS}
        for m in C.MODEL_ORDER for L in ("L1", "L2")],
       ["model", "level", "median_code_cells", "max_code_cells", "median_tokens_per_task",
        "n_zero_code_cell_tasks", "censored_at_max_steps"])
