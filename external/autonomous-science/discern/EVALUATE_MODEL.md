# Evaluate an additional model

The prepared tasks can be run with another model. This is different from
`reproduce_current_results.py`, which reproduces the published roster from recorded
artifacts. Live evaluation uses paid model, reviewer, and judge APIs and requires
human adjudication. The release does not yet provide a one-command, arbitrary-model
leaderboard update.

## 1. Install and check the prepared inputs

Work in a separate clone so evaluation cannot overwrite your reference copy:

```bash
git lfs install
git clone https://huggingface.co/datasets/discern-bench-anon/discern-benchmark
cd discern-benchmark
git lfs pull
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r environment/runtime-smoke-requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
command -v bwrap
python -m unittest -v test_release_packaging
python check_runtime_inputs.py
python check_runtime_smoke.py
```

Linux with working bubblewrap/user namespaces is required. The runtime requirements
record a tested CPU environment, not a portable lockfile for every platform. The
smoke checks load inputs inside the sealed sandbox; they do not evaluate a model.
Resolve missing inputs before proceeding. Follow [EXTERNAL_RUNTIME.md](EXTERNAL_RUNTIME.md)
to obtain CADD and ESM from their owners, subject to their terms. Do not rerun world
builders as an installation step: they can overwrite the prepared benchmark.

## 2. Configure the model

`models.py` routes model IDs by family. Set the relevant credential in your local
environment, never in a committed file:

| Family | Environment variable |
| --- | --- |
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Gemini | `GEMINI_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |
| GLM | `ZHIPU_API_KEY` |
| Kimi | `MOONSHOT_API_KEY` |
| Grok | `XAI_API_KEY` |
| Qwen | `DASHSCOPE_API_KEY` |

Use an API model ID supported by the endpoint and not already represented in the
release. IDs become output filenames, so avoid slashes and path characters. A new
provider or a local model server needs an adapter in `models.py`; an arbitrary ID
does not automatically select an arbitrary endpoint. Preserve tool calls, usage
accounting, refusal handling, and sandbox isolation when adding an adapter.

L3 also needs the three reviewers configured in `run_l3.py` (currently GLM-4.6,
Gemini-3.1-flash-lite-preview, and DeepSeek-reasoner). Grading/verification defaults
to GPT-5.5 and needs its credential. Check endpoint availability before launching.
Missing reviewers or grader fallbacks are not a complete, protocol-matched run.
Record any replacement, generation-budget change, model version, and evaluation date.

## 3. Run one task, then the suite

Set your real API model ID in place of the placeholder. This command makes live
calls and writes outputs into the prepared run directory:

```bash
export DISCERN_MODEL='YOUR_MODEL_ID'
python run_level.py scrna L1 "$DISCERN_MODEL" 1 --cells 0
```

Inspect the output and trace under `tracks/scrna/L1/results/scrna_l1_run/` for
successful tool execution, valid final output, and recorded usage. Runners are not
a safe resume interface: repeated commands may overwrite the same model's outputs.
Use a fresh evaluation clone or explicitly select only unfinished cells.

For each core track, run `L1` and each analysis-family key in its `SPEC['L2']`:

```bash
python run_level.py scrna annotation "$DISCERN_MODEL" 1
```

The eight core track IDs are `cf_gwas`, `clinvar_acmg`, `bulk_rnaseq`, `scrna`,
`crispr_screen`, `enhancer_activity`, `hist_gene_exp`, and `protein_ddg`.
Read the family keys and run directories without making API calls:

```bash
python - <<'PY'
import task_spec
for track in ('cf_gwas', 'clinvar_acmg', 'bulk_rnaseq', 'scrna',
              'crispr_screen', 'enhancer_activity', 'hist_gene_exp', 'protein_ddg'):
    spec = task_spec.load(track)
    print(track, 'L1', spec['L1']['run_dir'])
    for family, config in spec['L2'].items():
        print(track, family, config['run_dir'])
PY
```

Before exposing a model to L3 evidence, run the track's prior probe in its separate
context, then run the prepared L3 manifest:

```bash
python tracks/scrna/L3/prior_probe.py tracks/scrna/L3/results/l3_run "$DISCERN_MODEL"
python run_l3.py tracks/scrna/L3/results/l3_run/manifest.json "$DISCERN_MODEL"
```

Repeat with each core track ID. Preserve the probe cache/overlay, including refusals
and unknown priors; do not substitute another model's eligibility. The third
positional argument of `run_l3.py` is an output suffix, not a reviewer. L3 runs three
review rounds. Core coverage is 79 L1, 102 L2 across 24 families, and 22 L3 tasks;
L3 scoring eligibility can be smaller. Physics is a separate extension, not part of
the eight-track Overall score.

## 4. Grade, verify, and adjudicate

Example L1 and L2 commands (both require completed outputs):

```bash
python grade_generic.py tracks/scrna/L1/results/scrna_l1_run "$DISCERN_MODEL"
python verify_grades.py tracks/scrna/L1/results/scrna_l1_run "$DISCERN_MODEL"
python tracks/scrna/L2/grade_scrna_l2.py tracks/scrna/L2/results/scrna_l2_annotation_run "$DISCERN_MODEL"
```

Resolve other L2 graders with `graders.grader_for(track, family)`. After grading,
resolve the verifier's filename prefix with `graders.graded_prefix(run_dir, model)`
and pass it as the third argument to `verify_grades.py`; prefixes differ by family.
L1 grading includes an LLM-assisted branch, so it is not wholly offline.

```bash
python grade_l3.py tracks/scrna/L3/results/l3_run "$DISCERN_MODEL"
python verify_l3.py tracks/scrna/L3/results/l3_run "$DISCERN_MODEL"
```

Human experts adjudicate L1/L2 disagreements and review each L3 response. Save
model/task identifiers, original grades, final rulings, and reasons. Apply rulings
before aggregation; raw graded files alone are not authoritative when a ledger
overrides them. Do not edit existing models' rulings or bypass adjudication guards.

## 5. Report the new model without changing the published record

Map L2 outcomes through the track-specific `L2/map_l2_meta.py` rules to the shared
four dimensions before averaging. Inspect their roster/output configuration before
running them: published exporters and aggregation scripts contain fixed-roster
assumptions and are not an automatic registration system for a new model.

For finalized scores on the 0–100 scale, average L1 and eligible L3 tasks within
each track. For L2, average the four mapped dimensions per task, then tasks within
each family, then families equally. The track score is the geometric mean of its
three level scores; Overall averages the eight track scores equally. Do not silently
omit missing tracks, treat prior-ineligible L3 tasks as zero, or report incomplete
coverage as a full-suite score.

Report coverage and eligibility alongside level/Overall scores, commitment,
conditional novelty, and novelty yield. Record agent-only input/output tokens,
API calls, code executions, and dated pricing separately from reviewers, judges,
and verification. Keep new tables and adjudication records separate from the
published exports until their mappings and totals have been reviewed. See
[REPRODUCIBILITY.md](REPRODUCIBILITY.md) for reproducing the existing paper rather
than evaluating an additional model.
