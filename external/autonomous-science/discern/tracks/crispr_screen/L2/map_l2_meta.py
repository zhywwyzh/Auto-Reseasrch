#!/usr/bin/env python3
"""Map frozen CRISPR-screen L2 grades to the shared equal-weight A/I/M/C rubric."""

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
)


FAMILIES = {
    "scoring": "crispr_l2_scoring_run",
    "calling": "crispr_l2_calling_run",
    "context": "crispr_l2_context_run",
}


def map_record(ctx):
    detail = str(ctx.graded.get("detail", ""))
    flagged = token_bool(detail, "flagged")
    if ctx.adjudication:
        reviewed = explicit_recognition(str(ctx.adjudication.get("reason", "")))
        if reviewed is not None:
            flagged = reviewed
    if ctx.clean:
        recognized = True if ctx.legacy_final >= 2 else None
    else:
        recognized = flagged
    # Recover the already-recorded quantitative outcome rather than treating the old
    # joint 0--3 ladder as a new analytical subscore.
    if "no " in detail.lower() or ctx.graded.get("state") == "NO-OUTPUT":
        a = 0.0
    elif "auroc=" in detail.lower():
        auroc = first_number(detail, (r"auroc=([-+]?\d+(?:\.\d+)?)",))
        a = 1.0 if auroc is not None and auroc >= 0.90 else 2 / 3 if auroc is not None and auroc >= 0.80 else 1 / 3 if auroc is not None and auroc >= 0.65 else 0.0
    elif "recovered" in detail.lower() and "%" in detail:
        pct = first_number(detail, (r"recovered(?: only)?\s+(\d+(?:\.\d+)?)%",))
        a = clamp01((pct or 0.0) / 100.0)
    elif "negfp=" in detail.lower():
        recall = first_number(detail, (r"recall=([-+]?\d+(?:\.\d+)?)",))
        neg_fp = first_number(detail, (r"negfp=([-+]?\d+(?:\.\d+)?)",))
        a = avg((recall, None if neg_fp is None else 1.0 - neg_fp))
    elif "recall=" in detail.lower():
        recall = first_number(detail, (r"recall=([-+]?\d+(?:\.\d+)?)",))
        # threshold_sensitivity stores no FP component in the frozen record. Its old
        # both-required tier disambiguates whether the unrecorded FP check passed.
        if ctx.world == "threshold_sensitivity" and ctx.legacy_final == 1:
            a = 0.0 if flagged else 1.0
        else:
            a = clamp01(recall)
    elif "artifact-leak=" in detail.lower():
        leak = first_number(detail, (r"artifact-leak=([-+]?\d+(?:\.\d+)?)",))
        a = 0.0 if leak is None else clamp01(1.0 - leak)
    elif "overlap=" in detail.lower():
        overlap = first_number(detail, (r"overlap=([-+]?\d+(?:\.\d+)?)",))
        a = 0.0 if overlap is None else clamp01(overlap / 0.30)
    elif "preserved=" in detail.lower():
        a = clamp01(first_number(detail, (r"preserved=([-+]?\d+(?:\.\d+)?)",)))
    else:
        a = 1.0 if ctx.legacy_final >= 2 else 0.0

    # The frozen CRISPR record does not retain a distinct method field. A corrected
    # output is therefore joint outcome/method evidence; the explicit flag remains I.
    method = a
    dims = ladder_dimensions(
        ctx.legacy_final,
        clean=ctx.clean,
        recognized=recognized,
        analysis=a,
        method=method,
    )
    return dims, {
        "source_fields": ["score", "detail", "state", "issue_type", "verify.reason", "adjudication.reason"],
        "parsed_flagged": flagged,
        "quantitative_outcome": round(a, 6),
        "joint_evidence": True,
    }


if __name__ == "__main__":
    run_track_mapping(script_file=__file__, track="crispr_screen", families=FAMILIES, mapper=map_record)
