"""scRNA L2 CLEAN GROUND TRUTH — run the standard annotation pipeline end-to-end on the clean pbmc3k (the L1
clean world = 2,700 real cells) to produce the reference cell-type map + marker table that L2 grades against and
L3 hands forward. Reproducible: seeded PCA/neighbors/leiden. Human-curated cluster->cell-type mapping (canonical
PBMC markers), verified against per-cluster discriminating-marker means (recorded in ground_truth.json).

Deps (installed in the run venv .venv_bench, also needed in the L2 sandbox): scanpy, leidenalg, igraph, anndata.
Output: tracks/scrna/L2/ground_truth/{cell_labels.csv, cluster_marker_means.csv, cluster_top_markers.csv, ground_truth.json}.
Usage: python tracks/scrna/L2/build_ground_truth.py
"""
import scanpy as sc, numpy as np, pandas as pd, json, tarfile, tempfile, os, glob, warnings
warnings.filterwarnings("ignore"); sc.settings.verbosity = 0

HERE = os.path.dirname(os.path.abspath(__file__))
CLEAN_WORLD = os.path.join(os.path.dirname(HERE), "L1/results/scrna_l1_run/data/cell000")  # L1 clean world (2700 real cells)
OUT = os.path.join(HERE, "ground_truth"); os.makedirs(OUT, exist_ok=True)
RES = 1.0

# Human-curated cluster -> cell type (res=1.0, seed 0), from canonical PBMC markers + verified marker means.
CURATED = {"0": "CD4 T", "1": "CD4 T", "2": "FCGR3A Mono", "3": "CD8 T", "4": "CD14 Mono",
           "5": "Platelet", "6": "B", "7": "DC", "8": "NK", "9": "NK"}
LOW_CONF = {"9": "small (9 cells) CD3D/NKG7/CD79A-mixed -> likely NK / doublet-like; low confidence"}
CANON_MARKERS = {"CD4 T": ["IL7R", "CD3D", "CCR7"], "CD8 T": ["CD8A", "CD8B", "CD3D"], "B": ["MS4A1", "CD79A"],
                 "NK": ["GNLY", "NKG7"], "CD14 Mono": ["CD14", "LYZ"], "FCGR3A Mono": ["FCGR3A", "MS4A7"],
                 "DC": ["FCER1A", "CST3"], "Platelet": ["PPBP", "PF4"]}


def load_clean():
    tf = [f for f in os.listdir(CLEAN_WORLD) if f.endswith(".tar.gz")][0]
    tmp = tempfile.mkdtemp()
    with tarfile.open(os.path.join(CLEAN_WORLD, tf)) as t:
        t.extractall(tmp)
    mdir = os.path.dirname(glob.glob(tmp + "/**/matrix.mtx.gz", recursive=True)[0])
    ad = sc.read_10x_mtx(mdir); ad.var_names_make_unique()
    return ad


def main():
    ad = load_clean()
    sc.pp.filter_genes(ad, min_cells=3)
    ad.layers["counts"] = ad.X.copy()
    sc.pp.normalize_total(ad, target_sum=1e4); sc.pp.log1p(ad); ad.raw = ad
    sc.pp.highly_variable_genes(ad, n_top_genes=2000)
    adh = ad[:, ad.var.highly_variable].copy(); sc.pp.scale(adh, max_value=10)
    sc.tl.pca(adh, n_comps=50, random_state=0)
    sc.pp.neighbors(adh, n_neighbors=10, n_pcs=40, random_state=0)
    sc.tl.leiden(adh, resolution=RES, random_state=0, flavor="igraph", n_iterations=2, directed=False)
    ad.obs["leiden"] = adh.obs["leiden"].values
    ad.obs["cell_type"] = ad.obs.leiden.map(CURATED).astype(str)

    # per-cluster discriminating-marker means (evidence for the curated labels)
    disc = [g for g in ["IL7R", "CCR7", "CD8A", "CD8B", "CD3D", "GNLY", "NKG7", "MS4A1", "CD79A",
                        "CD14", "LYZ", "FCGR3A", "MS4A7", "FCER1A", "CST3", "PPBP"] if g in ad.raw.var_names]
    raw = pd.DataFrame(ad.raw[:, disc].X.toarray(), columns=disc, index=ad.obs_names)
    raw["leiden"] = ad.obs.leiden.values
    marker_means = raw.groupby("leiden").mean().round(3)

    # data-driven top markers per cluster (Wilcoxon) — for the L2 marker/DE ground truth
    sc.tl.rank_genes_groups(ad, "leiden", method="wilcoxon", n_genes=15)
    top = {cl: list(ad.uns["rank_genes_groups"]["names"][cl][:15]) for cl in CURATED}

    ad.obs[["leiden", "cell_type"]].to_csv(os.path.join(OUT, "cell_labels.csv"))
    marker_means.to_csv(os.path.join(OUT, "cluster_marker_means.csv"))
    pd.DataFrame(top).to_csv(os.path.join(OUT, "cluster_top_markers.csv"), index=False)

    gt = {
        "substrate": "clean pbmc3k (L1 clean world, 2700 real cells, hg19)",
        "pipeline": f"scanpy: normalize_total(1e4)->log1p->HVG(2000)->scale->PCA(50)->neighbors(10,40pc)->leiden(res={RES},seed0)",
        "n_cells": int(ad.n_obs), "n_clusters": int(ad.obs.leiden.nunique()),
        "cluster_to_cell_type": CURATED,
        "low_confidence_clusters": LOW_CONF,
        "cell_type_composition": ad.obs.cell_type.value_counts().to_dict(),
        "canonical_markers": CANON_MARKERS,
        "cluster_top_markers": top,
        "note": ("Human-curated from canonical PBMC markers; cluster_marker_means.csv is the evidence. This clean "
                 "annotation is the L2 ground truth (annotation/marker/composition tasks grade against it) and the "
                 "substrate the L2 confounds are injected on. L3 (pending) hands this map forward for the CD4-monocyte flip."),
    }
    json.dump(gt, open(os.path.join(OUT, "ground_truth.json"), "w"), indent=1)
    print(f"[scrna L2 GT] {ad.n_obs} cells, {ad.obs.leiden.nunique()} clusters -> {len(set(CURATED.values()))} cell types")
    print("composition:", gt["cell_type_composition"])
    print(f"saved -> {OUT}/")


if __name__ == "__main__":
    main()
