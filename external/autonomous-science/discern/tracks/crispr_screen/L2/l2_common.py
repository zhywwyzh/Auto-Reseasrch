"""crispr_screen L2 — shared helpers + world injections/materializers.

Single source of truth imported by BOTH reference_solver.py (golden truth + trap-fire verification) and
world_builder.py — a world can never drift from what the solver verified. RE-SAVED 2026-08-12 from the
crispr-building session's context (see RECOVERY_NOTE.md): the sourceless .pyc stopgap is replaced by this
byte-faithful source (verified: reference_solver regenerates the restored gold identically).

Substrate = the BUILT L1 HAP1/TKOv3 pooled-KO screen (data/clean/counts_clean.tsv.gz: sgRNA,gene,T0,rep1..3) +
the mounted CEGv2 / NEGv1 gold gene lists + the TKOv3 alignment summary. The "tool" is a BAGEL-style Bayes-Factor
scorer reimplemented in numpy/scipy (MAGeCK/Chronos/CRISPRcleanR are NOT installed) — NON-CIRCULAR: the
essential/non-essential fold-change distributions are learned from the EXTERNAL CEG/NEG gold lists.

Reframed for the single-line HAP1/TKOv3 substrate (the DepMap CN-artifact / cross-line-panel design is NOT
constructible here). Every world is solver-first FIRE-CHECKED.
  (1) scoring   clean / guide_efficiency (TT) / off_target_promiscuous (DC)   [outlier_guide dropped: confounded]
  (2) calling   clean / null_calibration (TT) / replicate_irreproducible (TT) / threshold_sensitivity (S)
  (3) context   clean / artifact_context_hit (TT) / over_correction_erases_real (S)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

TRACK = Path(__file__).resolve().parents[1]
DATA = TRACK / "data"
CLEAN = DATA / "clean" / "counts_clean.tsv.gz"
RES_DIR = DATA / "resources"
CEG_F = RES_DIR / "CEGv2.txt"
NEG_F = RES_DIR / "NEGv1.txt"
ALIGN_F = RES_DIR / "TKOv3_align_summary_REAGENT_ID.txt"
PROC = DATA / "processed"
RNG_SEED = 20260812
REPS = ["rep1", "rep2", "rep3"]
_GRID = np.linspace(-13.0, 5.0, 400)          # LFC grid for the BF KDE interpolation


# ---------------------------------------------------------------- loaders
def load_counts():
    return pd.read_csv(CLEAN, sep="\t")


def load_gene_lists():
    ceg = set(l.split("\t")[0].strip() for l in open(CEG_F).read().splitlines()[1:] if l.strip())
    neg = set(l.split("\t")[0].strip() for l in open(NEG_F).read().splitlines()[1:] if l.strip())
    return ceg, neg


def promiscuous_guides():
    """reagent_id -> list of OFF-TARGET gene symbols from the TKOv3 alignment summary (multi-targeting guides:
    gene-symbol tokens beyond the primary-target column; coordinate tokens 'chr..' are skipped)."""
    m = {}
    for line in open(ALIGN_F):
        f = line.rstrip("\n").split("\t")
        if not f or not f[0]:
            continue
        extra = [t.strip() for c in f[3:] for t in c.split(",")
                 if t.strip() and not t.strip().startswith("chr")]
        if extra:
            m[f[0]] = extra
    return m


# ---------------------------------------------------------------- BAGEL-style scoring machinery
def guide_lfc(counts):
    """Per-guide log2 fold-change vs T0, each sample depth-normalized to 1e7 reads (+0.5 pseudocount)."""
    tot = {c: counts[c].sum() for c in ["T0"] + REPS}
    t0 = counts["T0"] / tot["T0"] * 1e7
    fc = pd.DataFrame({r: np.log2((counts[r] / tot[r] * 1e7 + 0.5) / (t0 + 0.5)) for r in REPS},
                      index=counts.index)
    fc["mean"] = fc[REPS].mean(axis=1)
    return fc


def gene_scores(counts, ceg, neg):
    """The correct-tool output: per-gene BAGEL-style Bayes Factor (higher = more essential) + naive/robust aggregates.
    The essential/non-essential guide-LFC densities are learned from the world's own CEG/NEG guides — non-circular."""
    fc = guide_lfc(counts)
    g = counts[["sgRNA", "gene"]].copy()
    g["lfc"] = fc["mean"].values
    for r in REPS:
        g[r] = fc[r].values
    ess = g.loc[g.gene.isin(ceg), "lfc"].values
    non = g.loc[g.gene.isin(neg), "lfc"].values
    ke, kn = gaussian_kde(ess), gaussian_kde(non)
    lr = np.log(np.clip(ke(_GRID), 1e-12, None)) - np.log(np.clip(kn(_GRID), 1e-12, None))
    g["bf_guide"] = np.interp(g["lfc"].values, _GRID, lr)
    agg = g.groupby("gene").agg(
        mean_lfc=("lfc", "mean"), median_lfc=("lfc", "median"), best_lfc=("lfc", "min"),
        bf=("bf_guide", "sum"), n_guides=("lfc", "size"),
        lfc_rep1=("rep1", "mean"), lfc_rep2=("rep2", "mean"), lfc_rep3=("rep3", "mean"))
    agg["is_ceg"] = agg.index.isin(ceg)
    agg["is_neg"] = agg.index.isin(neg)
    return agg


