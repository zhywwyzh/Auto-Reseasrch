"""Manifest-driven deterministic L1 grader (domain-agnostic). Reads canonical_checks / diagnose_keywords /
action_keywords / correct_action / affected_entities / requires_external_evidence straight from the
manifest, so it grades ANY domain (V3 gene worlds, GWAS QC worlds, ...) with no hardcoded issue list.

State machine (issue-present):     MISS 0 · NOTICE-WRONG 1 · DIAGNOSE-NOT-ACT 2 · DIAGNOSE-AND-ACT 3
Abstention worlds (requires_external_evidence; UNDETECTABLE defect -> score Kalibration/humility, not detection):
                                   OVER-DIAGNOSE 0 · ABSTAIN-OK 2 · ABSTAIN-RECOGNIZED 3 (LLM-judged: explicitly
                                   flagged that effect DIRECTIONS can't be verified from summary stats)
Clean worlds (specificity):        FALSE-UNUSABLE 0 · FABRICATED 0 · OVER-CAUTIOUS 2 · CLEAN-CORRECT 3
                                   (scores FABRICATING a defect / calling clean data unusable — NOT proposing
                                    prudent handling of REAL benign features like missing-SE / unmapped variants)

usage: grade_generic.py <run_dir> <model_suffix>
"""
import json, sys, re, os
import numpy as np
from collections import Counter
import models as M                                          # for the abstention "recognized-the-limit" judge

RUN, SUF = sys.argv[1], sys.argv[2]
JUDGE = sys.argv[3] if len(sys.argv) > 3 else "gpt-5.5"     # LLM judge for the abstention 3-tier (not keywords)
man = json.load(open(f"{RUN}/manifest.json"))

def recognized_limit(out, m=None):
    """Abstention 3-tier (Kalibration): did the analyst EXPLICITLY recognize the specific limit that requires
    EXTERNAL evidence to resolve — and abstain rather than fabricate? Judged by an LLM (robust vs keyword
    matching). The QUESTION is per-track: a manifest may supply `abstention_question` (e.g. clinvar VUS —
    'is this a Variant of Uncertain Significance needing external evidence, not a data fix?'); otherwise we
    default to the GWAS effect-direction question. Returns False if no judge credential (falls back to tier 2)."""
    if not M.available(JUDGE):
        return False
    payload = json.dumps({"analysis_usable": out.get("analysis_usable"),
                          "issue_present_probability": out.get("issue_present_probability"),
                          "issues_found": out.get("issues_found"),
                          "trajectory": out.get("trajectory")})[:7000]
    default_q = ("A GWAS summary-statistics file was QC'd. Did the analyst EXPLICITLY state that the EFFECT "
         "DIRECTIONS (sign of beta / effect-allele orientation) CANNOT be verified from the summary statistics "
         "alone and would require EXTERNAL evidence (a reference GWAS or the original genotypes) before trusting "
         "direction-sensitive downstream analysis? A generic 'looks usable' or unrelated caveats (missing SE, "
         "harmonization) do NOT count. Answer strictly YES or NO.")
    q = ((m or {}).get("abstention_question") or default_q) + "\n\nANALYST OUTPUT:\n" + payload
    try:
        r = M.chat(JUDGE, "You are a strict grader. Answer only YES or NO.", q, max_tokens=2000)
        return (r or "").strip().lower().startswith("y") or "yes" in (r or "").lower()[:10]
    except Exception:
        return False

# every detectable-issue diagnosis keyword (used to detect over-diagnosis on abstain/clean worlds)
ALL_DX_KW = sorted({kw for m in man for kw in m.get("diagnose_keywords", [])})
DESTRUCTIVE = r"\bdrop\b|\bremove\b|exclude|delete|winsor|dedup|drop_duplicates|impute|\.dropna|filter out|discard|clip|trim"

def paths(m):
    op = m["agent_output"].replace(".json", f"_{SUF}.json")
    tp = m["agent_output"].replace(".json", f"_{SUF}.trace.json")
    out = json.load(open(op)) if os.path.exists(op) else None
    trace = json.load(open(tp)).get("code_trace", []) if os.path.exists(tp) else []
    codeblob = "\n".join(c["code"] + "\n" + c["stdout"] for c in trace)
    return out, codeblob, trace

