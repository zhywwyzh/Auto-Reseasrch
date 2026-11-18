"""Figure 7 -- evidence -> hypothesis -> criticism -> test, on three OBJECTIVELY SELECTED cases.

WHY THESE THREE, and the selection rule is stated so nobody has to trust that attractive transcripts
were not cherry-picked. Each case is the ARGMAX of a pre-stated criterion over the 130
aggregate-eligible L3 outcomes:

  1. HIGHEST COMPLETE RESULT           protein_ddg / cf_stabilizing / claude-opus-5   D=3 Q=3.0 N=3
     the only outcome scoring 3 on every one of D, Q and N.
  2. STRONGEST CROSS-MODEL HOTSPOT     hist_gene_exp / cf_bivalent_native / deepseek  D=3 Q=2.6 N=3
     the world where novelty concentrates: 3 of the benchmark's 4 N=3 outcomes are on it.
  3. HIGHEST REAL-WORLD COMMITMENT     enhancer_activity / real / claude-opus-5       D=3 Q=2.6 N=2
     the best committed result on a REAL world, so the figure is not three constructed inversions.

Case 3 earns its place by being the one that does NOT claim a discovery. Its family ranks 1/141 within
the pre-specified partition (permutation p=0.0102) yet does not clear the genome-wide family-wise max
null, and the final answer says exactly that. If the paper's claim is "guide a human toward discovery",
the calibrated non-discovery is the load-bearing example, not the two flips.

THE RED LINE IS THE POINT. Reviewer robustness is graded as a number on the Q axis, and a number cannot
show whether a model retreated on the right thing. Printing what each model WITHDREW after adversarial
review makes that visible: an unsupported geometric claim, an over-strong chromatin label, and a trend
read out of noise. All three retreats are correct, and none of them abandons the underlying finding.

SOURCE. The three transcripts named in the panel footers, read directly -- `versions[0]` is the initial
claim and `versions[-1]` the final one, with the reviewer critiques in `rounds[*]['critiques']`. Every
number printed here is quoted from those files.

LANGUAGE. "Valid novelty UNDER THE BENCHMARK RUBRIC". Whether any of this is novel to the field needs a
blinded prior-art audit that has not been run, and DUSP4 in particular may be a new application of a
known chromatin principle rather than a new principle.

Caption draft, kept here so figure and caption stay in sync:

    Figure 7: Evidence to hypothesis to criticism to test, on three cases selected by pre-stated rules
    rather than by inspection: the only outcome scoring 3 on all of D, Q and N; the world carrying 3 of
    the benchmark's 4 N=3 outcomes; and the best committed result on a real (non-counterfactual) world.
    Each row follows the same grammar, and the red line names what the model WITHDREW after three rounds
    of adversarial review -- a claim the reviewer-robustness score records only as a number. The third
    case is the one that declines to claim a discovery: the family ranks 1/141 within its pre-specified
    partition but does not clear the genome-wide null, and the final answer says so and proposes the
    experiment that would settle it.

Run: .venv_bench/bin/python fig07_case_studies.py
"""
import textwrap
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import fig_common as C

# 5.5 in, like every other float. ICLR's template is SINGLE-COLUMN (\textwidth 5.5 in) and `figure*`
# does not create a wider region, so an earlier 6.95 in build would have been scaled to 79% and its
# 7.5 pt body would have rendered at 5.9 pt. Fitting the column meant changing the LAYOUT, not the type:
# the six stages run 2 wide x 3 deep per case instead of 3 wide x 2 deep, which doubles the characters
# per line at the same point size.
FIG_W = 5.42
STAGE = ["prior expectation", "observed evidence", "initial claim",
         "reviewer challenge", "final bounded claim", "discriminating test"]
TONE = {0: "#5E6B73", 1: "#20618F", 2: "#20618F", 3: "#8A5A0C", 4: "#1B6B50", 5: "#1B6B50"}

