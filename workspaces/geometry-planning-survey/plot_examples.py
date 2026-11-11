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
fig.savefig(out / 'bezier-certificate.pdf', metadata={'CreationDate': None, 'ModDate': None}, bbox_inches='tight')
plt.close(fig)
print('Rendered analytic illustration; no experimental measurements.')

# Conceptual diagram: arrows encode interfaces, not empirical performance.
from matplotlib.patches import Rectangle
fig, ax = plt.subplots(figsize=(10, 3.8))
ax.set(xlim=(0,10), ylim=(0,3.8)); ax.axis('off')
boxes=[(.12,2.2,'Reference geometry','robot + obstacles'),(2.62,2.2,'Representation','final constraint or screening'),(5.12,2.2,'Finite encoding','curve + constraints'),(7.62,2.2,'Candidate search','budget + stopping rule')]
for x,y,title,sub in boxes:
 ax.add_patch(Rectangle((x,y),2.25,1.02,facecolor='#f2f5f3',edgecolor='#526771',lw=.9))
 ax.text(x+1.125,y+.68,title,ha='center',fontsize=10,fontweight='bold')
 ax.text(x+1.125,y+.28,sub,ha='center',fontsize=8)
for x in [2.37,4.87,7.37]:ax.annotate('',xy=(x+.22,2.71),xytext=(x,2.71),arrowprops={'arrowstyle':'->','color':'#182d36'})
ax.add_patch(Rectangle((5.12,.55),4.75,.9,facecolor='white',edgecolor='#126354',lw=1.2))
ax.text(7.495,1.12,'Validation: geometry, interpolation, tolerance',ha='center',fontsize=10)
ax.text(7.495,.77,'Accept / reject / return evidence to search',ha='center',fontsize=9)
ax.annotate('',xy=(8.75,1.47),xytext=(8.75,2.17),arrowprops={'arrowstyle':'->','color':'#182d36'})
ax.annotate('',xy=(9.55,2.17),xytext=(9.55,1.47),arrowprops={'arrowstyle':'->','color':'#126354'})
ax.text(.16,1.42,'Conditional inclusions:',fontsize=10,fontweight='bold')
ax.text(.16,.98,r'$\mathcal{F}_E \subseteq \mathcal{F}_R \subseteq \mathcal{F}$',fontsize=17)
ax.text(.16,.43,'Only with sufficient encoding and\nconservative final acceptance.',fontsize=9)
fig.savefig(out/'constraint-chain.svg',metadata={'Date':None},bbox_inches='tight')
fig.savefig(out/'constraint-chain.pdf',metadata={'CreationDate':None,'ModDate':None},bbox_inches='tight')
plt.close(fig)
