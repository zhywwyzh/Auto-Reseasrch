#!/usr/bin/env python3
"""Map frozen scRNA-seq L2 grades to the shared equal-weight A/I/M/C rubric."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from l2_meta_common import avg, explicit_recognition, ladder_dimensions, run_track_mapping  # noqa: E402


FAMILIES = {
    "annotation": "scrna_l2_annotation_run",
    "marker_de": "scrna_l2_marker_de_run",
    "composition": "scrna_l2_composition_run",
}


def _reported_accuracy(note):
    ratios = [(int(a), int(b)) for a, b in re.findall(r"(\d+)/(\d+)", note) if int(b) > 0]
    if not ratios:
        return None
    # All recorded fractions are performance evidence; average them rather than selecting a favorable one.
    return avg(a / b for a, b in ratios)


def map_record(ctx):
    note = str(ctx.graded.get("note", ""))
    low = ctx.evidence_text
    a = _reported_accuracy(note)
    if a is None:
        a = 1.0 if ctx.legacy_final >= 3 else 0.67 if ctx.legacy_final >= 2 else 0.33 if ctx.legacy_final >= 1 else 0.0
    recognized = explicit_recognition(low)
    if ctx.clean:
        i = 1.0 if ctx.legacy_final >= 2 else 0.5 if ctx.legacy_final >= 1 else 0.0
    else:
        i = 1.0 if recognized is True else 0.0
    response_terms = r"excluded|pseudobulk|tuned|verified|preserved|confounded|unattributable|flagged"
    response_recorded = bool(re.search(response_terms, low)) and recognized is not False
    m = 1.0 if response_recorded and a >= 0.6 else 0.5 if response_recorded or a >= 0.6 else 0.0
    if ctx.clean:
        m = a
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
        "recorded_fraction_accuracy": a,
        "parsed_recognition": recognized,
        "parsed_method_response": response_recorded,
        "joint_evidence": False,
    }


if __name__ == "__main__":
    run_track_mapping(script_file=__file__, track="scrna", families=FAMILIES, mapper=map_record)
