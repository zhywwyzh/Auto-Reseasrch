"""hist_gene_exp L2 — shared helpers + world injections.

Single source of truth imported by BOTH reference_solver.py (golden truth + trap-fire verification)
and world_builder.py (world materialization) — a world can never drift from what the solver verified.

Sub-tasks (L2_DESIGN.md "Track — hist_gene_exp L2"; v2 parameterization LOCKED by the 2026-08-12
solver exploration — every non-clean world below was verified to FIRE on the real substrate):
  (1) regression      — mark->expression regression on the per-gene table
        clean / gc_cpg_confound (DC, GC bias injected into the RNA quantification — Benjamini&Speed
        2012 class) / outlier_leverage (S) / nonlinearity_saturation (S)
  (2) quantify        — signal quantification from raw ENCODE alignments (3 TOOL TRAPS, TWAS analog)
        clean (H3K4me3 +-1kb; default-no-input is fine) / no_input_normalization (H3K27me3 +-10kb;
        skipping the PRESENT input control silently loses the repressive biology) /
        broad_mark_narrow_default (MACS3 default narrow fragments H3K27me3 domains) /
        wrong_promoter_window (+-1kb TSS convention mis-captures the broad mark)
  (3) effect_ranking  — per-mark independent effect / ranking
        clean / multicollinearity (TT, n=400 pilot mini-cohort: naive OLS loses H3K27me3, dnase sign
        unstable) / omitted_confounder (DC, prepared matrix omits H3K27ac -> H3K4me3 coef inflates
        2x) / aggregation_reversal (S, CGI vs non-CGI strata)
"""
import json, subprocess, sys
from pathlib import Path

import numpy as np
import pandas as pd

TRACK = Path(__file__).resolve().parents[1]
PROC = TRACK / "data" / "processed"
PANEL_DIR = TRACK / "data" / "raw" / "alignments_panel"
GENE_TABLE = PROC / "l2_gene_table.csv"
RNG_SEED = 20260812

TARGET_MARK = "h3k4me3"          # sub-task (1)'s target relationship (the strong canonical positive)
MARKS = ["h3k4me3", "h3k27ac", "h3k27me3", "dnase"]
COVARS = ["gc_content", "cpg_oe"]
PANEL_GSIZE = 552700000          # summed hg38 length of chr8+9+11+17+22

# ---------------------------------------------------------------- table stats
def zscore(x):
    x = np.asarray(x, float)
    return (x - x.mean()) / x.std()

def pearson(a, b):
    return float(np.corrcoef(a, b)[0, 1])

def spearman(a, b):
    from scipy.stats import spearmanr
    return float(spearmanr(a, b).statistic)

def gc_composite(df):
    return zscore(zscore(df.gc_content) + zscore(df.cpg_oe))

def partial_r(df, mark=TARGET_MARK, covars=COVARS, y="gene_expression"):
    """Partial correlation of mark vs expression given the GC/CpG covariates — the golden (1)
    estimand. Chosen over a standardized beta because it is EXACTLY invariant to any injected
    component lying in the covariate span (verified: clean 0.4555 == confounded 0.4555)."""
    X = np.column_stack([zscore(df[c]) for c in covars] + [np.ones(len(df))])
    rx = zscore(df[mark]) - X @ np.linalg.lstsq(X, zscore(df[mark]), rcond=None)[0]
    ry = zscore(df[y]) - X @ np.linalg.lstsq(X, zscore(df[y]), rcond=None)[0]
    return float(np.corrcoef(rx, ry)[0, 1])

def ols_std(df, predictors, y="gene_expression"):
    """Standardized OLS coefficients dict for `predictors` jointly."""
    X = np.column_stack([zscore(df[c]) for c in predictors] + [np.ones(len(df))])
    coef, *_ = np.linalg.lstsq(X, zscore(df[y]), rcond=None)
    return {p: float(c) for p, c in zip(predictors, coef)}

def ridge_std(df, predictors, y="gene_expression", alpha=None):
    """Standardized ridge coefficients (stable golden reference for (3))."""
    from sklearn.linear_model import Ridge
    X = np.column_stack([zscore(df[c]) for c in predictors])
    r = Ridge(alpha=alpha if alpha is not None else len(df) / 100.0).fit(X, zscore(df[y]))
    return {p: float(c) for p, c in zip(predictors, r.coef_)}

