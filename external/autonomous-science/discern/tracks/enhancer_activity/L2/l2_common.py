"""enhancer_activity L2 — shared helpers + world injections. Single source of truth imported by BOTH
reference_solver.py and world_builder.py (no drift).

Substrate = the BUILT L1 Klein 2018 cross-species STARR-seq table (data/raw/klein_2018_s4_with_sequences.csv:
coordinate, enrichment_score, sequence — 11 primate species, ~327 ortholog families). DATA-CONFOUND-focused,
CROSS-SPECIES-heavy (the feasibility gate: FIMO/HOMER/liftOver absent, GPN mapping missing, and seq->activity /
per-species scale / conservation~activity all null in aggregate — Klein's real biology). What fires = input-
integrity + cross-species-structure confounds that corrupt the analysis conclusion. THREE analyses:

 (1) divergence   — which enhancer FAMILIES have diverged (turnover) activity across species.
     clean / species_batch_confound (DC, one species' assay shifted -> spurious divergence; normalize) /
     enrichment_outlier (DC, implausible out-of-range values fake turnover; verify plausibility) /
     phylo_pseudoreplication (DC, turnover driven only by a closely-related species PAIR is correlated noise,
     not real cross-clade turnover; the 11 species are NOT independent) / species_dropout_bias (DC, a duplicated/
     mislabeled species inflates a family's apparent range; one-per-species must hold).
 (2) conservation — rank the most sequence-CONSERVED enhancer families (from the 11-species ortholog set), and
     surface conserved-sequence-but-divergent-activity families (turnover; the L3 feeder).
     clean / gc_conservation_bias (DC, GC content biases the raw %-identity conservation estimate; adjust) /
     alignment_quality (DC, families with heterogeneous ortholog lengths give unreliable conservation; exclude) /
     conservation_as_proxy (prior/task-framed, do NOT read conservation as activity — the data decouples them).
 (3) ranking      — the most ACTIVE enhancers, correctly handling the cross-species ortholog structure.
     clean / ortholog_family_leakage (DC, per-row ranking double-counts the same family across 11 species;
     dedup to family) / duplicate_contamination (DC, injected exact-duplicate rows inflate the active set) /
     reference_species_bias (DC, ranking by activity-relative-to-human biases toward human-outlier families).
"""
import itertools
import re
from pathlib import Path

import numpy as np
import pandas as pd

TRACK = Path(__file__).resolve().parents[1]
RAW = TRACK / "data" / "raw" / "klein_2018_s4_with_sequences.csv"
PROC = TRACK / "data" / "processed"
RNG_SEED = 20260812
TURNOVER_THR = 2.0
MIN_SPECIES = 4
OUTLIER_MAD = 6.0
# rough phylo order (great apes -> OWM -> NWM); adjacent = closely related
PHYLO_ORDER = ["hg38", "panTro5", "gorGor3", "ponAbe2", "nomLeu3", "chlSab2", "papAnu2", "rheMac3",
               "macFas5", "calJac3", "saiBol1"]
REFERENCE_SPECIES = "hg38"


# ---------------------------------------------------------------- loaders
def load_klein():
    df = pd.read_csv(RAW).dropna(subset=["sequence", "enrichment_score"]).copy()
    df["seq"] = df.sequence.str.upper().str.replace(r"[^ACGT]", "", regex=True)
    df = df[df.seq.str.len() >= 50].reset_index(drop=True)
    df["family"] = df.coordinate.str.replace(r"_[A-Za-z0-9]+$", "", regex=True)
    df["species"] = df.coordinate.str.extract(r"_([A-Za-z0-9]+)$")[0]
    df["gc"] = df.seq.apply(lambda s: (s.count("G") + s.count("C")) / len(s))
    return df


def agent_view(df):
    """Columns handed to the agent in a world dir (mirrors the L1 raw layout — no family/species leak)."""
    return df[["coordinate", "enrichment_score", "sequence"]].copy()


# ---------------------------------------------------------------- (1) divergence machinery
def family_divergence(df, score_col="enrichment_score"):
    g = df.groupby("family")[score_col].agg(rng=lambda x: float(x.max() - x.min()), n="size")
    g["n_species"] = df.groupby("family").species.nunique()
    return g


def turnover_set(df, thr=TURNOVER_THR, min_sp=MIN_SPECIES, score_col="enrichment_score"):
    g = family_divergence(df, score_col)
    return set(g[(g.rng > thr) & (g.n_species >= min_sp)].index)


def per_species_z(df, score_col="enrichment_score"):
    return df.groupby("species")[score_col].transform(lambda v: (v - v.mean()) / v.std())


