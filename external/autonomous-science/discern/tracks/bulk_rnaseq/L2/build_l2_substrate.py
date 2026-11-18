"""bulk_rnaseq L2 — substrate builder (run ONCE, before the reference solver).

Produces the analysis-ready substrate the three L2 sub-tasks run on (from the REAL GSE152418
PBMC cohort — COVID-19 vs Healthy, Arunachalam/Wherry-adjacent Emory cohort — already QC'd at L1):

  data/processed/counts_expressed.tsv.gz  — raw counts filtered to expressed genes
                                            (>=10 counts in >=5 samples), Ensembl IDs
  data/processed/gene_meta.tsv            — gene_id, symbol, biotype, exon_union_bp
                                            (exon-union length parsed from GENCODE v29 —
                                            needed by the gene_length_bias world / GOseq-style null)
  data/processed/l2_provenance.json       — cohort definition + filter provenance

Cohort: DE sub-tasks use COVID-19 (16) vs Healthy (17); the single Convalescent sample is
EXCLUDED from DE and included only in the structure sub-task's full-cohort worlds.

usage: /workspace/home/miniconda3/envs/bulkl2/bin/python build_l2_substrate.py
"""
import gzip, json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

TRACK = Path(__file__).resolve().parents[1]
PROC = TRACK / "data" / "processed"
GTF = Path("/workspace/discern-benchmark/tracks/hist_gene_exp/data/raw/reference/gencode.v29.gtf.gz")

MIN_COUNT, MIN_SAMPLES = 10, 5


def exon_union_lengths():
    """gene_id (version-stripped) -> exon-union bp from GENCODE v29."""
    exons = defaultdict(list)
    with gzip.open(GTF, "rt") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            f = line.split("\t")
            if f[2] != "exon":
                continue
            gid = f[8].split('gene_id "')[1].split('"')[0].split(".")[0]
            exons[gid].append((int(f[3]), int(f[4])))
    out = {}
    for gid, iv in exons.items():
        iv.sort()
        tot, cs, ce = 0, iv[0][0], iv[0][1]
        for s, e in iv[1:]:
            if s <= ce + 1:
                ce = max(ce, e)
            else:
                tot += ce - cs + 1
                cs, ce = s, e
        out[gid] = tot + (ce - cs + 1)
    return out


def main():
    PROC.mkdir(parents=True, exist_ok=True)
    counts = pd.read_csv(TRACK / "data" / "clean" / "counts_clean.tsv.gz", sep="\t", index_col=0)
    meta = pd.read_csv(TRACK / "data" / "clean" / "sample_metadata.tsv", sep="\t")

    expressed = (counts >= MIN_COUNT).sum(axis=1) >= MIN_SAMPLES
    ce = counts[expressed]
    print(f"[filter] {expressed.sum()}/{len(counts)} genes expressed (>= {MIN_COUNT} counts in >= {MIN_SAMPLES} samples)")

    print("[gtf] parsing GENCODE v29 exon-union lengths ...")
    lens = exon_union_lengths()
    ann = pd.read_csv(TRACK / "data" / "resources" / "gene_annotation.tsv", sep="\t")
    ann = ann.set_index("gene_id")
    gm = pd.DataFrame(index=ce.index)
    gm["symbol"] = ann.reindex(gm.index).symbol
    gm["biotype"] = ann.reindex(gm.index).biotype
    gm["exon_union_bp"] = [lens.get(g, np.nan) for g in gm.index]
    n_len = gm.exon_union_bp.notna().sum()
    print(f"[gene_meta] symbols for {gm.symbol.notna().sum()}/{len(gm)}; exon-union length for {n_len}/{len(gm)}")

    ce.to_csv(PROC / "counts_expressed.tsv.gz", sep="\t", compression="gzip")
    gm.reset_index().rename(columns={"index": "gene_id"}).to_csv(PROC / "gene_meta.tsv", sep="\t", index=False)

    de_samples = meta[meta.condition.isin(["COVID-19", "Healthy"])].sample_id.tolist()
    json.dump({
        "source": "GSE152418 raw counts (real, L1-shared substrate); filter >=10 counts in >=5 samples",
        "n_genes_expressed": int(expressed.sum()),
        "de_cohort": {"contrast": "COVID-19 vs Healthy", "n": len(de_samples), "samples": de_samples,
                      "excluded": meta[meta.condition == "Convalescent"].sample_id.tolist()},
        "structure_cohort": "all 34 samples",
        "gene_lengths": "GENCODE v29 exon-union bp (version-stripped Ensembl IDs)",
        "covariates_in_metadata": ["sex", "rin", "pct_intronic", "three_prime_bias"],
    }, open(PROC / "l2_provenance.json", "w"), indent=1)
    print(f"[out] {PROC}/counts_expressed.tsv.gz + gene_meta.tsv + l2_provenance.json")


if __name__ == "__main__":
    main()
