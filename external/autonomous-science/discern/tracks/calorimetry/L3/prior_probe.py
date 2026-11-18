"""
Materialize Calorimetry L3's frozen task-matched Gate-0 adjudications into
grade_l3's prior_probe_cache.json.

Active targets:
- cu-cp-bulk-reuse       (~8 nm world): 5 successful PRIOR_HELD probes;
  Kimi remains execution-unresolved/N/A and is intentionally absent.
- cu-cp-bulk-reuse-50nm (~50 nm world): 6/6 PRIOR_HELD.

NO API calls.
"""

from pathlib import Path
import hashlib
import json
import sys


HERE = Path(__file__).resolve().parent

RUN = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else HERE / "results" / "l3_run"
)

ANCHOR8 = "cu-cp-bulk-reuse"
ANCHOR50 = "cu-cp-bulk-reuse-50nm"

RAW8 = json.loads(
    (HERE / "physics_probe_results" / "nano_cu_prior_gate.json").read_text()
)

ADJ8 = json.loads(
    (HERE / "physics_probe_results" / "nano_cu_gate0_adjudication.json").read_text()
)

RAW50_NONCLAUDE = json.loads(
    (
        HERE
        / "physics_probe_results"
        / "nano_cu_50nm_prior_gate_nonclaude.json"
    ).read_text()
)

RAW50_CLAUDE = json.loads(
    (
        HERE
        / "physics_probe_results"
        / "nano_cu_50nm_prior_gate_claude.json"
    ).read_text()
)

ADJ50 = json.loads(
    (
        HERE
        / "physics_probe_results"
        / "nano_cu_50nm_gate0_adjudication.json"
    ).read_text()
)


def sha_text(text):
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def cache_entry(
    model,
    anchor,
    answer,
    source,
):

    return {
        "model":
            model,

        "gene":
            anchor,

        "anchor":
            anchor,

        "knew_prior":
            True,

        "prior_knew":
            True,

        "available":
            True,

        "answer":
            answer,

        "source":
            source,

        "adjudication":
            "prior_held",
    }


# ======================================================================================
# 8-nm frozen anchor
# ======================================================================================

if not (
    ADJ8.get(
        "successful_prior_probes"
    )
    == 5
    and ADJ8.get(
        "successful_prior_held"
    )
    == 5
    and ADJ8.get(
        "execution_unresolved"
    )
    == 1
    and ADJ8.get(
        "any_prior_knew_false"
    )
    is False
):

    raise RuntimeError(
        "8-nm Gate-0 summary no longer matches "
        "the frozen 5-held + 1-N/A state"
    )


models8 = RAW8.get(
    "models",
    {},
)


def pick8(
    *aliases,
):

    for alias in aliases:

        if alias in models8:
            return alias

    for key in models8:

        lk = key.lower()

        if any(
            alias.lower()
            in lk
            for alias in aliases
        ):

            return key

    raise KeyError(
        aliases
    )


mapping8 = {
    "gpt-4.1":
        pick8(
            "gpt-4.1"
        ),

    # Preserve historical alias.
    "gpt-5.6":
        pick8(
            "gpt-5.6"
        ),

    "gpt-5.6-sol":
        pick8(
            "gpt-5.6"
        ),

    "deepseek-v4-pro":
        pick8(
            "deepseek-v4-pro",
            "deepseek",
        ),

    "glm-5.2":
        pick8(
            "glm-5.2",
            "glm",
        ),

    "claude-opus-5":
        pick8(
            "claude-opus-5",
            "claude",
        ),
}


cache = {}


for benchmark_model, raw_key in mapping8.items():

    record = models8[
        raw_key
    ]

    answer = str(
        record.get(
            "answer",
            "",
        )
        or ""
    ).strip()

    if (
        not record.get(
            "completed"
        )
        or not answer
    ):

        raise RuntimeError(
            "frozen successful 8-nm probe missing answer: "
            f"{benchmark_model}/{raw_key}"
        )

    cache[
        f"{benchmark_model}|{ANCHOR8}"
    ] = cache_entry(
        benchmark_model,
        ANCHOR8,
        answer,
        "physics_probe_results/nano_cu_prior_gate.json",
    )


