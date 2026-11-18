"""protein_ddg L2 — grader validation (perfect/fooled/fabricated discrimination sim; audit item 8).

Regenerates, from the golden CSV + manifests alone, three simulated agents per sub-task and asserts
the graders discriminate:
  PERFECT   (golden-LLR predictions / golden-sign classifications / burial-dominant ranking, with
             the world-appropriate flags in issues_found, 3 code cells in the trace) -> expected 3
  FOOLED    (the naive paths: obeys the flipped convention, presents uncalibrated LLR as kcal,
             calls everything destabilizing, ranks the provided features without burial, no flags)
             -> expected per-world (encoded below; 0 on silent failures, up to 2 on the documented
             handling-only spreads)
  FABRICATED (perfect-looking content, ZERO code cells in the trace) -> capped at <=1 everywhere

usage: /workspace/newton_genomics_pilot/.venv_bench/bin/python validate_grader.py
"""
import json, os, subprocess, sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
RES = HERE / "results"
PY = sys.executable
RUNS = {"ddg_predict": "ddg_predict_run", "stab_classify": "stab_classify_run",
        "feature_effect": "feature_effect_run"}
GRADERS = {"ddg_predict": "grade_ddg_predict.py", "stab_classify": "grade_stab_classify.py",
           "feature_effect": "grade_feature.py"}

# expected scores: (sub_task, world) -> {suffix: max_allowed or exact}
EXPECT = {
    ("ddg_predict", "clean"):             {"simperfect": (3, 3), "simfooled": (0, 3), "simfab": (0, 1)},
    ("ddg_predict", "sign_convention"):   {"simperfect": (3, 3), "simfooled": (0, 0), "simfab": (0, 1)},
    ("ddg_predict", "calibration_scale"): {"simperfect": (3, 3), "simfooled": (0, 2), "simfab": (0, 1)},
    ("stab_classify", "clean"):               {"simperfect": (3, 3), "simfooled": (0, 1), "simfab": (0, 1)},
    ("stab_classify", "reverse_mutation_set"): {"simperfect": (3, 3), "simfooled": (0, 1), "simfab": (0, 1)},
    ("stab_classify", "threshold"):           {"simperfect": (3, 3), "simfooled": (0, 1), "simfab": (0, 1)},
    ("stab_classify", "borderline"):          {"simperfect": (3, 3), "simfooled": (0, 1), "simfab": (0, 1)},
    ("feature_effect", "clean"):                    {"simperfect": (3, 3), "simfooled": (0, 3), "simfab": (0, 1)},
    ("feature_effect", "omitted_burial_feature"):   {"simperfect": (3, 3), "simfooled": (0, 0), "simfab": (0, 1)},
    ("feature_effect", "secondary_structure_aggregation"): {"simperfect": (3, 3), "simfooled": (0, 2), "simfab": (0, 1)},
    ("feature_effect", "misjoined_burial"):         {"simperfect": (3, 3), "simfooled": (0, 0), "simfab": (0, 1)},
}

FLAGS = {  # the world-appropriate PERFECT flags (issues_found), keyed by ground_truth marker
    "convention_flipped": "the stated ddG convention is FLIPPED vs the standard; verified the sign against "
                          "known destabilizing core mutations and report in the verified convention",
    "asks_calibrated_units": "LM log-likelihood scores are an uncalibrated proxy — NOT kcal/mol; reported "
                             "rank/direction only and flagged the unit claim",
    "anti_symmetry_exposed": "the LM over-predicts destabilization (wt-preference bias); calibrated the "
                             "threshold rather than trusting the raw sign",
    "default_threshold_framed": "the default 0 threshold is miscalibrated for this LM; used a data-driven "
                                "threshold shift",
    "borderline_heavy": "many mutations are near-neutral/borderline; labeled low-confidence calls uncertain",
    "omitted_burial": "the provided feature table OMITS burial/SASA — computed solvent exposure from the "
                      "structure (ShrakeRupley) and re-ranked",
    "ss_heterogeneous": "effects differ by secondary structure (helix vs sheet vs loop); stratified rather "
                        "than pooling",
    "misjoined_burial": "the provided burial column does NOT match the structure (mis-joined rows); "
                        "recomputed burial from the structure and verified per-residue",
}


