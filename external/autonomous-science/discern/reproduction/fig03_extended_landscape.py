#!/usr/bin/env python3
"""Eight-model reporting extension. Separate stage rows preserve 7.5pt text at 5.5in.

Do not modify the original six-model extracts, F03, or seven-model figure. Grid and
track means include both completed extensions; the task-ceiling strip stays six-model.
"""
import csv
import json
from pathlib import Path
import statistics as st
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import fig_common as C

ROOT = Path(__file__).resolve().parent
LEVELS = ("L1", "L2", "L3")
MODELS = [*C.MODEL_ORDER, "glm-5.3", "gpt-6-astra"]
NAMES = {**C.FULL, "glm-5.3": "GLM-5.3", "gpt-6-astra": "GPT-6 Astra"}
SHORT = {**C.SHORT, "gpt-5.6-sol": "GPT-5.6\nSol", "glm-5.2": "GLM-5.2", "glm-5.3": "GLM-5.3", "gpt-6-astra": "GPT-6\nAstra"}
KEY = {"GWAS": "GWAS", "ClinVar": "clinvar", "scRNA": "scRNA", "CRISPR": "crispr_screen", "Enhancer": "enhancer_activity", "Histone": "hist_gene_exp", "Protein": "protein_ddg", "Bulk RNA": "bulk_rnaseq"}
rows = [r for r in C.load("fig_data_levels.csv") if not r["family"]]
fs = json.loads((ROOT / "results/final_scores.json").read_text())["track_aggregation"]
for model in ("glm-5.3", "gpt-6-astra"):
    with (ROOT / f"results/new_models/{model}_levels.csv").open() as f:
        extra = list(csv.DictReader(f))
    assert len(extra) == 24
    for r in extra:
        r["score_pct"] = float(r["score_pct"])
    rows += extra
    report = json.loads((ROOT / f"results/new_models/ROLLUP_{model}.json").read_text())
    for t in report["tracks"].values():
        fs[t["canonical_key"]][model] = t
val = {(r["track_display"], r["level"], r["model"]): r["score_pct"] for r in rows}
assert len(val) == 192
geo = {t: st.mean(fs[key][m]["track_geo"] for m in MODELS) * 100/3 for t,key in KEY.items()}
tracks = sorted(geo, key=lambda t: -geo[t])
means = {(t,l): st.mean(val[t,l,m] for m in MODELS) for t in tracks for l in LEVELS}
COLORS = {"L1": "#255E92", "L2": "#CE8A2E", "L3": "#2A7A50"}
ramps = {l: LinearSegmentedColormap.from_list(l,["#f5f7fa",c]) for l,c in COLORS.items()}
fig, ax = plt.subplots(figsize=(5.5,5.65))
ax.set_position([0,0,1,1]); ax.set_xlim(0,5.5); ax.set_ylim(0,5.65); ax.axis("off")
XL,CW,RH = .92,.49,.14
for i,m in enumerate(MODELS):
    ax.text(XL+(i+.5)*CW,5.47,SHORT[m],ha="center",va="center",fontsize=7.5,color=C.INK)
ax.text(.02,5.47,"Track / stage",fontsize=7.5,va="center",color=C.INK2)
MX,MW = 4.99,.43
ax.text(MX+MW/2,5.51,"track mean",fontsize=7.5,ha="center",color=C.INK2)
for tick in (30,60,90):
    ax.text(MX+MW*(tick-30)/60,5.34,str(tick),fontsize=6.5,ha="center",color=C.INK3)
y = 5.28
cells = []
for t in tracks:
    mid = y-1.5*RH
    ax.text(.02,mid,t,fontsize=7.5,fontweight="bold",va="center",color=C.INK)
    for l in LEVELS:
        cy=y-RH/2
        ax.text(.82,cy,l,fontsize=7.5,ha="right",va="center",color=COLORS[l])
        for i,m in enumerate(MODELS):
            v=val[t,l,m]
            ax.add_patch(plt.Rectangle((XL+i*CW+.012,y-RH+.007),CW-.024,RH-.014,facecolor=ramps[l](v/100),edgecolor="none"))
            ax.text(XL+(i+.5)*CW,cy,f"{v:.0f}",ha="center",va="center",fontsize=7.5,color="white" if v>=70 and l!='L2' else C.INK)
            cells.append({"row_type":"level_cell","track":t,"level":l,"model":NAMES[m],"score_pct":v,"track_stage_mean_pct":means[t,l],"track_geo_pct":geo[t]})
        y-=RH
    for tick in (30,60,90):
        x=MX+MW*(tick-30)/60
        ax.plot([x,x],[y,y+3*RH],color=C.GRID,lw=.6,zorder=0)
    for l in LEVELS:
        ax.scatter(MX+MW*(means[t,l]-30)/60,mid,s=13,color=COLORS[l],edgecolor="white",linewidth=.4)
    x=MX+MW*(geo[t]-30)/60
    ax.plot([x,x],[mid-.07,mid+.07],lw=1.0,color=C.INK2)
    y-=.055
ax.text(.02,y-.075,"Eight models: task outcomes at the 100-point ceiling",fontsize=7.5,fontweight="bold",color=C.INK)
for i,(l,file,col) in enumerate((("L1","fig_data_l1_8models.csv","score"),("L2","fig_data_l2_8models.csv","score"),("L3","fig_data_l3_8models.csv","composite"))):
    eligible=[r for r in C.load(file) if r.get("state")!='CONFOUNDED-EXCLUDED' and r[col] is not None]
    n=sum(r[col]>=3 for r in eligible);d=len(eligible);cy=y-.24-i*.19
    ax.text(.81,cy,l,fontsize=7.5,ha="right",va="center",color=COLORS[l])
    ax.add_patch(plt.Rectangle((XL,cy-.045),2.3,.09,facecolor="#f2f4f7"))
    ax.add_patch(plt.Rectangle((XL,cy-.045),2.3*n/d,.09,facecolor=COLORS[l]))
    ax.text(3.4,cy,f"{n}/{d}   {100*n/d:.1f}%",fontsize=7.5,va="center",color=C.INK2)
    cells.append({"row_type":"task_ceiling","level":l,"ceiling_n":n,"ceiling_d":d,"note":"eight-model recorded task outcomes"})
perfect=sum(v>=100 for v in val.values())
ax.text(.02,y-.80,f"{perfect}/192 track-stage means reach 100 (GLM-5.3, Protein L1). Neutral ticks: track chain score.",fontsize=6.5,color=C.INK3)
C.save(fig,"F03_chain_landscape_8models",cells,["row_type","track","level","model","score_pct","track_stage_mean_pct","track_geo_pct","ceiling_n","ceiling_d","note"])
