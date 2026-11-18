"""LEVEL 2 - Task A: GWAS Signal EDA (disease-aware). Inject SIGNAL-LEVEL confounds into a real
CF-lung-severity GWAS that all PASS basic validity checks, so the agent must reason about the GWAS
statistics (lambda_GC, QQ/p-value shape, sig counts, beta distribution) and about DISEASE PLAUSIBILITY
(this is a severity/modifier trait -> a peak at CFTR itself is a red flag).

Worlds: clean, inflation, deflation, null_signal, CFTR_artifact, wrong_locus, batch_concentration.

usage: gwas_signaleda_worlds.py <n_per_issue> <out_dir>
"""
import sys, json, os, hashlib
import numpy as np
import pandas as pd
from scipy.stats import chi2

def det_seed(*p): return int(hashlib.md5("|".join(map(str, p)).encode()).hexdigest()[:8], 16)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gwas_task2_worlds import load_clean_full        # reuse the cleaned real substrate

N = 20000            # variants per world (enough for a stable lambda_GC)
SIG = 5e-8
CFTR = (7, 117_559_590)      # CFTR, chr7q31.2 (GRCh38) — causal CF gene; implausible as a SEVERITY peak
DESERT = (2, 130_000_000)    # gene-poor region — generically implausible top hit
ISSUES = ["clean", "inflation", "deflation", "null_signal", "CFTR_artifact", "wrong_locus", "batch_concentration"]


def lambda_gc(p):
    p = np.clip(np.asarray(p, float), 1e-300, 1.0)
    return float(np.median(chi2.isf(p, 1)) / chi2.isf(0.5, 1))


def rescale_lambda(p, target):
    """Inflate/deflate the chi-square distribution so lambda_GC ~= target."""
    p = np.clip(np.asarray(p, float), 1e-300, 1.0)
    stat = chi2.isf(p, 1)
    factor = target / max(lambda_gc(p), 1e-6)
    return chi2.sf(stat * factor, 1)


def plant_peak(w, rng, chrom, pos, k=25, pmin=1e-15, pmax=1e-10):
    """Overwrite k background variants into a tight, strong peak at (chrom, pos)."""
    j = rng.choice(len(w), k, replace=False)
    w.loc[j, "chromosome"] = chrom
    w.loc[j, "base_pair_location"] = pos + rng.integers(-40_000, 40_000, k)
    w.loc[j, "p_value"] = np.geomspace(pmin, pmax, k)
    return [w.loc[t, "variant_id"] for t in j]


def build(full, issue, seed):
    rng = np.random.default_rng(seed)
    w = full.iloc[rng.choice(len(full), N, replace=False)].copy().reset_index(drop=True)
    affected, status = [], issue
    true_lambda = round(lambda_gc(w["p_value"]), 3)          # lambda of the real sampled signal

    if issue == "clean":
        pass
    elif issue == "inflation":
        target = float(rng.uniform(1.18, 1.30)); w["p_value"] = rescale_lambda(w["p_value"], target); true_lambda = target
    elif issue == "deflation":
        target = float(rng.uniform(0.80, 0.90)); w["p_value"] = rescale_lambda(w["p_value"], target); true_lambda = target
    elif issue == "null_signal":
        w["p_value"] = rng.uniform(0, 1, len(w)); true_lambda = round(lambda_gc(w["p_value"]), 3)
    elif issue == "CFTR_artifact":
        affected = plant_peak(w, rng, *CFTR)
    elif issue == "wrong_locus":
        affected = plant_peak(w, rng, *DESERT)
    elif issue == "batch_concentration":
        # cram many "hits" into one narrow window with near-identical p (technical artifact, not polygenic)
        j = rng.choice(len(w), 60, replace=False)
        w.loc[j, "chromosome"] = 12; w.loc[j, "base_pair_location"] = 50_000_000 + rng.integers(0, 50_000, 60)
        w.loc[j, "p_value"] = 1e-9 * (1 + rng.normal(0, 0.01, 60)).clip(0.5, 1.5)
        affected = [w.loc[t, "variant_id"] for t in j]

    n_sig = int((w["p_value"] < SIG).sum())
    gt = {"world_label": issue, "signal_status": status, "issue_present": issue != "clean",
          "true_lambda_gc": true_lambda, "n_genome_wide_sig": n_sig, "affected_entities": affected,
          "plausible_top_regions": ["chr11p13 (EHF/APIP)", "chr5p15"],
          "implausible_top_region": ({"CFTR_artifact": "CFTR chr7q31.2", "wrong_locus": "chr2 gene desert"}.get(issue)),
          "correct_usability": issue in ("clean",),
          "correct_pvalue_assessment": {"clean": "reasonable", "inflation": "inflated", "deflation": "deflated",
                                        "null_signal": "null", "CFTR_artifact": "suspicious",
                                        "wrong_locus": "suspicious", "batch_concentration": "suspicious"}[issue]}
    return w, gt


if __name__ == "__main__":
    NP = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    OUT = sys.argv[2] if len(sys.argv) > 2 else "results/gwas_signaleda_run"
    os.makedirs(f"{OUT}/data", exist_ok=True)
    full = load_clean_full()
    print(f"substrate {len(full)} variants, base lambda_GC={lambda_gc(full['p_value']):.3f}")
    man, cell = [], 0
    for issue in ISSUES:
        for r in range(NP):
            w, gt = build(full, issue, det_seed("gwas_signaleda", issue, r))
            p = f"{OUT}/data/cell{cell:03d}.tsv.gz"
            w.to_csv(p, sep="\t", index=False, compression="gzip")
            man.append({"cell": cell, "task": "gwas_signal_eda", "n_rows": len(w),
                        "agent_input": p, "agent_output": f"{OUT}/out_cell{cell:03d}.json",
                        "trait_context": "cystic fibrosis lung disease severity",
                        "unavailable_gold_standard_checks": ["LDSC intercept (needs LD panel)",
                                                             "allele-freq vs reference panel (needs 1000G/gnomAD)"],
                        **gt})
            cell += 1
    json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)
    from collections import Counter
    print(f"wrote {cell} worlds -> {OUT}  {dict(Counter(m['world_label'] for m in man))}")
    for m in man:
        if m["cell"] % NP == 0:
            print(f"  [{m['world_label']:<20}] lambda_GC={m['true_lambda_gc']:<5} n_sig={m['n_genome_wide_sig']:<4} "
                  f"assess={m['correct_pvalue_assessment']:<11} implausible={m['implausible_top_region']}")
