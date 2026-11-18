"""Table 1 -> APPENDIX inventory: every track, every stage, in full, with its L3 grounding.

WHY THE FORM CHANGED. This was a one-row-per-track grid whose L1/L2 cells named two representative
families and closed with an ellipsis, because at 5.5 in a five-column grid cannot hold more. Moving it
to the appendix removes the reason for the ellipsis, so the table is now STACKED BLOCKS: one block per
track, each carrying the FULL task-family list plus a new fourth field, the L3 GROUNDING REFERENCE.

A stacked block is also the right shape for a table that is still growing. Adding a track means
appending a TRACKS entry and naming its domain; nothing re-flows, nothing has to be re-truncated, and
the width never changes. A grid would have to lose a column or shrink its type with every new domain.

THIS IS THE TRACK OVERVIEW, NOT THE TASK REGISTRY. Its L1 and L2 fields name task FAMILIES, which is
what fits at this width; every individual world, with what it does and what response it expects, is in
T05 (all 79 L1 worlds), T06 (all 102 L2 worlds) and T07 (all 22 L3 dossiers). The design constraints
those tables serve are T08. This table exists to be read in one sitting; those exist to be looked up.

THE GROUNDING FIELD IS THE POINT OF THE REWRITE. The paper's claim is that DISCERN instantiates
DOCUMENTED failure modes on real data rather than inventing puzzles, and that claim is only as good as
the per-world citation. Bibliographic identities and PMIDs were verified against PubMed where
applicable on 2026-08-29; non-PubMed primary-source records were checked separately. Every reference
was matched to the world that actually SHIPPED, not merely to the design; the authority is
`L3_DESIGN.md` -> "L3 GROUNDING -- VERIFIED AGAINST WHAT SHIPPED", and the two kinds of
counterfactual are distinguished there:

  * NATIVE counterfactual  -> a PHENOMENON citation: the surprising value is really in the data.
  * INJECTED counterfactual -> an INJECTION-DESIGN citation: the state is constructed, so what must be
    grounded is coherence (the modified quantity moves as a real biological unit moves), not a claim
    that the injected state has been observed.

Demanding a published observation of an injected state would be asking for the wrong object, which is
why `cf_mhc2_injected` is cited on CIITA module architecture rather than on a COVID finding.

NAMES DESCRIBE THE ANALYSIS, NOT ITS FAILURE MODE: "TWAS harmonization" is the task; the silent failure
is what the world injects into it. ESM-2 gives an uncalibrated stability proxy, so the text says
"stability scoring" rather than implying calibrated ddG. "cf" is never used for cystic fibrosis, because
the paper uses cf for counterfactual. The enhancer substrate is called "primate enhancer orthologs"
because the analysed table records n_species = 10 while the source metadata says 11.

AUTHORED AT FINAL SIZE: 5.5 in wide, every glyph >= 7.5 pt, canvas sized to the drawn content.

Caption draft, kept here so table and caption stay in sync:

    Table A1: The DISCERN track inventory. One block per real-data track, grouped by biological
    organisation, giving the substrate, the L1 and L2 task-family lists, the L3 evidence-expectation
    conflict, and the published work that grounds it. Families are named here; the per-world detail is
    Tables A2-A4 (T05-T07). Grounding is of two kinds: a NATIVE counterfactual cites the PHENOMENON it
    instantiates, while an INJECTED one cites the regulatory architecture that makes the injection
    coherent -- it does not claim the constructed state has been observed. Eight tracks yield 203
    canonical tasks: 79 at L1 (64 controlled integrity challenges, 7 boundary cases carrying no issue
    at all, 8 clean controls, spanning 58 distinct task types; class is read from each world's
    issue_present flag), 102 at L2 across 24 analysis families, and 22 L3
    dossiers (8 real, 14 counterfactual). Across the six-model roster that is 1,218 resolved
    task-model outcomes, of which 1,217 were graded; one was excluded by the prior-admissibility gate
    because Claude Opus 5 did not hold the prior the bulk_rnaseq cytokine counterfactual exists to
    contradict, which is a measurement of its prior rather than missing data. Grounding is tagged by
    KIND, and the tag follows the counterfactual's ROUTE: GWAS, ClinVar and CRISPR's
    cf_tmprss15_essential are injected worlds, so their references are marked [injection design] even
    though each cites a documented phenomenon -- what an injected world has to ground is coherence.
    The ClinVar, scRNA and Histone substrate lines were added and PubMed-verified 2026-08-30. What
    each stage measures is given in
    Figure 2; the scope overview is Figure 13.

Run: python tab01_coverage.py
"""
import collections
import textwrap
import matplotlib.pyplot as plt
import fig_common as C

