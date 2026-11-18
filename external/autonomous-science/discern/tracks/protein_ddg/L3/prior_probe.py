"""protein_ddg L3 prior-knowledge probe — GATE 0 for the "stabilizing mutation ESM misses" flip.

THE FLIP under test: a mutation whose MEASURED ddG is STABILIZING while ESM (and the naive biophysical prior)
call it destabilizing. It only tests "trust the data over the prior" if the model HOLDS the destabilizing prior.

  knew_prior=True  iff it says DESTABILIZE      -> holds the prior the Tsuboyama measurement contradicts.
  knew_prior=False iff it says STABILIZE        -> no prior to overturn.
  knew_prior=False if it VOLUNTEERS the mechanism (buried-charge relief / desolvation / repacking gain)
                   -> it already knows the exception, so it cannot be surprised -> CONFOUNDED.

WHY THE VOLUNTEER CHECK IS THE WHOLE POINT (ADD_A_TRACK GATE 0): an L3 flip needs a PER-FACT prior that is
commonly WRONG. A "principle-with-a-rider" prior does NOT qualify, because models spontaneously supply the rider.
Prior data: paralog redundancy knew_prior=False 8/8; conservation=>function False 6/6; PPAN essentiality True 6/6.
"Removing an unsatisfied buried charge can stabilize" is EXACTLY such a rider -- if models volunteer it, this
flip is dead and protein gets no L3, the same way enhancer was dropped.

usage: prior_probe.py <run_dir> <model> [<model> ...]
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
import models as M
from probe_cache_io import load_cache, save_cache   # frozen-safe cache I/O (2026-09-05)

RUN = sys.argv[1]
MODELS = sys.argv[2:] or ["gpt-4.1"]

SYS = ("You are a protein-biophysics expert. Answer ONLY from established biophysical knowledge — you have no "
       "experimental dataset in front of you.")

# (mutation, description, measured ddG, ESM LLR) -- all verified against L2/golden/gb1_ddg_golden.csv 2026-08-16.
# ddG > 0 = MORE stable (Tsuboyama convention). Every FLIP candidate is stabilizing-but-ESM-says-destabilizing.
CANDIDATES = {
    "E27F": ("Glu27 -> Phe in the B1 domain of protein G (GB1): a partially buried glutamate "
             "(relative burial ~0.69) replaced by phenylalanine", +1.420, -5.552, "flip"),
    "E27L": ("Glu27 -> Leu in GB1: the same partially buried glutamate replaced by leucine",
             +1.396, -4.094, "flip"),
    "L5F":  ("Leu5 -> Phe in GB1: a fully buried core leucine replaced by phenylalanine",
             +1.817, -4.322, "flip"),
    "L5C":  ("Leu5 -> Cys in GB1: a fully buried core leucine replaced by cysteine",
             +2.529, -5.821, "flip"),
    # CONTROL: genuinely destabilizing and ESM agrees. Models SHOULD say destabilize here. If a model says
    # "destabilize" to everything, this control cannot distinguish a held prior from a constant answer --
    # so a candidate is only usable if the model separates it from this control.
    "A26E": ("Ala26 -> Glu in GB1: a buried alanine replaced by glutamate (charge INTO the core)",
             -3.060, -7.524, "control"),
    # NEUTRAL anchors for the INJECTED cf_destabilizing world. Here the prior we must confirm is
    # "negligible effect" -- a conservative SURFACE substitution. A binary stabilize/destabilize question
    # cannot express that, so role="neutral" asks a THREE-WAY question and knew_prior=True iff the model
    # answers 'negligible'. The injected ddG (-3.60) then contradicts a CORRECT, firmly held prior.
    # Route (b) candidates 2026-08-16. V54C FAILED the gate 3/3 ("destabilize") -- a buried Val->Cys LOSES
    # side-chain volume in the core, which models correctly read as destabilising, so an injected -3.60 would
    # CONFIRM the prior instead of contradicting it. These three are buried but chosen so the swap does NOT
    # obviously lose packing: V54I/V54L ADD volume (beta-branched -> larger hydrophobe) and Y3F removes only a
    # hydroxyl. The world needs a "negligible" prior at a site where a large ddG is still biophysically
    # coherent -- that is the tension V54C failed.
    "V54I": ("Val54 -> Ile in GB1: a fully buried core valine replaced by isoleucine (both beta-branched "
             "hydrophobes; isoleucine is slightly larger)", +0.062, -3.494, "neutral"),
    "V54L": ("Val54 -> Leu in GB1: a fully buried core valine replaced by leucine (both aliphatic "
             "hydrophobes of similar size)", +0.177, -3.157, "neutral"),
    "Y3F":  ("Tyr3 -> Phe in GB1: a buried tyrosine replaced by phenylalanine (identical aromatic ring, "
             "removing only the para-hydroxyl)", -0.035, -4.234, "neutral"),
    "V54C": ("Val54 -> Cys in GB1: a fully buried core valine replaced by cysteine",
             +0.027, -5.717, "neutral"),   # FAILED gate 3/3 -- kept as the record
    "Q2T":  ("Gln2 -> Thr in GB1: a solvent-exposed surface glutamine replaced by threonine",
             +0.000, -1.260, "neutral"),   # RETIRED as the cf anchor (exposed -> injection detectable)
    "E42T": ("Glu42 -> Thr in GB1: a solvent-exposed surface glutamate replaced by threonine",
             +0.002, -1.663, "neutral"),
}

# Volunteering ANY of these = the model already supplies the exception -> principle-with-a-rider -> CONFOUNDED.
RELIEF_CUES = ("charge relief", "buried charge", "unsatisfied", "desolvat", "relieve", "relief",
               "could stabilize", "may stabilize", "might stabilize", "can be stabilizing",
               "repack", "better packing", "improved packing", "hydrophobic burial gain")


def probe(model, mut):
    label, ddg, llr, role = CANDIDATES[mut]
    if role == "neutral":
        q = (f"What effect does the following mutation have on the thermodynamic stability of the folded "
             f"protein?\n\n{label}\n\nAnswer in 1-2 sentences, then end with exactly one word on its own "
             f"line: 'stabilize', 'destabilize', or 'negligible' (use 'negligible' if the effect on folding "
             f"stability is expected to be small, within roughly +/-0.5 kcal/mol).")
    else:
        q = (f"Does the following mutation stabilize or destabilize the folded protein?\n\n{label}\n\n"
             f"Answer in 1-2 sentences, then end with exactly one word on its own line: "
             f"either 'stabilize' or 'destabilize'.")
    ans = (M.chat(model, SYS, q) or "").strip()
    # REFUSAL guard (2026-09-03): a provider-level refusal (claude-fable-5 dual-use layer) is NOT
    # evidence about the model's prior. Returning it as a normal empty/short answer let the
    # gene-symbol regex score knew_prior=False off a truncated fragment, which would silently
    # mis-gate L3 admissibility. Refused -> REFUSED_PROBE, and the caller records knew_prior=None.
    if M.LAST_STOP_REASON.get(model) == "refusal":
        return {"mutation": mut, "role": role, "ddg_measured": ddg, "esm_llr": llr,
                "answer": "[REFUSED_PROBE]", "tail": "", "knew_prior": None,
                "volunteered_relief": [], "refused": True}

    tail = ans.split()[-1].lower().strip(".") if ans else ""
    if role == "neutral":
        # the prior to confirm is "no meaningful effect"; the injection (-3.60) contradicts exactly that
        knew = True if ("negligib" in tail or "neutral" in tail or "small" in tail) else False
        return {"mutation": mut, "role": role, "ddg_measured": ddg, "esm_llr": llr,
                "answer": ans[:700], "tail": tail, "knew_prior": knew, "volunteered_relief": []}
    if not tail:
        knew = None
    elif "destabil" in tail:
        knew = True          # holds the prior the measurement contradicts
    elif "stabil" in tail:
        knew = False         # already expects stabilization -> nothing to overturn
    else:
        knew = None
    volunteered = [c for c in RELIEF_CUES if c in ans.lower()]
    if volunteered and role == "flip":
        knew = False         # knows the exception -> cannot be surprised
    return {"mutation": mut, "role": role, "ddg_measured": ddg, "esm_llr": llr,
            "answer": ans[:700], "tail": tail, "knew_prior": knew, "volunteered_relief": volunteered}


def main():
    os.makedirs(RUN, exist_ok=True)
    p = os.path.join(RUN, "prior_probe_cache.json")
    cache = load_cache(RUN)
    print(f"{'model':<18}{'mut':<7}{'role':<9}{'knew_prior':<12}{'volunteered relief':<34}tail")
    for model in MODELS:
        for mut in CANDIDATES:
            if f"{model}|{mut}" in cache:            # resume: never re-bill a completed probe
                continue
            r = probe(model, mut)
            cache[f"{model}|{mut}"] = r
            save_cache(RUN, cache)  # FLUSH PER CALL -- pass 1 hit a timeout and lost all 25
            print(f"{model:<18}{mut:<7}{r['role']:<9}{str(r['knew_prior']):<12}"
                  f"{str(r['volunteered_relief'])[:32]:<34}{r['tail']}", flush=True)
    print(f"\n[probe] -> {p}")
    print("[probe] GATE: a candidate is USABLE only if knew_prior=True for most models AND few volunteer the")
    print("[probe] relief mechanism. If every flip candidate probes False, protein L3 is DROPPED (cf. enhancer).")


if __name__ == "__main__":
    main()
