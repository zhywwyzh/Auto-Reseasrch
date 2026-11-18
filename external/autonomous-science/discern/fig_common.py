"""Shared plotting contract for the cost/efficiency figures (E1-E4).

This is NOT a figure script -- it is the frozen contract from FIGURES_2_5_PLAN.md "Shared plotting
contract", imported by fig_E*.py so the cost panels match Figures 2-7 exactly. One .py file per figure;
this file holds only what every one of them must agree on.

Contract points honoured here:
  * ONE stable model order and ONE frozen model->colour map (FIGURES_2_5_PLAN.md).
  * Model colours NEVER encode scientific states. E4 plots states (abstained/committed), so it uses the
    reserved state colour for abstention and a neutral ink for the comparison -- no model colour at all.
  * Short labels on crowded axes; full names belong in the caption.
  * TIERED TYPE SIZES, sized for a two-column ICLR PDF. The plan's line reads "minimum final text
    7.5 pt"; an audit on 2026-08-27 found that was never literally true -- 19 of 23 scripts carried
    sub-7.5 pt text, including F01, F03, F05, F09, T04 and the cost panels, all from the original
    build. The rule that IS true, and that the figures were actually designed to, is tiered:
        PRIMARY   >= 7.5 pt   values in cells, axis tick labels, axis labels, model / row / column
                              names -- anything a reader must read to get the result.
        SECONDARY >= 6.0 pt   keys, denominators, in-figure notes, contour labels, provenance footers
                              and dense categorical tick labels that cannot fit at 7.5.
    `check_figure_contract.py` enforces the 6.0 floor mechanically, AFTER any LaTeX rescaling, and
    prints the per-script minimum so drift is visible. The primary tier is held by review, since a
    parser cannot tell a key from a tick label.
  * Vector PDF + SVG plus a 300-dpi PNG preview.
  * Every script emits a companion CSV holding EXACTLY the plotted values.
"""
import csv, json, os
from functools import lru_cache
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "results/figures")

# ---- frozen model contract (FIGURES_2_5_PLAN.md) -------------------------------------------------
MODEL_ORDER = ["gpt-4.1", "gpt-5.6-sol", "claude-opus-5", "deepseek-v4-pro", "glm-5.2", "kimi-k3"]
COLOR = {"gpt-4.1": "#7A7A7A", "gpt-5.6-sol": "#0072B2", "claude-opus-5": "#D55E00",
         "deepseek-v4-pro": "#009E73", "glm-5.2": "#CC79A7", "kimi-k3": "#E69F00"}
FULL = {"gpt-4.1": "GPT-4.1", "gpt-5.6-sol": "GPT-5.6-sol", "claude-opus-5": "Claude Opus 5",
        "deepseek-v4-pro": "DeepSeek V4 Pro", "glm-5.2": "GLM-5.2", "kimi-k3": "Kimi K3"}
SHORT = {"gpt-4.1": "GPT-4.1", "gpt-5.6-sol": "GPT-5.6", "claude-opus-5": "Claude",
         "deepseek-v4-pro": "DeepSeek", "glm-5.2": "GLM", "kimi-k3": "Kimi"}

# ---- reserved state colours (never a model colour) -----------------------------------------------
STATE_ABSTENTION = "#8B5FBF"      # purple, per the plan's reserved state palette
NEUTRAL_INK = "#4A4A4A"           # a neutral ink for a baseline comparison, deliberately NOT the
                                  # plan's clean-control gray #7A7A7A, which is GPT-4.1's model colour

INK, INK2, INK3, GRID = "#111111", "#4A4A4A", "#767676", "#DDDDDD"

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "font.family": "DejaVu Sans", "font.size": 7.5,
    "axes.labelsize": 8, "axes.titlesize": 9.5, "axes.titleweight": "bold", "axes.titlepad": 7,
    "axes.edgecolor": GRID, "axes.linewidth": 0.7, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "grid.color": GRID, "grid.linewidth": 0.5,
    "legend.frameon": False, "legend.fontsize": 7.5,
    "pdf.fonttype": 42, "svg.fonttype": "none",
})


