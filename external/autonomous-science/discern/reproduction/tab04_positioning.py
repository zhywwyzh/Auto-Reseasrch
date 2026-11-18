"""Table 4 -- positioning against the closest benchmarks.

Modelled on BixBench Table 1, "BixBench comparison to related benchmarks", and answering
PAPER_OUTLINE.md §11's own Table 1 ("Positioning against seven closest works ... essential, Related
Work; keep compact"), which did not exist as an artifact.

Content is transcribed from RELATED_WORK_AUDIT_2026-08-16.md §4, whose ruling is that DISCERN must NOT
claim to be first at realistic evaluation, real data, counterfactual discovery, executed-code grading,
process grading, hypothesis generation or calibrated trust -- each has clear prior art. The defensible
claim is the COMBINATION, and specifically that DISCERN grades whether an agent independently verifies a
plausible tool output rather than merely invoking the tool or reaching the expected answer.

The cost column is NOT from that audit -- the audit has no cost column, which was itself an omission.
These entries were verified by reading each paper on 2026-08-24/25 (see FIGURES_BUILT.md §5).

"partial" and "not identified" are used exactly as the audit defines them: not identified means the
inspected source did not make the feature a benchmarked construct, NOT that no task incidentally
contains it.

Run: .venv_bench/bin/python tab04_positioning.py
"""
import matplotlib.pyplot as plt
import fig_common as C

COLS = ["real\ndata", "controlled\nDGP", "executed\nprocess", "process\ngrading",
        "clean\nspecificity", "silent\noutput trap", "prior\nconflict", "novelty\nscored",
        "review /\ndebate", "cost\nreported"]
Y, P, N = "yes", "part", "no"
ROWS = [
    ("GeneBench-Pro", [N, Y, Y, P, N, P, N, N, N, Y]),
    ("BiomniBench", [Y, N, Y, Y, N, N, N, N, N, Y]),
    ("NewtonBench", [N, Y, Y, P, N, N, P, N, N, Y]),
    ("DiscoveryBench", [P, Y, Y, Y, N, N, N, Y, N, N]),
    ("DiscoveryWorld", [N, Y, Y, Y, N, P, N, Y, N, N]),
    ("BixBench", [Y, N, Y, P, N, N, N, P, N, N]),
    ("ScienceAgentBench", [Y, P, Y, Y, N, N, N, N, N, Y]),
    ("The AI Scientist", [P, N, Y, Y, N, N, N, Y, Y, Y]),
    ("DISCERN (ours)", [Y, Y, Y, Y, Y, Y, Y, Y, Y, Y]),
]
FILL = {Y: "#20618F", P: "#B4CFE4", N: "#F2F2F2"}
INKC = {Y: "white", P: C.INK, N: C.INK3}
GLYPH = {Y: "●", P: "◐", N: "○"}

# THE ONE ROTATED APPENDIX FLOAT. This is a comparator-positioning table: its width is set by the
# benchmark names and criteria text, not by a plot that can be squeezed, so shrinking figsize only
# widened it (the text does not scale). Typeset it with \begin{sidewaysfigure} in the appendix, where
# the available width is the PAGE HEIGHT (~9 in) and no rescaling happens at all -- which is the
# canonical use of a rotated float and the only exemption check_figure_contract.py grants.
fig, ax = plt.subplots(figsize=(4.60, 3.4))   # ICLR text width is 5.5 in, single column
ax.axis("off")
x0, cw, rh = 0.185, (1 - 0.185) / len(COLS), 0.092
head_y = 0.86

for j, c in enumerate(COLS):
    ax.text(x0 + j * cw + cw / 2, head_y + 0.035, c, ha="center", va="bottom", fontsize=6.4,
            color=C.INK, linespacing=1.5)
ax.plot([0, 1], [head_y - 0.012] * 2, color=C.INK2, lw=1.0)
ax.plot([0, 1], [head_y + 0.165] * 2, color=C.INK2, lw=1.0)

for i, (name, vals) in enumerate(ROWS):
    y = head_y - 0.052 - i * rh
    ours = name.startswith("DISCERN")
    if ours:
        ax.plot([0, 1], [y + rh / 2 - 0.004] * 2, color=C.INK2, lw=1.0)
    ax.text(0.004, y, name, ha="left", va="center", fontsize=6.6, color=C.INK,
            fontweight="bold" if ours else "normal")
    for j, v in enumerate(vals):
        cx = x0 + j * cw + cw / 2
        ax.add_patch(plt.Rectangle((x0 + j * cw + 0.004, y - rh / 2 + 0.008), cw - 0.008, rh - 0.016,
                                   facecolor=FILL[v], edgecolor="white", linewidth=1.0))
        ax.text(cx, y, GLYPH[v], ha="center", va="center", fontsize=7.2, color=INKC[v])
ax.plot([0, 1], [head_y - 0.052 - (len(ROWS) - 1) * rh - rh / 2 - 0.004] * 2, color=C.INK2, lw=1.0)

ax.text(0, head_y + 0.245, "Positioning: the contribution is the combination, not any single axis",
        fontsize=9.5, fontweight="bold", color=C.INK, va="bottom")
ax.text(0, head_y - 0.052 - len(ROWS) * rh - 0.03,
        "● benchmarked construct   ◐ adjacent or present in some form   ○ not identified as a construct. "
        "'Not identified' means the inspected\nsource did not make it a benchmarked feature, not that no "
        "task incidentally contains it (RELATED_WORK_AUDIT §4's own definition).\nNo row but ours is full, "
        "and that is the claim: every column has clear prior art, so DISCERN must not claim to be first at "
        "any one of\nthem. The sharpest single claim is the 'silent output trap' column — grading whether "
        "an agent independently verifies a plausible\ntool output, rather than whether it invoked the tool "
        "or reached the expected answer. The cost column was verified by reading\neach paper (2026-08-25); "
        "the source audit has no cost column, which was itself an omission.",
        fontsize=6.6, color=C.INK3, va="top", linespacing=1.55)

C.save(fig, "T04_positioning",
       [{"work": name, **{c.replace("\n", " "): v for c, v in zip(COLS, vals)}}
        for name, vals in ROWS],
       ["work"] + [c.replace("\n", " ") for c in COLS])