CASES = [
    dict(title="GB1 buried-position stabilization",
         meta="protein_ddg · cf_stabilizing · Claude Opus 5 · D=3  Q=3.0  N=3",
         rule="highest complete result: the only outcome scoring 3 on D, Q and N",
         box=["Large aromatics buried in a packed core destabilize. L5F expected ΔΔG < 0.",
              "L5F ΔΔG = +1.82 — 3rd of 1064 mutations, 99.7th pct. All 17 buried stabilizing "
              "mutations sit at 4 of the 9 buried positions.",
              "Two packing regimes: L5/L7/V54 line one contiguous 'unsaturated' aliphatic "
              "micro-cavity; ΔΔG set by a three-term volume rule.",
              "Contiguity is asserted, not shown. The volume-correlation classifier has bootstrap "
              "CIs too wide to separate sites (pos5 r=0.36 [−0.52, 0.89]).",
              "Four mechanistically distinct site classes, classified by the SIGN of sub-wild-type "
              "volume substitutions — categorical, with CIs reported.",
              "Combinatorial L5F / L7W / V54F double and triple mutants, with double-mutant "
              "epistasis controls."],
         withdrawn="withdrew: the single contiguous cavity, and volume correlation as the classifier",
         src="tracks/protein_ddg/L3/results/l3_run/out_cf_stabilizing_claude-opus-5.json"),
    dict(title="DUSP4 bivalent promoter",
         meta="hist_gene_exp · cf_bivalent_native · DeepSeek V4 Pro · D=3  Q=2.6  N=3",
         rule="novelty hotspot: 3 of the benchmark's 4 N=3 outcomes are on this world",
         box=["Strong promoter H3K4me3 means the gene is expressed.",
              "H3K4me3 log2 3.98 (81st pct) WITH H3K27me3 1.22 over ±10 kb (97th pct), and mRNA "
              "0.49 against a panel median of 2.04.",
              "DUSP4 is bivalent and PRC2/H3K27me3-repressed; EZH2 inhibition will de-repress it.",
              "A ±10 kb window cannot establish promoter co-occupancy, so 'bivalent' claims more "
              "than the measurement supports.",
              "A provisional, threshold-defined bivalent-LIKE state — 1 of only 3/4081 genes meeting "
              "both thresholds; other repressors and a poised state left open.",
              "Locus-specific H3K27me3 ChIP-qPCR / CUT&RUN at the DUSP4 TSS, plus an EZH2-inhibition "
              "time course with matched controls."],
         withdrawn="withdrew: unqualified 'bivalent', and promoter co-occupancy as established",
         src="tracks/hist_gene_exp/L3/results/l3_run/out_cf_bivalent_native_deepseek-v4-pro.json"),
    dict(title="Hominoid enhancer gain  (a REAL world)",
         meta="enhancer_activity · real · Claude Opus 5 · D=3  Q=2.6  N=2",
         rule="best committed result on a real world — not a constructed inversion",
         box=["None available: the element is a bare coordinate, so there is no per-fact textbook "
              "expectation to overturn.",
              "All 5 apes exceed all 5 monkeys with no overlap; contrast 2.52. Species genome-wide "
              "medians sit within a 0.30 band, so not an assay offset.",
              "A single saltatory activity gain on the hominoid stem, since partially and "
              "monotonically attenuated along the African-ape lineage.",
              "'Monotonic attenuation' reads a trend out of noise, and a single outgroup cannot "
              "polarize the change.",
              "A within-family CANDIDATE only: permutation p=0.0102, rank 1/141, but 2.519 does not "
              "clear the genome-wide max null (mean 2.91, p95 3.66) — it would fail a genome-wide "
              "screen. Polarity rests on one outgroup.",
              "Ancestral-sequence reconstruction of the hominoid-stem allele, plus a species-swap "
              "MPRA."],
         withdrawn="withdrew: the attenuation trend, and the discovery framing itself — replaced by "
                   "a stated candidate",
         src="tracks/enhancer_activity/L3/results/l3_run/out_real_claude-opus-5.json"),
]

BW, BGAP = 0.484, 0.022
FS_BODY, FS_STAGE, FS_TITLE = 7.5, 7.5, 8.6
CH = 0.0094                                  # one wrapped body line, in axes fraction
WRAP = 44                                    # characters per line inside a box at FS_BODY

