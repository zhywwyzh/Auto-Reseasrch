"""Shared I/O, provenance, aggregation, and validation for L2 meta-review.

This layer NEVER reads agent outputs or traces.  It consumes only the frozen
deterministic grades, verifier records, manifests (for world identity), and the
human adjudication ledger.  Track-specific scripts supply the evidence mapping.
"""

from __future__ import annotations

import csv
import json
import os
import math
import re
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Callable, Iterable


_FROZEN_MODELS = (
    "claude-opus-5",
    "deepseek-v4-pro",
    "glm-5.2",
    "gpt-4.1",
    "gpt-5.6-sol",
    "kimi-k3",
)
# POST-FREEZE ROSTER ADDITIONS (2026-09-04). The frozen six are the default and are what every
# published figure/table was built from. A post-freeze model (glm-5.3, claude-fable-5, ...) can be
# meta-mapped WITHOUT touching frozen outputs by setting BOTH:
#     L2_META_MODELS=<model>            -- map only that model
#     L2_META_OUT=<dir>                 -- write elsewhere than tracks/<t>/L2/results/meta_review
# Unset, behaviour is byte-identical to the frozen pipeline.
MODELS = tuple(
    m.strip() for m in os.environ["L2_META_MODELS"].split(",") if m.strip()
) if os.environ.get("L2_META_MODELS") else _FROZEN_MODELS

DIMENSIONS = (
    "analytical_correctness",
    "issue_recognition",
    "methodological_response",
    "result_calibration",
)


@dataclass(frozen=True)
class MetaContext:
    track: str
    family: str
    run_name: str
    model: str
    manifest: dict[str, Any]
    graded: dict[str, Any]
    verify: dict[str, Any]
    raw_score: float
    legacy_final: float
    legacy_score_source: str
    adjudication: dict[str, Any] | None

    @property
    def world(self) -> str:
        world = self.graded.get("world") or self.graded.get("world_label")
        if not world:
            raise RuntimeError(f"Missing world/world_label in graded row: {self.graded}")
        return str(world)

    @property
    def clean(self) -> bool:
        # Historical manifests generally carry issue_present explicitly.
        # Newer tracks may carry only issue_type. Preserve historical
        # behavior when issue_present is available and otherwise fall back
        # to the documented reporting taxonomy.
        issue_present = self.manifest.get("issue_present")

        if issue_present is not None:
            return (not bool(issue_present)) or self.world == "clean"

        issue_type = str(self.manifest.get("issue_type") or "").strip().lower()

        if issue_type:
            return issue_type in {"none", "clean", "null"} or self.world == "clean"

        return self.world == "clean"

    @property
    def evidence_text(self) -> str:
        parts = [
            self.graded.get("note", ""),
            self.graded.get("detail", ""),
            self.verify.get("reason", ""),
            (self.adjudication or {}).get("reason", ""),
        ]
        return " | ".join(str(x) for x in parts if x).lower()


def clamp01(value: Any) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(value):
        return 0.0
    return max(0.0, min(1.0, value))


def avg(values: Iterable[Any]) -> float:
    vals = [float(v) for v in values if v is not None]
    return clamp01(mean(vals)) if vals else 0.0


def score_from_dimensions(dimensions: dict[str, float]) -> float:
    """Equal-weight four-axis score, scaled back to the benchmark's 0--3 range."""
    return 3.0 * mean(clamp01(dimensions[d]) for d in DIMENSIONS)


def token_bool(text: str, key: str) -> bool | None:
    match = re.search(rf"(?<![a-z0-9_]){re.escape(key)}\s*=\s*(true|false)", text, re.I)
    return None if not match else match.group(1).lower() == "true"


def token_number(text: str, key: str) -> float | None:
    match = re.search(
        rf"(?<![a-z0-9_]){re.escape(key)}\s*=\s*([-+]?\d+(?:\.\d+)?)",
        text,
        re.I,
    )
    return None if not match else float(match.group(1))


def first_number(text: str, patterns: Iterable[str]) -> float | None:
    """Return the first numeric value captured by an explicit recorded-note pattern."""
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return float(match.group(1))
    return None


