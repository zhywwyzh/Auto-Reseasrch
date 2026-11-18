"""Figure E1 -- Quality versus cost, with the Pareto frontier.

Proposed slot: main paper, section 6.4 (cost and efficiency). The one cost figure that earns main-paper
space; E2-E4 are appendix candidates.

Claim: quality is not bought. GPT-5.6-sol holds the top benchmark score at lower cost than Claude
Opus 5, so the frontier has a corner point rather than the usual accuracy-for-money trade-off. The two
heaviest TOKEN consumers (DeepSeek, GLM) are among the CHEAPEST in dollars, which is why cost is
reported in dollars here and in tokens in E3.

Form: scatter, one point per model, log cost axis. Identity is carried by both the frozen model colour
and a direct label, never colour alone. Dotted line marks the Pareto frontier.

Run: .venv_bench/bin/python fig_E1_quality_vs_cost.py
"""
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import fig_common as C

E = C.efficiency()
BM = E["by_model"]

pts = [(BM[m]["usd_per_assigned_task"], BM[m]["score_chain_pct"], m)
       for m in C.MODEL_ORDER]
# Pareto frontier: walking left to right on cost, keep every point that beats all cheaper ones.
front, best = [], -1.0
for x, y, m in sorted(pts):
    if y > best:
        front.append(m)
        best = y

fig, ax = plt.subplots(figsize=(3.4, 2.9))          # single ICLR column

fx = [BM[m]["usd_per_assigned_task"] for m in front]
fy = [BM[m]["score_chain_pct"] for m in front]
ax.plot(fx, fy, ls=(0, (2, 2.5)), lw=1.0, color=C.INK3, alpha=0.8, zorder=1)

for x, y, m in pts:
    on = m in front
    ax.scatter(x, y, s=46 if on else 34, zorder=3, linewidth=1.4,
               color=C.COLOR[m] if on else "white", edgecolor=C.COLOR[m])

label_offset = {"gpt-4.1": (0, 9), "gpt-5.6-sol": (-13, 6), "claude-opus-5": (11, -4),
                "deepseek-v4-pro": (11, -13), "glm-5.2": (-8, 6), "kimi-k3": (7, 11)}
align = {"deepseek-v4-pro": "left", "claude-opus-5": "left", "glm-5.2": "right",
         "gpt-5.6-sol": "right", "kimi-k3": "left"}
for x, y, m in pts:
    ax.annotate(f"{C.SHORT[m]}\n${x:.2f}", (x, y), textcoords="offset points",
                xytext=label_offset[m], ha=align.get(m, "center"), fontsize=7.5,
                color=C.INK, linespacing=1.3)

ax.set_xscale("log")
ax.set_xlim(0.028, 2.0)
ax.set_ylim(34, 82)
ax.set_xticks([0.05, 0.1, 0.25, 0.5, 1.0])
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:g}"))
ax.set_xlabel("Cost per task (USD, log scale)")
ax.set_ylabel("Life-science chain score (0–100)")
ax.set_title("Quality is not bought", loc="left")
C.footnote(ax, "Dotted line: Pareto frontier; filled points lie on it. Bench-only tokens at\n"
               "first-party list rates, 2026-08-24. Denominator: 203 assigned tasks per model.\n"
               "Shared L3 reviewers and grading excluded.")
C.tidy(ax)

C.save(fig, "E1_quality_vs_cost",
       [{"model": C.FULL[m], "usd_per_task": BM[m]["usd_per_assigned_task"],
         "quality_track_geo_mean": BM[m]["score_chain_pct"],
         "usd_per_quality_point": BM[m]["usd_per_quality_point"],
         "on_pareto_frontier": m in front} for m in C.MODEL_ORDER],
       ["model", "usd_per_task", "quality_track_geo_mean", "usd_per_quality_point",
        "on_pareto_frontier"])
