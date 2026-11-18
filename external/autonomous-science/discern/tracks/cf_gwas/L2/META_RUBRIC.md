# GWAS L2 meta-review mapping

This retrospective mapper uses only `graded_*.json`, `verify_*.json`, the run manifest, and
`results/adjudications.json`. It never reads agent outputs or execution traces.

All four dimensions are in `[0,1]`; a world score is `3 * mean(A, I, M, C)`.

| Family | Analytical correctness (A) | Issue recognition (I) | Methodological response (M) | Result calibration (C) |
|---|---|---|---|---|
| Signal EDA | Mean of `lambda_ok` and `assess_ok` | Suspicious: `flagged`; objective: `assess_ok`; clean: `third_axis` no-overflag restraint | Suspicious: recorded flag-and-qualify `third_axis`; objective: usability `third_axis`; clean: analytical execution | Mean of `qualified` and `named_unavailable` |
| Locus | Mean of recall, precision, and locus-count agreement | `interp_score` | `exec_score / 2` | `issue_handled`; interpretation/calibration is tagged joint because the frozen record does not separate them |
| TWAS | Mean of normalized z-correlation, SNP fraction, top-gene recall, and sign agreement; decisive sign inversion is zero | Trap-specific recognition in the frozen verifier/adjudication reason | Recorded TWAS state: correct standard run 1, hand-rolled/partial 0.5, weak/empty 0 | Existing adjudicated ladder mapped to calibrated use/non-use |

The family score is the mean across worlds. GWAS L2 is the macro-average of Signal EDA,
Locus, and TWAS family scores. The legacy total is retained for provenance but is not averaged
again, because that would double-count its components.

For accepted Signal-EDA verifier overrides, only the revised three-axis core survives—not a revised
axis-by-axis record. That core is therefore assigned jointly to A/I/M, while C continues to use the
separately recorded qualification and unavailable-check fields. This avoids fabricating a decomposition.
