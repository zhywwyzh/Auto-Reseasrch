"""Table T08 -> APPENDIX: the design constraints, and what each one prevents.

FORM BORROWED FROM GENEBENCH-PRO TABLE 1: principle -> implementation -> the failure that occurs if
the principle is dropped. That third column is what makes the table an argument rather than a list of
virtues; a constraint no one could violate is not a constraint. Every implementation cell names a
countable feature of the shipped benchmark, and those counts are DERIVED here rather than typed, so a
constraint cannot outlive the thing that enforces it.

WHY THIS TABLE AND THE REGISTRIES ARE DIFFERENT OBJECTS. T05-T07 say what every world is. This says
why the set has the shape it has -- in particular why 40 of the 203 tasks contain no defect at all,
which reads as wasted budget until the failure column states what happens without them.

Caption draft, kept here so table and caption stay in sync:

    Table A5: DISCERN's design constraints. Each row gives a principle, how the benchmark implements
    it, and the failure that follows if it is dropped. The counts are derived from the shipped task
    set. Two constraints are worth reading together: two-sided calibration and output verification.
    Because 40 of 203 tasks contain no defect and 7 more contain a phenomenon that resembles one, a
    model cannot score well by suspecting everything; and because 34 L2 worlds are tool- or
    procedure-output traps in which the software runs to completion and returns an invalid result, it
    cannot score well by trusting execution either. The prior gate is the L3 analogue: a
    counterfactual is admitted for a model only when that model is measured to hold the belief the
    evidence will contradict, which is why one cell of the 1,218 is excluded rather than scored zero.

Run: .venv_bench/bin/python tab08_design_constraints.py
"""
import collections
import csv
import os
import textwrap

import matplotlib.pyplot as plt

import fig_common as C

BASE = os.path.dirname(os.path.abspath(__file__))
reg = list(csv.DictReader(open(os.path.join(BASE, "results/world_registry.csv"))))
l3 = list(csv.DictReader(open(os.path.join(BASE, "results/fig_data_l3.csv"))))
cls = collections.Counter(r["class"] for r in reg)
n_l3 = len({(r["track"], r["world"]) for r in l3})
n_l3_real = len({(r["track"], r["world"]) for r in l3 if r["is_counterfactual"] != "True"})
n_control = cls["clean control"] + n_l3_real
n_tasks = len(reg) + n_l3
n_fam = len({(r["track"], r["family"]) for r in reg if r["level"] == "L2"})
n_track = len({r["track"] for r in reg})
n_excluded = sum(1 for r in l3 if r["state"] == "CONFOUNDED-EXCLUDED")

ROWS = [
    ("Evidence isolation",
     f"Each of the {n_tasks} worlds is served in its own sealed workspace holding only that world's "
     f"data and documentation. Golden answers, reference solutions and sibling worlds are outside it.",
     "A model reads the answer, or infers it by comparing a perturbed world against its clean twin, "
     "and the score measures retrieval instead of analysis."),
    ("Controlled realism",
     f"Every world is a real published substrate — {n_track} of them — plus one controlled delta. "
     f"Nothing is simulated from scratch, so the unperturbed state is what the field actually measured.",
     "Synthetic problems whose difficulty is arbitrary, or real data whose ground truth nobody knows, "
     "so a wrong answer cannot be distinguished from an unlucky one."),
    ("Two-sided calibration",
     f"{n_control} of {n_tasks} tasks contain no defect at all ({cls['clean control']} L1 and L2 clean "
     f"controls, {n_l3_real} L3 real controls), and {cls['boundary case']} boundary worlds contain a "
     f"real phenomenon that resembles a defect and must be kept.",
     "A model scores well by suspecting everything. Reflexive doubt is indistinguishable from "
     "diagnosis when every world is broken."),
    ("Output verification",
     f"{cls['tool / procedure trap']} L2 worlds leave the data intact and trap the procedure: the "
     f"software runs to completion and returns a complete-looking result that is invalid.",
     "Successful execution is read as a valid answer, which is the failure mode that matters most in "
     "practice and the one a data-corruption benchmark cannot test."),
    ("Held-prior conflict",
     "An L3 counterfactual is admitted for a model only when a prior probe measures THAT model "
     "holding the belief the evidence will contradict; a model that does not hold it is excluded from "
     f"that cell rather than scored ({n_excluded} of 1,218 outcomes).",
     "Ignorance is scored as evidence-over-prior reasoning: a model with no expectation to overturn "
     "looks identical to one that correctly overturned it."),
    ("Independent validity rubric",
     "L3 scoring is a seven-axis rubric applied to the evidence, run as the median of three "
     "independent draws. Three rounds of adversarial review pressure the model, but the reviewer "
     "never defines the truth.",
     "Authority votes override the supplied evidence, and the benchmark rewards conceding to a "
     "reviewer rather than holding a position the data supports."),
]