def flag_implausible(df, score_col="enrichment_score", k=OUTLIER_MAD):
    v = df[score_col]; med = v.median(); mad = (v - med).abs().median() * 1.4826
    if mad <= 0:
        return []
    return df.index[(v - med).abs() > k * mad].tolist()


def clade_robust_turnover(df, thr=TURNOVER_THR, min_sp=MIN_SPECIES):
    """Phylo-aware turnover: real cross-clade turnover is CONSISTENT across related species — the most-deviant
    species should agree with its phylogenetic NEIGHBOUR, or a second (non-neighbour) species should also be
    strongly deviant. A single species that disagrees with its own sister is phylo-inconsistent noise -> demote."""
    rank = {s: i for i, s in enumerate(PHYLO_ORDER)}
    keep = set()
    for fam, g in df.groupby("family"):
        if g.species.nunique() < min_sp:
            continue
        gg = g.groupby("species").enrichment_score.mean()
        med = gg.median()
        if (gg.max() - gg.min()) <= thr:
            continue
        dev = (gg - med)
        out_sp = dev.abs().idxmax(); oi = rank.get(out_sp)
        neigh = [s for s in gg.index if s != out_sp and oi is not None and abs(rank.get(s, 99) - oi) <= 1]
        consistent = any(np.sign(dev[s]) == np.sign(dev[out_sp]) and abs(dev[s]) >= 0.5 * abs(dev[out_sp])
                         for s in neigh)
        second = dev.abs().sort_values(ascending=False)
        multi = len(second) > 1 and second.iloc[1] >= thr * 0.5     # a 2nd species also strongly deviant
        if consistent or multi:
            keep.add(fam)
    return keep


def one_per_species_ok(df):
    """Families with a DUPLICATED species (same species appears >1x) — an integrity violation that inflates range."""
    bad = []
    for fam, g in df.groupby("family"):
        if g.species.duplicated().any():
            bad.append(fam)
    return set(bad)


# ---------------------------------------------------------------- (2) conservation machinery
def _k6(s):
    return set(s[i:i + 6] for i in range(len(s) - 5))


def family_conservation(df):
    """Per-family sequence conservation (mean pairwise 6-mer Jaccard among orthologs; length-robust) +
    length-heterogeneity (a low-quality-alignment tell) + mean GC. Returns a DataFrame indexed by family."""
    rows = []
    for fam, g in df.groupby("family"):
        seqs = g.seq.tolist()
        if len(seqs) < 3:
            continue
        ks = [_k6(s) for s in seqs]
        sims = [len(a & b) / max(1, len(a | b)) for a, b in itertools.combinations(ks, 2)]
        lens = [len(s) for s in seqs]
        rows.append((fam, float(np.mean(sims)), float(np.std(lens) / max(1, np.mean(lens))),
                     float(g.gc.mean()), float(g.enrichment_score.max() - g.enrichment_score.min())))
    return pd.DataFrame(rows, columns=["family", "cons", "len_het", "gc", "act_range"]).set_index("family")


def gc_adjust_conservation(cons_df):
    """Robust move for gc_conservation_bias: regress out GC from the conservation estimate (residual conservation)."""
    x = cons_df.gc.values; y = cons_df.cons.values
    b = np.polyfit(x, y, 1)
    return pd.Series(y - np.polyval(b, x), index=cons_df.index)


def conserved_set(cons_series_or_df, frac=0.25):
    """Top-`frac` most-conserved families (the gradeable output)."""
    s = cons_series_or_df.cons if hasattr(cons_series_or_df, "cons") else cons_series_or_df
    return set(s.sort_values(ascending=False).head(int(len(s) * frac)).index)


def bad_alignment_families(cons_df, thr=0.15):
    return set(cons_df.index[cons_df.len_het > thr])


# ---------------------------------------------------------------- (3) ranking machinery
def active_family_set(df, frac=0.15, score_col="enrichment_score"):
    """Top-`frac` most-active FAMILIES (family activity = max over its species-orthologs) — the dedup'd truth."""
    fam_act = df.groupby("family")[score_col].max()
    return set(fam_act.sort_values(ascending=False).head(int(df.family.nunique() * frac)).index)


def naive_row_top_families(df, n=None, score_col="enrichment_score"):
    """The FOOLED per-ROW ranking: top-n rows, mapped to families (double-counts ortholog duplicates)."""
    n = n or int(df.family.nunique() * 0.15)
    return set(df.nlargest(n, score_col).family)


# ---------------------------------------------------------------- world injectors (deterministic DELTAs)
def inj_species_batch(df, offset=3.0, seed=RNG_SEED):
    rng = np.random.default_rng(seed + 1)
    sp = df.species.value_counts().idxmax()
    d = df.copy()
    d.loc[d.species == sp, "enrichment_score"] = d.loc[d.species == sp, "enrichment_score"] + offset
    return d, {"species": sp, "offset": offset, "kind": "spurious_divergence"}


