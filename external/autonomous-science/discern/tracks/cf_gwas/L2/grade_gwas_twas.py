"""LEVEL 2 - Task B grader: TWAS vs golden truth (Design A — the agent already ran the tool). Reads the
agent's output CSV, compares to Mario's clean S-PrediXcan output, and scores whether the harmonization was
correct (SNP usage) and the gene-level result is right (z-score correlation, top-gene recall, direction).

Silent-failure detection: a non-empty CSV that used ~0 model SNPs (or has flipped signs) scores low.

usage: grade_gwas_twas.py <run_dir> <suffix>
"""
import json, sys, os
import numpy as np
import pandas as pd
from collections import Counter

RUN, SUF = sys.argv[1], sys.argv[2]
man = json.load(open(f"{RUN}/manifest.json"))
TOP_N = 20

def load_twas(path):
    try:
        d = pd.read_csv(path)
        if "gene" in d.columns and "zscore" in d.columns:
            for c in ("zscore", "pvalue", "n_snps_used"):
                if c in d.columns: d[c] = pd.to_numeric(d[c], errors="coerce")
            return d
    except Exception:
        pass
    return None

def used_metaxcan(m):
    """Did the agent invoke the provided field-standard tool (S-PrediXcan / MetaXcan) rather than HAND-ROLL the
    TWAS math itself? A correct hand-rolled result is capped below tool use (non-standard / error-prone)."""
    tp = m["agent_output"].replace(".json", f"_{SUF}.trace.json")
    if not os.path.exists(tp): return True                      # unknown -> don't penalize
    code = " ".join(c.get("code", "") for c in json.load(open(tp)).get("code_trace", [])).lower()
    return ("spredixcan" in code) or ("metaxcan" in code)

rows = []
for m in man:
    op = m["agent_output"].replace(".json", f"_{SUF}.json")
    if not os.path.exists(op): continue
    out = json.load(open(op))
    gold = pd.read_csv(m["golden_truth"])
    ag = load_twas(str(out.get("output_path", "")))

    if ag is None:
        rows.append({"cell": m["cell"], "world": m["world_label"], "state": "NO-OUTPUT", "score": 0,
                     "z_corr": None, "snp_frac": 0.0, "top_recall": 0.0, "sign_ok": None,
                     "agent_snps": out.get("n_snps_used_total")}); continue

    g = gold.dropna(subset=["zscore"]); a = ag.dropna(subset=["zscore"])
    merged = g.merge(a, on="gene", suffixes=("_g", "_a"))
    z_corr = float(np.corrcoef(merged["zscore_g"], merged["zscore_a"])[0, 1]) if len(merged) > 5 else None
    snp_frac = (float(a["n_snps_used"].sum()) / max(float(g["n_snps_used"].sum()), 1)
                if "n_snps_used" in a.columns else (len(a) / max(len(g), 1)))
    top_gold = set(gold.nsmallest(TOP_N, "pvalue")["gene"]); top_ag = set(ag.nsmallest(TOP_N, "pvalue")["gene"])
    top_recall = len(top_gold & top_ag) / TOP_N
    sign_ok = (float((np.sign(merged["zscore_g"]) == np.sign(merged["zscore_a"])).mean()) >= 0.9
               if len(merged) > 5 else None)

    # score: reproduced the golden truth?  3 = high z-corr + good SNP usage + right direction
    if z_corr is not None and z_corr >= 0.95 and snp_frac >= 0.5 and sign_ok:
        state, score = ("TWAS-CORRECT", 3) if used_metaxcan(m) else ("TWAS-CORRECT-HANDROLLED", 2)
    elif z_corr is not None and z_corr >= 0.7 and snp_frac >= 0.25:
        state, score = "TWAS-PARTIAL", 2
    elif snp_frac >= 0.05:
        state, score = "TWAS-WEAK", 1
    else:
        state, score = "TWAS-EMPTY (silent fail)", 0        # ran but ~0 model SNPs matched
    rows.append({"cell": m["cell"], "world": m["world_label"], "state": state, "score": score,
                 "z_corr": None if z_corr is None else round(z_corr, 3), "snp_frac": round(snp_frac, 3),
                 "top_recall": round(top_recall, 2), "sign_ok": sign_ok, "agent_snps": out.get("n_snps_used_total")})

print(f"=== {RUN} — {SUF} (TWAS vs golden truth) ===")
print(f"{'world':<20}{'state':<26}{'score':>6}{'z_corr':>8}{'snp_frac':>9}{'top20':>7}{'sign_ok':>8}")
for r in sorted(rows, key=lambda x: x["world"]):
    print(f"{r['world']:<20}{r['state']:<26}{r['score']:>6}{str(r['z_corr']):>8}{r['snp_frac']:>9}"
          f"{r['top_recall']:>7}{str(r['sign_ok']):>8}")
print(f"\nmean TWAS score: {np.mean([r['score'] for r in rows]):.2f}/3   states: {dict(Counter(r['state'] for r in rows))}")
print(f"silent failures (~0 SNPs matched): {sum(r['state'].startswith('TWAS-EMPTY') for r in rows)}/{len(rows)}")
json.dump(rows, open(f"{RUN}/graded_twas_{SUF}.json", "w"), indent=1)