FIG_W = 5.5
UNIT_IN = 6.21
FS_TRACK, FS_LAB, FS_BODY, FS_REF, FS_NUM = 8.2, 7.5, 7.5, 7.5, 7.5
STAGE = {"L1": "#255E92", "L2": "#CE8A2E", "L3": "#2A7A50"}

# One entry per track. To add a domain (the physics tracks are next), append here: nothing else moves.
#   (display, substrate, L1 families, L2 families, L3 conflict, [(grounding line, kind), ...])
# kind: "phenomenon" = a native world instantiating documented biology · "injection" = a constructed
#       world grounded on coherence · "substrate" = where the data came from.
# Three substrate lines that this table previously lacked entirely, while GWAS, CRISPR, Enhancer,
# Protein and Bulk RNA all carried one. Added and verified against PubMed 2026-08-30.
CLINVAR_SUB = ("ClinVar: Landrum MJ et al., Nucleic Acids Res 2018;46:D1062, PMID 29165669",
               "substrate")
SCRNA_SUB = ("10x Genomics pbmc3k: Zheng GXY et al., Nat Commun 2017;8:14049, PMID 28091601",
             "substrate")
HIST_SUB = ("ENCODE K562 ChIP-seq + RNA-seq: ENCODE Project Consortium, Nature 2012;489:57, "
            "PMID 22955616", "substrate")

