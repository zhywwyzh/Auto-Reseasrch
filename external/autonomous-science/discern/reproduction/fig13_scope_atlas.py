"""Figure 13 -> MAIN-PAPER scope overview: what DISCERN covers, and what it perturbs.

BUILD ID, NOT PAPER POSITION. The intended slot is the main text's scope figure, replacing the
T01a/T01b inventory that currently sits there; T01 moves to the appendix and grows into the complete
registries (T05 L1, T06 L2, T07 L3). The number here only has to be unique among the built figures.

WHY A COMPACT OVERVIEW AND A SEPARATE COMPLETE INVENTORY. GeneBench-Pro's Figure 2 is a hierarchical
atlas -- domain, subdomain, representative analyses, problem COUNT -- and does not enumerate its 129
problems anywhere in that figure; its Table 1 does a different job entirely (design principle ->
requirement -> failure if violated). BiomniBench's Figure 2 pairs a construction workflow with a
coverage matrix and its marginal distributions. Both separate the compact overview from the complete
inventory. DISCERN has a page limit those papers did not, so that separation is not a stylistic choice
here: the overview is the only scope object the main text can afford, and everything enumerable moves
to the appendix registries.

PANEL A IS A SCIENTIFIC HIERARCHY, NOT A PAGE ORDER. The tracks are grouped by what they measure --
statistical/clinical genetics, transcriptomics, functional/regulatory genomics, protein biophysics --
because the previous grouping was `PER_PART = 4`, a LaTeX page-break constant. A reader should be able
to see that the benchmark spans four levels of biological organisation, which no operational ordering
shows.

PANEL B IS THE CLAIM THE ATLAS CANNOT MAKE. Scope alone does not distinguish DISCERN from a task
collection; the controlled intervention does. So B gives, per stage, how many worlds are CONTROLS and
how the rest divide into intervention classes. Hue is the stage (matching Figure 3), intensity is the
class within it, and the control segment is always the lightest -- a benchmark that only perturbs
would reward reflexive suspicion, so the controls are part of the design, not filler.

THE STAGES ARE A DEPENDENT CHAIN; THE WORLDS ARE INDEPENDENTLY CONSTRUCTED. An earlier draft said
"the three stages are independent", which is the opposite of the paper's central argument -- integrity
constrains analysis and analysis constrains discovery, which is why the aggregate is a weakest link.
What is independent is the BENCHMARK's construction: each stage instantiates and scores its own worlds
on the same substrate, and no perturbation propagates from one stage to the next. A reader who sees
L1, L2 and L3 counts on one row will otherwise assume a single defect travelling down the chain.

EVERY NUMBER IS DERIVED. Counts come from the extracted CSVs, never from a literal here; the L3 route
split is the one authored constant and it is ASSERTED against the world list in fig_data_l3.csv, so a
new or renamed world fails the build instead of being silently miscounted. The initial physics
extension (orbital and oscillations) is reported separately in the appendix and appears in neither
final_scores.json nor fig_data_levels.csv. Provisional calorimetry and nuclear-decay directories are
also outside the paper registry. This figure therefore draws only the frozen life-science core.

AUTHORED AT FINAL SIZE: 5.5 in wide, primary text >= 7.5 pt, secondary >= 6.0 pt.

Caption draft, kept here so figure and caption stay in sync:

    Figure 2: Scientific scope and controlled intervention coverage in DISCERN -- THE FROZEN
    MOLECULAR-LIFE-SCIENCE CORE. The initial two-track physics extension is reported separately in
    the appendix. (A) The eight real-data tracks, grouped by biological organisation, each with its
    substrate and its task count at the three stages (L1 integrity, L2 analysis, L3 discovery). The
    scientific stages form a DEPENDENT CHAIN -- integrity constrains analysis, analysis constrains
    discovery -- but DISCERN constructs and scores stage-specific worlds INDEPENDENTLY: no
    perturbation propagates between stages. (B) How those tasks divide into controls and
    controlled interventions. Controls -- worlds an agent should pass through unchanged -- are 8 of 79
    at L1, 24 of 102 at L2 and 8 of 22 at L3; a benchmark made only of perturbed worlds
    would reward reflexive suspicion, so clean and boundary worlds are part of the measurement. At L1
    the 71 challenges span 65 distinct task types, and "challenge" rather than "defect" because not all
    are damage: several are conditions a competent analyst must recognise and handle, such as a
    heavy-atom X-ray structure carrying no hydrogens. Table A2 subdivides them further than there is
    room for here. At L2 the pressure is on the analysis rather
    than the data: 34 of the 78 perturbed worlds are tool- or procedure-output traps in which the
    software succeeds and returns something invalid. At L3 the 14 counterfactuals split by ROUTE: a
    NATIVE world's surprising value is really in the data, whereas an INJECTED world modifies an
    upstream quantity and re-runs the real scorer, which is what lets a conflict be placed where a
    prior is known to be held. GWAS, as one worked example across the three independent stages: L1
    presents allele frequencies on a percentage scale where 0-1 is required; L2 runs a TWAS that
    completes and returns 12k genes after matching almost no model SNPs; L3 presents an internally
    consistent TGFB1 sign inversion against a held prior. The complete registries -- every L1 world,
    every L2 world, every L3 dossier with its grounding -- are Tables T05-T07.

Run: .venv_bench/bin/python fig13_scope_atlas.py
"""
import collections
import textwrap
import matplotlib.pyplot as plt
import fig_common as C

