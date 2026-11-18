# Release Validation

The public DISCERN artifact was subjected to a final clean-room reproduction test before release.

## Final result

- Clean-room checks passed: **42**
- Clean-room checks failed: **0**
- Result: **PASS**
- Generated paper-facing output files: **272**
- Public candidate changed during clean-room run: **No**
- Identity scan hits: **0**
- Strong credential-pattern hits: **0**

## Reproduction checks

The clean-room run successfully regenerated:

- the L1/L2 world registry
- canonical six-model figure-data products
- eight-model extended figure-data products
- benchmark coverage tables
- L1, L2, and L3 registry tables
- main and appendix figures
- the complete 12/12 extended-figure suite

The canonical figure-data regeneration produced:

- 474 L1 model-task rows
- 612 L2 model-task rows
- 610 L2 component rows
- 131 L3 model-world rows
- 288 level-summary rows
- 4,828 long-form figure-data rows

The extended eight-model regeneration produced:

- 632 L1 rows
- 816 L2 rows
- 175 L3 rows
- 384 level-summary rows
- 8 model-efficiency rows
- 192 model × track × level efficiency rows

## Authority checks

The frozen final-score and row-level authority products remained byte-identical during reproduction.

`verification/authority_index.csv` validated with:

- 1,863 eligible model-world rows
- 1,860 scored rows
- 3 explicitly confounded/excluded rows

No evaluated model or model API was called during clean-room reproduction.

The validation operated only on the reviewer-facing public artifact and its declared Python dependencies.

## Publication transport note

After clean-room validation, one recorded CSV exceeded the Hugging Face plain-Git 10 MiB threshold. The file is therefore stored through Git LFS in the Hub repository. Its working-tree bytes were verified unchanged before and after LFS tracking. This publication-transport change does not alter benchmark science, prompts, recorded outputs, scores, adjudications, or reproduction logic.
