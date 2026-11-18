"""LEVEL 2 - Task 2: Lead SNP / Locus analysis worlds (HARDER confounds).

Locus-preserving worlds (keep all variants near the real genome-wide-significant signals) with confounds
that pass basic validity but fool naive distance-based grouping / lead selection, so they require real
GWAS reasoning:
  clean               - the 2 real loci (chr5, chr11p13/EHF-APIP)
  masked_secondary    - a 2nd independent lead ~300kb from a real lead (distance-merging hides it)
  mega_locus          - a dense 2Mb long-range-LD cluster (naive +-500kb fragments it into many fakes)
  pvalue_underflow    - top-locus p-values set to exactly 0 (can't rank the lead by p naively)
  threshold_edge      - a suggestive decoy at p~1e-6 (just under 5e-8) that must NOT be called a locus
  inflation_fake_loci - lambda_GC~1.25 -> scattered fake singleton "loci" genome-wide

Each world stores an explicit ground truth (reference_leads, correct_n_loci, issue-specific fields).

usage: gwas_task2_worlds.py <n_per_issue> <out_dir>
"""
import sys, json, os, hashlib
import numpy as np
import pandas as pd
from scipy.stats import chi2

def det_seed(*p): return int(hashlib.md5("|".join(map(str, p)).encode()).hexdigest()[:8], 16)

SRC = "/workspace/discern-benchmark/tracks/cf_gwas/data/gwas_cys_fib/bench_gwas_csfb_sample.tsv.gz"
SIG = 5e-8; LOCUS_KB = 500_000; BG = 3000
VALID = {"A", "C", "G", "T"}
ISSUES = ["clean", "masked_secondary", "mega_locus", "pvalue_underflow", "threshold_edge", "scattered_fake_loci"]