# ======================================================================================
# 50-nm frozen anchor
# ======================================================================================

expected50 = {
    "gpt-4.1",
    "gpt-5.6-sol",
    "glm-5.2",
    "deepseek-v4-pro",
    "kimi-k3",
    "claude-opus-5",
}

roster50 = set(
    ADJ50.get(
        "canonical_roster"
    )
    or []
)

if roster50 != expected50:

    raise RuntimeError(
        "unexpected 50-nm canonical roster: "
        f"{sorted(roster50)}"
    )


if not (
    ADJ50.get(
        "successful_prior_probes"
    )
    == 6
    and ADJ50.get(
        "successful_prior_held"
    )
    == 6
    and ADJ50.get(
        "execution_unresolved"
    )
    == 0
    and ADJ50.get(
        "any_prior_knew_false"
    )
    is False
    and ADJ50.get(
        "anchor_switch_required"
    )
    is False
):

    raise RuntimeError(
        "50-nm Gate-0 summary is not "
        "the frozen 6/6 PRIOR_HELD state"
    )


adj50 = {
    row[
        "canonical_key"
    ]:
        row
    for row in ADJ50.get(
        "adjudications",
        [],
    )
}


if set(
    adj50
) != expected50:

    raise RuntimeError(
        "unexpected 50-nm adjudication keys: "
        f"{sorted(adj50)}"
    )


models50 = RAW50_NONCLAUDE.get(
    "models",
    {},
)


for model in sorted(
    expected50
):

    row = adj50[
        model
    ]

    if (
        row.get(
            "prior_knew"
        )
        is not True
        or row.get(
            "adjudication"
        )
        != "prior_held"
    ):

        raise RuntimeError(
            f"50-nm adjudication is not PRIOR_HELD for {model}"
        )


    if model == "claude-opus-5":

        if RAW50_CLAUDE.get(
            "model"
        ) != model:

            raise RuntimeError(
                "50-nm Claude raw artifact model mismatch"
            )

        if RAW50_CLAUDE.get(
            "completed"
        ) is not True:

            raise RuntimeError(
                "50-nm Claude raw probe is not completed"
            )

        answer = RAW50_CLAUDE.get(
            "answer"
        )

        source = (
            "physics_probe_results/"
            "nano_cu_50nm_prior_gate_claude.json"
        )

    else:

        record = models50.get(
            model
        )

        if not isinstance(
            record,
            dict,
        ):

            raise RuntimeError(
                f"50-nm raw non-Claude record missing for {model}"
            )

        if record.get(
            "completed"
        ) is not True:

            raise RuntimeError(
                f"50-nm raw probe is not completed for {model}"
            )

        answer = record.get(
            "answer"
        )

        source = (
            "physics_probe_results/"
            "nano_cu_50nm_prior_gate_nonclaude.json"
        )


    if (
        not isinstance(
            answer,
            str,
        )
        or not answer.strip()
    ):

        raise RuntimeError(
            f"50-nm raw answer missing for {model}"
        )


    expected_hash = row.get(
        "answer_sha256"
    )

    actual_hash = sha_text(
        answer
    )


    if actual_hash != expected_hash:

        raise RuntimeError(
            f"50-nm raw-answer hash mismatch for {model}: "
            f"{actual_hash} != {expected_hash}"
        )


    cache[
        f"{model}|{ANCHOR50}"
    ] = cache_entry(
        model,
        ANCHOR50,
        answer,
        source,
    )


RUN.mkdir(
    parents=True,
    exist_ok=True,
)

cache_path = (
    RUN
    / "prior_probe_cache.json"
)

cache_path.write_text(
    json.dumps(
        cache,
        indent=2,
    )
    + "\n"
)


print(
    "[probe-cache] wrote",
    cache_path,
    f"({len(cache)} entries)",
)

print(
    "[probe-cache] 8-nm: 5 successful PRIOR_HELD models materialized "
    "(plus legacy gpt-5.6 alias); Kimi-k3 remains absent as "
    "execution-unresolved/N/A."
)

print(
    "[probe-cache] 50-nm: 6/6 canonical PRIOR_HELD models materialized "
    f"under {ANCHOR50!r}."
)
