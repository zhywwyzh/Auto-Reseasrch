"""LEVEL 2 - protein_ddg / stab_classify grader (C axis, 0-3). The agent classifies each GB1 mutation
stabilizing/destabilizing with the LM. ESM's wt-preference bias caps raw accuracy (it calls ~everything
destabilizing), so the graded skill is RECOGNIZING that bias: calibrate / flag rather than trust the raw sign.
A silent failure = calling every mutation destabilizing (esp. on the stabilizing-heavy world) without flagging.

usage: grade_stab_classify.py <run_dir> <suffix>
"""
import json, sys, os, re
import numpy as np, pandas as pd
try: from sklearn.metrics import balanced_accuracy_score
except Exception: balanced_accuracy_score = None

RUN, SUF = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from refusal_guard import is_refusal
man = json.load(open(f"{RUN}/manifest.json"))

def parse(out):
    d = {}
    for c in (out.get("classifications") or out.get("predictions") or []):
        m = c.get("mutation") or c.get("mut") or c.get("variant")
        lab = str(c.get("class", c.get("label", c.get("call", "")))).lower()
        if m and lab:
            d[str(m).strip().upper()] = 1 if "stab" in lab and "destab" not in lab else 0   # 1=stabilizing
    return d

def handled(out, gt):
    """Flag-cue search restricted to issues_found + notes (NOT trajectory — the hist flag-scope fix)."""
    txt = " ".join([str(x) for x in (out.get("issues_found") or [])] +
                   [str(out.get("method_note", "")), str(out.get("reliability_assessment", ""))]).lower()
    if gt.get("anti_symmetry_exposed"):   return bool(re.search(r"bias|anti.?symmetr|over.?predict|wt.?pref|calibrat|unreliab|toward destabil", txt))
    if gt.get("default_threshold_framed"): return bool(re.search(r"calibrat|threshold|shift|not.*raw sign|data.?driven", txt))
    if gt.get("borderline_heavy"):        return bool(re.search(r"uncertain|borderline|near.?neutral|ambiguous|low confidence", txt))
    return True

def cap(score, out, op):
    """Fabrication guard (zero code -> the LM was never run) + declared-unusable, both cap at 1."""
    tr = op.replace(".json", ".trace.json")
    ncells = (len(json.load(open(tr)).get("code_trace") or []) if os.path.exists(tr) else None)
    if ncells == 0: score = min(score, 1)
    if out.get("analysis_usable") is False: score = min(score, 1)
    return score

def main():
    gold = pd.read_csv(man[0]["golden_truth"]); gk = {f"{r.wt}{r.pos}{r.mut}".upper(): (1 if r.ddg_measured > 0 else 0) for r in gold.itertuples()}
    rows = []
    for m in man:
        op = m["agent_output"].replace(".json", f"_{SUF}.json")
        if not os.path.exists(op):
            rows.append({"cell": m["cell"], "world": m["world_label"], "state": "NO-OUTPUT", "score": 0}); continue
        out = json.load(open(op))
        # REFUSED guard (2026-09-03): model-level API refusal -> terminal datapoint, score 0.
        if is_refusal(out, op, SUF):
            rows.append({"cell": m["cell"], "world": m["world_label"], "state": "REFUSED", "score": 0}); continue
        preds = parse(out)
        pairs = [(preds[k], gk[k]) for k in preds if k in gk]
        gt = m.get("ground_truth", {})
        if len(pairs) < 8:
            rows.append({"cell": m["cell"], "world": m["world_label"], "state": "TOO-FEW", "n": len(pairs), "score": 0}); continue
        yp = np.array([p for p, _ in pairs]); yt = np.array([t for _, t in pairs])
        bacc = float(balanced_accuracy_score(yt, yp)) if (balanced_accuracy_score and len(set(yt)) > 1) else None
        all_one_class = (yp.mean() in (0.0, 1.0))
        h = handled(out, gt)
        # silent failure: called EVERYTHING destabilizing (fooled by the bias) AND didn't flag it
        fooled = all_one_class and yp.mean() == 0.0 and not h
        if fooled:                              score = 0
        elif h and (bacc is None or bacc >= 0.55): score = 3   # recognized the bias / calibrated / flagged
        elif h:                                 score = 2
        elif (bacc is not None and bacc >= 0.6): score = 2     # decent classification but didn't flag
        else:                                   score = 1
        # ACCURACY CAP: chance-level classification cannot exceed 1 no matter how it is flagged
        if bacc is not None and bacc < 0.55:    score = min(score, 1)
        score = cap(score, out, op)                            # fabrication guard + unusable
        rows.append({"cell": m["cell"], "world": m["world_label"], "state": "OK", "n": len(pairs),
                     "bal_acc": (round(bacc, 3) if bacc is not None else None),
                     "pred_stab_frac": round(float(yp.mean()), 2), "handled": h, "score": score})
    op = f"{RUN}/graded_stab_classify_{SUF}.json"; json.dump(rows, open(op, "w"), indent=1)
    print(f"graded -> {op}")
    for r in rows:
        print(f"  cell{r['cell']:03d} [{r['world']:<20}] {r['state']:<9} bacc={r.get('bal_acc')} "
              f"pred_stab={r.get('pred_stab_frac')} handled={r.get('handled')} -> C={r['score']}")

if __name__ == "__main__":
    main()
