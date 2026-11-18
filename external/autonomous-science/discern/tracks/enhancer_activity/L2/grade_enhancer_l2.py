"""enhancer_activity L2 grader (C axis, 0-3) — 3 analyses (divergence / conservation / ranking), cross-species
DATA-CONFOUND focus. Value-checks the agent's family-set CSV against the solver golden set; flag credit only from
declared-flag fields. Fabrication guard (0 code cells -> cap 1); forced-unusable -> cap 1.

usage: grade_enhancer_l2.py <RUN_DIR> <model>
"""
import json, os, sys, re
import pandas as pd

RUN, SUF = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from refusal_guard import is_refusal

CUES = {
    "species_batch_confound": ("batch", "per-species", "per species", "normaliz", "offset", "scale", "z-norm", "outlier species"),
    # + capping/saturation synonyms (verify 2026-08-13): glm named the trap exactly — "Saturation/capping
    # artifact: 15 values are exact round numbers ... capped/saturated measurements" — and excluded them
    # (leaked=0.00, F1=1.00), but no cue matched, so a perfect answer graded 2 instead of 3. "capped"/
    # "capping" (not bare "cap", which hits capture/capacity) + saturat/clipp/ceiling/round number.
    # THIRD synonym gap on this one world (verify 2026-08-13). Models describe the same artifact in their own
    # vocabulary and the cue list keeps missing it: glm "Saturation/capping artifact"; kimi "15 single-species
    # enrichment SPIKES (|score|>=8) ... SPURIOUS ... false-positive"; claude "15 CORRUPTED/SENTINEL enrichment
    # values (exact 9, 10.5, 11, 12, -14; real data span -5.84..2.82)". All three excluded them correctly
    # (leaked=0.00, F1 0.97-1.00) yet scored `flagged=False`. Added spike/spurious/sentinel/corrupt/anomal.
    # NOTE for the paper: keyword flag-detection has now under-credited 3 of 6 models on ONE world — the
    # failure mode is systematic, not a one-off (see PAPER_NOTES G8g).
    "enrichment_outlier": ("outlier", "implausib", "out-of-range", "out of range", "data error", "data-entry",
                           "invalid", "range check", "capped", "capping", "saturat", "clipp", "ceiling",
                           "round number", "spike", "spurious", "sentinel", "corrupt", "anomal"),
    "phylo_pseudoreplication": ("phylo", "clade", "sister", "neighbour", "neighbor", "independen", "pseudoreplic", "single species", "correlated", "one species"),
    "species_duplicate": ("duplicat", "one-per-species", "one per species", "dedup", "merge", "same species"),
    "gc_conservation_bias": ("gc", "g+c", "composition", "adjust", "regress", "normaliz"),
    "alignment_quality": ("alignment", "length", "truncat", "heterogen", "unreliable", "gap", "indel"),
    "conservation_as_proxy": ("not activity", "decoupl", "turnover", "proxy", "prior", "sequence property", "does not predict", "not predictive"),
    "ortholog_family_leakage": ("dedup", "double-count", "double count", "ortholog", "per-row", "per row", "aggregate", "one per family", "family level"),
    "duplicate_contamination": ("duplicat", "exact", "dedup", "merge"),
    "reference_species_bias": ("reference", "human", "absolute", "relative", "bias"),
}
FLAG_GATED = {"gc_conservation_bias", "conservation_as_proxy"}     # correct family-set regardless -> discriminator is the flag
LEAKED = {"enrichment_outlier", "phylo_pseudoreplication", "species_duplicate"}   # injected FAKE families -> must exclude
_PRECISION_UNUSED = {"species_batch_confound", "ortholog_family_leakage", "reference_species_bias", "duplicate_contamination"}


def load_out(cell):
    p = f"{RUN}/out_cell{cell:03d}_{SUF}.json"
    if not os.path.exists(p):
        return None
    d = json.load(open(p))
    if d.get("_noncompliant"):
        # REFUSED guard (2026-09-03): a model-level refusal is graded 0/REFUSED, not skipped.
        if is_refusal(d, p, SUF):
            d["_refused"] = True
            return d
        return None
    tr = p.replace(".json", ".trace.json")
    if os.path.exists(tr):
        d["_n_code_cells"] = len(json.load(open(tr)).get("code_trace") or [])
    return d


def caps(out, score):
    if out.get("_n_code_cells") == 0:
        score = min(score, 1)
    if out.get("analysis_usable") is False:
        score = min(score, 1)
    return score


def _values_only(x):
    acc = []
    def rec(v):
        if isinstance(v, dict): [rec(u) for u in v.values()]
        elif isinstance(v, (list, tuple)): [rec(u) for u in v]
        elif v is not None: acc.append(str(v))
    rec(x); return acc


def flag_cues(out, *words):
    fields = [out.get("issues_found"), out.get("method"), out.get("method_note"), out.get("reliability_assessment"), out.get("notes")]
    b = " | ".join(_values_only([f for f in fields if f])).lower()
    return any(w in b for w in words)


def issues_cues(out, *words):
    """'Named the pitfall' credit requires the flag DECLARED in issues_found (values-only) — an
    agent describing its own method is not flagging (audit B1; the bulk lesson)."""
    b = " | ".join(_values_only(out.get("issues_found") or [])).lower()
    return any(w in b for w in words)


def norm_family(x):
    """Canonicalize: strip trailing _<assembly> AND any leading 'chr' (alias-robustness: gpt-4.1
    emitted 'chr'-less coordinates on one world — format deviance shouldn't zero a match the way
    CD16-vs-FCGR3A once did; both sides normalize identically so this is purely permissive)."""
    return re.sub(r"^chr", "", re.sub(r"_[A-Za-z0-9]+$", "", str(x).strip()), flags=re.I)


