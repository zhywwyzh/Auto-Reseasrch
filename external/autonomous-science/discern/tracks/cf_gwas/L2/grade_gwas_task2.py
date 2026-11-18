"""LEVEL 2 - Task 2 deterministic grader (HARDER confounds). Grades the agent's reported loci against the
explicit per-world ground truth, from the natural output (loci + notes + data_quality_flags) — no coaching
fields in the schema.

Per world:
  recall/precision of leads vs reference_leads · n_loci vs correct_n_loci · issue-specific handling:
    masked_secondary   -> detected 2 independent signals in the masked locus?
    mega_locus         -> avoided fragmenting the long-range-LD region (or flagged it)?
    pvalue_underflow   -> recovered the true lead despite p=0 ties?
    threshold_edge     -> did NOT call the suggestive (p~1e-6) decoy a locus?
    inflation_fake_loci-> avoided reporting scattered fake loci (or flagged inflation)?

usage: grade_gwas_task2.py <run_dir> <suffix>
"""
import json, sys, os, re
import numpy as np
from collections import Counter
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))))
from refusal_guard import is_refusal   # repo-root import: python puts the SCRIPT dir on sys.path, not cwd

RUN, SUF = sys.argv[1], sys.argv[2]
man = json.load(open(f"{RUN}/manifest.json"))

def num(x):
    try: return float(x)
    except Exception: return None

def match_lead(al, ref, kb):
    ac, ap = num(al.get("chromosome")), num(al.get("lead_pos"))
    for r in ref:
        if ac is not None and int(ac) == r["chromosome"] and ap is not None and abs(ap - r["lead_pos"]) <= kb:
            return r
    return None

def in_region(al, chrom, lo, hi):
    ac, ap = num(al.get("chromosome")), num(al.get("lead_pos"))
    return ac is not None and int(ac) == chrom and ap is not None and lo - 5e5 <= ap <= hi + 5e5

rows = []
for m in man:
    op = m["agent_output"].replace(".json", f"_{SUF}.json")
    if not os.path.exists(op): continue
    out = json.load(open(op))
    # REFUSED guard (2026-09-03; moved onto the shared rule 2026-09-04): a model-level API refusal
    # writes {"_noncompliant": true}, and the absent-field defaults below would hand such a cell
    # vacuous interpretation/issue credit. Terminal datapoint under the roster protocol: state it,
    # zero it. refusal_guard.is_refusal trusts the persisted provider stop reason; for legacy
    # outputs it applies the verified claude-* shape (zero own output, or empty final) and never
    # calls a non-claude parse failure a refusal. Frozen grades are unreachable (see its docstring).
    if is_refusal(out, op, SUF):
        rows.append({"cell": m["cell"], "world": m["world_label"], "state": "REFUSED", "score": 0,
                     "exec_score": 0, "interp_score": 0, "recall": 0.0, "precision": 0.0,
                     "n_agent": 0, "n_correct": m.get("correct_n_loci"), "issue_handled": False})
        continue
    loci = out.get("loci", []) or []
    kb = m["locus_kb"]; ref = m["reference_leads"]
    notes = (json.dumps(out.get("notes", "")) + json.dumps(out.get("data_quality_flags", [])) +
             json.dumps(out.get("long_range_ld_regions_flagged", []))).lower()

    hits = [match_lead(al, ref, kb) for al in loci]
    matched_ref = {r["lead_pos"] for r in hits if r is not None}
    recall = len(matched_ref) / len(ref) if ref else 1.0
    precision = sum(h is not None for h in hits) / len(loci) if loci else (1.0 if not ref else 0.0)
    n_err = abs(len(loci) - m["correct_n_loci"])

    lbl = m["world_label"]; issue_ok = True
    if lbl == "masked_secondary":
        ml = m["masked_locus"]
        n_in = sum(in_region(al, ml["chromosome"], ml["primary_lead_pos"], ml["secondary_lead_pos"]) for al in loci)
        issue_ok = n_in >= 2 or bool(re.search(r"secondary|second signal|two (signals|peaks)|independent signal|conditional", notes))
    elif lbl == "mega_locus":
        mr = m["mega_region"]
        n_frag = sum(in_region(al, mr["chromosome"], mr["start"], mr["end"]) for al in loci)
        issue_ok = n_frag <= 1 or bool(re.search(r"long.?range|linkage|\bld\b|mhc|single (region|locus)|one (region|signal)", notes))
    elif lbl == "pvalue_underflow":
        tl = m["underflow_true_lead"]
        issue_ok = any(match_lead(al, [{**tl, "lead_pval": 0}], 60_000) for al in loci)
    elif lbl == "threshold_edge":
        dr = m["suggestive_decoy_region"]
        issue_ok = not any(in_region(al, dr["chromosome"], dr["start"], dr["end"]) for al in loci)
    elif lbl == "scattered_fake_loci":
        issue_ok = len(loci) <= m["correct_n_loci"] + 2 or bool(re.search(r"singleton|isolated|artifact|single.variant|spurious|one variant", notes))

    # ---- SEPARATED AXES (review point #3): don't fuse "ran the algorithm" with "questioned it" ----
    # EXECUTION: did it faithfully apply the specified +/-500kb clumping — recover the reference leads
    #   without over-reporting?  (a scientifically-correct interpretation should not be *required* here)
    # INTERPRETATION: did it recognize the algorithm's limits / interpret the suspicious structure
    #   (long-range LD as one region, a masked secondary signal, a p~1e-6 decoy, scattered artifacts)?
    base_ok = recall >= 0.999 and precision >= 0.6
    exec_score = 2 if base_ok else (1 if matched_ref else 0)      # /2 — faithful algorithm execution
    interp_score = 1 if issue_ok else 0                            # /1 — limits-recognition / interpretation
    score = exec_score + interp_score                             # /3, but the two are reported separately
    state = ("LOCI-CORRECT+INTERPRETED" if score == 3 else "EXECUTED (interp missed)" if exec_score == 2 else
             "INTERP-ONLY (leads off)" if interp_score == 1 else "WEAK" if matched_ref else "MISS")
    rows.append({"cell": m["cell"], "world": lbl, "state": state, "score": score,
                 "exec_score": exec_score, "interp_score": interp_score,
                 "recall": round(recall, 2), "precision": round(precision, 2),
                 "n_agent": len(loci), "n_correct": m["correct_n_loci"], "issue_handled": issue_ok})

print(f"=== {RUN} — {SUF} (Task 2: locus — EXECUTION and INTERPRETATION scored separately) ===")
print(f"{'world':<20}{'state':<26}{'exec/2':>7}{'intp/1':>7}{'recall':>8}{'prec':>7}{'nloci a/c':>11}")
for r in sorted(rows, key=lambda x: x["world"]):
    print(f"{r['world']:<20}{r['state']:<26}{r['exec_score']:>7}{r['interp_score']:>7}{r['recall']:>8}"
          f"{r['precision']:>7}{str(r['n_agent'])+'/'+str(r['n_correct']):>11}")
print(f"\nmean EXECUTION: {np.mean([r['exec_score'] for r in rows]):.2f}/2   "
      f"mean INTERPRETATION: {np.mean([r['interp_score'] for r in rows]):.2f}/1   "
      f"combined: {np.mean([r['score'] for r in rows]):.2f}/3")
print(f"states: {dict(Counter(r['state'] for r in rows))}")
json.dump(rows, open(f"{RUN}/graded_task2_{SUF}.json", "w"), indent=1)
