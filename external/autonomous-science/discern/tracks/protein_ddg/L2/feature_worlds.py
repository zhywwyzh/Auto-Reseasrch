"""LEVEL 2 - protein_ddg sub-task feature_effect (ESM-INDEPENDENT, Biopython): given GB1 mutations with MEASURED
ΔΔG + the structure, determine which STRUCTURAL feature most determines stability and rank feature importance.
Golden = the true ranking from the data: burial (|corr|=0.49) > hydrophobicity-change (0.31) > volume-change (0.12).
Fire-checked (solver-first): burial DOMINATES, so the firing trap is OMITTING it.

Worlds (clean + 3):
  clean                       : agent computes features from the structure; ranks burial #1  [golden]
  omitted_burial_feature      : provided_features.csv gives dHphob+dVol but NOT burial -> naive ranks hydrophobicity
                                #1 (wrong); correct = notice the dominant determinant is missing, compute burial (SASA)
                                from the structure -> burial #1  [FIRES: burial 0.49 >> hydrophobicity 0.31]
  secondary_structure_aggregation: the burial->ΔΔG slope is heterogeneous by SS (H -3.6, E -2.9, L -2.0); correct =
                                stratify / report the heterogeneity, don't quote one pooled slope  [moderate]
  misjoined_burial            : provided_features.csv HAS a burial column but it is MIS-JOINED (values shuffled to the
                                wrong residues — a wrong-merge-key bug) -> |corr| collapses 0.37->0.08, naive trusts it
                                and ranks hydrophobicity #1 (wrong); correct = VERIFY the provided feature by
                                recomputing rSASA from the structure -> true burial #1  [FIRES: perm 0.08 << dHphob 0.28,
                                8/8 seeds]. A verify-the-PROVIDED-feature tool-trap, distinct from omitted_burial
                                (absent) — the two are the sub-task's two tool-traps.
   (REBUILT from `collinearity`, which did NOT fire: burial<->dHphob r=0.33 (VIF~1.1) is not operationally collinear,
    and that world PROVIDED burial -> strictly easier than clean -> handling-only. reference_solver ④ locks the new one.)
  (dropped crystal_contact: GB1 2QMT is a single chain -> crystal contacts need symmetry mates -> not constructible.)

usage: feature_worlds.py <out_dir> [n_mut]
"""
import sys, os, json, shutil, hashlib
import pandas as pd, numpy as np
from Bio.PDB import PDBParser, Selection
from Bio.PDB.SASA import ShrakeRupley

HERE = os.path.dirname(os.path.abspath(__file__)); TRACK = os.path.dirname(HERE)
GOLD = f"{HERE}/golden/gb1_ddg_golden.csv"; STRUCT = f"{TRACK}/data/clean/gb1.pdb"
ISSUES = ["clean", "omitted_burial_feature", "secondary_structure_aggregation", "misjoined_burial"]
ISSUE_TYPE = {'clean': 'none', 'omitted_burial_feature': 'tool-trap', 'secondary_structure_aggregation': 'statistical', 'misjoined_burial': 'tool-trap'}
MAXASA = {'A':129,'R':274,'N':195,'D':193,'C':167,'E':223,'Q':225,'G':104,'H':224,'I':197,'L':201,'K':236,'M':224,'F':240,'P':159,'S':155,'T':172,'W':285,'Y':263,'V':174}
KD = {'A':1.8,'R':-4.5,'N':-3.5,'D':-3.5,'C':2.5,'E':-3.5,'Q':-3.5,'G':-0.4,'H':-3.2,'I':4.5,'L':3.8,'K':-3.9,'M':1.9,'F':2.8,'P':-1.6,'S':-0.8,'T':-0.7,'W':-0.9,'Y':-1.3,'V':4.2}
VOL = {'A':88.6,'R':173.4,'N':114.1,'D':111.1,'C':108.5,'E':138.4,'Q':143.8,'G':60.1,'H':153.2,'I':166.7,'L':166.7,'K':168.6,'M':162.9,'F':189.9,'P':112.7,'S':89.0,'T':116.1,'W':227.8,'Y':193.6,'V':140.0}
T21 = {'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLU':'E','GLN':'Q','GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F','PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V'}

def det_seed(*p): return int(hashlib.md5("|".join(map(str, p)).encode()).hexdigest()[:8], 16)

def burial_map():
    s = PDBParser(QUIET=True).get_structure("gb1", STRUCT); ShrakeRupley().compute(s, level="R")
    m = {}
    for r in Selection.unfold_entities(s[0]["A"], "R"):
        aa = T21.get(r.resname)
        if aa: m[r.id[1]] = round(1 - min(1.0, r.sasa / MAXASA[aa]), 3)   # 1=buried
    return m

def features(g, bmap):
    g = g.copy()
    g["burial"] = g.pos.map(lambda p: bmap.get(p, 0.5))
    g["dHphob"] = [KD[r.wt] - KD[r.mut] for r in g.itertuples()]
    g["dVol"] = [abs(VOL[r.wt] - VOL[r.mut]) for r in g.itertuples()]
    return g

