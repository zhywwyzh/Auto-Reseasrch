#!/usr/bin/env python3
"""Map frozen histone/gene-expression L2 grades to shared A/I/M/C dimensions."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from l2_meta_common import (  # noqa: E402
    avg,
    clamp01,
    explicit_recognition,
    first_number,
    ladder_dimensions,
    run_track_mapping,
    token_bool,
    token_number,
)


FAMILIES = {
    "quantify": "hist_l2_quantify_run",
    "ranking": "hist_l2_ranking_run",
    "regression": "hist_l2_regression_run",
}


def map_record(ctx):
    note = str(ctx.graded.get("note", ""))
    low = note.lower()
    recognized = None
    for key in ("flagged", "named", "justified", "covar/col"):
        value = token_bool(note, key)
        if value is not None:
            recognized = value if recognized is None else recognized or value
    if recognized is None:
        recognized = explicit_recognition(ctx.evidence_text)
    if ctx.adjudication:
        reviewed = explicit_recognition(str(ctx.adjudication.get("reason", "")))
        if reviewed is not None:
            recognized = reviewed

    if ctx.family == "quantify":
        corr = token_number(note, "corr")
        if ctx.world == "broad_mark_narrow_default":
            observed = token_number(note, "domains_mb")
            gold = first_number(note, (r"gold broad\s+([-+]?\d+(?:\.\d+)?)",))
            a = 0.0 if observed is None or gold in (None, 0) else clamp01(1.0 - abs(observed - gold) / (0.35 * gold))
            method_values = [token_bool(note, "broad_mode")]
        else:
            accuracy_terms = [None if corr is None else abs(corr)]
            rho = token_number(note, "rho")
            gold_rho = first_number(note, (r"\(gold\s+([-+]?\d+(?:\.\d+)?)\)",))
            if rho is not None and gold_rho not in (None, 0):
                accuracy_terms.append(clamp01(1.0 - abs(rho - gold_rho) / abs(gold_rho)))
            a = avg(accuracy_terms)
            if ctx.world == "wrong_promoter_window":
                window = token_number(note, "window")
                method_values = [None if window is None else window >= 5000, token_bool(note, "justified")]
            else:
                method_values = [token_bool(note, "input")]
    elif ctx.family == "ranking":
        if ctx.world == "clean":
            a = float(bool(token_bool(note, "joint_ok")))
            method_values = [token_bool(note, "covar/col")]
        elif ctx.world == "multicollinearity":
            a = float(bool(token_bool(note, "sign_consistent")))
            method_values = [token_bool(note, "flagged")]
        elif ctx.world == "omitted_confounder":
            reincluded = token_bool(note, "reincluded")
            observed = token_number(note, "k4me3")
            gold = first_number(note, (r"\(gold\s+([-+]?\d+(?:\.\d+)?)\)",))
            closeness = None if observed is None or gold in (None, 0) else clamp01(1.0 - abs(observed - gold) / abs(gold))
            a = avg((reincluded, closeness))
            method_values = [reincluded]
        else:
            n_strata = token_number(note, "n_strata")
            num_ok = token_bool(note, "num_ok")
            a = avg((None if n_strata is None else n_strata >= 2, num_ok))
            method_values = [None if n_strata is None else n_strata >= 2]
    else:
        if ctx.world == "clean":
            observed = token_number(note, "r")
            gold = first_number(note, (r"gold r=([-+]?\d+(?:\.\d+)?)",))
        elif ctx.world == "gc_cpg_confound":
            observed = token_number(note, "beta_adj")
            gold = first_number(note, (r"gold\s+([-+]?\d+(?:\.\d+)?)",))
        else:
            observed = token_number(note, "rho")
            gold = first_number(note, (r"gold\s+([-+]?\d+(?:\.\d+)?)",))
        a = 0.0 if observed is None or gold is None else clamp01(1.0 - abs(observed - gold) / max(abs(gold), 0.05))
        # Robust/adjusted method details were not retained separately from the
        # resulting estimate; M therefore shares the quantitative record with A.
        method_values = [a]

    method_values = [v for v in method_values if v is not None]
    method = avg(float(v) for v in method_values) if method_values else None
    dims = ladder_dimensions(
        ctx.legacy_final,
        clean=ctx.clean,
        recognized=recognized,
        analysis=a,
        method=method,
    )
    return dims, {
        "source_fields": ["score", "note", "verify.reason", "adjudication.reason"],
        "parsed_recognition": recognized,
        "parsed_method_signals": method_values,
        "analytical_component": round(a, 6),
        "joint_evidence": ctx.family == "regression" or not method_values,
    }


if __name__ == "__main__":
    run_track_mapping(script_file=__file__, track="hist_gene_exp", families=FAMILIES, mapper=map_record)
