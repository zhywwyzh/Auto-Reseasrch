# Runtime references downloaded from their owners

Do not bundle the CADD subset or ESM checkpoints in the public upload. Obtain
them outside the sandbox before evaluation; the execution sandbox stays offline.
Full construction datasets remain link-only.

## CADD v1.7, GRCh38

Review https://cadd.bihealth.org/download. The provider permits non-commercial
applications; commercial use requires a separate license. This repository does
not grant additional rights.

With `pysam` installed, run in a fresh output directory:

```bash
python fetch_external_runtime.py cadd --accept-cadd-terms \
  --output tracks/clinvar_acmg/L2/l2/resources
```

Only CADD files are created; ClinVar and gnomAD files are not changed. The command
refuses to overwrite existing CADD files. It retrieves the panel intervals from
the official versioned file using tabix range requests, creates a local index,
and verifies the SHA-256 of the decompressed text against the frozen benchmark.
On 2026-09-25 all 2,211,126 reconstructed rows matched. Compression bytes may
differ between library versions; the decompressed content must match exactly.

## ESM-2

```bash
python fetch_external_runtime.py esm --output resources/torch/hub/checkpoints
```

The command downloads the 150M and 650M model weights and their contact-regression
companions from Meta's official endpoints. It verifies each file against the
frozen SHA-256 in `verification/runtime_files.csv`. All four files were downloaded
and matched on 2026-09-25. Model cards declare MIT; see `THIRD_PARTY_NOTICES.md`.
Downloads are not a change to model weights or task settings.

## Calorimetry is not yet a tested reconstruction path

The NIST source records are identified, but simply rerunning the shipped builders
is not an installation procedure: they can overwrite manifests and gold files,
and the L3 code depends on intermediate shadow-analysis assets not included in
the release. Do not claim the prepared calorimetry tasks are reproducible from
upstream downloads alone until that route passes comparison to the frozen inputs.
Prepared inputs are supplied separately; the reconstruction route is unchanged.