def vif(df, predictors):
    out = {}
    for p in predictors:
        others = [q for q in predictors if q != p]
        X = np.column_stack([zscore(df[q]) for q in others] + [np.ones(len(df))])
        yv = zscore(df[p])
        coef, res, *_ = np.linalg.lstsq(X, yv, rcond=None)
        r2 = 1.0 - (res[0] / len(yv) if len(res) else np.mean((yv - X @ coef) ** 2))
        out[p] = float(1.0 / max(1e-9, 1.0 - r2))
    return out

def bootstrap_sign_stability(df, predictors, n=300, seed=RNG_SEED):
    """Fraction of bootstrap OLS fits agreeing with the full-fit sign, per predictor."""
    rng = np.random.default_rng(seed)
    full = ols_std(df, predictors)
    agree = {p: 0 for p in predictors}
    for _ in range(n):
        idx = rng.integers(0, len(df), len(df))
        b = ols_std(df.iloc[idx], predictors)
        for p in predictors:
            agree[p] += int(np.sign(b[p]) == np.sign(full[p]))
    return {p: agree[p] / n for p in predictors}

def cgi_mask(df):
    """CGI-like promoters (Gardiner-Garden-ish): CpG obs/exp >= 0.6 AND GC >= 0.5."""
    return (df.cpg_oe >= 0.6) & (df.gc_content >= 0.5)

# ------------------------------------------------- sub-task (1) injections (DELTAS on the real table)
def inj_gc_cpg_confound(df, k=0.5):
    """DATA CONFOUND — GC-dependent quantification bias in the RNA-seq (Benjamini & Speed 2012):
    expression is inflated along the promoter GC/CpG composite. The naive Pearson mark~expression
    INFLATES (+0.543 -> +0.648 at k=0.5) because the mark itself is GC-correlated (r=0.52); the
    GC/CpG-ADJUSTED partial correlation is EXACTLY unchanged (0.4555). Robust move: adjust for the
    provided gc_content/cpg_oe covariates. Affine in the covariate span — no clipping (clipping
    breaks the exact-recovery property; the k*std*(comp-min) form keeps values positive)."""
    d = df.copy()
    comp = gc_composite(d)
    d["gene_expression"] = (d.gene_expression + k * d.gene_expression.std() * (comp - comp.min())).round(4)
    return d

def inj_outlier_leverage(df, n_out=60, mult=3.0, seed=RNG_SEED):
    """STATISTICAL — 60 extreme-signal promoters at lowest-expression-decile genes: leverage points
    that drag the naive Pearson (0.543 -> 0.440) while Spearman barely moves (0.550 -> 0.536).
    Robust move: rank-based / robust estimate + flag the outliers."""
    rng = np.random.default_rng(seed)
    d = df.copy()
    low_idx = d.gene_expression.nsmallest(int(len(d) * 0.1)).index
    pick = rng.choice(low_idx, n_out, replace=False)
    d.loc[pick, TARGET_MARK] = round(float(d[TARGET_MARK].max()) * mult, 4)
    return d, [str(g) for g in d.loc[pick, "gene_id"]]

def inj_nonlinearity_saturation(df, K_q=0.30):
    """STATISTICAL — saturate the target mark (Michaelis-Menten-like): monotone relation preserved
    (Spearman unchanged) but the naive LINEAR Pearson understates it (0.543 -> 0.485).
    Robust move: rank/spline check; report the monotone association."""
    d = df.copy()
    x = d[TARGET_MARK].astype(float)
    K = float(x.quantile(K_q)) + 1e-6
    d[TARGET_MARK] = ((x / (K + x)) * x.max() * 0.9).round(4)
    return d

# ------------------------------------------------- sub-task (3) world materializers
def sub_multicollinearity(df, n=400, seed=RNG_SEED):
    """TOOL TRAP — a 'pilot mini-cohort' row-subsample of the REAL table (no value changed).
    At n=400 with VIF~6.5, default OLS produces a complete-looking per-mark effect table that is
    silently WRONG: H3K27me3's independent effect vanishes (-0.01 vs golden -0.134; sign stability
    0.60) and dnase's sign is a coin flip (0.51). Robust move: check VIF/bootstrap CIs, regularize,
    refuse confident per-predictor claims the n cannot support."""
    return df.sample(n=n, random_state=seed).reset_index(drop=True)

