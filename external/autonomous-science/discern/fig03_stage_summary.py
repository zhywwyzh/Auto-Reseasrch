"""Compact Figure 3 from recorded eight-model exports; full matrix is retained.

Dots are equally weighted means across eight models. Lines are observed min-max
ranges, not confidence intervals. The ceiling panel uses the same recorded
task-outcome definitions as the full Figure 3. No scores or runs are modified.
"""
from pathlib import Path
import csv
import hashlib
import json
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results/figures'
MODELS = ['gpt-5.6-sol', 'claude-opus-5', 'kimi-k3', 'glm-5.2',
          'deepseek-v4-pro', 'gpt-4.1', 'glm-5.3', 'gpt-6-astra']
COLORS = {'L1':'#255E92', 'L2':'#CE8A2E', 'L3':'#2A7A50'}
SOURCES = [ROOT/'results'/f'fig_data_{kind}_8models.csv' for kind in ['levels','l1','l2','l3']]


def read(path):
    with path.open() as f: return list(csv.DictReader(f))


def derive():
    rows = [r for r in read(SOURCES[0]) if not r['family']]
    values = {(r['track_display'],r['level'],r['model']):float(r['score_pct']) for r in rows}
    assert len(rows)==len(values)==192
    assert {r['model'] for r in rows}==set(MODELS)
    tracks = {r['track_display'] for r in rows}
    assert len(tracks)==8
    # Preserve the full matrix's track order by descending mean geometric score.
    tracks = sorted(tracks, key=lambda t: -statistics.mean(
        (values[t,'L1',m]*values[t,'L2',m]*values[t,'L3',m])**(1/3) for m in MODELS))
    summary=[]
    for track in tracks:
        for level in COLORS:
            vs=[values[track,level,m] for m in MODELS]
            summary.append(dict(track=track,level=level,n_models=8,
                                mean=statistics.mean(vs),minimum=min(vs),maximum=max(vs)))
    ceilings=[]
    for level,path,column in zip(COLORS,SOURCES[1:],['score','score','composite']):
        eligible=[r for r in read(path) if r['model'] in MODELS
                  and r.get('state')!='CONFOUNDED-EXCLUDED' and r[column] not in ('','None')]
        n=sum(float(r[column])>=3 for r in eligible)
        ceilings.append(dict(level=level,numerator=n,denominator=len(eligible),percent=100*n/len(eligible)))
    assert [(r['numerator'],r['denominator']) for r in ceilings]==[(384,632),(279,816),(1,172)]
    annotations=[dict(track='Protein',level='L1',model='glm-5.3',score=values['Protein','L1','glm-5.3']),
                 dict(track='CRISPR',level='L2',model='glm-5.3',score=values['CRISPR','L2','glm-5.3'])]
    assert annotations[0]['score']==100 and round(annotations[1]['score'],1)==3.5
    # Audit against every cell in the retained full matrix, not just its means.
    old=[r for r in read(OUT/'F03_chain_landscape_8models.csv') if r['row_type']=='level_cell']
    fullnames={'gpt-5.6-sol':'GPT-5.6-sol','claude-opus-5':'Claude Opus 5','kimi-k3':'Kimi K3',
               'glm-5.2':'GLM-5.2','deepseek-v4-pro':'DeepSeek V4 Pro','gpt-4.1':'GPT-4.1',
               'glm-5.3':'GLM-5.3','gpt-6-astra':'GPT-6 Astra'}
    by_name={v:k for k,v in fullnames.items()}
    assert len(old)==192
    for r in old:
        assert abs(float(r['score_pct'])-values[r['track'],r['level'],by_name[r['model']]])<.011, r
    return dict(tracks=tracks,summary=summary,ceilings=ceilings,annotations=annotations,
                source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES})


