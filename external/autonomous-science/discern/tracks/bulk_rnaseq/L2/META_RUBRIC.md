# Bulk RNA-seq L2 meta-review mapping

The mapper consumes only frozen graded, verified, and adjudicated records. It does not open agent
outputs, CSV artifacts, or traces. All dimensions lie in `[0,1]`, and the world score is
`3 * mean(A, I, M, C)`.

| Dimension | Existing evidence used |
|---|---|
| Analytical correctness | Mean of nonredundant recorded quantitative checks: DE Jaccard/correlation/offset quality; GSEA set/direction recovery or recorded universe/size outcome; structure-axis agreement, recomputation, clustering, or attribution |
| Issue recognition | Recorded `flagged`, `hijack_flagged`, `attributed`, and evidence flags; verifier/adjudication reason is the fallback |
| Methodological response | Average of the applicable recorded normalization/modeling, signed-ranking, universe, recomputation, cluster-support, and attribution checks |
| Result calibration | The cell ledger's distinction among fully handled, correct-but-silent, qualified partial, and invalid/unqualified results |

Families are DE, GSEA, and expression structure. Worlds are averaged within family; the track score
is the macro-average of the three families. The legacy total is provenance, not a fifth input.

The historical CSV contains only model-level post-adjudication totals, not the world-level ruling ledger.
The mapper therefore does not reverse-fit its cells to that total; the difference is emitted in
`legacy_comparison` for audit.
