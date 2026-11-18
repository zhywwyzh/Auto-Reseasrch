"""hist_gene_exp L3 prior probe — the GATE 0 check for the bivalency flip.

THE PRIOR: "strong promoter H3K4me3 => the gene is expressed".
PREDICTION-eliciting phrasing, deliberately NOT principle-validation: the enhancer flip died partly because its
probe asked models to VALIDATE a principle, which invites the rider. Here we ask for a PREDICTION about a named
gene, so the answer reveals whether the model actually holds the belief for THAT gene.

  knew_prior=True   -> predicts EXPRESSED and does NOT volunteer this gene's specific bivalency/Polycomb state
                       -> holds the belief the data overturns -> ADMISSIBLE (manifest carries True).
  knew_prior=False  -> predicts silent, OR names this gene's bivalency specifically -> nothing to overturn.

REASON-ADJUDICATION (this is why a keyword read must not decide): a GENERIC caveat appended to an *expressed*
prediction -- e.g. claude's "H3K4me3 can also be bivalent" -- is NOT gene-specific knowledge and must NOT
exclude the cell. A keyword scan on "bivalent/poised" wrongly dropped claude on DUSP4 and DEPTOR; only on NR4A3
did claude reason SPECIFICALLY that the gene is poised (NR4A3 was dropped from the anchor slots as a result).
`knew_prior_raw` preserves the keyword verdict; `knew_prior` is the adjudicated one.

Validated run 2026-08-19 (6 models): DUSP4 6/6, DEPTOR 6/6, PBX3 6/6 -- the flip SURVIVES GATE 0. Contrast
enhancer conservation 0/6 and the crispr paralog flip 8/8 False, both of which died on the volunteered rider.

usage: prior_probe.py <run_dir> <model> [<model> ...]
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
import models as M
from probe_cache_io import load_cache, save_cache   # frozen-safe cache I/O (2026-09-05)

RUN = sys.argv[1]
MODELS = sys.argv[2:] or ["gpt-4.1"]

SYS = "You are a gene-regulation expert. Answer ONLY from established knowledge, not from any dataset in front of you."

# gene -> which world it anchors
GENES = {
    "UFD1":   "real (native: K4me3 + expressed, prior HOLDS -> affirm; ungated)",
    "DUSP4":  "cf_bivalent_native (native conflict: K4me3 but silent -> FLIP)",
    "ST13":   "cf_bivalent_injected (K27me3 injected + silenced -> FLIP)",
}
# GENE-SPECIFIC bivalency cues. A generic 'H3K4me3 can be bivalent' rider does NOT count -- it must be about
# THIS gene being poised/Polycomb-repressed in K562.
BIV = ("bivalen", "polycomb", "h3k27me3", "k27me3", "prc2", "ezh2", "poised")


def probe(model, gene):
    q = (f"In K562 cells, the promoter of {gene} carries strong H3K4me3. Based on established knowledge, would "
         f"you expect {gene} to be highly expressed in K562? Give a one-sentence expectation, then end with "
         f"exactly one word on its own line: 'expressed', 'silent', or 'uncertain'.")
    a = (M.chat(model, SYS, q) or "").strip()
    # REFUSAL guard (2026-09-03): a provider-level refusal (claude-fable-5 dual-use layer) is NOT
    # evidence about the model's prior. Returning it as a normal empty/short answer let the
    # gene-symbol regex score knew_prior=False off a truncated fragment, which would silently
    # mis-gate L3 admissibility. Refused -> REFUSED_PROBE, and the caller records knew_prior=None.
    if M.LAST_STOP_REASON.get(model) == "refusal":
        return {"model": model, "gene": gene, "world": GENES[gene], "tail": "",
                "volunteered_bivalency": None, "knew_prior": None, "knew_prior_raw": None,
                "answer": "[REFUSED_PROBE]", "refused": True,
                "note": "Provider-level refusal: NOT evidence about the prior."}

    tail = a.split()[-1].lower().strip(".'\"") if a else ""
    volunteered = [c for c in BIV if c in a.lower()]
    raw = (tail == "expressed") and not volunteered          # keyword verdict (pre-adjudication)
    return {"model": model, "gene": gene, "world": GENES[gene], "tail": tail,
            "volunteered_bivalency": volunteered, "knew_prior": raw, "knew_prior_raw": raw,
            "answer": a[:700],
            "note": ("ADJUDICATE THE REASON: if the model predicted 'expressed' and the cue is a GENERIC "
                     "'H3K4me3 isn't always active' caveat rather than this gene's specific K562 state, set "
                     "knew_prior back to True with the evidence recorded. Only gene-specific poised/Polycomb "
                     "reasoning excludes the cell.")}


def main():
    os.makedirs(RUN, exist_ok=True)
    p = os.path.join(RUN, "prior_probe_cache.json")
    cache = load_cache(RUN)
    print(f"{'model':<18}{'gene':<9}{'knew_prior':<12}{'volunteered':<28}tail")
    for m in MODELS:
        for g in GENES:
            k = f"{m}|{g}"
            if k in cache and cache[k].get("tail"):
                r = cache[k]
                print(f"{m:<18}{g:<9}{str(r['knew_prior']):<12}{str(r.get('volunteered_bivalency'))[:26]:<28}{r['tail']}  (cached)")
                continue
            r = probe(m, g)
            cache[k] = r
            save_cache(RUN, cache)      # flush per call
            print(f"{m:<18}{g:<9}{str(r['knew_prior']):<12}{str(r['volunteered_bivalency'])[:26]:<28}{r['tail']}", flush=True)
    save_cache(RUN, cache)
    print(f"\n[probe] -> {p}")
    print("[probe] ADMISSIBLE = knew_prior True (holds 'H3K4me3 => expressed', the belief the data overturns).")
    print("[probe] Any False from a GENERIC rider must be REASON-ADJUDICATED back to True before it excludes a cell.")


if __name__ == "__main__":
    main()
