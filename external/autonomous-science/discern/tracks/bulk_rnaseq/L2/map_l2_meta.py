#!/usr/bin/env python3
"""Map frozen bulk-RNA L2 grades to the shared equal-weight A/I/M/C rubric."""

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
    "de": "bulk_l2_de_run",
    "gsea": "bulk_l2_gsea_run",
    "structure": "bulk_l2_structure_run",
}


def map_record(ctx):
    note = str(ctx.graded.get("note", ""))
    low = note.lower()
    recognized = None
    joint_evidence = False
    for key in ("flagged", "hijack_flagged", "attributed", "evidence"):
        value = token_bool(note, key)
        if value is not None:
            recognized = value if recognized is None else recognized or value
    if recognized is None:
        recognized = explicit_recognition(ctx.evidence_text)
    if ctx.adjudication:
        reviewed = explicit_recognition(str(ctx.adjudication.get("reason", "")))
        if reviewed is not None:
            recognized = reviewed

    if ctx.family == "de":
        jac = token_number(note, "jac")
        corr = token_number(note, "corr")
        offset = token_number(note, "offset")
        if ctx.clean:
            a = avg((jac, None if corr is None else abs(corr)))
            method_signals = [token_bool(note, "sound_norm")]
        elif ctx.world == "normalization_default":
            # The frozen note stores both the top-set agreement and LFC offset;
            # 0.14 is the naive offset written in the same grade record.
            offset_quality = None if offset is None else 1.0 - min(abs(offset) / 0.14, 1.0)
            a = avg((jac, offset_quality))
            method_signals = [recognized]
            joint_evidence = True
        else:
            a = clamp01(jac)
            method_signals = [token_bool(note, "modeled")]
    elif ctx.family == "gsea":
        if ctx.clean:
            hits = first_number(note, (r"hits=(\d+(?:\.\d+)?)/10",))
            dir_ok = token_number(note, "dir_ok")
            hit_fraction = None if hits is None else hits / 10.0
            direction_fraction = None if hits in (None, 0) or dir_ok is None else dir_ok / hits
            a = avg((hit_fraction, direction_fraction))
            method_signals = [token_bool(note, "signed")]
        elif ctx.world == "ranking_metric_default":
            down_hits = first_number(note, (r"hits=(\d+(?:\.\d+)?)",))
            n_down = first_number(note, (r"of\s+(\d+(?:\.\d+)?)\s+down-labeled",))
            exact_recovery = None if down_hits is None else min(down_hits / 2.0, 1.0)
            substantive_down_result = None if n_down is None else float(n_down > 0)
            a = avg((exact_recovery, substantive_down_result))
            method_signals = [token_bool(note, "signed_rebuilt")]
        elif ctx.world == "wrong_background_universe":
            expressed = any(k in low for k in ("express", "tested", "de table", "ranked gene list", "de statistics"))
            genome = any(k in low for k in ("genome", "background_genes", "all annotated")) and not expressed
            spurious = token_number(note, "spurious_reported")
            a = 1.0 if expressed else 0.0 if genome else 0.5 if spurious == 0 else 0.0
            method_signals = [expressed]
            joint_evidence = True
        else:
            median_size = first_number(note, (r"top-\d+=([-+]?\d+(?:\.\d+)?)",))
            a = 0.0 if median_size is None else 1.0 if median_size <= 150 else 0.5 if median_size < 300 else 0.0
            method_signals = [None if median_size is None else median_size <= 150]
            joint_evidence = True
    else:
        assoc = token_number(note, "assoc")
        if assoc is not None and abs(assoc) > 1:
            assoc = None
        assoc_quality = None if assoc is None else clamp01(1.0 - abs(abs(assoc) - 0.90) / 0.90)
        if ctx.clean:
            cluster = token_bool(note, "cluster_supported")
            a = avg((assoc_quality, cluster))
            method_signals = [cluster]
            joint_evidence = True
        elif ctx.world == "pca_on_raw_counts":
            recomputed = token_bool(note, "recomputed")
            a = avg((assoc_quality, recomputed))
            method_signals = [recomputed]
            joint_evidence = True
        else:
            attributed = token_bool(note, "attributed")
            evidence = token_bool(note, "evidence")
            a = avg((attributed, evidence))
            method_signals = [attributed, evidence]
            joint_evidence = True

    method_signals = [x for x in method_signals if x is not None]
    method = avg(float(x) for x in method_signals) if method_signals else None
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
        "parsed_method_signals": method_signals,
        "analytical_component": round(a, 6),
        "joint_evidence": joint_evidence or not method_signals,
    }


if __name__ == "__main__":
    run_track_mapping(script_file=__file__, track="bulk_rnaseq", families=FAMILIES, mapper=map_record)
