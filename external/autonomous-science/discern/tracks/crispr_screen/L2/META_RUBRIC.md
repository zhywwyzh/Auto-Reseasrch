# CRISPR-screen L2 meta-review mapping

This mapper reads only frozen `graded`, `verify`, manifest, and adjudication records. It does not
read an agent output, score CSV, or trace. The four `[0,1]` dimensions are equally averaged and
rescaled to 0–3.

| Dimension | Existing evidence |
|---|---|
| Analytical correctness | The recorded AUROC tier, recall plus negative-control specificity, affected-gene recovery, artifact avoidance, context overlap, or real-gene preservation; applicable components are averaged |
| Issue recognition | Recorded `flagged=True/False`; clean worlds receive restraint credit when the validated grade shows no false diagnosis |
| Methodological response | Corrected output recovery/preservation/exclusion; this is explicitly tagged as joint outcome/method evidence because no separate method field survives in the frozen record |
| Result calibration | Existing adjudicated distinction among fully handled, silently correct, qualified partial, and fooled/unqualified outputs |

The threshold-sensitivity world preserves its special both-required contract: a legacy score of one
with a flag is recognition-only; a score of one without a flag is accuracy-only. Scoring, calling,
and context family means are macro-averaged.