def load_clean_full():
    df = pd.read_csv(SRC, sep="\t", compression="infer", low_memory=False)
    req = ["variant_id", "chromosome", "base_pair_location", "effect_allele", "other_allele",
           "effect_allele_frequency", "beta", "p_value"]
    for c in ["effect_allele", "other_allele"]:
        df[c] = df[c].astype(str).str.upper().str.strip()
    for c in ["chromosome", "base_pair_location", "effect_allele_frequency", "beta", "p_value"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[req + [c for c in ["hm_variant_id"] if c in df.columns]].dropna(subset=req)
    df = df[df["chromosome"].between(1, 22) & (df["base_pair_location"] > 0)
            & df["effect_allele"].isin(VALID) & df["other_allele"].isin(VALID)
            & (df["effect_allele"] != df["other_allele"])
            & df["effect_allele_frequency"].between(0, 1) & df["p_value"].between(0, 1)]
    df = df.drop_duplicates(subset=["variant_id"]).drop_duplicates(
        subset=["chromosome", "base_pair_location", "effect_allele", "other_allele"])
    comp = {"A": "T", "T": "A", "C": "G", "G": "C"}
    df = df[df["effect_allele"].map(comp) != df["other_allele"]]
    return df.reset_index(drop=True)


def lambda_gc(p):
    p = np.clip(np.asarray(p, float), 1e-300, 1.0)
    return float(np.median(chi2.isf(p, 1)) / chi2.isf(0.5, 1))

def rescale_lambda(p, target):
    p = np.clip(np.asarray(p, float), 1e-300, 1.0)
    return chi2.sf(chi2.isf(p, 1) * (target / max(lambda_gc(p), 1e-6)), 1)


def greedy_loci(df, thresh=SIG, kb=LOCUS_KB):
    sig = df[df["p_value"] < thresh].sort_values("p_value")
    loci, used = [], set()
    for _, r in sig.iterrows():
        vid = str(r["variant_id"])
        if vid in used: continue
        near = sig[(sig["chromosome"] == r["chromosome"])
                   & ((sig["base_pair_location"] - r["base_pair_location"]).abs() <= kb)]
        near = near[~near["variant_id"].astype(str).isin(used)]
        loci.append({"chromosome": int(r["chromosome"]), "lead_variant_id": vid,
                     "lead_pos": int(r["base_pair_location"]), "lead_pval": float(r["p_value"]),
                     "n_sig_variants": int(len(near))})
        used.update(near["variant_id"].astype(str).tolist())
    return loci


def standard_qc(df):
    d = df.copy().drop_duplicates()
    d = d.drop_duplicates(subset=["chromosome", "base_pair_location", "effect_allele", "other_allele"])
    return d[(d["p_value"] >= 0) & (d["p_value"] <= 1) & d["chromosome"].between(1, 22) & (d["base_pair_location"] > 0)]


def locus_preserving_base(full, seed):
    rng = np.random.default_rng(seed); keep = []
    for chrom, g in full.groupby("chromosome"):
        lead_pos = g.loc[g["p_value"] < SIG, "base_pair_location"].values
        if not len(lead_pos): continue
        pos = g["base_pair_location"].values; mask = np.zeros(len(g), bool)
        for sp in lead_pos: mask |= np.abs(pos - sp) <= LOCUS_KB
        keep.append(g[mask])
    neigh = pd.concat(keep) if keep else full.iloc[:0]
    rest = full.drop(index=neigh.index)
    bg = rest.iloc[rng.choice(len(rest), min(BG, len(rest)), replace=False)]
    return pd.concat([neigh, bg]).drop_duplicates(subset=["variant_id"]).reset_index(drop=True)


def plant(w, rng, chrom, lo, hi, k, pmin, pmax):
    j = rng.choice(len(w), k, replace=False)
    w.loc[j, "chromosome"] = chrom
    w.loc[j, "base_pair_location"] = rng.integers(lo, hi, k)
    w.loc[j, "p_value"] = np.geomspace(pmin, pmax, k)
    return [w.loc[t, "variant_id"] for t in j]


def build(full, issue, seed):
    rng = np.random.default_rng(seed)
    w = locus_preserving_base(full, seed)
    real = greedy_loci(standard_qc(w))                       # the 2 real loci
    ref_leads = [{"chromosome": L["chromosome"], "lead_pos": L["lead_pos"], "lead_pval": L["lead_pval"]} for L in real]
    correct_n = len(real); affected = []; extra = {}
    top = min(real, key=lambda L: L["lead_pval"]) if real else {"chromosome": 5, "lead_pos": 586509}

    if issue == "clean":
        pass
    elif issue == "masked_secondary":
        sec = top["lead_pos"] + 300_000
        affected = plant(w, rng, top["chromosome"], sec - 20_000, sec + 20_000, 8, 1e-11, 1e-8)
        extra = {"masked_locus": {"chromosome": top["chromosome"], "primary_lead_pos": top["lead_pos"],
                                  "secondary_lead_pos": sec, "expected_n_independent_signals": 2}}
    elif issue == "mega_locus":
        affected = plant(w, rng, 6, 30_000_000, 32_000_000, 250, 1e-20, 1e-8)   # long-range-LD region
        extra = {"mega_region": {"chromosome": 6, "start": 30_000_000, "end": 32_000_000, "expected_loci_in_region": 1}}
        ref_leads = ref_leads + [{"chromosome": 6, "lead_pos": 31_000_000, "lead_pval": 1e-20}]
        correct_n = len(real) + 1
    elif issue == "pvalue_underflow":
        near = w[(w["chromosome"] == top["chromosome"])
                 & ((w["base_pair_location"] - top["lead_pos"]).abs() <= 50_000)].index
        w.loc[near, "p_value"] = 0.0
        extra = {"underflow_true_lead": {"chromosome": top["chromosome"], "lead_pos": top["lead_pos"]}}
    elif issue == "threshold_edge":
        affected = plant(w, rng, 9, 40_000_000, 40_300_000, 20, 1e-6, 5e-6)      # suggestive, NOT genome-wide
        extra = {"suggestive_decoy_region": {"chromosome": 9, "start": 40_000_000, "end": 40_300_000}}
    elif issue == "scattered_fake_loci":
        # ~15 ISOLATED singleton "hits" (each far from others & from the real loci) -> fake singleton loci.
        # Tell: a real locus has MANY nearby significant variants; a lone singleton is likely an artifact.
        for _ in range(15):
            j = int(rng.integers(0, len(w)))
            w.loc[j, "chromosome"] = int(rng.integers(1, 23))
            w.loc[j, "base_pair_location"] = int(rng.integers(1_000_000, 200_000_000))
            w.loc[j, "p_value"] = float(rng.uniform(1e-8, 4e-8))
            affected.append(w.loc[j, "variant_id"])
        extra = {"n_fake_singletons": 15}                                        # correct = report only the 2 real loci

    gt = {"world_label": issue, "issue_type": "none" if issue == "clean" else issue, "issue_present": issue != "clean",
          "affected_entities": affected, "reference_leads": ref_leads, "correct_n_loci": correct_n,
          "sig_threshold": SIG, "locus_kb": LOCUS_KB,
          "trait_context": "cystic fibrosis lung disease severity", **extra}
    return w.reset_index(drop=True), gt


if __name__ == "__main__":
    NP = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    OUT = sys.argv[2] if len(sys.argv) > 2 else "results/gwas_task2_run"
    os.makedirs(f"{OUT}/data", exist_ok=True)
    full = load_clean_full()
    print(f"substrate {len(full)} variants, {(full['p_value']<SIG).sum()} genome-wide-sig")
    man, cell = [], 0
    for issue in ISSUES:
        for r in range(NP):
            w, gt = build(full, issue, det_seed("gwas_task2_v2", issue, r))
            p = f"{OUT}/data/cell{cell:03d}.tsv.gz"; w.to_csv(p, sep="\t", index=False, compression="gzip")
            man.append({"cell": cell, "task": "gwas_lead_snp_locus", "n_rows": len(w),
                        "agent_input": p, "agent_output": f"{OUT}/out_cell{cell:03d}.json", **gt})
            cell += 1
    json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)
    from collections import Counter
    print(f"wrote {cell} worlds -> {OUT}  {dict(Counter(m['world_label'] for m in man))}")
    for m in man:
        if m["cell"] % NP == 0:
            sp = {k: v for k, v in m.items() if k in ("masked_locus", "mega_region", "underflow_true_lead",
                                                      "suggestive_decoy_region", "n_fake_singletons")}
            print(f"  [{m['world_label']:<20}] rows={m['n_rows']:<6} correct_n_loci={m['correct_n_loci']}  {sp}")
