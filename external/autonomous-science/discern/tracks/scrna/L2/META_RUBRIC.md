# scRNA-seq L2 meta-review mapping

The mapper uses only frozen grade notes, verification, manifests, and adjudication. It explicitly
excludes the abandoned standalone `scrna_l2_resolution_trap_run`; the canonical resolution trap is
already one world in the composition family. No agent output or trace is read.

| Dimension | Existing evidence |
|---|---|
| Analytical correctness | Mean of every recovery/composition/accuracy fraction recorded in the grade note; the adjudicated ladder is fallback when no fraction exists |
| Issue recognition | Recorded `flagged`, `recognized`, `named`, `verified`, or confound diagnosis, with negative guards for “did not flag,” “no awareness,” and fooled outcomes |
| Methodological response | Recorded exclusion, pseudobulk, tuning, verification, preservation, or confound-aware response |
| Result calibration | Existing adjudicated distinction among full, weak-but-honest, silently right, and fooled outcomes |

Annotation, marker-DE, and composition family means are macro-averaged. Ten canonical composition
cells have no matching verifier row: all five Claude worlds (the verifier file is absent), plus the
`resolution_trap` row omitted from each of the other five verifier files. Their frozen grader and any
cell-adjudication evidence are still mapped, and the missing-verifier count is emitted in validation.
Dimensions are equally averaged and rescaled to 0–3.

For deepseek's `doublet_as_type` composition cell, `final_scores.json` records 3 while the explicit human
adjudication ledger records 2 and explains that the injected doublet population was missed. The meta-review
uses the cell adjudication (the more specific source) and exposes the resulting roll-up difference.
