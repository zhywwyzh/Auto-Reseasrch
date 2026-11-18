"""Figure E2 -- Where the money goes: cost decomposed by stage.

Proposed slot: appendix (cost and efficiency).

Claim: cost concentrates in the ANALYSIS loop, not in discovery. L3 generates a hypothesis and defends
it through three rounds of adversarial review and is still the cheapest stage for all six models,
because L1/L2 run a 20-step sandbox tool loop while L3 runs at 3-6 steps. This is the opposite of the
usual intuition that hypothesis generation is the expensive part.

Form: stacked horizontal bars, one per model, three stage segments. Stage is a structural facet, not a
scientific state, so the segments take an ordered light-to-dark ramp of a single neutral-blue hue rather
than three categorical hues -- which also keeps every model colour free for E1/E3.

Run: .venv_bench/bin/python fig_E2_cost_by_level.py
"""
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import fig_common as C

E = C.efficiency()
BM = E["by_model"]
LEVELS = ["L1", "L2", "L3"]
STAGE = {"L1": "L1  data integrity", "L2": "L2  analysis", "L3": "L3  discovery"}
# sequential ramp, one hue, light -> dark (stage is ordered, so magnitude encoding beats identity)
RAMP = {"L1": "#BBD4E8", "L2": "#6FA8CE", "L3": "#20618F"}

order = sorted(C.MODEL_ORDER, key=lambda m: -BM[m]["usd_total"])
usd = {L: [round(BM[m]["by_level"][L]["usd_per_cell"] * BM[m]["by_level"][L]["n_cells"], 2)
           for m in order] for L in LEVELS}

fig, ax = plt.subplots(figsize=(3.4, 2.5))
y = list(range(len(order)))
left = [0.0] * len(order)
for L in LEVELS:
    ax.barh(y, usd[L], left=left, height=0.62, color=RAMP[L], edgecolor="white", linewidth=1.3,
            label=STAGE[L], zorder=3)
    left = [a + b for a, b in zip(left, usd[L])]

for i, m in enumerate(order):
    ax.text(left[i] + 7, i, f"${BM[m]['usd_total']:,.0f}", va="center", fontsize=7.5, color=C.INK)

ax.set_yticks(y)
ax.set_yticklabels([C.SHORT[m] for m in order], fontsize=7.5, color=C.INK)
ax.invert_yaxis()
ax.set_xlim(0, 360)
ax.set_xticks([0, 100, 200, 300])
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:g}"))
ax.set_xlabel("Total cost across all eight tracks (USD)")
ax.set_title("Cost lives in the analysis loop", loc="left")
ax.legend(loc="lower right", handlelength=1.0, borderpad=0.2, labelspacing=0.35)
C.footnote(ax, "L1/L2 run a 20-step sandbox tool loop; L3 runs at 3–6 steps plus three\n"
               f"review rounds. Benchmark total: ${E['totals']['bench_usd']:,.2f} over "
               f"{E['n_outputs_metered']:,} executed outputs.", y=-0.30)
C.tidy(ax, axis="x")

C.save(fig, "E2_cost_by_level",
       [{"model": C.FULL[m], "level": L, "n_tasks": BM[m]["by_level"][L]["n_cells"],
         "usd_total": usd[L][i], "usd_per_task": BM[m]["by_level"][L]["usd_per_cell"],
         "median_tokens_per_task": BM[m]["by_level"][L]["median_tokens"]}
        for i, m in enumerate(order) for L in LEVELS],
       ["model", "level", "n_tasks", "usd_total", "usd_per_task", "median_tokens_per_task"])
