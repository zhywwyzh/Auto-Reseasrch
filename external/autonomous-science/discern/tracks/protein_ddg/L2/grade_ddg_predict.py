"""LEVEL 2 - protein_ddg / ddg_predict grader. The agent predicts a per-mutation stability score with the LM;
we grade DIRECTION + RANK vs the Tsuboyama golden (magnitude is not ESM's strength -> not required), plus the
world's confound handling. Golden ddg>0 = MORE stable; the agent's score should, per the stated convention,
correlate POSITIVELY with the golden -> a NEGATIVE correlation means it followed a flipped label / inverted sign
(the silent failure).  This is the single 0-3 L2 correctness score. NOTE 2026-08-29: no benchmark output
computes or aggregates a shared C/M/K/I/T score vector -- verify_grades.py returns ONE verifier score, not
M/K/I axes; "C" is only this script's historic name for the score it emits.

usage: grade_ddg_predict.py <run_dir> <suffix>
"""
import json, sys, os, re
import numpy as np, pandas as pd
from scipy.stats import spearmanr
try: from sklearn.metrics import roc_auc_score
except Exception: roc_auc_score = None

RUN, SUF = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from refusal_guard import is_refusal
man = json.load(open(f"{RUN}/manifest.json"))
FRAC = 0.6             # require the agent to reach >=60% of the PER-WORLD correct-tool (golden ESM) rho (no hardcoded ceiling)

def parse_preds(out):
    """Return dict mutation->pred_score from the agent output (tolerant to a few field names)."""
    d = {}
    for p in (out.get("predictions") or out.get("ddg") or []):
        m = p.get("mutation") or p.get("mut") or p.get("variant")
        v = p.get("ddg_pred", p.get("score", p.get("ddg", p.get("stability"))))
        if m and v is not None:
            try: d[str(m).strip().upper()] = float(v)
            except Exception: pass
    return d

def handled(out, gt):
    """Did the agent address THIS world's confound? Cue search restricted to FLAG-BEARING fields
    (issues_found + free-text notes) — NOT trajectory (trajectory narration false-fires 'handled';
    the hist L2 flag-scope fix, L2_DESIGN.md flag-scope addendum)."""
    txt = " ".join([str(x) for x in (out.get("issues_found") or [])] +
                   [str(out.get("method_note", "")), str(out.get("reliability_assessment", ""))]).lower()
    # CUE TIGHTENED (verify 2026-08-16). The old pattern included bare `verif` and `destabiliz.*stabiliz`,
    # which matched a mere RESTATEMENT of the metadata convention and so awarded the inverted-but-flagged
    # tier (1) to models that simply FOLLOWED the flipped convention. Observed over-credits:
    #   sol      "defines positive scores as destabilizing and negative scores as stabilizing"  <- restatement
    #   kimi     "destabilizing / negative=more stable"                                          <- restatement
    #   deepseek matched bare "verif" in "could only be verified indirectly"                     <- not a flag
    # A genuine flag must assert the convention is WRONG/SUSPECT or that it was CORRECTED — not describe it.
    if gt.get("convention_flipped"):
        # PROXIMITY, not bare keywords. Bare terms fail in BOTH directions here:
        #   too loose -> `verif` / `destabiliz.*stabiliz` matched a mere RESTATEMENT of the convention
        #                (sol, kimi, deepseek were awarded the flagged tier for describing it);
        #   naively widened -> `disagree` matched glm's unrelated aside that "masked-marginal and
        #                WT-marginal approaches disagree on sign" for 3 near-neutral mutations.
        # A genuine flag must put a CHALLENGE word near a CONVENTION word (within ~120 chars).
        CHALLENGE = r"flip(ped|ping)?\b|invert|revers|opposite|contradict|inconsisten|mismatch|suspect|" \
                    r"backwards|wrong|does not match|disagree"
        # SUBJECT must be the DECLARED CONVENTION itself. Bare "sign"/"positive" is too generic: it
        # matched glm's "masked-marginal and WT-marginal approaches disagree on sign" — sign ambiguity
        # of 3 near-neutral mutations, not a challenge to the metadata convention.
        SUBJECT = r"convention|task_meta|metadata|stated (sign|label|direction)|declared|as (labell?ed|given)"
        for mm in re.finditer(CHALLENGE, txt, re.I):
            a, b = max(0, mm.start() - 120), min(len(txt), mm.end() + 120)
            if re.search(SUBJECT, txt[a:b], re.I):
                return True
        return False
    if gt.get("asks_calibrated_units"):
        return bool(re.search(r"proxy|uncalibrat|not calibrat|dimensionless|not kcal|arbitrary|"
                              r"relative (only|scale)|rank[- ]only|no absolute", txt))
    return True   # clean world: nothing to flag