TRACKS = [
    ("GWAS", "cystic fibrosis lung-disease severity, GWAS Catalog GCST003143",
     "clean · duplicate rows · beta outlier · EAF-scale mismatch · impossible values · invalid alleles · "
     "versioned-ID duplicates · effect-sign swap · high-MAF palindromic SNPs · metadata reconciliation",
     "GWAS signal diagnostics · locus analysis · TWAS variant harmonization (a plausible TWAS result "
     "produced from almost no matched model SNPs)",
     "real control · cf_GSTM1: deleterious direction · cf_TGFB1: protective direction",
     [("Corvol et al., Nat Commun 2015, PMID 26417704", "substrate"),
      ("Gerlach, Milind, Spence & Pritchard, bioRxiv 2025 — TWAS effect SIGNS are unreliable at a "
       "measurable rate, which is what makes an injected sign inversion coherent", "injection")]),
    ("ClinVar", "ClinVar records + patient VCF",
     "clean · low coverage · strand bias · contamination · genome-build mismatch · AF-scale mismatch · "
     "duplicate variants · metadata reconciliation · reference validation · VUS abstention",
     "ACMG classification · prioritisation · secondary findings",
     "real control · cf_FH: APOB supported over the LDLR anchor · cf_LFS: a non-classic partner supported "
     "over the TP53 anchor",
     [CLINVAR_SUB,
      ("NEJM 2016, PMID 27532831 · JAMA 2018, PMID 30264118 — published classifications get "
       "reclassified, so a wrong upstream call is the documented state these worlds construct",
       "injection")]),
    ("scRNA", "10x PBMC scRNA-seq (pbmc3k)",
     "clean · empty droplets · high mitochondrial fraction · high hemoglobin · doublets · ambient RNA · "
     "feature-type contamination · count-complexity anomaly · metadata reconciliation · low-RNA boundary",
     "cell-type annotation · marker-gene differential expression · composition confound (scanpy)",
     "real CD4-T control · cf_cd16_mono · cf_cd68_mono: canonical-marker discrimination changes by context",
     [SCRNA_SUB,
      ("Li et al., BMC Bioinformatics 2022, PMID 35831796 (sc2marker) — canonical markers are "
       "context-dependent, not absolute",
       "phenomenon")]),
    ("CRISPR", "genome-wide CRISPR-KO screen, HAP1 (TKOv3)",
     "clean · T$_0$ library skew · low coverage · replicate discordance · sample mislabel · control-guide "
     "integrity · guide-gene misannotation · clonal jackpot · index hopping · strong-signal boundary",
     "essentiality scoring · hit calling · screen context (BAGEL-style Bayes factor)",
     "real PRMT5 control · cf_ppan_dispensable (native) · cf_tmprss15_essential (injected)",
     [("Hart et al., G3 2017, PMID 28655737 — the CEGv2 / NEGv1 reference sets", "substrate"),
      ("De Kegel & Ryan, PLoS Genet 2019 · Dede et al., Genome Biol 2020 — never-essential genes are "
       "enriched for paralogs, so buffering masks essentiality", "phenomenon"),
      ("Hart et al., Cell 2015, PMID 26627737 — genotype-specific liabilities: fitness genes essential "
       "in some backgrounds and not others, which is what makes cf_tmprss15_essential coherent",
       "injection")]),
    ("Enhancer", "primate enhancer orthologs, cross-species MPRA",
     "clean · sequence-fetch failure · assembly-build mismatch · liftOver failure · coordinate offset · "
     "strand/reverse-complement inconsistency · duplicate-family leakage · sequence-length/span mismatch · "
     "repeat-rich boundary",
     "conservation · divergence · ranking across species",
     "real lineage-gain candidate · cf_confounded: injected species-batch offset in a flat family",
     [("Klein JC et al., Genome Biology 2018;19:99, PMID 30045748", "substrate"),
      ("Villar et al., Cell 2015, PMID 25635462 · Pollard et al., Nature 2006, PMID 16915236 — "
       "lineage-specific regulatory innovation is real", "phenomenon"),
      ("Ioannidis, Epidemiology 2008, PMID 18633328 — the top hit of a screen is the one most likely "
       "inflated, so the correct act is a calibrated candidate", "phenomenon"),
      ("Leek et al., Nat Rev Genet 2010, PMID 20838408 — a technical offset mimicking biology",
       "injection")]),
    ("Histone", "ENCODE K562 ChIP-seq (H3K4me3, H3K27me3, matched input) + RNA-seq",
     "clean · low signal-to-noise · missing input control · blacklist contamination · batch effect · "
     "duplicate samples · expression-unit error · metadata reconciliation · reference validation · "
     "antibody-efficiency abstention",
     "ChIP signal quantification · ranking · mark-expression regression",
     "real UFD1 control · cf_bivalent_native: DUSP4 · cf_bivalent_injected: ST13",
     [HIST_SUB,
      ("Bernstein et al., Cell 2006;125:315 · Voigt & Reinberg 2013 — bivalent domains are documented, "
       "and the poised state is reactivatable", "phenomenon")]),
    ("Protein", "GB1 deep mutational stability (Tsuboyama/Rocklin 2023) + structure",
     "clean · missing atoms · missing hydrogens · steric clash · unresolved altloc · multi-model ambiguity · "
     "heteroatom/ligand handling · non-standard residue · numbering reconciliation · flexible-region abstention",
     "ESM-2 stability scoring (an uncalibrated proxy, not calibrated ddG) · structural determinants of "
     "stability · stability classification",
     "real control · cf_stabilizing: a measured stabilizing mutation that ESM2-650M scores as destabilizing",
     [("Tsuboyama & Rocklin 2023 — measured ddG, PDB 1PGA / 2QMT", "substrate"),
      ("native measured reversal in the substrate; DISCERN's audit observes that 0 of 17 buried stabilizing "
       "mutations receives a positive ESM2 LLR (a benchmark observation, not a source-paper claim)",
       "phenomenon")]),
    ("Bulk RNA", "COVID-19 PBMC RNA-seq, GEO GSE152418",
     "clean · library-size outlier · unfiltered low-count genes · rRNA-depletion failure · globin "
     "contamination · RNA degradation · gDNA contamination · sample-sex swap · metadata reconciliation · "
     "divergent-sample boundary",
     "differential expression (PyDESeq2) · GSEA · library structure",
     "real ISG control · cf_cytokine_flip (native) · cf_mhc2_injected (injected)",
     [("Arunachalam et al., Science 2020, PMID 32788292", "substrate"),
      ("Hadjadj 2020 Science · Mann 2020 Sci Immunol · Schulte-Schrepping 2020 Cell — monocyte "
       "immunoparalysis: cytokines suppressed in blood while ISGs rise", "phenomenon"),
      ("Meissner et al., PNAS 2010, PMID 20639463 — the class II locus is a coordinately regulated, "
       "CIITA-driven module, which is what makes a uniform module-wide shift coherent", "injection")]),
]

# Tracks are ordered and grouped by BIOLOGICAL ORGANISATION, matching Figure 13 panel A. The previous
# order was arbitrary and the previous page break was PER_PART = 4, a LaTeX constant: a reader could
# not see that the benchmark spans four levels of organisation because nothing in the layout said so.
DOMAINS = [
    ("Statistical and clinical genetics", ["GWAS", "ClinVar"]),
    ("Transcriptomics and cellular genomics", ["Bulk RNA", "scRNA"]),
    ("Functional and regulatory genomics", ["CRISPR", "Enhancer", "Histone"]),
    ("Protein biophysics", ["Protein"]),
]
_BY_NAME = {t[0]: t for t in TRACKS}
assert {n for _, ns in DOMAINS for n in ns} == set(_BY_NAME), "DOMAINS does not cover TRACKS"
# (domain-or-None, track). The domain label is carried on the FIRST track of its group, so a group
# that lands at a page boundary still announces itself.
ORDERED = [(d if i == 0 else None, _BY_NAME[n])
           for d, ns in DOMAINS for i, n in enumerate(ns)]

