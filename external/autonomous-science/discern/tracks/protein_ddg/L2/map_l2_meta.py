#!/usr/bin/env python3
"""Map frozen protein-ddG L2 grades to the shared equal-weight A/I/M/C rubric."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from l2_meta_common import avg, explicit_recognition, ladder_dimensions, run_track_mapping  # noqa: E402


FAMILIES = {
    "ddg_predict": "ddg_predict_run",
    "stability_classification": "stab_classify_run",
    "feature_effect": "feature_effect_run",
}


def map_record(ctx):
    row = ctx.graded
    handled = bool(row.get("handled"))
    if ctx.adjudication:
        reviewed = explicit_recognition(str(ctx.adjudication.get("reason", "")))
        if reviewed is not None:
            handled = reviewed
    if ctx.family == "ddg_predict":
        rho = row.get("spearman")
        bar = row.get("bar")
        auroc = row.get("auroc")
        rq = 0.0 if rho is None or bar is None else 1.0 if float(rho) >= float(bar) else 0.5 if float(rho) > 0 else 0.0
        aq = 0.0 if auroc is None else 1.0 if float(auroc) >= 0.65 else 0.5 if float(auroc) >= 0.55 else 0.0
        a = avg((rq, aq))
    elif ctx.family == "stability_classification":
        bacc = row.get("bal_acc")
        bacc_quality = 0.0 if bacc is None else 1.0 if float(bacc) >= 0.60 else 0.5 if float(bacc) >= 0.55 else 0.0
        pred_frac = row.get("pred_stab_frac")
        nondegenerate = None if pred_frac is None else float(float(pred_frac) not in (0.0, 1.0))
        a = avg((bacc_quality, nondegenerate))
    else:
        a = float(row.get("top_feature") == row.get("golden_dominant"))

    i = 1.0 if handled else (1.0 if ctx.clean and ctx.legacy_final >= 2 else 0.0)
    m = a if ctx.clean else 1.0 if handled and a >= 0.75 else 0.5 if handled or a > 0 else 0.0
    dims = ladder_dimensions(
        ctx.legacy_final,
        clean=ctx.clean,
        recognized=bool(i),
        analysis=a,
        method=m,
    )
    dims["issue_recognition"] = i
    return dims, {
        "source_fields": [
            "score", "spearman", "auroc", "bal_acc", "top_feature",
            "pred_stab_frac", "golden_dominant", "handled", "verify.reason", "adjudication.reason",
        ],
        "joint_evidence": False,
    }


if __name__ == "__main__":
    run_track_mapping(script_file=__file__, track="protein_ddg", families=FAMILIES, mapper=map_record)
