"""crispr_screen L3 prior-knowledge probe (task-matched to the paralog-buffered essentiality flip).

The flip only tests "trust the data over the prior" if the model HOLDS the textbook prior that the candidate gene
is broadly essential in cancer cell lines. Probe, in a clean isolated context, whether the model asserts that.

  knew_prior=True  iff it says ESSENTIAL       -> holds the prior the HAP1 screen contradicts -> genuine test.
  knew_prior=False iff it says NON-ESSENTIAL   -> no prior to override, OR it already volunteers the paralog
                    buffering -> CONFOUNDED (grade_l3 excludes the cell). None -> unclear.

Per L3_DESIGN "Selection rule": pick the gene whose broad-essential reputation the MOST roster models hold while
the FEWEST already know its HAP1 paralog buffering. Famous SWI/SNF + cohesin pairs (SMARCA2/4, ARID1A/B, STAG1/2)
carry the strongest prior but the highest chance the model already knows the synthetic lethality; the metabolic /
ESCRT pairs (ME2/ME3, VPS4A/VPS4B) are lower-fame and lower confound risk.

We ALSO detect volunteered buffering knowledge ("paralog", "redundant", "VPS4A compensates", ...) because a model
that already knows the mechanism cannot be surprised by it -> that is the confound the gate must catch.

Writes {run_dir}/prior_probe_cache.json in the format grade_l3.cached_prior_probe expects
(key = f"{model}|{flipped_gene}").

usage: prior_probe.py <run_dir> <model> [<model> ...]
"""
import json, os, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
import models as M
from probe_cache_io import load_cache, save_cache   # frozen-safe cache I/O (2026-09-05)

RUN = sys.argv[1]
MODELS = sys.argv[2:] or ["gpt-4.1"]

SYS = ("You are a cancer functional-genomics expert. Answer ONLY from established knowledge of gene essentiality "
       "in cancer cell lines — not from any dataset in front of you.")

# candidate flip genes: CEG-reputation genes that are NON-DEPLETING in the HAP1 golden because a paralog buffers.
# (mean_lfc verified against tracks/crispr_screen/L2/gold/golden_scores.csv)
CANDIDATES = {
    # class A — paralog-buffered pairs (L3_DESIGN lead candidates). PROBE RESULT 2026-08-13: knew_prior=False for
    # ALL FOUR on both gpt-4.1 and gpt-5.6-sol — models correctly know these are NOT pan-essential (that is exactly
    # WHY they are paralog-buffered), so there is no textbook prior for the screen to overturn. Class A is DEAD as
    # the flip anchor; kept here as the record of the screen.
    "ME2":     ("ME2 (malic enzyme 2)",            "ME3"),
    "VPS4B":   ("VPS4B (ESCRT-III ATPase)",        "VPS4A"),
    "ARID1B":  ("ARID1B (SWI/SNF subunit)",        "ARID1A"),
    "SMARCA2": ("SMARCA2 / BRM (SWI/SNF ATPase)",  "SMARCA4"),
    # class B — the CEGv2 core-essential genes that are NON-DEPLETING in this HAP1 screen (also named in
    # L3_DESIGN). Here the prior is REFERENCE-ANNOTATED (CEGv2, in the dossier) as well as parametric, so the
    # conflict is visible in the data AND held by the model.
    "POLR2A":  ("POLR2A (RNA polymerase II largest subunit)", None),
    "HDAC3":   ("HDAC3 (histone deacetylase 3)",             None),
    "PPAN":    ("PPAN (peter pan homolog, ribosome biogenesis)", None),
    "NKAP":    ("NKAP (NF-kB activating protein)",           None),
    # --- CF-world focus genes (added 2026-08-14 after the gpt-4.1 smoke) -------------------------------
    # EVERY counterfactual world's focus gene must be probed HERE with the essentiality question. If it is
    # absent, grade_l3 falls back to its built-in cached_prior_probe, which asks the GWAS-style DIRECTIONAL
    # question ("is higher X protective?") — that cannot classify an essentiality answer, returns
    # knew_prior=None, and the world is CONFOUNDED-EXCLUDED. The gpt-4.1 smoke lost 3 of 5 worlds this way.
    "PRMT5":     ("PRMT5 (protein arginine methyltransferase 5)", None),   # cf_textbook_holds
    "UPF1":      ("UPF1 (NMD RNA helicase)",                      None),   # cf_artifact_nonessential
    "TMPRSS15":  ("TMPRSS15 (enteropeptidase)",                   None),   # cf_no_paralog_nonessential
    # ACTL6A replaces UPF1 as the cf_artifact anchor (2026-08-14). UPF1 was invalid: at the L2 golden's
    # aggregation it is -2.668, BELOW the -2.506 threshold, so the caller does NOT miss it — the "miss" was an
    # artifact of the dossier recomputing LFCs instead of reading the golden. ACTL6A genuinely satisfies the
    # premise: golden mean -1.430 (caller MISSES it) while its two well-covered guides are -2.869/-2.895
    # (mean -2.882, below threshold) and a guide with ZERO T0 counts scores +1.068, dragging the mean up.
    "ACTL6A":    ("ACTL6A / BAF53A (SWI/SNF actin-like subunit)",  None),   # cf_artifact — REJECTED, see below
    # ACTL6A REJECTED as the cf_artifact anchor (probe 2026-08-14): 5/6 True but claude-opus-5 volunteered
    # ACTL6A/ACTL6B paralog redundancy unprompted -> CONFOUNDED for that model. It is a SWI/SNF subunit, i.e.
    # exactly the paralog-famous family the original class-A screen showed models volunteer. PRELID1 is the
    # alternative: mitochondrial lipid transfer, no famous paralog story, and an equally clean artifact
    # signature — golden -1.953 (caller MISSES it), well-covered guides -3.736 / -3.173 (mean -3.454, far
    # below the -2.506 threshold), dead guide at T0=44 scoring -0.583.
    "PRELID1":   ("PRELID1 (mitochondrial lipid-transfer protein)", None),  # cf_artifact — REJECTED 0/6, no prior
    # PRELID1 REJECTED (probe 2026-08-14): knew_prior=False on ALL SIX — no model holds an essentiality prior
    # for it, so the artifact world would carry no conflict at all. Remaining candidates whose WELL-COVERED
    # guides still cross the -2.506 threshold (so the "caller missed a truly essential gene" premise holds):
    "MAGOH":     ("MAGOH (exon junction complex core subunit)",    None),
    "MVK":       ("MVK (mevalonate kinase)",                       None),
    "PSMA2":     ("PSMA2 (20S proteasome alpha subunit)",          None),
}
# volunteered-mechanism cues: if the model already names the buffering, the surprise is gone -> CONFOUNDED
BUFFER_CUES = ("paralog", "redundan", "compensat", "buffer", "synthetic lethal", "synthetically lethal")


