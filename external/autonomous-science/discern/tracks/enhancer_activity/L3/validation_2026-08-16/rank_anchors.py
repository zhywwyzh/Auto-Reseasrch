import sys; sys.path.insert(0,"tracks/enhancer_activity/L2")
import numpy as np, pandas as pd, l2_common as C
df=C.load_klein(); piv=df.pivot_table("enrichment_score","family","species",aggfunc="mean")
dfz=df.copy(); dfz["z"]=C.per_species_z(dfz); pivz=dfz.pivot_table("z","family","species",aggfunc="mean")
SP=C.PHYLO_ORDER  # great apes -> OWM -> NWM order
rank={s:i for i,s in enumerate(SP)}
# clade labels by phylo position
def clade_of(species_set):
    idx=sorted(rank[s] for s in species_set if s in rank)
    if not idx: return "?"
    # contiguous?
    contig = idx==list(range(idx[0],idx[-1]+1))
    names={0:"human",1:"chimp",2:"gorilla",3:"orang",4:"gibbon",5:"vervet",6:"baboon",7:"rhesus",8:"crab-mac",9:"marmoset",10:"squirrelMk"}
    span=f"{names.get(idx[0])}..{names.get(idx[-1])}" if len(idx)>1 else names.get(idx[0])
    return ("CONTIG " if contig else "split ")+span

real_turn=C.turnover_set(df) & C.clade_robust_turnover(df)
cand=[f for f in real_turn if piv.loc[f].dropna().shape[0]>=8]
rows=[]
for f in cand:
    a=piv.loc[f].dropna()
    # high group = species clearly above the family's low mode. Use a gap split at the largest jump in sorted values.
    v=a.sort_values(ascending=False)
    diffs=v.values[:-1]-v.values[1:]
    cut=int(np.argmax(diffs))+1           # top `cut` = high group
    high=set(v.index[:cut]); low=set(v.index[cut:])
    sep=v.values[:cut].mean()-v.values[cut:].mean()
    # clade consistency: is the high group a contiguous clade?
    hi_idx=sorted(rank[s] for s in high if s in rank)
    contig = hi_idx==list(range(hi_idx[0],hi_idx[-1]+1)) if hi_idx else False
    rows.append((f,len(a),round(sep,2),len(high),contig,clade_of(high),round(pivz.loc[f,v.index[0]],2),round(v.values[0],2)))
R=pd.DataFrame(rows,columns=["family","n","separation","n_high","clade_contig","high_clade","z_lead","peak"])
R=R.sort_values(["clade_contig","separation"],ascending=[False,False])
pd.set_option("display.width",200)
print(R.to_string(index=False))
