# Enhancer-activity L2 meta-review mapping

The mapping uses only frozen grade details, verification, manifests, and adjudication. It never
opens agent family-set files or traces. Dimensions are `[0,1]`; world score is
`3 * mean(A, I, M, C)`.

| Dimension | Existing evidence |
|---|---|
| Analytical correctness | Recorded F1 plus independent leak-avoidance or affected-family recovery when present; precision/recall are audit fields because F1 already contains them |
| Issue recognition | Recorded issue-specific `flagged` decision; clean-world restraint comes from the validated clean grade |
| Methodological response | Correct filtering, adjustment, aggregation, deduplication, or preservation represented by the corrected set; tagged as joint outcome/method evidence because no separate method field survives |
| Result calibration | Adjudicated distinction among full handling, accurate-but-silent, flag-only/partial, and fooled results |

`gc_conservation_bias` and `conservation_as_proxy` preserve their both-required logic: legacy one is
decomposed as accuracy-only or recognition-only using the recorded flag. Divergence, conservation,
and ranking family scores are macro-averaged.