def agent_families(out):
    p = out.get("output_path")
    if not p or not os.path.exists(p):
        return None
    try:
        df = pd.read_csv(p)
    except Exception:
        return None
    col = next((c for c in df.columns if c.lower() in ("family", "coordinate", "coord", "enhancer", "base")), df.columns[0])
    return set(norm_family(v) for v in df[col].dropna())


def f1(pred, gold):
    if not pred:
        return 0.0, 0.0, 0.0
    tp = len(pred & gold); prec = tp / len(pred); rec = tp / max(1, len(gold))
    return (2 * prec * rec / (prec + rec) if prec + rec else 0.0), prec, rec


def grade(m, out):
    pred = agent_families(out)
    if pred is None or len(pred) < 1:
        return 0, "no family CSV"
    gold = set(norm_family(f) for f in m["gold"]["golden_set"])
    F, prec, rec = f1(pred, gold)
    w = m["world_label"]
    # ---- BRITTLE-CUTOFF ADJUSTMENT (conservation sub-task ONLY; owner ruling 2026-08-13) -----------------
    # The conservation golden is "top 69 of 279 families by cons_gc_adj". That cutoff sits in the DENSEST part
    # of the metric: 85% of families lie within +/-0.01 of it, on a metric whose entire range is 0.043. So set
    # membership is decided by tiny differences in how conservation is computed, not by whether the science is
    # right. Measured by perturbation: a metric difference of sd 0.005 -> expected F1 0.64; sd 0.01 -> 0.50;
    # sd 0.02 -> 0.38. Against the original 0.55 gate, a model whose estimate differs by a quarter of the
    # metric's range fails regardless of method quality — and indeed ALL four real models land at F1 0.17-0.42
    # (incl. every clean world) while the personas score 1.00 only because they are handed the golden's own
    # numbers and never recompute. (NOT a wrong-metric-variant artifact: ranking by RAW cons instead of
    # GC-adjusted still gives F1 0.91.) The proper fix is to grade RANK CORRELATION, which needs a scored
    # ranking the agents were never asked for; until that re-run happens, widen the SET-BASED thresholds here
    # so they price metric agreement honestly. `leaked` / `recovered` are NOT widened — they are computed
    # against an exact injected family list, so they are not cutoff-brittle.
    BRITTLE = "conservation" in RUN
    if w == "clean":
        if BRITTLE:
            return (3 if F >= 0.45 else 2 if F >= 0.35 else 1 if F >= 0.25 else 0), f"F1={F:.2f} [brittle-adj]"
        return (3 if F >= 0.7 else 2 if F >= 0.55 else 1 if F >= 0.35 else 0), f"F1={F:.2f}"
    flagged = issues_cues(out, *CUES.get(w, ()))     # audit B1: named-the-pitfall lives in issues_found
    extra = ""
    if w in LEAKED:
        aff = set(norm_family(f) for f in m["gold"]["families"])
        leaked = len(pred & aff) / max(1, len(aff))
        # audit B2: leak-avoidance alone is not accuracy — the returned set must also be RIGHT
        ok = leaked <= 0.25 and rec >= 0.6 and prec >= 0.6
        extra = f" leaked={leaked:.2f}"
    elif w == "alignment_quality":
        aff = set(norm_family(f) for f in m["gold"]["families"])
        recov = len(pred & aff) / max(1, len(aff))
        ok = recov >= 0.6 and prec >= 0.6 and rec >= 0.6                      # audit B2
        extra = f" recovered={recov:.2f}"
    elif w in FLAG_GATED:
        ok = F >= (0.35 if BRITTLE else 0.55)                                  # brittle-cutoff adjustment
    else:  # PRECISION worlds (naive method -> wrong set)
        ok = (prec >= 0.35 and rec >= 0.35) if BRITTLE else (prec >= 0.7 and rec >= 0.6)
    # audit B3: accuracy CAPS everywhere — flagged-but-wrong is 1, never 2.
    # FLAG_GATED worlds additionally use BOTH-REQUIRED (crispr threshold_sensitivity precedent):
    # validation measured naive F1 0.91-1.00 on these (accuracy carries no signal — the graded
    # skill IS the adjustment/interpretation), so accurate-but-silent also caps at 1 there.
    if w in FLAG_GATED:
        s = 3 if ok and flagged else 1 if (ok or flagged) else 0
    else:
        s = 3 if ok and flagged else 2 if ok else 1 if flagged else 0
    return s, f"F1={F:.2f} P={prec:.2f} R={rec:.2f} flagged={flagged}{extra}"


def main():
    man = json.load(open(f"{RUN}/manifest.json"))
    rows = []
    for m in man:
        out = load_out(m["cell"])
        if out is None:
            rows.append({"cell": m["cell"], "world": m["world_label"], "state": "NO-OUTPUT", "score": 0}); continue
        if out.get("_refused"):
            rows.append({"cell": m["cell"], "world": m["world_label"], "state": "REFUSED", "score": 0}); continue
        s, why = grade(m, out); s = caps(out, s)
        rows.append({"cell": m["cell"], "world": m["world_label"], "issue_type": m["issue_type"], "state": "OK", "detail": why, "score": s})
    json.dump(rows, open(f"{RUN}/graded_{SUF}.json", "w"), indent=1)
    print(f"graded -> {RUN}/graded_{SUF}.json")
    for r in rows:
        print(f"  cell{r['cell']:03d} [{r['world']:<26}] {r.get('issue_type',''):<13} {r['state']:<9} {r.get('detail','')}  -> C={r['score']}")


if __name__ == "__main__":
    main()
