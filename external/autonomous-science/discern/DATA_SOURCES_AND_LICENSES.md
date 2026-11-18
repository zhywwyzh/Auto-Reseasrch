# Data Sources, Redistribution, and Third-Party Terms

DISCERN is released as a reproducibility artifact package. This repository does
not attempt to relicense third-party datasets, publications, databases, or
software.

Upstream licenses and terms remain controlling. Where redistribution status is
unclear, source payloads are intentionally omitted and the release instead
provides provenance, citations, reconstruction code, and—where available—
checksums.

## Local runtime-package update

The working copy now stages prepared benchmark inputs and required runtime
references separately from construction-only source collections. The
track-by-track policies below describe the original published snapshot, not an
approval to redistribute newly staged files. Consult `RUNTIME_DATA.md` and
`verification/runtime_files.csv` for the staged payload. `SOURCE_DATA_POLICY.tsv`
contains source links and flags the pending redistribution review. Derived inputs
are not automatically exempt from upstream terms.

`SOURCE_DATA_POLICY.tsv` provides a machine-readable summary of the decisions
below. `SOURCE_DATA_CHECKSUMS.tsv` records checksums for intentionally withheld
source payloads for which a frozen local copy was available during release
construction.

## Release modes

This release distinguishes four forms of source support:

1. **Source data itself** — an upstream payload redistributed only when doing so
   is needed and the applicable terms are sufficiently clear.
2. **Benchmark-derived artifacts** — frozen benchmark-generated transformations,
   gold standards, manifests, synthetic/counterfactual worlds, and evaluation
   artifacts that do not serve as a substitute copy of the complete upstream
   source dataset.
3. **Reconstruction/preparation software** — scripts that obtain or transform
   upstream material.
4. **Source references** — URLs, accession identifiers, citations, provenance
   metadata, and checksums.

A source being omitted from this repository does **not** mean that it is
unavailable. It means the reviewer should obtain it from the official provider
under that provider's current terms.

## Track-by-track policy

### Bulk RNA-seq

**Upstream sources:** GEO series GSE152418 and GENCODE v29 annotation.

The release retains benchmark-derived gold artifacts, metadata, manifests,
builders, model artifacts, grades, and verification records. It does not
redistribute a separate copy of the raw study count matrix or a full upstream
GENCODE payload.

NCBI's GEO disclaimer states that NCBI places no restriction on use or
distribution of GEO data, while noting that submitters may retain intellectual
property rights in submitted material. GENCODE describes its project data as
open access.

Official sources:

- https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE152418
- https://www.ncbi.nlm.nih.gov/geo/info/disclaimer.html
- https://www.gencodegenes.org/pages/data_access.html

### Counterfactual GWAS

**Upstream sources:** GWAS Catalog study GCST003143, PredictDB, GTEx, and
MetaXcan.

The release does not redistribute the source GWAS summary-statistics payload,
GTEx protected/raw donor-level data, or external PredictDB model databases.
Preparation/build scripts and frozen benchmark-derived artifacts are included.
The vendored MetaXcan software subtree is retained together with its upstream
license.

The GWAS Catalog states that most deposited summary-statistic datasets are
available under CC0 or EMBL-EBI standard terms, with exceptions; the individual
study's Usage License remains controlling. PredictDB states CC BY-SA 4.0 for
the work and MIT for source code. GTEx explicitly separates portal open-access
files from protected raw sequencing and full donor metadata.

Official sources:

- https://www.ebi.ac.uk/gwas/downloads/summary-statistics
- https://predictdb.org/
- https://gtexportal.org/home/downloads/adult-gtex/overview

### ClinVar / ACMG

**Upstream sources:** ClinVar, gnomAD v4.1 summary data, and CADD scores.

The release ships builders and frozen benchmark artifacts rather than bulk
copies of these upstream resources.

ClinVar requests attribution when its data are copied or distributed. The
gnomAD public summary-data distribution describes those summary data as
released for the wider scientific community without restriction on use and
also links its current terms. CADD states that its scores are freely available
for non-commercial applications and that commercial applications require
contact/licensing.

Official sources:

- https://www.ncbi.nlm.nih.gov/clinvar/docs/maintenance_use/
- https://registry.opendata.aws/broad-gnomad/
- https://cadd.gs.washington.edu/
- https://cadd.bihealth.org/download
- https://krishna.gs.washington.edu/download/CADD/v1.7/GRCh38/whole_genome_SNVs.tsv.gz