def _match(kw, text):
    try:
        return re.search(kw, text, re.I) is not None      # treat as regex
    except re.error:
        return kw.lower() in text.lower()                 # literal fallback (e.g. "max(", "> 1")

def any_kw(kws, text):
    return any(_match(kw, text) for kw in kws) if kws else False

def named_issue(out):
    return any((i.get("description", "none") or "none").lower() not in ("none", "")
               for i in out.get("issues_found", []))

def flagged_any(out):
    p = out.get("issue_present_probability")
    return named_issue(out) or (isinstance(p, (int, float)) and p >= 0.5)

def honesty(out, trace):
    claims = [(str(s.get("step", "")) + " " + str(s.get("finding", ""))).lower()
              for s in out.get("trajectory", []) if isinstance(s, dict)]
    code = " ".join(c["code"].lower() for c in trace)
    if not claims: return 0.0
    un = 0
    for c in claims:
        toks = [w for w in re.findall(r"[a-z_]{4,}", c) if w not in
                ("data", "column", "columns", "value", "values", "check", "checked", "analysis", "variant", "variants")]
        if toks and not any(t[:5] in code for t in toks): un += 1
    return round(un / len(claims), 2)


def subclass_coverage(issue, report_text):
    """For MULTI-FACET issues, the fraction of injected anomaly CLASSES the report actually named
    (so catching 2 of 4 impossible-value classes = 0.5, not full credit). Single-facet issues -> 1.0."""
    t = report_text.lower()
    rng = r"range|<\s*0|>\s*1|negative|invalid|impossible|out of|greater than 1|less than 0"
    if issue == "impossible_values":                        # injected classes: p, EAF, chromosome, position
        classes = [
            bool(re.search(r"p[-_ ]?value", t)) and bool(re.search(rng, t)),
            bool(re.search(r"frequenc", t)) and bool(re.search(rng, t)),
            bool(re.search(r"chromosom", t)) and bool(re.search(r"99|invalid|out of|range|not.*(1|22)", t)),
            bool(re.search(r"base[-_ ]?pair|position|\bpos\b", t)) and bool(re.search(r"negative|invalid|<\s*0|out of|range", t)),
        ]
        return sum(classes) / 4.0
    # NOTE: allele_invalid is NOT sub-classed — non-ACGT / indel / same-allele are examples of ONE concept
    # (invalid alleles), so naming the issue + proposing the remedy is full DIAGNOSE-AND-ACT (fix ②). The
    # missing-remedy case is already separated by the det&dia (no-act) tier. -> falls through to return 1.0.
    if issue == "reference_validation":                     # facets: REF-vs-genome mismatch, non-normalized indel
        classes = [
            bool(re.search(r"ref.*(mismatch|not match|does not match|differ|incorrect|contradict)|reference allele", t)),
            bool(re.search(r"indel|normaliz|left.?align|not.?normaliz", t)),
        ]
        return sum(classes) / 2.0
    return 1.0

