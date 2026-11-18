"""Three-panel eight-model L3 view; reuses the audited A/B builder without saving it.

All 176 planned cells shown in C: 172 eligible, three recorded exclusions and one
absent gate exclusion. The original six-model figures are never overwritten.
"""
from pathlib import Path
import collections
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
source = (ROOT / 'fig06_extended_prior_to_yield.py').read_text()
source = source[:source.index('C.save(fig,')]
source = source.replace('SHORT = {**C.SHORT,', 'SHORT = {**C.SHORT, "claude-opus-5": "Opus 5", "glm-5.2": "GLM-5.2", "gpt-5.6-sol": "GPT-5.6-sol",')
source = source.replace('figsize=(5.5, 2.75)', 'figsize=(5.5, 6.3)')
source = source.replace('fig.add_gridspec(1, 2, width_ratios=[1, 1], left=0.135, right=0.955, top=0.86, bottom=0.20,\n                      wspace=0.34)',
    'fig.add_gridspec(2, 2, height_ratios=[1, 1.5], width_ratios=[1, 1], left=0.14, right=0.94, top=0.95, bottom=0.24, hspace=0.55, wspace=0.34)')
source = source.replace('fig.add_subplot(gs[0, 0])', 'fig.add_subplot(gs[0, 0])')
source = source.replace('fig.add_subplot(gs[0, 1])', 'fig.add_subplot(gs[0, 1])')
source = source.replace('np.linspace(0.02, 1.6, 200)', 'np.linspace(0.02, 2.15, 200)')
source = source.replace('marker="D" if new else "o"', 'marker="o"')
source = source.replace('"◆ post-freeze"', '""')  # One-commitment caveat lives in the caption.
exec(compile(source, str(ROOT / 'fig06_extended_prior_to_yield.py'), 'exec'))

allrows = C.load('fig_data_l3_8models.csv')
worlds = sorted({(r['track_display'],r['track'],r['world'],r['is_counterfactual']) for r in allrows},
                key=lambda w:(w[0],w[3],w[2]))
lookup = {(r['track'],r['world'],r['model']):r for r in allrows}
ax = fig.add_subplot(gs[1,:])
ramp=['#edf3ee','#b3d1bc','#619e75','#1b6b50']
export=[]
for i,(display,t,w,cf) in enumerate(worlds):
    for j,m in enumerate(MODELS):
        r=lookup.get((t,w,m)); y=len(MODELS)-j-.5
        excluded=r is None or r['state']=='CONFOUNDED-EXCLUDED'
        n=None if excluded else r['novelty']
        if excluded:
            ax.text(i+.5,y,'×',ha='center',va='center',fontsize=7.5,color=C.INK3)
        else:
            ax.add_patch(plt.Rectangle((i+.05,y-.45),.9,.9,
                facecolor='white' if n is None else ramp[int(n)],
                edgecolor=C.STATE_ABSTENTION if n is None else 'none',
                linewidth=.7,linestyle='--' if n is None else '-'))
            if n == 3:ax.text(i+.5,y,'3',ha='center',va='center',fontsize=7.5,color='white')
        export.append(dict(panel='C',model=m,track=t,world=w,novelty='excluded' if excluded else 'abstained' if n is None else n))
ax.set_xlim(0,22);ax.set_ylim(0,8)
ax.set_yticks([7.5-j for j in range(8)], [SHORT[m] for m in MODELS],fontsize=7.5)
ax.set_xticks([i+.5 for i in range(22)], [('· ' if cf else '▪ ')+w.removeprefix('cf_').replace('_',' ') for _,_,w,cf in worlds],rotation=90,fontsize=6.8)
ax.tick_params(length=0)
for spine in ax.spines.values():spine.set_visible(False)
start=0
for end in range(1,23):
    if end==22 or worlds[end][0]!=worlds[start][0]:
        ax.text((start+end)/2,8.2,worlds[start][0],ha='center',fontsize=6.4)
        start=end
ax.set_title('C   Novelty by world: 6 maxima, 4 in DUSP4',loc='left',fontsize=8,pad=17)
fig.text(.14,.017,'N: 0–3 (light–dark) · dashed: abstained · ×: excluded · ▪ real · · counterfactual',fontsize=6.4,color=C.INK2)
for m in MODELS:
    p,n,nc,ne=HURDLE[m]
    export.append(dict(panel='B',model=m,commit_rate=p,mean_novelty_given_commit=n,
                       n_committed=nc,n_eligible=ne,yield_value=p*n))
C.save(fig,'F06_full_8models',export,['panel','model','track','world','novelty','commit_rate',
           'mean_novelty_given_commit','n_committed','n_eligible','yield_value'])