The packaged CADD resource builder selects scores from the v1.7 GRCh38
whole-genome SNV release above. Its source is identified; permission to rehost
the selected scores remains pending rather than being inferred from download access.

### CRISPR screen

**Upstream sources:** Hart Lab BAGEL/TKOv3-related resources, including the
CEGv2 and NEGv1 reference sets used by the frozen benchmark.

The public release retains benchmark-derived gold tables and builders rather
than packaging a separate upstream raw-screen archive. The Hart Lab BAGEL
repository identifies its software distribution as MIT-licensed.

Official source:

- https://github.com/hart-lab/bagel

### Enhancer activity

**Upstream source:** Klein et al., *Functional characterization of enhancer
evolution in the primate lineage*, Genome Biology 19, 99 (2018), including its
supplementary processed data.

The release includes frozen benchmark-derived conservation/divergence/ranking
and validation artifacts plus builders. It does not need to duplicate the
complete upstream source workbook.

The published article is CC BY 4.0 and states that the CC0 public-domain
dedication applies to data made available in the article unless otherwise
stated.

Official publication:

- https://doi.org/10.1186/s13059-018-1473-6

### Histone / gene expression

**Upstream sources:** released ENCODE K562 epigenomic data and GENCODE v29.

The large source BAM/BigWig/GTF payloads are not bundled. Source accessions,
builders, benchmark-derived gold artifacts, and recorded evaluation artifacts
are retained.

ENCODE states that released project data are available for unrestricted use.
GENCODE project data are open access.

Official sources:

- https://www.encodeproject.org/about/data-use-policy/
- https://www.gencodegenes.org/pages/data_access.html

### Protein stability / ddG

**Upstream sources:** Tsuboyama et al. mega-scale protein-stability datasets
( Zenodo record 7992926 ) and structures from the Protein Data Bank.

The release does not redistribute the large Tsuboyama source tables. The
Zenodo record is publicly downloadable, but an explicit license value was not
verified on the record during release preparation, so the conservative policy
is to provide the DOI/source reference and reconstruction logic instead.

PDB archive data files are available under CC0 1.0 and can be obtained directly
from the wwPDB/RCSB archive.

Official sources:

- https://doi.org/10.5281/zenodo.7992926
- https://www.wwpdb.org/about/usage-policies

Runtime protein models are Meta ESM-2 `esm2_t33_650M_UR50D` and
`esm2_t30_150M_UR50D`, with contact-regression companion weights. Official Meta
model cards label both models MIT licensed:

- https://huggingface.co/facebook/esm2_t33_650M_UR50D
- https://huggingface.co/facebook/esm2_t30_150M_UR50D
- https://github.com/facebookresearch/esm
- https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t33_650M_UR50D.pt
- https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t30_150M_UR50D.pt

The upstream loader obtains companion files from:

- https://dl.fbaipublicfiles.com/fair-esm/regression/esm2_t33_650M_UR50D-contact-regression.pt
- https://dl.fbaipublicfiles.com/fair-esm/regression/esm2_t30_150M_UR50D-contact-regression.pt

See THIRD_PARTY_NOTICES.md for the remaining file-level checks; these models are
not licensed under the separate ESM Atlas data license.

### Single-cell RNA-seq

**Upstream source:** 10x Genomics "3k PBMCs from a Healthy Donor", Cell Ranger
1.1.0.

The source matrices are not duplicated in this release. The preparation code
and frozen benchmark artifacts are retained. The exact 10x PBMC3k dataset page
states that the dataset is licensed under CC BY 4.0.

Official source:

- https://www.10xgenomics.com/datasets/3-k-pbm-cs-from-a-healthy-donor-1-standard-1-1-0

### Calorimetry

**Upstream source:** NIST ThermoML records and their cited journal sources,
including Journal of Chemical Thermodynamics material used for the frozen
calorimetry substrate.

Source mapping supplied by the project owner and reviewed on 2026-09-25:

- L1 / base heat-capacity data: Lang, B. E., Boerio-Goates, J., and Woodfield,
  B. F. (2006), *Design and construction of an adiabatic calorimeter for samples
  of less than 1 cm3 in the temperature range T=15 K to T=350 K*, Journal of
  Chemical Thermodynamics 38, 1655–1663. Copper, alumina, and benzoic acid
  measurements distributed through the NIST/TRC ThermoML Archive:
  https://trc.nist.gov/ThermoML/10.1016/j.jct.2006.03.016.html
- Additional L2 heptane source: https://trc.nist.gov/ThermoML/10.1021/je100658y.html
- L3 nano-Cu literature: https://doi.org/10.1103/PhysRevB.36.7888 and
  https://doi.org/10.1351/PAC-CON-08-09-15

The literature references ground the constructed L3 conditions; they must not be
read as claiming that every constructed task value was directly measured in those
publications. Citations alone do not confer redistribution permission.

DISCERN reformats source measurements into task tables and applies controlled
changes specified by its world builders. These changes and constructed
counterfactual conditions are DISCERN's, not claims made by the source authors.
Credit for the underlying measurements remains with the cited researchers and
NIST/TRC. Original third-party terms remain applicable rather than being replaced
by DISCERN's MIT code license.

The local ThermoML-derived source payload
`tracks/calorimetry/calorimetry_raw.json` is intentionally **not
redistributed**. Its frozen SHA-256 checksum is recorded in
`SOURCE_DATA_CHECKSUMS.tsv`.

The release retains world builders, manifests, gold standards, benchmark
transformations, probes, outputs, grades, and verifier/adjudication artifacts.

NIST states that files in the ThermoML Archive are made available through
cooperation with participating journals and **with permission of the journal
publishers**. Because that statement does not establish a blanket downstream
redistribution license for a repackaged source payload, DISCERN uses the
conservative citation/reconstruction-only policy.

Official sources:

- https://www.nist.gov/mml/acmd/trc/thermoml/thermoml-archive
- https://www.nist.gov/mml/acmd/trc/thermoml

### Nuclear decay

**Upstream source:** Goddard, *Multi year radiation measurement data*, version 1
(2020), DOI 10.17632/tfcc3jk869.1, including NaI Co-60 and Mn-54 measurements.
The project owner identified this source; the dataset name and Co-60 filename
match the L1 builder. The dataset page explicitly states **CC BY 4.0**.

- Dataset: https://data.mendeley.com/datasets/tfcc3jk869/1
- Article: https://doi.org/10.1016/j.dib.2020.105828
- License: https://creativecommons.org/licenses/by/4.0/

Attribute Goddard and the dataset DOI for derived measurements, retain the license
link, and identify DISCERN's selection, normalization, aggregation, and controlled
modifications as benchmark transformations, not original observations. This source
check does not claim a byte-for-byte reconstruction of the prepared inputs.

The original large measurement/spectral payloads are not redistributed.
Frozen benchmark-derived worlds, source-provenance metadata, gold artifacts,
probe records, outputs, grades, and builders are included.

The auxiliary detector-efficiency values are drawn from a separate source:

- Akar Tarım, U., Gürler, O., and Yalçın, S. (2018), *A Quick Method to Calculate
  NaI(Tl) Detector Efficiency Depending on Gamma ray Energy and Source-to-detector
  Distance*, Celal Bayar University Journal of Science 14(2), 195–199.
  https://doi.org/10.18466/cbayarfbe.396704

DISCERN uses selected numerical efficiency values to construct its near-field
detector-response check. Its imposed geometry drift and task conditions are
benchmark modifications, not observations attributed to this paper. Article text
and figures are not bundled as part of this attribution update.

That publication is a supporting scientific reference; it should not be
interpreted as establishing redistribution rights for the separate raw
measurement substrate.

## Important distinction: source data vs. recorded benchmark artifacts

Model outputs, execution traces, deterministic grades, verifier records,
adjudication ledgers, benchmark manifests, synthetic/counterfactual worlds,
and benchmark-generated gold artifacts are reproducibility records of DISCERN.
They are retained even when a separate third-party source payload is omitted.

This policy intentionally avoids treating the existence of a source file on
the development server as permission to redistribute that source file.

## No blanket third-party relicensing

No project-level license added elsewhere in this repository should be
interpreted as changing the license or terms of third-party material.

When rebuilding a track, users are responsible for complying with the current
terms of the relevant upstream source.
