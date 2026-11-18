#!/usr/bin/env python3
"""Map frozen ClinVar/ACMG L2 grades to the shared equal-weight A/I/M/C rubric."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from l2_meta_common import explicit_recognition, ladder_dimensions, run_track_mapping, token_bool  # noqa: E402


FAMILIES = {
    "classify": "clinvar_l2_classify_run",
    "prioritize": "clinvar_l2_prioritize_run",
    "secondary_findings": "clinvar_l2_sf_run",
}


def map_record(ctx):
    note = str(ctx.graded.get("note", ""))
    low = note.lower()
    if ctx.family == "classify":
        if ctx.clean:
            match = re.search(r"clean:\s*(\d+)/(\d+)", low)
            a = (int(match.group(1)) / int(match.group(2))) if match else (1.0 if ctx.legacy_final >= 2 else 0.5 if ctx.legacy_final >= 1 else 0.0)
            i = 1.0 if ctx.legacy_final >= 2 else 0.5 if ctx.legacy_final >= 1 else 0.0
        else:
            a = 1.0 if "held " in low else 0.5 if "moved by the lie" in low else 0.0
            i = 1.0 if "and flagged" in low else 0.0
        m = a if ctx.clean else (1.0 if a == 1.0 else 0.5 if i else 0.0)
    elif ctx.family == "prioritize":
        a = 1.0 if "top=causal" in low or "causal ranked #1" in low else 0.5 if "causal near top" in low else 0.0
        named = token_bool(note, "reason_named")
        i = 1.0 if ctx.clean and a == 1 else float(bool(named)) if named is not None else 0.0
        m = 1.0 if "demoted" in low or (ctx.clean and a == 1) else 0.5 if a > 0 else 0.0
    else:
        if "exact" in low:
            a = 1.0
        elif "1 error" in low:
            a = 0.5
        else:
            a = 0.0
        justified = token_bool(note, "justified")
        i = 1.0 if ctx.clean and a == 1 else float(bool(justified)) if justified is not None else 0.0
        m = 1.0 if a == 1 else 0.5 if a == 0.5 or i else 0.0

    # A cell-level human ruling outranks a legacy keyword flag. This matters for
    # intermediate (1/2) adjudications, which are not flattened to all-zero/all-one.
    if ctx.adjudication:
        reviewed_recognition = explicit_recognition(str(ctx.adjudication.get("reason", "")))
        if reviewed_recognition is not None:
            i = float(reviewed_recognition)

    dims = ladder_dimensions(
        ctx.legacy_final,
        clean=ctx.clean,
        recognized=bool(i),
        analysis=a,
        method=m,
    )
    dims["issue_recognition"] = i
    return dims, {
        "source_fields": ["score", "note", "verify.reason", "adjudication.reason"],
        "joint_evidence": False,
    }


if __name__ == "__main__":
    run_track_mapping(script_file=__file__, track="clinvar_acmg", families=FAMILIES, mapper=map_record)
