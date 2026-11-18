"""bulk_rnaseq L3 — build the INJECTED DE table for cf_mhc2_injected (Route 2).

MUST be run in the bulk build env (has PyDESeq2):
    ~/miniconda3/envs/bulkl2/bin/python tracks/bulk_rnaseq/L3/build_injection.py

INJECTION DISCIPLINE (L3_DESIGN "the two admissible routes"): scale the UPSTREAM RAW COUNTS for the MHC
class-II module in the COVID samples, then RE-RUN THE REAL SCORER (l2_common.run_deseq, the same call that
produced golden_de.csv). No log2FoldChange is ever hand-edited. Locality and coherence are ASSERTED here, so a
future edit that breaks them crashes instead of shipping a detectable world.

WHY THE WHOLE MODULE, NOT A FEW GENES (measured 2026-08-22): a 9-gene subset FAILED the local-peer check --
it left HLA-DMB (-0.612, padj 8e-5) DOWN while raising its obligate heterodimer partner HLA-DMA, and left the
DQA2/DQB2 paralogs at -1.92/-1.42 while raising DQA1/DQB1. Chemically incoherent and detectable; the same
failure class that killed protein's V54I anchor. A UNIFORM count factor over the FULL module shifts every gene
by the same constant in log2 space, so each gene's position RELATIVE to its peers is preserved exactly.

MEASURED RESULT (factor 2.2, +1.137 log2): size-factor drift max 0.0005; off-target log2FC drift over 17,910
genes max 0.0010 / mean 0.00067; zero genes >0.10; zero sign flips among baseline-significant genes.
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tracks/bulk_rnaseq/L2"))
import l2_common as C

OUT = os.path.join(HERE, "injected"); os.makedirs(OUT, exist_ok=True)
FACTOR = 2.2                       # -> +1.137 log2 uniform shift on the module
MHC2 = ["HLA-DRA", "HLA-DRB1", "HLA-DRB5", "HLA-DPA1", "HLA-DPB1", "HLA-DPB2",
        "HLA-DQA1", "HLA-DQA2", "HLA-DQB1", "HLA-DQB2",
        "HLA-DMA", "HLA-DMB", "HLA-DOA", "HLA-DOB", "CD74", "CIITA"]
MAX_OFF_DRIFT = 0.01               # off-target |dlog2FC| must stay far below any call-changing level


def main():
    counts, meta, gm = C.load_all()
    Xde, Mde = C.de_cohort(counts, meta)
    sym = gm["symbol"]
    target = [i for g in MHC2 for i in sym[sym == g].index if i in Xde.index]
    assert len(target) == len(MHC2), f"expected {len(MHC2)} module ids, mapped {len(target)}"
    covid = Mde.index[Mde["condition"] == "COVID-19"]

    base, sf0 = C.run_deseq(Xde, Mde, ["condition"])            # the REAL scorer, unmodified data
    Xi = Xde.copy()
    Xi.loc[target, covid] = (Xi.loc[target, covid] * FACTOR).round().astype(int)
    inj, sf1 = C.run_deseq(Xi, Mde, ["condition"])              # the REAL scorer, modified counts

    # ---- LOCALITY: only the module may move ----
    j = base[["log2FoldChange"]].join(inj[["log2FoldChange"]], lsuffix="_b", rsuffix="_i").dropna()
    off = j.drop(index=[t for t in target if t in j.index])
    drift = (off.log2FoldChange_i - off.log2FoldChange_b).abs()
    sf_drift = float(np.abs(np.asarray(sf1) / np.asarray(sf0) - 1).max())
    flips = [g for g in base[base.padj < 0.05].index
             if g in off.index and np.sign(j.loc[g, "log2FoldChange_b"]) != np.sign(j.loc[g, "log2FoldChange_i"])]
    assert drift.max() < MAX_OFF_DRIFT, f"off-target leak: max drift {drift.max():.4f}"
    assert not flips, f"{len(flips)} off-target sign flips"

    # ---- COHERENCE: the module must move as one, and its regulator with it ----
    res = inj.join(sym).set_index("symbol")
    up_sig = [g for g in MHC2 if res.loc[g, "padj"] < 0.05 and res.loc[g, "log2FoldChange"] > 0]
    dn_sig = [g for g in MHC2 if res.loc[g, "padj"] < 0.05 and res.loc[g, "log2FoldChange"] < 0]
    assert not dn_sig, f"module incoherent — still significantly DOWN: {dn_sig}"
    assert res.loc["CIITA", "log2FoldChange"] > 0, "CIITA (class-II master regulator) must move with the module"
    for a, b in [("HLA-DMA", "HLA-DMB"), ("HLA-DQA1", "HLA-DQB1"), ("HLA-DPA1", "HLA-DPB1")]:
        assert np.sign(res.loc[a, "log2FoldChange"]) == np.sign(res.loc[b, "log2FoldChange"]), \
            f"heterodimer {a}/{b} split — chemically incoherent"

    out = os.path.join(OUT, "de_mhc2_injected.csv")
    inj.join(sym).to_csv(out)
    print(f"[inject] module n={len(target)}  factor={FACTOR}  "
          f"added {int((Xde.loc[target, covid]*(FACTOR-1)).sum().sum()):,} counts")
    print(f"[inject] LOCALITY  size-factor drift {sf_drift:.5f} | off-target max {drift.max():.5f} "
          f"mean {drift.mean():.6f} | >0.10: {int((drift>0.10).sum())} | sign flips: {len(flips)}")
    print(f"[inject] COHERENCE {len(up_sig)}/{len(MHC2)} significantly UP, 0 significantly down, "
          f"CIITA {res.loc['CIITA','log2FoldChange']:+.3f}, heterodimers aligned")
    print(f"[inject] -> {out}")
    print(res.loc[MHC2, ["log2FoldChange", "padj"]].round(3).to_string())


if __name__ == "__main__":
    main()
