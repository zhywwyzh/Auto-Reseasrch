"""Table T07 -> APPENDIX: the complete L3 world registry, all 22 dossiers, with route and grounding.

WHY ROUTE IS THE FIRST COLUMN AND NOT A FOOTNOTE. A counterfactual reaches the model by one of two
routes, and the route decides what its citation has to prove.

  NATIVE   -- nothing is modified; the surprising value is really in the data. Its reference must be a
              PHENOMENON citation: the literature has to show this kind of thing happens.
  INJECTED -- an upstream quantity is modified and the REAL scorer re-run. Its reference must be a
              COHERENCE argument: the modified quantity has to move the way a real biological unit
              moves. Demanding a published observation of an injected state would be asking for the
              wrong object -- the injection exists precisely to create a condition the substrate does
              not produce on its own.

T01 tagged GWAS, ClinVar and CRISPR grounding as `[phenomenon]` while those worlds are INJECTED. The
citations were not wrong, the tag was: Gerlach establishes that TWAS sign inversion is a documented
failure mode, which is exactly what makes a TWAS sign injection coherent. This table states the route
and then the kind of grounding that route requires.

EVIDENCE AND PRIOR ARE EXTRACTED, NOT PARAPHRASED. `data_supported_direction` and
`textbook_expectation_direction` are read from the shipped L3 manifest -- the same strings the grader
is handed as ground truth -- so the appendix cannot describe a conflict the models were not given.
Route, expected act and grounding are authored, transcribed from `L3_AS_BUILT.md` and from
`L3_DESIGN.md` -> "L3 GROUNDING — VERIFIED AGAINST WHAT SHIPPED", and every world name is ASSERTED
against the scored world list so a rename fails the build.

THE PRIOR GATE IS PART OF THE ROW, BUT AS AN OUTCOME, NOT A DESIGN FLAG. An earlier version printed
the manifest's `knew_prior_admissible`, which is wrong twice over: that field records the probe
POLARITY a world requires, not whether any model passed it. It read as "prior gate held" on
`cf_cytokine_flip`, from which a model was in fact excluded, and as "not held" on `cf_mhc2_injected`,
where the Boolean merely specifies the opposite polarity. What a reader needs is how many models the
world was actually scored for, so that is DERIVED from the frozen results.

Two worlds are 5 of 6, by different mechanisms:
  * bulk_rnaseq `cf_cytokine_flip` -- Claude Opus 5 is ABSENT from the results. The prior-admissibility
    gate excluded it before the task, because it did not hold the cytokine-storm belief the world
    exists to contradict. That is a measurement of its prior, not missing data.
  * cf_gwas `cf_GSTM1` -- Kimi K3 is PRESENT but graded CONFOUNDED-EXCLUDED, its prior knowledge
    recorded as uncertain at grading time. A different exclusion at a different stage.
`knew_prior_admissible` stays in the CSV as design provenance and is not shown in the table.

Caption draft, kept here so table and caption stay in sync:

    Table A4: The complete L3 discovery registry. All 22 dossiers with, for each, the route by which
    it reaches the model, the evidence it supplies, the prior that evidence meets, the act it was
    built to require, and its grounding. 8 are real controls where evidence and prior AGREE -- these
    test over-diagnosis, not conflict -- 6 are NATIVE counterfactuals whose surprising value is really
    in the data, and 8 are INJECTED, modifying an upstream quantity and re-running the real scorer.
    The two routes carry different citation burdens: a native world cites the PHENOMENON it
    instantiates, an injected world cites the regulatory architecture that makes the injection
    coherent. Evidence and prior text is quoted from the shipped manifest, i.e. from the ground truth
    the grader itself receives. All PMIDs are verified against PubMed; the ClinVar,
    scRNA and Histone substrate references, which T01 previously lacked, were added and verified
    2026-08-30. Each counterfactual row states how many of the six models it was SCORED for. Two are
    five of six, by different mechanisms: Claude Opus 5 was excluded from bulk `cf_cytokine_flip` by
    the pre-task prior gate, and Kimi K3 was graded CONFOUNDED-EXCLUDED on GWAS `cf_GSTM1`.

Run: .venv_bench/bin/python tab07_l3_registry.py
"""
import collections
import csv
import glob
import json
import os
import textwrap

