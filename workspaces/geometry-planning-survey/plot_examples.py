#!/usr/bin/env python3
"""Render an analytic illustration; this is not a planning experiment."""
from pathlib import Path
import json
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / 'survey.json').read_text())['analytic_example']
points = data['control_points']
left, right = data['subdivided_control_points']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.hashsalt': 'TR003-analytic-bezier'})
fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
for ax, title in zip(axes, ['One segment: sufficient test rejects', 'Two segments: sufficient test accepts']):
    ax.axhspan(0, 0.3, color='#edf3f0', label='Safe side of lower boundary')
    ax.axhline(0, color='#172d36', linewidth=1.1)
    curve = PathPatch(MplPath(points, [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3]),
                      facecolor='none', edgecolor='#126354', linewidth=2.7, label='Same exact quadratic curve')
    ax.add_patch(curve)
    ax.set(title=title, xlim=(-0.08, 1.08), ylim=(-0.15, 0.28), xlabel='x (normalized coordinate)')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(alpha=0.18)
axes[0].set_ylabel('y (normalized coordinate)')
axes[0].plot(*zip(*points), '--o', color='#526771', linewidth=1.2, label='Original control polygon')
axes[0].annotate('Control point outside', xy=(0.5, -0.1), xytext=(0.08, -0.135), fontsize=9)
for i, part in enumerate([left, right]):
    axes[1].plot(*zip(*part), '--o', color='#526771', linewidth=1.2,
                 label='Subdivided control polygons' if i == 0 else None)
axes[1].annotate('Minimum clearance = 0.05', xy=(0.5, 0.05), xytext=(0.17, 0.13),
                 arrowprops={'arrowstyle': '-', 'color': '#526771'}, fontsize=9)
for ax in axes:
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), frameon=False, fontsize=8)
fig.subplots_adjust(bottom=0.29, wspace=0.18, top=0.88)
out = ROOT / 'figures'
out.mkdir(exist_ok=True)
fig.savefig(out / 'bezier-certificate.svg', metadata={'Date': None}, bbox_inches='tight')
plt.close(fig)
print('Rendered analytic illustration; no experimental measurements.')
