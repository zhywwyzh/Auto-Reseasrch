# ClinVar/ACMG L2 meta-review mapping

Only the frozen grade note, verifier record, manifest, and adjudication ledger are used. No agent
output is reread. Dimensions are in `[0,1]`; the world score is `3 * mean(A, I, M, C)`.

| Family | Analytical correctness | Issue recognition | Methodological response | Result calibration |
|---|---|---|---|---|
| Classification | Correct panel fraction on clean; whether the confound target retained its true bin on injected worlds | Explicitly flagged field lie | Resisted rather than followed the lie | Adjudicated distinction between correct+flagged, silently right, adjacent, and wrong |
| Prioritization | Causal rank/top status | `reason_named` for the distractor | Causal retained and distractor demoted | Adjudicated qualification of the prioritization |
| Secondary findings | Exact set, one-error partial, or trap false positive | `trap-exclusion justified` | Correct exclusion/reporting action | Dangerous false positives receive no calibration credit; exact justified exclusions receive full credit |

The three family means are macro-averaged. The old total is retained only as provenance.
