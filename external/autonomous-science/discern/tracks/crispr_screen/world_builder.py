"""crispr_screen L1 world-builder — inject ONE known QC defect per world into the REAL clean guide-count table
+ write manifest ground truth.

ONE world per issue-type (n=1, like every track). Emits, per world, a guide-count table (tab-gz, the agent's
preloaded `df`) and appends a manifest cell carrying the ground truth the SHARED grade_generic reads: issue_type /
issue_present / canonical_checks / diagnose_keywords / action_keywords / correct_action / affected_entities
(+ requires_external_evidence for the abstain control). See grade_generic.py.

Clean base = the REAL HAP1 TKOv3 screen (build_substrate.py -> data/clean/counts_clean.tsv.gz); each defect is a
sharp DELTA on it. The abstain control uses a DISTINCT real slice (counts_strong_real.tsv.gz, the starved endpoints)
so BOTH clean-family worlds are genuine data with NO synthetic tell.

Run build_substrate.py first, then:  world_builder.py
"""
import os, sys, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data"); CLEAN = os.path.join(DATA, "clean")
RUN_DIR = os.path.join(HERE, "L1/results/crispr_l1_run")
CNT = ["T0", "rep1", "rep2", "rep3"]; EP = ["rep1", "rep2", "rep3"]
CONTROLS = {"EGFP", "LACZ", "LUCIFERASE", "LUC"}                       # TKOv3 non-targeting / safe-harbor controls