def main():
    OUT = sys.argv[1] if len(sys.argv) > 1 else f"{HERE}/results/feature_effect_run"
    NMUT = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    gold = features(pd.read_csv(GOLD), burial_map())
    os.makedirs(f"{OUT}/data", exist_ok=True)
    man, cell = [], 0
    for issue in ISSUES:
        rng = np.random.default_rng(det_seed("feature", issue))
        muts = gold.sample(min(NMUT, len(gold)), random_state=int(rng.integers(1e9))).sort_values("pos").reset_index(drop=True)
        # golden feature ranking on THIS subset (abs corr with ddg)
        rank = sorted(["burial", "dHphob", "dVol"], key=lambda f: -abs(np.corrcoef(muts.ddg_measured, muts[f])[0, 1]))
        cd = f"{OUT}/data/cell{cell:03d}"; os.makedirs(cd, exist_ok=True); shutil.copy(STRUCT, f"{cd}/structure.pdb")
        muts[["wt", "pos", "mut", "ddg_measured"]].assign(mutation=[f"{r.wt}{r.pos}{r.mut}" for r in muts.itertuples()])[["mutation", "ddg_measured"]].to_csv(f"{cd}/mutations_ddg.csv", index=False)
        meta = {"protein": "GB1", "structure": "structure.pdb", "task": "identify which STRUCTURAL feature most determines ΔΔG; rank feature importance",
                "sequence": "".join(gold.drop_duplicates("pos").sort_values("pos").wt)}
        gt = {"dominant_feature": rank[0], "ranking": rank, "omitted_burial": False, "ss_heterogeneous": False, "misjoined_burial": False}
        if issue == "omitted_burial_feature":
            pf = muts.assign(mutation=[f"{r.wt}{r.pos}{r.mut}" for r in muts.itertuples()])[["mutation", "dHphob", "dVol"]]  # burial OMITTED
            pf.to_csv(f"{cd}/provided_features.csv", index=False)
            meta["provided_features"] = "provided_features.csv (hydrophobicity & volume change)"
            gt["omitted_burial"] = True; gt["correct_action"] = "the provided features omit BURIAL, the dominant determinant; compute relative SASA from the structure and include it -> burial ranks #1"
        elif issue == "secondary_structure_aggregation":
            gt["ss_heterogeneous"] = True; gt["correct_action"] = "the burial->ΔΔG slope differs by secondary structure (helix steeper than loop); stratify / report the heterogeneity, not one pooled slope"
        elif issue == "misjoined_burial":
            # burial column PRESENT but MIS-JOINED (values shuffled to the wrong residues — a wrong-merge-key bug):
            # |corr| collapses -> a naive agent trusts it and ranks hydrophobicity #1; correct = recompute rSASA.
            pr = np.random.default_rng(det_seed("feature", "misjoined_burial", "perm"))
            bad = muts.burial.values[pr.permutation(len(muts))]
            pf = muts.assign(mutation=[f"{r.wt}{r.pos}{r.mut}" for r in muts.itertuples()], burial=bad)[["mutation", "burial", "dHphob", "dVol"]]
            pf.to_csv(f"{cd}/provided_features.csv", index=False)
            meta["provided_features"] = "provided_features.csv (burial, hydrophobicity, volume)"
            gt["misjoined_burial"] = True; gt["correct_action"] = "the provided BURIAL column is mis-joined (values do not match the residues); do NOT trust it — recompute relative SASA from the structure to verify -> true burial ranks #1"
        else:
            gt["correct_action"] = "compute burial (SASA), hydrophobicity- and volume-change from the structure; rank by association with ΔΔG -> burial dominant"
        json.dump(meta, open(f"{cd}/task_meta.json", "w"), indent=1)
        man.append({"cell": cell, "task": "feature_effect", "world_label": issue, "issue_type": ISSUE_TYPE[issue],
                    "issue_present": issue != "clean", "agent_input": cd, "agent_output": f"{OUT}/out_cell{cell:03d}.json",
                    "golden_truth": GOLD, "n_mut": len(muts), "ground_truth": gt, "correct_action": gt.get("correct_action", "")})
        if issue == "secondary_structure_aggregation":
            man[-1]["note"] = ("task-framed world (hist aggregation_reversal precedent): data generated "
                               "identically to clean (only the sampling seed differs); the probed "
                               "deliverable — per-secondary-structure effect heterogeneity — is what makes "
                               "the pooled answer naive; graded on stratification/handling")
        cell += 1
    json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)

    # STAMP (audit fix): re-applying a builder must never drop expected_method/verify_rubric —
    # emit them here from the spec instead of relying on a separate stamp_methods pass.
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", "..")))
    import task_spec as _T
    _sub = _T.load("protein_ddg")["L2"]["feature_effect"]
    for _m in man:
        _m["expected_method"] = _sub["expected_method"]
        _m["verify_rubric"] = _sub["info"]["rubric"]
    json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)
    assert sum(m["issue_type"] == "tool-trap" for m in man) >= 1, "L2 sub-task must contain >=1 tool-trap (ADD_A_TRACK)."
    print(f"wrote {cell} worlds -> {OUT}")
    for m in man:
        print(f"  cell{m['cell']:03d} [{m['world_label']:<32}] n={m['n_mut']:<3} golden_dominant={m['ground_truth']['dominant_feature']}")

if __name__ == "__main__":
    main()