fig, ax = plt.subplots(figsize=(FIG_W, 9.0))
ax.set_position([0, 0, 1, 1]); ax.axis("off"); ax.patch.set_visible(False)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)

y = 0.995
for ci, case in enumerate(CASES):
    # Three header lines per case cost 0.45 in of a figure that has to leave room for a caption inside
    # ICLR's ~9 in text height. Title and identity share a line; the selection rule keeps its own,
    # because it is the claim that these cases were not cherry-picked and must stay legible.
    y -= 0.019
    ax.text(0.004, y, f"{ci + 1}.  {case['title']}", fontsize=FS_TITLE, fontweight="bold",
            color=C.INK, va="top")
    # RIGHT-aligned, and the track name dropped from the string: the transcript path at the foot of
    # each case already names the track, and a left-aligned meta at a fixed x collided with case 3's
    # longer title while pushing the emitted width past 5.5 in.
    ax.text(0.996, y + 0.0015, case["meta"].split(" · ", 1)[1], fontsize=7.5, color=C.INK2,
            va="top", ha="right")
    y -= 0.0145
    ax.text(0.004, y, f"selection rule — {case['rule']}", fontsize=7.5, color=C.INK3,
            style="italic", va="top")
    y -= 0.009

    # 2 wide x 3 deep. Reading order is left-to-right then down, so the grammar still runs
    # prior -> evidence -> claim -> challenge -> final -> test.
    for band in (0, 1, 2):
        cols = [textwrap.wrap(case["box"][band * 2 + k], WRAP) for k in range(2)]
        bh = max(len(c) for c in cols) * CH + 0.014
        y -= bh + 0.0155                      # room for the stage label above each box
        for k in range(2):
            si = band * 2 + k
            x = 0.004 + k * (BW + BGAP)
            ax.text(x + 0.004, y + bh + 0.003, STAGE[si], fontsize=FS_STAGE, color=TONE[si],
                    fontweight="bold", va="bottom")
            ax.add_patch(FancyBboxPatch((x, y), BW, bh,
                                        boxstyle="round,pad=0.001,rounding_size=0.004",
                                        facecolor="#FBFCFD", edgecolor=TONE[si], linewidth=0.7))
            for li, ln in enumerate(cols[k]):
                ax.text(x + 0.007, y + bh - 0.008 - li * CH, ln, fontsize=FS_BODY, color=C.INK,
                        va="center")
            if k == 0:
                ax.annotate("", xy=(x + BW + BGAP - 0.004, y + bh / 2), xytext=(x + BW + 0.004,
                                                                               y + bh / 2),
                            arrowprops=dict(arrowstyle="-|>", color=C.INK3, lw=0.8))
        if band < 2:                           # wrap-around into the next band
            # Kept hard left and clear of the next band's stage label, which starts at x=0.008.
            ax.annotate("", xy=(-0.006, y - 0.013), xytext=(-0.006, y + 0.002),
                        arrowprops=dict(arrowstyle="-|>", color=C.INK3, lw=0.8))

    y -= 0.0145
    ax.plot([0.004, 0.030], [y + 0.003] * 2, color="#B03A2E", lw=1.4)
    ax.text(0.036, y + 0.003, case["withdrawn"], fontsize=7.5, color="#B03A2E", va="center")
    y -= 0.0105
    ax.text(0.004, y, case["src"], fontsize=6.4, color=C.INK3, va="top", family="DejaVu Sans")
    y -= 0.0135
    if ci < len(CASES) - 1:
        ax.plot([0, 1], [y] * 2, color=C.GRID, lw=0.7)

_bot = y - 0.004
ax.set_ylim(_bot, 1.0)
fig.set_size_inches(FIG_W, 9.0 * (1.0 - _bot))

C.save(fig, "F07_case_studies",
       [{"case": c["title"], "selection_rule": c["rule"], "identity": c["meta"], "stage": STAGE[i],
         "content": c["box"][i], "withdrawn_after_review": c["withdrawn"] if i == 5 else "",
         "transcript": c["src"] if i == 5 else ""}
        for c in CASES for i in range(6)],
       ["case", "selection_rule", "identity", "stage", "content", "withdrawn_after_review",
        "transcript"])
