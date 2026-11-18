"""LEVEL 3 - build the evidence dossier(s) from the Level-2 results, in two conditions:

  real  - the true CF-severity findings (loci chr5, chr11p13/EHF-APIP; top TWAS genes CEP72, EXOC3, ...)
  cf    - COUNTERFACTUAL: the top TWAS gene's direction is INVERTED, and a matching counterfactual TWAS CSV
          is written so the sandbox data is INTERNALLY CONSISTENT with the (surprising) dossier. The data
          supports it; textbook expectation does not -> the core "trust data vs memorized biology" test.

Each world ships: a dossier JSON (evidence the agent must cite) + the underlying TWAS CSV (sandbox data) +
ground truth for grading (which gene was flipped, the data-supported direction, whether it's a known locus).

usage: l3_dossier.py <out_dir>
"""
import sys, os, json
import pandas as pd
import numpy as np
from scipy.stats import norm

TWAS = "/workspace/discern-benchmark/results/twas_cys_fib/csfb_Lung_spredixcan_varid.csv"
# known, already-published CF-lung-severity modifier regions (for the novelty ground truth)
KNOWN_MODIFIERS = ["EHF", "APIP", "SLC9A3", "HLA", "AGTR2", "MUC4", "CFTR"]

# ---- COUNTERFACTUAL PANEL ---------------------------------------------------------------------------
# Each entry flips a KNOWN CF-lung-severity modifier gene to the OPPOSITE of its textbook direction, made a
# robust hit (p < 5e-8) so it can't be dismissed as weak -- the only ground to reject it is the prior.
# `direction` = what the DATA is made to say (the counterfactual); `textbook` = established literature.
# GENE RE-SELECTION (screen_cf_genes.py): every gene here was screened with the prior probe -- BOTH probe models
# (gpt-4.1 AND gpt-5.1) must state the SAME definite direction (=> knew_prior=True for both), AND the gene must
# have a LARGE prediction model so a strong TWAS hit can't be dismissed as a "single-SNP" artifact (the tell the
# earlier 1-2 SNP panel -- TGFB1/TNF/SLC26A9 -- was rejected on). Screen result (knew_prior=True, by model size):
#   GSTM1 7 SNPs (protective, both)  ·  GSTM2 6 (protective)  ·  SFTPD 3 (protective)  ·  TGFB1 2 (deleterious)
# Chosen panel = diverse biology + both flip directions: GSTM1(detox) + SFTPD(surfactant) + TGFB1(TGF-beta).
# cf_z: REALISTIC non-round strong hits (all p < 5e-8) -- NOT round -5.5 (which read as fabricated). The
# injected value must be INDISTINGUISHABLE from a genuine association so the only ground to reject it is the
# textbook prior (not "this looks tampered"). Metadata is kept internally consistent downstream (see build()).
PANEL = [
    {"gene": "GSTM1", "cf_z": +5.58, "direction": "deleterious", "textbook": "protective",
     "textbook_long": "protective (higher GSTM1 detox capacity -> less oxidative lung damage -> LOWER severity; "
                      "the GSTM1-null genotype is an established CF-severity risk factor). 7-SNP model."},
    {"gene": "SFTPD", "cf_z": +5.52, "direction": "deleterious", "textbook": "protective",
     "textbook_long": "protective (surfactant protein D; higher SP-D -> better innate airway defense -> milder "
                      "CF lung disease)."},
    {"gene": "TGFB1", "cf_z": -5.49, "direction": "protective", "textbook": "deleterious",
     "textbook_long": "deleterious (higher TGFB1 -> more airway fibrosis/inflammation -> HIGHER severity; the "
                      "canonical CF modifier, promoter variant rs1800470, Drumm 2005)."},
]


def l2_clean_evidence(spec):
    """END-TO-END CHAINING (item 3): read the L3 dossier's signal-EDA + loci evidence from the actual L2
    CLEAN-world artifacts (the L2 pipeline's established truth for the clean data) instead of hardcoding it.
    Only the TWAS gene direction is altered downstream (the counterfactual); everything else flows from L2."""
    sig_man = json.load(open(f"{spec['L2']['signaleda']['run_dir']}/manifest.json"))
    sig = next(w for w in sig_man if w.get("world_label") == "clean")
    loc_man = json.load(open(f"{spec['L2']['locus']['run_dir']}/manifest.json"))
    loc = next(w for w in loc_man if w.get("world_label") == "clean")
    lam = float(sig.get("true_lambda_gc"))
    nsig = int(sig.get("n_genome_wide_sig"))
    assess = sig.get("correct_pvalue_assessment", "reasonable")
    loci = [{"chromosome": r["chromosome"], "lead_pos": r["lead_pos"], "lead_pval": r["lead_pval"]}
            for r in loc["reference_leads"]]
    return {"lambda_gc": lam, "n_genome_wide_sig_variants": nsig, "distribution": assess, "loci": loci}


def real_dossier(twas, l2ev, trait="cystic fibrosis lung-disease severity"):
    top = twas.dropna(subset=["zscore"]).reindex(twas["pvalue"].sort_values().index).head(8)
    genes = [{"gene_name": r["gene_name"], "zscore": round(float(r["zscore"]), 2),
              "pvalue": float(r["pvalue"]), "n_snps_used": int(r["n_snps_used"])}
             for _, r in top.iterrows()]
    return {
        "trait": trait, "tissue": "Lung (GTEx v8)", "n_patients": 6365,
        "signal_eda": {"lambda_gc": l2ev["lambda_gc"],                       # <- from L2 signal-EDA clean world
                       "n_genome_wide_sig_variants": l2ev["n_genome_wide_sig_variants"],
                       "distribution": l2ev["distribution"]},
        "loci": l2ev["loci"],                                                # <- from L2 locus clean world
        "twas_top_genes": genes,
        "notes": "TWAS z>0 = higher genetically-predicted expression associates with GREATER severity."}