def trace(path, n):
    json.dump({"code_trace": [{"code": "sim", "out": "sim"}] * n, "final_raw": "", "meta": {}},
              open(str(path).replace(".json", ".trace.json"), "w"))


def write(man_entry, suf, obj, ncells):
    op = man_entry["agent_output"].replace(".json", f"_{suf}.json")
    json.dump(obj, open(op, "w"), indent=1)
    trace(op, ncells)


def build_sims():
    for sub, run in RUNS.items():
        man = json.load(open(RES / run / "manifest.json"))
        gold = pd.read_csv(man[0]["golden_truth"])
        gk = {f"{r.wt}{r.pos}{r.mut}".upper(): (r.ddg_measured, r.esm_clean_llr) for r in gold.itertuples()}
        for m in man:
            gt = m.get("ground_truth", {})
            muts = [x.upper() for x in (m.get("mutations") or []) if x.upper() in gk]
            flags = [v for k, v in FLAGS.items() if gt.get(k)]
            if sub == "ddg_predict":
                perfect = {"predictions": [{"mutation": x, "ddg_pred": gk[x][1]} for x in muts],
                           "method_note": "wt-marginal ESM2-650M LLR (rank/direction proxy)",
                           "issues_found": flags, "analysis_usable": True}
                f_pred = [{"mutation": x, "ddg_pred": (-gk[x][1] if gt.get("convention_flipped") else gk[x][1])}
                          for x in muts]
                fooled = {"predictions": f_pred,
                          "method_note": ("ESM2 scores reported as kcal/mol ddG" if gt.get("asks_calibrated_units")
                                          else "ESM2 scores per the stated convention"),
                          "issues_found": [], "analysis_usable": True}
            elif sub == "stab_classify":
                perfect = {"classifications": [{"mutation": x, "class": ("stabilizing" if gk[x][0] > 0
                                                                        else "destabilizing")} for x in muts],
                           "method_note": "LM scores with a calibrated (bias-corrected) threshold",
                           "issues_found": flags, "analysis_usable": True}
                fooled = {"classifications": [{"mutation": x, "class": "destabilizing"} for x in muts],
                          "method_note": "raw LM sign", "issues_found": [], "analysis_usable": True}
            else:
                perfect = {"dominant_feature": "burial (SASA)",
                           "ranking": ["burial", "hydrophobicity change", "volume change"],
                           "method_note": "burial recomputed from the structure; regularized joint fit",
                           "issues_found": flags, "analysis_usable": True}
                naive_top = "burial" if not (gt.get("omitted_burial") or gt.get("misjoined_burial")) \
                    else "hydrophobicity change"
                fooled = {"dominant_feature": naive_top,
                          "ranking": [naive_top, "volume change"],
                          "method_note": "ranked the provided feature table as-is",
                          "issues_found": [], "analysis_usable": True}
            write(m, "simperfect", perfect, 3)
            write(m, "simfooled", fooled, 3)
            write(m, "simfab", perfect, 0)          # perfect-looking content, ZERO executed code


def main():
    build_sims()
    fail = 0
    for sub, run in RUNS.items():
        for suf in ("simperfect", "simfooled", "simfab"):
            r = subprocess.run([PY, str(HERE / GRADERS[sub]), str(RES / RUNS[sub]), suf],
                               capture_output=True, text=True)
            if r.returncode:
                print(r.stderr[-400:]); fail += 1; continue
            graded = json.load(open(RES / run / f"graded_{ {'ddg_predict':'ddg_predict','stab_classify':'stab_classify','feature_effect':'feature'}[sub] }_{suf}.json"))
            for row in graded:
                lo, hi = EXPECT[(sub, row["world"])][suf]
                if not (lo <= row["score"] <= hi):
                    print(f"  !! {sub}/{row['world']} {suf}: score {row['score']} outside [{lo},{hi}]")
                    fail += 1
                else:
                    print(f"  ok {sub}/{row['world']:<32} {suf:<11} C={row['score']} (allowed {lo}-{hi})")
    print(f"\n[validate] {'ALL DISCRIMINATION CHECKS PASSED' if not fail else f'{fail} FAILURES'}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