import matplotlib.pyplot as plt

import fig_common as C
import registry_common as R

BASE = os.path.dirname(os.path.abspath(__file__))

# (route, expected act, [(kind, reference), ...]). Route authority: L3_AS_BUILT.md. Grounding
# authority: L3_DESIGN.md -> "L3 GROUNDING — VERIFIED AGAINST WHAT SHIPPED".
SUB = "substrate"
PHE = "phenomenon"
INJ = "injection design"
CORVOL = (SUB, "Corvol H et al., Nat Commun 2015, PMID 26417704")
GERLACH = (INJ, "Gerlach, Milind, Spence & Pritchard, bioRxiv 2025 — TWAS effect SIGNS are unreliable "
                "at a measurable rate, so a sign inversion is the documented failure this injects")
# T01 carried no substrate line for ClinVar, scRNA or Histone. These three close that gap and were
# verified against PubMed 2026-08-30, like the rest of the table.
CLINVAR_SUB = (SUB, "ClinVar: Landrum MJ et al., Nucleic Acids Res 2018;46:D1062, PMID 29165669")
SCRNA_SUB = (SUB, "10x Genomics pbmc3k: Zheng GXY et al., Nat Commun 2017;8:14049, PMID 28091601")
HIST_SUB = (SUB, "ENCODE K562 ChIP-seq + RNA-seq: ENCODE Project Consortium, Nature 2012;489:57, "
                 "PMID 22955616")
RECLASS = (INJ, "NEJM 2016, PMID 27532831 · JAMA 2018, PMID 30264118 — published classifications get "
                "reclassified, so a wrong upstream call is the documented state this constructs")
BIVALENT = (PHE, "Bernstein BE et al., Cell 2006;125:315 · Voigt & Reinberg 2013 — bivalent domains "
                 "are documented and the poised state is reactivatable")
KOHL = (PHE, "Li et al., BMC Bioinformatics 2022, PMID 35831796 (sc2marker) — canonical markers are "
             "context-dependent, not absolute")
TSUBOYAMA = (SUB, "Tsuboyama & Rocklin 2023 — measured ΔΔG, PDB 1PGA / 2QMT")

