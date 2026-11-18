"""Render the paper's standalone profile matrix from saved eight-model metrics.

Presentation only: no grader, aggregation, or stability analysis is rerun.
The original combined WS02 PDF remains the source for the separate cost panel.
"""
from pathlib import Path
import csv
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'outputs/8models/data/profile_metrics_long.csv'
OUT = HERE / 'outputs/8models/figures'
MODELS = ['gpt-5.6-sol', 'claude-opus-5', 'kimi-k3', 'glm-5.2',
          'deepseek-v4-pro', 'gpt-4.1', 'glm-5.3', 'gpt-6-astra']
NAMES = ['GPT-5.6\nsol', 'Claude\nOpus 5', 'Kimi\nK3', 'GLM\n5.2',
         'DeepSeek\nV4 Pro', 'GPT-4.1', 'GLM\n5.3', 'GPT-6\nAstra']
GROUPS = [
    ('Evidence judgment and handling', '#255E92', [
        ('L1 clean specificity', 'Clean-data judgment'),
        ('L1 defect handling', 'Challenge handling'),
        ('L1 no fabrication', 'No fabrication recorded'),
    ]),
    ('Analytical behavior', '#CE8A2E', [
        ('L2 clean specificity', 'Clean-analysis performance'),
        ('L2 analytical correctness', 'Analytical correctness'),
        ('L2 issue recognition', 'Issue recognition'),
        ('L2 methodological response', 'Methodological response'),
        ('L2 result calibration', 'Result calibration'),
    ]),
    ('Response behavior', '#2A7A50', [
        ('L3 evidence fidelity', 'Evidence fidelity*'),
        ('L3 moved to supplied evidence', 'Moves toward evidence | CF'),
        ('L3 causal calibration', 'Causal calibration*'),
        ('L3 hypothesis commitment', 'Hypothesis commitment'),
        ('L3 valid novelty given commitment', 'Valid novelty*'),
        ('L3 response to critique', 'Response to critique*'),
        ('L3 scientific humility', 'Acknowledges uncertainty*'),
        ('L3 citation integrity', 'Citation integrity*'),
    ]),
]


def main():
    with SOURCE.open() as f:
        records = {(r['model'], r['metric']): r for r in csv.DictReader(f)}
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.5,
                         'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    fig = plt.figure(figsize=(5.5, 6.6))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, 5.5), ylim=(6.6, 0)); ax.axis('off')
    left, width, row_h = 1.83, 3.62 / 8, .213
    cmap = LinearSegmentedColormap.from_list('quality', ['#F5F8FA', '#AECADD', '#255E92'])
    ax.text(.04, .12, 'Scientific working-style profiles', fontsize=9, weight='bold', va='top')
    ax.text(.04, .36, 'Scores and rates on 0–100; compare models within a row.', fontsize=6.8, va='top')
    for j, name in enumerate(NAMES):
        ax.text(left+(j+.5)*width, .74, name, ha='center', va='center', fontsize=7.5)
    exported = []
    y = 1.07
    for group, color, rows in GROUPS:
        ax.add_patch(Rectangle((.03, y), 5.42, .23, facecolor='#EDF1F4', edgecolor='none'))
        ax.text(.06, y+.115, group, color=color, weight='bold', va='center', fontsize=7.5)
        y += .26
        for metric, label in rows:
            ax.text(left-.07, y+row_h/2, label, ha='right', va='center', fontsize=7.5)
            for j, model in enumerate(MODELS):
                r = records[model, metric]; value = float(r['value'])
                assert 0 <= value <= 100
                ax.add_patch(Rectangle((left+j*width, y), width, row_h,
                                      facecolor=cmap(value/100), edgecolor='white', linewidth=.6))
                ax.text(left+(j+.5)*width, y+row_h/2, f'{value:.0f}', ha='center', va='center',
                        color='white' if value >= 72 else '#162C3D', fontsize=7.5)
                exported.append({'model': model, 'metric': metric, 'value': value})
            y += row_h
            if metric == 'L3 hypothesis commitment':
                ax.text(left-.07, y+.09, 'Hypotheses / eligible', ha='right', va='center', fontsize=6.6)
                for j, model in enumerate(MODELS):
                    r = records[model, metric]
                    ax.text(left+(j+.5)*width, y+.09,
                            f"{int(float(r['numerator']))}/{int(float(r['denominator']))}",
                            ha='center', va='center', fontsize=6.6,
                            weight='bold' if model == 'gpt-6-astra' else 'normal')
                y += .19
        y += .09
    notes = [
        '* L3 quality is conditional on producing a hypothesis. Astra: one hypothesis only.',
        'CF = eligible counterfactual dossiers. Abstention is not necessarily evidence rejection.',
        'Clean-data judgment is rubric credit, not the clean-acceptance rate.',
        'L2: equal-family, then equal-track averages. No fabrication: recorded checks, not proof.',
        'No combined style score. Cross-track ranking stability is reported in the appendix.',
    ]
    for line in notes:
        ax.text(.04, y, line, va='top', fontsize=6.4, color='#405466'); y += .15
    assert y < 6.6
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for t in ax.texts:
        bb=t.get_window_extent(renderer)
        assert bb.x0 >= 0 and bb.x1 <= fig.bbox.width and bb.y0 >= 0 and bb.y1 <= fig.bbox.height, t.get_text()
    for ext in ['pdf', 'png', 'svg']:
        fig.savefig(OUT / f'WS02_profile_panel_paper_8models.{ext}', dpi=240)
    plt.close(fig)
    (OUT / 'WS02_profile_panel_paper_8models.json').write_text(json.dumps(exported, indent=2)+'\n')
    assert len(exported) == 16*8
    print('Rendered 128 unchanged values in three behavior groups.')


if __name__ == '__main__':
    main()