# ---- scientific hierarchy: the one authored structure in panel A ---------------------------------
# (domain, [(track_display, substrate one-liner), ...]). Substrates are the analysed material, phrased
# as a reader of the track would name it; the full citation lives in the appendix inventory.
DOMAINS = [
    ("Statistical &\nclinical genetics", [
        ("GWAS", "cystic-fibrosis GWAS"),
        ("ClinVar", "variant records + VCF"),
    ]),
    ("Transcriptomics &\ncellular genomics", [
        ("Bulk RNA", "COVID-19 PBMC RNA-seq"),
        ("scRNA", "10x PBMC scRNA-seq"),
    ]),
    ("Functional &\nregulatory genomics", [
        ("CRISPR", "genome-wide KO, HAP1"),
        ("Enhancer", "primate enhancer MPRA"),
        ("Histone", "K562 ChIP-seq + RNA-seq"),
    ]),
    ("Protein\nbiophysics", [
        ("Protein", "GB1 stability DMS + PDB"),
    ]),
]

# ---- L3 route: the one authored constant in panel B, asserted against the shipped world list ------
# Authority is L3_AS_BUILT.md. NATIVE = the surprising value is really in the data, nothing modified.
# INJECTED = an upstream quantity is modified and the REAL scorer re-run. The distinction is not
# cosmetic: it decides what a world's grounding citation has to be (a phenomenon vs a coherence
# argument), so miscounting it here would misdescribe the benchmark's evidence base.
INJECTED = {"cf_GSTM1", "cf_TGFB1", "cf_FH", "cf_LFS", "cf_tmprss15_essential",
            "cf_confounded", "cf_bivalent_injected", "cf_mhc2_injected"}

STAGE = {"L1": "#255E92", "L2": "#CE8A2E", "L3": "#2A7A50"}
# Hue = stage (as Figure 3), intensity = class within the stage. The control segment is always the
# lightest, never a grey: it is a measured condition, not an absence of one.
CLASS_RAMP = {
    "L1": {"clean control": "#DCE8F3", "challenge": "#255E92"},
    "L2": {"clean control": "#FAEBD3", "statistical trap": "#E9B96B", "tool / procedure trap": "#CE8A2E",
           "data confound": "#8A5A0E"},
    "L3": {"real control": "#D8EAE0", "native counterfactual": "#6FAE8C", "injected counterfactual": "#2A7A50"},
}
FS_TRACK, FS_SUB, FS_NUM, FS_DOM, FS_PANEL, FS_SEG, FS_KEY = 7.8, 6.4, 7.5, 7.5, 8.4, 6.6, 6.8
# Secondary lines are wrapped to a MEASURED width: DejaVu Sans at 6.8 pt runs ~17.8 chars/in, so
# 5.5 in is 96 characters. An unmeasured 128 emitted the figure at 6.35 in, over the 5.50 gate,
# and pinning these lines at XD pushed them a further 1.1 in right.
WRAP_KEY = 96

