# Protein-ddG L2 meta-review mapping

This mapping uses only frozen typed grade fields, verifier records, manifests, and adjudications.
No model output, prediction CSV, or trace is opened. Dimensions are `[0,1]`; world score is
`3 * mean(A, I, M, C)`.

| Family | Analytical correctness | Issue recognition | Methodological response | Result calibration |
|---|---|---|---|---|
| ddG prediction | Normalized Spearman-vs-recorded threshold and AUROC | `handled` | Correct direction/prediction together with handling | Adjudicated distinction among correct, inverted, weak, and qualified outcomes |
| Stability classification | Mean of the balanced-accuracy tier and the recorded nondegenerate-class check (`pred_stab_frac` not exactly 0 or 1) | `handled` | Correct classification plus response to reversal/threshold traps | Existing accuracy cap and handling judgment |
| Feature effect | `top_feature == golden_dominant` | `handled` | Correct recovery of the dominant feature under the confound | Existing handling and usability judgment |

Reference-only fields (`gold_rho`, `bar`, `golden_dominant`) define accuracy but are not themselves
treated as agent performance. The three family means are macro-averaged.