WORLDS = {
    ("cf_gwas", "real"): ("native", "AFFIRM the measured loci; the prior agrees, so the test is "
                          "over-diagnosis", [CORVOL]),
    ("cf_gwas", "cf_GSTM1"): ("injected", "HOLD the measured direction against the prior, without "
                              "overclaiming cause; ask for colocalisation / replication",
                              [CORVOL, GERLACH]),
    ("cf_gwas", "cf_TGFB1"): ("injected", "same act, opposite sign — hold the protective direction "
                              "the data supports", [CORVOL, GERLACH]),
    ("clinvar_acmg", "real"): ("native", "AFFIRM the upstream classification; it is the molecular "
                               "diagnosis", [CLINVAR_SUB]),
    ("clinvar_acmg", "cf_FH"): ("injected", "RE-DERIVE from the raw evidence and support the "
                                "non-classic partner gene over the famous anchor",
                                [CLINVAR_SUB, RECLASS]),
    ("clinvar_acmg", "cf_LFS"): ("injected", "same construction; the supported mechanism must match "
                                 "the family history, not the famous gene", [CLINVAR_SUB, RECLASS]),
    ("scrna", "real"): ("native", "AFFIRM the annotation; the marker profile and the label agree",
                        [SCRNA_SUB]),
    ("scrna", "cf_cd16_mono"): ("native", "HOLD the RNA-level value: the memorised protein-level "
                                "marker prior does not transfer to this assay", [SCRNA_SUB, KOHL]),
    ("scrna", "cf_cd68_mono"): ("native", "same construction, different marker", [SCRNA_SUB, KOHL]),
    ("crispr_screen", "real"): ("native", "AFFIRM: the call and the prior agree",
                                [(SUB, "Hart T et al., G3 2017, PMID 28655737 — the CEGv2 / NEGv1 "
                                  "reference sets")]),
    ("crispr_screen", "cf_ppan_dispensable"): (
        "native", "HOLD the measured dispensability and offer a mechanism (paralog buffering) rather "
        "than dismissing the screen",
        [(PHE, "De Kegel & Ryan, PLoS Genet 2019 · Dede et al., Genome Biol 2020 — never-essential "
          "genes are enriched for paralogs, so buffering masks essentiality")]),
    ("crispr_screen", "cf_tmprss15_essential"): (
        "injected", "the opposite direction — hold the measured essentiality of a control gene",
        [(INJ, "Hart T et al., Cell 2015;163:1515, PMID 26627737 — genotype-specific liabilities: "
          "fitness genes essential in some backgrounds and not others, which is what makes an "
          "injected context-specific essentiality coherent")]),
    ("enhancer_activity", "real"): (
        "native", "PROPOSE A CALIBRATED CANDIDATE, not a discovery: rank 1/141 and within-family "
        "p = 0.010, but it does not clear the genome-wide max null",
        [(SUB, "Klein JC et al., Genome Biology 2018;19:99, PMID 30045748"),
         (PHE, "Villar D et al., Cell 2015, PMID 25635462 · Pollard KS et al., Nature 2006, "
          "PMID 16915236 — lineage-specific regulatory innovation is real"),
         (PHE, "Ioannidis JP, Epidemiology 2008, PMID 18633328 — the top hit of a screen is the one "
          "most likely inflated, so the correct act is a calibrated candidate")]),
    ("enhancer_activity", "cf_confounded"): (
        "injected", "SUPPRESS and name the cause: a flat family given a per-species offset that "
        "tracks the genome-wide median, not biology",
        [(SUB, "Klein JC et al., Genome Biology 2018;19:99, PMID 30045748"),
         (INJ, "Leek JT et al., Nat Rev Genet 2010, PMID 20838408 — a technical offset mimicking "
          "biology is the canonical high-throughput failure mode")]),
    ("hist_gene_exp", "real"): ("native", "AFFIRM: chromatin and expression agree",
                                [HIST_SUB, BIVALENT]),
    ("hist_gene_exp", "cf_bivalent_native"): (
        "native", "FLIP: a strong-H3K4me3 promoter that is silent under a real broad H3K27me3 domain",
        [HIST_SUB, BIVALENT]),
    ("hist_gene_exp", "cf_bivalent_injected"): (
        "injected", "VERIFY FIRST, then flip: the added H3K27me3 is matched by input, so the ratio is "
        "genuine rather than a coverage artifact", [HIST_SUB, BIVALENT]),
    ("protein_ddg", "real"): ("native", "AFFIRM the destabilising direction; measurement and prior "
                              "agree", [TSUBOYAMA]),
    ("protein_ddg", "cf_stabilizing"): (
        "native", "HOLD THE MEASUREMENT over the predictor: a measured stabilising mutation that "
        "ESM2-650M scores as destabilising",
        [TSUBOYAMA,
         (PHE, "native measured reversal in the substrate; DISCERN's own audit observes that 0 of 17 "
          "buried stabilizing mutations receives a positive ESM2 LLR — a benchmark observation, not a "
          "source-paper claim")]),
    ("bulk_rnaseq", "real"): ("native", "AFFIRM the interferon programme; the prior agrees, so the "
                              "test is over-diagnosis",
                              [(SUB, "Arunachalam PS et al., Science 2020, PMID 32788292")]),
    ("bulk_rnaseq", "cf_cytokine_flip"): (
        "native", "FLIP against the cytokine-storm narrative: NF-κB targets are measured DOWN while "
        "ISGs rise",
        [(SUB, "Arunachalam PS et al., Science 2020, PMID 32788292"),
         (PHE, "Hadjadj 2020 Science · Mann 2020 Sci Immunol · Schulte-Schrepping 2020 Cell — "
          "monocyte immunoparalysis: cytokines suppressed in blood while ISGs rise")]),
    ("bulk_rnaseq", "cf_mhc2_injected"): (
        "injected", "VERIFY: the class-II module moves coordinately, which is what a real regulatory "
        "change looks like — not a per-gene artifact",
        [(SUB, "Arunachalam PS et al., Science 2020, PMID 32788292"),
         (INJ, "Meissner TB et al., PNAS 2010, PMID 20639463 — the class II locus is a coordinately "
          "regulated, CIITA-driven module, which is what makes a uniform module-wide shift coherent")]),
}


