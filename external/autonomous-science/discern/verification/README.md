# DISCERN Result and Score Authority

This directory provides the reviewer-facing provenance map from each eligible
frozen model/world evaluation to the artifacts that establish its result.

## Files

- `authority_index.csv` — one row per eligible frozen model/world evaluation.
- `exclusions.csv` — explicit pre-run admissibility exclusions recorded by the
  frozen benchmark registry.

## Frozen evaluation universe

The release contains 233 worlds:

- 203 core DISCERN life-science tasks; and
- 30 preliminary Physics-extension worlds.

Eight models are represented in the extended artifact set. One explicit
model/world pair was excluded by the frozen admissibility registry before
scoring, leaving 1,863 authority-index rows.

## Evidence chain

Each row links, where applicable:

1. frozen manifest;
2. recorded output artifact(s);
3. recorded L1/L2 trace artifact(s);
4. deterministic grade artifact;
5. verifier artifact;
6. applicable adjudication-ledger entries;
7. accepted score or exclusion status; and
8. aggregate-result authority.

Multiple recorded output artifacts are preserved when a canonical world was
evaluated through repeated cells or replicates.

## Deterministic score fields

Most graders store the deterministic task score in `score`.

GWAS signal-EDA uses `core_score` as its authoritative 0-3 task score. That is
the field used by benchmark aggregation, figure-data extraction, and verifier
logic.

L3 uses `composite` for scoreable worlds.

## Human adjudication precedence

The adjudication ledgers contain different kinds of rulings and must not be
interpreted as a flat list of competing final scores.

For L1/L2, a numeric row-level `human_final` adjudication overrides the
pre-adjudication deterministic score.

For L3, the ledgers may contain axis-level or supporting rulings such as
data-fidelity, causal-calibration, reviewer-robustness, scientific-humility,
citation-integrity, or novelty decisions. These are retained as provenance
but are not themselves treated as row-level composite scores.

Only an adjudication explicitly identified as a derived/mechanical composite
overrides the deterministic L3 `composite`.

If no explicit composite adjudication exists, the frozen deterministic L3
composite remains the row-level score.

## L3 admissibility

L3 prior-gate/admissibility decisions are handled separately from score-axis
adjudications.

A `CONFOUNDED-EXCLUDED` row with an upheld gate exclusion has no accepted
numeric score and is not assigned zero. It remains in the authority table for
provenance with `accepted_status=confounded_excluded`.

These rows are excluded from the corresponding aggregate means according to
the frozen L3 protocol.

## Verifier exceptions

`verifier_status=documented_validation_override` denotes an accepted artifact
provenance gap explicitly recorded in `benchmark_registry.json`.

## Aggregate score authority

`authority_index.csv` is a row-level provenance table. It is not itself a
replacement for the frozen aggregate authorities.

For the canonical six-model core benchmark, the final aggregate authority is
`results/final_scores.json`, including documented post-adjudication per-track
CSV authorities.

The later Astra/GLM-5.3 extension is represented by the frozen eight-model
figure-data products and new-model adjudication ledger.

The Physics extension is represented by its frozen score products under
`results/final_scores/physics_extension/` and remains excluded from the core
DISCERN Overall Score.

Use the supplied reproduction scripts for paper-facing score and figure
regeneration rather than blindly re-averaging this CSV.
