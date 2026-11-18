"""enhancer_activity L3 anti-recall probe — the admissibility gate for the DISCOVERY-VALIDITY worlds.

This track is NOT a prior-flip (ADD_A_TRACK GATE 0 closed that route: conservation=>function probed
knew_prior=False 0/6 because models volunteer sequence turnover). The worlds are process counterfactuals, so
the probe here is an ANTI-RECALL check rather than a prior check: it confirms the model does NOT already
recognise the focus coordinate and its lineage story from memory. If it DID, it could answer from recall
instead of from the supplied evidence, and the cell would be confounded.

  knew_prior=False  -> does NOT recognise the locus -> must reason from the data -> ADMISSIBLE (the expected
                       and required state; manifest carries knew_prior_admissible=False).
  knew_prior=True   -> claims to recognise it -> CONFOUNDED (grade_l3 excludes the cell).

FABRICATION ADJUDICATION (this is why `tail` alone must never decide): a model can answer "known" and be
CONFABULATING. deepseek did this twice -- a fake VISTA accession for the 16:9.22 Mb anchor, and for
chr11:67,914,328 it claimed "ENCODE cCRE EH11E0679143, intron of CHKA": the accession is malformed (real human
cCRE IDs are EH38E#######, EH38 = build, not chromosome) and CHKA sits at 11q13.2 ~68.14 Mb, ~230 kb away and
not an intron. A keyword read of the tail would have wrongly excluded that cell. `knew_prior_raw` preserves
what was said; `adjudication` records why it was overridden.

usage: prior_probe.py <run_dir> <model> [<model> ...]
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
import models as M
from probe_cache_io import load_cache, save_cache   # frozen-safe cache I/O (2026-09-05)

RUN = sys.argv[1]
MODELS = sys.argv[2:] or ["gpt-4.1"]

SYS = ("You are a comparative-genomics expert. Answer ONLY from established knowledge of published regulatory "
       "elements — you have no dataset in front of you.")

# key -> (human coordinate as shown to the model, which world it anchors)
ANCHORS = {
    "enh_15_65108751": ("chr15:65,108,751-65,108,937 (hg38)", "real"),
    "enh_16_27482121": ("chr16:27,482,121-27,482,306 (hg38)", "cf_miscaused"),
    "enh_20_30301259": ("chr20:30,301,259-30,301,445 (hg38)", "cf_confounded"),
}


def probe(model, key):
    coord, world = ANCHORS[key]
    q = (f"Do you recognise the human genomic region {coord} as a specifically characterised enhancer or "
         f"regulatory element with a known target gene and a known species/lineage-specific activity pattern? "
         f"Answer in 1-2 sentences, then end with exactly one word on its own line: either 'known' or "
         f"'unknown'.")
    ans = (M.chat(model, SYS, q) or "").strip()
    # REFUSAL guard (2026-09-03): a provider-level refusal (claude-fable-5 dual-use layer) is NOT
    # evidence about the model's prior. Returning it as a normal empty/short answer let the
    # gene-symbol regex score knew_prior=False off a truncated fragment, which would silently
    # mis-gate L3 admissibility. Refused -> REFUSED_PROBE, and the caller records knew_prior=None.
    if M.LAST_STOP_REASON.get(model) == "refusal":
        return {"anchor": key, "world": world, "coordinate": coord, "answer": "[REFUSED_PROBE]",
                "tail": "", "knew_prior": None, "knew_prior_raw": None, "refused": True,
                "note": "Provider-level refusal: NOT evidence about the prior."}

    tail = ans.split()[-1].lower().strip(".") if ans else ""
    raw = ("known" in tail and "un" not in tail) if tail else None
    return {"anchor": key, "world": world, "coordinate": coord, "answer": ans[:700], "tail": tail,
            "knew_prior": raw, "knew_prior_raw": raw,
            "note": ("If knew_prior is True, VERIFY the claimed element/accession before accepting it — a "
                     "confabulated accession must be adjudicated to False, not used to exclude the cell.")}



# ---------------------------------------------------------------------------------------------------
# METHODOLOGICAL-PRIOR PROBE (added 2026-08-16 — the gate that actually establishes a CONTRADICTION).
#
# The anti-recall probe above only rules out RETRIEVAL. It does NOT establish that anything conflicts:
# knew_prior=False there means "no belief about this locus at all", so nothing is being overturned. Every
# other L3 track gates on a prior the DATA CONTRADICTS; enhancer's prior is METHODOLOGICAL rather than
# per-fact, and it had never been measured. This probes it.
#
#   knew_prior=True  -> the model reaches for a human/lineage REGULATORY INNOVATION reading -> the world's
#                       data (batch offset / baboon-driven) CONTRADICTS it -> genuine test -> ADMISSIBLE.
#   knew_prior=False -> the model spontaneously raises assay/batch/normalisation or selection-bias caveats
#                       FIRST -> it already supplies the rider, so there is no prior to overturn ->
#                       principle-with-a-rider, the failure that killed conservation=>function (0/6) and the
#                       paralog flip (8/8). If this comes back False roster-wide, the affected world is DEAD.
#
# Deliberately coordinate-free: no locus, no numbers from the build, nothing that could be recalled.
# ---------------------------------------------------------------------------------------------------
HEURISTIC = {
    "heur_human_elevation": (
        "In a cross-species reporter (MPRA) experiment measuring the activity of orthologous enhancers in "
        "several primate species, one enhancer shows much HIGHER activity in human than in every other "
        "species tested. What is the most likely explanation?",
        "cf_confounded"),
    "heur_diff_from_human": (
        "In a cross-species enhancer study, a researcher ranks all enhancer families by the largest absolute "
        "difference between any species' activity and the human activity, then takes the top-ranked family. "
        "What does that top-ranked family most likely represent?",
        "cf_miscaused"),
}
# PER-WORLD rider cues. A generic "there could be artifacts" does NOT defuse a world -- only the SPECIFIC
# rider that would neutralise THAT world's construction does. Checked against real answers 2026-08-16:
#   - claude said "all orthologs are ASSAYED in the same trans environment" (an argument FOR a cis difference)
#     and "rule out mapping/alignment ARTIFACTS" -- neither is a per-species genome-wide offset, so neither
#     defuses cf_confounded. A generic cue list wrongly scored that False.
#   - claude DID lead with "the ranking statistic is a maximum ... most likely an extreme-value outlier",
#     which is exactly the rider that defuses cf_miscaused. That one is a genuine False.
RIDERS_BY_WORLD = {
    # cf_confounded injects a PER-SPECIES GENOME-WIDE offset. Only a cross-sample/batch-normalisation caveat
    # defuses it; alignment/orthology artifacts are a different concern and do not.
    "cf_confounded": ("batch", "genome-wide", "genome wide", "global shift", "median", "normaliz", "normalis",
                      "per-species offset", "library", "depth differences between species",
                      "compare .* other enhancers", "distribution of all"),
    # cf_miscaused is a SELECTION-BIAS world (rank on max|species - human|). The defusing rider is the
    # extreme-value / max-statistic / any-species-direction critique.
    "cf_miscaused": ("extreme.value", "extreme value", "outlier", "max(imum)? over", "maximum over",
                     "selection bias", "winner.s curse", "regression to the mean", "any species",
                     "either direction", "does not mean human", "not necessarily human", "unshrunk"),
}
INNOVATION_CUES = ("human-specific", "human specific", "lineage-specific", "lineage specific", "innovation",
                   "gain of function", "gain-of-function", "adaptive", "evolutionary change",
                   "regulatory innovation", "derived", "positive selection", "human-accelerated",
                   "human accelerated", "human-gained", "human gained")


def probe_heuristic(model, key):
    q, world = HEURISTIC[key]
    ans = (M.chat(model, SYS_H, q + " Answer in 2-3 sentences.") or "").strip()
    low = ans.lower()
    riders = [c for c in RIDERS_BY_WORLD[world] if re.search(c, low)]
    innov = [c for c in INNOVATION_CUES if c in low]
    # knew_prior = holds the innovation reading WITHOUT volunteering the methodological rider
    knew = bool(innov) and not riders
    return {"probe": key, "world": world, "question": q, "answer": ans[:900],
            "innovation_cues": innov, "rider_cues": riders, "knew_prior": knew,
            "note": "knew_prior=True means the innovation reading was reached WITHOUT volunteering an "
                    "assay/selection caveat. Any rider => the model supplies its own correction => no prior."}


SYS_H = ("You are a comparative-genomics expert. Answer from general scientific reasoning; you have no "
         "specific dataset in front of you.")


# GATE REWIRE (made automatic 2026-09-07).
#
# On 2026-08-16 the admissibility gate for the ANCHORS worlds was switched from the ANTI-RECALL probe to the
# METHODOLOGICAL prior above, and the six frozen models' cache entries were rewired BY HAND: the heuristic
# answer was copied onto the anchor key that grade_l3 reads, keeping the anti-recall verdict under
# `anti_recall` and stamping `gate_source`. main()'s default mode was never updated to do this, so a NEW model
# got only the anti-recall answer under the gate key. glm-5.3 answered the anti-recall question honestly
# ("I do not recognise chr20:30,301,259-30,301,445"), that False was read as the GATE, and cf_confounded was
# scored CONFOUNDED-EXCLUDED -- while the frozen models, gated on the methodological question, were admitted.
# The default mode now reproduces the rewire for every model, so the trap cannot recur.
GATE_SOURCE = {world: probe_key for probe_key, (_q, world) in HEURISTIC.items()}


def rewire_gate(cache, model, anchor_key, world):
    """Point the anchor key grade_l3 reads at the METHODOLOGICAL prior, preserving the anti-recall verdict."""
    src = GATE_SOURCE.get(world)
    if not src:
        return None                                   # world has no methodological gate (e.g. `real`)
    h = cache.get(f"{model}|{src}")
    if not h:
        return None
    gate_key = f"{model}|{anchor_key}"
    prev = cache.get(gate_key) or {}
    if prev.get("gate_source") == src:
        return prev                                   # already rewired
    cache[gate_key] = {
        "anti_recall": prev.get("knew_prior"),        # keep the recall verdict; it is NOT the gate
        "anti_recall_answer": (prev.get("answer") or "")[:700] or None,
        "knew_prior": h.get("knew_prior"),
        "gate_source": src,
        "rewired": ("2026-08-16 gate switched from anti-recall to the methodological prior; anti_recall "
                    "preserved. admissible flipped False->True on the manifest. Applied automatically by "
                    "prior_probe.py since 2026-09-07."),
        "answer": h.get("answer"),
    }
    return cache[gate_key]


def main():
    os.makedirs(RUN, exist_ok=True)
    p = os.path.join(RUN, "prior_probe_cache.json")
    cache = load_cache(RUN)
    if os.environ.get("PROBE_MODE") == "heuristic":
        print(f"{'model':<18}{'probe':<24}{'world':<16}{'knew_prior':<12}riders / innovation")
        for model in MODELS:
            for key in HEURISTIC:
                k = f"{model}|{key}"
                if k in cache:
                    r = cache[k]
                else:
                    r = probe_heuristic(model, key); cache[k] = r
                    save_cache(RUN, cache)
                print(f"{model:<18}{key:<24}{r['world']:<16}{str(r['knew_prior']):<12}"
                      f"{str(r['rider_cues'])[:34]} / {str(r['innovation_cues'])[:30]}", flush=True)
        save_cache(RUN, cache)
        print(f"\n[probe] -> {p}")
        print("[probe] ADMISSIBLE = knew_prior True (holds the innovation reading the world contradicts).")
        print("[probe] If False roster-wide, that world has NO prior to overturn and must be DROPPED.")
        return
    print(f"{'model':<18}{'anchor':<20}{'world':<16}{'knew_prior':<12}tail")
    for model in MODELS:
        for key in ANCHORS:
            k = f"{model}|{key}"
            if k in cache:
                r = cache[k]
                print(f"{model:<18}{key:<20}{ANCHORS[key][1]:<16}{str(r.get('knew_prior')):<12}{r.get('tail')}  (cached)")
                continue
            r = probe(model, key)
            cache[k] = r
            save_cache(RUN, cache)      # flush per call — a timeout must not discard the run
            print(f"{model:<18}{key:<20}{r['world']:<16}{str(r['knew_prior']):<12}{r['tail']}", flush=True)
    # The anti-recall answers above are NOT the gate. Run the methodological prior and rewire it onto the
    # anchor keys grade_l3 reads, exactly as the frozen roster was treated.
    print()
    for model in MODELS:
        for hkey in HEURISTIC:
            hk = f"{model}|{hkey}"
            if hk not in cache:
                cache[hk] = probe_heuristic(model, hkey); save_cache(RUN, cache)
        for akey, (_coord, world) in ANCHORS.items():
            r = rewire_gate(cache, model, akey, world)
            if r:
                print(f"[gate] {model:<18}{akey:<20}{world:<16}knew_prior={str(r['knew_prior']):<6}"
                      f"(from {r['gate_source']}; anti_recall={r.get('anti_recall')})")
    save_cache(RUN, cache)
    print(f"\n[probe] -> {p}")
    print("[probe] GATE = the METHODOLOGICAL prior (knew_prior True = holds the innovation reading the world")
    print("[probe] contradicts). The anti-recall verdict is preserved under `anti_recall` and is NOT the gate.")


if __name__ == "__main__":
    main()