def essential_threshold(scores, q=0.95):
    """The correctly-calibrated cutoff: BF at the q-quantile of the NON-ESSENTIAL (NEG) genes (~5% NEG-FDR)."""
    return float(np.quantile(scores.loc[scores.is_neg, "bf"], q))


def call_essential(scores, thr):
    return scores.bf > thr


def rep_concordant(scores, cut=-1.0, need=2):
    """A depletion is REPRODUCIBLE only if >= `need` of the 3 replicate gene-LFCs clear `cut`."""
    return (scores[["lfc_rep1", "lfc_rep2", "lfc_rep3"]] < cut).sum(axis=1) >= need


# ---------------------------------------------------------------- world injectors (pure DELTAs on real counts)
def _pick(genes, pool, n, seed):
    return list(np.random.default_rng(seed).choice(sorted(set(genes) & set(pool)), n, replace=False))


def inj_guide_efficiency(counts, ceg, n_genes=12, seed=RNG_SEED):
    """TOOL TRAP — real essentials with mostly DEAD guides: keep only the single most-depleting guide active, set the
    others' endpoints back to T0. Naive gene-MEAN dilutes below the cutoff; best-guide/BF recovers."""
    d = counts.copy()
    fc = guide_lfc(d)["mean"]
    avail = [g for g, k in counts.groupby("gene").size().items() if g in ceg and k >= 4]
    genes = _pick(avail, avail, n_genes, seed)
    for gene in genes:
        idx = d.index[d.gene == gene].tolist()
        keep = fc.loc[idx].idxmin()
        for i in idx:
            if i != keep:
                for r in REPS:
                    d.loc[i, r] = d.loc[i, "T0"]
    return d, {"genes": genes, "truth": "essential"}


def inj_outlier_guide(counts, neg, n_genes=12, seed=RNG_SEED):
    """(DROPPED from the shipped set — confounded with guide_efficiency; kept for reference.) One hyperactive guide
    fakes essentiality for a non-essential gene."""
    d = counts.copy()
    avail = [g for g, k in counts.groupby("gene").size().items() if g in neg and k >= 4]
    genes = _pick(avail, avail, n_genes, seed)
    for gene in genes:
        i = d.index[d.gene == gene].tolist()[0]
        for r in REPS:
            d.loc[i, r] = max(1, int(d.loc[i, "T0"] * 0.02))
    return d, {"genes": genes, "truth": "non-essential"}