# ---- derive every count --------------------------------------------------------------------------
l1 = C.load("fig_data_l1.csv")
l2 = C.load("fig_data_l2.csv")
l3 = C.load("fig_data_l3.csv")
m0 = C.MODEL_ORDER[0]

l1_worlds = {(r["track_display"], r["world"]): r for r in l1 if r["model"] == m0}
l2_worlds = {(r["track_display"], r["family"], r["world"]): r for r in l2}
l3_worlds = {(r["track_display"], r["world"]): r for r in l3}

TRACKS = [t for _, ts in DOMAINS for t, _ in ts]
count = {t: (sum(1 for k in l1_worlds if k[0] == t),
             sum(1 for k in l2_worlds if k[0] == t),
             sum(1 for k in l3_worlds if k[0] == t)) for t in TRACKS}
assert set(TRACKS) == {k[0] for k in l1_worlds}, "panel A track list is not the shipped track list"

# L1 classes come from the REGISTRY, which reads each world's `issue_present` flag, rather than being
# re-derived here from the world name. Two places deriving one classification two ways is how they come
# to disagree, and the name heuristic was wrong about what these worlds ARE even where it happened to
# count them correctly.
_reg = [r for r in C.load("world_registry.csv") if r["level"] == "L1"]
_c1 = collections.Counter(r["class"] for r in _reg)
n_clean1, n_bound1 = _c1["clean control"], _c1["boundary case"]
n_def1 = _c1["controlled integrity challenge"]
# Distinct types over the MERGED challenge set (boundary + challenge), because that is the set panel B
# now shows as one segment. 58 was the challenge-only count and would have under-described the 71.
# The merged figure is 65, which is exactly F12's "65 distinct non-clean world types" -- the two
# figures describe the same object, and if they ever disagree one of them has drifted.
n_types1 = len({r["world"] for r in _reg if r["class"] != "clean control"})
assert n_clean1 + n_bound1 + n_def1 == len(l1_worlds), "registry and scored L1 world sets disagree"

L2_CLASS = {"none": "clean control", "data-confound": "data confound",
            "tool-trap": "tool / procedure trap", "statistical": "statistical trap"}
c2 = collections.Counter(L2_CLASS[r["issue_type"]] for r in l2_worlds.values())

cf = {k[1] for k, r in l3_worlds.items() if r["is_counterfactual"]}
assert INJECTED <= cf, f"authored INJECTED names not in the shipped worlds: {INJECTED - cf}"
c3 = {"real control": len(l3_worlds) - len(cf),
      "native counterfactual": len(cf - INJECTED), "injected counterfactual": len(INJECTED)}

# TWO L1 SEGMENTS IN THE MAIN PAPER, THREE IN THE APPENDIX. The registry keeps clean / boundary /
# challenge apart because the GRADER does: each has its own non-overlapping outcome vocabulary --
# CLEAN-CORRECT|OVER-CAUTIOUS|FALSE-UNUSABLE for a clean control, ABSTAIN-RECOGNIZED|ABSTAIN-OK|
# OVER-DIAGNOSE for a boundary world, DIAGNOSE-AND-ACT|NOTICE-WRONG|MISS for a challenge. There is no
# room to explain that here, so the two non-clean classes merge.
#
# They merge into CHALLENGE, not into the controls, and the data decides that: a boundary world carries
# is_clean=False, the same flag Figure 4A uses to split L1 clean-vs-injected, and Figure 4B's "48 clean
# controls" is 8 worlds x 6 models with boundary excluded. Folding boundary into the controls here
# would contradict both. It is also the right reading -- the agent must DO something in a boundary
# world, recognise that something is unusual and retain the data anyway, which is exactly what a clean
# control does not ask of it. T05 keeps all three; 71 = 7 boundary + 64 challenge.
COMP = {"L1": {"clean control": n_clean1, "challenge": n_bound1 + n_def1},
        "L2": dict(c2), "L3": c3}

# ---- layout ---------------------------------------------------------------------------------------
FIG_W, UNIT_IN = 5.5, 6.21
NCOL = max(len(ts) for _, ts in DOMAINS)
XD = 0.234                                   # domain-label column: "regulatory genomics" needs 1.22 in
                                             # at 7.5 pt bold; 0.205 ran it under the CRISPR card
