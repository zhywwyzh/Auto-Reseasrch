"""Merged main-text figure: (A) working-style overview + (B) compact track-stage summary.

Panel A reuses draw_overview() from build_profile_overview_paper with the same data; model names
are drawn vertically so the full leaderboard names fit at ~7 pt in narrow columns, and explanatory
notes are left to the caption. Panel B redraws fig03_stage_summary's content as ONE panel: for each
track, three stage dots (eight-model mean) with min-max lines, L1/L2/L3 stacked within the row; the
rubric ceilings are three separate thin bars on one 0-100 scale (not stacked, not overlaid).
All numbers come from the same derive() functions as the standalone figures; nothing is recomputed.
"""
import sys, json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import build_profile_overview_paper as OV
import fig03_stage_summary as ST
import fig_palette_main as P

# Runtime override only for this main-text composite, not the appendix output.
ST.COLORS = P.STAGE

OUT = HERE / 'outputs/8models/figures'
W, H = 5.5, 2.50
OV_W = 4.06                      # panel A width (in); panel B takes the rest
LEFT = 1.36                      # panel A row-label margin (in)
FONTS = dict(title=8.0, subtitle=6.0, header=6.4, label=6.6, detail=6.2, cell=7.0, main=7.0, sub=6.2, tiny=6.0, note=6.0)
SHORT_NAMES = ['Sol', 'Opus 5', 'Kimi K3', 'GLM 5.2', 'DS V4', 'GPT-4.1', 'GLM 5.3', 'Astra']
COND = 'DejaVu Sans Condensed'
ROW_LABELS = [('Evidence\njudgment', 'L1\nClean\naccepted/8'),
              ('Analytical\nbehavior', ''),
              ('Response\nbehavior', 'commit %\nnovelty* (n)'),
              ('Operational\nexpenditure', 'Mtok\nQ/Mtok')]
DIM_LABELS = [('analytical_correctness', 'Correctness'), ('issue_recognition', 'Recognition'),
              ('methodological_response', 'Method'), ('result_calibration', 'Calibration')]
INK, MUTED = '#263645', '#475565'


def draw_stage_panel(fig, x0, x1):
    """Stage panel in [x0, x1] inches: stage dots per track + three separate ceiling bars."""
    rep = ST.derive(); tracks = rep['tracks']; levels = list(ST.COLORS)
    lab_w = .64                                            # track-label margin (in)
    px = (x0 + lab_w) / W; pw = (x1 - x0 - lab_w - .06) / W
    ax = fig.add_axes([px, .300, pw, .585])
    off = {'L1': -.27, 'L2': 0.0, 'L3': .27}
    for i, track in enumerate(tracks):
        for level in levels:
            r = next(r for r in rep['summary'] if r['track'] == track and r['level'] == level)
            y = i + off[level]
            ax.hlines(y, r['minimum'], r['maximum'], color=ST.COLORS[level], alpha=.5, lw=1.1)
            ax.scatter(r['mean'], y, s=12, color=ST.COLORS[level], edgecolor='white', linewidth=.3, zorder=3)
    for a in rep['annotations']:
        y = tracks.index(a['track']) + off[a['level']]
        ax.scatter(a['score'], y, s=14, marker='D', facecolor='white', edgecolor=INK, linewidth=.7, zorder=4)
    ax.set(xlim=(-4, 104), ylim=(7.6, -.6), xticks=[0, 50, 100], yticks=range(8))
    ax.set_yticklabels([{'Histone': 'Epigenome'}.get(t, t) for t in tracks], fontsize=7.0)
    ax.tick_params(axis='y', length=0, pad=3); ax.tick_params(axis='x', length=2, labelsize=7.0)
    for i in range(1, 8): ax.axhline(i - .5, color='#EEF1F4', lw=.5, zorder=0)
    ax.grid(axis='x', color='#E1E6EB', lw=.5); ax.set_axisbelow(True)
    for side in ['left', 'right', 'top']: ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color('#A8B0B8')
    ax.set_xlabel('Score (0–100)', fontsize=7.0, labelpad=2)
    # panel title + stage key on one line below it
    fig.text(x0 / W + .008, .975, 'A', va='top', fontsize=9, weight='bold')
    kx = px + pw
    for level in reversed(levels):
        t = fig.text(kx, .905, level, ha='right', va='bottom', fontsize=7.0, weight='bold', color=ST.COLORS[level])
        fig.canvas.draw(); bb = t.get_window_extent(fig.canvas.get_renderer())
        kx -= (bb.width / fig.bbox.width) + .02
    # ceilings: three separate thin bars, shared 0-100 scale, one row per stage
    fig.text(x0 / W + .008, .175, 'Max. rubric credit', va='top', fontsize=6.5, color=MUTED)
    bar = fig.add_axes([px, .045, pw, .105]); bar.set(xlim=(0, 100), ylim=(2.7, -.7))
    bar.set_yticks(range(3)); bar.set_yticklabels(levels, fontsize=6.5)
    for tl, level in zip(bar.get_yticklabels(), levels): tl.set_color(ST.COLORS[level]); tl.set_fontweight('bold')
    bar.tick_params(axis='y', length=0, pad=3); bar.set_xticks([])
    for side in ['left', 'right', 'top', 'bottom']: bar.spines[side].set_visible(False)
    for k, r in enumerate(rep['ceilings']):
        bar.barh(k, 100, color='#EDF1F4', height=.72)
        bar.barh(k, r['percent'], color=ST.COLORS[r['level']], height=.72)
        bar.text(r['percent'] + 2.5, k, f"{r['percent']:.1f}%", va='center', ha='left', fontsize=6.2, color=INK)
    return rep