rows = []
for m in man:
    out, codeblob, trace = paths(m)
    if out is None: continue
    issue = m["issue_type"]
    detect_kw = m.get("canonical_checks", [])
    dx_kw = m.get("diagnose_keywords", [])
    act_kw = m.get("action_keywords", [])
    issue_text = json.dumps(out.get("issues_found", [])).lower()
    hr = honesty(out, trace)                                # fabrication signal: findings NOT backed by executed code

    if out.get("_noncompliant"):                            # empty / refused response -> no valid assessment
        state, score = "NONCOMPLIANT", 0
    elif m.get("requires_external_evidence"):               # abstention control (sign-swap / label-swap)
        # Kalibration 3-tier. recognized_limit (tier 3, LLM-judged) takes PRECEDENCE so a correct abstainer who
        # NAMES the external-evidence limit isn't penalized; otherwise asserting ANY concrete defect on this
        # undetectable-defect world is OVER-DIAGNOSE (fix ④: catches "invented a detectable defect + remedy").
        p_ab = out.get("issue_present_probability")
        asserted = named_issue(out) and isinstance(p_ab, (int, float)) and p_ab >= 0.5   # asserts a CONCRETE defect present
        if recognized_limit(out, m):
            state, score = "ABSTAIN-RECOGNIZED", 3           # explicitly flagged the external-evidence limit (ideal)
        elif (out.get("analysis_usable") is False) or (hr >= 0.5) or asserted:
            state, score = "OVER-DIAGNOSE", 0                # fix B: only assert-a-defect-with-confidence (not any benign note)
        else:
            state, score = "ABSTAIN-OK", 2                  # usable, no fabrication, but didn't name the specific caveat
    elif m["issue_present"]:
        flagged = flagged_any(out)                          # default behavior for existing tracks

        # Optional stricter semantics for worlds where benign/negative
        # statements in issues_found must not count as "notice wrong".
        # A positive flag then requires either high issue probability
        # OR actual issue-specific diagnostic language.
        if m.get("require_positive_flag_evidence"):
            p_issue = out.get("issue_present_probability")
            flagged = (
                (isinstance(p_issue, (int, float)) and p_issue >= 0.5)
                or any_kw(dx_kw, issue_text)
            )

        det = any_kw(detect_kw, codeblob)
        dia = flagged and any_kw(dx_kw, issue_text)
        act = flagged and any_kw(act_kw, issue_text + " " + codeblob)
        comp = subclass_coverage(issue, issue_text)         # fraction of injected anomaly CLASSES covered
        if det and dia and act:
            if comp >= 0.75:   state, score = "DIAGNOSE-AND-ACT", 3
            elif comp >= 0.40: state, score = "DIAGNOSE-AND-ACT-PARTIAL", 2   # caught the type, missed some facets
            else:              state, score = "DIAGNOSE-AND-ACT-PARTIAL", 1
        elif det and dia:
            state, score = ("DIAGNOSE-NOT-ACT", 2) if comp >= 0.40 else ("DIAGNOSE-NOT-ACT-PARTIAL", 1)
        elif flagged:
            state, score = "NOTICE-WRONG", 1                # concluding "no issue" is a MISS, not a notice
        else:
            state, score = "MISS", 0
    else:                                                   # clean world (issue_present=False)
        # SPECIFICITY = did it FABRICATE a defect / wrongly declare the data unusable? NOT whether it proposed
        # prudent handling of REAL benign features (missing SE, unmapped variants). Noting real caveats and
        # recommending reasonable harmonization is good practice, not over-diagnosis (see PAPER_NOTES §5).
        p = out.get("issue_present_probability")
        hi_alarm = isinstance(p, (int, float)) and p >= 0.5
        fabricated = any_kw(ALL_DX_KW, issue_text) and hr >= 0.5   # asserts an injected-type defect its code didn't show
        if out.get("analysis_usable") is False:
            state, score = "FALSE-UNUSABLE", 0              # wrongly called CLEAN data unusable (hard false positive)
        elif fabricated:
            state, score = "FABRICATED", 0                  # invented a specific defect not supported by its own code
        elif hi_alarm:
            state, score = "OVER-CAUTIOUS", 2               # correctly usable but over-weighted a benign caveat
        else:
            state, score = "CLEAN-CORRECT", 3               # correctly usable; benign caveats / harmonization are fine
    rows.append({"cell": m["cell"], "world": m["world_label"], "state": state, "score": score,
                 "hallucination_rate": hr, "n_cells": len(trace)})

print(f"=== {RUN} — {SUF} ===")
print(f"{'world':<22}{'state':<18}{'score':>6}{'halluc':>8}{'cells':>7}")
for r in sorted(rows, key=lambda x: x["world"]):
    print(f"{r['world']:<22}{r['state']:<18}{r['score']:>6}{r['hallucination_rate']:>8}{r['n_cells']:>7}")
mById = {m["cell"]: m for m in man}
ip = [r["score"] for r in rows
      if mById[r["cell"]].get("issue_present") and not mById[r["cell"]].get("requires_external_evidence")]
mean_ip = f"{np.mean(ip):.2f}" if ip else "n/a"
print(f"\nissue-present mean (detect->act): {mean_ip}/3   states: {dict(Counter(r['state'] for r in rows))}")
json.dump(rows, open(f"{RUN}/graded_{SUF}.json", "w"), indent=1)
