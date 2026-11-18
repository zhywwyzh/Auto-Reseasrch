"""crispr_screen L3 dossier builder — ESSENTIALITY CALL vs PRIOR (3 worlds: 1 real + 2 counterfactual).

Chains off the clean L2 `calling` result: hands the agent the L2 essentiality call for a focus gene plus the
guide-level screen evidence, and asks it to INTERPRET that call.

THE CALLER (what `called_essential` means — read this before touching anything):
  The L2 caller is a BAGEL-style Bayes Factor. Per guide it computes log P(lfc | essential) - log P(lfc |
  non-essential), with both densities learned by KDE from THIS screen's own CEGv2 / NEGv1 guides; the per-guide
  LLRs are SUMMED per gene to give `bf`. A gene is called essential iff `bf > essential_thr`, where the
  threshold is a QUANTILE OF THE NEG GENES' BF DISTRIBUTION (NEG-anchored, so the FPR is controlled).
  ==> `essential_thr` (-2.506) IS A BAYES-FACTOR CUTOFF, **NOT** a log-fold-change cutoff.
  A previous build compared it against `gene_mean_lfc` (a units error) and therefore mis-selected three
  "the caller missed it" anchors (UPF1 / PSMA2 / ACTL6A) that the caller had in fact called essential.
  This builder now READS `bf` and `essential` straight from gold/golden_essential.csv instead of recomputing.

THE THREE WORLDS — the conflict is NATIVE in one and INJECTED in the other:
  real    PRMT5     BF +30.04, essential=True.  Probe: 6/6 models say essential. Data and prior AGREE ->
                    no surprise. Tests OVER-DIAGNOSIS: do not invent a finding where there is none.
                    (A single outlier guide at -0.238 is the bait; the gpt-4.1 smoke bit on it.)
  cf_ppan_dispensable
          PPAN      BF -5.86, essential=False. Probe: 6/6 say essential. THE CONFLICT IS ALREADY IN THE REAL
                    DATA — nothing is injected. CEGv2 + every model say core-essential; the screen says
                    dispensable, reproducibly (replicate spread 0.108, four well-covered guides, none
                    strongly depleting). Correct: FLIP toward the data.
  cf_tmprss15_essential
          TMPRSS15  BF -8.31 natively (a NEGv1 control every model correctly calls non-essential) -> there is
                    NO conflict until we make one. INJECTED, mirroring the GWAS `cf_zscore` construction:
                    the endpoint counts are scaled per replicate by (0.10, 0.15, 0.12) and the REAL scorer is
                    re-run, so bf / mean_lfc / per-replicate means / guide LFCs all stay mutually consistent
                    (BF +16.2, mean -2.90, spread 0.59 — comparable to PRMT5's 0.86, not implausibly tight).
                    Correct: FLIP toward the data in the OPPOSITE direction — a gene you believe is a
                    non-essential control IS essential in this line.

WHY THE TWO CF WORLDS POINT OPPOSITE WAYS: a model cannot score by always resolving the conflict the same
direction ("trust the data => non-essential", or reflexive contrarianism). It must follow the evidence each
time. That contrast is this track's headline measurement.

usage: dossier.py [out_dir]     (default: tracks/crispr_screen/L3/results/l3_run)
"""
import csv, json, os, sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
L2 = os.path.join(ROOT, "tracks/crispr_screen/L2")
sys.path.insert(0, L2)
import l2_common as C                                                    # the REAL scorer

CLEAN = os.path.join(L2, "results/crispr_l2_calling_run/data/cell000")   # the L2 CLEAN calling world
GOLD = pd.read_csv(os.path.join(L2, "gold/golden_essential.csv")).set_index("gene")
THR = json.load(open(os.path.join(L2, "gold/gold_solver.json")))["calling"]["clean"]["essential_thr"]

INJECT_FACTORS = (0.10, 0.15, 0.12)      # per-replicate, TMPRSS15 only — see module docstring

