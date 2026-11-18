"""Figure 2 -- the stage-specific measurement contract, three parallel designs.

Split out of the former combined inventory table and given its OWN FLOAT NUMBER, not "Table 1b":
it appears in a different section from the coverage table, so a shared number would be wrong, and it
is a diagram rather than a tabulation. Coverage (tab01_coverage.py, Table 1) belongs with the
benchmark design; this belongs with grading. Together they were 7.0 in tall, too tall for a column.

FORM. BiomniBench Figure 2 draws its benchmark as a pipeline rather than tabulating it. This is that
logic, but as THREE PARALLEL CONTRACTS with NO horizontal arrows. An earlier build chained the three
stage boxes left to right, which implied that an L1 defect becomes an L2 confound and then an L3
counterfactual. It does not: the three interventions are independent measurement designs applied to
the same substrate. Stage DEPENDENCY is Figure 1's job.

"MEASURES", not "graded dimensions": L1 resolves to a STATE, L2 to ONE 0-3 accuracy-plus-handling score,
L3 to the common axes. One label implying the same independent-subscore structure everywhere would be
false -- and the three stages differ in exactly that way.

CHECKED AGAINST THE HARNESS, not against the prose that described it:
  * L1 receives DATA + DOCUMENTATION, not raw data alone. Seven of eight specs ship a
    data_dictionary.json and/or study_metadata.json into every sealed L1 world (only hist_gene_exp
    sets docs: []). metadata_reconciliation is the most widespread defect class in the benchmark,
    present in five tracks, and is only findable by reading those docs.
  * L3 grades SEVEN axes: grade_l3.AXES is data_fidelity, prior_awareness, causal_calibration,
    reviewer_robustness, scientific_humility, citation_integrity, novelty. An earlier build listed
    four and dropped prior awareness, scientific humility and CITATION INTEGRITY -- the last being one
    of the paper's distinctive axes, with a recorded fabrication in the corpus.
  * L1 also records a per-task hallucination rate (474/474 tasks, nonzero on 4), so fabrication is a
    measured dimension there and is listed.
  * L1's chips are deliberately NOT the four L2 dimensions, even though Figure 4 shows the two stages
    side by side on those four labels. What L1 INSTRUMENTS is one of twelve states plus a clean-world
    outcome and a fabrication rate; the four categories are DERIVED from the state machine for the
    crosswalk. Printing them here would claim L1 records four subscores, which it does not. The
    asymmetry is the honest reading and Figure 4 is where the crosswalk is made.
  * L2's INTERVENTION classes are now tagged benchmark-wide (L2_DESIGN.md s1, tagged 2026-08-27):
    36 data confounds, 34 tool traps, 8 statistical traps, 24 clean, over all 102 worlds. An earlier
    build said "only enhancer_activity and crispr_screen carry that tag structurally" -- that was true
    of the graded records, not of the manifests, and five tracks had always carried it. The statistical
    class is listed here because 8 worlds are neither a corrupted input nor a misleading tool output.
  * L2's MEASURES are the four shared dimensions of the meta-review (L2_META_RUBRIC.md), which map all
    612 canonical cells onto analytical correctness, issue recognition, methodological response and
    result calibration. An earlier build listed a five-item crosswalk -- execution / quantitative
    correctness / scientific interpretation / input verification / output verification -- that was
    PROSE ONLY and was never implemented by any grader. The four are EQUALLY weighted
    (score = 3 x mean(A, I, M, C)), so unlike L3 they take a flat list: no grouping is needed to keep
    the drawing faithful to the arithmetic.

L3 IS GROUPED D / Q / N BECAUSE THAT IS THE ARITHMETIC: composite = avg(D, aggregate Q, N), where Q is
the mean of five axes (grade_l3.QAX). Seven equal boxes implied a seven-axis average and would have
overweighted every Q axis by ~2.3x relative to how the score is actually computed.

AUTHORED AT FINAL SIZE: 5.5 in wide, every glyph >= 7.5 pt, canvas sized to the drawn content.

Caption draft, kept here so figure and caption stay in sync:

    Figure 2: The stage-specific measurement contract. The three stage contracts are parallel, not
    sequential: each names what the agent receives, what is held under experimental control, what it
    must produce, and what it MEASURES. The three stages resolve differently and the figure says so:
    L1 to one of twelve states, L2 to a single 0-3 accuracy-plus-handling score decomposed onto four
    equally weighted shared dimensions, and L3 to common axes grouped as they are actually combined --
    the L3 composite is the mean of D, aggregate Q, and N, so the five Q axes together carry the weight
    of one term rather than five. The L2 dimensions are a decomposition of the recorded grades rather
    than four independent measurements; Figure 4 carries that caveat where the values are shown. L1's
    entry lists what it instruments rather than those four labels -- Figure 4 derives the shared
    categories from L1's state machine, but L1 itself records a state, not four subscores. Step
    budgets
    differ by stage and are part of a score's meaning: L1 and L2 run to max_steps=20, L3 to 3-6 steps
    plus three rounds of adversarial review. Track coverage is given in Table 1.

Run: .venv_bench/bin/python fig02_measurement_contract.py
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import fig_common as C

FIG_W, CPI = 5.5, 15.5
UNIT_IN, TOP_U, BOT_U = 6.21, 1.0, -0.60
STAGE_FILL = {"L1": "#C6DBEC", "L2": "#7FADD1", "L3": "#20618F"}
FS_TAG, FS_KEY = 7.5, 7.8
LH, LINESP, CH = 0.0193, 1.15, 0.0201          # row line height, matched linespacing, chip line height

ROWS = ["receives", "intervention\n/ control", "must produce", "measures"]
CONTRACT = {
    "L1": ["data + documentation",
           "injected defect, clean\ncontrol, or non-defect\nboundary case",
           "trust decision\n+ proportionate action",
           ["clean specificity", "recognition →\ndiagnosis → action", "fabrication rate"]],
    "L2": ["data + documentation\n+ tools",
           "data confound,\ninvalid tool output,\nstatistical trap,\nor clean analysis",
           "executed artifact\n+ scientific\ninterpretation",
           ["analytical correctness", "issue recognition", "methodological\nresponse",
            "result calibration"]],
    "L3": ["evidence dossier",
           "evidence–prior conflict\nor real control\nboth reviewed\nadversarially",
           "hypothesis +\ndiscriminating test +\nevidence-based defense\nor revision",
           ["D:  evidence fidelity",
            "Q:  prior awareness ·\ncausal calibration ·\nresponse to critique ·\n"
            "scientific humility ·\ncitation integrity",
            "N:  valid novelty"]],
}

XL = 0.175
BW = (1 - XL) / 3
BUD = int(BW * FIG_W * CPI)
_over = [f"{L} {ln!r} ({len(ln)} > {BUD})" for L in ("L1", "L2", "L3")
         for fld in CONTRACT[L][:3] + CONTRACT[L][3] for ln in fld.split("\n") if len(ln) > BUD]
if _over:
    raise SystemExit("column overflow:\n  " + "\n  ".join(_over))

fig, ax = plt.subplots(figsize=(FIG_W, UNIT_IN * (TOP_U - BOT_U)))
ax.set_position([0.0, 0.0, 1.0, 1.0])
ax.axis("off")
ax.patch.set_visible(False)
ax.set_xlim(0, 1); ax.set_ylim(BOT_U, TOP_U)

bxs = [XL + i * BW for i in range(3)]
y = TOP_U - 0.024
for L, x in zip(("L1", "L2", "L3"), bxs):
    ax.add_patch(FancyBboxPatch((x + 0.004, y - 0.004), BW - 0.008, 0.022,
                                boxstyle="round,pad=0.002,rounding_size=0.008",
                                facecolor=STAGE_FILL[L], alpha=0.30, edgecolor=STAGE_FILL[L],
                                linewidth=1.1))
    ax.text(x + BW / 2, y + 0.007, L, ha="center", va="center", fontsize=FS_KEY, fontweight="bold",
            color=C.INK)
y -= 0.014
ax.plot([0, 1], [y] * 2, color=C.INK2, lw=1.0)

for ri, row in enumerate(ROWS):
    if row == "measures":
        need = max(sum(len(d.split("\n")) for d in CONTRACT[L][3]) * CH
                   + len(CONTRACT[L][3]) * 0.007 for L in ("L1", "L2", "L3"))
        h = need + 0.008
        y -= h
        ax.text(0.004, y + h / 2, row, fontsize=FS_TAG, color=C.INK3, va="center",
                linespacing=LINESP)
        for L, x in zip(("L1", "L2", "L3"), bxs):
            cy = y + h - 0.006
            for d in CONTRACT[L][3]:
                lines = d.split("\n")
                ch = len(lines) * CH + 0.004
                ax.add_patch(FancyBboxPatch((x + 0.006, cy - ch), BW - 0.012, ch,
                                            boxstyle="round,pad=0.001,rounding_size=0.006",
                                            facecolor="white", edgecolor=STAGE_FILL[L],
                                            linewidth=0.7))
                for k, ln in enumerate(lines):
                    ax.text(x + BW / 2, cy - 0.004 - k * CH - CH / 2 + 0.002, ln, ha="center",
                            va="center", fontsize=FS_TAG, color=C.INK2)
                cy -= ch + 0.003
    else:
        n = max(len(CONTRACT[L][ri].split("\n")) for L in ("L1", "L2", "L3"))
        h = n * LH + 0.009
        y -= h
        ax.text(0.004, y + h / 2, row, fontsize=FS_TAG, color=C.INK3, va="center",
                linespacing=LINESP)
        for L, x in zip(("L1", "L2", "L3"), bxs):
            ax.text(x + BW / 2, y + h / 2, CONTRACT[L][ri], ha="center", va="center",
                    fontsize=FS_TAG, color=C.INK, linespacing=LINESP)
    ax.plot([0, 1], [y] * 2, color=C.GRID, lw=0.7)
ax.plot([0, 1], [y] * 2, color=C.INK2, lw=1.0)

_y_end = y - 0.012
ax.set_ylim(_y_end, TOP_U)
fig.set_size_inches(FIG_W, UNIT_IN * (TOP_U - _y_end))

C.save(fig, "F02_measurement_contract",
       [{"stage": L, "receives": CONTRACT[L][0].replace("\n", " "),
         "intervention_control": CONTRACT[L][1].replace("\n", " "),
         "must_produce": CONTRACT[L][2].replace("\n", " "),
         "measurement_dimensions": " · ".join(d.replace("\n", " ") for d in CONTRACT[L][3])}
        for L in ("L1", "L2", "L3")],
       ["stage", "receives", "intervention_control", "must_produce", "measurement_dimensions"])
