"""Four-category overview with decomposed L2; no new score or regrading."""
from pathlib import Path
import csv
import json
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from build_profile_panel_paper import MODELS, NAMES, HERE

ROOT = HERE.parent
OUT = HERE / 'outputs/8models/figures'


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def derive():
    metrics = {(r['model'], r['metric']): r for r in read(HERE / 'outputs/8models/data/profile_metrics_long.csv')}
    efficiency = {r['model']: r for r in read(ROOT / 'results/efficiency_by_model_8models.csv')}
    levels = read(ROOT / 'results/fig_data_levels_8models.csv')
    clean = [r for r in read(ROOT / 'results/fig_data_l1_8models.csv') if r['is_clean'] == 'True']
    result = []
    for model in MODELS:
        e = efficiency[model]
        scores = {}
        for level in ['L1', 'L2']:
            selected = [r for r in levels if r['model'] == model and r['level'] == level and not r['family']]
            assert len(selected) == 8 and len({r['track'] for r in selected}) == 8
            scores[level] = statistics.mean(float(r['score']) * 100/3 for r in selected)
        controls = [r for r in clean if r['model'] == model]
        assert len(controls) == 8
        commit = metrics[model, 'L3 hypothesis commitment']
        result.append(dict(
            model=model, overall=float(e['score_chain_pct']), l1=scores['L1'], l2=scores['L2'],
            clean_accepted=sum(r['state']=='CLEAN-CORRECT' for r in controls), clean_total=8,
            result_calibration=float(metrics[model, 'L2 result calibration']['value']),
            analytical_correctness=float(metrics[model, 'L2 analytical correctness']['value']),
            issue_recognition=float(metrics[model, 'L2 issue recognition']['value']),
            methodological_response=float(metrics[model, 'L2 methodological response']['value']),
            commitment=float(commit['value']), hypotheses=int(float(commit['numerator'])),
            eligible=int(float(commit['denominator'])),
            novelty_conditional=float(metrics[model, 'L3 valid novelty given commitment']['value']),
            tokens_million=int(e['total'])/1e6,
            quality_per_million_tokens=float(e['score_chain_pct'])/(int(e['total'])/1e6)))
    assert sum(r['clean_accepted'] for r in result) == 19
    assert sum(r['eligible'] for r in result) == 172
    assert sum(r['hypotheses'] for r in result) == 94
    for key,expected in [('analytical_correctness',68.5),('issue_recognition',69.9),
                         ('methodological_response',70.4),('result_calibration',64.5)]:
        assert round(statistics.mean(r[key] for r in result),1)==expected
    return result


FONTS=dict(title=8.5,subtitle=6.2,header=6.7,label=7.0,detail=6.0,cell=6.5,main=7.4,sub=6.0,tiny=5.8,note=5.9)


ROW_LABELS=[('Evidence judgment\nand handling','L1 / clean accepted'),
            ('Analytical behavior',''),
            ('Response behavior','commit % / novelty* (n)'),
            ('Operational\nexpenditure','M tokens / Q per Mtok')]
DIM_LABELS=[('analytical_correctness','Analytical correctness'),('issue_recognition','Issue recognition'),
            ('methodological_response','Methodological response'),('result_calibration','Result calibration')]