def prepared_matrix_omit(df):
    """DATA CONFOUND — the 'prepared modeling matrix' handed to the agent OMITS H3K27ac (the top
    co-varying activation mark) and the covariates. Fitting what's given inflates H3K4me3's
    'independent effect' 2x (0.374 vs golden 0.185 — classic omitted-variable bias). Robust move:
    verify the INPUT — notice the full gene table alongside includes h3k27ac, re-include it."""
    return df[["gene_id", "gene_name", "chrom", "h3k4me3", "h3k27me3", "dnase",
               "gene_expression", "gene_length"]].copy()

# ------------------------------------------------- sub-task (2) quantification helpers (BAM panel)
def _bam(name):
    return str(PANEL_DIR / f"{name}.panel.bam")

def promoter_read_counts(bam, genes_df, half=1000):
    """Reads-in-window per gene (pysam), normalized to reads-per-million-per-kb — the HAND-ROLLED
    coverage quantification (what a no-deepTools agent plausibly computes)."""
    import pysam
    bf = pysam.AlignmentFile(bam, "rb")
    total = sum(s.mapped for s in bf.get_index_statistics()) or 1
    vals = []
    for _, g in genes_df.iterrows():
        lo, hi = max(0, int(g.tss) - half), int(g.tss) + half
        try:
            c = bf.count(g.chrom, lo, hi)
        except ValueError:
            c = 0
        vals.append(c * 1e6 / total / ((hi - lo) / 1000.0))
    bf.close()
    return np.array(vals)

def norm_log2ratio(mark_counts, input_counts, pseudo=0.5):
    """Input-normalized promoter signal: log2((mark+p)/(input+p)) on library-normalized counts —
    the hand-rolled analog of deepTools bamCompare log2ratio."""
    return np.log2((mark_counts + pseudo) / (input_counts + pseudo))

def macs3_callpeak(mark, outdir, broad=False, name=None, gsize=PANEL_GSIZE):
    """Run MACS3 callpeak (mark vs the input control) — DEFAULT narrow unless broad=True."""
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    name = name or (str(mark).split("/")[-1].replace(".panel.bam", "").replace(".bam", "")
                    + ("_broad" if broad else "_narrow"))
    cmd = [str(Path(sys.executable).parent / "macs3"), "callpeak",
           "-t", _bam(mark) if not str(mark).endswith(".bam") else str(mark),
           "-c", _bam("input"), "-f", "BAM", "-n", name, "--outdir", str(outdir),
           "-g", str(gsize), "-q", "0.05"]
    if broad:
        cmd += ["--broad", "--broad-cutoff", "0.1"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"macs3 failed: {r.stderr[-800:]}")
    return outdir / (name + ("_peaks.broadPeak" if broad else "_peaks.narrowPeak"))

def peak_stats(peak_file):
    n, bp = 0, 0
    for line in open(peak_file):
        f = line.split("\t")
        n += 1; bp += int(f[2]) - int(f[1])
    return {"n_peaks": n, "total_bp": bp, "mean_width": (bp / n if n else 0)}

def overlap_bp(peak_file, genes_df, half=10000):
    """Per-gene bp of called-peak/domain overlap in TSS+-half — the downstream per-gene view of a
    peak-calling result (used to show narrow-default fragmentation costs real biology)."""
    from collections import defaultdict
    iv = defaultdict(list)
    for line in open(peak_file):
        f = line.split("\t")
        iv[f[0]].append((int(f[1]), int(f[2])))
    for ch in iv:
        iv[ch].sort()
    out = []
    for _, g in genes_df.iterrows():
        lo, hi = int(g.tss) - half, int(g.tss) + half
        tot = 0
        for s, e in iv.get(g.chrom, []):
            if e < lo:
                continue
            if s > hi:
                break
            tot += min(e, hi) - max(s, lo)
        out.append(tot)
    return np.array(out)

def panel_genes():
    """Genes on the BAM panel chromosomes (from the L2 gene table), for per-gene quantification."""
    df = pd.read_csv(GENE_TABLE)
    prov = json.load(open(PANEL_DIR / "panel_provenance.json"))
    return df[df.chrom.isin(prov["panel"])].reset_index(drop=True)