# How many of the six models each world was actually SCORED for, read from the frozen results. A model
# can be missing two ways and both reduce this number: excluded by the pre-task prior gate (no row at
# all) or graded CONFOUNDED-EXCLUDED (a row with no composite). Both are exclusions; neither is a zero,
# and neither is visible in the manifest's design flags.
_L3ROWS = list(csv.DictReader(open(os.path.join(BASE, "results/fig_data_l3.csv"))))
N_MODELS = len({r["model"] for r in _L3ROWS})
ELIGIBLE = collections.defaultdict(lambda: [0, N_MODELS])
for _r in _L3ROWS:
    if _r["state"] != "CONFOUNDED-EXCLUDED":
        ELIGIBLE[(_r["track_display"], _r["world"])][0] += 1

ROUTE_COLOR = {"native": "#2A7A50", "injected": "#8A5A0E"}
LIMIT = 300

# ---- read the shipped manifests ------------------------------------------------------------------
canon = {(r["track"], r["world"]): r for r in
         csv.DictReader(open(os.path.join(BASE, "results/fig_data_l3.csv")))}
disp = {t: r["track_display"] for (t, _), r in canon.items()}
cells = {}
for path in sorted(glob.glob(os.path.join(BASE, "tracks/*/L3/results/*/manifest*.json"))):
    track = os.path.relpath(path, BASE).split(os.sep)[1]
    try:
        doc = json.load(open(path))
    except (json.JSONDecodeError, OSError):
        continue
    for c in (doc if isinstance(doc, list) else doc.get("cells", [])):
        if isinstance(c, dict) and (track, c.get("world")) in canon:
            cells.setdefault((track, c["world"]), c)

assert set(WORLDS) == set(cells) == {k for k in canon}, \
    f"authored rows and shipped worlds disagree: {set(WORLDS) ^ set(cells)}"

by_track = collections.OrderedDict()
for (tr, w), c in sorted(cells.items(), key=lambda kv: (disp[kv[0][0]], kv[0][1] != "real",
                                                        kv[0][1])):
    by_track.setdefault(disp[tr], []).append((w, c, WORLDS[(tr, w)]))

# ---- draw ----------------------------------------------------------------------------------------
FIG_W, UNIT_IN = R.FIG_W, R.UNIT_IN
XB = 0.115                       # label column: "grounding" at 7.0 pt needs 0.60 in
wrap_body = int((1.0 - XB) * FIG_W * R.CPI)
wrap_meta = int((1.0 - XB) * FIG_W * (R.CPI * 7.5 / R.FS_META))


