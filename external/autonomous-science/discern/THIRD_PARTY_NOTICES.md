# Licensing scope and third-party attribution

DISCERN-authored code and documentation are MIT licensed. The dataset card uses
`license: other` because this repository contains a mixture of licenses; it does
not claim that all bundled data are MIT licensed.

## Confirmed terms and attribution

- MetaXcan: upstream MIT license retained at `tracks/cf_gwas/L2/MetaXcan/LICENSE`.
- Nuclear-decay measurement source: Goddard, *Multi year radiation measurement
  data*, version 1, DOI 10.17632/tfcc3jk869.1. The dataset page explicitly states
  CC BY 4.0. Attribute the source, link the license, and identify benchmark
  transformations and controlled changes. This does not license independently
  sourced detector-calibration material.
  Sources: https://data.mendeley.com/datasets/tfcc3jk869/1 and
  https://creativecommons.org/licenses/by/4.0/
- ESM: official Meta model cards explicitly label both the 650M and 150M ESM-2
  models MIT licensed. This resolves the previous lack of model-specific license
  evidence; the ESM Atlas CC BY 4.0 license is unrelated. Preserve Meta's copyright
  and MIT notice when packaging covered files. Exact original-format checkpoint
  correspondence and the separate contact-regression files remain packaging checks.
  Sources: https://huggingface.co/facebook/esm2_t33_650M_UR50D and
  https://huggingface.co/facebook/esm2_t30_150M_UR50D
  License: https://github.com/facebookresearch/esm/blob/main/LICENSE
- CADD: the official download page permits non-commercial applications and directs
  commercial users to obtain a license. This is not a verified blanket permission
  for us to redistribute a subset under MIT.
  Source: https://cadd.gs.washington.edu/download
- ThermoML: NIST states archive files are available with journal publishers'
  permission. That statement alone does not establish downstream redistribution
  rights for every prepared calorimetry input.
  Source: https://www.nist.gov/mml/acmd/trc/thermoml

## Source update verified 2026-09-25

The source links supplied by the project owner match the nuclear L1 builder's
dataset name and Co-60 series, the calorimetry builders' cited records, and the
CADD resource builder's v1.7 GRCh38 URL. This is provenance verification, not a
byte-for-byte reconstruction of every prepared input. Full upstream construction
collections remain link-only.

## Remaining checks

The project owner has directed publication of the attributed prepared physics
inputs. This decision does not establish independently verified redistribution
permission or change the source terms. Full construction archives remain link-only;
CADD and ESM references are fetched directly from their owners.

- [x] **Identify the nuclear-decay measurement source and its license.**
  Goddard's dataset is CC BY 4.0; the accompanying article is
  https://doi.org/10.1016/j.dib.2020.105828. Retain attribution and modification
  notices for derived inputs. The auxiliary detector-efficiency reference has
  its own provenance and is not covered by this dataset license.
- [ ] **Pending: clarify calorimetry redistribution terms.**
  The Lang/Boerio-Goates/Woodfield ThermoML record, L2 heptane record, and L3
  nano-Cu literature are now identified in DATA_SOURCES_AND_LICENSES.md.
  Source-specific redistribution terms still need clarification.
- [x] **Provide a tested alternative to CADD-subset redistribution.**
  Direct rehosting remains unapproved. A tested alternative is now available:
  `fetch_external_runtime.py cadd` reconstructs all 2,211,126 frozen rows with an
  exact decompressed SHA-256 match. Exclude the subset and index from upload and
  use this route under the upstream terms (see EXTERNAL_RUNTIME.md).
- [x] **Provide a tested ESM upstream-download alternative.**
  `fetch_external_runtime.py esm` downloads both original-format model files and
  both contact-regression companions; all four match frozen SHA-256 checksums.
  Exclude these files from upload and link Meta's original distribution instead.

Original attribution and source links for all tracks are in
DATA_SOURCES_AND_LICENSES.md. This document does not assert that every source has
completed file-level license review or that public access itself grants rights.