CGAP = 0.008
CW = (1.0 - XD - (NCOL - 1) * CGAP) / NCOL   # cards fill the row exactly; nothing runs off the canvas
PAD = 0.010                                  # card inner padding, left and right
# Line heights in axes fractions. 1 in = 1/UNIT_IN = 0.161 units, and a line of n pt needs about
# 1.33 n/72 in, so a 6.4 pt line is 0.0190 units. Hard-won: tab01 once used a line height SMALLER
# than the glyph, and every wrapped line overlapped the next.
LH_NAME, LH_SUB, LH_NUM = 0.0180, 0.0160, 0.0175
CPI_SUB = 19.0                               # chars per inch, DejaVu Sans at 6.4 pt (measured)
# Substrates are written to fit ONE line at this width. Each extra wrapped line costs 0.10 in in
# every one of the four bands, and this figure competes for main-text space with the results.
WRAP_SUB = int((CW - 2 * PAD) * FIG_W * CPI_SUB)

fig, ax = plt.subplots(figsize=(FIG_W, UNIT_IN))
ax.set_position([0, 0, 1, 1]); ax.axis("off"); ax.patch.set_visible(False)
ax.set_xlim(0, 1)

y = 1.0
ax.text(0.0, y, "Scientific scope and controlled intervention coverage in DISCERN",
        fontsize=9.6, fontweight="bold", color=C.INK, va="top")

y -= 0.020
ax.plot([0, 1], [y] * 2, color=C.INK2, lw=1.0)

# ---- panel A ---------------------------------------------------------------------------------------
y -= 0.017
ax.text(0.0, y, "A   Eight real-data tracks, by biological organisation", fontsize=FS_PANEL,
        fontweight="bold", color=C.INK, va="top")
# The panel covers biology only while the paper claims two domains, so the figure names the checkpoint
# rather than leaving a reader to infer that physics is missing. It sits on the panel-A heading line,
# not the title line, where it overprinted the title.
ax.text(1.0, y, "frozen molecular-life-science checkpoint", fontsize=FS_KEY, color=C.INK3,
        va="top", ha="right")
y -= 0.016
ax.text(0.0, y, "substrate, then tasks separately instantiated at   ·   "
        "L1 integrity · L2 analysis · L3 discovery", fontsize=FS_KEY, color=C.INK3, va="top")
y -= 0.012

# Every card in a domain row is drawn to the SAME height, set by the longest substrate in that row,
# so the row reads as one band rather than a ragged set of boxes.
wrapped = {t: textwrap.wrap(sub, WRAP_SUB) for _, ts in DOMAINS for t, sub in ts}
for dom, tracks in DOMAINS:
    y -= 0.007
    top = y
    nl = max(len(wrapped[t]) for t, _ in tracks)
    card_h = 0.009 + LH_NAME + nl * LH_SUB + 0.005 + LH_NUM + 0.006
    ax.text(0.0, top - 0.006, dom, fontsize=FS_DOM, fontweight="bold", color=C.INK2, va="top",
            linespacing=1.35)
    for ci, (t, _) in enumerate(tracks):
        x = XD + ci * (CW + CGAP)
        ax.add_patch(plt.Rectangle((x, top - card_h), CW, card_h, facecolor="#F7F9FB",
                                   edgecolor=C.GRID, lw=0.7))
        ty = top - 0.009
        ax.text(x + PAD, ty, t, fontsize=FS_TRACK, fontweight="bold", color=C.INK, va="top")
        ty -= LH_NAME
        for ln in wrapped[t]:
            ax.text(x + PAD, ty, ln, fontsize=FS_SUB, color=C.INK3, va="top")
            ty -= LH_SUB
        # the three counts sit on one baseline, each in its own stage colour: the row IS the chain
        cx = x + PAD
        for L, n in zip(("L1", "L2", "L3"), count[t]):
            ax.text(cx, top - card_h + 0.007, f"{L} {n}", fontsize=FS_NUM, color=STAGE[L],
                    fontweight="bold", va="baseline")
            cx += 0.074            # 0.058 was narrower than "L2 17" at 7.5 pt bold, so the three
                                   # stage counts ran together into one unreadable string
    y = top - card_h