def main():
    # Resolve the condensed face explicitly on hosts whose font cache exposes
    # it only as a stretch variant of DejaVu Sans.
    from matplotlib.font_manager import fontManager, FontEntry
    fontManager.ttflist.append(FontEntry(
        fname='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf',
        name=COND))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.0, 'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    data = OV.derive()
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set(xlim=(0, W), ylim=(H, 0)); ax.axis('off'); ax.set_zorder(-1)
    SP_W = W - OV_W - .14                      # stage panel width (in), drawn first on the left
    rep = draw_stage_panel(fig, 0.0, SP_W)
    ax.plot([SP_W + .07, SP_W + .07], [.12, H - .12], color='#D5DBE1', lw=.6)
    ax.text(SP_W + .16, .09, 'B', fontsize=9, weight='bold', va='top')
    right = OV.draw_overview(ax, data, x0=SP_W + .14, left=LEFT, width=(OV_W - LEFT) / 8, fonts=FONTS, token_unit='',
                             title=False, notes=False,
                             names=SHORT_NAMES, header_rotation=0, header_va='bottom', header_y=.30, row_top=.36,
                             row_labels=ROW_LABELS, dim_labels=DIM_LABELS, group_x=.64, pct_sign='', header_family=COND, tiny_family=COND,
                             quality_palette=P.QUALITY_RAMP, contrast_color=P.text_on)
    assert abs(right - W) < 1e-6
    OV.check_bounds(fig, ax)
    fig.canvas.draw(); rend = fig.canvas.get_renderer()
    for t in fig.findobj(matplotlib.text.Text):
        if not t.get_visible() or not t.get_text(): continue
        bb = t.get_window_extent(rend)
        assert bb.x0 >= -.5 and bb.x1 <= fig.bbox.width + .5 and bb.y0 >= -.5 and bb.y1 <= fig.bbox.height + .5, t.get_text()
    for ext in ['pdf', 'png', 'svg']: fig.savefig(OUT / f'WS02F03_overview_stage_8models.{ext}', dpi=240)
    plt.close(fig)
    (OUT / 'WS02F03_overview_stage_8models.json').write_text(json.dumps(dict(overview=data, stage=rep), indent=2) + '\n')
    print(f'PASS: merged figure {W}x{H} in; panel A {OV_W} in + panel B; ceilings',
          [(r['numerator'], r['denominator']) for r in rep['ceilings']])


if __name__ == '__main__': main()
