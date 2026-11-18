import sys; sys.path.insert(0,"tracks/enhancer_activity/L2")
import numpy as np, pandas as pd, l2_common as C
df=C.load_klein(); cons=C.family_conservation(df)
piv=df.pivot_table("enrichment_score","family","species",aggfunc="mean")
dfz=df.copy(); dfz["z"]=C.per_species_z(dfz); pivz=dfz.pivot_table("z","family","species",aggfunc="mean")
nsp=df.groupby("family").species.nunique()
SP=C.PHYLO_ORDER

real_turn = C.turnover_set(df) & C.clade_robust_turnover(df)
broad=[f for f in real_turn if nsp.get(f,0)>=8]
broad=sorted(broad, key=lambda f: -(piv.loc[f].max()-piv.loc[f].min()))
print(f"ROUTE C — {len(broad)} real-turnover families (n>=8), sorted by range:\n")
for f in broad:
    a=piv.loc[f]; v=a.dropna().sort_values(ascending=False)
    lead=v.index[0]; z=pivz.loc[f,lead]
    rng=v.iloc[0]-v.iloc[-1]
    vec=" ".join(f"{s[:6]}={a[s]:+.1f}" for s in SP if s in a.index and not np.isnan(a[s]))
    print(f"{f:22s} n={int(nsp[f])} range={rng:4.2f} lead={lead}(z={z:+.2f}) cons_pctl={(cons.cons<cons.cons.get(f,0)).mean():.0%}")
    print(f"    {vec}")
