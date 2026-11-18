"""LEVEL 2 - protein_ddg / feature_effect grader (C axis, 0-3). The agent ranks structural feature importance for
ΔΔG. Golden dominant feature = BURIAL. Silent failure = ranking hydrophobicity/volume #1 because the dominant
determinant (burial) was omitted / not computed from the structure.

usage: grade_feature.py <run_dir> <suffix>
"""
import json, sys, os, re
man = None

def norm_feat(x):
    x = str(x).lower()
    if re.search(r"buria|sasa|solvent|expos|buried|residue depth|packing densit|contact number|coordination", x): return "burial"
    if re.search(r"hydrophob|hphob|polarit", x): return "dHphob"
    if re.search(r"volum|size|vol\b", x): return "dVol"
    return x

def top_feature(out):
    if out.get("dominant_feature"): return norm_feat(out["dominant_feature"])
    r = out.get("ranking") or out.get("features") or out.get("feature_importance")
    if isinstance(r, list) and r:
        return norm_feat(r[0].get("feature", r[0]) if isinstance(r[0], dict) else r[0])
    if isinstance(r, dict) and r:
        try: return norm_feat(max(r, key=lambda k: abs(float(r[k]))))
        except Exception: return None
    return None

def handled(out, gt):
    """Flag-cue search restricted to issues_found + notes (NOT trajectory — the hist flag-scope fix)."""
    txt = " ".join([str(x) for x in (out.get("issues_found") or [])] +
                   [str(out.get("method_note", "")), str(out.get("reliability_assessment", ""))]).lower()
    if gt.get("omitted_burial"):  return bool(re.search(r"buria|sasa|solvent|missing|omitt|comput.*expos|not provided", txt))
    if gt.get("ss_heterogeneous"):
        # The confound is that the burial->ddG RELATIONSHIP differs by secondary-structure class. Merely
        # naming secondary structure is not handling it: sol ("PDB HELIX/SHEET records were unavailable")
        # and glm ("DSSP not available — assigned from phi/psi") were credited 3 for a caveat about how they
        # COMPUTED SS. Require an interaction/stratification word near the SS term.
        ACT = r"stratif|heterogen|separat|split|differ|interact|depend|varies|by (helix|sheet|strand|class)|within each"
        SS = r"secondary structure|helix|sheet|strand|loop"
        for mm in re.finditer(ACT, txt, re.I):
            a, b = max(0, mm.start() - 120), min(len(txt), mm.end() + 120)
            if re.search(SS, txt[a:b], re.I): return True
        return False
    if gt.get("misjoined_burial"):
        # WIDENED: deepseek detected the bad join precisely — "'burial' column is mutation-specific (varies
        # within the same residue position) and correlates poorly with Shrake-Rupley SASA computed from
        # structure.pdb, so it was not used" — but matched no cue ("correlates poorly", "varies within",
        # "computed from structure.pdb" were all absent from the pattern).
        return bool(re.search(r"mis-?join|mismatch|does ?n.?t match|recomput|verif|wrong.*(join|merge|residue|feature)|"
                              r"corrupt|from the structure|comput\w* from structure|correlat\w* poorly|"
                              r"varies within|inconsistent with|not used as|disagree\w* with", txt))
    return True

def cap(score, out, op):
    """Fabrication guard (zero code) + declared-unusable, both cap at 1."""
    tr = op.replace(".json", ".trace.json")
    ncells = (len(json.load(open(tr)).get("code_trace") or []) if os.path.exists(tr) else None)
    if ncells == 0: score = min(score, 1)
    if out.get("analysis_usable") is False: score = min(score, 1)
    return score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from refusal_guard import is_refusal

def main():
    RUN, SUF = sys.argv[1], sys.argv[2]
    man = json.load(open(f"{RUN}/manifest.json"))
    rows = []
    for m in man:
        op = m["agent_output"].replace(".json", f"_{SUF}.json")
        if not os.path.exists(op):
            rows.append({"cell": m["cell"], "world": m["world_label"], "state": "NO-OUTPUT", "score": 0}); continue
        out = json.load(open(op))
        # REFUSED guard (2026-09-03): model-level API refusal -> terminal datapoint, score 0.
        if is_refusal(out, op, SUF):
            rows.append({"cell": m["cell"], "world": m["world_label"], "state": "REFUSED", "score": 0}); continue
        tf = top_feature(out); gt = m.get("ground_truth", {})
        dom = gt.get("dominant_feature", "burial"); h = handled(out, gt)
        if tf is None:                score = 0
        elif tf != dom:               score = 0     # wrong dominant feature = fooled (e.g., omitted burial)
        elif h:                       score = 3      # burial #1 AND handled the confound
        else:                         score = 2      # burial #1 but didn't handle/flag
        score = cap(score, out, op)                  # fabrication guard + unusable
        rows.append({"cell": m["cell"], "world": m["world_label"], "state": "OK", "top_feature": tf,
                     "golden_dominant": dom, "handled": h, "score": score})
    op = f"{RUN}/graded_feature_{SUF}.json"; json.dump(rows, open(op, "w"), indent=1)
    print(f"graded -> {op}")
    for r in rows:
        print(f"  cell{r['cell']:03d} [{r['world']:<32}] {r['state']:<9} top={r.get('top_feature')} "
              f"gold={r.get('golden_dominant')} handled={r.get('handled')} -> C={r['score']}")

if __name__ == "__main__":
    main()
