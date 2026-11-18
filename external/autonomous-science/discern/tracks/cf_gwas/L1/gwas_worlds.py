"""
GWAS Basic worlds: inject ONE data-integrity issue (K=1) into a real GWAS
summary-statistics substrate.

Writes agent TSV.GZ files + a ground-truth manifest for deterministic scoring.
No agent / no API.

Issue types:
clean · duplication · beta_outlier · eaf_scale · impossible_values ·
id_version_dup · effect_sign_swap

usage:
python v1_gwas_worlds.py <n_per_issue> <out_dir>
"""

import sys, json, os, hashlib
import numpy as np
import pandas as pd


def det_seed(*parts):
    """Deterministic seed across processes."""
    return int(hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


CLEAN_PATH = "/workspace/discern-benchmark/tracks/cf_gwas/data/gwas_cys_fib/bench_gwas_csfb_sample.tsv.gz"

# Number of variants sampled into each world.
N = 5000

ISSUES = [
    "clean",
    "duplication",
    "beta_outlier",
    "eaf_scale",
    "impossible_values",
    "allele_invalid",
    "id_version_dup",
    "effect_sign_swap",
    "palindromic_high_maf",
    "metadata_reconciliation",
]

VALID_ALLELES = {"A", "C", "G", "T"}

CANONICAL_CHECKS = {
    "duplication": [
        "duplicated", "drop_duplicates", "value_counts", "nunique"
    ],
    "beta_outlier": [
        "describe", "quantile", "iqr", "zscore", "outlier", "abs(", "hist"
    ],
    "eaf_scale": [
        "effect_allele_frequency", "max(", "> 1", "between", "describe", "rescale"
    ],
    "impossible_values": [
        "p_value", "effect_allele_frequency", "chromosome", "base_pair_location",
        "isin", "< 0", "> 1", "unique", "isna", "value_counts"
    ],
    "allele_invalid": [
        "effect_allele", "other_allele", "isin", "A", "C", "G", "T",
        "str.len", "nchar", "unique", "value_counts"
    ],
    "id_version_dup": [
        "variant_id", "chromosome", "base_pair_location", "effect_allele",
        "other_allele", "duplicated", "split", "strip"
    ],
    "effect_sign_swap": [],
    "palindromic_high_maf": [
        "palindromic", "ambiguous", "A/T", "C/G", "T/A", "G/C",
        "maf", "effect_allele_frequency"
    ],
    "metadata_reconciliation": [
        "study_metadata", "metadata", "effect_size_type", "beta", "describe",
        "min(", "exp", "log", "odds", "read"
    ],
}

CORRECT_ACTION = {
    "clean": "none",
    "duplication": "dedup",
    "beta_outlier": "flag_outliers_or_robustify",
    "eaf_scale": "rescale_frequency",
    "impossible_values": "exclude_or_set_na",
    "allele_invalid": "exclude_invalid_or_non_biallelic_variants",
    "id_version_dup": "collapse_duplicate_variant_identities",
    "effect_sign_swap": "abstain_requires_external_evidence",
    "palindromic_high_maf": "flag_or_exclude_before_harmonization",
    "metadata_reconciliation": "reconcile_metadata_effect_type_or_log_transform",
}

# Keywords the grader matches in the agent's free-text issues_found to credit DIAGNOSE (named the issue)
DIAGNOSE_KEYWORDS = {
    "duplication": ["duplicat", "repeated", "identical row", "same row"],
    "beta_outlier": ["outlier", "implausibl.*(beta|effect)",
                     "(beta|effect).*(implausibl|corrupt|impossibl|grossly|absurd|unrealistic|extreme|inflated)",
                     "extreme beta", "large effect", "inflated effect", "unrealistic beta"],
    "eaf_scale": ["scale", "0-100", "0 to 100", "percent", "out of range", "greater than 1",
                  "> 1", "rescale", "frequenc.*100", "not.*0.*1"],
    "impossible_values": ["impossible", "invalid", "out of range", "negative p", "p.?value.*(>|greater).*1",
                          "negative position", "invalid chrom", "chromosome.*99", "out-of-range"],
    "allele_invalid": ["allele", "non-biallelic", "indel", "invalid allele", "not.*acgt", "multi-allelic",
                       "structural variant", "same allele"],
    "id_version_dup": ["version", "\\.2", "versioned", "id.*duplicat", "same variant", "alias"],
    "effect_sign_swap": ["sign", "flipped", "direction", "strand", "swapped"],
    "palindromic_high_maf": ["palindrom", "ambiguous", "strand", "a/t", "c/g"],
    "metadata_reconciliation": ["metadata", "effect_size_type", "odds ratio", "\\bor\\b", "not.*beta",
                                "centered.*1", "all positive", "positive.*effect", "contradict",
                                "inconsistent.*metadata", "exp", "does not match"],
}
# Keywords for ACT (proposed the canonical remediation) — matched in issues_found + code
ACTION_KEYWORDS = {
    "duplication": ["dedup", "drop.*duplicat", "remove.*duplicat", "drop_duplicates", "collapse"],
    "beta_outlier": ["exclud", "remov", "winsor", "robust", r"\bcap\b", "clip", "flag", "recover", r"\bdrop\b"],
    "eaf_scale": ["rescale", "divide.*100", "/ ?100", "convert.*frequenc", "back to.*0.*1"],
    "impossible_values": ["exclude", "remov", "set.*na", "drop", "filter", "correct", r"\bfix\b", "rescale", "clip", "cap "],
    "allele_invalid": ["exclude", "remove", "keep.*biallelic", "filter.*allele", "drop.*allele"],
    "id_version_dup": ["collapse", "strip.*version", "merge", "dedup", "remove.*version"],
    "effect_sign_swap": ["abstain", "external", "cannot.*determin", "requires.*validation",
                         "flag.*uncertain", "second measurement", "replicat"],
    "palindromic_high_maf": ["exclude.*palindrom", "remove.*palindrom", "flag.*palindrom",
                             "drop.*ambiguous", "exclude.*ambiguous"],
    "metadata_reconciliation": ["log", "log.?transform", "convert.*odds", "treat as odds",
                                "reconcile", "flag.*metadata", "ln(", "np.log", "correct.*effect.?type"],
}

DATA_ONLY_DETECTABLE = {
    "clean": True,
    "duplication": True,
    "beta_outlier": True,
    "eaf_scale": True,
    "impossible_values": True,
    "allele_invalid": True,
    "id_version_dup": True,
    "effect_sign_swap": False,
    "palindromic_high_maf": True,
    "metadata_reconciliation": True,
}


def load_real():
    """Load clean GWAS summary statistics and keep rows suitable for a clean substrate."""
    df = pd.read_csv(CLEAN_PATH, sep="\t", compression="infer", low_memory=False)

    required = [
        "variant_id",
        "chromosome",
        "base_pair_location",
        "effect_allele",
        "other_allele",
        "effect_allele_frequency",
        "beta",
        "p_value",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    keep_cols = required[:]
    for c in [
        "hm_variant_id",
        "hm_rsid",
        "hm_chrom",
        "hm_pos",
        "hm_other_allele",
        "hm_effect_allele",
        "hm_beta",
        "hm_effect_allele_frequency",
        "hm_code",
    ]:
        if c in df.columns:
            keep_cols.append(c)

    df = df[keep_cols].copy()

    for c in ["effect_allele", "other_allele", "hm_effect_allele", "hm_other_allele"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.upper().str.strip()

    for c in [
        "chromosome",
        "base_pair_location",
        "effect_allele_frequency",
        "beta",
        "p_value",
        "hm_pos",
        "hm_beta",
        "hm_effect_allele_frequency",
        "hm_code",
    ]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Create a clean-ish substrate before injecting issues.
    df = df.dropna(subset=required)

    df = df[
        df["chromosome"].between(1, 22)
        & (df["base_pair_location"] > 0)
        & df["effect_allele"].isin(VALID_ALLELES)
        & df["other_allele"].isin(VALID_ALLELES)
        & (df["effect_allele"] != df["other_allele"])
        & df["effect_allele_frequency"].between(0, 1)
        & df["p_value"].between(0, 1)
    ].copy()

    df = df.drop_duplicates(subset=["variant_id"])
    df = df.drop_duplicates(
        subset=["chromosome", "base_pair_location", "effect_allele", "other_allele"]
    )

    # Strip NATURAL palindromic (strand-ambiguous) SNPs so the clean substrate is palindrome-free.
    # Then `palindromic_high_maf` is the ONLY source of palindromes -> a clean/corrupt binary,
    # and an agent flagging a palindrome on any other world is a true false positive.
    _comp = {"A": "T", "T": "A", "C": "G", "G": "C"}
    _is_palindromic = df["effect_allele"].map(_comp) == df["other_allele"]
    df = df[~_is_palindromic].copy()

    df = df.reset_index(drop=True)

    if len(df) < N:
        raise ValueError(f"Clean substrate has only {len(df)} rows, but N={N}.")

    return df


def beta_summary(df):
    return {
        "beta_min": round(float(df["beta"].min()), 6),
        "beta_max": round(float(df["beta"].max()), 6),
        "beta_median": round(float(df["beta"].median()), 6),
        "beta_abs_p99": round(float(df["beta"].abs().quantile(0.99)), 6),
    }


def build(df_all, issue, seed):
    """Sample N real variants, then inject ONE GWAS QC issue."""
    rng = np.random.default_rng(seed)

    idx = rng.choice(len(df_all), N, replace=False)
    world = df_all.iloc[idx].copy().reset_index(drop=True)

    affected = []
    clean_beta_summary = beta_summary(world)

    if issue == "clean":
        pass

    elif issue == "duplication":
        # About 17% exact duplicate rows appended.
        m = int(0.17 * N)
        j = rng.choice(N, m, replace=False)
        dups = world.iloc[j].copy()
        world = pd.concat([world, dups], ignore_index=True)
        affected = world.iloc[N:]["variant_id"].astype(str).tolist()

    elif issue == "beta_outlier":
        # Extreme beta values create leverage/outlier behavior.
        m = max(6, int(0.006 * N))
        j = rng.choice(N, m, replace=False)

        base = max(float(world["beta"].abs().quantile(0.99)), 1e-6)

        for k, t in enumerate(j):
            sign = -1 if k % 2 == 0 else 1
            new_beta = sign * base * rng.uniform(30, 60)
            world.loc[t, "beta"] = new_beta

            if "hm_beta" in world.columns and pd.notna(world.loc[t, "hm_beta"]):
                world.loc[t, "hm_beta"] = new_beta

        affected = world.loc[j, "variant_id"].astype(str).tolist()

    elif issue == "eaf_scale":
        # Unit/scale mismatch: EAF is expected as 0-1 but stored as 0-100.
        world["effect_allele_frequency"] = world["effect_allele_frequency"] * 100.0

        if "hm_effect_allele_frequency" in world.columns:
            world["hm_effect_allele_frequency"] = world["hm_effect_allele_frequency"] * 100.0

        affected = ["effect_allele_frequency"]

    elif issue == "impossible_values":
        # Impossible values across key GWAS fields.
        m = max(10, int(0.02 * N))
        j = rng.choice(N, m, replace=False)

        for k, t in enumerate(j):
            mod = k % 6

            if mod == 0:
                world.loc[t, "p_value"] = -0.01
            elif mod == 1:
                world.loc[t, "p_value"] = 1.5
            elif mod == 2:
                world.loc[t, "effect_allele_frequency"] = -0.2
            elif mod == 3:
                world.loc[t, "effect_allele_frequency"] = 1.3
            elif mod == 4:
                world.loc[t, "chromosome"] = 99
            else:
                world.loc[t, "base_pair_location"] = -100

        affected = world.loc[j, "variant_id"].astype(str).tolist()

    elif issue == "allele_invalid":
        # Invalid/non-biallelic allele values.
        # Creates rows with N, I/D, multi-character alleles, or same allele twice.
        m = max(10, int(0.02 * N))
        j = rng.choice(N, m, replace=False)

        bad_values = ["N", "I", "D", "AT"]

        for k, t in enumerate(j):
            mod = k % 5

            if mod == 0:
                world.loc[t, "effect_allele"] = "N"
            elif mod == 1:
                world.loc[t, "other_allele"] = "I"
            elif mod == 2:
                world.loc[t, "effect_allele"] = "AT"
            elif mod == 3:
                world.loc[t, "other_allele"] = "D"
            else:
                # Same allele on both sides is invalid for a biallelic SNP.
                world.loc[t, "other_allele"] = world.loc[t, "effect_allele"]

        affected = world.loc[j, "variant_id"].astype(str).tolist()

    elif issue == "palindromic_high_maf":
        # Strand-ambiguous SNPs with MAF near 0.5.
        # A/T and C/G variants near 0.5 are hard to orient safely.
        m = max(10, int(0.05 * N))
        j = rng.choice(N, m, replace=False)

        pairs = [("A", "T"), ("T", "A"), ("C", "G"), ("G", "C")]

        for k, t in enumerate(j):
            a1, a2 = pairs[k % len(pairs)]
            eaf = float(np.clip(0.5 + rng.normal(0, 0.025), 0.40, 0.60))

            world.loc[t, "effect_allele"] = a1
            world.loc[t, "other_allele"] = a2
            world.loc[t, "effect_allele_frequency"] = eaf

            # Keep harmonized columns aligned if present, so this issue is specifically
            # about palindromic/high-MAF ambiguity, not a harmonization mismatch.
            if "hm_effect_allele" in world.columns:
                world.loc[t, "hm_effect_allele"] = a1
            if "hm_other_allele" in world.columns:
                world.loc[t, "hm_other_allele"] = a2
            if "hm_effect_allele_frequency" in world.columns:
                world.loc[t, "hm_effect_allele_frequency"] = eaf

        affected = world.loc[j, "variant_id"].astype(str).tolist()

    elif issue == "id_version_dup":
        # Same genomic identity appears twice, but the duplicate has a versioned variant ID.
        m = int(0.05 * N)
        j = rng.choice(N, m, replace=False)

        dups = world.iloc[j].copy()
        dups["variant_id"] = dups["variant_id"].astype(str) + ".2"

        if "hm_variant_id" in dups.columns:
            dups["hm_variant_id"] = dups["hm_variant_id"].astype(str) + ".2"

        world = pd.concat([world, dups], ignore_index=True)
        affected = dups["variant_id"].astype(str).tolist()

    elif issue == "effect_sign_swap":
        # Label-swap analogue: beta signs are flipped but table can still look internally valid.
        # Correct behavior is to recognize this needs external evidence.
        m = int(0.30 * N)
        j = rng.choice(N, m, replace=False)

        world.loc[j, "beta"] = -1 * world.loc[j, "beta"]

        if "hm_beta" in world.columns:
            mask = world.loc[j, "hm_beta"].notna()
            world.loc[j[mask], "hm_beta"] = -1 * world.loc[j[mask], "hm_beta"]

        affected = []

    elif issue == "metadata_reconciliation":
        # study_metadata.json declares effect_size_type="beta"; here the effect column is made
        # ODDS-RATIO-like (exp(beta): all positive, centered ~1). Detectable only by cross-checking the
        # DISCOVERABLE metadata (still says "beta") against the effect distribution -> a metadata<->data
        # contradiction. Correct move: recognize the mismatch and log-transform / reconcile the effect type.
        world["beta"] = np.exp(world["beta"].astype(float))
        if "hm_beta" in world.columns:
            hm = world["hm_beta"].notna()
            world.loc[hm, "hm_beta"] = np.exp(world.loc[hm, "hm_beta"].astype(float))
        affected = ["effect column is odds-ratio-scaled but study_metadata.json declares effect_size_type=beta"]

    else:
        raise ValueError(f"Unknown issue: {issue}")

    corrupt_beta_summary = beta_summary(world)

    gt = {
        "world_label": issue,
        "issue_type": "none" if issue == "clean" else issue,
        "issue_present": issue != "clean",
        "affected_entities": affected,
        "correct_action": CORRECT_ACTION[issue],
        "canonical_checks": CANONICAL_CHECKS.get(issue, []),
        "diagnose_keywords": DIAGNOSE_KEYWORDS.get(issue, []),
        "action_keywords": ACTION_KEYWORDS.get(issue, []),
        "data_only_detectable": DATA_ONLY_DETECTABLE[issue],
        "requires_external_evidence": not DATA_ONLY_DETECTABLE[issue],
        "clean_beta_summary": clean_beta_summary,
        "corrupted_beta_summary": corrupt_beta_summary,
    }

    return world, gt


def write_tsv(world, path):
    world.to_csv(path, sep="\t", index=False, compression="gzip")


if __name__ == "__main__":
    NP = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    OUT = sys.argv[2] if len(sys.argv) > 2 else "results/gwas_v1_basic"

    os.makedirs(f"{OUT}/data", exist_ok=True)

    df_all = load_real()

    man = []
    cell = 0

    for issue in ISSUES:
        for r in range(NP):
            seed = det_seed("gwas_gcst003143", issue, r)
            world, gt = build(df_all, issue, seed)

            p = f"{OUT}/data/cell{cell:03d}.tsv.gz"
            write_tsv(world, p)

            man.append({
                "cell": cell,
                "source": "GCST003143",
                "task_type": "gwas_summary_statistics_qc",
                "trait_context": "cystic fibrosis lung disease severity",
                "n_rows": len(world),
                "agent_input": p,
                "agent_output": f"{OUT}/out_cell{cell:03d}.json",
                "columns_present": list(world.columns),
                "per_variant_sample_size_available": False,
                "standard_error_available": False,
                "imputation_info_available": False,
                **gt,
            })

            cell += 1

    json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)

    from collections import Counter

    print(
        f"wrote {cell} worlds -> {OUT}  "
        f"issues={dict(Counter(m['world_label'] for m in man))}"
    )

    for m in man:
        if m["cell"] % NP == 0:
            print(
                f"  [{m['world_label']:<18}] "
                f"rows={m['n_rows']:<6} "
                f"affected={len(m['affected_entities']):<6} "
                f"action={m['correct_action']}"
            )