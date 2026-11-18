"""hist_gene_exp L2 — confound injectors (SINGLE SOURCE OF TRUTH) — v2, evidence-calibrated.

Used by BOTH reference_solver.py (to verify each trap fires: naive != golden, robust ~= golden — a world that
doesn't fire doesn't ship) and world_builder.py (to build the shipped worlds). Each injector is a DELTA on the
REAL clean per-gene table (never synthesizes the clean data). Deterministic (fixed seeds).

v2 changes (driven by the v1 end-to-end trap-fire audit — see gold/ and L2_DESIGN.md build notes):
  * gc_cpg_confound: inject the GC common-cause bias into the EXPRESSION column (RNA-seq GC library bias — a
    real phenomenon), NOT into the mark. Adding a weak common cause to the strong mark column DILUTES the
    naive correlation instead of inflating it (v1 bug); biasing expression with +lam*z(gc_axis) INFLATES the
    naive mark~expression estimate AND is removed EXACTLY by partialling out GC/CpG -> adjusted recovers the
    golden adjusted beta algebraically. Leaves an in-data tell: corr(gc_content, expression) jumps ~0.19 -> ~0.6.
  * regression worlds run on a seeded N_PANEL-gene subsample (leverage/saturation cannot move Pearson at
    n=19k; at n=2000 they discriminate). subsample_panel() is the shared, seeded selector.
  * outlier_leverage: outliers = SILENT genes given extreme mark signal (discordant leverage points drag the
    naive fit); stronger factor.
  * omitted_confounder (③): linear GC-driven component added to ONE mark (h3k4me3) -> naive 4-mark OLS
    inflates its beta / scrambles the ranking; including the gc covariate removes the term exactly.
"""
import numpy as np

MARK = "h3k4me3"                     # ① primary relationship (positive, strong in K562)
SEED = 20260812
N_PANEL = 2000                       # ① worlds run on this seeded gene panel (leverage needs small n)


def _z(x):
    x = np.asarray(x, float)
    return (x - x.mean()) / (x.std() or 1.0)


def subsample_panel(df, n=N_PANEL, seed=SEED):
    """The shared seeded gene panel for ① regression worlds (clean + confounds -> SAME panel)."""
    return df.sample(n=n, random_state=seed).reset_index(drop=True).copy()


def inj_gc_cpg_confound(df, lam=0.8):
    """① DATA CONFOUND — GC/CpG common-cause bias injected into EXPRESSION (RNA-seq GC library bias):
    expression' = expression + lam*sd(expr)*z(gc_axis). Naive mark~expression INFLATES; adjusting for
    gc_content+cpg_oe removes the injected term exactly -> recovers the golden adjusted beta."""
    out = df.copy()
    gc_axis = _z(_z(out["gc_content"]) + _z(out["cpg_oe"]))
    out["gene_expression"] = np.round(
        out["gene_expression"] + lam * out["gene_expression"].std() * gc_axis, 4)
    return out


def inj_outlier_leverage(df, n_out=25, target=6.0):
    """① STATISTICAL — extreme-signal promoters at SILENT genes: discordant leverage points that drag the
    naive Pearson/OLS fit down. Sets the mark to ~target*sd above the mean at n_out of the least-expressed
    genes. Robust move: Spearman / robust regression ~= golden (n_out/N ranks barely move)."""
    rng = np.random.default_rng(SEED)
    out = df.copy()
    idx = out.nsmallest(n_out * 8, "gene_expression").sample(n=n_out, random_state=SEED).index
    hi = out[MARK].mean() + target * out[MARK].std() * (1 + 0.15 * rng.random(n_out))
    out.loc[idx, MARK] = np.round(hi, 4)
    return out, sorted(out.loc[idx, "gene_id"].tolist())


def inj_nonlinearity_saturation(df, k_quantile=0.10):
    """① STATISTICAL — saturate the mark signal (Michaelis-Menten-like) so the naive LINEAR fit
    underestimates the relationship; rank/Spearman (monotone-preserving) ~= golden Spearman."""
    out = df.copy()
    x = out[MARK].to_numpy(float)
    K = np.quantile(x[x > 0], k_quantile)
    vmax = np.quantile(x, 0.98)
    out[MARK] = np.round(vmax * x / (K + x), 4)
    return out


def inj_omitted_confounder(df, lam=1.0):
    """③ DATA CONFOUND — linear GC-driven component added to ONE mark: h3k4me3' = h3k4me3 + lam*sd*z(gc).
    Naive 4-mark OLS (no covariates) inflates h3k4me3 / scrambles the ranking; a model that INCLUDES the
    gc_content covariate absorbs the injected term exactly -> per-mark effects ~= golden."""
    out = df.copy()
    out["h3k4me3"] = np.round(
        out["h3k4me3"] + lam * out["h3k4me3"].std() * _z(out["gc_content"]), 4)
    return out


INJECTORS = {
    "gc_cpg_confound": inj_gc_cpg_confound,
    "outlier_leverage": inj_outlier_leverage,
    "nonlinearity_saturation": inj_nonlinearity_saturation,
    "omitted_confounder": inj_omitted_confounder,
}