FIG_W, UNIT_IN = 5.5, 6.21
FS_H, FS_P, FS_B = 7.6, 7.5, 7.5
LH, CPI = 0.0185, 15.8
X1, X2, X3 = 0.004, 0.200, 0.620      # principle · implementation · failure prevented
W2 = int((X3 - X2 - 0.010) * FIG_W * CPI)
W3 = int((1.0 - X3) * FIG_W * CPI)
W1 = int((X2 - X1 - 0.008) * FIG_W * CPI)

fig, ax = plt.subplots(figsize=(FIG_W, UNIT_IN))
ax.set_position([0, 0, 1, 1]); ax.axis("off"); ax.patch.set_visible(False)
ax.set_xlim(0, 1)
y = 1.0
ax.text(X1, y, "Design constraints, and the failure each one prevents", fontsize=9.6,
        fontweight="bold", color=C.INK, va="top")
y -= 0.024
for x, h in ((X1, "principle"), (X2, "DISCERN implementation"), (X3, "failure prevented if dropped")):
    ax.text(x, y, h, fontsize=FS_H, fontweight="bold", color=C.INK2, va="top")
y -= 0.019
ax.plot([0, 1], [y] * 2, color=C.INK2, lw=1.0)

for i, (p, impl, fail) in enumerate(ROWS):
    y -= 0.010
    top = y
    cols = [(X1, textwrap.wrap(p, W1), FS_P, C.INK, True),
            (X2, textwrap.wrap(impl, W2), FS_B, C.INK, False),
            (X3, textwrap.wrap(fail, W3), FS_B, C.INK3, False)]
    for x, lines, fs, col, bold in cols:
        for j, ln in enumerate(lines):
            ax.text(x, top - j * LH, ln, fontsize=fs, color=col, va="top",
                    fontweight="bold" if bold else "normal")
    y = top - max(len(l) for _, l, _, _, _ in cols) * LH - 0.006
    if i < len(ROWS) - 1:
        ax.plot([0, 1], [y] * 2, color=C.GRID, lw=0.7)

ax.plot([0, 1], [y] * 2, color=C.INK2, lw=1.0)
y -= 0.017
foot = (f"Counts are derived from the shipped task set: {n_tasks} canonical tasks over {n_track} "
        f"tracks and {n_fam} L2 analysis families. The first three constraints shape what a world IS; "
        f"the last three shape what a SCORE means.")
for i, ln in enumerate(textwrap.wrap(foot, int(FIG_W * CPI))):
    ax.text(X1, y - i * LH, ln, fontsize=7.0, color=C.INK2, va="top")
y -= len(textwrap.wrap(foot, int(FIG_W * CPI))) * LH + 0.008

ax.set_ylim(y, 1.0)
fig.set_size_inches(FIG_W, UNIT_IN * (1.0 - y))
C.save(fig, "T08_design_constraints",
       [{"principle": p, "implementation": impl, "failure_prevented": f} for p, impl, f in ROWS],
       ["principle", "implementation", "failure_prevented"])
print(f"   {len(ROWS)} constraints · {n_control} control tasks of {n_tasks} · "
      f"{cls['tool / procedure trap']} tool traps")
