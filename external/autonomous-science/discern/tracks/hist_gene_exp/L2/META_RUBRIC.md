# Histone/gene-expression L2 meta-review mapping

The mapper reads only frozen grades, verifier records, manifests, and adjudications. It does not
reopen agent outputs, per-gene artifacts, or traces. Four `[0,1]` dimensions are averaged equally
and rescaled to 0–3.

| Dimension | Existing evidence |
|---|---|
| Analytical correctness | Average of applicable recorded quantitative checks: signal/gold agreement, effect closeness, broad-domain recovery, joint/sign consistency, confounder reinclusion, or stratified recovery |
| Issue recognition | Recorded `flagged`, `named`, `justified`, or collinearity/covariate evidence; verifier reason is fallback |
| Methodological response | Average of applicable input normalization, broad-mode, window justification, joint modeling, reinclusion, stratification, and robust/adjusted-result evidence |
| Result calibration | The cell ledger's handling ladder, including clean restraint, correct-but-silent, qualified partial, fabrication, and forced-unusable caps |

Quantification, ranking, and regression worlds are averaged within family; the track score is their
macro-average. The post-adjudication CSV remains the legacy-source check, not an extra dimension.
Because the CSV does not preserve its per-world decisions, the mapper does not reverse-fit cells to it;
the old total and the cell-ledger recomputation are both disclosed.
