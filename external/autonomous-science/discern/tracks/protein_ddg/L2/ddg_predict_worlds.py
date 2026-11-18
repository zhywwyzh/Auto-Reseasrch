"""LEVEL 2 - protein_ddg sub-task ddg_predict: predict per-mutation ΔΔG (DIRECTION+RANK) for GB1 with a
sequence LM (ESM2). Golden = Tsuboyama GB1 measured ΔΔG (L2/golden/gb1_ddg_golden.csv; ddg>0 = MORE stable).
ESM zero-shot is strong on DIRECTION (AUROC 0.70, 96% sign on |ddg|>1) but weak on magnitude & config-insensitive
(rubric_reference.json) -> we grade direction/rank, and the worlds are INPUT-expressible confounds that make the
DEFAULT usage silently wrong.

Worlds (clean + 2) — each FIRE-CHECKED (solver-first): the trap must actually make the DEFAULT usage wrong.
  clean            : real GB1 domain seq + correct WT (1-based) + standard convention (ddg>0 = stabilizing)
  sign_convention  : task metadata states a FLIPPED convention (positive = destabilizing) -> naive follows the
                     label and inverts the ranking (fire-check: rho +0.32 -> -0.32, C 3->0); correct = verify vs a
                     known core mutation (buried Leu->Ala is destabilizing) and report consistent with the DATA
  calibration_scale: metadata asks for ΔΔG in kcal/mol -> naive reports raw LLR as if calibrated; correct =
                     recognize ESM LLR is a rank proxy (not kcal/mol) and say so / rank rather than fake units
  FIRE-CHECK FINDINGS (solver-first, per the hist-L2 lesson that designed traps often fail):
   - `sign_convention` FIRES (accuracy-breaking); `calibration_scale` discriminates on handling only.
   - DROPPED `sequence_context`: SAGG tag barely degrades ESM (0.275->0.244) + real failure = WT-mismatch = L1.
   - DROPPED `position_indexing`: it FIRES as a bug (off-by-one collapses rho 0.40->~0) but is a pure ESM tool
     bug (BOS offset) on IDENTICAL data to clean -> not a separable data-world; any data form is L1 numbering.
   ESM ① is thin (2 clean traps); the track's depth lives in ② (classification) + ③ (structural features).

usage: ddg_predict_worlds.py <out_dir> [n_mut]
"""
import sys, os, json, shutil, hashlib
import pandas as pd, numpy as np
from Bio.PDB import PDBParser, PPBuilder

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)
GOLD = f"{HERE}/golden/gb1_ddg_golden.csv"
STRUCT = f"{TRACK}/data/clean/gb1.pdb"                       # L1-clean GB1 2QMT (reused; L1 untouched)
ISSUES = ["clean", "sign_convention", "calibration_scale"]
ISSUE_TYPE = {'clean': 'none', 'sign_convention': 'data-confound', 'calibration_scale': 'tool-trap'}

def det_seed(*p): return int(hashlib.md5("|".join(map(str, p)).encode()).hexdigest()[:8], 16)

def gb1_seq():
    s = PDBParser(QUIET=True).get_structure("gb1", STRUCT)
    return "".join(str(pp.get_sequence()) for pp in PPBuilder().build_peptides(s[0]["A"]))

