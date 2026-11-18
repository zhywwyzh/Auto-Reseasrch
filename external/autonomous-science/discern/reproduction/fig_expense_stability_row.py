"""Figure 5: (A) token use by L1/L2 category difficulty, (B) code executions versus
tokens, (C) cross-track ranking consistency. Reads existing exports without rescoring.
Code-cell counts are not API steps, so no execution-budget ceiling is drawn.
"""
from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import fig_common_ext as X
import fig_palette_main as P

ROOT = Path(__file__).resolve().parent; OUT = ROOT / 'results/figures'
DATA = ROOT / 'Scientific Working Style Profile Draft/outputs/8models/data'
MODELS = ['gpt-5.6-sol', 'claude-opus-5', 'kimi-k3', 'glm-5.2', 'deepseek-v4-pro', 'gpt-4.1', 'glm-5.3', 'gpt-6-astra']
COLOR = P.MODEL
NAMES = ['Sol', 'Opus 5', 'Kimi K3', 'GLM 5.2', 'DS V4', 'GPT-4.1', 'GLM 5.3', 'Astra']
FS = 7.5; INK = '#263645'
plt.rcParams.update({'font.size': FS, 'font.family': 'DejaVu Sans', 'pdf.fonttype': 42, 'svg.fonttype': 'none'})


def read(p): return list(csv.DictReader(open(p)))


def tidy(ax):
    for s in ['top', 'right', 'left']: ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0); ax.tick_params(axis='x', length=2, labelsize=FS)


