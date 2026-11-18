"""Derive direct-Fable and Fable-to-Opus replay costs without changing run scores.

The direct row prices every canonical Fable invocation that exists on disk. The refusal-stop protocol
produced all 181 L1/L2 outputs and seven L3 outputs; the remaining 15 L3 tasks were not invoked. Its
paper-facing $/task denominator remains the common 203 assigned life-science tasks.

The replay row retains the cost of every recorded Fable invocation, then adds the canonical Opus cost
for each cell whose score source in the fallback-replay artifact is Opus. This is a derived replay,
not an observed product-surface bill or a claim about Anthropic's internal routing charges.

Run: python3 fable_cost_replay.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
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
N_ASSIGNED = 203
OUT = NEW / "FABLE_COST_claude-fable-5_and_opus-replay.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def price(rates: dict, model: str, tokens_in: int, tokens_out: int) -> float:
    rate = rates["models"][model]
    return (
        tokens_in / 1_000_000 * rate["input_usd_per_mtok"]
        + tokens_out / 1_000_000 * rate["output_usd_per_mtok"]
    )


def meter(path: Path, model: str) -> tuple[int, int, int]:
    data = json.loads(path.read_text())
    meta = data["_meta"]
    estimated = meta.get("tokens") == "estimated"
    factor = float(meta.get("calibration_factor", 1.0)) if estimated else 1.0
    own = (meta.get("by_model") or {}).get(model)
    if own:
        return (
            round(float(own.get("in", 0)) * factor),
            round(float(own.get("out", 0)) * factor),
            int(own.get("calls", 0)),
        )
    return (
        round(float(meta.get("in", 0)) * factor),
        round(float(meta.get("out", 0)) * factor),
        int(meta.get("calls", 0)),
    )


def output_path(manifest_path: Path, row: dict, model: str) -> Path:
    return manifest_path.parent / f"{Path(row['agent_output']).stem}_{model}.json"


def main() -> None:
    pricing_path = RESULTS / "pricing.json"
    replay_path = NEW / "FALLBACK_REPLAY_claude-fable-5_to_claude-opus-5.json"
    registry_path = RESULTS / "world_registry.csv"
    rates = json.loads(pricing_path.read_text())
    replay = json.loads(replay_path.read_text())
    with registry_path.open(newline="") as handle:
        registry = [row for row in csv.DictReader(handle) if row["level"] in {"L1", "L2"}]
    if len(registry) != 181:
        raise RuntimeError(f"expected 181 canonical L1/L2 tasks, found {len(registry)}")

    manifest_cache: dict[Path, list[dict]] = {}

    def registry_output(level: str, track: str, family: str | None, world: str, model: str) -> Path:
        matches = [
            row
            for row in registry
            if row["level"] == level
            and row["track"] == track
            and row["world"] == world
            and (level == "L1" or row["family"] == family)
        ]
        if len(matches) != 1:
            raise RuntimeError(f"registry join failed for {(level, track, family, world)}: {len(matches)}")
        source = matches[0]
        manifest_path = ROOT / source["source_manifest"]
        rows = manifest_cache.setdefault(manifest_path, json.loads(manifest_path.read_text()))
        worlds = [row for row in rows if row.get("world_label") == world]
        if len(worlds) != 1:
            raise RuntimeError(f"manifest join failed for {(level, track, family, world)}: {len(worlds)}")
        return output_path(manifest_path, worlds[0], model)

    def l3_output(track: str, world: str, model: str) -> Path:
        manifest_path = ROOT / f"tracks/{track}/L3/results/l3_run/manifest.json"
        rows = manifest_cache.setdefault(manifest_path, json.loads(manifest_path.read_text()))
        worlds = [row for row in rows if row.get("world") == world]
        if len(worlds) != 1:
            raise RuntimeError(f"L3 manifest join failed for {(track, world)}: {len(worlds)}")
        return output_path(manifest_path, worlds[0], model)

    fable_paths: list[tuple[str, Path]] = []
    for row in registry:
        path = registry_output(row["level"], row["track"], row.get("family"), row["world"], FABLE)
        if not path.exists():
            raise RuntimeError(f"missing canonical Fable L1/L2 output: {path}")
        fable_paths.append((row["level"], path))
    for track in TRACKS:
        manifest_path = ROOT / f"tracks/{track}/L3/results/l3_run/manifest.json"
        for row in json.loads(manifest_path.read_text()):
            path = output_path(manifest_path, row, FABLE)
            if path.exists():
                fable_paths.append(("L3", path))

    fable_level_counts = Counter(level for level, _ in fable_paths)
    if fable_level_counts != {"L1": 79, "L2": 102, "L3": 7}:
        raise RuntimeError(f"Fable invocation coverage changed: {dict(fable_level_counts)}")

    fallback_paths: list[tuple[str, Path]] = []
    for level, cells in replay["cells"].items():
        for cell in cells:
            if not cell["source"].startswith("opus_fallback"):
                continue
            if level == "L3":
                path = l3_output(cell["track"], cell["world"], OPUS)
            else:
                path = registry_output(level, cell["track"], cell.get("family"), cell["world"], OPUS)
            if not path.exists():
                raise RuntimeError(f"fallback replay selected a missing Opus output: {path}")
            fallback_paths.append((level, path))

    fallback_level_counts = Counter(level for level, _ in fallback_paths)
    expected_fallback = {"L1": 29, "L2": 44, "L3": 19}
    if fallback_level_counts != expected_fallback:
        raise RuntimeError(
            f"Opus fallback coverage changed: {dict(fallback_level_counts)} != {expected_fallback}"
        )

    def aggregate(paths: list[tuple[str, Path]], model: str) -> dict:
        usage = [meter(path, model) for _, path in paths]
        tokens_in = sum(row[0] for row in usage)
        tokens_out = sum(row[1] for row in usage)
        calls = sum(row[2] for row in usage)
        usd = price(rates, model, tokens_in, tokens_out)
        return {
            "model": model,
            "n_invocations": len(paths),
            "n_estimated_token_records": sum(
                json.loads(path.read_text())["_meta"].get("tokens") == "estimated"
                for _, path in paths
            ),
            "by_level": dict(Counter(level for level, _ in paths)),
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "total_tokens": tokens_in + tokens_out,
            "calls": calls,
            "usd": round(usd, 6),
        }

    fable_cost = aggregate(fable_paths, FABLE)
    opus_increment = aggregate(fallback_paths, OPUS)
    replay_usd = fable_cost["usd"] + opus_increment["usd"]
    replay_tokens = fable_cost["total_tokens"] + opus_increment["total_tokens"]
    chain = float(replay["summary"]["life_science_chain"])

    output = {
        "_schema": {
            "generated_by": "fable_cost_replay.py",
            "scope": "cost-only derived view; no run output or score is modified",
            "pricing": "uncached, non-batch first-party list rates in results/pricing.json",
            "direct_denominator": "203 assigned life-science tasks; 188 were invoked and 15 L3 tasks were not run under the refusal-stop protocol",
            "replay_definition": "all recorded Fable invocation cost plus canonical Opus cost on the 92 cells selected for fallback",
            "warning": "The replay is not an observed product-surface bill and does not claim Anthropic's internal routing charges.",
        },
        "direct_fable": {
            **fable_cost,
            "n_assigned": N_ASSIGNED,
            "n_not_invoked": N_ASSIGNED - fable_cost["n_invocations"],
            "usd_per_assigned_task": round(fable_cost["usd"] / N_ASSIGNED, 6),
            "quality_chain": None,
            "usd_per_quality_point": None,
        },
        "opus_fallback_increment": opus_increment,
        "fable_to_opus_replay": {
            "n_assigned": N_ASSIGNED,
            "underlying_model_invocations": fable_cost["n_invocations"] + opus_increment["n_invocations"],
            "total_tokens": replay_tokens,
            "usd": round(replay_usd, 6),
            "usd_per_assigned_task": round(replay_usd / N_ASSIGNED, 6),
            "quality_chain": chain,
            "usd_per_quality_point": round((replay_usd / N_ASSIGNED) / chain, 6),
        },
        "input_sha256": {
            "results/pricing.json": sha256(pricing_path),
            "results/world_registry.csv": sha256(registry_path),
            "results/new_models/FALLBACK_REPLAY_claude-fable-5_to_claude-opus-5.json": sha256(replay_path),
        },
    }
    OUT.write_text(json.dumps(output, indent=2) + "\n")
    print(
        f"direct Fable: ${output['direct_fable']['usd_per_assigned_task']:.6f}/task; "
        f"replay: ${output['fable_to_opus_replay']['usd_per_assigned_task']:.6f}/task, "
        f"${output['fable_to_opus_replay']['usd_per_quality_point']:.6f}/quality point"
    )


if __name__ == "__main__":
    main()