def draw_overview(ax, data, x0=0.0, left=1.47, width=.45, y0=0.0, fonts=FONTS, title=True, notes=True,
                  token_unit='M', names=None, header_rotation=0, header_y=.61, row_top=.94,
                  row_labels=None, dim_labels=None, pad=0.0, header_va='top', group_x=None, pct_sign='%', header_family=None, tiny_family=None,
                  quality_palette=None, contrast_color=None):
    """Draw the four-category table into `ax` (inch coordinates, y increasing downward).
    x0/y0 offset the block so it can be composed with other panels; returns the block's right edge.
    header_rotation=90 draws model names vertically (full names at readable size in narrow columns)."""
    f=fonts; L=x0+left; height=.43
    if title:
        ax.text(x0+.04,y0+.10,title if isinstance(title,str) else 'Scientific working-style overview',
                fontsize=f['title'],weight='bold',va='top')
        if notes:
            ax.text(x0+.04,y0+.34,'Four working-style categories; Overall is reported in Table 1.',fontsize=f['subtitle'],va='top')
    for j,name in enumerate(names or NAMES):
        if header_rotation:
            ax.text(L+(j+.5)*width,y0+header_y,name,ha='center',va='bottom',fontsize=f['header'],rotation=header_rotation)
        else:
            ax.text(L+(j+.5)*width,y0+header_y,name,ha='center',va=header_va,fontsize=f['header'],family=header_family)
    labels=row_labels or ROW_LABELS
    dims=dim_labels or DIM_LABELS
    cmap=LinearSegmentedColormap.from_list('quality',quality_palette or ['#F3F7FA','#A9C8DE','#255E92'])
    side=group_x is not None
    ys=([row_top, row_top+.43, row_top+1.11, row_top+1.54] if side else
        [row_top, row_top+.43+pad, row_top+1.28+2*pad, row_top+1.71+2*pad])
    for i,(label,detail) in enumerate(labels):
        y=y0+ys[i]
        if i==1:
            if side:
                ax.text(x0+group_x,y+.32,label,ha='right',va='center',fontsize=f['label'],weight='bold')
            else:
                ax.text(L-.08,y+.06,label,ha='right',va='center',fontsize=f['label'],weight='bold')
            for k,(key,title_) in enumerate(dims):
                yy=(y+k*.16) if side else (y+.17+pad+k*.16)
                ax.text(L-.08,yy+.065,title_,ha='right',va='center',fontsize=f['detail'],color='#485968')
                for j,r in enumerate(data):
                    value=r[key]
                    ax.add_patch(Rectangle((L+j*width,yy),width,.15,facecolor=cmap(value/100),edgecolor='white',linewidth=.5))
                    ax.text(L+(j+.5)*width,yy+.075,f'{value:.1f}',ha='center',va='center',fontsize=f['cell'],
                            color=contrast_color(cmap(value/100)) if contrast_color else ('white' if value>=72 else '#163247'))
            continue
        if side:
            ax.text(x0+group_x,y+.20,label,ha='right',va='center',fontsize=f['label'],weight='bold')
            ax.text(L-.08,y+.20,detail,ha='right',va='center',fontsize=f['detail'],color='#485968')
        else:
            ax.text(L-.08,y+.12,label,ha='right',va='center',fontsize=f['label'],weight='bold')
            ax.text(L-.08,y+.32,detail,ha='right',va='center',fontsize=f['detail'],color='#485968')
        for j,r in enumerate(data):
            if i==0: value=r['l1']; main=f'{value:.1f}'; sub=f"{r['clean_accepted']}/{r['clean_total']}"
            elif i==2: value=None; main=f"{r['commitment']:.1f}{pct_sign}"; sub=f"{r['novelty_conditional']:.1f}"
            else: value=None; main=f"{r['tokens_million']:.2f}{token_unit}"; sub=f"{r['quality_per_million_tokens']:.2f}"
            bg=cmap(value/100) if value is not None else '#EDF1F4'
            color=contrast_color(bg) if contrast_color else ('white' if value is not None and value>=72 else '#163247')
            ax.add_patch(Rectangle((L+j*width,y),width,height-.035,facecolor=bg,edgecolor='white',linewidth=.7))
            ax.text(L+(j+.5)*width,y+(.09 if i==2 else .20 if not sub else .12),main,ha='center',va='center',fontsize=f['main'],color=color)
            if sub:
                ax.text(L+(j+.5)*width,y+(.22 if i==2 else .29),sub,ha='center',va='center',fontsize=f['sub'],color=color)
            if i==2:
                ax.text(L+(j+.5)*width,y+.34,f"({r['hypotheses']}/{r['eligible']})",
                        ha='center',va='center',fontsize=f['tiny'],color=color,family=tiny_family)
    if notes:
        lines=[
            'Quality uses 0–100. Clean accepted = correctly accepted controls / eight controls.',
            '* Novelty is conditional on commitment; n = hypotheses / eligible dossiers.',
            'Astra’s conditional novelty describes one hypothesis. More commitment is not always better.',
        ]
        for i,line in enumerate(lines): ax.text(x0+.04,y0+3.07+i*.12,line,fontsize=f['note'],va='top',color='#465A6B')
    return L+8*width


def check_bounds(fig, ax):
    fig.canvas.draw(); renderer=fig.canvas.get_renderer()
    for t in ax.texts:
        bb=t.get_window_extent(renderer)
        assert bb.x0>=0 and bb.x1<=fig.bbox.width and bb.y0>=0 and bb.y1<=fig.bbox.height,t.get_text()


def main():
    data = derive()
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':7.0,
                         'pdf.fonttype':42, 'svg.fonttype':'none'})
    W=5.10; fig=plt.figure(figsize=(W, 3.45)); ax=fig.add_axes([0,0,1,1])
    ax.set(xlim=(0,W), ylim=(3.45,0)); ax.axis('off')
    draw_overview(ax, data)
    check_bounds(fig, ax)
    for ext in ['pdf','svg','png']: fig.savefig(OUT/f'WS02_overview_paper_8models.{ext}',dpi=240)
    plt.close(fig)
    (OUT/'WS02_overview_paper_8models.json').write_text(json.dumps(data,indent=2)+'\n')
    print('Verified four-category overview: all four L2 dimension means reconciled; 19/64 clean accepted, 94/172 committed.')


if __name__=='__main__': main()
