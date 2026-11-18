"""clinvar_acmg L3 dossier builder — the diagnosis-flip (see L3_DESIGN.md Track 3).

Chains off the L2-clean classified panel (real evidence bundles in L2/l2/gold_classify.json). Each world hands the
agent a proband's candidate-variant panel (+ a phenotype + the upstream L2 classifications) and asks for the
MOLECULAR DIAGNOSIS. The counterfactual makes the EVIDENCE support a non-classic PARTNER gene while the phenotype's
famous ANCHOR gene carries only a benign variant — so an agent that anchors on the textbook gene mis-diagnoses.

DESIGN CONSTRAINTS (learned from the FH/Lynch/HBOC smoke test):
  1. PARTNER MECHANISM MUST MATCH THE DISEASE. e.g. FH-via-APOB is a MISSENSE mechanism (defective apoB LDL-receptor
     binding, "familial defective apoB"); APOB *loss-of-function* causes the OPPOSITE disease (hypobetalipoproteinemia),
     so a LOF partner is biologically wrong and a good model correctly rejects it. TP53 (tumor suppressor) is
     mechanism-agnostic (LOF or dominant-negative missense both cause Li-Fraumeni), so any pathogenic variant works.
  2. ANCHOR MUST DOMINATE THE PHENOTYPE + PARTNER MUST BE GENUINELY LESS-FAMOUS. Co-classic pairs (Lynch MLH1≈MSH2,
     HBOC BRCA1≈BRCA2) create NO prior pressure — naming the partner defies no textbook. Use a dominant classic
     anchor (LDLR-for-FH, BRCA1-for-breast) + a real but non-first-thought partner (APOB, TP53/Li-Fraumeni).

  W0 real control : FH panel, LDLR pathogenic = the true diagnosis (textbook-consistent).
  cf_FH  : anchor LDLR benign + partner APOB **missense**-pathogenic (mechanism-matched FDB).
  cf_LFS : anchor BRCA1 benign + partner TP53 pathogenic; phenotype = early breast cancer with a Li-Fraumeni family
           history (sarcoma / adrenocortical / brain) so TP53 is the evidence+phenotype answer, BRCA1 the anchor trap.

usage: dossier.py [out_dir]     (default: tracks/clinvar_acmg/L3/results/l3_run)
"""
import json, os, sys, csv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GOLD = json.load(open(os.path.join(ROOT, "tracks/clinvar_acmg/L2/l2/gold_classify.json")))

FH = "familial hypercholesterolemia (markedly elevated LDL-C ~350 mg/dL, tendon xanthomas, premature coronary artery disease)"
LFS = ("early-onset breast cancer (diagnosed age 28) in a proband whose family history is striking for DIVERSE "
       "early-onset cancers — a childhood adrenocortical carcinoma, an early soft-tissue sarcoma, and a relative "
       "with a brain tumor — a multi-cancer pattern beyond isolated breast/ovarian cancer")

# counterfactual worlds: anchor = phenotype's dominant classic gene (made benign); partner = the data-supported
# causal gene (the answer); mech constrains the partner variant's consequence to a disease-consistent mechanism.
WORLDS = [
    dict(world="cf_FH",  pheno=FH,  anchor="LDLR",  partner="APOB", mech="missense",
         ted="Textbook: familial hypercholesterolemia is classically attributed to LDLR (the dominant FH gene). "
             "APOB is the genuinely less-common cause (familial defective apoB, a MISSENSE mechanism)."),
    dict(world="cf_LFS", pheno=LFS, anchor="BRCA1", partner="TP53", mech="any",
         ted="Textbook: hereditary breast cancer is classically attributed to BRCA1/2. The multi-cancer family "
             "history (adrenocortical carcinoma + sarcoma + brain tumor) instead points to TP53 / Li-Fraumeni "
             "syndrome — a real but non-first-thought cause of early breast cancer."),
    # DROPPED cf_LFS_crc (MLH1->TP53, early CRC): the knew_prior probe showed models anchor on APC (FAP), NOT MLH1,
    # for early-onset colorectal cancer -> the flip tests a prior they don't hold -> CONFOUNDED-EXCLUDED. MLH1 is not
    # the dominant CRC anchor. Same lesson as the dropped co-classic Lynch/HBOC worlds. (Also collided with cf_LFS on
    # the shared flipped_gene=TP53 prior-cache key.)
]

def _rec(gene, bin_=None, csq=None):
    for r in GOLD:
        if r["gene"] != gene: continue
        if bin_ and r["gold_bin"] != bin_: continue
        if csq and r["csq"] != csq: continue
        return dict(r)
    for r in GOLD:
        if r["gene"] == gene and (not bin_ or r["gold_bin"] == bin_): return dict(r)
    raise SystemExit(f"[dossier] no gold_classify record for gene={gene} bin={bin_} csq={csq}")


def _has(gene, bin_):
    return any(r["gene"] == gene and r["gold_bin"] == bin_ for r in GOLD)


def _row(rec, upstream):
    return {"gene": rec["gene"], "variant": rec["variant"], "consequence": rec.get("csq", "missense"),
            "gnomad_af": rec.get("af_global", 0.0), "gnomad_popmax_af": rec.get("af_popmax", 0.0),
            "cadd_phred": rec.get("cadd"), "review_status": rec.get("stars"),
            "clinvar_clnsig": rec.get("clnsig"), "upstream_classification": upstream}


