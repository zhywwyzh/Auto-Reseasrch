# Reproducing DISCERN from recorded artifacts

This release separates **artifact reproduction** from **benchmark execution**.

The paper-facing score, table, and figure reproduction workflow operates on
the frozen recorded manifests, outputs, traces, deterministic grades,
verification records, adjudication ledgers, and final score products contained
in this repository.

It does not require rerunning evaluated language models.

## Environment

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r environment/requirements.txt
```

For local repository modules, run commands from the repository root. If a
script is launched directly from another working directory, set:

```bash
export PYTHONPATH="$PWD:$PWD/reproduction"
```

## Frozen evaluation universe

The public provenance maps are:

- `prompts/prompt_index.csv`
- `prompts/recorded_prompt_variants.csv`
- `verification/authority_index.csv`
- `verification/exclusions.csv`
- `results/benchmark_registry.json`
- `results/final_scores.json`

The core DISCERN benchmark contains 203 life-science tasks.

The preliminary Physics extension contains 30 additional worlds and is not
included in the core DISCERN Overall Score.

## Score authority

Do not reconstruct reported scores by blindly averaging raw graded JSON files.

Some track-level published values use frozen post-adjudication score
authorities. The row-level provenance and accepted-score chain are documented
in `verification/authority_index.csv`, while the canonical six-model aggregate
authority is recorded in `results/final_scores.json`.

The later eight-model extension uses the frozen extended figure-data products
and associated adjudication records.

## No model calls

Paper-output reproduction should use only recorded artifacts. Evaluated model
providers are not needed for this workflow.

Scripts whose purpose is benchmark execution or model verification against a
live provider are distinct from the artifact-only reproduction workflow and
should not be invoked merely to regenerate the paper's frozen summaries.

## Data sources

See:

- `DATA_SOURCES_AND_LICENSES.md`
- `SOURCE_DATA_POLICY.tsv`
- `SOURCE_DATA_CHECKSUMS.tsv`

Some upstream source datasets are intentionally not redistributed. Their
omission does not prevent reproduction of frozen paper scores from the
recorded benchmark artifacts.

## Clean-room validation

The release is designed so that paper-facing score, table, and figure
regeneration can be exercised from a fresh copy of this public repository
without access to the private development tree.

The exact validated clean-room commands and output checks are recorded during
release QA and should be used as the final reproduction path.