# ---- ordered outcome ramp -------------------------------------------------------------------------
# L1/L3 outcome states are ORDINAL (scientifically desirable -> severe failure), so they take an ordered
# ramp, never nine categorical hues. Abstention keeps its reserved purple as the neutral middle.
OUTCOME = {
    "DIAGNOSE-AND-ACT": "#1B6B50", "DIAGNOSE-AND-ACT-PARTIAL": "#4E9C7D",
    "DIAGNOSE-NOT-ACT": "#93C4AC", "NOTICE-WRONG": "#F0B27A",
    "ABSTAIN-RECOGNIZED": STATE_ABSTENTION, "ABSTAIN-OK": "#C3A7DE",
    "OVER-DIAGNOSE": "#E07B5A", "MISS": "#B03A2E", "NONCOMPLIANT": "#6B6B6B",
    "CLEAN-CORRECT": "#1B6B50", "OVER-CAUTIOUS": "#F0B27A", "FALSE-UNUSABLE": "#B03A2E",
}
# Sequential fill for 0-100% heat maps: one hue, light -> dark (never a rainbow).
SEQ = ["#F2F6FA", "#D7E5F0", "#B4CFE4", "#8AB4D6", "#5E94C4", "#3A76AE", "#22588C", "#123C63"]


def seq_color(pct):
    """Map 0-100 onto the sequential ramp; returns (facecolor, text_color)."""
    i = min(len(SEQ) - 1, max(0, int(pct / 100 * len(SEQ))))
    return SEQ[i], ("white" if i >= 5 else INK)


def matrix_panel(ax, col_labels, col_denoms, values, fmt="{:.2f}", ylabels=None):
    """Model x component matrix on a 0-1 sequential fill. `values[(model, col)]` may be None.

    Denominators are printed under every column heading, because a component measured on n=3 must not
    look as stable as one measured on n=7 (FIGURES_2_5_PLAN.md, Figure 5 Panel B).
    """
    ylabels = ylabels or [SHORT[m] for m in MODEL_ORDER]
    for i, m in enumerate(MODEL_ORDER):
        for j, c in enumerate(col_labels):
            v = values.get((m, c))
            if v is None:
                ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor="#FAFAFA", edgecolor="white",
                                           linewidth=1.4))
                ax.text(j + .5, i + .5, "–", ha="center", va="center", fontsize=7.5, color=INK3)
                continue
            face, txt = seq_color(100 * v)
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=face, edgecolor="white", linewidth=1.4))
            ax.text(j + .5, i + .5, fmt.format(v), ha="center", va="center", fontsize=7.3, color=txt)
    ax.set_xlim(0, len(col_labels)); ax.set_ylim(len(MODEL_ORDER), 0)
    ax.set_xticks([j + .5 for j in range(len(col_labels))])
    ax.set_xticklabels([f"{c}\n(n={col_denoms[c]})" for c in col_labels], fontsize=7, color=INK,
                       linespacing=1.5)
    ax.set_yticks([i + .5 for i in range(len(MODEL_ORDER))])
    ax.set_yticklabels(ylabels, fontsize=7.5, color=INK)
    ax.xaxis.set_ticks_position("top"); ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)


def efficiency():
    """The single source of numbers for every cost figure."""
    with open(os.path.join(BASE, "results/efficiency.json")) as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def check_score_sources():
    from audit_l2_reconciliation import assert_canonical_l2
    assert_canonical_l2(BASE)


