"""LEVEL 2 - Task B: TWAS worlds. Each world is a GWAS the agent must harmonize into a TWAS model's
variant space and run a TWAS on. Corruptions break the harmonization SILENTLY (a careless run still yields
a non-empty CSV that used ~0 model SNPs). Golden truth = Mario's clean S-PrediXcan output.

We start from the (already model-overlapping) summary stats, PARSE the GTEx varID back into raw coordinates,
and hand the agent only raw-looking columns (rsid, chrom, pos, alleles, beta, p) — the agent must REBUILD
the model's varID (chr_pos_ref_alt_b38) itself.

Worlds: clean · build_mismatch (hg19 positions) · allele_order_swap · id_only (coords hidden).

usage: gwas_twas_worlds.py <n_per_issue> <out_dir>
"""
import sys, json, os, hashlib
import numpy as np
import pandas as pd

def det_seed(*p): return int(hashlib.md5("|".join(map(str, p)).encode()).hexdigest()[:8], 16)

READY = "/workspace/discern-benchmark/tracks/cf_gwas/data/gwas_cys_fib/metaxcan_ready/csfb_for_spredixcan_varid.tsv.gz"
GOLD = "/workspace/discern-benchmark/tracks/cf_gwas/L2/twas_cys_fib/csfb_Lung_spredixcan_varid.csv"
ISSUES = ["clean", "build_mismatch", "allele_order_swap", "id_only"]


def load_raw():
    """Parse the GTEx panel_variant_id back into raw coordinate columns."""
    d = pd.read_csv(READY, sep="\t", compression="infer", low_memory=False)
    parts = d["panel_variant_id"].str.split("_", expand=True)      # chr5 _ 568029 _ T _ C _ b38
    d["chromosome"] = parts[0].str.replace("chr", "", regex=False)
    d["base_pair_location"] = pd.to_numeric(parts[1], errors="coerce")
    # ref=non_effect (other), alt=effect  (chr_pos_ref_alt)
    out = pd.DataFrame({"rsid": d["rsid"], "chromosome": d["chromosome"],
                        "base_pair_location": d["base_pair_location"].astype("Int64"),
                        "effect_allele": d["effect_allele"], "other_allele": d["non_effect_allele"],
                        "beta": d["beta"], "p_value": d["pvalue"], "frequency": d["frequency"]})
    return out.dropna(subset=["base_pair_location"]).reset_index(drop=True)


def build(raw, issue, seed):
    rng = np.random.default_rng(seed); w = raw.copy(); note = {}
    if issue == "clean":
        pass
    elif issue == "build_mismatch":
        # positions look like a different genome build -> rebuilt varIDs won't match the b38 model
        w["base_pair_location"] = (w["base_pair_location"].astype(int) + rng.integers(-6000, -2000)).astype("Int64")
        note = {"note": "coordinates are NOT GRCh38 (build mismatch)"}
    elif issue == "allele_order_swap":
        w["effect_allele"], w["other_allele"] = w["other_allele"].copy(), w["effect_allele"].copy()
        note = {"note": "effect/other alleles swapped"}
    elif issue == "id_only":
        w = w[["rsid", "beta", "p_value"]].copy()                 # coords + alleles hidden -> must map via rsID
        note = {"note": "only rsIDs available, no coordinates/alleles"}
    return w.reset_index(drop=True), note


if __name__ == "__main__":
    NP = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    OUT = sys.argv[2] if len(sys.argv) > 2 else "results/gwas_twas_run"
    os.makedirs(f"{OUT}/data", exist_ok=True)
    raw = load_raw()
    print(f"raw GWAS (model-overlapping): {len(raw)} variants | golden truth: {GOLD}")
    man, cell = [], 0
    for issue in ISSUES:
        for r in range(NP):
            w, note = build(raw, issue, det_seed("gwas_twas", issue, r))
            p = f"{OUT}/data/cell{cell:03d}.tsv.gz"; w.to_csv(p, sep="\t", index=False, compression="gzip")
            man.append({"cell": cell, "task": "gwas_twas", "world_label": issue,
                        "issue_type": "none" if issue == "clean" else issue, "issue_present": issue != "clean",
                        "n_rows": len(w), "agent_input": p, "agent_output": f"{OUT}/out_cell{cell:03d}.json",
                        "golden_truth": GOLD, "tissue": "Lung", "trait_context": "cystic fibrosis lung disease severity",
                        "correct_action": {"clean": "build varID from coords, run summary-based TWAS",
                                           "build_mismatch": "detect build mismatch; use rsID key or liftover",
                                           "allele_order_swap": "harmonize alleles to model ref/alt order",
                                           "id_only": "map rsID to the model's variant key"}[issue], **note})
            cell += 1
    json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)
    from collections import Counter
    print(f"wrote {cell} worlds -> {OUT}  {dict(Counter(m['world_label'] for m in man))}")
    for m in man:
        if m["cell"] % NP == 0:
            print(f"  [{m['world_label']:<18}] rows={m['n_rows']:<6} cols={'rsid-only' if m['world_label']=='id_only' else 'full'} "
                  f"action={m['correct_action']}")