def inj_enrichment_outlier(df, n_families=15, seed=RNG_SEED):
    rng = np.random.default_rng(seed)
    clean_turn = turnover_set(df)
    conserved = [f for f, g in df.groupby("family") if f not in clean_turn and len(g) >= 5]
    fams = list(rng.choice(sorted(conserved), min(n_families, len(conserved)), replace=False))
    d = df.copy(); affected = []
    for f in fams:
        idx = d.index[d.family == f].tolist()[0]
        d.loc[idx, "enrichment_score"] = float(rng.choice([9.0, 12.0, -14.0, 10.5, 11.0]))
        affected.append(f)
    return d, {"families": affected, "kind": "fake_turnover"}


def inj_phylo_pseudoreplication(df, n_families=15, seed=RNG_SEED):
    """DC — fabricate turnover that is a SINGLE sister-species jump: in conserved families, shift ONE species
    (and it alone) to an extreme, choosing a species with a phylo-neighbour present. Naive range>thr calls
    turnover; the clade-robust move sees the divergence is one closely-related-species contrast and demotes it."""
    rng = np.random.default_rng(seed + 2)
    clean_turn = turnover_set(df)
    conserved = [f for f, g in df.groupby("family")
                 if f not in clean_turn and len(g) >= 6 and "panTro5" in set(g.species) and "hg38" in set(g.species)]
    fams = list(rng.choice(sorted(conserved), min(n_families, len(conserved)), replace=False))
    d = df.copy(); affected = []
    for f in fams:
        # push panTro5 to an extreme relative to its neighbour hg38 (a single sister jump)
        idx = d.index[(d.family == f) & (d.species == "panTro5")]
        if len(idx):
            base = d.loc[d.family == f, "enrichment_score"].median()
            d.loc[idx[0], "enrichment_score"] = base - 2.6
            affected.append(f)
    return d, {"families": affected, "kind": "fake_turnover_singlepair"}


def inj_species_duplicate(df, n_families=15, seed=RNG_SEED):
    """DC — duplicate ONE species within a family under an extreme value (a merge/label error): the family gains
    a second same-species row with an extreme enrichment, inflating its apparent range. Detectable as a duplicated
    species; the robust move enforces one-per-species (dedup) before computing divergence."""
    rng = np.random.default_rng(seed + 3)
    clean_turn = turnover_set(df)
    conserved = [f for f, g in df.groupby("family") if f not in clean_turn and len(g) >= 5]
    fams = list(rng.choice(sorted(conserved), min(n_families, len(conserved)), replace=False))
    add = []; affected = []
    for f in fams:
        g = df[df.family == f].iloc[0]
        dup = g.copy()
        dup["enrichment_score"] = float(rng.choice([4.5, -6.5, 5.0]))    # extreme duplicate of an existing species
        add.append(dup); affected.append(f)
    d = pd.concat([df, pd.DataFrame(add)], ignore_index=True)
    return d, {"families": affected, "kind": "fake_turnover_dupspecies"}


def inj_alignment_quality(df, n_families=12, seed=RNG_SEED):
    """DC (conservation) — inject length-heterogeneous orthologs (truncations) into some HIGH-conservation families:
    the raw %-identity/6-mer conservation drops spuriously; the robust move flags the bad-alignment families
    (length heterogeneity) and excludes them rather than mis-ranking them as non-conserved."""
    rng = np.random.default_rng(seed + 4)
    cons = family_conservation(df)
    top = cons.sort_values("cons", ascending=False).head(80).index.tolist()
    fams = list(rng.choice(top, min(n_families, len(top)), replace=False))
    d = df.copy(); affected = []
    for f in fams:
        idx = d.index[d.family == f].tolist()[0]                        # truncate one ortholog to ~40%
        s = d.loc[idx, "seq"]; d.loc[idx, "seq"] = s[: max(50, int(len(s) * 0.4))]
        d.loc[idx, "sequence"] = d.loc[idx, "seq"]
        affected.append(f)
    return d, {"families": affected, "kind": "bad_alignment"}


def inj_duplicate_rows(df, n=60, seed=RNG_SEED):
    """DC (ranking) — inject exact-duplicate rows of some ACTIVE enhancers (a merge/dedup error): the naive active
    set / active-fraction inflates; the robust move drops exact duplicates."""
    rng = np.random.default_rng(seed + 5)
    active = df[df.enrichment_score > df.enrichment_score.quantile(0.9)]
    dup = active.sample(min(n, len(active)), random_state=1).copy()
    d = pd.concat([df, dup], ignore_index=True)
    return d, {"n_dup": len(dup), "kind": "inflated_active"}