def probe(model, gene):
    label, paralog = CANDIDATES[gene]
    q = (f"Is {label} essential for proliferation in MOST human cancer cell lines? Answer in 1-2 sentences, then end "
         f"with exactly one word on its own line: either 'essential' or 'nonessential'.")
    ans = (M.chat(model, SYS, q) or "").strip()
    # REFUSAL guard (2026-09-03): a provider-level refusal (claude-fable-5 dual-use layer) is NOT
    # evidence about the model's prior. Returning it as a normal empty/short answer let the
    # gene-symbol regex score knew_prior=False off a truncated fragment, which would silently
    # mis-gate L3 admissibility. Refused -> REFUSED_PROBE, and the caller records knew_prior=None.
    if M.LAST_STOP_REASON.get(model) == "refusal":
        return {"gene": gene, "paralog": paralog, "answer": "[REFUSED_PROBE]", "tail": "",
                "knew_prior": None, "volunteered_buffering": None, "refused": True}

    tail = ans.split()[-1].lower().strip(".") if ans else ""
    knew = ("essential" in tail and "non" not in tail) if tail else None
    volunteered = [c for c in BUFFER_CUES if c in ans.lower()]
    if volunteered:                       # already knows the mechanism -> cannot be surprised -> confounded
        knew = False
    return {"gene": gene, "paralog": paralog, "answer": ans[:700], "tail": tail,
            "knew_prior": knew, "volunteered_buffering": volunteered}


def main():
    os.makedirs(RUN, exist_ok=True)
    p = os.path.join(RUN, "prior_probe_cache.json")
    cache = load_cache(RUN)
    print(f"{'model':<18}{'gene':<10}{'knew_prior':<12}{'volunteered buffering':<26}tail")
    for model in MODELS:
        for gene in CANDIDATES:
            r = probe(model, gene)
            cache[f"{model}|{gene}"] = r
            print(f"{model:<18}{gene:<10}{str(r['knew_prior']):<12}{str(r['volunteered_buffering'])[:24]:<26}{r['tail']}")
    save_cache(RUN, cache)
    print(f"\n[probe] -> {p}")
    print("[probe] SELECTION RULE: pick the gene with the most knew_prior=True and the fewest volunteered_buffering.")


if __name__ == "__main__":
    main()
