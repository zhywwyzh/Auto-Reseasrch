#!/usr/bin/env python3
"""Build a separate Fable 5 -> Opus 5 fallback-replay score artifact.

This script never edits ``results/final_scores.json`` or any run/grade artifact.  It
constructs a *system* result, not a Fable model result:

* keep the post-adjudication Fable score when Fable answered;
* use the canonical Claude Opus 5 score when Fable refused or the refusal-stop
  protocol prevented the task from being run;
* preserve canonical prior-gate omission when Opus itself has no eligible L3 score;
* aggregate with DISCERN's normal world -> family -> track -> stage/chain rules.

The three answered Enhancer L2 cells are meta-mapped in a temporary directory so
the shared A/I/M/C scale is used without modifying the run tree.  Mid-chain and
unrun L3 substitutions are explicitly a replay-from-task-start assumption; this
artifact is not an observed Anthropic product-surface fallback trajectory.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
NEW = RESULTS / "new_models"
FABLE = "claude-fable-5"
OPUS = "claude-opus-5"
TRACKS = (
    "bulk_rnaseq",
    "cf_gwas",
    "clinvar_acmg",
    "crispr_screen",
    "enhancer_activity",
    "hist_gene_exp",
    "protein_ddg",
    "scrna",
)
OUT = NEW / "FALLBACK_REPLAY_claude-fable-5_to_claude-opus-5.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def family_name(name: str | None) -> str | None:
    aliases = {
        "signaleda": "signal-eda",
        "signal_eda": "signal-eda",
        "secondary_findings": "sf",
        "effect_ranking": "ranking",
    }
    return aliases.get(name, name)


def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("mean of empty collection")
    return statistics.fmean(values)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def enhancer_meta_rows() -> list[dict[str, str]]:
    """Meta-map Fable Enhancer L2 in scratch space; never touch canonical outputs."""
    with tempfile.TemporaryDirectory(prefix="discern_fallback_replay_") as tmp:
        env = dict(os.environ)
        env["L2_META_MODELS"] = FABLE
        env["L2_META_OUT"] = tmp
        subprocess.run(
            [sys.executable, str(ROOT / "tracks/enhancer_activity/L2/map_l2_meta.py")],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        return read_csv(Path(tmp) / "l2_meta_scores.csv")


def main() -> None:
    difficulty_path = NEW / "refusal_difficulty_analysis.json"
    difficulty = json.loads(difficulty_path.read_text())
    refusal_rows = difficulty["rows"]

    refusal: dict[tuple[str, str, str | None, str], bool] = {}
    for row in refusal_rows:
        key = (
            row["level"],
            row["track"],
            family_name(row.get("family")),
            row["world"],
        )
        if key in refusal:
            raise RuntimeError(f"duplicate refusal key: {key}")
        refusal[key] = bool(row["refused"])

    # L1: Fable's post-adjudication cell score is already carried by the frozen-data
    # refusal registry.  Substitute Opus only for explicitly refused cells.
    opus_l1_rows = [
        row for row in read_csv(RESULTS / "fig_data_l1.csv") if row["model"] == OPUS
    ]
    opus_l1 = {(row["track"], row["world"]): float(row["score"]) for row in opus_l1_rows}
    l1_cells: list[dict[str, object]] = []
    for row in refusal_rows:
        if row["level"] != "L1":
            continue
        key = (row["track"], row["world"])
        is_refusal = bool(row["refused"])
        score = opus_l1[key] if is_refusal else float(row["fable"])
        l1_cells.append(
            {
                "track": row["track"],
                "world": row["world"],
                "source": "opus_fallback" if is_refusal else "fable_answer",
                "score": round(score, 6),
            }
        )
    if len(l1_cells) != 79:
        raise RuntimeError(f"expected 79 L1 cells, found {len(l1_cells)}")

    # L2: all selected values must be on the shared meta-rubric scale.
    fable_meta_rows: list[dict[str, str]] = []
    for path in sorted((NEW / "meta_claude-fable-5").glob("*/l2_meta_scores.csv")):
        fable_meta_rows.extend(read_csv(path))
    fable_meta_rows.extend(enhancer_meta_rows())
    fable_l2 = {
        (row["track"], family_name(row["family"]), row["world"]): float(row["meta_score"])
        for row in fable_meta_rows
    }
    opus_l2_rows = [
        row for row in read_csv(RESULTS / "fig_data_l2.csv") if row["model"] == OPUS
    ]
    opus_l2 = {
        (row["track"], row["family"], row["world"]): float(row["score"])
        for row in opus_l2_rows
    }
    l2_cells: list[dict[str, object]] = []
    for (track, family, world), opus_score in sorted(opus_l2.items()):
        ref_key = ("L2", track, family, world)
        if ref_key not in refusal:
            raise RuntimeError(f"missing refusal status for L2 key: {ref_key}")
        is_refusal = refusal[ref_key]
        if is_refusal:
            score = opus_score
            source = "opus_fallback"
        else:
            key = (track, family, world)
            if key not in fable_l2:
                raise RuntimeError(f"answered Fable L2 cell lacks meta score: {key}")
            score = fable_l2[key]
            source = "fable_answer"
        l2_cells.append(
            {
                "track": track,
                "family": family,
                "world": world,
                "source": source,
                "score": round(score, 6),
            }
        )
    if len(l2_cells) != 102:
        raise RuntimeError(f"expected 102 L2 cells, found {len(l2_cells)}")

    # L3: preserve Fable's two observed scRNA scores.  Replay Opus from task start
    # everywhere else.  The Opus-inadmissible Bulk cytokine world remains omitted.
    all_l3_rows = read_csv(RESULTS / "fig_data_l3.csv")
    universe = sorted({(row["track"], row["world"]) for row in all_l3_rows})
    opus_l3 = {
        (row["track"], row["world"]): float(row["composite"])
        for row in all_l3_rows
        if row["model"] == OPUS
    }
    fable_scrna = json.loads((NEW / "scrna_claude-fable-5.json").read_text())["L3"]
    fable_l3 = {
        ("scrna", "real"): float(fable_scrna["real"]["composite"]),
        ("scrna", "cf_cd16_mono"): float(fable_scrna["cf_cd16_mono"]["composite"]),
    }
    l3_cells: list[dict[str, object]] = []
    l3_omissions: list[dict[str, str]] = []
    for key in universe:
        track, world = key
        if key in fable_l3:
            l3_cells.append(
                {"track": track, "world": world, "source": "fable_answer", "score": fable_l3[key]}
            )
        elif key in opus_l3:
            l3_cells.append(
                {
                    "track": track,
                    "world": world,
                    "source": "opus_fallback_from_task_start",
                    "score": round(opus_l3[key], 6),
                }
            )
        else:
            l3_omissions.append(
                {
                    "track": track,
                    "world": world,
                    "reason": "no canonical Opus score (Opus prior-gate omission)",
                }
            )
    if len(universe) != 22 or len(l3_cells) != 21 or len(l3_omissions) != 1:
        raise RuntimeError(
            f"unexpected L3 coverage: universe={len(universe)}, cells={len(l3_cells)}, "
            f"omissions={len(l3_omissions)}"
        )

    by_l1: dict[str, list[float]] = defaultdict(list)
    for row in l1_cells:
        by_l1[str(row["track"])].append(float(row["score"]))
    l1_track = {track: mean(by_l1[track]) for track in TRACKS}

    by_family: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in l2_cells:
        by_family[(str(row["track"]), str(row["family"]))].append(float(row["score"]))
    family_scores = {key: mean(values) for key, values in by_family.items()}
    by_track_family: dict[str, list[float]] = defaultdict(list)
    for (track, _family), score in family_scores.items():
        by_track_family[track].append(score)
    l2_track = {track: mean(by_track_family[track]) for track in TRACKS}

    by_l3: dict[str, list[float]] = defaultdict(list)
    for row in l3_cells:
        by_l3[str(row["track"])].append(float(row["score"]))
    l3_track = {track: mean(by_l3[track]) for track in TRACKS}

    per_track: dict[str, dict[str, float]] = {}
    for track in TRACKS:
        chain = (l1_track[track] * l2_track[track] * l3_track[track]) ** (1 / 3)
        per_track[track] = {
            "L1": round(l1_track[track], 6),
            "L2": round(l2_track[track], 6),
            "L3": round(l3_track[track], 6),
            "chain": round(chain, 6),
            "L1_pct": round(100 * l1_track[track] / 3, 3),
            "L2_pct": round(100 * l2_track[track] / 3, 3),
            "L3_pct": round(100 * l3_track[track] / 3, 3),
            "chain_pct": round(100 * chain / 3, 3),
        }

    stage_values = {
        "L1": [l1_track[track] for track in TRACKS],
        "L2": [l2_track[track] for track in TRACKS],
        "L3": [l3_track[track] for track in TRACKS],
    }
    summary: dict[str, object] = {}
    for stage, values in stage_values.items():
        summary[stage] = {
            "mean": round(mean(values), 6),
            "sample_sd_across_tracks": round(statistics.stdev(values), 6),
            "mean_pct": round(100 * mean(values) / 3, 3),
            "sample_sd_pct": round(100 * statistics.stdev(values) / 3, 3),
        }
    chain_values = [per_track[track]["chain"] for track in TRACKS]
    summary["life_science_chain"] = round(100 * mean(chain_values) / 3, 3)
    summary["overall_two_domain"] = None

    input_paths = [
        difficulty_path,
        RESULTS / "fig_data_l1.csv",
        RESULTS / "fig_data_l2.csv",
        RESULTS / "fig_data_l3.csv",
        NEW / "scrna_claude-fable-5.json",
        NEW / "adjudications_new_models.json",
    ] + sorted((NEW / "meta_claude-fable-5").glob("*/l2_meta_scores.csv"))
    payload = {
        "_schema": {
            "artifact": "counterfactual fallback replay; NOT a canonical model score",
            "generated": str(date.today()),
            "fable_model": FABLE,
            "fallback_model": OPUS,
            "selection_rule": "Fable answer if present; otherwise canonical Opus score",
            "aggregation": "L1 world mean; L2 world->family->track; L3 eligible-world mean; geometric chain within track; arithmetic mean across 8 tracks",
            "important": "The direct API run did not execute fallback. Opus L3 substitutions for stopped/unrun tasks replay Opus from task start and are not observed mid-chain routes.",
            "canonical_scores_modified": False,
        },
        "summary": summary,
        "source_counts": {
            "L1": {
                "fable_answer": sum(row["source"] == "fable_answer" for row in l1_cells),
                "opus_fallback": sum(row["source"] == "opus_fallback" for row in l1_cells),
            },
            "L2": {
                "fable_answer": sum(row["source"] == "fable_answer" for row in l2_cells),
                "opus_fallback": sum(row["source"] == "opus_fallback" for row in l2_cells),
            },
            "L3": {
                "fable_answer": sum(row["source"] == "fable_answer" for row in l3_cells),
                "opus_fallback_from_task_start": sum(
                    row["source"] == "opus_fallback_from_task_start" for row in l3_cells
                ),
                "canonical_omissions": len(l3_omissions),
            },
        },
        "per_track": per_track,
        "L3_omissions": l3_omissions,
        "cells": {"L1": l1_cells, "L2": l2_cells, "L3": l3_cells},
        "input_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in input_paths},
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        f"wrote {OUT.relative_to(ROOT)} | "
        f"L1={summary['L1']['mean_pct']:.1f}+-{summary['L1']['sample_sd_pct']:.1f} "
        f"L2={summary['L2']['mean_pct']:.1f}+-{summary['L2']['sample_sd_pct']:.1f} "
        f"L3={summary['L3']['mean_pct']:.1f}+-{summary['L3']['sample_sd_pct']:.1f} "
        f"chain={summary['life_science_chain']:.1f}"
    )


if __name__ == "__main__":
    main()
