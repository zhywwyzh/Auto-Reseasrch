"""LEVEL 2 - protein_ddg sub-task stab_classify: classify each GB1 mutation as stabilizing / destabilizing with a
sequence LM (ESM2). Golden = Tsuboyama sign (ddg>0 = stabilizing). This is ESM's STRONG benchmark axis because its
wt-preference bias creates traps that FIRE (fire-checked, solver-first):
  - ESM LLR is almost always < 0 (any change looks 'less likely') -> raw sign / zero-threshold calls EVERYTHING
    destabilizing: sign-acc on stabilizing = 0.00, on destabilizing = 1.00; default-threshold balanced-acc = 0.50.

Worlds (clean + 3):
  clean              : balanced set (destab + stab + neutral); classify each; standard framing
  reverse_mutation_set: stabilizing-HEAVY list -> the anti-symmetry bias is exposed (naive sign(LLR) misses all the
                       stabilizing ones); correct = recognize ESM over-predicts destabilizing, calibrate/flag,
                       don't trust the raw sign for stabilizing calls  [FIRES]
  threshold          : metadata frames "classify at the tool score's sign (>0 = stabilizing)" -> naive uses the
                       zero-threshold and over-calls destabilizing; correct = calibrate a data-driven threshold  [FIRES]
  borderline         : near-neutral list (|ddg| small) -> genuinely hard; correct = flag uncertainty, don't force

usage: stab_classify_worlds.py <out_dir> [n_mut]
"""
import sys, os, json, shutil, hashlib
import pandas as pd, numpy as np
from Bio.PDB import PDBParser, PPBuilder

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)
GOLD = f"{HERE}/golden/gb1_ddg_golden.csv"
STRUCT = f"{TRACK}/data/clean/gb1.pdb"
ISSUES = ["clean", "reverse_mutation_set", "threshold", "borderline"]
ISSUE_TYPE = {'clean': 'none', 'reverse_mutation_set': 'tool-trap', 'threshold': 'tool-trap', 'borderline': 'statistical'}

def det_seed(*p): return int(hashlib.md5("|".join(map(str, p)).encode()).hexdigest()[:8], 16)

def gb1_seq():
    s = PDBParser(QUIET=True).get_structure("gb1", STRUCT)
    return "".join(str(pp.get_sequence()) for pp in PPBuilder().build_peptides(s[0]["A"]))

def pick(gold, issue, n, seed):
    rng = np.random.default_rng(seed)
    d = gold[gold.ddg_measured < -0.5]; s = gold[gold.ddg_measured > 0.5]; nz = gold[gold.ddg_measured.abs() <= 0.5]
    tk = lambda df, k: df.sample(min(k, len(df)), random_state=int(rng.integers(1e9)))
    if issue == "reverse_mutation_set":   sel = pd.concat([tk(s, n * 2 // 3), tk(d, n // 3)])      # stabilizing-heavy
    elif issue == "borderline":           sel = pd.concat([tk(gold[gold.ddg_measured.abs() < 0.7], n)])  # near-neutral
    else:                                 sel = pd.concat([tk(d, n // 2), tk(s, n // 3), tk(nz, n // 6)])  # balanced
    return sel.drop_duplicates(["pos", "wt", "mut"]).sort_values("pos").reset_index(drop=True)

def build(issue):
    meta = {"protein": "GB1 (protein G B1 domain)", "structure": "structure.pdb",
            "task": "classify each mutation as 'stabilizing' or 'destabilizing'",
            "convention": "stabilizing = raises folding stability (ΔΔG>0); destabilizing = lowers it"}
    gt = {"anti_symmetry_exposed": False, "default_threshold_framed": False, "borderline_heavy": False}
    if issue == "reverse_mutation_set":
        gt["anti_symmetry_exposed"] = True
        gt["correct_action"] = "the LM's wt-preference bias predicts nearly everything destabilizing; recognize it, calibrate/flag, do NOT trust raw sign for stabilizing calls"
    elif issue == "threshold":
        meta["scoring_hint"] = "classify by the sign of the tool's score (score>0 = stabilizing)"   # the trap framing
        gt["default_threshold_framed"] = True
        gt["correct_action"] = "the LM score is negatively shifted; the zero-threshold over-calls destabilizing -> calibrate a data-driven threshold, don't use raw sign"
    elif issue == "borderline":
        gt["borderline_heavy"] = True
        gt["correct_action"] = "most mutations are near-neutral (|ΔΔG| small) -> flag uncertainty, don't force confident calls"
    else:
        gt["correct_action"] = "classify each mutation stabilizing/destabilizing from the LM score, calibrated"
    return meta, gt

def main():
    OUT = sys.argv[1] if len(sys.argv) > 1 else f"{HERE}/results/stab_classify_run"
    NMUT = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    seq = gb1_seq(); gold = pd.read_csv(GOLD)
    os.makedirs(f"{OUT}/data", exist_ok=True)
    man, cell = [], 0
    for issue in ISSUES:
        muts = pick(gold, issue, NMUT, det_seed("stab_classify", issue))
        meta, gt = build(issue)
        cd = f"{OUT}/data/cell{cell:03d}"; os.makedirs(cd, exist_ok=True)
        shutil.copy(STRUCT, f"{cd}/structure.pdb")
        pd.DataFrame({"mutation": [f"{r.wt}{r.pos}{r.mut}" for r in muts.itertuples()]}).to_csv(f"{cd}/mutations.csv", index=False)
        meta["sequence"] = seq
        json.dump(meta, open(f"{cd}/task_meta.json", "w"), indent=1)
        man.append({"cell": cell, "task": "stab_classify", "world_label": issue,
                    "issue_type": ISSUE_TYPE[issue], "issue_present": issue != "clean",
                    "agent_input": cd, "agent_output": f"{OUT}/out_cell{cell:03d}.json",
                    "golden_truth": GOLD, "n_mut": len(muts),
                    "mutations": [f"{r.wt}{r.pos}{r.mut}" for r in muts.itertuples()],
                    "frac_stabilizing": round(float((muts.ddg_measured > 0).mean()), 2),
                    "ground_truth": gt, "correct_action": gt.get("correct_action", "")})
        cell += 1
    json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)

    # STAMP (audit fix): re-applying a builder must never drop expected_method/verify_rubric —
    # emit them here from the spec instead of relying on a separate stamp_methods pass.
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", "..")))
    import task_spec as _T
    _sub = _T.load("protein_ddg")["L2"]["stab_classify"]
    for _m in man:
        _m["expected_method"] = _sub["expected_method"]
        _m["verify_rubric"] = _sub["info"]["rubric"]
    json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)
    assert sum(m["issue_type"] == "tool-trap" for m in man) >= 1, "L2 sub-task must contain >=1 tool-trap (ADD_A_TRACK)."
    print(f"wrote {cell} worlds -> {OUT}")
    for m in man:
        print(f"  cell{m['cell']:03d} [{m['world_label']:<20}] n={m['n_mut']:<3} frac_stab={m['frac_stabilizing']}")

if __name__ == "__main__":
    main()
