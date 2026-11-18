"""Figure 1 -- the evidence-preserving scientific chain, and how it breaks.

Spec: PAPER_OUTLINE.md "Figure 1 -- The evidence-preserving scientific chain". The one visual that
defines the paper: raw data -> L1 integrity decision -> L2 verified analysis -> evidence dossier ->
L3 hypothesis under adversarial review -> guidance for a human, with the propagated-error path beneath
it and the three objects of CALIBRATED trust marked at the stage each is tested.

This is a SCHEMATIC: it encodes the benchmark's construct, not measurements. It is the only figure here
with no data behind it, so its companion CSV lists the nodes and edges rather than plotted values.

NO IN-FIGURE CAPTION. At ICLR's 5.5-inch column the explanatory paragraph would render below 6 pt, so
it belongs in \\caption{}. Draft, kept here so figure and caption stay in sync:

    Figure 1: The evidence-preserving scientific chain. Each stage hands its OUTPUT forward as the next
    stage's evidence, so an unverified step is not a local error -- it is inherited, and the lower row
    traces that inheritance to its endpoint. The chain exists for its last two boxes: GENERATE a
    hypothesis the evidence supports, then GUIDE a human's next experiment. The final box is dashed and
    carries a question mark because it is the claim under test, not a result; everything to its left is
    the machinery that would have to hold for the answer to be yes. DISCERN grades the three shaded
    stages, and each tests a different object of calibrated trust -- in the data (L1), in a tool's
    output (L2), and in the model's own prior (L3). Note the vertical pairing of the two endpoints:
    "false discovery guidance" sits directly beneath the question it would be the wrong answer to.

Run: .venv_bench/bin/python fig01_evidence_chain.py
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import fig_common as C

GOOD, BAD, GOAL = "#20618F", "#B03A2E", "#1B6B50"
# Each stage's label is a list of (text, emphasised) lines, so the two acts the paper is actually about
# can be set in bold inside their boxes: GENERATING a hypothesis at L3, and GUIDING a human afterwards.
# Everything before those two is the machinery that makes them trustworthy.
STAGES = [
    ([("raw assay", 0), ("data", 0)], "substrate", None),
    ([("L1", 0), ("integrity", 0), ("decision", 0)], "L1", "in DATA"),
    ([("L2", 0), ("verified", 0), ("analysis", 0)], "L2", "in TOOL OUTPUT"),
    ([("evidence", 0), ("dossier", 0)], "handoff", None),
    ([("L3", 0), ("GENERATE", 1), ("a HYPOTHESIS", 1), ("+ defend it", 0)], "L3", "in PRIOR"),
    # The '?' is the point of the whole paper: this box is a QUESTION, not an achievement. The dashed
    # outline says the same thing visually -- every other box on the chain is something the benchmark
    # measures; this one is what it is trying to find out.
    ([("GUIDE a", 1), ("human's NEXT", 1), ("EXPERIMENT ?", 1)], "use", None),
]
BROKEN = ["defect\nmissed", "invalid\noutput", "plausible\nwrong result", "false\nconclusion",
          "false discovery\nguidance"]

fig, ax = plt.subplots(figsize=(6.9, 3.4))
ax.set_xlim(0, 100); ax.set_ylim(0, 68); ax.axis("off")

W, H, GAP = 14.5, 12.5, 2.2        # widened so the two emphasised labels fit inside their boxes
CHAIN_Y, FAIL_Y = 31.0, 10.0       # box bottoms
TRUST_Y = CHAIN_Y + H + 10.0       # the three objects of trust
BRACE_Y = TRUST_Y + 3.0            # the span that names the construct they belong to

x = 1.0
centers = []
for lines, kind, trust in STAGES:
    graded = kind in ("L1", "L2", "L3")
    goal = kind == "use"
    face = "#DCEAF7" if kind == "L3" else "#EAF1F8" if graded else "#E7F3EC" if goal else "white"
    edge = GOAL if goal else GOOD if graded else C.GRID
    lw = 2.0 if kind in ("L3", "use") else 1.3          # the two acts get the heavier outline
    ls = (0, (4.5, 2.2)) if goal else "solid"           # dashed = asserted, not yet established
    ax.add_patch(FancyBboxPatch((x, CHAIN_Y), W, H, boxstyle="round,pad=0.35,rounding_size=1.1",
                                facecolor=face, edgecolor=edge, linewidth=lw, linestyle=ls,
                                zorder=3))
    # lines are drawn individually so a single line can be emphasised without splitting the box
    step = 3.1
    y_top = CHAIN_Y + H / 2 + step * (len(lines) - 1) / 2
    for k, (txt, em) in enumerate(lines):
        ax.text(x + W / 2, y_top - k * step, txt, ha="center", va="center",
                fontsize=6.2 if em else 7.3, color=GOAL if (em and goal) else C.INK,
                fontweight="bold" if em else "normal", zorder=4)
    if trust:
        ax.text(x + W / 2, TRUST_Y, trust, ha="center", va="center", fontsize=6.6,
                color=GOOD, fontweight="bold", zorder=4)
    centers.append(x + W / 2)
    x += W + GAP

# Name the construct once, above the three objects it applies to. Ordinary trust is not the claim --
# CALIBRATED trust is, and repeating "trust in ..." three times said the weaker thing three times.
lo, hi = centers[1] - W / 2 + 1.0, centers[4] + W / 2 - 1.0
ax.plot([lo, hi], [BRACE_Y] * 2, color=GOOD, lw=0.9, zorder=2)
for xt in (lo, hi):
    ax.plot([xt, xt], [BRACE_Y, BRACE_Y - 1.6], color=GOOD, lw=0.9, zorder=2)
ax.text((lo + hi) / 2, BRACE_Y + 2.4, "CALIBRATED TRUST", ha="center", va="center", fontsize=7.0,
        color=GOOD, fontweight="bold", zorder=4)

for i, (a, b) in enumerate(zip(centers, centers[1:])):
    last = i == len(centers) - 2                        # the hand-off to the human is the payoff
    ax.add_patch(FancyArrowPatch((a + W / 2 + 0.4, CHAIN_Y + H / 2), (b - W / 2 - 0.4, CHAIN_Y + H / 2),
                                 arrowstyle="-|>", mutation_scale=11 if last else 9,
                                 color=GOAL if last else GOOD, lw=1.7 if last else 1.2, zorder=2))

ax.text(centers[-1], CHAIN_Y + H + 3.2, "the open question", ha="center", va="center",
        fontsize=6.4, color=GOAL, style="italic", zorder=4)

# the propagated-error path
for i, label in enumerate(BROKEN):
    cx = centers[i + 1] if i + 1 < len(centers) else centers[-1]
    ax.add_patch(FancyBboxPatch((cx - W / 2, FAIL_Y), W, 8.6,
                                boxstyle="round,pad=0.3,rounding_size=1.0",
                                facecolor="#FBEDEA", edgecolor=BAD, linewidth=1.0, zorder=3))
    ax.text(cx, FAIL_Y + 4.3, label, ha="center", va="center", fontsize=6.8, color=BAD,
            linespacing=1.4, zorder=4)
for i in range(len(BROKEN) - 1):
    a, b = centers[i + 1], centers[i + 2]
    ax.add_patch(FancyArrowPatch((a + W / 2 + 0.4, FAIL_Y + 4.3), (b - W / 2 - 0.4, FAIL_Y + 4.3),
                                 arrowstyle="-|>", mutation_scale=8, color=BAD, lw=1.0, zorder=2))
ax.add_patch(FancyArrowPatch((centers[1], CHAIN_Y - 0.8), (centers[1], FAIL_Y + 9.4),
                             arrowstyle="-|>", mutation_scale=8, color=BAD, lw=1.0,
                             ls=(0, (2.5, 2)), zorder=2))
ax.text(centers[1] + 1.2, (CHAIN_Y + FAIL_Y + 8.6) / 2, "one unverified step\nleaves the chain",
        fontsize=6.6, color=BAD, va="center", linespacing=1.4)

# Iteration arrow on the L3 box. DiscoveryWorld Figure 2 makes iteration explicit -- agents must loop
# hypothesis and experiment to reach an explanatory discovery. Ours iterates too, but over REVIEW rather
# than over experiments: the hypothesis is defended across three adversarial rounds and may be revised.
_l3 = centers[4]
ax.annotate("", xy=(_l3 + W / 2 - 1.2, CHAIN_Y + H + 0.4),
            xytext=(_l3 - W / 2 + 1.2, CHAIN_Y + H + 0.4),
            arrowprops=dict(arrowstyle="-|>", color=GOOD, lw=1.0,
                            connectionstyle="arc3,rad=-0.75", shrinkA=0, shrinkB=0))
ax.text(_l3, CHAIN_Y + H + 6.4, "3 review rounds", ha="center", fontsize=6.4, color=GOOD)

ax.text(0.6, 67.0, "The evidence-preserving scientific chain", fontsize=9.5, fontweight="bold",
        color=C.INK, va="top")

C.save(fig, "F01_evidence_chain",
       [{"row": "chain", "position": i, "node": " ".join(t for t, _e in s[0]), "kind": s[1],
         "calibrated_trust_in": s[2] or ""} for i, s in enumerate(STAGES)] +
       [{"row": "failure", "position": i + 1, "node": b.replace("\n", " "), "kind": "propagated",
         "calibrated_trust_in": ""} for i, b in enumerate(BROKEN)],
       ["row", "position", "node", "kind", "calibrated_trust_in"])