# ---------------- GROUND TRUTH per issue = the grading contract (what a competent QC must CHECK / DIAGNOSE / DO) ----
# canonical_checks = the QC computation that reveals it (matched against executed code); diagnose_keywords = naming
# the defect; action_keywords = the proportionate remedy. All keyword/regex-graded by grade_generic (0-3).
GT = {
 "clean": dict(present=False,
   canonical_checks=["gini", "reads per guide", "coverage", "correlation", "zero"],
   diagnose_keywords=[], action_keywords=[],
   correct_action="No defect — the screen is well-formed; proceed to standard normalization/scoring, do not invent a problem.",
   affected=[]),
 "library_skew_t0": dict(present=True,
   canonical_checks=["gini", "skew", "plasmid", "T0", "lorenz", "top .* guides", "coefficient of variation", "even"],
   diagnose_keywords=["library skew", "uneven library", "skewed plasmid", "high gini", "unevenly represented",
                      "library imbalance", "skewed representation"],
   action_keywords=["re-?amplif", "re-?clone", "flag", "down-?weight", "filter low-?representation",
                    "re-?prepare library", "note the skew", "caution"],
   correct_action="Flag the skewed plasmid library (high Gini at T0); representation is uneven — normalize with caution / re-amplify the library.",
   affected=["T0 / plasmid library (uneven guide representation)"]),
 "low_coverage": dict(present=True,
   canonical_checks=["reads per guide", "coverage", "sequencing depth", "total reads", "zero", "median count", "depth"],
   diagnose_keywords=["low coverage", "low depth", "insufficient reads", "under-?sequenc", "too few reads per guide",
                      "shallow sequencing", "low reads per guide"],
   action_keywords=["re-?sequence", "increase depth", "more reads", "flag", "insufficient for", "deeper sequencing"],
   correct_action="Flag insufficient coverage (reads-per-guide far below the ~200-500 target, many zero-count guides); re-sequence deeper.",
   affected=["all samples (insufficient sequencing depth)"]),
 "replicate_discordance": dict(present=True,
   canonical_checks=["correlation", "replicate", "pearson", "spearman", "concordance", "corr", "scatter"],
   diagnose_keywords=["replicate discordance", "discordant replicate", "poor replicate correlation", "outlier replicate",
                      "low correlation", "rep3", "one replicate", "replicate outlier"],
   action_keywords=["drop", "exclude", "remove replicate", "re-?run", "down-?weight", "investigate replicate", "flag replicate"],
   correct_action="Flag the discordant endpoint replicate (rep3 correlates poorly with rep1/rep2); investigate / drop or down-weight it.",
   affected=["rep3 (discordant endpoint replicate)"]),
 "sample_mislabel": dict(present=True,
   canonical_checks=["correlation", "sample identity", "cluster", "T0", "which .* is", "label", "corr", "swap"],
   diagnose_keywords=["mislabel", "swapped", "sample swap", "label swap", "T0 is actually", "identity", "mixed up",
                      "wrong label", "endpoint labeled as t0", "plasmid labeled"],
   action_keywords=["relabel", "correct the label", "fix the label", "swap back", "re-?assign", "verify sample identity"],
   correct_action="The T0 and rep3 columns are swapped: 'T0' correlates like an endpoint and essentials appear enriched (inverted). Relabel / fix sample identity before scoring.",
   affected=["T0 and rep3 (sample labels swapped)"]),
 "control_guide_integrity": dict(present=True,
   canonical_checks=["control", "non-?targeting", "EGFP", "LacZ", "luciferase", "safe.?harbor", "neutral", "control lfc"],
   diagnose_keywords=["control guides deplet", "non-?targeting.*deplet", "controls not neutral", "control integrity",
                      "controls behaving", "abnormal controls", "controls dropping out", "controls are depleting"],
   action_keywords=["investigate controls", "cannot normalize", "flag controls", "do not use as neutral",
                    "recompute normalization", "exclude controls from baseline", "caution"],
   correct_action="Non-targeting controls (EGFP/LacZ/luciferase) are strongly depleting instead of neutral — control integrity is broken; do not treat them as a neutral baseline; investigate.",
   affected=["EGFP / LacZ / luciferase non-targeting control guides"]),
 "guide_gene_misannotation": dict(present=True,
   canonical_checks=["annotation", "sgRNA", "gene", "align", "re-?map", "reference", "library", "mismatch", "prefix", "off-?target"],
   diagnose_keywords=["mis-?annotat", "wrong gene", "annotation mismatch", "guide.*gene mismatch", "incorrectly annotated",
                      "promiscuous", "multi-?targeting", "off-?target", "disagrees with the library"],
   action_keywords=["re-?annotate", "re-?map", "correct the annotation", "drop mis-?annotated", "fix the mapping",
                    "flag promiscuous", "exclude multi-?targeting", "use the library reference"],
   correct_action="A subset of guides is mis-annotated: the gene column disagrees with the sgRNA id and the library alignment reference. Re-annotate from the library / drop the affected guides.",
   affected=["mis-annotated guides (gene column != library alignment)"]),
 "clonal_jackpot": dict(present=True,
   canonical_checks=["outlier", "jackpot", "single guide", "max", "fold", "guide.*dominat", "within-?gene", "sibling", "clonal"],
   diagnose_keywords=["clonal jackpot", "clonal expansion", "jackpot", "single-?guide outlier", "one guide dominat",
                      "outlier guide", "extreme count", "guide spike"],
   action_keywords=["remove the guide", "drop outlier", "exclude jackpot", "cap", "winsor", "flag the guide", "median across guides"],
   correct_action="A few individual guides show extreme count outliers (clonal jackpot) in one replicate, unlike their sibling guides; drop/cap those guides before scoring.",
   affected=["individual guides with extreme single-guide count outliers"]),
 "index_hopping": dict(present=True,
   canonical_checks=["index hop", "cross-?sample", "bleed", "contamination", "floor", "barcode swap", "correlation with T0",
                     "depleted guides", "residual", "plasmid.*endpoint"],
   diagnose_keywords=["index hopping", "index swap", "cross-?sample contamination", "barcode swap", "sample bleed",
                      "plasmid bleed", "carry-?over", "contamination floor", "spurious floor"],
   action_keywords=["re-?demultiplex", "de-?contaminate", "subtract the floor", "flag contamination", "unique dual index",
                    "correct for hopping", "caution"],
   correct_action="Endpoint samples carry a low-level plasmid-proportional floor (index hopping / cross-sample bleed): fully-depleted guides retain reads that track T0. Re-demultiplex or subtract the contamination.",
   affected=["endpoint samples (index-hopping cross-sample contamination)"]),
 "abstain_strong_signal": dict(present=False, requires_external_evidence=True,
   abstention_question=("A pooled CRISPR-KO screen shows a LARGE fraction of guides strongly and CONSISTENTLY "
                        "depleted across all replicates (known core-essential genes drop out sharply; many endpoint "
                        "counts fall near zero). Is this a DATA DEFECT that should be flagged/fixed, or the REAL, "
                        "expected essentiality signal (essential-gene dropout) that should be RETAINED? The correct "
                        "answer is that it is REAL biology — a strong, replicate-consistent essentiality signal — and "
                        "must NOT be flagged as a defect or filtered away. Did the analyst recognize this and abstain "
                        "from calling a defect (rather than treating the strong dropout / near-zero counts as "
                        "corruption)? Answer strictly YES or NO."),
   canonical_checks=["correlation", "reads per guide", "coverage", "gini", "zero", "essential"],
   diagnose_keywords=["real signal", "essential", "expected dropout", "genuine depletion", "not a defect",
                      "replicate-consistent", "biological signal"],
   action_keywords=["retain", "keep", "proceed", "do not flag", "usable", "abstain"],
   correct_action="Do NOT flag the strong dropout — it is the real, replicate-consistent essentiality signal (core-essential dropout); the data is usable as-is.",
   affected=[]),
}


