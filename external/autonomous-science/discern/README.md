---
pretty_name: DISCERN Benchmark
license: other
tags:
  - benchmark
  - scientific-discovery
  - agents
  - genomics
  - reproducibility
---

# DISCERN Benchmark

DISCERN-authored code and documentation use the [MIT license](LICENSE).
This does not relicense datasets, model weights, or other third-party materials.
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for source-specific terms
and uncertainties. Prepared benchmark inputs are provided with attribution;
publication does not assert a blanket license over third-party materials.
Download CADD and ESM runtime references separately using
[EXTERNAL_RUNTIME.md](EXTERNAL_RUNTIME.md).

This repository is the anonymous reproducibility artifact accompanying an ICLR 2027 submission.

DISCERN evaluates whether AI agents follow observed scientific evidence when that evidence can conflict with familiar or memorized scientific priors. The release contains frozen benchmark definitions, prompts, recorded model artifacts, deterministic grading outputs, adjudication records, verification metadata, and the scripts used to regenerate the paper-facing summaries and figures.

## Benchmark scope

The frozen molecular-life-science core contains **203 tasks across eight tracks**:

| Stage | Scope |
|---|---:|
| L1 | 79 tasks |
| L2 | 102 tasks across 24 analysis families |
| L3 | 22 worlds |
| **Total** | **203 tasks** |

The eight core tracks cover:

- bulk RNA-seq
- counterfactual GWAS
- ClinVar / ACMG interpretation
- CRISPR screening
- enhancer activity
- histone / gene-expression analysis
- protein stability
- single-cell RNA-seq

The release also includes a **preliminary cross-domain physics extension** covering calorimetry and nuclear decay. Physics is reported separately and is **not included in the core DISCERN Overall Score**.

## What is included

The reviewer-facing artifact includes, where redistribution is permitted:

- frozen task and world manifests
- benchmark builders and sandbox/tool definitions
- prompts and recorded prompt variants
- golden standards and reference artifacts
- recorded model outputs and traces
- deterministic grades and verifier outputs
- human adjudication and correction ledgers
- prior-probe / Gate-0 artifacts where applicable
- canonical score products
- figure-data tables
- scripts for regenerating tables and figures
- environment requirements
- data-source, provenance, and redistribution documentation
- row-level score-authority and exclusion indexes

The benchmark science, prompts, frozen scores, and adjudications were not modified for this release.

## Models and score authority

All evaluated models use the same task and scoring definitions. The common model
index is `results/models/index.json`; model coverage is reported explicitly rather
than dividing models into an original cohort and later additions. Fable's refusals
and incomplete coverage remain visible. Fable-to-Opus fallback is a derived replay,
not an independently evaluated model.

Finalized scores and human adjudications retain their authority. Historical score
files are preserved rather than recomputed or averaged into a new score. The model
index points to those sources, including `results/final_scores.json`,
`results/model_reports/`, and the adjudication ledgers. The legacy
`results/new_models` path is only a compatibility alias for existing scripts.

### Row-level audit

`verification/authority_index.csv` provides the reviewer-facing row-level score-authority map across the frozen evaluation universe.

It records the accepted score source, gate state, verifier state, and adjudication provenance used to connect recorded model-world results to paper-facing aggregates.

`verification/exclusions.csv` records explicit exclusions.

## Prompt release

Prompt materials are under:

`prompts/`

The release contains an indexed, content-addressed prompt package with recorded runtime variants. L1/L2 prompts are recoverable from the recorded evaluation traces. L3 runtime context is defined jointly by its manifest, dossier, tool environment, and prior-probe machinery.

## Evaluating an additional model

See [Evaluate your model](EVALUATE_MODEL.md) for runtime setup, model credentials,
a one-task smoke run, all-track execution, prior probes, grading, human adjudication,
and score aggregation. Live evaluation requires API access; the published-artifact
reproduction commands below do not run a new model.

## Reproducing paper-facing artifacts

