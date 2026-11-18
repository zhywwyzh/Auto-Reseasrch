"""F04+F06 in ONE row: L1 clean controls (A), L1 integrity challenges (B), L3 evidence vs stated
prior (C), L3 discovery hurdle (D). Presentation-only: every number is re-derived from the 8-model
figure tables and asserted against the CSVs the standalone figures wrote.

Authored at 5.5 x 2.15 in; model names appear once (panel A) with a colour key that identifies the
points in panel D.
"""
from pathlib import Path
import csv, collections, statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import fig_common as C
import fig_common_ext as X
import fig_palette_main as P

ROOT = Path(__file__).resolve().parent; OUT = ROOT / 'results/figures'
MODELS = ['gpt-5.6-sol', 'claude-opus-5', 'kimi-k3', 'glm-5.2', 'deepseek-v4-pro', 'gpt-4.1', 'glm-5.3', 'gpt-6-astra']
NAMES = ['Sol', 'Opus 5', 'Kimi K3', 'GLM 5.2', 'DS V4', 'GPT-4.1', 'GLM 5.3', 'Astra']
COLOR = P.MODEL
CLEAN = ['CLEAN-CORRECT', 'OVER-CAUTIOUS', 'FALSE-UNUSABLE']
STATES = ['DIAGNOSE-AND-ACT', 'DIAGNOSE-AND-ACT-PARTIAL', 'DIAGNOSE-NOT-ACT', 'NOTICE-WRONG',
          'ABSTAIN-RECOGNIZED', 'ABSTAIN-OK', 'OVER-DIAGNOSE', 'MISS', 'NONCOMPLIANT']
STATE_LAB = ['Diagnose + act', 'Partial action', 'Diagnose only', 'Wrong diagnosis',
             'Abstain (recog.)', 'Abstain (approp.)', 'Over-diagnose', 'Miss', 'Noncompliant']
CATS = ['data', 'mixed', 'prior', 'declined']
CAT_LAB = {'data': 'moved to data', 'mixed': 'partly retreated', 'prior': 'snapped to prior', 'declined': 'declined'}
FILL = P.FILL
FS = 6.5


def bucket(label):
    u = str(label or '').upper()
    return ('data' if u.startswith('TRUSTS-DATA') else 'prior' if u.startswith('TRUSTS-PRIOR')
            else 'mixed' if u.startswith('MIXED') else None)


def derive():
    l1 = C.load('fig_data_l1_8models.csv'); l3 = [r for r in C.load('fig_data_l3_8models.csv') if r['state'] != 'CONFOUNDED-EXCLUDED']
    clean = {m: collections.Counter(r['state'] for r in l1 if r['model'] == m and r['is_clean']) for m in MODELS}
    inj = {m: collections.Counter(r['state'] for r in l1 if r['model'] == m and not r['is_clean']) for m in MODELS}
    prior = collections.defaultdict(collections.Counter); hurdle = {}
    for m in MODELS:
        for r in (x for x in l3 if x['model'] == m and x['is_counterfactual']):
            b = bucket(r['data_vs_prior'])
            if b is None and str(r['state']).startswith('ABSTAIN'): b = 'declined'
            if b: prior[m][b] += 1
        elig = [r for r in l3 if r['model'] == m]; com = [r for r in elig if not str(r['state']).startswith('ABSTAIN')]
        nov = [r['novelty'] for r in com if r['novelty'] is not None]
        hurdle[m] = (len(com) / len(elig), statistics.mean(nov) if nov else 0.0, len(com), len(elig))
    # audit against the standalone figures' exports
    ref = {r['model']: r for r in csv.DictReader(open(OUT / 'F06_prior_to_yield_8models.csv'))}
    for m in MODELS:
        assert abs(float(ref[m]['p_commit']) - hurdle[m][0]) < 1e-3 and abs(float(ref[m]['mean_novelty_given_commit']) - hurdle[m][1]) < 1e-2, m
        assert all(int(ref[m][f'prior_{c}']) == prior[m][c] for c in CATS), m
    assert sum(sum(v.values()) for v in clean.values()) == 64 and sum(sum(v.values()) for v in inj.values()) == 568
    return clean, inj, prior, hurdle


def stacked(ax, counts, order, colors):
    for i, m in enumerate(MODELS):
        tot = sum(counts[m].values()); left = 0
        for k in order:
            w = 100 * counts[m][k] / tot
            if w: ax.barh(i, w, left=left, color=colors[k], height=.66, edgecolor='white', linewidth=.3)
            left += w
    ax.set(xlim=(0, 100), ylim=(7.6, -.6), xticks=[0, 50, 100], yticks=range(8))
    ax.set_xticklabels(['0', '50', '100%'], fontsize=FS); ax.set_yticklabels([''] * 8)
    ax.get_xticklabels()[-1].set_ha('right'); ax.get_xticklabels()[0].set_ha('left')
    for s in ['top', 'right', 'left']: ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0); ax.tick_params(axis='x', length=2, labelsize=FS)