# ---- panel B ---------------------------------------------------------------------------------------
y -= 0.020
ax.plot([0, 1], [y] * 2, color=C.GRID, lw=0.7)
y -= 0.017
ax.text(0.0, y, "B   Controls and controlled interventions, per stage", fontsize=FS_PANEL,
        fontweight="bold", color=C.INK, va="top")
y -= 0.016
ax.text(0.0, y, "bar width is proportional to the number of worlds; the lightest segment is the control",
        fontsize=FS_KEY, color=C.INK3, va="top")
y -= 0.012

BAR_X, BAR_W, BAR_H = XD, 1.0 - XD, 0.030
STAGE_TOTAL = {L: sum(COMP[L].values()) for L in ("L1", "L2", "L3")}
WIDEST = max(STAGE_TOTAL.values())
for L in ("L1", "L2", "L3"):
    y -= 0.010
    order = list(CLASS_RAMP[L])                       # control first, then increasing intervention
    tot = STAGE_TOTAL[L]
    ax.text(0.0, y - BAR_H / 2, f"{L}   n = {tot}", fontsize=FS_NUM, color=STAGE[L],
            fontweight="bold", va="center")
    # bars share ONE scale across stages, so L3's 22 worlds cannot look like L1's 79
    x = BAR_X
    for cls in order:
        n = COMP[L].get(cls, 0)
        if not n:
            continue
        w = BAR_W * n / WIDEST
        ax.add_patch(plt.Rectangle((x, y - BAR_H), w, BAR_H, facecolor=CLASS_RAMP[L][cls],
                                   edgecolor="white", lw=0.8))
        dark = order.index(cls) >= (2 if L == "L2" else 1)
        if w > 0.030:
            ax.text(x + w / 2, y - BAR_H / 2, str(n), fontsize=FS_SEG,
                    color="white" if dark else C.INK, ha="center", va="center", fontweight="bold")
        x += w
    y -= BAR_H + 0.004
    # the class names go UNDER the bar, not in a legend: three stages have three different class sets,
    # so a shared legend would have nine entries and none of them would be attached to its stage
    key = "   ·   ".join(f"{cls} {COMP[L].get(cls, 0)}" for cls in order if COMP[L].get(cls, 0))
    ax.text(BAR_X, y, key, fontsize=FS_KEY, color=C.INK3, va="top")
    y -= 0.014

y -= 0.008
ax.plot([0, 1], [y] * 2, color=C.INK2, lw=1.0)
y -= 0.015
foot = (f"{sum(STAGE_TOTAL.values())} canonical tasks over 8 tracks. "
        f"The {n_bound1 + n_def1} L1 challenges span {n_types1} distinct task types. "
        f"The scientific stages form a DEPENDENT CHAIN, but DISCERN constructs and "
        f"scores stage-specific worlds INDEPENDENTLY: perturbations do not propagate between stages. "
        f"Complete registries: "
        f"Tables T05 (L1), T06 (L2), T07 (L3).")
for i, ln in enumerate(textwrap.wrap(foot, WRAP_KEY)):
    ax.text(0.0, y - i * 0.0155, ln, fontsize=FS_KEY, color=C.INK2, va="top")
y -= len(textwrap.wrap(foot, WRAP_KEY)) * 0.0155 + 0.006

ax.set_ylim(y, 1.0)
fig.set_size_inches(FIG_W, UNIT_IN * (1.0 - y))

rows = [{"panel": "A", "domain": dom.replace("\n", " "), "track": t, "substrate": sub.replace("\n", " "),
         "n_l1": count[t][0], "n_l2": count[t][1], "n_l3": count[t][2]}
        for dom, ts in DOMAINS for t, sub in ts]
rows += [{"panel": "B", "level": L, "intervention_class": cls, "n_worlds": COMP[L].get(cls, 0),
          "stage_total": STAGE_TOTAL[L]}
         for L in ("L1", "L2", "L3") for cls in CLASS_RAMP[L] if COMP[L].get(cls, 0)]
C.save(fig, "F13_scope_atlas", rows,
       ["panel", "domain", "track", "substrate", "n_l1", "n_l2", "n_l3", "level",
        "intervention_class", "n_worlds", "stage_total"])
print(f"   L1 {n_clean1}c/{n_bound1}b/{n_def1}d ({n_types1} types) · L2 {dict(c2)} · L3 {c3}")