# world -> (gene, condition, knew_prior_admissible, trait)
#   knew_prior_admissible = the probe answer this world REQUIRES for the cell to be a genuine test:
#     cf_ppan      True  — the model must HOLD "PPAN is essential" for the flip to overturn something
#     cf_tmprss15  False — the model must hold "TMPRSS15 is NON-essential" (all 6 do); the injected data
#                          contradicts THAT prior, so False is the admissible state here
WORLDS = [
    ("real",                  "PRMT5",    "real",           None,  "HAP1 essentiality call (core-essential that DOES deplete)"),
    ("cf_ppan_dispensable",   "PPAN",     "counterfactual", True,  "HAP1 essentiality call (core-essential, NOT depleting)"),
    ("cf_tmprss15_essential", "TMPRSS15", "counterfactual", False, "HAP1 essentiality call (non-essential control that DOES deplete)"),
]


def counts():
    cf = [f for f in os.listdir(CLEAN) if f.startswith("counts")][0]
    return pd.read_csv(os.path.join(CLEAN, cf), sep="\t")


def scored(cnt, exclude_from_kde=None):
    """Score with the REAL caller. `exclude_from_kde` drops a gene from the NEGv1 pool the KDE is learned
    from — REQUIRED when injecting a NEG gene, because the caller learns its 'non-essential' density FROM
    those guides. Injecting TMPRSS15 without this shifted 380 reference genes' BF by >0.5 (max 6.42): the
    counterfactual would have silently altered every OTHER gene's score too, so the two worlds would not be
    comparable. Excluding it keeps the yardstick fixed and confines the injection to the focus gene."""
    ceg = set(GOLD.index[GOLD.is_ceg]); neg = set(GOLD.index[GOLD.is_neg])
    if exclude_from_kde:
        neg = neg - {exclude_from_kde}
    s = C.gene_scores(cnt, ceg, neg)
    s["is_neg"] = s.index.isin(set(GOLD.index[GOLD.is_neg]))      # restore true membership for reporting
    return s


def guide_rows(cnt, gene):
    """Per-guide evidence straight from the (possibly injected) counts, using the REAL lfc function."""
    sub = cnt[cnt.gene == gene]
    fc = C.guide_lfc(cnt).loc[sub.index]
    return [{"sgRNA": r.sgRNA, "T0": int(r.T0), **{rr: int(getattr(r, rr)) for rr in C.REPS},
             "guide_lfc": round(float(fc.loc[i, "mean"]), 3)} for i, r in zip(sub.index, sub.itertuples())]


