"""bulk_rnaseq L3 prior probe — the GATE 0 check for the cytokine-storm flip.

THE PRIOR: "COVID-19 is a cytokine storm, so NF-kB inflammatory targets (TNF, IL1B) are UP in patients".
The golden DE for this PBMC cohort shows the opposite -- TNF -1.30, IL1B -1.70, TNFAIP3 -1.28, NFKB1 -0.32
(all padj < 0.05) -- while ISGs are strongly UP. The mechanism is circulating-monocyte hyporesponsiveness /
immunoparalysis: cytokines are high in serum and lung but SUPPRESSED in the blood transcriptome.

  knew_prior=True   -> answers UP (holds the cytokine-storm prior) and does NOT volunteer the
                       PBMC/blood-suppression rider -> the data overturns a belief it holds -> ADMISSIBLE.
  knew_prior=False  -> answers DOWN, or specifically volunteers that the BLOOD/PBMC transcriptome is
                       suppressed/immunoparalysed -> nothing to overturn -> CONFOUNDED.

REASON-ADJUDICATION (same rule as hist): a GENERIC hedge -- "compartments can differ", "depends on severity
and timing" -- appended to an UP answer is NOT knowledge of this cohort's PBMC suppression and must NOT
exclude the cell. Only a specific claim that the blood/PBMC transcriptome shows DOWN-regulated NF-kB targets
counts as the confound. `knew_prior_raw` keeps the keyword verdict; `knew_prior` is the adjudicated one.

RISK (flagged in L3_DESIGN): this is the same GATE 0 class as hist -- a per-condition prior with a possible
compartment rider. The cytokine-storm narrative dominates the literature and the PBMC-suppression finding is
specialist, so the prior is expected to hold, but it MUST be measured before the build is trusted.

usage: prior_probe.py <run_dir> <model> [<model> ...]
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
import models as M
from probe_cache_io import load_cache, save_cache   # frozen-safe cache I/O (2026-09-05)

RUN = sys.argv[1]
MODELS = sys.argv[2:] or ["deepseek-v4-pro"]

SYS = ("You are an immunology / transcriptomics expert. Answer ONLY from established knowledge, not from any "
       "dataset in front of you.")

# key -> (question, which world it anchors)
ANCHORS = {
    "NFKB_TNF": ("In the peripheral blood (PBMC) transcriptome of COVID-19 patients compared with healthy "
                 "controls, would you expect NF-kB inflammatory target genes such as TNF and IL1B to be "
                 "UP-regulated or DOWN-regulated? Give a one-sentence expectation, then end with exactly one "
                 "word on its own line: 'up', 'down', or 'uncertain'.",
                 "cf_cytokine_flip"),
    # MHC2 gates cf_mhc2_injected. Added to this script 2026-09-07: the six frozen models' MHC2 entries were
    # written by the design-time `bulk_cf_scan` (PAPER_NOTES G13) and this on-demand script was never updated to
    # match the manifest, so a NEW model had no MHC2 entry and bulk L3 grading died (grade_l3 refuses to probe
    # live). Prompt mirrors the house ISG/NFKB_TNF format; ADMISSIBLE STATE IS False -- the naive prior is 'up',
    # and a 'down' answer (the correct reading of the real data, which the injected table contradicts) ADMITS
    # the cell. knew_prior is therefore True only when the model answers the naive 'up'.
    "MHC2":     ("In the peripheral blood (PBMC) transcriptome of COVID-19 patients compared with healthy "
                 "controls, would you expect MHC class II genes such as HLA-DRA, HLA-DPA1 and CD74 to be "
                 "UP-regulated or DOWN-regulated? Give a one-sentence expectation, then end with exactly one "
                 "word on its own line: 'up', 'down', or 'uncertain'.",
                 "cf_mhc2_injected"),
    "IG_COMPOSITION": (
                "In the peripheral blood (PBMC) transcriptome of COVID-19 patients compared with healthy "
                "controls, immunoglobulin genes such as IGHG1 and IGKC are strongly up-regulated. Does that "
                "indicate that individual B cells are producing more antibody per cell? Give a one-sentence "
                "expectation, then end with exactly one word on its own line: 'yes', 'no', or 'uncertain'.",
                "cf_composition_artifact"),
    "ISG":      ("In the peripheral blood (PBMC) transcriptome of COVID-19 patients compared with healthy "
                 "controls, would you expect interferon-stimulated genes such as ISG15 and MX1 to be "
                 "UP-regulated or DOWN-regulated? Give a one-sentence expectation, then end with exactly one "
                 "word on its own line: 'up', 'down', or 'uncertain'.",
                 "real (control — the prior AGREES with the data here)"),
}
# SPECIFIC riders only: a generic 'compartments differ' hedge does NOT defuse the world.
RIDERS = ("pbmc", "blood transcriptome", "peripheral blood", "immunoparalysis", "hyporesponsive",
          "monocyte hyporesponsive", "suppressed in blood", "down in blood", "endotoxin tolerance")


def probe(model, key):
    q, world = ANCHORS[key]
    a = (M.chat(model, SYS, q) or "").strip()
    # REFUSAL guard (2026-09-03): a provider-level refusal (claude-fable-5 dual-use layer) is NOT
    # evidence about the model's prior. Returning it as a normal empty/short answer let the
    # gene-symbol regex score knew_prior=False off a truncated fragment, which would silently
    # mis-gate L3 admissibility. Refused -> REFUSED_PROBE, and the caller records knew_prior=None.
    if M.LAST_STOP_REASON.get(model) == "refusal":
        return {"model": model, "anchor": key, "world": world, "tail": "", "volunteered_riders": [],
                "knew_prior": None, "knew_prior_raw": None, "answer": "[REFUSED_PROBE]",
                "refused": True, "note": "Provider-level refusal: NOT evidence about the prior."}

    tail = a.split()[-1].lower().strip(".'\"") if a else ""
    low = a.lower()
    # the rider only counts if it appears WITH a down/suppression claim about blood
    riders = [c for c in RIDERS if c in low and ("down" in low or "suppress" in low or "reduc" in low)]
    if key == "IG_COMPOSITION":
        # the defusing rider here is CELL-COMPOSITION: plasmablast/plasma-cell expansion, more B cells, not
        # more antibody per cell. A model that volunteers that already supplies the world's answer.
        comp = [c for c in ("plasmablast", "plasma cell", "plasma-cell", "cell composition", "composition",
                            "more b cells", "expansion", "proportion", "frequency of", "cell-type shift")
                if c in low]
        raw = (tail == "yes") and not comp
        return {"model": model, "anchor": key, "world": world, "tail": tail, "volunteered_riders": comp,
                "knew_prior": raw, "knew_prior_raw": raw, "answer": a[:700],
                "note": "knew_prior=True means it attributes the Ig signal to PER-CELL output without "
                        "volunteering plasmablast expansion — the composition confound the world tests."}
    if key == "MHC2":
        # Injected world (cf_tmprss15 polarity): ADMISSIBLE STATE IS False. The naive prior is 'up';
        # 'down' is the correct reading of the REAL data, which the injected table contradicts, so a
        # 'down' answer ADMITS the cell. No rider subtraction -- matches the frozen bulk_cf_scan entries.
        raw = (tail == "up")
        return {"model": model, "anchor": key, "world": world, "tail": tail, "volunteered_riders": riders,
                "knew_prior": raw, "knew_prior_raw": raw, "answer": a[:700],
                "prior_expected": "up", "measured": "DOWN -0.55/-0.55 (padj ~4e-4)",
                "note": "ADMISSIBLE STATE IS False (injected world). The model must hold 'COVID PBMC => MHC "
                        "class II DOWN' -- the correct reading of the real data -- and the INJECTED table "
                        "contradicts THAT prior. A 'down' answer therefore ADMITS the cell.",
                "provenance": "tracks/bulk_rnaseq/L3/prior_probe.py 2026-09-07 (anchor added; frozen models "
                              "came from bulk_cf_scan 2026-08-22, PAPER_NOTES G13)"}
    if key == "NFKB_TNF":
        raw = (tail == "up") and not riders
    else:                                     # ISG control: the prior and the data both say UP
        raw = (tail == "up")
    return {"model": model, "anchor": key, "world": world, "tail": tail, "volunteered_riders": riders,
            "knew_prior": raw, "knew_prior_raw": raw, "answer": a[:700],
            "note": ("ADJUDICATE THE REASON: a generic 'compartments/severity/timing can differ' hedge on an "
                     "UP answer is NOT knowledge of this cohort's PBMC suppression and must not exclude the "
                     "cell. Only a specific blood/PBMC-is-suppressed claim does.")}


def main():
    os.makedirs(RUN, exist_ok=True)
    p = os.path.join(RUN, "prior_probe_cache.json")
    cache = load_cache(RUN)
    print(f"{'model':<18}{'anchor':<11}{'knew_prior':<12}{'riders':<26}tail")
    for m in MODELS:
        for k in ANCHORS:
            ck = f"{m}|{k}"
            if ck in cache and cache[ck].get("tail"):
                r = cache[ck]
                print(f"{m:<18}{k:<11}{str(r['knew_prior']):<12}{str(r.get('volunteered_riders'))[:24]:<26}{r['tail']}  (cached)")
                continue
            r = probe(m, k)
            cache[ck] = r
            save_cache(RUN, cache)      # flush per call
            print(f"{m:<18}{k:<11}{str(r['knew_prior']):<12}{str(r['volunteered_riders'])[:24]:<26}{r['tail']}", flush=True)
    save_cache(RUN, cache)
    print(f"\n[probe] -> {p}")
    print("[probe] ADMISSIBLE = knew_prior True (holds 'COVID => NF-kB targets UP', which the data overturns).")
    print("[probe] If False roster-wide, cf_cytokine_flip is DEAD and the track needs a different flip.")


if __name__ == "__main__":
    main()