def main():
    report=derive(); tracks=report['tracks']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7.5,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig=plt.figure(figsize=(5.5,3.2))
    fig.text(.02,.975,'Performance varies across tracks and stages',va='top',fontsize=9,weight='bold')
    fig.text(.02,.930,'Dots: eight-model means. Lines: observed min–max, not uncertainty intervals.',va='top',fontsize=6.6,color='#475565')
    axes=[]
    for j,level in enumerate(COLORS):
        ax=fig.add_axes([.205+j*.263,.25,.225,.57]); axes.append(ax)
        for i,track in enumerate(tracks):
            r=next(r for r in report['summary'] if r['track']==track and r['level']==level)
            ax.hlines(i,r['minimum'],r['maximum'],color=COLORS[level],alpha=.5,lw=1.4)
            ax.scatter(r['mean'],i,s=24,color=COLORS[level],edgecolor='white',linewidth=.4,zorder=3)
        ax.set(xlim=(-4,104),ylim=(7.7,-.6),xticks=[0,50,100],yticks=range(8))
        ax.set_yticklabels(tracks if j==0 else ['']*8)
        ax.set_title(level,color=COLORS[level],fontsize=8.5,weight='bold',pad=8)
        ax.tick_params(axis='y',length=0,pad=7); ax.tick_params(axis='x',length=2)
        ax.grid(axis='x',color='#E1E6EB',lw=.6); ax.set_axisbelow(True)
        for side in ['left','right','top']: ax.spines[side].set_visible(False)
        ax.spines['bottom'].set_color('#A8B0B8')
    for a in report['annotations']:
        ax=axes[list(COLORS).index(a['level'])]; y=tracks.index(a['track'])
        ax.scatter(a['score'],y,s=26,marker='D',facecolor='white',edgecolor='#263645',linewidth=.8,zorder=4)
        label=f"GLM-5.3: {a['score']:.1f}" if a['score']<100 else 'GLM-5.3: 100'
        ax.annotate(label,(a['score'],y),xytext=(96 if a['score']==100 else 8,y-.37),
                    ha='right' if a['score']==100 else 'left',va='bottom',fontsize=6.5,
                    arrowprops={'arrowstyle':'-','color':'#53606D','lw':.6},color='#263645')
    fig.text(.60,.185,'Stage score (0–100)',ha='center',fontsize=7.5)
    fig.text(.025,.128,'Maximum\nrubric credit',va='top',fontsize=6.5,color='#475565')
    for i,r in enumerate(report['ceilings']):
        left=.205+i*.263
        bar=fig.add_axes([left,.118,.225,.019]); bar.set(xlim=(0,100),ylim=(-.5,.5)); bar.axis('off')
        bar.barh(0,100,color='#EDF1F4',height=1)
        bar.barh(0,r['percent'],color=COLORS[r['level']],height=1)
        fig.text(left+.1125,.080,f"{r['percent']:.1f}% ({r['numerator']}/{r['denominator']})",
                 ha='center',fontsize=7.5)
    fig.text(.02,.020,'Stage ceilings differ; L3 requires all seven axes at maximum. Not end-to-end success rates.',fontsize=6.5,color='#475565')
    fig.canvas.draw(); renderer=fig.canvas.get_renderer()
    for text in fig.findobj(matplotlib.text.Text):
        if not text.get_visible() or not text.get_text(): continue
        bb=text.get_window_extent(renderer)
        assert bb.x0>=-.5 and bb.x1<=fig.bbox.width+.5 and bb.y0>=-.5 and bb.y1<=fig.bbox.height+.5,text.get_text()
    for ext in ['pdf','png','svg']: fig.savefig(OUT/f'F03_stage_summary_8models.{ext}',dpi=240)
    plt.close(fig)
    (OUT/'F03_stage_summary_8models.json').write_text(json.dumps(report,indent=2)+'\n')
    with (OUT/'F03_stage_summary_8models.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(report['summary'][0])); writer.writeheader();writer.writerows(report['summary'])
    print('PASS: 192 source cells reconciled; 24 means/ranges and all ceiling counts verified.')


if __name__=='__main__': main()