def page(chunk, idx, n_parts, foot):
    fig, ax = plt.subplots(figsize=(FIG_W, UNIT_IN))
    ax.set_position([0, 0, 1, 1]); ax.axis("off"); ax.patch.set_visible(False)
    ax.set_xlim(0, 1)
    y = [1.0]

    def line(label, body, size, color, wrap, gap=0.004, label_color=None):
        y[0] -= gap
        rows = textwrap.wrap(body, wrap) or [""]
        top = y[0]
        if label:
            ax.text(0.004, top, label, fontsize=R.FS_META, color=label_color or C.INK3, va="top",
                    style="italic")
        for i, ln in enumerate(rows):
            ax.text(XB, top - i * R.LH, ln, fontsize=size, color=color, va="top")
        y[0] = top - len(rows) * R.LH

    suffix = f"  ({idx + 1} of {n_parts})" if n_parts > 1 else ""
    ax.text(0.004, y[0], "L3 discovery — complete world registry" + suffix, fontsize=9.6,
            fontweight="bold", color=C.INK, va="top")
    y[0] -= 0.022
    ax.plot([0, 1], [y[0]] * 2, color=C.INK2, lw=1.0)

    for ti, (track, worlds) in enumerate(chunk):
        y[0] -= 0.019
        ax.text(0.004, y[0], track, fontsize=R.FS_GROUP, fontweight="bold", color=C.INK, va="top")
        ax.text(0.998, y[0], f"{len(worlds)} worlds", fontsize=R.FS_META, color=C.INK3, va="top",
                ha="right")
        y[0] -= 0.019
        for w, c, (route, act, refs) in worlds:
            cond = "real control" if c.get("condition") == "real" else "counterfactual"
            _e, _n = ELIGIBLE[(track, w)]
            tag = f"{cond}  ·  {route}" + ("" if c.get("condition") == "real" else
                                           f"  ·  scored for {_e}/{_n} models")
            y[0] -= 0.006
            ax.text(0.004, y[0], w, fontsize=R.FS_WORLD, fontweight="bold", color=C.INK, va="top")
            ax.text(0.998, y[0], tag, fontsize=R.FS_META, color=ROUTE_COLOR[route], va="top",
                    ha="right", fontweight="bold")
            y[0] -= R.LH
            ev = c.get("data_supported_direction")
            pr = c.get("textbook_expectation_direction")
            line("evidence", R.two_sentences(ev, LIMIT) if ev else
                 "no direction recorded — this world carries the canonical unmodified evidence",
                 R.FS_BODY, C.INK if ev else C.INK3, wrap_body, gap=0.0)
            line("prior", R.two_sentences(pr, LIMIT) if pr else
                 "no prior recorded for this world", R.FS_BODY, C.INK if pr else C.INK3, wrap_body)
            line("expected", act, R.FS_BODY, C.INK, wrap_body)
            for j, (kind, ref) in enumerate(refs):
                line("grounding" if j == 0 else "", f"[{kind}]  {ref}", R.FS_META, C.INK3,
                     wrap_meta, gap=0.004 if j == 0 else 0.002)
        y[0] -= 0.008
        if ti < len(chunk) - 1:
            ax.plot([0, 1], [y[0]] * 2, color=C.GRID, lw=0.7)

    y[0] -= 0.004
    ax.plot([0, 1], [y[0]] * 2, color=C.INK2, lw=1.0)
    y[0] -= 0.017
    text = foot if idx == n_parts - 1 else "Continued on next page."
    for i, ln in enumerate(textwrap.wrap(text, wrap_meta + 14)):
        ax.text(0.004, y[0] - i * R.LH, ln, fontsize=R.FS_META, color=C.INK2, va="top")
    y[0] -= len(textwrap.wrap(text, wrap_meta + 14)) * R.LH + 0.008

    ax.set_ylim(y[0], 1.0)
    fig.set_size_inches(FIG_W, UNIT_IN * (1.0 - y[0]))
    return fig


n_real = sum(1 for _, c in cells.items() if c.get("condition") == "real")
n_inj = sum(1 for k, (r, _, _) in WORLDS.items() if r == "injected"
            and cells[k].get("condition") != "real")
n_nat = len(cells) - n_real - n_inj
foot = (f"{len(cells)} L3 dossiers over {len(by_track)} tracks: {n_real} real controls where evidence "
        f"and prior AGREE, {n_nat} NATIVE counterfactuals whose surprising value is really in the "
        f"data, and {n_inj} INJECTED, which modify an upstream quantity and re-run the real scorer. "
        f"A native world's grounding must be a PHENOMENON citation; an injected world's must be a "
        f"COHERENCE argument. Evidence and prior are quoted from the shipped manifest — the same "
        f"ground truth the grader receives — and cut to their first sentences; T07.csv carries them "
        f"in full.")

pages = R.paginate(list(by_track.items()), draw_fn=page, foot=foot)
for i, chunk in enumerate(pages):
    fig = page(chunk, i, len(pages), foot)
    name = "T07_l3_registry" if len(pages) == 1 else f"T07{chr(ord('a') + i)}_l3_registry"
    C.save(fig, name,
           [{"track": t, "world": w, "condition": c.get("condition"), "route": route,
             "models_scored": ELIGIBLE[(t, w)][0], "models_total": N_MODELS,
             "knew_prior_admissible_design_flag": c.get("knew_prior_admissible"),
             "evidence": c.get("data_supported_direction") or "",
             "prior": c.get("textbook_expectation_direction") or "", "expected_act": act,
             "grounding": " | ".join(f"[{k}] {r}" for k, r in refs)}
            for t, ws in chunk for w, c, (route, act, refs) in ws],
           ["track", "world", "condition", "route", "models_scored", "models_total",
            "knew_prior_admissible_design_flag", "evidence", "prior", "expected_act", "grounding"])
print(f"   {len(cells)} worlds · {n_real} real + {n_nat} native + {n_inj} injected · {len(pages)} part(s)")