def build(out):
    data = os.path.join(out, "data"); os.makedirs(data, exist_ok=True)
    base = counts()
    manifest = []

    for world, gene, cond, admissible, trait in WORLDS:
        cnt = base.copy()
        injected = (world == "cf_tmprss15_essential")
        if injected:                                   # scale endpoint counts, then RE-RUN the real scorer
            sel = cnt.gene == gene
            for r, f in zip(C.REPS, INJECT_FACTORS):
                cnt.loc[sel, r] = np.maximum((cnt.loc[sel, r] * f).round(), 0).astype(int)
            s = scored(cnt, exclude_from_kde=gene).loc[gene]
            bf, mean_lfc = float(s.bf), float(s.mean_lfc)
            reps = {r: round(float(getattr(s, "lfc_" + r)), 3) for r in C.REPS}
        else:                                          # READ the golden — never recompute (the units bug)
            g = GOLD.loc[gene]
            bf, mean_lfc = float(g.bf), float(g.mean_lfc)
            s = scored(cnt).loc[gene]
            reps = {r: round(float(getattr(s, "lfc_" + r)), 3) for r in C.REPS}
        called = bool(bf > THR)
        spread = round(max(reps.values()) - min(reps.values()), 3)
        guides = guide_rows(cnt, gene)

        # the `screen` dataframe: the focus gene's guides + CEG/NEG gene-level reference context
        ref = scored(cnt, exclude_from_kde=gene if injected else None)
        ref = ref[ref.is_ceg | ref.is_neg].reset_index()
        ref["set"] = np.where(ref.is_ceg, "CEGv2_core_essential", "NEGv1_non_essential")
        csv_path = os.path.join(data, f"screen_{world}.csv")
        rows = ([{"gene": gene, "level": "guide", **gd} for gd in guides] +
                [{"gene": r.gene, "level": "gene_reference", "set": r.set,
                  "bf": round(float(r.bf), 3), "guide_lfc": round(float(r.mean_lfc), 3), "T0": ""}
                 for r in ref.itertuples()])
        keys = sorted({k for r in rows for k in r})
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)

        doss = {
            "task_note": ("Clean L2 result for a genome-wide CRISPR-KO screen in HAP1 (TKOv3 library, T0 vs three "
                          "endpoint replicates). The L2 essentiality caller produced the call below for one focus "
                          "gene. Its guide-level evidence is provided (and loadable as the `screen` dataframe in "
                          "the sandbox), alongside the CEGv2 core-essential / NEGv1 non-essential reference sets. "
                          "INTERPRET the call: is it right, what does it mean for this gene in this cell line, and "
                          "does the evidence support any novel, discovery-guiding hypothesis?"),
            "focus_gene": gene,
            "l2_clean_evidence": {
                "called_essential": called,
                "bayes_factor": round(bf, 3),
                "essential_threshold_on_BAYES_FACTOR": THR,
                "caller_note": ("The caller is a BAGEL-style Bayes Factor: per-guide log-likelihood ratios "
                                "(essential vs non-essential guide-LFC densities learned from this screen's own "
                                "CEGv2/NEGv1 guides), SUMMED per gene. A gene is called essential iff its Bayes "
                                "factor exceeds the threshold, which is a quantile of the NEGv1 genes' BF "
                                "distribution. The threshold applies to the BAYES FACTOR, not to log2 fold-change."),
                "gene_mean_lfc": round(mean_lfc, 3),
                "per_replicate_mean_lfc": reps,
                "replicate_spread": spread,
                "n_guides": len(guides),
                "in_CEGv2_core_essential": bool(GOLD.loc[gene, "is_ceg"]),
                "in_NEGv1_non_essential": bool(GOLD.loc[gene, "is_neg"]),
            },
            "guide_level_evidence": guides,
            "reference_note": ("CEGv2 = the Hart core-essential reference (essential across most cancer cell "
                               "lines); NEGv1 = the matched non-essential reference. Membership is an ANNOTATION "
                               "from other cell lines, not a measurement in this screen."),
        }
        dj = os.path.join(data, f"dossier_{world}.json"); json.dump(doss, open(dj, "w"), indent=1)
        row = {"track": "crispr_screen", "world": world, "condition": cond,
               "dossier": dj, "twas_csv": csv_path,
               "agent_output": os.path.join(out, f"out_{world}.json"),
               "flipped_gene": gene, "target_gene": gene, "gene_aliases": [gene], "trait": trait,
               "data_supported_direction": DSD[world].format(gene=gene, bf=round(bf, 2),
                                                             mean=round(mean_lfc, 2), spread=spread),
               "textbook_expectation_direction": TED[world].format(gene=gene)}
        if admissible is not None:
            row["knew_prior_admissible"] = admissible
        if injected:
            row["injected"] = {"kind": "endpoint_count_scaling", "per_replicate_factors": list(INJECT_FACTORS),
                               "native_bf": round(float(GOLD.loc[gene, "bf"]), 3),
                               "native_mean_lfc": round(float(GOLD.loc[gene, "mean_lfc"]), 3)}
        manifest.append(row)

    mf = os.path.join(out, "manifest.json"); json.dump(manifest, open(mf, "w"), indent=1)
    print(f"[dossier] wrote {len(manifest)} worlds -> {mf}\n")
    for m in manifest:
        e = json.load(open(m["dossier"]))["l2_clean_evidence"]
        inj = "  INJECTED" if "injected" in m else ""
        print(f"  {m['world']:<24}{m['flipped_gene']:<10}BF={e['bayes_factor']:>8}  called_essential={str(e['called_essential']):<6}"
              f"  mean_lfc={e['gene_mean_lfc']:<8} spread={e['replicate_spread']}{inj}")