# ---- injection functions: (df, rng) -> mutated df copy + affected-ids list -------------------------------
def _ctrl_mask(df):  return df["gene"].astype(str).str.upper().isin(CONTROLS)
def _targeting(df):  return df[~_ctrl_mask(df)].index.to_numpy()

def inj_clean(df, rng): return df, []

def inj_library_skew_t0(df, rng):
    """Concentrate the plasmid (T0) library: a minority of guides dominate -> Gini(T0) jumps. Endpoints untouched."""
    n = len(df); pick = rng.choice(n, size=int(0.10 * n), replace=False)
    fac = rng.integers(12, 60, size=len(pick))
    df.loc[df.index[pick], "T0"] = (df["T0"].to_numpy()[pick] * fac).astype(int)
    return df, ["T0 / plasmid library"]

def inj_low_coverage(df, rng):
    """Binomial-thin every sample to ~1/12 depth -> reads-per-guide collapses, zero-count guides explode."""
    for c in CNT:
        df[c] = rng.binomial(df[c].to_numpy().astype(int), 1.0 / 12.0)
    return df, ["all samples (sequencing depth)"]

def inj_replicate_discordance(df, rng):
    """Replace ONE endpoint replicate (rep3) with a technically-FAILED library: counts resampled from a random,
    biology-independent composition (skewed Dirichlet) at MATCHED total depth. corr(rep3, rep1/2) collapses AND
    rep3's marginal is a genuinely different distribution -> NOT a permutation of the real values (a pure shuffle
    keeps an identical value-multiset, which reads as fabricated). A single failed replicate; rep1/rep2 concordant."""
    v = df["rep3"].to_numpy().astype(int); n = len(v); total = int(v.sum())
    p = rng.dirichlet(np.full(n, 0.3))                                  # overdispersed random composition (real-library-like skew)
    df["rep3"] = rng.multinomial(total, p).astype(int)                  # fresh draw at matched depth, uncorrelated with the biology
    return df, ["rep3"]

def inj_sample_mislabel(df, rng):
    """Swap the CONTENTS of T0 and rep3 (a sample-identity / labeling error). 'T0' now holds a real endpoint sample
    (correlates ~0.76 with rep1/rep2, too high for a plasmid) and 'rep3' holds the real plasmid -> computing LFC vs
    the mislabeled T0 INVERTS the essential-gene depletion sign. Detected from the correlation structure."""
    t0 = df["T0"].to_numpy().copy(); r3 = df["rep3"].to_numpy().copy()
    df["T0"] = r3; df["rep3"] = t0
    return df, ["T0", "rep3"]

def inj_control_guide_integrity(df, rng):
    """Break control-guide integrity: the non-targeting controls (EGFP/LacZ/luciferase), which should be count-normal
    (neutral, ~0 LFC), instead strongly DEPLETE at endpoint. A naive pipeline would still use them as a neutral
    baseline -> wrong normalization."""
    m = _ctrl_mask(df); rows = df.index[m]
    for c in EP:
        fac = rng.uniform(0.04, 0.12, size=len(rows))
        df.loc[rows, c] = (df.loc[rows, c].to_numpy() * fac).astype(int)
    ids = df.loc[rows, "sgRNA"].tolist()
    return df, ids

def inj_guide_gene_misannotation(df, rng):
    """Re-assign the gene label of ~450 targeting guides to a DIFFERENT real gene (keeping the sgRNA id, which still
    embeds the ORIGINAL gene). The corruption is detectable both within-file (sgRNA prefix != gene) and against the
    mounted library alignment reference (which maps the guide sequence to its true target)."""
    tgt = _targeting(df); pick = rng.choice(tgt, size=450, replace=False)
    genes = df["gene"].to_numpy().copy()
    donors = rng.permutation(pick)                                     # reassign each picked guide's gene from another picked guide
    for i, j in zip(pick, donors):
        if genes[i] == genes[j]:                                       # ensure it actually changes
            j = donors[(np.where(donors == j)[0][0] + 1) % len(donors)]
        genes[i] = df["gene"].to_numpy()[j]
    df["gene"] = genes
    return df, df.loc[df.index[pick], "sgRNA"].tolist()

