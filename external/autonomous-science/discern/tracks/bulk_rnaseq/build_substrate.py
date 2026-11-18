"""bulk_rnaseq L1 substrate builder — carve the REAL clean bulk RNA-seq count matrix + sample metadata.

NON-NEGOTIABLE (ADD_A_TRACK.md §1): the clean substrate is REAL public data; L1 issues are injected as DELTAS
on it (never synthesize the clean control — a synthetic tell becomes a false "defect").

SOURCE (real, public, GEO): Arunachalam et al. 2020, "Systems biological assessment of immunity to mild versus
severe COVID-19 infection in humans", Science 369:1210 (PMID 32788292). Bulk RNA-seq of human PBMC — a raw
gene x sample read-count matrix with per-sample metadata carrying BOTH a clear condition (disease state:
COVID-19 / Convalescent / Healthy) AND sex (gender: M/F) — the sex column is needed for the XIST/RPS4Y
sample-identity-swap world. 34 samples (16 M, 18 F), 60,683 Ensembl genes.
  - GEO series: GSE152418  (ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE152418)
  - raw counts:  suppl/GSE152418_p20047_Study1_RawCounts.txt.gz  (ENSEMBLID x 34 samples, raw integer counts)
  - metadata:    matrix/GSE152418_series_matrix.txt.gz  (per-sample gender + disease state + severity)

Chosen over the classic airway/dex screen (GSE52778): that set lacks a balanced two-sex design, and the XIST/
RPS4Y sample-swap world REQUIRES both sexes present with clean sex-marker separation. This PBMC set has perfect
sex-marker separation (F: XIST+ / RPS4Y1~0; M: RPS4Y1/DDX3Y+ / XIST~0) — a swapped label is unambiguously
detectable, and it is whole-blood-derived (PBMC), so a globin / rRNA-depletion-failure contamination world is
domain-realistic. Gene IDs are kept as real Ensembl IDs.

A read-only gene annotation (real, from Ensembl BioMart) is mounted as a RESOURCE (gene_id -> symbol,
chromosome, biotype) so the agent can map ENSG ids to sex markers / globin / rRNA / biotype — the RNA-seq analog
of a mounted genome/GTF (a resource, not an answer). Ensembl release = current www.ensembl.org (BioMart).

Clean slices written to data/clean/:
  counts_clean.tsv.gz     gene_id + 34 sample columns (raw integer counts) — REAL, byte-for-byte from GEO
  sample_metadata.tsv     sample_id, condition, sex, organism, genome_build, rin, pct_intronic, three_prime_bias
                          (condition/sex from GEO; organism/build = provenance labels; the three QC summary
                          metrics are realistic clean-range values added here — every world shares this schema,
                          so their presence is not a per-world tell; only the degradation/gDNA worlds push
                          specific samples out of range.)
data/resources/gene_annotation.tsv  (gene_id, symbol, chromosome, biotype) — the mounted read-only reference.
data/data_dictionary.json + data/study_metadata.json (generic; identical across worlds — no leak).

usage: build_substrate.py            (requires network the FIRST time to fetch the raw files; then offline)
"""
import os, sys, json, gzip, urllib.request, urllib.parse
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RAW = os.path.join(DATA, "raw"); RES = os.path.join(DATA, "resources"); CLEAN = os.path.join(DATA, "clean")

GEO = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE152nnn/GSE152418"
COUNTS_RAW = os.path.join(RAW, "GSE152418_p20047_Study1_RawCounts.txt.gz")
MATRIX_RAW = os.path.join(RAW, "GSE152418_series_matrix.txt.gz")
ANNOT_RAW = os.path.join(RAW, "ensembl_gene_annotation.tsv")

BIOMART_XML = ('<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE Query>'
    '<Query virtualSchemaName="default" formatter="TSV" header="0" uniqueRows="1" count="" '
    'datasetConfigVersion="0.6"><Dataset name="hsapiens_gene_ensembl" interface="default">'
    '<Attribute name="ensembl_gene_id"/><Attribute name="external_gene_name"/>'
    '<Attribute name="chromosome_name"/><Attribute name="gene_biotype"/></Dataset></Query>')


def _fetch(dest, url):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"[substrate] downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def _fetch_annotation():
    if os.path.exists(ANNOT_RAW) and os.path.getsize(ANNOT_RAW) > 0:
        return ANNOT_RAW
    url = "https://www.ensembl.org/biomart/martservice?" + urllib.parse.urlencode({"query": BIOMART_XML})
    return _fetch(ANNOT_RAW, url)


def _parse_metadata():
    """Pull per-sample title / gender / disease-state from the GEO series matrix."""
    titles = chars = None; char_rows = []
    with gzip.open(MATRIX_RAW, "rt") as f:
        for line in f:
            if line.startswith("!Sample_title"):
                titles = [x.strip('"') for x in line.rstrip("\n").split("\t")[1:]]
            elif line.startswith("!Sample_characteristics_ch1"):
                char_rows.append([x.strip('"') for x in line.rstrip("\n").split("\t")[1:]])
    # char_rows order in this series: days_post_symptom_onset, gender, disease state, severity, geo-loc, cell type
    def val(cell):
        return cell.split(":", 1)[1].strip() if ":" in cell else cell.strip()
    def find(prefix):
        for row in char_rows:
            if row and row[0].lower().startswith(prefix):
                return [val(c) for c in row]
        raise SystemExit(f"[substrate] characteristic '{prefix}' not found in series matrix")
    gender = find("gender")
    disease = find("disease state")
    return pd.DataFrame({"sample_id": titles, "condition": disease, "sex": gender})


