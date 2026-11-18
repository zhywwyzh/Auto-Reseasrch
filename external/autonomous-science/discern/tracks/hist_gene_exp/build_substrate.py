"""Generalized substrate builder for the scalar_feature_expression family:
any K562 ChIP/accessibility bigWig -> per-gene table (feature + expression + length),
using gencode V29 promoter TSS aggregation joined to real K562 RNA-seq.

usage: build_substrate.py <bigWig> <feature_col_name> <out.csv>
"""
import csv, gzip, sys
import numpy as np
import pyBigWig

BW, COL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
GTF = "realdata/gencode.v29.gtf.gz"; RNA = "realdata/k562_rna.tsv"; PROM = 1000

tss = {}
with gzip.open(GTF, "rt") as fh:
    for line in fh:
        if line.startswith("#"): continue
        f = line.split("\t")
        if f[2] != "gene": continue
        gid = f[8].split('gene_id "')[1].split('"')[0]
        tss[gid] = (f[0], int(f[3]) if f[6] == "+" else int(f[4]))

expr = {}
for r in csv.DictReader(open(RNA), delimiter="\t"):
    if r["gene_id"].startswith("ENSG") and float(r["TPM"]) > 0:
        expr[r["gene_id"]] = (float(r["TPM"]), float(r["length"]))

bw = pyBigWig.open(BW); chroms = set(bw.chroms())
rows = []
for gid, (tpm, length) in expr.items():
    if gid not in tss: continue
    chrom, t = tss[gid]
    if chrom not in chroms: continue
    try: val = bw.stats(chrom, max(0, t - PROM), t + PROM, type="mean")[0]
    except Exception: val = None
    rows.append((gid, float(val or 0.0), np.log1p(tpm), np.log1p(length)))
bw.close()

acc = np.log1p(np.array([r[1] for r in rows])); ex = np.array([r[2] for r in rows])
print(f"[{COL}] {len(rows)} genes; REAL corr({COL}, expression) = {np.corrcoef(acc, ex)[0,1]:+.3f}")
with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["gene_id", COL, "gene_expression", "gene_length"])
    for gid, a, e, l in rows:
        w.writerow([gid, round(float(np.log1p(a)), 4), round(float(e), 4), round(float(l), 4)])
print(f"[out] {OUT}")
