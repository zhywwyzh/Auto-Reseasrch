"""scrna L1 substrate builder — download a REAL 10x PBMC matrix and carve the clean control.

NON-NEGOTIABLE (ADD_A_TRACK.md §1): the clean substrate is REAL public data; L1 issues are injected as DELTAS on it.
Source = 10x Genomics public PBMC (v1, ~2,700 PBMCs). We keep the **raw/unfiltered** barcodes so real empty droplets
exist (needed for the empty_droplets / ambient_rna QC worlds), then downsample to a tractable size.

Output (tracks/scrna/data/clean/):
  matrix.mtx.gz · barcodes.tsv.gz · features.tsv.gz   (standard 10x trio the agent loads)
  study_metadata.json   (species / chemistry / expected_cells — for metadata_reconciliation worlds)
Also writes tracks/scrna/data/data_dictionary.json.

usage: build_substrate.py [out_dir=tracks/scrna/data]
Requires network + scipy (scanpy NOT required — we use scipy.io). Disk: the raw tarball is ~fewMB-tensMB.
"""
import os, sys, json, urllib.request, tarfile, gzip, io
import numpy as np
import scipy.io as sio
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "data")
RAW_URL = "https://cf.10xgenomics.com/samples/cell-exp/1.1.0/pbmc3k/pbmc3k_raw_gene_bc_matrices.tar.gz"
# Cut real cells at the pbmc3k NATURAL knee (~rank 2700, UMI ~548) so the kept set has a smooth low-UMI tail
# (30k -> ~548) instead of an artificial mid-distribution floor at rank 1500 (UMI 2110). KNEE_GAP skips the
# ambiguous ~150 barcodes just below the knee so sampled empties are clearly empty (UMI < ~180).
N_REAL, N_EMPTY, KNEE_GAP, SEED = 2700, 2700, 150, 0
EXPECTED_CELLS = 3000                                    # advertised 10x loading target (round, != recovered nBC 2700)


def _download(url, dest):
    if os.path.exists(dest): return dest
    print(f"[substrate] downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})  # 10x CDN 403s the default urllib UA
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def _write_10x(out_dir, mat, barcodes, features):
    """mat = genes x cells CSC; features = list of (id, name, type); barcodes = list of str. 10x mtx is genes x cells."""
    os.makedirs(out_dir, exist_ok=True)
    with gzip.open(os.path.join(out_dir, "matrix.mtx.gz"), "wb") as f:
        sio.mmwrite(f, sp.csc_matrix(mat), field="integer")
    with gzip.open(os.path.join(out_dir, "barcodes.tsv.gz"), "wt") as f:
        f.write("\n".join(barcodes) + "\n")
    with gzip.open(os.path.join(out_dir, "features.tsv.gz"), "wt") as f:
        f.write("\n".join(f"{i}\t{n}\t{t}" for i, n, t in features) + "\n")


def build(out=OUT):
    os.makedirs(out, exist_ok=True)
    tar = _download(RAW_URL, os.path.join(out, "pbmc3k_raw.tar.gz"))
    # the tarball holds raw_gene_bc_matrices/hg19/{matrix.mtx,genes.tsv,barcodes.tsv}
    with tarfile.open(tar) as tf:
        base = [n for n in tf.getnames() if n.endswith("matrix.mtx")][0].rsplit("/", 1)[0]
        mat = sio.mmread(tf.extractfile(f"{base}/matrix.mtx")).tocsc()               # genes x barcodes
        genes = [ln.decode().rstrip("\n").split("\t") for ln in tf.extractfile(f"{base}/genes.tsv")]
        barcodes = [ln.decode().strip() for ln in tf.extractfile(f"{base}/barcodes.tsv")]
    features = [(g[0], g[1] if len(g) > 1 else g[0], "Gene Expression") for g in genes]

    counts = np.asarray(mat.sum(axis=0)).ravel()                                     # UMIs per barcode
    nonzero = np.argsort(-counts); nonzero = nonzero[counts[nonzero] > 0]
    real_idx = nonzero[:N_REAL]                                                       # real cells DOWN TO the knee (smooth tail, no artificial floor)
    empty_pool = nonzero[N_REAL + KNEE_GAP:]                                          # skip the ambiguous knee zone -> clearly-empty droplets
    rng = np.random.default_rng(SEED)
    empty_idx = rng.choice(empty_pool, size=min(N_EMPTY, len(empty_pool)), replace=False)
    keep = np.concatenate([real_idx, empty_idx]); rng.shuffle(keep)
    sub = mat[:, keep]
    bc = [barcodes[i] for i in keep]

    clean = os.path.join(out, "clean")
    _write_10x(clean, sub, bc, features)
    json.dump({"species": "human", "genome": "hg19", "chemistry": "10x 3' v1",
               "expected_cells": EXPECTED_CELLS, "assay": "scRNA-seq", "tissue": "PBMC"},
              open(os.path.join(clean, "study_metadata.json"), "w"), indent=1)
    json.dump({"matrix.mtx.gz": "genes x barcodes sparse counts (MatrixMarket)",
               "barcodes.tsv.gz": "one cell barcode per line",
               "features.tsv.gz": "gene_id<TAB>gene_name<TAB>feature_type (feature_type MUST be all 'Gene Expression')",
               "study_metadata.json": "declared species/genome/chemistry/expected_cells"},
              open(os.path.join(out, "data_dictionary.json"), "w"), indent=1)
    print(f"[substrate] wrote clean 10x matrix -> {clean}  ({sub.shape[0]} genes x {sub.shape[1]} barcodes; "
          f"{N_REAL} real + {len(empty_idx)} empty)")
    return clean


if __name__ == "__main__":
    build()
