#!/usr/bin/env python3
"""Map frozen GWAS L2 grades to the shared equal-weight A/I/M/C rubric."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from l2_meta_common import avg, ladder_dimensions, run_track_mapping  # noqa: E402


FAMILIES = {
    "signal_eda": "gwas_signaleda_run",
    "locus": "gwas_task2_run",
    "twas": "gwas_twas_run",
}


def _twas_analysis(row):
    z = row.get("z_corr")
    snp = row.get("snp_frac")
    top = row.get("top_recall")
    sign = row.get("sign_ok")
    if z is not None and float(z) < 0 and sign is False:
        return 0.0
    zq = 1.0 if z is not None and float(z) >= 0.95 else 0.5 if z is not None and float(z) >= 0.7 else 0.0
    sq = 1.0 if snp is not None and float(snp) >= 0.5 else 0.5 if snp is not None and float(snp) >= 0.25 else 0.0
    tq = None if top is None else max(0.0, min(1.0, float(top)))
    dq = None if sign is None else float(bool(sign))
    return avg((zq, sq, tq, dq))


def map_record(ctx):
    row, world = ctx.graded, ctx.world
    evidence = {"source_fields": [], "joint_evidence": False}

    if ctx.family == "signal_eda":
        a = avg((float(bool(row.get("lambda_ok"))), float(bool(row.get("assess_ok")))))
        if row.get("category") == "suspicious":
            i = float(bool(row.get("flagged")))
            m = float(row.get("third_axis") or 0.0)  # recorded flag-and-qualify response
        elif row.get("category") == "clean":
            i = float(row.get("third_axis") or 0.0)  # no-overflag restraint
            m = a
        else:
            i = float(bool(row.get("assess_ok")))
            m = float(row.get("third_axis") or 0.0)  # objective usability response
        c = avg((float(bool(row.get("qualified"))), float(bool(row.get("named_unavailable")))))
        if ctx.adjudication and ctx.adjudication.get("resolution") == "manual-override":
            # The accepted verifier supplies only the corrected three-axis core,
            # not a post-adjudication decomposition. Preserve it as joint evidence
            # instead of inventing which original axis moved.
            a = i = m = float(ctx.legacy_final) / 3.0
            evidence["joint_evidence"] = True
        evidence["source_fields"] = [
            "lambda_ok", "assess_ok", "flagged", "plausibility_ok", "qualified", "third_axis"
        ]
        return {
            "analytical_correctness": a,
            "issue_recognition": i,
            "methodological_response": m,
            "result_calibration": c,
        }, evidence

    if ctx.family == "locus":
        recall = float(row.get("recall", 0.0))
        precision = float(row.get("precision", 0.0))
        n_agent = float(row.get("n_agent", 0.0))
        n_correct = float(row.get("n_correct", 0.0))
        count_accuracy = 1.0 - min(abs(n_agent - n_correct) / max(n_correct, 1.0), 1.0)
        a = avg((recall, precision, count_accuracy))
        i = float(row.get("interp_score", 0))
        handled = float(bool(row.get("issue_handled")))
        m = float(row.get("exec_score", 0)) / 2.0
        # The frozen locus record jointly stores interpretation and disposition.
        c = handled
        evidence.update(
            source_fields=["exec_score", "interp_score", "issue_handled", "recall", "precision", "n_agent", "n_correct"],
            joint_evidence=True,
        )
        return {
            "analytical_correctness": a,
            "issue_recognition": i,
            "methodological_response": m,
            "result_calibration": c,
        }, evidence

    # TWAS: all recorded quantitative checks enter A; verifier/adjudication reasons supply trap recognition.
    a = _twas_analysis(row)
    reason = ctx.evidence_text
    key = {
        "build_mismatch": r"build|coordinate|liftover|rsid.*varid|varid.*rsid",
        "allele_order_swap": r"allele|orientation|sign flip|sign inversion|swap",
        "id_only": r"rsid|varid|identifier|variant key|mapping",
        "clean": r"verified|non.?trivial|snp.*(?:use|match)|no silent|concord",
    }[world]
    i = 1.0 if re.search(key, reason, re.I) and ctx.verify.get("llm", ctx.legacy_final) >= 2 else 0.5 if re.search(key, reason, re.I) else 0.0
    state = str(row.get("state", ""))
    m = 1.0 if state == "TWAS-CORRECT" else 0.5 if state in {"TWAS-CORRECT-HANDROLLED", "TWAS-PARTIAL"} else 0.0
    c = ladder_dimensions(ctx.legacy_final, clean=ctx.clean, recognized=i >= 0.5, analysis=a, method=m)["result_calibration"]
    evidence["source_fields"] = ["z_corr", "snp_frac", "top_recall", "sign_ok", "state", "verify.reason"]
    return {
        "analytical_correctness": a,
        "issue_recognition": i,
        "methodological_response": m,
        "result_calibration": c,
    }, evidence


if __name__ == "__main__":
    run_track_mapping(script_file=__file__, track="cf_gwas", families=FAMILIES, mapper=map_record)
