#!/usr/bin/env python3
"""Map frozen enhancer-activity L2 grades to the shared equal-weight A/I/M/C rubric."""

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
    "divergence": "enhancer_l2_divergence_run",
    "conservation": "enhancer_l2_conservation_run",
    "ranking": "enhancer_l2_ranking_run",
}
FLAG_GATED = {"gc_conservation_bias", "conservation_as_proxy"}


def map_record(ctx):
    detail = str(ctx.graded.get("detail", ""))
    flagged = token_bool(detail, "flagged")
    if ctx.adjudication:
        reviewed = explicit_recognition(str(ctx.adjudication.get("reason", "")))
        if reviewed is not None:
            flagged = reviewed
    recognized = (True if ctx.clean and ctx.legacy_final >= 2 else flagged)
    f1 = first_number(detail, (r"f1=([-+]?\d+(?:\.\d+)?)",))
    precision = first_number(detail, (r"(?:^|\s)p=([-+]?\d+(?:\.\d+)?)",))
    recall = first_number(detail, (r"(?:^|\s)r=([-+]?\d+(?:\.\d+)?)",))
    leaked = first_number(detail, (r"leaked=([-+]?\d+(?:\.\d+)?)",))
    recovered = first_number(detail, (r"recovered=([-+]?\d+(?:\.\d+)?)",))

    # F1 is the nonredundant accuracy summary. Injected-family recovery/leakage is
    # an additional, independent condition in the original grader and is averaged
    # when present; P/R remain audit fields because F1 already contains them.
    accuracy_terms = [f1]
    if leaked is not None:
        accuracy_terms.append(1.0 - leaked)
    if recovered is not None:
        accuracy_terms.append(recovered)
    a = avg(accuracy_terms) if any(v is not None for v in accuracy_terms) else 0.0
    if ctx.world in FLAG_GATED and ctx.legacy_final == 1 and f1 is None:
        a = 0.0 if flagged else 1.0
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
        "recorded_metrics": {
            "f1": f1,
            "precision_audit_only": precision,
            "recall_audit_only": recall,
            "leak_avoidance": None if leaked is None else clamp01(1.0 - leaked),
            "affected_recovery": recovered,
        },
        "joint_evidence": True,
    }


if __name__ == "__main__":
    run_track_mapping(script_file=__file__, track="enhancer_activity", families=FAMILIES, mapper=map_record)
