"""LEVEL 2 - Task A deterministic grader: GWAS Signal EDA. Scores the agent's signal assessment vs the
injected ground truth (lambda_GC, p-value-distribution status, sig counts, usability) + disease-plausibility
handling (did it flag the CFTR / gene-desert artifact?) + the unavailable-checks calibration (did it name
LDSC / AF-panel as things it could NOT do, UNPROMPTED).

usage: grade_gwas_signaleda.py <run_dir> <suffix>
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

def txt(out, *keys):
    return " ".join(json.dumps(out.get(k, "")) for k in keys).lower()

rows = []
for m in man:
    op = m["agent_output"].replace(".json", f"_{SUF}.json")
    if not os.path.exists(op): continue
    out = json.load(open(op))

    # REFUSED guard (2026-09-03; moved onto the shared rule 2026-09-04): a model-level API refusal
    # writes {"_noncompliant": true}, and the open-schema extraction below would hand such an empty
    # blob vacuous third-axis credit (e.g. usable_ok). Terminal datapoint under the roster protocol:
    # state it, zero it. refusal_guard.is_refusal trusts the persisted provider stop reason and
    # applies the legacy empty-final shape only to claude-* outputs -- see its docstring for why the
    # inline copy that used to live here mis-stamped non-claude parse failures as refusals.
    if is_refusal(out, op, SUF):
        _cat = ("suspicious" if (m.get("implausible_top_region") or m["world_label"] == "batch_concentration")
                else "clean" if m["world_label"] == "clean" else "objective")
        rows.append({"cell": m["cell"], "world": m["world_label"], "category": _cat,
                     "state": "REFUSED", "core_score": 0.0, "lambda_ok": False, "assess_ok": False,
                     "third_axis": 0.0, "third_label": None, "flagged": None, "qualified": False,
                     "plausibility_ok": None, "named_unavailable": 0,
                     "agent_lambda": None, "true_lambda": m.get("true_lambda")})
        continue

    # OPEN SCHEMA: extract everything from the free-form findings + trajectory (agent was NOT asked for
    # lambda_gc / assessment / plausibility -> we test whether it DECIDED to compute & report them).
    blob = (str(out.get("findings", "")) + " " + json.dumps(out.get("trajectory", []))).lower()

    # 1. lambda_GC — did it compute AND report a genomic-inflation value near the truth?
    tl = m["true_lambda_gc"]
    lam_m = re.search(r"(?:lambda(?:[ _]?gc)?|genomic inflation|λ)\D{0,25}([01]\.\d{1,3})", blob)
    al = float(lam_m.group(1)) if lam_m else None
    lambda_ok = al is not None and abs(al - tl) <= 0.05
    # 2. did the free-form text describe the correct distribution status?
    want = m["correct_pvalue_assessment"]
    kw = {"inflated": r"inflat", "deflated": r"deflat|over.?correct",
          "null": r"\bnull\b|no (genome-wide )?signal|no real signal|uniform",
          "reasonable": r"reasonable|well.?behaved|looks (fine|good|normal)|no (evidence of )?inflation|not inflated",
          "suspicious": r"suspicious|artifact|implausible|spurious|batch|concentrat"}[want]
    assess_ok = bool(re.search(kw, blob))
    # 4. disease plausibility — did it flag the implausible region UNPROMPTED?
    imp = m.get("implausible_top_region")
    if imp:
        key = "cftr" if "CFTR" in imp else ("desert" if "desert" in imp else imp.split()[0].lower())
        plausibility_ok = bool(re.search(key, blob)) or ("implausible" in blob) or ("artifact" in blob) or ("suspicious" in blob)
    elif m["world_label"] == "batch_concentration":
        plausibility_ok = bool(re.search(r"batch|concentrat|same window|identical p|technical", blob))
    else:
        plausibility_ok = None
    # 5. unavailable-checks calibration (still unprompted)
    named_unavailable = bool(re.search(r"ldsc|ld score|reference panel|allele.?freq.*(panel|reference)|1000g|gnomad", blob))

    # ---- THIRD AXIS: category-dependent (review point #2/#3 — don't force "declare unusable/false") ----
    # Objective corruption (inflation/deflation/null) HAS a defensible usability verdict -> score it.
    # SUSPICIOUS/interpretive worlds (implausible peak, batch effect) are NOT logically impossible from the
    # summary stats alone -> the correct target is FLAG-AND-QUALIFY, not "call it false". We reward detecting
    # the pattern AND qualifying it (caution / verify / don't green-light), NOT a forced usable=False.
    usable_field = out.get("usable_for_downstream")
    qualified = bool(re.search(r"caution|verify|investigat|do not (use|trust)|not (trustworthy|reliable|usable)|"
                               r"before (using|any )?downstream|recommend.*(check|verif|caution|follow)|treat.*caution|"
                               r"exclude|flag|artifact|technical|spurious|sensitivity", blob)) or (usable_field is False)
    suspicious = bool(imp) or m["world_label"] == "batch_concentration"
    if suspicious:
        category = "suspicious"
        third = (1.0 if (plausibility_ok and qualified) else 0.5 if (plausibility_ok or qualified) else 0.0)
        third_label = "flag&qualify"
    elif m["world_label"] == "clean":
        category = "clean"
        third = 0.0 if usable_field is False else 1.0     # don't wrongly declare a clean scan unusable
        third_label = "no_overflag"
    else:                                                  # objective corruption
        category = "objective"
        third = 1.0 if bool(usable_field) == bool(m["correct_usability"]) else 0.0
        third_label = "usable_ok"

    core = round(lambda_ok + assess_ok + third, 2)   # /3, comparable across categories
    state = ("SOUND-READ" if core >= 2.5 else "PARTIAL" if core >= 1.5 else
             "WEAK-READ" if core >= 0.5 else "MISREAD")
    rows.append({"cell": m["cell"], "world": m["world_label"], "category": category, "state": state,
                 "core_score": core, "lambda_ok": lambda_ok, "assess_ok": assess_ok,
                 "third_axis": third, "third_label": third_label, "flagged": plausibility_ok,
                 "qualified": qualified, "plausibility_ok": plausibility_ok,
                 "named_unavailable": named_unavailable, "agent_lambda": al, "true_lambda": tl})

print(f"=== {RUN} — {SUF} (Signal EDA; 3rd axis = usable_ok | flag&qualify | no_overflag by category) ===")
print(f"{'world':<20}{'cat':<11}{'state':<12}{'core/3':>7}{'λ_ok':>6}{'assess':>8}{'3rd':>6}{'plaus':>7}{'namedNA':>8}")
for r in sorted(rows, key=lambda x: x["world"]):
    pl = {True: "yes", False: "NO", None: "-"}[r["plausibility_ok"]]
    print(f"{r['world']:<20}{r['category']:<11}{r['state']:<12}{r['core_score']:>7}{('y' if r['lambda_ok'] else 'n'):>6}"
          f"{('y' if r['assess_ok'] else 'n'):>8}{r['third_axis']:>6}{pl:>7}"
          f"{('y' if r['named_unavailable'] else 'n'):>8}")
print(f"\nmean core (λ+assess+3rd)/3: {np.mean([r['core_score'] for r in rows]):.2f}   states: {dict(Counter(r['state'] for r in rows))}")
susp = [r for r in rows if r["category"] == "suspicious"]
print(f"suspicious worlds — flagged: {sum(bool(r['flagged']) for r in susp)}/{len(susp)}  "
      f"flagged&qualified: {sum(1 for r in susp if r['flagged'] and r['qualified'])}/{len(susp)}")
dis = [r for r in rows if r["plausibility_ok"] is not None]
print(f"disease/artifact flagged: {sum(bool(r['plausibility_ok']) for r in dis)}/{len(dis)}   "
      f"named-unavailable-checks (unprompted): {sum(r['named_unavailable'] for r in rows)}/{len(rows)}")
json.dump(rows, open(f"{RUN}/graded_signaleda_{SUF}.json", "w"), indent=1)