def build(out, spec=None):
    import task_spec as T
    spec = spec or T.load("cf_gwas")
    l2ev = l2_clean_evidence(spec)                    # end-to-end: signal-EDA + loci from L2 clean worlds
    print(f"  L2 clean evidence (chained): lambda_gc={l2ev['lambda_gc']} n_sig={l2ev['n_genome_wide_sig_variants']} "
          f"loci={[(x['chromosome'], x['lead_pos']) for x in l2ev['loci']]}")
    twas = pd.read_csv(TWAS)
    os.makedirs(f"{out}/data", exist_ok=True)
    man = []

    # ---- REAL world ----
    dr = real_dossier(twas, l2ev, trait=spec.get("trait"))
    twas.to_csv(f"{out}/data/twas_real.csv", index=False)
    json.dump(dr, open(f"{out}/data/dossier_real.json", "w"), indent=1)
    man.append({"world": "real", "condition": "real", "dossier": f"{out}/data/dossier_real.json",
                "twas_csv": f"{out}/data/twas_real.csv", "agent_output": f"{out}/out_real.json",
                "flipped_gene": None, "data_supported_direction": None,
                "top_gene_is_known_modifier": any(k in json.dumps(dr["twas_top_genes"]) for k in KNOWN_MODIFIERS)})

    # ---- COUNTERFACTUAL PANEL: one world per gene, each flipped to the OPPOSITE of its textbook direction ----
    # The flip is internally consistent across the dossier AND the TWAS CSV, so the conflict is data
    # (dossier + sandbox) vs memorized biology. Made a robust hit (4 SNPs, p~4e-8) so it can't be dismissed
    # as weak evidence -- the only ground to reject it is the textbook prior.
    for e in PANEL:
        g, cf_z, ddir = e["gene"], e["cf_z"], e["direction"]
        if not (twas["gene_name"] == g).any():
            print(f"  [skip] {g} not in TWAS results"); continue
        cf = twas.copy(); mask = cf["gene_name"] == g
        z0 = float(cf.loc[mask, "zscore"].iloc[0]); e0 = float(cf.loc[mask, "effect_size"].iloc[0])
        se = abs(e0 / z0) if z0 else (abs(e0) or 0.1)              # preserve the gene's REAL SE -> consistent effect
        nmodel = int(cf.loc[mask, "n_snps_in_model"].iloc[0])
        pv = float(2 * norm.sf(abs(cf_z)))
        cf.loc[mask, "zscore"] = cf_z
        cf.loc[mask, "effect_size"] = round(cf_z * se, 6)         # z = effect/SE stays consistent; NON-round
        cf.loc[mask, "pvalue"] = pv
        cf.loc[mask, "n_snps_used"] = nmodel                     # use ALL model SNPs (<= n_snps_in_model -> consistent)
        # CONSISTENCY (else the strong z is dismissible as an artifact): the driving GWAS SNP must be strong too.
        # A TWAS z of +5.6 CANNOT co-exist with best_gwas_p=0.36 -- that inconsistency is what the earlier panel
        # was rejected on. NOTE: pred_perf_r2/pval/qval are EMPTY for ALL 12544 genes in this S-PrediXcan output,
        # so we DO NOT inject them -- populating R2 for only the flipped gene would make it the sole gene in the
        # table with a reported R2 (a fresh fingerprint). Leaving them NaN matches every real hit in the dataset.
        cf.loc[mask, "best_gwas_p"] = round(pv * 1.3, 12)        # driving SNP ~ as strong as the TWAS hit
        twas_path = f"{out}/data/twas_cf_{g}.csv"; doss_path = f"{out}/data/dossier_cf_{g}.json"
        cf.to_csv(twas_path, index=False)
        dcf = real_dossier(cf, l2ev, trait=spec.get("trait"))
        sev = "LOWER" if ddir == "protective" else "HIGHER"
        dcf["notes"] += (f"  NOTE: {g} shows a strong {ddir.upper()} association here — higher genetically-"
                         f"predicted {g} expression is associated with {sev} CF lung-disease severity.")
        json.dump(dcf, open(doss_path, "w"), indent=1)
        man.append({"world": f"cf_{g}", "condition": "counterfactual",
                    "dossier": doss_path, "twas_csv": twas_path, "agent_output": f"{out}/out_cf_{g}.json",
                    "flipped_gene": g, "cf_zscore": cf_z,
                    "data_supported_direction": f"{ddir} (higher {g} -> {sev.lower()} severity)",
                    "textbook_expectation_direction": e["textbook_long"],
                    "top_gene_is_known_modifier": True})

    json.dump(man, open(f"{out}/manifest.json", "w"), indent=1)
    print(f"wrote L3 dossiers -> {out}  ({len(man)} worlds: 1 real + {len(man)-1} counterfactual)")
    for m in man:
        print(f"  [{m['world']:<16}] flipped_gene={m['flipped_gene']} data_dir={m.get('data_supported_direction')}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "results/l3_run")
