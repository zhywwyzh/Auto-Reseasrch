import sys; sys.path.insert(0,"tracks/enhancer_activity/L2")
import numpy as np, pandas as pd, l2_common as C
df=C.load_klein(); piv=df.pivot_table("enrichment_score","family","species",aggfunc="mean")
SP=C.PHYLO_ORDER
APES=["hg38","panTro5","gorGor3","ponAbe2","nomLeu3"]; MONK=["chlSab2","papAnu2","rheMac3","macFas5","calJac3","saiBol1"]
def apemonk(a):
    ap=[a[s] for s in APES if s in a.index and not np.isnan(a[s])]
    mo=[a[s] for s in MONK if s in a.index and not np.isnan(a[s])]
    if len(ap)<3 or len(mo)<3: return np.nan
    return float(np.mean(ap)-np.mean(mo))
REAL="15:65108751-65108937"; obs=apemonk(piv.loc[REAL]); print(f"REAL {REAL} ape-vs-monkey contrast = {obs:.2f}")

# (1) genome-wide max ape-monkey |contrast| permutation null (family-wise)
rng=np.random.default_rng(31); vals=df["enrichment_score"].values; nullmax=[]
for _ in range(500):
    d=df.copy(); d["enrichment_score"]=rng.permutation(vals)
    p=d.pivot_table("enrichment_score","family","species",aggfunc="mean")
    c=[abs(apemonk(p.loc[f])) for f in p.index]; nullmax.append(np.nanmax(c))
nullmax=np.array(nullmax)
print(f"(1) FAMILY-WISE null of max|ape-monkey contrast|: mean={nullmax.mean():.2f} p95={np.quantile(nullmax,.95):.2f} max={nullmax.max():.2f}")
print(f"     REAL exceeds family-wise p95? {obs>np.quantile(nullmax,.95)}")

# (2) per-family permutation p: shuffle the species labels WITHIN this family's row values many times
row=piv.loc[REAL].dropna(); v=row.values; labels=list(row.index)
rng2=np.random.default_rng(7); ge=0; N=5000
for _ in range(N):
    perm=rng2.permutation(v); a=pd.Series(perm,index=labels)
    if abs(apemonk(a))>=abs(obs): ge+=1
print(f"(2) WITHIN-family label-permutation p (2-sided) = {ge/N:.4f}  (does the ape/monkey partition beat random partitions of its own 10 values?)")

# (3) how many families have a LARGER ape-monkey contrast than REAL? (rank among real families)
allc=pd.Series({f:apemonk(piv.loc[f]) for f in piv.index}).dropna()
print(f"(3) REAL rank by ape-monkey contrast: {(allc>obs).sum()+1} of {len(allc)}  (top {100*((allc>obs).sum()+1)/len(allc):.1f}%)")