l1 = C.load("fig_data_l1.csv")
l2 = C.load("fig_data_l2.csv")
l3 = C.load("fig_data_l3.csv")
lev = C.load("fig_data_levels.csv")
nm = len(C.MODEL_ORDER)
count = {t: (len([r for r in l1 if r["track_display"] == t and r["model"] == C.MODEL_ORDER[0]]),
             len([r for r in l2 if r["track_display"] == t]) // nm,
             len({r["world"] for r in l3 if r["track_display"] == t})) for t, *_ in TRACKS}
TOT = tuple(sum(count[t][i] for t, *_ in TRACKS) for i in range(3))
N_FAM = len({(r["track_display"], r["family"]) for r in lev if r["level"] == "L2" and r["family"]})
# L1 class counts come from the REGISTRY, which reads each world's `issue_present` flag. This used to
# infer the class from the world NAME ("abstain" in the label), which reached the right 8/7/64 split by
# coincidence and mislabelled what the worlds are -- protein's `missing_hydrogens` is a heavy-atom
# X-ray structure, ordinary preparation rather than corruption. Three files were deriving one
# classification three ways; now only extract_world_registry.py derives it and the rest read it.
_reg1 = [r for r in C.load("world_registry.csv") if r["level"] == "L1"]
_c1 = collections.Counter(r["class"] for r in _reg1)
N_CLEAN, N_BOUNDARY = _c1["clean control"], _c1["boundary case"]
N_INJECTED = _c1["controlled integrity challenge"]
N_TYPES = len({r["world"] for r in _reg1 if r["class"] == "controlled integrity challenge"})
N_CF = len({(r["track_display"], r["world"]) for r in l3 if r["is_counterfactual"]})

# ---- layout -----------------------------------------------------------------------------------
# XL 0.115: "grounding" is the longest label and needs 0.58 in at 7.5 pt; a 0.072 gutter ran it into
# the body column. LH 0.0185: 7.5 pt type needs ~0.115 in of line height -- the previous 0.0132 gave
# 0.082 in, i.e. LESS than the glyph height, so every wrapped line overlapped the next row.
XL, XR = 0.115, 0.998
CPI_BODY = 15.8                       # chars per inch, DejaVu Sans at 7.5 pt (measured empirically)
WRAP = int((XR - XL) * FIG_W * CPI_BODY)
LH = 0.0185                           # one wrapped line, axes fraction

# EMITTED IN PARTS, because the full inventory is 13.6 in tall and a LaTeX float cannot break across
# pages. PER_PART is chosen so each part lands under ~8 in and still carries a caption. This is also
# how the table absorbs growth: adding the physics tracks appends TRACKS entries and, once they cross
# a boundary, one more part appears -- no re-flow, no re-truncation, no width change.
MAX_IN = 8.5           # a float taller than this cannot sit on one ICLR page
KIND_MARK = {"phenomenon": "phenomenon", "injection": "injection design", "substrate": "substrate"}