def explicit_recognition(text: str) -> bool | None:
    """Conservative recognition signal from already-written grade/verify reasons."""
    negative = (
        r"did not flag|didn't flag|not flag(?:ged)?|no (?:explicit )?(?:flag|recognition|awareness)|"
        r"missed (?:the )?(?:issue|artifact|confound|trap)|not handled|silently right|fooled"
    )
    if re.search(negative, text, re.I):
        return False
    positive = (
        r"\bflagged\b|\brecognized\b|\bidentified\b|\bdetected\b|\bnamed\b|\bcaught\b|"
        r"\bdiagnosed\b|\bverified\b|\bconfounded\b|\bqualified\b"
    )
    return True if re.search(positive, text, re.I) else None


def ladder_analysis(score: float, recognized: bool | None = None) -> float:
    """Fallback only when a track has no separable quantitative component."""
    if score >= 2:
        return 1.0
    if score >= 1:
        return 0.25 if recognized is True else 0.5
    return 0.0


def ladder_dimensions(
    score: float,
    *,
    clean: bool,
    recognized: bool | None = None,
    analysis: float | None = None,
    method: float | None = None,
    calibration: float | None = None,
) -> dict[str, float]:
    """Documented fallback for legacy graders that stored only a ladder and a flag.

    Explicit track evidence always takes precedence.  This function makes the
    residual assumptions uniform and visible instead of hiding them in eight scripts.
    """
    a = ladder_analysis(score, recognized) if analysis is None else clamp01(analysis)
    if recognized is None:
        if clean:
            i = 1.0 if score >= 2 else 0.5 if score >= 1 else 0.0
        else:
            i = 1.0 if score in (1, 3) else 0.0
    else:
        i = float(recognized)

    if method is None:
        if clean:
            m = a
        elif a >= 0.75 and i >= 0.75:
            m = 1.0
        elif a > 0 or i > 0:
            m = 0.5
        else:
            m = 0.0
    else:
        m = clamp01(method)

    if calibration is None:
        if clean:
            c = 1.0 if score >= 2 else 0.5 if score >= 1 else 0.0
        elif score >= 3:
            c = 1.0
        elif score >= 2:
            c = 0.5
        elif score >= 1:
            c = 0.5 if i > 0 else 0.25
        else:
            c = 0.0
    else:
        c = clamp01(calibration)

    return dict(zip(DIMENSIONS, (a, i, m, c)))


def apply_extreme_manual_adjudication(
    dimensions: dict[str, float], context: MetaContext
) -> tuple[dict[str, float], str | None]:
    """Respect decisive human overrides without pretending to reinterpret prose.

    A manual 3 means the legacy evidence was adjudicated fully correct/handled;
    a manual 0 means it was adjudicated a full miss.  Intermediate overrides keep
    the track mapper's component evidence and remain visible in provenance.
    """
    adj = context.adjudication
    if not adj or adj.get("resolution") in {"det-correct", "deterministic-stands", "det-stands"}:
        return dimensions, None
    if context.track == "cf_gwas" and context.family == "signal_eda":
        # Signal-EDA's accepted verifier ruling stores only a revised 0--3 core,
        # not which of its three original axes changed. The track mapper assigns
        # that inseparable core to A/I/M and preserves the separately recorded C.
        return dimensions, "manual_signal_core_joint_mapping"
    final = float(adj["human_final"])
    if final == 3:
        return {d: 1.0 for d in DIMENSIONS}, "manual_3_all_axes"
    if final == 0:
        return {d: 0.0 for d in DIMENSIONS}, "manual_0_all_axes"
    return dimensions, "manual_intermediate_component_mapping"


def _find_graded_file(run_dir: Path, model: str) -> Path:
    files = sorted(run_dir.glob(f"graded*{model}.json"))
    if len(files) != 1:
        raise RuntimeError(f"Expected one graded file for {run_dir} / {model}; found {files}")
    return files[0]


