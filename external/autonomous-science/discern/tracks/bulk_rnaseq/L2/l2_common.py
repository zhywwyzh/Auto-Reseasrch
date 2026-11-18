"""bulk_rnaseq L2 — shared helpers + world injections/materializers.

Single source of truth imported by BOTH reference_solver.py (golden truth + trap-fire verification)
and world_builder.py — a world can never drift from what the solver verified.

Sub-tasks (L2_DESIGN.md "Track — bulk_rnaseq L2"; parameterization informed by the 2026-08-12
empirical scoping pass on the REAL GSE152418 substrate — see the BUILD ADDENDUM for deviations):
  (1) de        — differential expression, COVID-19 vs Healthy (PyDESeq2 golden)
        clean / batch_confound (TT, injected discoverable batch) /
        normalization_default (TT, sample-SELECTED plasmablast/IG composition skew — real, max 24%
        total-count-vs-median-of-ratios divergence) / hidden_covariate (DC, amplified RIN-coupled
        degradation; rin/three_prime_bias sit in the metadata as the data-internal tell)
  (2) gsea      — pathway enrichment on the golden DE result
        clean / ranking_metric_default (TT, unsigned ranking) /
        wrong_background_universe (TT, genome-vs-expressed ORA universe; REPLACES the designed
        gene_length_bias which does NOT fire on this substrate — 1.10x length ratio, corr -0.02) /
        geneset_size_bias (S)
  (3) structure — unsupervised structure over all 34 samples
        clean / pca_on_raw_counts (TT, REFRAMED: raw PC1 is hijacked by extreme-abundance genes
        (HBB/S100A8/9/IG), condition corr 0.48 vs 0.90 after log — NOT the designed libsize story,
        which does not fire at 1.6x spread) / composition_confound (DC, task-framed attribution:
        IGfrac~PC1 corr 0.74) / over_cluster_default (S, bootstrap co-assignment golden)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

TRACK = Path(__file__).resolve().parents[1]
PROC = TRACK / "data" / "processed"
RES_DIR = TRACK / "data" / "resources"
RNG_SEED = 20260812

COUNTS = PROC / "counts_expressed.tsv.gz"
GENE_META = PROC / "gene_meta.tsv"
METADATA = TRACK / "data" / "clean" / "sample_metadata.tsv"
GMT = {"hallmark": RES_DIR / "h.all.v2023.2.Hs.symbols.gmt",
       "reactome": RES_DIR / "c2.cp.reactome.v2023.2.Hs.symbols.gmt",
       "gobp": RES_DIR / "c5.go.bp.v2023.2.Hs.symbols.gmt"}


def load_all():
    counts = pd.read_csv(COUNTS, sep="\t", index_col=0)
    meta = pd.read_csv(METADATA, sep="\t").set_index("sample_id")
    gm = pd.read_csv(GENE_META, sep="\t", index_col=0)
    return counts, meta, gm


def de_cohort(counts, meta):
    m = meta[meta.condition.isin(["COVID-19", "Healthy"])].copy()
    return counts[m.index], m


def load_gmt(path):
    sets = {}
    for line in open(path):
        f = line.rstrip("\n").split("\t")
        sets[f[0]] = set(f[2:])
    return sets


# ---------------------------------------------------------------- DE (PyDESeq2) machinery
def run_deseq(counts, meta, design_cols, contrast=("condition", "COVID-19", "Healthy")):
    """PyDESeq2 with an explicit design; returns the results_df (+ size factors)."""
    import inspect
    from pydeseq2.dds import DeseqDataSet
    from pydeseq2.ds import DeseqStats
    kw = {}
    sig = inspect.signature(DeseqDataSet.__init__).parameters
    if "design" in sig:
        kw["design"] = "~" + "+".join(design_cols)
    else:
        kw["design_factors"] = list(design_cols)
    dds = DeseqDataSet(counts=counts.T, metadata=meta, refit_cooks=True, quiet=True, **kw)
    dds.deseq2()
    st = DeseqStats(dds, contrast=list(contrast), quiet=True)
    st.summary()
    sf = pd.Series(np.asarray(dds.obs["size_factors"]), index=dds.obs_names)
    return st.results_df.copy(), sf


def de_concordance(res_a, res_b, n_top=500):
    """How well DE result a reproduces reference b: logFC corr + top-gene overlap."""
    j = res_a[["log2FoldChange", "padj"]].join(res_b[["log2FoldChange", "padj"]],
                                               lsuffix="_a", rsuffix="_b").dropna()
    lfc_corr = float(np.corrcoef(j.log2FoldChange_a, j.log2FoldChange_b)[0, 1])
    top_a = set(j.nsmallest(n_top, "padj_a").index)
    top_b = set(j.nsmallest(n_top, "padj_b").index)
    return {"lfc_corr": lfc_corr, "top500_jaccard": len(top_a & top_b) / len(top_a | top_b)}


# ---------------------------------------------------------------- (1) DE world materializers
def inj_batch_confound(counts, meta, n_genes_frac=0.40, sigma=1.2, seed=RNG_SEED):
    """TOOL TRAP — inject a DISCOVERABLE 2-batch structure partially aligned with condition
    (batch B = most COVID + a few Healthy), as per-gene multiplicative log-normal factors applied
    to batch-B samples. The default `~condition` design absorbs batch into DE; the robust move is
    to DISCOVER the batch axis (correlation/PCA structure) and fit `~batch+condition`.
    Partial (not perfect) alignment keeps the model identifiable."""
    rng = np.random.default_rng(seed)
    Xde, m = de_cohort(counts, meta)
    covid = list(m.index[m.condition == "COVID-19"])
    healthy = list(m.index[m.condition == "Healthy"])
    batch_b = sorted(rng.choice(covid, 9, replace=False).tolist()
                     + rng.choice(healthy, 6, replace=False).tolist())   # moderate alignment: naive contaminated, model identifiable (scan-locked)
    genes = rng.choice(Xde.index, int(len(Xde) * n_genes_frac), replace=False)
    fac = pd.Series(np.exp(rng.normal(0, sigma, len(genes))), index=genes)
    out = Xde.copy().astype(float)
    out.loc[genes, batch_b] = out.loc[genes, batch_b].mul(fac, axis=0)
    out = out.round().astype(int)
    m2 = m.copy()
    m2["batch"] = ["B" if s in set(batch_b) else "A" for s in m2.index]   # ground truth (NOT given to agent)
    return out, m2, sorted(batch_b), [str(g) for g in genes[:0]]  # gene list omitted from manifest (30% of genome)


def naive_cpm_lfc(counts, meta):
    """The normalization_default NAIVE path: per-gene logFC from the prepared total-count-CPM
    matrix (mean logCPM difference). On this cohort the real plasmablast/IG composition skew
    (SF/TC down to 0.76) biases it globally (median offset ~-0.14 vs the median-of-ratios golden;
    ~100 truly-null genes shift by >=0.3). v1 LESSON: selecting IG-heavy samples DEFEATS the trap
    (the median-of-ratios pseudo-reference shifts with the selection, shrinking the divergence to
    0.86) -> the world keeps the FULL DE cohort and ships a prepared CPM artifact instead."""
    Xde, m = de_cohort(counts, meta)
    lib = Xde.sum(axis=0)
    lcpm = np.log2(Xde / lib * 1e6 + 1)
    grp = (m.condition == "COVID-19").values
    return lcpm.loc[:, grp].mean(axis=1) - lcpm.loc[:, ~grp].mean(axis=1)


def inj_hidden_covariate(counts, meta, strength=1.8, seed=RNG_SEED):
    """DATA CONFOUND — amplify the REAL RIN axis (rin correlates with condition at -0.29 and sits
    in the metadata): RNA-degradation-style count decay, stronger for LONG genes and LOW-RIN
    samples (3'-bias mechanism). Naive `~condition` DE absorbs the degradation axis; robust =
    notice the rin/three_prime_bias metadata columns + the length-coupled signal and model rin."""
    rng = np.random.default_rng(seed)
    Xde, m = de_cohort(counts, meta)
    gm = pd.read_csv(GENE_META, sep="\t", index_col=0)
    L = np.log10(gm.reindex(Xde.index).exon_union_bp.fillna(gm.exon_union_bp.median()))
    lz = (L - L.mean()) / L.std()                       # long genes decay more
    deg = (9.2 - m.rin) / (9.2 - m.rin).max()           # 0 (best RIN) .. 1 (worst)
    lam = np.outer((lz.clip(-1.5, 1.5) + 1.5) / 3.0, deg) * strength   # gene x sample decay rate
    keep = np.exp(-lam)
    out = pd.DataFrame(rng.binomial(Xde.values.astype(int), keep),
                       index=Xde.index, columns=Xde.columns)
    return out, m


# ---------------------------------------------------------------- (2) GSEA helpers
def ora(de_symbols, universe, gene_sets, min_size=15):
    """Hypergeometric over-representation with an explicit universe."""
    from scipy.stats import hypergeom
    de_u = set(de_symbols) & universe
    rows = []
    for name, s in gene_sets.items():
        s_u = s & universe
        if len(s_u) < min_size:
            continue
        k = len(de_u & s_u)
        p = float(hypergeom.sf(k - 1, len(universe), len(s_u), len(de_u)))
        rows.append((name, k, len(s_u), p))
    return pd.DataFrame(rows, columns=["set", "k", "K", "p"]).sort_values("p").reset_index(drop=True)


def prerank_scores(res, gm, signed=True):
    """Gene-level ranking metric: signed Wald stat (golden) or unsigned -log10(p) (the naive
    direction-blind default)."""
    j = res if "symbol" in res.columns else res.join(gm[["symbol"]])
    j = j.dropna(subset=["symbol"])
    j = j.loc[~j.symbol.duplicated()]
    if signed:
        return pd.Series(j.stat.values, index=j.symbol)
    return pd.Series(-np.log10(j.pvalue.clip(1e-300)).values, index=j.symbol)


def set_direction_calls(rnk, gene_sets, min_size=15):
    """Simple direction-aware set score: mean rank-z of members. Sign = direction call."""
    r = rnk.rank()
    z = (r - r.mean()) / r.std()
    out = {}
    for name, s in gene_sets.items():
        members = z.reindex(list(s)).dropna()
        if len(members) >= min_size:
            out[name] = float(members.mean())
    return pd.Series(out)


# ---------------------------------------------------------------- (3) structure helpers
def logcpm(counts):
    lib = counts.sum(axis=0)
    return np.log2(counts / lib * 1e6 + 1)


def pca_axes(mat_samples_x_features, n=4):
    from sklearn.decomposition import PCA
    p = PCA(n_components=n)
    pcs = p.fit_transform(mat_samples_x_features)
    return pcs, p


def bootstrap_coassignment(pcs, k, n_boot=200, seed=RNG_SEED):
    """Stability of a KMeans k: mean bootstrap co-assignment consistency (0.5=chance, 1=stable)."""
    from sklearn.cluster import KMeans
    rng = np.random.default_rng(seed)
    n = len(pcs)
    ref = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(pcs)
    same_ref = (ref[:, None] == ref[None, :])
    agree = []
    for _ in range(n_boot):
        idx = rng.choice(n, n, replace=True)
        lab = KMeans(n_clusters=k, n_init=4, random_state=int(rng.integers(1e6))).fit_predict(pcs[idx])
        same = (lab[:, None] == lab[None, :])
        ref_pairs = same_ref[np.ix_(idx, idx)]
        mask = ~np.eye(len(idx), dtype=bool)
        agree.append(float((same == ref_pairs)[mask].mean()))
    return float(np.mean(agree))


def ig_fraction(counts, gm):
    ig = gm[gm.symbol.astype(str).str.startswith(("IGH", "IGK", "IGL"))].index
    return counts.loc[counts.index.intersection(ig)].sum(axis=0) / counts.sum(axis=0)


# ---------------------------------------------------------------- prepared-artifact materializers
# The hist `model_matrix.csv` pattern: worlds that would otherwise share identical data with clean
# get a PREPARED, plausibly-convenient artifact whose naive use IS the trap; the raw inputs sit
# alongside so the robust move is always possible. (See BUILD ADDENDUM for why each exists.)

def prep_cpm_matrix(counts):
    """normalization_default — a 'convenience' CPM-normalized matrix (the total-count artifact):
    analyzing it directly inherits the plasmablast/IG composition bias; robust = return to the raw
    counts and use proper (median-of-ratios) size factors."""
    lib = counts.sum(axis=0)
    return (counts / lib * 1e6).round(3)


def prep_unsigned_rnk(golden_res_with_symbol):
    """ranking_metric_default — a prepared .rnk 'gene ranking' by -log10(p) (direction lost):
    preranked GSEA on it is direction-blind; robust = rebuild a SIGNED metric from the DE table."""
    j = golden_res_with_symbol.dropna(subset=["symbol"])
    j = j.loc[~j.symbol.duplicated()]
    rnk = pd.DataFrame({"gene": j.symbol,
                        "score": -np.log10(j.pvalue.clip(1e-300))}).sort_values("score", ascending=False)
    return rnk


def prep_genome_background(gene_sets, expressed_symbols):
    """wrong_background_universe — a prepared 'background gene universe (all annotated genes)'
    list: ORA against it fabricates ~100 spurious GO-BP hits; robust = expressed-gene universe."""
    return sorted(set().union(*gene_sets.values()) | set(expressed_symbols))


def prep_raw_pca(counts, n=4):
    """pca_on_raw_counts — precomputed 'sample PCA' of the UNTRANSFORMED count matrix: its PC1 is
    hijacked by extreme-abundance genes (HBB/S100A8/9/IG) and loses the condition axis; robust =
    recompute on a variance-stabilized/log transform and check the loadings."""
    from sklearn.decomposition import PCA
    p = PCA(n_components=n)
    scores = p.fit_transform(counts.T.values)
    sc = pd.DataFrame(scores, index=counts.columns, columns=[f"PC{i+1}" for i in range(n)])
    ld = pd.DataFrame(p.components_.T, index=counts.index, columns=[f"PC{i+1}" for i in range(n)])
    return sc.round(3), ld.round(6)
