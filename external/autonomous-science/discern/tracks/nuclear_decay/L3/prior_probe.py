"""
Materialize Nuclear L3's frozen Co-60 reference-prior Gate-0 adjudication into
grade_l3's prior_probe_cache.json.

Active anchor:
    co60-terrestrial-half-life

State:
    5 successfully executed models: PRIOR_HELD
    Claude Opus 5: provider/model refusal -> execution-unresolved/N/A

No API/model calls are made here.
"""

from pathlib import Path
import json
import sys


HERE = Path(__file__).resolve().parent

RUN = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else HERE / "results" / "l3_run"
)

ANCHOR = "co60-terrestrial-half-life"

RAW_PATH = (
    HERE
    / "physics_probe_results"
    / "co60_reference_gate0_nonclaude.json"
)

ADJ_PATH = (
    HERE
    / "physics_probe_results"
    / "co60_reference_gate0_adjudication.json"
)

RAW = json.loads(RAW_PATH.read_text())
ADJ = json.loads(ADJ_PATH.read_text())

models = RAW.get("models", {})

held = {
    row["model"]: row
    for row in ADJ.get("adjudications", [])
    if row.get("adjudication") == "PRIOR_HELD"
}

cache = {}

for model, adj in held.items():
    r = models.get(model)

    if not r:
        raise RuntimeError(
            f"raw successful probe missing for {model}"
        )

    answer = str(r.get("answer", "") or "").strip()

    if not (
        r.get("completed") is True
        and r.get("execution_unresolved") is False
        and answer
    ):
        raise RuntimeError(
            f"raw successful probe invariant failed for {model}"
        )

    cache[f"{model}|{ANCHOR}"] = {
        "model": model,
        "gene": ANCHOR,
        "anchor": ANCHOR,
        "knew_prior": True,
        "prior_knew": True,
        "available": True,
        "answer": answer,
        "source": (
            "physics_probe_results/"
            "co60_reference_gate0_nonclaude.json"
        ),
        "adjudication": "prior_held",
        "note": (
            "Named-fact/surface prior: ordinary terrestrial Co-60 "
            "half-life ~5.27 y, elicited before any counterfactual "
            "stellar-state evidence."
        ),
    }

# Claude is intentionally absent while refusal remains unresolved.
claude_rows = [
    row
    for row in ADJ.get("adjudications", [])
    if row.get("model") == "claude-opus-5"
]

if claude_rows:
    cr = claude_rows[0]

    if cr.get("adjudication") != "EXECUTION_UNRESOLVED_NA":
        raise RuntimeError(
            "Claude must be unresolved/N/A if omitted from cache"
        )

RUN.mkdir(parents=True, exist_ok=True)

p = RUN / "prior_probe_cache.json"
p.write_text(json.dumps(cache, indent=2))

print("[probe-cache] wrote", p)
print("[probe-cache] entries:", len(cache))
print("[probe-cache] Claude intentionally absent: refusal/unresolved/N/A")
