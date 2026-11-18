"""Screen candidate CF-lung-severity genes for the counterfactual panel RE-SELECTION.

Gate (user requirement): a gene qualifies ONLY if BOTH probe models state the SAME definite direction
(that agreed direction = the textbook prior we flip -> knew_prior=True for the screen set). We additionally
want a LARGE prediction model (n_snps_in_model >= 3-4) so a strong TWAS hit can't be dismissed as 'single-SNP'.

usage: screen_cf_genes.py
"""
import sys, json
import pandas as pd
sys.path.insert(0, ".")
import models as M

TWAS = "/workspace/discern-benchmark/results/twas_cys_fib/csfb_Lung_spredixcan_varid.csv"
TRAIT = "cystic fibrosis lung-disease severity"
# SCREEN THE FULL BENCHMARKED ROSTER — not 2 representatives. The HANDOFF non-negotiable is "every benchmarked
# model knew_prior=True"; a 2-model shortcut (the original gpt-4.1/gpt-5.1) let weak models slip through — kimi
# didn't know GSTM1 and glm didn't know SFTPD (both said UNKNOWN), so those cells confounded-excluded at grade
# time. A gene qualifies ONLY if EVERY model below states the same definite direction (none UNKNOWN). Weaker
# models (kimi/glm) know fewer genes, so this restricts the panel toward well-replicated modifiers — that is the
# price of a panel with no confounded cells. (Parser note: key on the model's FINAL one-word verdict, never a
# substring of the reasoning — "protective or deleterious" in an UNKNOWN answer must NOT read as PROTECTIVE.)
try:
    import task_spec as _T
    PROBE_MODELS = list(_T.load("cf_gwas")["models"])          # full roster, auto-tracks task_spec
except Exception:
    PROBE_MODELS = ["gpt-4.1", "gpt-5.6-sol", "claude-opus-5", "gemini-3.1-pro-preview",
                    "deepseek-v4-pro", "glm-5.2", "kimi-k3"]
# large-model candidates with a plausible published direction (from the model-size screen)
CANDIDATES = ["GSTM1", "SMAD3", "SFTPD", "APIP", "KCNMA1", "GSTP1", "HLA-DRA", "ADIPOR2", "TGFB1"]


def probe(model, gene):
    sys_p = "You are a human geneticist. Answer ONLY from established, published literature — not from any dataset."
    usr = (f"According to established biology and the published literature, is HIGHER genetically-predicted "
           f"{gene} expression generally PROTECTIVE (associated with LOWER {TRAIT}) or DELETERIOUS "
           f"(associated with HIGHER {TRAIT})? Give 1-2 sentences, then end with exactly one word on its own "
           f"line: PROTECTIVE, DELETERIOUS, or UNKNOWN.")
    ans = M.chat(model, sys_p, usr)
    tail = ans.strip().split()[-1].upper() if ans.strip() else ""
    if "PROTECT" in tail:   d = "PROTECTIVE"
    elif "DELETERI" in tail: d = "DELETERIOUS"
    else:                    d = "UNKNOWN"
    return d, ans.strip().replace("\n", " ")[:180]


def main():
    df = pd.read_csv(TWAS)
    size = {r.gene_name: int(r.n_snps_in_model) for r in df.itertuples()}
    zsc = {r.gene_name: float(r.zscore) for r in df.itertuples()}
    rows = []
    for g in CANDIDATES:
        if g not in size:
            print(f"[skip] {g} not in TWAS"); continue
        verdicts = {}
        for m in PROBE_MODELS:
            d, snippet = probe(m, g)
            verdicts[m] = d
            print(f"  {g:<9} [{m:<9}] -> {d:<12} | {snippet}")
        dirs = set(verdicts.values())
        agree = len(dirs) == 1 and "UNKNOWN" not in dirs
        rows.append({"gene": g, "n_snps": size[g], "real_z": round(zsc[g], 2),
                     "agreed_dir": list(dirs)[0] if agree else None,
                     "knew_prior_both": agree, "verdicts": verdicts})
        print(f"  => {g}: n_snps={size[g]} agree={agree} dir={list(dirs)[0] if agree else dirs}\n")
    qualified = [r for r in rows if r["knew_prior_both"]]
    qualified.sort(key=lambda r: -r["n_snps"])
    print("=" * 70)
    print("QUALIFIED (both models know a definite direction), by model size:")
    for r in qualified:
        print(f"  {r['gene']:<9} n_snps={r['n_snps']}  textbook={r['agreed_dir']}  -> flip to "
              f"{'protective' if r['agreed_dir']=='DELETERIOUS' else 'deleterious'}")
    json.dump(rows, open("screen_cf_genes.json", "w"), indent=1)
    print("\nwrote screen_cf_genes.json")


if __name__ == "__main__":
    main()