def inj_off_target_promiscuous(counts, neg, n_genes=10, seed=RNG_SEED):
    """DATA CONFOUND — TWO genuinely multi-targeting guides (flagged in the alignment summary) deplete a non-essential
    gene. Because two of ~four guides deplete, robust MEDIAN also fails; recovery needs the alignment file (drop the
    promiscuous guides). Verify-the-INPUT (guide->gene mapping), distinct from the value-robust outlier_guide."""
    d = counts.copy()
    prom = promiscuous_guides()
    by_gene = counts[counts.sgRNA.isin(prom)].groupby("gene").sgRNA.apply(list)
    avail = [g for g in by_gene.index if g in neg and len(by_gene[g]) >= 2]
    genes = _pick(avail, avail, min(n_genes, len(avail)), seed)
    hit_guides = {}
    for gene in genes:
        gd = d[d.gene == gene]
        pg = [s for s in gd.sgRNA if s in prom][:2]
        hit_guides[gene] = pg
        for s in pg:
            i = d.index[d.sgRNA == s][0]
            for r in REPS:
                d.loc[i, r] = max(1, int(d.loc[i, "T0"] * 0.03))
    return d, {"genes": genes, "truth": "non-essential", "promiscuous_guides": hit_guides}


def inj_replicate_irreproducible(counts, neg, n_genes=12, seed=RNG_SEED):
    """TOOL TRAP — a non-essential gene depletes strongly in ONE replicate only. Pooled gene-MEAN crosses the cutoff;
    requiring replicate concordance (>=2/3) rejects it."""
    d = counts.copy()
    avail = [g for g, k in counts.groupby("gene").size().items() if g in neg and k >= 4]
    genes = _pick(avail, avail, n_genes, seed)
    for gene in genes:
        for i in d.index[d.gene == gene].tolist():
            d.loc[i, "rep1"] = max(1, int(d.loc[i, "T0"] * 0.05))
    return d, {"genes": genes, "truth": "non-essential"}


def inj_context_artifact(counts, neg, n_genes=8, seed=RNG_SEED):
    """(3) TOOL TRAP — a "context-specific essential" that is actually an off-target/one-replicate ARTIFACT: a
    non-essential gene given one hyperactive guide AND a one-rep spike. Naive promotes it; robust demotes it."""
    d = counts.copy()
    avail = [g for g, k in counts.groupby("gene").size().items() if g in neg and k >= 4]
    genes = _pick(avail, avail, n_genes, seed)
    for gene in genes:
        idx = d.index[d.gene == gene].tolist()
        for r in REPS:
            d.loc[idx[0], r] = max(1, int(d.loc[idx[0], "T0"] * 0.02))
        d.loc[idx[1], "rep1"] = max(1, int(d.loc[idx[1], "T0"] * 0.04))
    return d, {"genes": genes, "truth": "non-essential(artifact)"}


# ---------------------------------------------------------------- prepared-artifact / selectors
def prep_allgene_z(scores):
    """null_calibration NAIVE artifact — a 'convenience' per-gene z-score table computed against the ALL-GENE null;
    a |z| cutoff on it silently misses ~24% of true essentials (the pooled sd is inflated by the essentials it
    contains). Robust = recompute the null from the NEG genes only."""
    mu, sd = scores.mean_lfc.mean(), scores.mean_lfc.std()
    z = (scores.mean_lfc - mu) / sd
    return pd.DataFrame({"gene": scores.index, "mean_lfc": scores.mean_lfc.round(4),
                         "z_allgene_null": z.round(4)}).sort_values("z_allgene_null")


def context_candidates(scores, thr, need=3, cut=-1.0):
    """Genes essential in HAP1 (BF>thr) that are NON-CORE (not CEG) and NON-NEG, with REPRODUCIBLE depletion across
    all `need` reps — the pool of genuine context-specific dependencies for (3)."""
    m = (scores.bf > thr) & (~scores.is_ceg) & (~scores.is_neg)
    reps_ok = (scores[["lfc_rep1", "lfc_rep2", "lfc_rep3"]] < cut).sum(axis=1) >= need
    return scores[m & reps_ok].sort_values("bf", ascending=False)