def build():
    _fetch(COUNTS_RAW, f"{GEO}/suppl/GSE152418_p20047_Study1_RawCounts.txt.gz")
    _fetch(MATRIX_RAW, f"{GEO}/matrix/GSE152418_series_matrix.txt.gz")
    _fetch_annotation()
    os.makedirs(CLEAN, exist_ok=True); os.makedirs(RES, exist_ok=True)

    # ---- clean count matrix (REAL, unmodified) --------------------------------------------------------------
    counts = pd.read_csv(COUNTS_RAW, sep="\t")
    counts = counts.rename(columns={counts.columns[0]: "gene_id"})
    counts.to_csv(os.path.join(CLEAN, "counts_clean.tsv.gz"), sep="\t", index=False, compression="gzip")
    sample_cols = list(counts.columns[1:])
    print(f"[substrate] counts_clean: {counts.shape[0]} genes x {len(sample_cols)} samples")

    # ---- sample metadata (condition + sex REAL; QC summary metrics realistic clean-range) -------------------
    meta = _parse_metadata()
    meta = meta.set_index("sample_id").loc[sample_cols].reset_index()          # align to count-matrix column order
    assert list(meta["sample_id"]) == sample_cols, "metadata / counts sample mismatch"
    rng = np.random.default_rng(20200811)                                       # deterministic clean QC values
    n = len(meta)
    meta["organism"] = "Homo sapiens"
    meta["genome_build"] = "GRCh38 (Ensembl)"
    meta["rin"] = np.round(rng.uniform(7.6, 9.4, n), 1)                         # RNA integrity (clean: high)
    meta["pct_intronic"] = np.round(rng.uniform(0.09, 0.17, n), 3)             # intronic-read fraction (clean: low, gDNA proxy)
    meta["three_prime_bias"] = np.round(rng.uniform(0.92, 1.25, n), 2)         # gene-body 3'/5' coverage ratio (clean: ~1)
    meta = meta[["sample_id", "condition", "sex", "organism", "genome_build",
                 "rin", "pct_intronic", "three_prime_bias"]]
    meta.to_csv(os.path.join(CLEAN, "sample_metadata.tsv"), sep="\t", index=False)
    print(f"[substrate] sample_metadata: {n} samples ({(meta.sex=='M').sum()} M / {(meta.sex=='F').sum()} F; "
          f"conditions {dict(meta.condition.value_counts())})")

    # ---- gene annotation resource (REAL, Ensembl BioMart), restricted to matrix genes ----------------------
    an = pd.read_csv(ANNOT_RAW, sep="\t", names=["gene_id", "symbol", "chromosome", "biotype"], dtype=str)
    an = an.drop_duplicates("gene_id")
    an = an[an["gene_id"].isin(set(counts["gene_id"]))].reset_index(drop=True)
    an.to_csv(os.path.join(RES, "gene_annotation.tsv"), sep="\t", index=False)
    print(f"[substrate] gene_annotation: {an.shape[0]} genes annotated "
          f"({100*an.shape[0]/counts.shape[0]:.1f}% of matrix); "
          f"rRNA/Mt_rRNA={an.biotype.isin(['rRNA','Mt_rRNA']).sum()}")

    # ---- generic docs (issue-NEUTRAL: no organism/build/condition claims -> cannot contradict a corrupted world) ----
    json.dump({
        "counts_matrix": "raw integer read counts, one row per gene (gene_id = Ensembl gene id), one column per "
                         "sample. Un-normalized, unfiltered gene-level counts (the standard raw input to a "
                         "differential-expression / pathway workflow).",
        "gene_id": "Ensembl gene identifier (namespace indicates the organism/annotation).",
        "sample_metadata_file": "a companion table 'sample_metadata.tsv' describes each sample: experimental "
                                "condition, annotated sex, dataset provenance fields, and per-sample "
                                "sequencing/QC summary metrics.",
        "gene_annotation_resource": "a read-only reference table maps each gene_id to its symbol, chromosome, "
                                    "and biotype (see the path given in the task).",
        "_note": "This is the raw count matrix BEFORE low-count filtering and normalization.",
    }, open(os.path.join(DATA, "data_dictionary.json"), "w"), indent=1)

    json.dump({
        "assay": "bulk RNA-seq (gene-level read counts), human PBMC",
        "input_stage": "raw count matrix + sample metadata (pre-filtering, pre-normalization)",
        "downstream": "low-count filtering, normalization, differential expression, pathway/GSEA",
        "provenance_note": "per-sample condition and sex, plus the dataset provenance fields (organism, genome "
                           "build), are recorded in the accompanying sample metadata table.",
        "source": "GEO GSE152418 (Arunachalam et al., Science 2020, PMID 32788292); gene annotation from "
                  "Ensembl BioMart.",
    }, open(os.path.join(DATA, "study_metadata.json"), "w"), indent=1)
    print(f"[substrate] clean substrate + resources + docs ready under {DATA}")


if __name__ == "__main__":
    build()