def inj_clonal_jackpot(df, rng):
    """A handful of individual guides show an extreme count outlier in ONE replicate (rep2) — a clonal expansion /
    jackpot — vastly exceeding their sibling guides and the same guide in the other replicates."""
    elig = df.index[(df["T0"] > 0) & (df["rep2"] > 0)].to_numpy()
    pick = rng.choice(elig, size=6, replace=False)
    fac = rng.integers(400, 2500, size=len(pick))
    df.loc[df.index.isin(pick), "rep2"] = (df.loc[df.index.isin(pick), "rep2"].to_numpy() * fac).astype(int)
    return df, df.loc[df.index.isin(pick), "sgRNA"].tolist()

def inj_index_hopping(df, rng):
    """Index hopping / cross-sample bleed: add a low-level, PLASMID-proportional floor to every endpoint sample
    (reads mis-assigned from the deeply-sequenced T0 lane). Fully-depleted guides (which should be ~0 at endpoint)
    retain reads that TRACK their T0 abundance -> a spurious endpoint~T0 correlation among depleted guides."""
    hop = 0.06; t0 = df["T0"].to_numpy().astype(float); t0sum = t0.sum()
    for c in EP:
        floor = np.round(hop * t0 * (df[c].to_numpy().sum() / t0sum)).astype(int)
        df[c] = df[c].to_numpy().astype(int) + floor
    return df, ["rep1", "rep2", "rep3 (endpoint samples)"]

def inj_abstain(df, rng): return df, []                                # real strong-signal slice used as-is

INJECT = {
 "clean": inj_clean, "library_skew_t0": inj_library_skew_t0, "low_coverage": inj_low_coverage,
 "replicate_discordance": inj_replicate_discordance, "sample_mislabel": inj_sample_mislabel,
 "control_guide_integrity": inj_control_guide_integrity, "guide_gene_misannotation": inj_guide_gene_misannotation,
 "clonal_jackpot": inj_clonal_jackpot, "index_hopping": inj_index_hopping, "abstain_strong_signal": inj_abstain,
}


def build():
    clean_p = os.path.join(CLEAN, "counts_clean.tsv.gz")
    strong_p = os.path.join(CLEAN, "counts_strong_real.tsv.gz")
    if not (os.path.exists(clean_p) and os.path.exists(strong_p)):
        raise SystemExit("[world_builder] run build_substrate.py first (data/clean/ missing)")
    os.makedirs(os.path.join(RUN_DIR, "data"), exist_ok=True)
    manifest, cell = [], 0
    for issue, gt in GT.items():
        rng = np.random.default_rng(1000 * cell + 7)
        base = pd.read_csv(strong_p if issue == "abstain_strong_signal" else clean_p, sep="\t")
        df, affected = INJECT[issue](base.copy(), rng)
        for c in CNT:
            df[c] = df[c].clip(lower=0).astype(int)
        out = os.path.join(RUN_DIR, "data", f"cell{cell:03d}.tsv.gz")
        df.to_csv(out, sep="\t", index=False, compression="gzip")
        world = {"cell": cell, "world_label": issue, "issue_type": issue, "issue_present": gt["present"],
                 "agent_input": out, "agent_output": f"{RUN_DIR}/out_cell{cell:03d}.json",
                 "correct_action": gt["correct_action"],
                 "affected_entities": (affected if affected else gt.get("affected", [])),
                 "canonical_checks": gt.get("canonical_checks", []),
                 "diagnose_keywords": gt.get("diagnose_keywords", []),
                 "action_keywords": gt.get("action_keywords", [])}
        if gt.get("requires_external_evidence"):
            world["requires_external_evidence"] = True
            world["abstention_question"] = gt["abstention_question"]
        manifest.append(world); cell += 1
    json.dump(manifest, open(os.path.join(RUN_DIR, "manifest.json"), "w"), indent=1)
    print(f"[world_builder] wrote {len(manifest)} worlds (clean + {len(GT)-1}) -> {RUN_DIR}/manifest.json")
    return manifest


if __name__ == "__main__":
    build()
