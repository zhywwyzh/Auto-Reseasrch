#!/usr/bin/env python3
"""Build the authoritative DISCERN benchmark-status registry.

The registry has two outputs:
  results/benchmark_registry.json  machine-readable source for paper tables
  BENCHMARK_STATUS.md              human-readable freeze dashboard

Only manifests explicitly listed in CANONICAL_RUNS count toward benchmark size. This prevents archives,
full-replicate manifests, smoke runs, and stale experiments from silently changing the paper's task count.
Run from anywhere:

    python gwas_counterfactual_benchmark/benchmark_registry.py

Use --check to fail when generated outputs are stale or when an unregistered canonical-looking manifest exists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent
JSON_OUT = ROOT / "results" / "benchmark_registry.json"
MD_OUT = ROOT / "BENCHMARK_STATUS.md"

MODEL_ROSTER = [
    "gpt-4.1",
    "gpt-5.6-sol",
    "claude-opus-5",
    "deepseek-v4-pro",
    "glm-5.2",
    "kimi-k3",
]

# Paper-facing count after the complete eight-track, six-model roster freeze (2026-08-23).
PAPER_TASK_CLAIM = 203

# Minimum result coverage required for the biology-domain freeze. "Validated" means complete eligible
# grades plus either complete independent-verification artifacts or an explicit documented validation
# decision in VALIDATION_OVERRIDES. Overrides remain visible in both registry outputs.
REQUIRED_VALIDATED_LEVELS = {
    "cf_gwas": ["L1", "L2", "L3"],
    "clinvar_acmg": ["L1", "L2", "L3"],
    "scrna": ["L1", "L2", "L3"],
    "bulk_rnaseq": ["L1", "L2", "L3"],
    "crispr_screen": ["L1", "L2", "L3"],
    "enhancer_activity": ["L1", "L2", "L3"],
    "hist_gene_exp": ["L1", "L2", "L3"],
    "protein_ddg": ["L1", "L2", "L3"],
}

# No designed-only biology tasks remain outside the required result freeze.
DESIGNED_NOT_IMPLEMENTED = []

# Explicit validation decisions whose supporting audit is documented outside per-model verify_*.json files.
# Overrides are visible in the generated registry; they never silently manufacture files.
VALIDATION_OVERRIDES = {
    "tracks/scrna/L2/results/scrna_l2_composition_run/manifest.json": {
        "models": MODEL_ROSTER,
        "basis": ("PAPER_NOTES G16d and results/final_scores.json: all six five-world composition "
                  "results finalized; design-owner validation confirmed 2026-08-23"),
        "artifact_gap": ("five non-Claude verify files predate the appended resolution_trap world "
                         "and cover 4/5 tasks; Claude composition verify file is absent"),
    },
}

# Model-specific worlds that are intentionally not run because the prior-knowledge gate makes the
# counterfactual inadmissible for that model. These are completed design outcomes, not missing results.
ADMISSIBILITY_EXCLUSIONS = {
    "tracks/bulk_rnaseq/L3/results/l3_run/manifest.json": {
        "claude-opus-5": {
            "worlds": ["cf_cytokine_flip"],
            "basis": ("PAPER_NOTES G15a: Claude predicts the data-supported DOWN direction and explicitly "
                      "holds the immunoparalysis prior, so the cytokine-storm flip cannot test "
                      "evidence-over-held-prior for this model."),
        },
    },
}

IGNORED_MANIFESTS = {
    "tracks/scrna/L2/results/scrna_l2_resolution_trap_run/manifest.json":
        "stale pre-merge run; resolution_trap is cell 4 of canonical scrna_l2_composition_run",
}

# Explicit allowlist: one canonical n=1 manifest per published task family.
CANONICAL_RUNS = [
    "tracks/bulk_rnaseq/L1/results/bulkrna_l1_run/manifest.json",
    "tracks/bulk_rnaseq/L2/results/bulk_l2_de_run/manifest.json",
    "tracks/bulk_rnaseq/L2/results/bulk_l2_gsea_run/manifest.json",
    "tracks/bulk_rnaseq/L2/results/bulk_l2_structure_run/manifest.json",
    "tracks/bulk_rnaseq/L3/results/l3_run/manifest.json",
    "tracks/cf_gwas/L1/results/gwas_qc_run/manifest.json",
    "tracks/cf_gwas/L2/results/gwas_signaleda_run/manifest.json",
    "tracks/cf_gwas/L2/results/gwas_task2_run/manifest.json",
    "tracks/cf_gwas/L2/results/gwas_twas_run/manifest.json",
    "tracks/cf_gwas/L3/results/l3_run/manifest.json",
    "tracks/clinvar_acmg/L1/results/clinvar_l1_run/manifest.json",
    "tracks/clinvar_acmg/L2/results/clinvar_l2_classify_run/manifest.json",
    "tracks/clinvar_acmg/L2/results/clinvar_l2_prioritize_run/manifest.json",
    "tracks/clinvar_acmg/L2/results/clinvar_l2_sf_run/manifest.json",
    "tracks/clinvar_acmg/L3/results/l3_run/manifest.json",
    "tracks/crispr_screen/L1/results/crispr_l1_run/manifest.json",
    "tracks/crispr_screen/L2/results/crispr_l2_calling_run/manifest.json",
    "tracks/crispr_screen/L2/results/crispr_l2_context_run/manifest.json",
    "tracks/crispr_screen/L2/results/crispr_l2_scoring_run/manifest.json",
    "tracks/crispr_screen/L3/results/l3_run/manifest.json",
    "tracks/enhancer_activity/L1/results/enhancer_l1_run/manifest.json",
    "tracks/enhancer_activity/L2/results/enhancer_l2_conservation_run/manifest.json",
    "tracks/enhancer_activity/L2/results/enhancer_l2_divergence_run/manifest.json",
    "tracks/enhancer_activity/L2/results/enhancer_l2_ranking_run/manifest.json",
    "tracks/enhancer_activity/L3/results/l3_run/manifest.json",
    "tracks/hist_gene_exp/L1/results/hist_qc_run/manifest.json",
    "tracks/hist_gene_exp/L2/results/hist_l2_quantify_run/manifest.json",
    "tracks/hist_gene_exp/L2/results/hist_l2_ranking_run/manifest.json",
    "tracks/hist_gene_exp/L2/results/hist_l2_regression_run/manifest.json",
    "tracks/hist_gene_exp/L3/results/l3_run/manifest.json",
    "tracks/protein_ddg/L1/results/protein_ddg_l1_run/manifest.json",
    "tracks/protein_ddg/L2/results/ddg_predict_run/manifest.json",
    "tracks/protein_ddg/L2/results/feature_effect_run/manifest.json",
    "tracks/protein_ddg/L2/results/stab_classify_run/manifest.json",
    "tracks/protein_ddg/L3/results/l3_run/manifest.json",
    "tracks/scrna/L1/results/scrna_l1_run/manifest.json",
    "tracks/scrna/L2/results/scrna_l2_annotation_run/manifest.json",
    "tracks/scrna/L2/results/scrna_l2_composition_run/manifest.json",
    "tracks/scrna/L2/results/scrna_l2_marker_de_run/manifest.json",
    "tracks/scrna/L3/results/l3_run/manifest.json",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def json_len(path: Path) -> int | None:
    try:
        obj = json.loads(path.read_text())
    except Exception:
        return None
    return len(obj) if isinstance(obj, list) else None


def artifact_world_labels(path: Path) -> list[str] | None:
    """Return task labels from a grade/verify list, or None for an unreadable shape."""
    try:
        rows = json.loads(path.read_text())
    except Exception:
        return None
    if not isinstance(rows, list):
        return None
    return [str(row.get("world_label", row.get("world", f"cell{row.get('cell', '?')}")))
            for row in rows if isinstance(row, dict)]


def best_artifact(run_dir: Path, prefix: str, model: str) -> tuple[str | None, int]:
    candidates = []
    for p in run_dir.glob(f"{prefix}*{model}*.json"):
        if p.name.startswith("aggregated_") or ".trace." in p.name or ".prerepair." in p.name:
            continue
        n = json_len(p)
        if n is not None:
            candidates.append((n, p.name))
    if not candidates:
        return None, 0
    n, name = max(candidates)
    return name, n


def run_identity(rel: str) -> tuple[str, str, str]:
    p = Path(rel)
    parts = p.parts
    track = parts[1]
    level = parts[2]
    family = parts[-2]
    return track, level, family


def discover_unregistered() -> list[str]:
    registered = set(CANONICAL_RUNS)
    found = set()
    for p in ROOT.glob("tracks/*/L[123]/results/*/manifest.json"):
        if "_archive" in p.parts or p.name != "manifest.json":
            continue
        found.add(str(p.relative_to(ROOT)))
    return sorted(found - registered - set(IGNORED_MANIFESTS))


def build_registry() -> dict:
    runs = []
    missing_manifests = []
    artifact_label_mismatches = []
    by_track_level: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    model_totals = {
        m: {"graded": 0, "verified_artifact": 0, "validated": 0, "gate_excluded": 0}
        for m in MODEL_ROSTER
    }

    for rel in CANONICAL_RUNS:
        path = ROOT / rel
        track, level, family = run_identity(rel)
        if not path.exists():
            missing_manifests.append(rel)
            continue
        manifest = json.loads(path.read_text())
        if not isinstance(manifest, list):
            raise ValueError(f"Manifest is not a JSON list: {rel}")
        n_tasks = len(manifest)
        labels = [str(x.get("world_label", x.get("world", f"cell{x.get('cell', '?')}"))) for x in manifest]
        run_dir = path.parent
        coverage = {}
        for model in MODEL_ROSTER:
            exclusion = ADMISSIBILITY_EXCLUSIONS.get(rel, {}).get(model, {})
            excluded_worlds = exclusion.get("worlds", [])
            unknown_exclusions = sorted(set(excluded_worlds) - set(labels))
            if unknown_exclusions:
                raise ValueError(f"Unknown gate-excluded worlds for {rel} / {model}: {unknown_exclusions}")
            expected_tasks = n_tasks - len(excluded_worlds)
            eligible_labels = [label for label in labels if label not in excluded_worlds]
            grade_file, graded = best_artifact(run_dir, "graded", model)
            verify_file, verified = best_artifact(run_dir, "verify", model)
            graded = min(graded, expected_tasks)
            verified = min(verified, expected_tasks)
            override = VALIDATION_OVERRIDES.get(rel, {})
            override_applies = model in override.get("models", [])
            validation_complete = verified == expected_tasks or override_applies
            if grade_file:
                got = artifact_world_labels(run_dir / grade_file)
                if got is None or Counter(got) != Counter(eligible_labels):
                    artifact_label_mismatches.append(
                        f"grade {rel} / {model}: expected {eligible_labels}, found {got}")
            if verify_file and verified == expected_tasks:
                got = artifact_world_labels(run_dir / verify_file)
                if got is None or Counter(got) != Counter(eligible_labels):
                    artifact_label_mismatches.append(
                        f"verify {rel} / {model}: expected {eligible_labels}, found {got}")
            coverage[model] = {
                "grade_file": grade_file,
                "graded_tasks": graded,
                "verify_file": verify_file,
                "verified_tasks": verified,
                "expected_tasks": expected_tasks,
                "gate_excluded_worlds": excluded_worlds,
                "gate_exclusion_basis": exclusion.get("basis"),
                "complete": graded == expected_tasks,
                "verified_complete": validation_complete,
                "validation_source": ("artifact" if verified == expected_tasks else
                                      "documented-override" if override_applies else None),
                "validation_basis": override.get("basis") if override_applies else None,
                "validation_artifact_gap": override.get("artifact_gap") if override_applies else None,
            }
            model_totals[model]["graded"] += graded
            model_totals[model]["verified_artifact"] += verified
            model_totals[model]["validated"] += expected_tasks if validation_complete else verified
            model_totals[model]["gate_excluded"] += len(excluded_worlds)

        n_complete = sum(v["complete"] for v in coverage.values())
        n_verified = sum(v["verified_complete"] for v in coverage.values())
        if n_verified == len(MODEL_ROSTER):
            status = "validated-full-roster"
        elif n_complete == len(MODEL_ROSTER):
            status = "graded-full-roster"
        elif n_complete or any(v["graded_tasks"] for v in coverage.values()):
            status = "partial-roster"
        else:
            status = "manifest-only"

        by_track_level[track][level] += n_tasks
        runs.append({
            "track": track,
            "level": level,
            "family": family,
            "manifest": rel,
            "manifest_sha256": sha256(path),
            "tasks": n_tasks,
            "world_labels": labels,
            "status": status,
            "full_roster_graded": n_complete,
            "full_roster_verified": n_verified,
            "coverage": coverage,
        })

    canonical_total = sum(r["tasks"] for r in runs)
    tracks = []
    for track in sorted(by_track_level):
        levels = {level: by_track_level[track].get(level, 0) for level in ("L1", "L2", "L3")}
        tracks.append({"track": track, "levels": levels, "tasks": sum(levels.values())})

    blockers = []
    if canonical_total != PAPER_TASK_CLAIM:
        blockers.append({
            "code": "paper-task-count-mismatch",
            "severity": "freeze-blocker",
            "detail": (f"Paper count is {PAPER_TASK_CLAIM}; explicit canonical manifests contain "
                       f"{canonical_total}. Reconcile before release."),
        })
    if missing_manifests:
        blockers.append({"code": "missing-canonical-manifest", "severity": "freeze-blocker",
                         "detail": ", ".join(missing_manifests)})
    unregistered = discover_unregistered()
    if unregistered:
        blockers.append({"code": "unregistered-manifest", "severity": "review-required",
                         "detail": ", ".join(unregistered)})
    if artifact_label_mismatches:
        blockers.append({"code": "artifact-world-label-mismatch", "severity": "freeze-blocker",
                         "detail": " | ".join(artifact_label_mismatches)})

    coverage_requirements = []
    for track, required_levels in REQUIRED_VALIDATED_LEVELS.items():
        for level in required_levels:
            relevant = [r for r in runs if r["track"] == track and r["level"] == level]
            incomplete = [r["family"] for r in relevant if r["status"] != "validated-full-roster"]
            met = bool(relevant) and not incomplete
            detail = ("all canonical families validated for all six models" if met else
                      ("not fully verified: " + ", ".join(incomplete) if relevant else
                       "no canonical families registered"))
            coverage_requirements.append({"track": track, "level": level,
                                          "required": "validated-full-roster", "met": met, "detail": detail})
            if not met:
                blockers.append({"code": f"required-coverage-{track}-{level.lower()}",
                                 "severity": "freeze-blocker", "detail": detail})

    planned_estimate = sum(x["estimated_tasks"] for x in DESIGNED_NOT_IMPLEMENTED)

    return {
        "schema_version": 1,
        "as_of": date.today().isoformat(),
        "definition": "One task is one entry in an explicitly allowlisted canonical n=1 manifest.",
        "model_roster": MODEL_ROSTER,
        "paper_task_claim": PAPER_TASK_CLAIM,
        "canonical_task_count": canonical_total,
        "task_claim_delta": PAPER_TASK_CLAIM - canonical_total,
        "designed_not_implemented_estimate": planned_estimate,
        "projected_task_count": canonical_total + planned_estimate,
        "canonical_run_count": len(runs),
        "tracks": tracks,
        "runs": runs,
        "model_coverage": model_totals,
        "required_validated_levels": REQUIRED_VALIDATED_LEVELS,
        "coverage_requirements": coverage_requirements,
        "designed_not_implemented": DESIGNED_NOT_IMPLEMENTED,
        "validation_overrides": VALIDATION_OVERRIDES,
        "admissibility_exclusions": ADMISSIBILITY_EXCLUSIONS,
        "ignored_manifests": IGNORED_MANIFESTS,
        "unregistered_manifests": unregistered,
        "missing_manifests": missing_manifests,
        "artifact_label_mismatches": artifact_label_mismatches,
        "freeze_blockers": blockers,
    }


def render_markdown(reg: dict) -> str:
    lines = [
        "# DISCERN Benchmark Status Registry",
        "",
        f"**As of:** {reg['as_of']}  ",
        f"**Registry schema:** v{reg['schema_version']}  ",
        f"**Counting rule:** {reg['definition']}",
        "",
        "This file is generated by `benchmark_registry.py`; do not edit task counts by hand. The explicit",
        "allowlist in that script defines which manifests are canonical and paper-facing.",
        "",
        "## Freeze summary",
        "",
        f"- Implemented canonical task count: **{reg['canonical_task_count']}**",
        f"- Designed-not-implemented tasks: **{reg['designed_not_implemented_estimate']}**",
        f"- Projected count from current registry + designs: **{reg['projected_task_count']}**",
        f"- Paper task count: **{reg['paper_task_claim']}**",
        f"- Difference (paper count − implemented registry): **{reg['task_claim_delta']:+d}**",
        f"- Canonical run families: **{reg['canonical_run_count']}**",
        f"- Benchmark models: **{len(reg['model_roster'])}**",
        "",
    ]
    if reg["freeze_blockers"]:
        lines += ["### Open freeze blockers", ""]
        for b in reg["freeze_blockers"]:
            lines.append(f"- **{b['severity']} — `{b['code']}`:** {b['detail']}")
        lines.append("")
    else:
        lines += ["**No registry-level freeze blockers detected.**", ""]

    lines += [
        "## Required biology-freeze coverage",
        "",
        "All eight tracks require validated L1–L3 coverage for all six models.",
        "",
        "| Track | Level | Required | Result | Detail |",
        "|---|---|---|---|---|",
    ]
    for req in reg["coverage_requirements"]:
        result = "PASS" if req["met"] else "FAIL"
        lines.append(f"| `{req['track']}` | {req['level']} | {req['required']} | **{result}** | {req['detail']} |")

    if reg["designed_not_implemented"]:
        lines += [
            "",
            "## Designed coverage not yet required for result freeze",
            "",
            "These designs count only as planning estimates until a canonical manifest exists.",
            "",
            "| Track | Level | Estimated tasks | Design status | Basis |",
            "|---|---|---:|---|---|",
        ]
        for item in reg["designed_not_implemented"]:
            lines.append(f"| `{item['track']}` | {item['level']} | ~{item['estimated_tasks']} | "
                         f"{item['status']} | {item['basis']} |")

    lines += [
        "## Tasks by track and level",
        "",
        "| Track | L1 | L2 | L3 | Total |",
        "|---|---:|---:|---:|---:|",
    ]
    for t in reg["tracks"]:
        lv = t["levels"]
        lines.append(f"| `{t['track']}` | {lv['L1']} | {lv['L2']} | {lv['L3']} | **{t['tasks']}** |")
    ltot = {l: sum(t["levels"][l] for t in reg["tracks"]) for l in ("L1", "L2", "L3")}
    lines.append(f"| **Total** | **{ltot['L1']}** | **{ltot['L2']}** | **{ltot['L3']}** | **{reg['canonical_task_count']}** |")

    lines += [
        "",
        "## Model coverage",
        "",
        "Counts distinguish eligible grades, per-task verification artifacts, validated eligible results, and",
        "prior-gate exclusions. A gate exclusion is a completed design outcome, not a missing run.",
        "",
        "| Model | Eligible graded | Verify artifacts | Validated eligible | Gate-excluded | Completed coverage |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    total = reg["canonical_task_count"]
    for model in reg["model_roster"]:
        c = reg["model_coverage"][model]
        completed = c["validated"] + c["gate_excluded"]
        lines.append(f"| `{model}` | {c['graded']} | {c['verified_artifact']} | {c['validated']} | "
                     f"{c['gate_excluded']} | {completed/total:.1%} |")

    lines += [
        "",
        "Validated counts may include an explicit documented override when per-task verification files",
        "are incomplete. The override does not manufacture verification artifacts:",
        "",
    ]
    for manifest, override in reg["validation_overrides"].items():
        lines.append(f"- `{manifest}`: {override['basis']}. Artifact gap: {override['artifact_gap']}.")

    lines += [
        "",
        "## Canonical run families",
        "",
        "`G/V` is the number of six roster models with complete grades / complete validation for that run.",
        "",
        "| Track | Level | Family | Tasks | Status | G/V | Manifest SHA-256 |",
        "|---|---|---|---:|---|---:|---|",
    ]
    for r in reg["runs"]:
        lines.append(
            f"| `{r['track']}` | {r['level']} | `{r['family']}` | {r['tasks']} | "
            f"{r['status']} | {r['full_roster_graded']}/{r['full_roster_verified']} | `{r['manifest_sha256'][:12]}` |"
        )

    lines += [
        "",
        "## Freeze protocol",
        "",
        "Before changing a paper-facing task count:",
        "",
        "1. Add or remove the canonical manifest in `CANONICAL_RUNS`.",
        "2. Run `python benchmark_registry.py`.",
        "3. Resolve every freeze blocker in this report.",
        "4. Update the abstract and paper tables from `results/benchmark_registry.json`.",
        "5. Record the registry JSON hash in the final reproduction package.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="fail if generated files are stale or any registry freeze blocker exists")
    args = ap.parse_args()
    reg = build_registry()
    json_text = json.dumps(reg, indent=2, sort_keys=True) + "\n"
    md_text = render_markdown(reg)

    if args.check:
        stale = not JSON_OUT.exists() or JSON_OUT.read_text() != json_text or not MD_OUT.exists() or MD_OUT.read_text() != md_text
        registry_error = bool(reg["freeze_blockers"])
        if stale:
            print("STALE: regenerate with `python benchmark_registry.py`")
        if registry_error:
            print("REGISTRY ERROR: freeze blockers remain; inspect BENCHMARK_STATUS.md after regeneration")
        return 1 if stale or registry_error else 0

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json_text)
    MD_OUT.write_text(md_text)
    print(f"wrote {JSON_OUT.relative_to(ROOT)}")
    print(f"wrote {MD_OUT.name}")
    print(f"canonical tasks={reg['canonical_task_count']} paper claim={reg['paper_task_claim']} blockers={len(reg['freeze_blockers'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
