#!/usr/bin/env python3
"""Read-only L2 reconciliation. Never applies a proposal or reads agent outputs.

Validate world dimensions -> family means -> track means against the approved
track_aggregation entries, not the historical `levels` blocks. Canonical values
are rounded to three decimals; dimension and export rounding have separate bounds.
Run from any directory: python audit_l2_reconciliation.py [--without-export]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent
DIMENSIONS = ("analytical_correctness", "issue_recognition",
              "methodological_response", "result_calibration")
TRACK_KEYS = {"bulk_rnaseq": "bulk_rnaseq", "cf_gwas": "GWAS",
              "clinvar_acmg": "clinvar", "crispr_screen": "crispr_screen",
              "enhancer_activity": "enhancer_activity", "hist_gene_exp": "hist_gene_exp",
              "protein_ddg": "protein_ddg", "scrna": "scRNA"}
CANONICAL_TOL = 0.000501  # three-decimal canonical rounding, not a score adjustment
EXPORT_TOL = 0.00011     # exported dimensions and scores have four decimals


def reconcile_rows(track, rows, canonical, *, score_tolerance=2e-6):
    """Return all errors and derived means; no writes and no tolerance back-fitting."""
    expected = canonical["track_aggregation"][TRACK_KEYS[track]]
    models = set(canonical["roster"])
    errors, families, identities, world_sets = [], defaultdict(list), set(), defaultdict(set)
    for row in rows:
        model, family, world = row["model"], row["family"], row["world"]
        key = model, family, world
        if key in identities:
            errors.append(f"{track}: duplicate cell {key}")
        identities.add(key)
        world_sets[model].add((family, world))
        try:
            dims = [float(row[d]) for d in DIMENSIONS]
            score = float(row["meta_score"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"{track}/{key}: missing/non-numeric dimensions or meta_score")
            continue
        if not all(math.isfinite(d) and 0 <= d <= 1 for d in dims):
            errors.append(f"{track}/{key}: invalid dimension bounds")
        if not math.isfinite(score) or abs(3 * mean(dims) - score) > score_tolerance:
            errors.append(f"{track}/{key}: world dimension-score mismatch")
        families[model, family].append(score)
    if set(world_sets) != models:
        errors.append(f"{track}: roster mismatch: {sorted(world_sets)}")
    if len({frozenset(v) for v in world_sets.values()}) != 1:
        errors.append(f"{track}: models do not share the same family/world inventory")
    means = {}
    for model in sorted(models):
        fs = [mean(v) for (m, _), v in families.items() if m == model]
        if not fs:
            errors.append(f"{track}/{model}: no family scores")
            continue
        value = mean(fs)
        approved = float(expected[model]["L2"])
        means[model] = {"derived": value, "canonical": approved,
                        "difference": value - approved}
        if abs(value - approved) > CANONICAL_TOL:
            errors.append(f"{track}/{model}: derived {value:.6f} != canonical {approved:.6f}")
    return {"track": track, "n_rows": len(rows), "means": means, "errors": errors}


def require_track_reconciliation(track, rows, canonical):
    report = reconcile_rows(track, rows, canonical)
    if report["errors"]:
        raise RuntimeError("L2 canonical reconciliation failed; no output should be published.\n"
                           + "\n".join(report["errors"]))
    return report


def audit(root=ROOT, *, check_export=True):
    root = Path(root)
    canonical = json.loads((root / "results/final_scores.json").read_text())
    proposal = json.loads((root / "results/l2_meta_review_proposal.json").read_text())
    errors, reports, ledger_cells = [], [], {}
    for track in TRACK_KEYS:
        path = root / f"tracks/{track}/L2/results/meta_review/l2_meta_scores.json"
        result = json.loads(path.read_text())
        report = reconcile_rows(track, result["rows"], canonical)
        reports.append(report)
        errors.extend(report["errors"])
        for row in result["rows"]:
            ledger_cells[track, row["model"], row["world"], row["family"]] = row
        for model, info in report["means"].items():
            for source, value in (
                ("proposal", proposal["tracks"][track][model]["meta_score"]),
                ("track_summary", result["track_summary"][model]["meta_score"]),
            ):
                if abs(float(value) - info["derived"]) > 2e-6:
                    errors.append(f"{track}/{model}: {source} differs from its world ledger")
    if sum(r["n_rows"] for r in reports) != 612:
        errors.append("Frozen-eight L2 inventory must contain 612 model-world cells")
    if check_export:
        with (root / "results/fig_data_l2.csv").open(newline="") as f:
            exported = list(csv.DictReader(f))
        # Match exports by model/world plus explicit family aliases, never fuzzy names.
        aliases = {"signal-eda": "signal_eda", "secondary_findings": "sf",
                   "effect_ranking": "ranking", "stab_classify": "stability_classification"}
        normalized = {}
        for key, row in ledger_cells.items():
            t, m, w, f = key
            normalized[t, m, w, aliases.get(f, f)] = row
        seen = set()
        for row in exported:
            key = row["track"], row["model"], row["world"], aliases.get(row["family"], row["family"])
            if key in seen:
                errors.append(f"export duplicate: {key}")
            seen.add(key)
            original = normalized.get(key)
            if original is None:
                errors.append(f"export unmatched: {key}")
                continue
            for field in (*DIMENSIONS, "meta_score"):
                if abs(float(row[field]) - float(original[field])) > EXPORT_TOL:
                    errors.append(f"export differs from ledger: {key}/{field}")
        if seen != set(normalized):
            errors.append("Export and ledger inventories differ")
    return {"status": "FAIL" if errors else "PASS", "tracks": reports, "errors": errors}


def assert_canonical_l2(root=ROOT, *, check_export=True):
    report = audit(root, check_export=check_export)
    if report["errors"]:
        raise RuntimeError("L2 source reconciliation FAILED. See L2_RECONCILIATION_20260906.md.\n"
                           + "\n".join(report["errors"]))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--without-export", action="store_true")
    args = parser.parse_args()
    result = audit(check_export=not args.without_export)
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result["errors"]))