def _load_adjudications(root: Path) -> list[dict[str, Any]]:
    """Human ledger, plus the RECONSTRUCTED bulk/hist L2 rulings when that file is present.

    bulk_rnaseq and hist_gene_exp never had their per-world L2 rulings written to
    results/adjudications.json -- only a post-adjudication total per model survived, in each track's
    authoritative CSV.  Those totals are world-weighted sums over a fixed denominator, so the point total
    is exact, and the verifier column determines which worlds moved (9 of 12 model-cells accepted every
    verifier disagreement; one is deterministic-stands; two are partial and carry a flagged conservative
    choice). Thus 10 of 12 cells are exactly determined. See build_reconstructed_l2_adjudications.py. Rows from that file are marked
    _reconstructed: true and are kept in a SEPARATE file so the human ledger stays pristine.
    """
    data = json.loads((root / "results/adjudications.json").read_text())
    rows = list(data.get("adjudications", []))
    extra = root / "results/adjudications_reconstructed_l2.json"
    if extra.exists():
        rows += list(json.loads(extra.read_text()).get("adjudications", []))
    # Post-freeze new-model rulings live in their own ledger with a lighter schema; translate them
    # into the shape this mapper expects. Only consulted for models named in L2_META_MODELS, so the
    # frozen roster's mapping is unaffected.
    nm = root / "results/new_models/adjudications_new_models.json"
    if nm.exists() and os.environ.get("L2_META_MODELS"):
        wanted = set(MODELS)
        for r in json.loads(nm.read_text()).get("rulings", []):
            if r.get("model") in wanted and isinstance(r.get("human_final"), (int, float)):
                rows.append({
                    "level": "L2", "track": r.get("track"), "run_dir": r.get("run", ""),
                    "world": r.get("world"), "model": r.get("model"),
                    "deterministic_original": r.get("det"), "llm_judge": r.get("judge"),
                    "human_final": r.get("human_final"),
                    # Use the finalized mapper's existing override vocabulary.
                    # In particular Signal-EDA only projects an adjudicated core
                    # onto A/I/M for manual-override; a generic label lost that
                    # ruling while still marking the row adjudicated.
                    "resolution": ("manual-override" if r.get("human_final") != r.get("det")
                                   else "deterministic-stands"),
                    "reason": r.get("reason", ""),
                    "_post_freeze": True,
                })
    return rows


def _adjudication_for(
    adjudications: list[dict[str, Any]], track: str, run_name: str, model: str, world: str
) -> dict[str, Any] | None:
    matches = [
        a
        for a in adjudications
        if a.get("level") == "L2"
        and a.get("track") == track
        and Path(str(a.get("run_dir", ""))).name == run_name
        and a.get("model") == model
        and a.get("world") == world
    ]
    if len(matches) > 1:
        raise RuntimeError(f"Duplicate adjudications: {track}/{run_name}/{model}/{world}")
    return matches[0] if matches else None