def pick_mutations(gold, n, seed):
    """Balanced direction: destabilizing (ddg<-0.5) + stabilizing (ddg>0.5) + near-neutral, spread over positions."""
    rng = np.random.default_rng(seed)
    d = gold[gold.ddg_measured < -0.5]; s = gold[gold.ddg_measured > 0.5]; nz = gold[gold.ddg_measured.abs() <= 0.5]
    take = lambda df, k: df.sample(min(k, len(df)), random_state=int(rng.integers(1e9)))
    sel = pd.concat([take(d, n // 2), take(s, max(1, n // 3)), take(nz, n // 6)]).drop_duplicates(["pos", "wt", "mut"])
    return sel.sort_values("pos").reset_index(drop=True)

def build(issue, seq, muts):
    """Return (sequence_given, meta, ground_truth) for the world. muts is the mutation list (pos/wt/mut)."""
    meta = {"protein": "GB1 (protein G B1 domain)", "structure": "structure.pdb",
            "ddg_convention": "positive = MORE stable (stabilizing); negative = destabilizing",
            "units": "arbitrary (report a stability score; direction & ranking are what matter)"}
    gt = {"convention_flipped": False, "asks_calibrated_units": False}
    given = seq
    if issue == "sign_convention":
        meta["ddg_convention"] = "positive = destabilizing; negative = MORE stable"   # FLIPPED vs Tsuboyama golden
        gt["convention_flipped"] = True; gt["correct_action"] = "verify the stated sign convention against a known core mutation (e.g. buried Leu->Ala is destabilizing) and report consistently with the DATA, not the flipped label"
    elif issue == "calibration_scale":
        meta["units"] = "kcal/mol (report calibrated ΔΔG in kcal/mol)"
        gt["asks_calibrated_units"] = True; gt["correct_action"] = "recognize a sequence-LM log-likelihood-ratio is an UNCALIBRATED rank proxy, not kcal/mol; report ranks/direction (or explicitly calibrate) rather than pass raw LLR off as kcal/mol"
    else:
        gt["correct_action"] = "score each mutation with the LM on the GB1 domain; report a stability score (direction & rank)"
    return given, meta, gt

def main():
    OUT = sys.argv[1] if len(sys.argv) > 1 else f"{HERE}/results/ddg_predict_run"
    NMUT = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    seq = gb1_seq(); gold = pd.read_csv(GOLD)
    os.makedirs(f"{OUT}/data", exist_ok=True)
    man, cell = [], 0
    for issue in ISSUES:
        muts = pick_mutations(gold, NMUT, det_seed("ddg_predict", issue))
        given, meta, gt = build(issue, seq, muts)
        cd = f"{OUT}/data/cell{cell:03d}"; os.makedirs(cd, exist_ok=True)
        shutil.copy(STRUCT, f"{cd}/structure.pdb")
        # mutations named in DOMAIN 1-based numbering (author 2QMT numbering == domain here)
        muts[["pos", "wt", "mut"]].assign(mutation=[f"{r.wt}{r.pos}{r.mut}" for r in muts.itertuples()])[["mutation"]].to_csv(f"{cd}/mutations.csv", index=False)
        meta["sequence"] = given
        json.dump(meta, open(f"{cd}/task_meta.json", "w"), indent=1)
        man.append({"cell": cell, "task": "ddg_predict", "world_label": issue,
                    "issue_type": ISSUE_TYPE[issue], "issue_present": issue != "clean",
                    "agent_input": cd, "agent_output": f"{OUT}/out_cell{cell:03d}.json",
                    "golden_truth": GOLD, "n_mut": len(muts),
                    "mutations": [f"{r.wt}{r.pos}{r.mut}" for r in muts.itertuples()],
                    "ground_truth": gt, "correct_action": gt.get("correct_action", "")})
        cell += 1
    json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)

    # STAMP (audit fix): re-applying a builder must never drop expected_method/verify_rubric —
    # emit them here from the spec instead of relying on a separate stamp_methods pass.
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", "..")))
    import task_spec as _T
    _sub = _T.load("protein_ddg")["L2"]["ddg_predict"]
    for _m in man:
        _m["expected_method"] = _sub["expected_method"]
        _m["verify_rubric"] = _sub["info"]["rubric"]
    json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)
    assert sum(m["issue_type"] == "tool-trap" for m in man) >= 1, "L2 sub-task must contain >=1 tool-trap (ADD_A_TRACK)."
    print(f"wrote {cell} worlds -> {OUT}")
    for m in man:
        print(f"  cell{m['cell']:03d} [{m['world_label']:<17}] n_mut={m['n_mut']:<3} "
              f"sign_flip={m['ground_truth']['convention_flipped']} kcal={m['ground_truth']['asks_calibrated_units']}")

if __name__ == "__main__":
    main()
