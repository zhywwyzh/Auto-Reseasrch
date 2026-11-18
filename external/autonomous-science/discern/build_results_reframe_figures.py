"""Presentation-only variants for the reorganized Results; original builders preserved."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import fig_palette_main as P

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results/figures'

def states():
    s = (ROOT / 'fig_states_row.py').read_text()
    s = s.replace('W, H = 5.5, 1.93', 'W, H = 5.5, 1.75')
    s = s.replace('.44, w / W, .49', '.19, w / W, .60')
    s = s.replace('.44, .10 / W, .49', '.19, .10 / W, .60')
    start = s.index('    axA = axes(')
    end = s.index('    axA.set_yticklabels', start)
    s = s[:start] + '''    axA = axes(.65, 1.25); axD = axes(2.52, 1.12); axC = axes(4.05, 1.30)
    stacked(axA, clean, CLEAN, P.OUTCOME); stacked(axC, prior, CATS, FILL)
''' + s[end:]
    s = s.replace("[(axA, 'A'), (axB, 'B'), (axD, 'C'), (axC, 'D')]", "[(axA, 'A'), (axD, 'B'), (axC, 'C')]")
    s = '\n'.join(line for line in s.split('\n') if not line.startswith('    legend(1.30, STATES'))
    s = s.replace("legend(3.80, CATS, [CAT_LAB[c] for c in CATS], FILL, 2, 'D')", "legend(3.90, CATS, ['To evidence', 'Partial retreat', 'To prior', 'Abstained'], FILL, 2, 'C')")
    s = s.replace("P.OUTCOME, 1, 'A')", "P.OUTCOME, 3, 'A')")
    # Put the legends beside the single top-row panel labels, not on a
    # second A/C-labelled row below the axes. Preserve the bar-panel height.
    s = s.replace("        ax.set_title(t, loc='left', fontsize=7.0, fontweight='bold', pad=4)",
                  "        fig.text({'A': .02, 'B': 2.52, 'C': 3.85}[t] / W, .95, t, fontsize=7.0, fontweight='bold', va='top')")
    s = s.replace('bbox_to_anchor=((x0 + .13) / W, .31)',
                  'bbox_to_anchor=((x0 + .13) / W, .995)')
    s = s.replace("        fig.text(x0 / W, yc, letter, fontsize=7.0, fontweight='bold', va='center', ha='left')", '')
    s = s.replace('dpi=200)', "dpi=200, bbox_inches='tight', pad_inches=.02)")
    s = s.replace('F04F06_states_row_8models', 'F04_working_styles_3panel_8models')
    exec(compile(s, str(ROOT / 'fig_states_row.py'), 'exec'), {'__name__':'__main__', '__file__':str(ROOT / 'fig_states_row.py')})

def stability():
    source = ROOT / 'Scientific Working Style Profile Draft/outputs/8models/data/working_style_stability.csv'
    with source.open() as f:
        rows = [r for r in csv.DictReader(f) if not r['dimension'].startswith('USD')]
    assert len(rows) == 17
    groups = [
        ('Resource use', [r for r in rows if r['group']=='interaction footprint']),
        ('Analytical judgment', [r for r in rows if '(L2)' in r['dimension'] and r['group']!='interaction footprint']),
        ('Evidence assessment and commitment', [r for r in rows if '(L2)' not in r['dimension'] and r['group']!='interaction footprint'])]
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':7.5, 'pdf.fonttype':42})
    fig = plt.figure(figsize=(3.50, 3.15))
    ax = fig.add_axes([.57,.12,.39,.83])
    labels=[]; positions=[]; headings=[]; y=0
    for title, items in groups:
        headings.append(ax.text(1.0,y,title,transform=ax.get_yaxis_transform(),fontsize=7.5,
                fontweight='bold',va='center',ha='center',linespacing=1.0))
        y+=1.6 if '\n' in title else 1.15
        for r in items:
            w=float(r['kendall_w'])
            ax.plot([.125,w],[y,y],color='#DFE4E8',lw=1)
            ax.scatter(w,y,color=P.BLUE,s=17,zorder=3)
            lab=r['dimension'].replace(' per task','').replace(' executed','').replace('methodological response','Methodological response').replace('diagnose-and-act rate','Diagnose + act').replace('no-fabrication rate','No fabrication').replace('prior-snap rate','Return to prior')
            lab=lab[0].upper()+lab[1:]
            labels.append(lab);positions.append(y);y+=1
        y+=.7
    assert len(labels)==17
    ax.set(xlim=(0,1.03),ylim=(y-.5,-.7),yticks=positions,yticklabels=labels,xticks=[.125,.5,1])
    ax.set_xticklabels(['0.125','0.5','1.0'])
    ax.axvline(.125,color='#A7ADB3',ls=':',lw=.8)
    # Share the tick-label row instead of reserving a separate label row.
    ax.text(-.12, -.026, "Kendall's W", transform=ax.transAxes,
            ha='right', va='top', fontsize=7.5)
    ax.tick_params(axis='y',length=0,labelsize=7.5)
    for side in ['top','right','left']: ax.spines[side].set_visible(False)
    fig.canvas.draw()
    # Center headings over both the metric-label column and the plotting area.
    renderer = fig.canvas.get_renderer()
    left = min(t.get_window_extent(renderer).x0 for t in ax.get_yticklabels())
    right = ax.get_window_extent(renderer).x1
    center = ax.transAxes.inverted().transform(((left + right) / 2, 0))[0]
    for heading in headings:
        heading.set_x(center)
    fig.canvas.draw()
    for t in fig.findobj(matplotlib.text.Text):
        if not t.get_visible() or not t.get_text(): continue
        b=t.get_window_extent(fig.canvas.get_renderer())
        assert b.x0 >= -.5 and b.x1 <= fig.bbox.width+.5 and b.y0>=-.5 and b.y1<=fig.bbox.height+.5,t.get_text()
    for ext in ['pdf','png']:
        fig.savefig(OUT/f'WS01_stability_grouped_8models.{ext}',dpi=200,
                    bbox_inches='tight',pad_inches=.02)
    print('PASS: all 17 existing non-USD stability measures preserved.')

def effort():
    import fig_expense_stability_row as E
    rows=E.read(OUT/'E3_effort_vs_spend_8models.csv')
    fig, ax=plt.subplots(figsize=(4.2,3.0))
    fig.subplots_adjust(left=.17,right=.97,bottom=.20,top=.77)
    handles=[]
    for m,name in zip(E.MODELS,E.NAMES):
        points={r['level']:(float(r['median_code_cells']),float(r['median_tokens_per_task'])/1000)
                for r in rows if r['model']==E.X.FULL[m]}
        x1,y1=points['L1'];x2,y2=points['L2']
        ax.plot([x1,x2],[y1,y2],color=P.MODEL[m],alpha=.6,lw=.8)
        h=ax.scatter(x1,y1,s=26,color=P.MODEL[m],marker=P.MARKER[m],label=name)
        ax.scatter(x2,y2,s=26,facecolor='white',edgecolor=P.MODEL[m],marker=P.MARKER[m],linewidth=1)
        handles.append(h)
    ax.set(yscale='log',xlim=(0,22),ylim=(5,600),xlabel='Median executed code cells per task',ylabel='Median tokens per task (k)')
    ax.set_yticks([10,100]);ax.set_yticklabels(['10','100'])
    for side in ['top','right']:ax.spines[side].set_visible(False)
    fig.legend(handles,E.NAMES,loc='upper center',ncol=4,fontsize=7,frameon=False,columnspacing=.8,handletextpad=.3)
    fig.text(.57,.02,'Filled: L1   Hollow: L2',ha='center',fontsize=7.5)
    for ext in ['pdf','png']:fig.savefig(OUT/f'E3_effort_appendix_8models.{ext}',dpi=200)
    print('PASS: existing 16 model-level effort points retained; no API-budget ceiling inferred.')

if __name__=='__main__':
    states()
    stability()
    effort()