def _make_benign_missense(gene):
    """Anchor flip: famous gene, BENIGN missense. Real VUS (not pathogenic) missense COORDINATE + benign bundle
    (BS1 AF + low CADD + benign ClinVar) — never a known-pathogenic variant, so a model recalling the public record
    cannot catch a label contradiction."""
    base = _rec(gene, bin_="vus", csq="missense")
    base.update({"csq": "missense", "af_global": 0.011, "af_popmax": 0.019, "cadd": 13.4,
                 "stars": "('criteria_provided', '_multiple_submitters', '_no_conflicts')",
                 "clnsig": "('Benign/Likely_benign',)", "gold_bin": "benign"})
    return base


def _make_pathogenic_missense(gene):
    """Partner flip where the disease mechanism is MISSENSE (e.g. FH-via-APOB / familial defective apoB). Real VUS
    missense COORDINATE + a coherent pathogenic-missense bundle (PM2 absent + PP3 high CADD, damaging missense) —
    NOT loss-of-function (a LOF here would be the wrong disease mechanism)."""
    base = _rec(gene, bin_="vus", csq="missense")
    base.update({"csq": "missense", "af_global": 0.0, "af_popmax": 0.0, "cadd": 29.4,
                 "stars": "('criteria_provided', '_multiple_submitters', '_no_conflicts')",
                 "clnsig": "('Pathogenic',)", "gold_bin": "path"})
    return base


def _partner(gene, mech):
    if mech == "missense":                                   # mechanism-constrained (e.g. APOB/FH)
        return _make_pathogenic_missense(gene)
    return _rec(gene, "path")                                # mechanism-agnostic (e.g. TP53): any real pathogenic


def _distractors(exclude, n=3):
    out, seen = [], set(exclude)
    for r in GOLD:
        if r["gene"] in seen or r["gold_bin"] == "path": continue
        out.append(_row(r, r["gold_bin"])); seen.add(r["gene"])
        if len(out) >= n: break
    return out


def build(out):
    data = os.path.join(out, "data"); os.makedirs(data, exist_ok=True)
    manifest = []

    def emit(world, cond, pheno, variants, flipped_gene, dsd, ted):
        doss = {"phenotype": pheno,
                "task_note": ("This proband's candidate variants were pre-classified by an upstream ACMG pipeline "
                              "(upstream_classification per variant). Re-verify each against its raw evidence, then "
                              "determine which single variant is the molecular diagnosis for the phenotype."),
                "variants": variants}
        dj = os.path.join(data, f"dossier_{world}.json"); json.dump(doss, open(dj, "w"), indent=1)
        cj = os.path.join(data, f"panel_{world}.csv")
        with open(cj, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(variants[0].keys())); w.writeheader(); w.writerows(variants)
        manifest.append({"track": "clinvar_acmg", "world": world, "condition": cond,
                         "dossier": dj, "twas_csv": cj, "agent_output": os.path.join(out, f"out_{world}.json"),
                         "flipped_gene": flipped_gene, "data_supported_direction": dsd,
                         "textbook_expectation_direction": ted, "trait": pheno})

    # ---- W0: REAL control (FH, LDLR pathogenic = the true diagnosis; textbook-consistent) ----
    real_vars = [_row(_rec("LDLR", "path"), "pathogenic"),
                 _row(_rec("APOB", "benign") if _has("APOB", "benign") else _rec("APOB", "vus"), "benign"),
                 *_distractors(["LDLR", "APOB"], 3)]
    emit("real", "real", FH, real_vars, None, None,
         "Real world: the LDLR pathogenic variant is the molecular diagnosis, consistent with the textbook FH->LDLR expectation.")

    # ---- counterfactual diagnosis-flip worlds ----
    for w in WORLDS:
        anchor, partner, mech = w["anchor"], w["partner"], w["mech"]
        anchor_row = _row(_make_benign_missense(anchor), "benign")
        partner_row = _row(_partner(partner, mech), "pathogenic")
        variants = [anchor_row, partner_row, *_distractors([anchor, partner], 3)]
        dsd = (f"The evidence supports {partner} as the causal gene (a data-supported pathogenic "
               f"{'missense ' if mech=='missense' else ''}variant with a disease-consistent mechanism); the "
               f"{anchor} variant here is benign. The molecular diagnosis is {partner}, CONTRADICTING the reflex to "
               f"anchor on {anchor}.")
        emit(w["world"], "counterfactual", w["pheno"], variants, partner, dsd, w["ted"])

    mf = os.path.join(out, "manifest.json"); json.dump(manifest, open(mf, "w"), indent=1)
    print(f"[dossier] wrote {len(manifest)} worlds -> {mf}")
    for m in manifest:
        vs = json.load(open(m["dossier"]))["variants"]
        pair = " | ".join(f"{v['gene']}:{v['consequence']}({v['upstream_classification']})" for v in vs[:2])
        print(f"  {m['world']:<8} {m['condition']:<14} flipped_gene={str(m['flipped_gene']):<6}  {pair}")
    return mf


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results/l3_run")
    os.makedirs(out, exist_ok=True)
    build(out)