def run_track_mapping(
    *,
    script_file: str,
    track: str,
    families: dict[str, str],
    mapper: Callable[[MetaContext], tuple[dict[str, float], dict[str, Any]]],
) -> dict[str, Any]:
    root = Path(script_file).resolve().parents[3]
    track_dir = root / "tracks" / track
    adjudications = _load_adjudications(root)
    rows: list[dict[str, Any]] = []

    for family, run_name in families.items():
        run_dir = track_dir / "L2/results" / run_name
        manifest_rows = json.loads((run_dir / "manifest.json").read_text())
        manifests = {str(x["world_label"]): x for x in manifest_rows}

        for model in MODELS:
            graded_path = _find_graded_file(run_dir, model)
            graded_payload = json.loads(graded_path.read_text())

            if isinstance(graded_payload, list):
                graded_rows = graded_payload
            elif (
                isinstance(graded_payload, dict)
                and isinstance(graded_payload.get("scores"), list)
            ):
                graded_rows = graded_payload["scores"]
            else:
                raise RuntimeError(
                    f"Unsupported graded-file schema for {graded_path}: "
                    f"{type(graded_payload).__name__}"
                )

            verify_path = run_dir / f"verify_{model}.json"
            verify_rows = json.loads(verify_path.read_text()) if verify_path.exists() else []
            verifies = {str(x["world"]): x for x in verify_rows}
            if len(graded_rows) != len(manifests):
                raise RuntimeError(
                    f"Coverage mismatch {track}/{family}/{model}: "
                    f"{len(graded_rows)} grades vs {len(manifests)} worlds"
                )

            for graded in graded_rows:
                world = str(
                    graded.get("world")
                    or graded.get("world_label")
                    or ""
                )
                if not world:
                    raise RuntimeError(
                        f"Missing world/world_label in {graded_path}: {graded}"
                    )
                if world not in manifests:
                    raise RuntimeError(f"Unknown world {track}/{family}/{world}")
                raw_score = graded.get("score", graded.get("core_score"))
                if raw_score is None:
                    raise RuntimeError(f"Missing score {track}/{family}/{model}/{world}")
                adj = _adjudication_for(adjudications, track, run_name, model, world)
                legacy_final = float(adj["human_final"]) if adj else float(raw_score)
                legacy_score_source = "adjudications.human_final" if adj else "graded.score"
                context = MetaContext(
                    track=track,
                    family=family,
                    run_name=run_name,
                    model=model,
                    manifest=manifests[world],
                    graded=graded,
                    verify=verifies.get(world, {}),
                    raw_score=float(raw_score),
                    legacy_final=legacy_final,
                    legacy_score_source=legacy_score_source,
                    adjudication=adj,
                )
                dimensions, evidence = mapper(context)
                if set(dimensions) != set(DIMENSIONS):
                    raise RuntimeError(
                        f"Bad dimension keys {track}/{family}/{model}/{world}: {dimensions.keys()}"
                    )
                dimensions = {d: round(clamp01(dimensions[d]), 6) for d in DIMENSIONS}
                dimensions, adjudication_mapping = apply_extreme_manual_adjudication(dimensions, context)
                world_score = round(score_from_dimensions(dimensions), 6)
                rows.append(
                    {
                        "track": track,
                        "family": family,
                        "run": run_name,
                        "model": model,
                        "world": world,
                        "issue_present": not context.clean,
                        **dimensions,
                        "meta_score": world_score,
                        "legacy_raw_score": context.raw_score,
                        "legacy_final_score": context.legacy_final,
                        "legacy_score_source": context.legacy_score_source,
                        "graded_file": str(graded_path.relative_to(root)),
                        "verify_file": str(verify_path.relative_to(root)) if verify_path.exists() else None,
                        "verify_det": context.verify.get("det"),
                        "verify_llm": context.verify.get("llm"),
                        "verify_record_present": bool(context.verify),
                        "adjudicated": bool(adj),
                        "adjudication_mapping": adjudication_mapping,
                        "joint_evidence": bool(evidence.get("joint_evidence", False)),
                        "mapping_evidence": evidence,
                    }
                )

    expected = sum(
        len(json.loads((track_dir / "L2/results" / run / "manifest.json").read_text()))
        for run in families.values()
    ) * len(MODELS)
    if len(rows) != expected:
        raise RuntimeError(f"Expected {expected} rows for {track}; produced {len(rows)}")

    family_summary: dict[str, Any] = {}
    for family in families:
        family_summary[family] = {}
        for model in MODELS:
            selected = [r for r in rows if r["family"] == family and r["model"] == model]
            dims = {d: mean(r[d] for r in selected) for d in DIMENSIONS}
            family_summary[family][model] = {
                "n_worlds": len(selected),
                "dimensions": {d: round(v, 6) for d, v in dims.items()},
                "meta_score": round(mean(r["meta_score"] for r in selected), 6),
                "legacy_final_mean": round(mean(r["legacy_final_score"] for r in selected), 6),
            }

    track_summary: dict[str, Any] = {}
    for model in MODELS:
        family_rows = [family_summary[f][model] for f in families]
        dims = {
            d: mean(fr["dimensions"][d] for fr in family_rows)
            for d in DIMENSIONS
        }
        macro_score = mean(fr["meta_score"] for fr in family_rows)
        dimension_score = score_from_dimensions(dims)
        if abs(macro_score - dimension_score) > 2e-6:
            raise RuntimeError(f"Aggregation invariant failed for {track}/{model}")
        track_summary[model] = {
            "n_families": len(families),
            "n_worlds": sum(fr["n_worlds"] for fr in family_rows),
            "dimensions": {d: round(v, 6) for d, v in dims.items()},
            "meta_score": round(macro_score, 6),
            "legacy_family_macro": round(
                mean(fr["legacy_final_mean"] for fr in family_rows), 6
            ),
        }

    canonical_names = {
        "cf_gwas": "GWAS",
        "clinvar_acmg": "clinvar",
        "scrna": "scRNA",
    }
    aggregate = json.loads((root / "results/final_scores.json").read_text())["track_aggregation"]
    canonical_track = canonical_names.get(track, track)
    # A post-freeze model has NO historical pre-meta L2 entry in final_scores.json (that file is the
    # frozen six's authority and is never rewritten for new models). Skip the historical comparison
    # for such models rather than KeyError; the frozen roster's audit is unchanged.
    current_l2 = {
        model: float(
            aggregate[canonical_track][model].get(
                "L2_superseded_pre_l2_meta",
                aggregate[canonical_track][model].get(
                    "L2_superseded", aggregate[canonical_track][model]["L2"]
                ),
            )
        )
        for model in MODELS
        if model in aggregate.get(canonical_track, {})
    }
    legacy_comparison = {
        model: {
            "historical_pre_meta_l2": current_l2[model],
            "cell_ledger_family_macro": track_summary[model]["legacy_family_macro"],
            "difference": round(track_summary[model]["legacy_family_macro"] - current_l2[model], 6),
        }
        for model in MODELS
        if model in current_l2
    }

    result = {
        "_schema": {
            "version": "L2-meta-v1",
            "classification_policy": "Explicit issue_present; otherwise issue_type; missing flag alone never implies clean (2026-09-06 canonical correction)",
            "dimensions": list(DIMENSIONS),
            "dimension_range": [0, 1],
            "world_score": "3 * arithmetic_mean(A, I, M, C)",
            "family_score": "arithmetic mean of eligible world scores",
            "track_score": "macro-average of family scores",
            "sources": "graded_*.json + verify_*.json + manifests + results/adjudications.json; no agent outputs/traces",
            "score_precedence": "adjudications.human_final when a cell ruling exists; otherwise graded score",
        },
        "track": track,
        "families": families,
        "models": list(MODELS),
        "n_rows": len(rows),
        "rows": rows,
        "family_summary": family_summary,
        "track_summary": track_summary,
        "legacy_comparison": legacy_comparison,
        "provenance_summary": {
            "graded_cells": len(rows),
            "verify_records_present": sum(bool(r["verify_record_present"]) for r in rows),
            "verify_records_absent": sum(not bool(r["verify_record_present"]) for r in rows),
            "human_adjudications_applied": sum(bool(r["adjudicated"]) for r in rows),
            "score_sources": {
                source: sum(r["legacy_score_source"] == source for r in rows)
                for source in sorted({r["legacy_score_source"] for r in rows})
            },
        },
        "validation": {
            "coverage_expected": expected,
            "coverage_observed": len(rows),
            "dimension_bounds": "passed",
            "family_means": "passed",
            "track_macro_equals_dimension_mean": "passed",
            "historical_pre_meta_l2_loaded_for_audit_only": "passed",
            "missing_verify_records_disclosed": sum(not bool(r["verify_record_present"]) for r in rows),
        },
    }

    # A regenerated proposal is not automatically an approved scoring revision.
    # Do not overwrite frozen ledgers with a different scoring version. Explicit
    # alternate output directories remain available for review-only candidates.
    from audit_l2_reconciliation import TRACK_KEYS, require_track_reconciliation
    if (track in TRACK_KEYS and set(MODELS) == set(_FROZEN_MODELS)
            and not os.environ.get("L2_META_OUT")):
        require_track_reconciliation(
            track, rows, json.loads((root / "results/final_scores.json").read_text())
        )

    out_dir = (Path(os.environ["L2_META_OUT"]) if os.environ.get("L2_META_OUT")
               else track_dir / "L2/results/meta_review")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "l2_meta_scores.json").write_text(json.dumps(result, indent=2) + "\n")
    with (out_dir / "l2_meta_scores.csv").open("w", newline="") as handle:
        fields = [
            "track", "family", "run", "model", "world", "issue_present",
            *DIMENSIONS, "meta_score", "legacy_raw_score", "legacy_final_score",
            "adjudicated", "legacy_score_source", "joint_evidence", "graded_file", "verify_file",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{track}: {len(rows)}/{expected} cells mapped; validation passed")
    for model in MODELS:
        print(f"  {model:<18} {track_summary[model]['meta_score']:.3f}")
    return result