def load(name):
    if name in {"fig_data_l2.csv", "fig_data_levels.csv", "efficiency_by_model.csv"}:
        check_score_sources()
    """Read one extracted table (see extract_figure_data.py). Numbers are coerced; '' stays None."""
    import csv as _csv
    out = []
    with open(os.path.join(BASE, "results", name)) as fh:
        for r in _csv.DictReader(fh):
            row = {}
            for k, v in r.items():
                if v == "" or v is None:
                    row[k] = None
                elif v in ("True", "False"):
                    row[k] = v == "True"
                else:
                    try:
                        row[k] = float(v) if ("." in v or "e" in v.lower()) else int(v)
                    except ValueError:
                        row[k] = v
            out.append(row)
    return out


def tidy(ax, axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)
    ax.set_axisbelow(True)
    ax.grid(True, axis=axis, alpha=0.9)
    ax.tick_params(length=0)


def footnote(ax, text, y=-0.24, fontsize=6.8):
    """Caption-style note under an axes, WRAPPED to the axes width.

    This used to place the string verbatim. Nothing clips it, so a long line ran past the axes and the
    tight bbox added the overhang to the emitted PDF -- and because text does not scale with figsize,
    shrinking the figure could not fix it. Four figures were pushed over ICLR's 5.5 in text width by
    their footnote alone (F14 by 1.65 in). Wrapping to the measured axes width removes the failure mode
    instead of hand-tuning each string; explicit newlines in `text` are still honoured as hard breaks.
    """
    import textwrap as _tw
    fig = ax.get_figure()
    width_in = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted()).width
    ncols = max(24, int(width_in / (fontsize * 0.0072)))     # DejaVu Sans averages ~0.52 em per char
    wrapped = "\n".join(l for para in text.split("\n")
                        for l in (_tw.wrap(para, ncols) or [""]))
    ax.text(0, y, wrapped, transform=ax.transAxes, fontsize=fontsize, color=INK3, linespacing=1.5,
            va="top")


def title(ax, text, loc="left", pad=8, fontsize=None, **kw):
    """Axes title, WRAPPED to the figure width.

    Same failure as the un-wrapped footnote: a loc="left" title extends right from the axes and never
    wraps, so a long one runs past the canvas and the tight bbox adds the overhang to the emitted PDF.
    Three figures were pushed over ICLR's 5.5 in text width by their title alone (F04C by 1.2 in), and
    because text does not scale with figsize, narrowing the figure could not fix it.
    """
    import textwrap as _tw
    fig = ax.get_figure()
    fs = fontsize if fontsize is not None else plt.rcParams["axes.titlesize"]
    avail = fig.get_size_inches()[0] - ax.get_position().x0 * fig.get_size_inches()[0]
    ncols = max(24, int(avail / (fs * 0.0074)))          # bold title, ~0.53 em per char
    ax.set_title("\n".join(_tw.wrap(text, ncols)), loc=loc, pad=pad, linespacing=1.3, **kw)


def save(fig, name, rows, fieldnames):
    """Vector PDF + SVG + 300-dpi PNG, plus the companion CSV of exactly the plotted values."""
    os.makedirs(OUT, exist_ok=True)
    # pad_inches MUST be 0. Every script here is authored at final size and sizes its canvas to the
    # drawn content, but matplotlib's "tight" bbox adds a 0.1 in default pad on EACH side -- so a figure
    # authored at 5.5 in was emitted at 5.70 in, scaled DOWN by LaTeX to the 5.5 in column, and every
    # 7.5 pt glyph landed at 7.2 pt. The whole set was silently under the legibility floor.
    # 0.01 was not small enough either: 0.02 in of total pad still pushed a float authored at exactly
    # \textwidth to 5.52 in, over the 5.50 in gate. At 0 the emitted width IS the authored width.
    # White space around a float is LaTeX's job, not the PDF's.
    for ext, dpi in (("pdf", None), ("svg", None), ("png", 300)):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=dpi, bbox_inches="tight",
                    pad_inches=0.0)
    plt.close(fig)
    with open(os.path.join(OUT, f"{name}.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: pdf+svg+png+csv -> results/figures/  ({len(rows)} plotted rows)")