Use Python 3 and install the small reviewer-facing dependency set:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r environment/requirements.txt
```

From the repository root, regenerate the canonical registries and figure-data products:

```bash
python extract_world_registry.py
python extract_figure_data.py
python extend_figure_data.py
```

Paper-facing table and figure builders are under:

`reproduction/`

For example:

```bash
cd reproduction

python tab01_coverage.py
python tab02_main_results.py
python fig03_chain_landscape.py
python fig03_extended_landscape.py
python fig06_full_8models.py
python make_extended_figures.py
```

These reproduction steps operate on the **recorded frozen artifacts**. They do not require rerunning commercial model APIs.

## Clean-room validation

Before release, the public artifact was copied into an isolated clean-room directory with:

- model/API credentials removed
- Python network access blocked
- access to the private development repository blocked
- private release-staging paths blocked

The clean-room validation regenerated the canonical registries, figure-data products, paper-facing tables, and figures from the public artifact alone.

See `VALIDATION.md` for the original release's validation summary. Those historical
checks do not certify subsequent edits. See `RELEASE_UPDATE.md` for the current
local staging status and outstanding runtime/publication checks.

For the current local candidate, use the scientific Python environment and run:

```bash
python -m unittest -v test_release_packaging
python check_runtime_inputs.py
python check_runtime_smoke.py
python reproduce_current_results.py
```

The seven packaging tests and all 46 representative sandbox input-loading checks
pass. They do not rerun agents or validate every analysis. The current-results
entry point separately regenerates result Figures 3–5 and the ten Table 1 numeric
rows from finalized exports, including Fable's conditional row and the derived
fallback replay. Its source-data assertions pass in a network-disabled sandbox;
see `verification/current_reproduction.json`. It does not reproduce the paper's
illustrative Figures 1–2 or regrade raw transcripts.

## Data sources and redistribution

See `DOCUMENTATION_ERRATA.md` for corrections to historical inventory citations
and six-model figure footnotes. These do not change recorded evaluations.

The runnable package includes prepared task inputs and required runtime resources,
not complete upstream collections used only to construct the benchmark. Upstream
datasets are linked in `DATA_SOURCES_AND_LICENSES.md`. The frozen prepared worlds
are used directly for evaluation; rebuilding them is a separate workflow.

`verification/runtime_files.csv` indexes staged inputs and checksums. Some runtime
references require separate installation or permission review; see `RUNTIME_DATA.md`.

DISCERN combines benchmark-generated artifacts with representations derived from multiple scientific sources.

Redistribution rights differ by source. Raw upstream data are therefore **not automatically included** merely because they were available during benchmark construction.

See:

- `DATA_SOURCES_AND_LICENSES.md`
- `SOURCE_DATA_POLICY.tsv`
- `SOURCE_DATA_CHECKSUMS.tsv`

These files describe the release posture for each source, including whether the artifact contains data, derived representations, preparation code, or citation/checksum-only provenance.

## Repository structure

```text
.
├── tracks/                       benchmark tracks and frozen run artifacts
├── prompts/                      indexed prompt package
├── results/                      canonical and extended result products
├── verification/                 row-level authority and exclusion indexes
├── reproduction/                 paper-facing table and figure builders
├── environment/                  reviewer-facing environment requirements
├── DATA_SOURCES_AND_LICENSES.md
├── SOURCE_DATA_POLICY.tsv
├── SOURCE_DATA_CHECKSUMS.tsv
├── REPRODUCIBILITY.md
├── VALIDATION.md
└── MANIFEST.sha256
```

## Integrity

`MANIFEST.sha256` contains SHA-256 checksums for the public release files, excluding Git metadata and the checksum manifest itself.

The repository was prepared from a fresh anonymous Git history rather than from the private development repository.

## Anonymous-review note

This artifact is prepared for anonymous review. The current worktree is audited
for configured account identifiers, archive ownership, BAM program headers,
document metadata, and recognizable credential signatures. See
`verification/identity_audit.json` and `verification/identity_cleanup.json` for
the audit scope and metadata-only change ledger. The scan does not prove the
absence of every unknown identifier.

Third-party scientific attribution and licensing information are preserved where required.