def draw_part(chunk, idx, n_parts):
    fig, ax = plt.subplots(figsize=(FIG_W, UNIT_IN))
    ax.set_position([0, 0, 1, 1]); ax.axis("off"); ax.patch.set_visible(False)
    ax.set_xlim(0, 1)
    y = [1.0]

    def line(label, body, colour, label_colour=None, gap=0.0035, bold_label=True):
        y[0] -= gap
        rows = textwrap.wrap(body, WRAP) or [""]
        top = y[0]
        ax.text(0.004, top, label, fontsize=FS_LAB, color=label_colour or colour,
                fontweight="bold" if bold_label else "normal", va="top")
        for i, ln in enumerate(rows):
            ax.text(XL, top - i * LH, ln, fontsize=FS_BODY, color=colour, va="top")
        y[0] = top - len(rows) * LH

    suffix = f"  ({idx + 1} of {n_parts})" if n_parts > 1 else ""
    ax.text(0.004, y[0], f"DISCERN inventory — every track, every stage{suffix}", fontsize=9.6,
            fontweight="bold", color=C.INK, va="top")
    y[0] -= 0.022
    ax.plot([0, 1], [y[0]] * 2, color=C.INK2, lw=1.0)

    for ti, (domain, (name, substrate, s1, s2, s3, refs)) in enumerate(chunk):
        n1, n2, n3 = count[name]
        if domain:
            y[0] -= 0.020
            ax.text(0.004, y[0], domain.upper(), fontsize=FS_LAB, fontweight="bold", color=C.INK3,
                    va="top")
            y[0] -= 0.007
        y[0] -= 0.019
        ax.text(0.004, y[0], name, fontsize=FS_TRACK, fontweight="bold", color=C.INK, va="top")
        ax.text(XR, y[0], f"{n1} + {n2} + {n3} tasks", fontsize=FS_NUM, color=C.INK3, va="top",
                ha="right")
        y[0] -= 0.0175
        line("", substrate, C.INK2, gap=0.0)
        line("L1", s1, C.INK, STAGE["L1"])
        line("L2", s2, C.INK, STAGE["L2"])
        line("L3", s3, C.INK, STAGE["L3"])
        for j, (ref, kind) in enumerate(refs):
            line("grounding" if j == 0 else "", f"[{KIND_MARK[kind]}]  {ref}", C.INK3,
                 label_colour=C.INK3, gap=0.0025 if j else 0.0035, bold_label=False)
        y[0] -= 0.009
        if ti < len(chunk) - 1:
            ax.plot([0, 1], [y[0]] * 2, color=C.GRID, lw=0.7)

    y[0] -= 0.004
    ax.plot([0, 1], [y[0]] * 2, color=C.INK2, lw=1.0)
    y[0] -= 0.018
    if idx == n_parts - 1:                       # totals only once, on the final part
        foot = (f"{sum(TOT)} canonical tasks = {TOT[0]} L1 ({N_INJECTED} controlled integrity "
                f"challenges, {N_BOUNDARY} boundary cases carrying no issue, {N_CLEAN} clean controls; "
                f"{N_TYPES} distinct task types) + {TOT[1]} L2 across {N_FAM} analysis families + {TOT[2]} L3 dossiers "
                f"({TOT[2] - N_CF} real, {N_CF} counterfactual).   × 6 models = "
                f"{sum(TOT) * nm:,} resolved task–model outcomes.")
    else:
        foot = "Continued on next page."
    rows = textwrap.wrap(foot, WRAP + 6)
    for i, ln in enumerate(rows):
        ax.text(0.004, y[0] - i * LH, ln, fontsize=FS_BODY, color=C.INK2, va="top")
    y[0] -= len(rows) * LH + 0.008

    ax.set_ylim(y[0], 1.0)
    fig.set_size_inches(FIG_W, UNIT_IN * (1.0 - y[0]))
    return fig


# Pages are MEASURED, not counted: track blocks differ by more than 2x in height, so a fixed
# blocks-per-page emitted one page well under half full and another over the page limit.
PARTS, _cur = [], []
for _row in ORDERED:
    _trial = _cur + [_row]
    _fig = draw_part(_trial, 0, 1)
    _h = _fig.get_size_inches()[1]
    plt.close(_fig)
    if _cur and _h > MAX_IN:
        PARTS.append(_cur); _cur = [_row]
    else:
        _cur = _trial
if _cur:
    PARTS.append(_cur)

for i, chunk in enumerate(PARTS):
    fig = draw_part(chunk, i, len(PARTS))
    name = "T01_coverage" if len(PARTS) == 1 else f"T01{chr(ord('a') + i)}_inventory"
    C.save(fig, name,
           [{"domain": d or "", "track": t, "substrate": sub, "n_l1": count[t][0],
             "n_l2": count[t][1], "n_l3": count[t][2], "l1_families": a, "l2_families": b,
             "l3_conflict": c, "l3_grounding": " | ".join(f"[{k}] {r}" for r, k in refs)}
            for d, (t, sub, a, b, c, refs) in chunk],
           ["domain", "track", "substrate", "n_l1", "n_l2", "n_l3", "l1_families", "l2_families",
            "l3_conflict", "l3_grounding"])
print(f"   L1={TOT[0]} ({N_INJECTED} challenge + {N_BOUNDARY} boundary + {N_CLEAN} clean, {N_TYPES} types)"
      f"  L2={TOT[1]} ({N_FAM} families)  L3={TOT[2]} ({TOT[2]-N_CF} real + {N_CF} cf)"
      f"  ->  {sum(TOT)} tasks, {sum(TOT)*nm:,} outcomes  ·  {len(PARTS)} part(s)")