def main():
    plt.rcParams.update({'font.size': FS, 'font.family': 'DejaVu Sans', 'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    clean, inj, prior, hurdle = derive()
    W, H = 5.5, 1.93
    fig = plt.figure(figsize=(W, H))
    def axes(x0, w): return fig.add_axes([x0 / W, .44, w / W, .49])
    axA = axes(.58, .96); axB = axes(1.68, 1.12); axC = axes(4.40, .96); axD = axes(3.30, .90)   # axC: prior bars (panel D position), axD: hurdle scatter (panel C position)
    stacked(axA, clean, CLEAN, P.OUTCOME); stacked(axB, inj, STATES, P.OUTCOME); stacked(axC, prior, CATS, FILL)
    axA.set_yticklabels(NAMES, fontsize=FS)
    key = fig.add_axes([.02 / W, .44, .10 / W, .49]); key.set(xlim=(0, 1), ylim=(7.6, -.6)); key.axis('off')
    for i, m in enumerate(MODELS):                     # colour key linking names to panel D
        key.scatter(.5, i, s=18, color=COLOR[m], marker=P.MARKER[m], zorder=5)
    for ax, t in [(axA, 'A'), (axB, 'B'), (axD, 'C'), (axC, 'D')]:
        ax.set_title(t, loc='left', fontsize=7.0, fontweight='bold', pad=4)
    # ---- D
    gx, gy = np.meshgrid(np.linspace(.02, 1, 200), np.linspace(.5, 72, 200))
    cs = axD.contour(gx, gy, gx * gy, levels=[10, 20, 30], colors=C.GRID, linewidths=.6)
    for m in MODELS:
        p, n, *_ = hurdle[m]
        axD.scatter([p], [n * 100 / 3], s=30, color=COLOR[m], marker=P.MARKER[m], edgecolor=COLOR[m], linewidth=.6, zorder=4)
    axD.set(xlim=(0, 1), ylim=(0, 72), xticks=[0, .5, 1], yticks=[0, 25, 50])
    axD.set_xticklabels(['0', '50', '100%'], fontsize=FS); axD.tick_params(length=2, labelsize=FS)
    axD.get_xticklabels()[-1].set_ha('right'); axD.get_xticklabels()[0].set_ha('left')
    axD.set_xlabel('committed (%)', fontsize=FS, labelpad=1); axD.set_ylabel('novelty | commit (0–100)', fontsize=FS, labelpad=1)
    for s in ['top', 'right']: axD.spines[s].set_visible(False)
    axD.text(.97, .04, 'contours: yield 10, 20, 30', transform=axD.transAxes, ha='right', va='bottom', fontsize=5.4, color=C.INK3)
    # ---- legends under their panels
    def legend(x0, keys, labs, colors, ncol, letter):
        # panel letter INLINE, left of the first colour patch (not a title row above)
        lg = fig.legend([Patch(color=colors[k]) for k in keys], labs, loc='upper left', bbox_to_anchor=((x0 + .13) / W, .31),
                        ncol=ncol, frameon=False, fontsize=5.6, handlelength=.9, handletextpad=.35, columnspacing=.3,
                        labelspacing=.25)
        fig.canvas.draw(); bb = lg.get_texts()[0].get_window_extent(fig.canvas.get_renderer())
        yc = (bb.y0 + bb.y1) / 2 / fig.bbox.height
        fig.text(x0 / W, yc, letter, fontsize=7.0, fontweight='bold', va='center', ha='left')
    legend(.05, CLEAN, ['Accept clean', 'Over-cautious', 'Reject clean'], P.OUTCOME, 1, 'A')
    legend(1.30, STATES, STATE_LAB, P.OUTCOME, 3, 'B')                       # spans B and C; C has no legend
    legend(3.80, CATS, [CAT_LAB[c] for c in CATS], FILL, 2, 'D')
    fig.canvas.draw(); rend = fig.canvas.get_renderer()
    for t in fig.findobj(matplotlib.text.Text):
        if not t.get_visible() or not t.get_text(): continue
        bb = t.get_window_extent(rend)
        assert bb.x0 >= -.5 and bb.x1 <= fig.bbox.width + .5 and bb.y0 >= -.5 and bb.y1 <= fig.bbox.height + .5, t.get_text()
    for ext in ['pdf', 'png']: fig.savefig(OUT / f'F04F06_states_row_8models.{ext}', dpi=200)
    plt.close(fig)
    with open(OUT / 'F04F06_states_row_8models.csv', 'w') as f:
        w = csv.writer(f); w.writerow(['model', *CLEAN, *STATES, *[f'prior_{c}' for c in CATS], 'p_commit', 'mean_novelty_given_commit', 'n_committed', 'n_eligible'])
        for m in MODELS: w.writerow([m, *[clean[m][k] for k in CLEAN], *[inj[m][k] for k in STATES], *[prior[m][c] for c in CATS], round(hurdle[m][0], 4), round(hurdle[m][1], 3), hurdle[m][2], hurdle[m][3]])
    print('PASS: 64 clean + 568 injected + prior/hurdle reconciled with F06 export')


if __name__ == '__main__': main()