def cap(score, out, op):
    """FABRICATION GUARD (sealed trace = ground truth): an agent that ran ZERO code cannot have run the
    LM -> numeric claims cap at 1. Declaring solvable data unusable also caps at 1."""
    tr = op.replace(".json", ".trace.json")
    ncells = (len(json.load(open(tr)).get("code_trace") or []) if os.path.exists(tr) else None)
    if ncells == 0: score = min(score, 1)
    if out.get("analysis_usable") is False: score = min(score, 1)
    return score

def main():
    gold = pd.read_csv(f"{man[0]['golden_truth']}" if os.path.isabs(man[0]['golden_truth']) else man[0]['golden_truth'])
    gkey = {f"{r.wt}{r.pos}{r.mut}".upper(): r.ddg_measured for r in gold.itertuples()}
    lkey = {f"{r.wt}{r.pos}{r.mut}".upper(): r.esm_clean_llr for r in gold.itertuples()}   # correct-tool LLR -> per-world gold rho
    rows = []
    for m in man:
        op = m["agent_output"].replace(".json", f"_{SUF}.json")
        if not os.path.exists(op):
            rows.append({"cell": m["cell"], "world": m["world_label"], "state": "NO-OUTPUT", "score": 0}); continue
        out = json.load(open(op))
        # REFUSED guard (2026-09-03): model-level API refusal -> terminal datapoint, score 0.
        if is_refusal(out, op, SUF):
            rows.append({"cell": m["cell"], "world": m["world_label"], "state": "REFUSED", "score": 0}); continue
        preds = parse_preds(out)
        pairs = [(preds[k], gkey[k]) for k in preds if k in gkey]
        gt = m.get("ground_truth", {})
        if len(pairs) < 8:
            rows.append({"cell": m["cell"], "world": m["world_label"], "state": "TOO-FEW-PREDS",
                         "n": len(pairs), "score": 0}); continue
        pv, gv = np.array([p for p, _ in pairs]), np.array([g for _, g in pairs])
        rho = float(spearmanr(pv, gv).correlation)
        # PER-WORLD correct-tool ceiling: gold rho = spearman(golden ESM LLR, measured) on THIS world's mutations
        wm = [x.upper() for x in (m.get("mutations") or [])]
        gr = [(lkey[x], gkey[x]) for x in wm if x in lkey and x in gkey]
        gold_rho = float(spearmanr([a for a, _ in gr], [b for _, b in gr]).correlation) if len(gr) > 8 else None
        bar = (FRAC * gold_rho) if (gold_rho and gold_rho > 0.10) else 0.12   # fraction of the achievable rho
        big = np.abs(gv) > 1.0
        auc = float(roc_auc_score((gv[big] > 0).astype(int), pv[big])) if (roc_auc_score and big.sum() > 4 and len(set((gv[big] > 0))) > 1) else None
        h = handled(out, gt)
        # direction correct = positive corr AND reaching a fraction of the per-world correct-tool rho
        dir_ok = rho > 0 and (rho >= bar or (auc is not None and auc >= 0.62))
        inverted = rho < -0.10                       # followed a flipped label / inverted sign -> silent failure
        if inverted:                       score = 1 if h else 0   # inverted-but-flagged (transparent) is fairer at 1
        elif not dir_ok:                   score = 1   # ran but weak/near-random direction
        elif dir_ok and h:                 score = 3
        else:                              score = 2   # right direction, didn't handle/flag the confound
        score = cap(score, out, op)                    # fabrication guard + unusable cap
        rows.append({"cell": m["cell"], "world": m["world_label"], "state": "OK", "n": len(pairs),
                     "spearman": round(rho, 3), "gold_rho": (round(gold_rho, 3) if gold_rho else None),
                     "bar": round(bar, 3), "auroc": (round(auc, 3) if auc is not None else None),
                     "handled": h, "score": score})
    out_path = f"{RUN}/graded_ddg_predict_{SUF}.json"
    json.dump(rows, open(out_path, "w"), indent=1)
    print(f"graded -> {out_path}")
    for r in rows:
        print(f"  cell{r['cell']:03d} [{r['world']:<17}] {r['state']:<12} "
              f"rho={r.get('spearman')} auroc={r.get('auroc')} handled={r.get('handled')} -> C={r['score']}")

if __name__ == "__main__":
    main()