def main():
    W, H = 5.5, 2.4
    fig = plt.figure(figsize=(W, H))
    # ---- A: tokens by task difficulty (F10): easy / medium / hard median tokens per model, hard/easy ratio at right
    f10 = read(OUT / 'F10_cost_by_difficulty_8models.csv'); full = {X.FULL[m]: m for m in MODELS}
    BANDS = P.BANDS
    ax = fig.add_axes([.62 / W, .26, .86 / W, .66]); ratios = []
    for i, m in enumerate(MODELS):
        v = {r['difficulty_band']: float(r['median_tokens_per_task']) / 1000 for r in f10 if full.get(r['model']) == m}
        ax.plot([min(v.values()), max(v.values())], [i, i], color='#aab4be', lw=1, zorder=1)
        for b, c in BANDS: ax.scatter(v[b], i, color=c, s=14, zorder=3, edgecolor='white', linewidth=.4)
        ratios.append(v['hard'] / v['easy'])
        ax.text(1.02, i, f"{v['hard'] / v['easy']:.2f}×", transform=ax.get_yaxis_transform(), va='center', ha='left', fontsize=6.8, color=INK)
    ax.set(xscale='log', ylim=(7.6, -.6), yticks=range(8), xlim=(5, 700)); ax.set_yticklabels(NAMES, fontsize=FS)
    ax.set_xticks([10, 100]); ax.set_xticklabels(['10', '100'], fontsize=FS)
    ax.set_xlabel('Median tokens per task (k)', fontsize=FS, labelpad=2); tidy(ax)
    fig.text(.05 / W, .975, 'A', fontsize=7.5, fontweight='bold', va='top')
    fig.legend([Patch(color=c) for _, c in BANDS], ['Easy', 'Medium', 'Hard'], loc='upper left',
               bbox_to_anchor=(.45 / W, .10), ncol=3, frameon=False, fontsize=FS, handlelength=.9, handletextpad=.4, columnspacing=.8)
    assert 0.99 < min(ratios) < 1.01 and 1.85 < max(ratios) < 1.87 and len(ratios) == 8, ratios
    key = fig.add_axes([.02 / W, .26, .10 / W, .66]); key.set(xlim=(0, 1), ylim=(7.6, -.6)); key.axis('off')
    for i, m in enumerate(MODELS): key.scatter(.5, i, s=20, color=COLOR[m], marker=P.MARKER[m], zorder=5)
    # ---- B: effort vs spend (E3): median code cells vs median tokens, L1 filled / L2 hollow, per model
    e3 = read(OUT / 'E3_effort_vs_spend_8models.csv'); fullmap = {X.FULL[m]: m for m in MODELS}
    cx = fig.add_axes([2.32 / W, .26, .90 / W, .66]); MAXS = 20
    for m in MODELS:
        pts = {r['level']: (float(r['median_code_cells']), float(r['median_tokens_per_task']) / 1000) for r in e3 if fullmap.get(r['model']) == m}
        (x1, y1), (x2, y2) = pts['L1'], pts['L2']
        cx.plot([x1, x2], [y1, y2], color=COLOR[m], lw=.8, alpha=.6, zorder=2)
        cx.scatter(x1, y1, s=24, color=COLOR[m], marker=P.MARKER[m], edgecolor=COLOR[m], linewidth=.5, zorder=3)
        cx.scatter(x2, y2, s=22, facecolor='white', edgecolor=COLOR[m], marker=P.MARKER[m], linewidth=1.0, zorder=3)
    cx.set(yscale='log', xlim=(0, 22.5), xticks=[0, 10, 20]); cx.set_ylim(5, 600)
    cx.set_yticks([10, 100]); cx.set_yticklabels(['10', '100'], fontsize=FS); cx.tick_params(axis='x', labelsize=FS, length=2)
    cx.set_xlabel('Median code cells per task', fontsize=FS, labelpad=2); cx.set_ylabel('Median tokens (k)', fontsize=FS, labelpad=1)
    for sd in ['top', 'right']: cx.spines[sd].set_visible(False)
    fig.text(1.92 / W, .975, 'B', fontsize=7.5, fontweight='bold', va='top')
    fig.legend([plt.Line2D([], [], marker='o', ls='', color='#555', markersize=4.5), plt.Line2D([], [], marker='o', ls='', markerfacecolor='white', markeredgecolor='#555', markersize=4.5)],
               ['L1', 'L2'], loc='upper left', bbox_to_anchor=(2.35 / W, .10), ncol=2, frameon=False, fontsize=FS, handletextpad=.3, columnspacing=1.0)
    # ---- C: stability (W only, USD rows dropped)
    st = [r for r in read(DATA / 'working_style_stability.csv') if not r['dimension'].startswith('USD')]
    assert len(st) == 17
    bx = fig.add_axes([4.45 / W, .18, 1.00 / W, .76])
    for i, r in enumerate(st):
        w = float(r['kendall_w']); bx.plot([0.125, w], [i, i], color='#dfe4e8', lw=1, zorder=1)
        bx.scatter(w, i, s=14, color=P.BLUE, zorder=3)
    labels = [r['dimension'].replace(' per task', '').replace(' executed', '').replace('result calibration', 'calibration')
              .replace('methodological response', 'method response').replace('analytical correctness', 'correctness')
              .replace('diagnose-and-act rate', 'diagnose+act').replace('no-fabrication rate', 'no fabrication').replace('prior-snap rate', 'return to prior').replace(' (L1)', ' L1').replace(' (L2)', ' L2').replace(' (L3)', ' L3') for r in st]
    bx.set(ylim=(len(st) - .4, -.8), xlim=(-.02, 1.02), yticks=range(len(st)), xticks=[.125, .5, 1])
    bx.set_xticklabels(['.125', '.5', '1'], fontsize=FS); bx.set_yticklabels(labels, fontsize=FS)
    bx.axvline(.125, color='#bbc3ca', ls=':', lw=.7); tidy(bx)
    bx.set_xlabel("Kendall's W", fontsize=FS, labelpad=2)
    fig.text(3.30 / W, .975, 'C', fontsize=7.5, fontweight='bold', va='top')
    fig.canvas.draw(); rend = fig.canvas.get_renderer()
    for t in fig.findobj(matplotlib.text.Text):
        if not t.get_visible() or not t.get_text(): continue
        bb = t.get_window_extent(rend)
        assert bb.x0 >= -.5 and bb.x1 <= fig.bbox.width + .5 and bb.y0 >= -.5 and bb.y1 <= fig.bbox.height + .5, t.get_text()
    for ext in ['pdf', 'png']: fig.savefig(OUT / f'E4WS01_expense_stability_row_8models.{ext}', dpi=200)
    print('PASS: hard/easy ratios %.2f-%.2f; %d stability rows' % (min(ratios), max(ratios), len(st)))


if __name__ == '__main__': main()