DSD = {
 "real": ("{gene} is annotated CORE-ESSENTIAL in CEGv2 and the screen AGREES: Bayes factor {bf} (far above the "
          "{thr} threshold), gene mean log2FC {mean}, so the caller correctly calls it essential. Prior and data "
          "POINT THE SAME WAY — there is no conflict and no surprise to find. The correct answer AFFIRMS "
          "essentiality. NOTE: one guide sits at -0.238 while the other three are -3.4 to -4.3; that single "
          "outlier is NOT evidence of a tolerant subpopulation and must not be spun into a novel finding. "
          "Inventing a discovery here is OVER-DIAGNOSIS and is the failure this world exists to catch."
          ).replace("{thr}", str(THR)),
 "cf_ppan_dispensable": (
          "{gene} is annotated CORE-ESSENTIAL in CEGv2 — and every roster model asserts it is essential — yet in "
          "THIS HAP1 screen it does NOT deplete: Bayes factor {bf} (below the {thr} threshold, so the caller does "
          "NOT call it essential) and gene mean log2FC {mean}. The non-depletion is REPRODUCIBLE across all three "
          "replicates (spread {spread}) with four well-covered guides and no dead-guide masking. NOTHING IS "
          "INJECTED — this conflict is native to the real data. The data-supported reading is that {gene} is "
          "DISPENSABLE in this near-haploid line despite its core-essential reputation: trust the screen over the "
          "annotation. NOVELTY CEILING (an example of a full-credit answer): {gene} (PPAN) acts in ribosome "
          "biogenesis / rRNA processing, so its dispensability implies ANOTHER factor carries that step here — "
          "name that compensating dependency as the candidate SYNTHETIC-LETHAL target and give a concrete test "
          "(knock it out in HAP1 and show the double loss is lethal while either single loss is tolerated). "
          "Merely restating that {gene} did not deplete is a 0 on novelty. A reading of 'only WEAKLY required' "
          "rather than strictly neutral is CONSISTENT with the flip — two guides sit at -0.5/-0.7 — and must not "
          "be penalised."
          ).replace("{thr}", str(THR)),
 "cf_tmprss15_essential": (
          "{gene} is a NEGv1 NON-ESSENTIAL control gene — the reference set says dispensable and every roster "
          "model correctly asserts it is non-essential. But in THIS screen it DEPLETES: Bayes factor {bf} (well "
          "above the {thr} threshold, so the caller DOES call it essential), gene mean log2FC {mean}, "
          "reproducible across all three replicates (spread {spread}) with well-covered guides. The "
          "data-supported reading is that {gene} IS REQUIRED in this cell line despite its non-essential "
          "reputation — trust the screen over the reference annotation. This is the MIRROR of the PPAN world: "
          "the conflict runs the OPPOSITE direction, so a model that resolves every conflict toward "
          "'non-essential' (or that is reflexively contrarian) fails here. NOVELTY CEILING: propose WHY a "
          "reference non-essential gene would be required specifically in a near-haploid line, and give one "
          "concrete test that would confirm it."
          ).replace("{thr}", str(THR)),
}
TED = {
 "real": ("Textbook/CEGv2: {gene} is a core-essential gene — required for proliferation across most human cancer "
          "cell lines — so knocking it out is expected to kill the cells. The screen agrees."),
 "cf_ppan_dispensable": (
          "Textbook/CEGv2: {gene} is a core-essential gene — essential for proliferation across most human cancer "
          "cell lines — so the expectation is that knocking it out kills the cells. The screen contradicts this."),
 "cf_tmprss15_essential": (
          "Textbook/NEGv1: {gene} is a standard NON-ESSENTIAL control gene, expected to show no fitness effect "
          "when knocked out. The screen contradicts this."),
}

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results/l3_run"))
