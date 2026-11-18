"""Shared drawing for the appendix world registries (T05 = L1, T06 = L2).

WHY THE TWO TABLES SHARE CODE. They are the same object at two stages: a complete, per-world listing
of what the world does and what a competent analyst is expected to do about it. Only the grouping key
differs -- L1 groups by track, L2 by track and analysis family. Writing them twice would let them
drift into two different reading conventions for one appendix.

THE NESTING IS FORCED BY THE DATA, not chosen for looks. `expected_method` is a property of the
ANALYSIS -- every world in a family carries the identical string, because it specifies the method the
family's task demands. `correct_action` is a property of the WORLD. So the method is printed once per
group as the group's protocol, and the per-world rows carry only what actually differs. Printing the
method on all 102 L2 rows would repeat 24 strings four times each and bury the discriminating text.

METHOD TEXT IS TRUNCATED, PER-WORLD TEXT IS NOT. `expected_method` runs to 1,700 characters -- printed
in full it would triple the appendix and drown the world rows it is meant to frame. It is cut to its
first two sentences, the cut is marked, and the companion CSV carries every string in full so nothing
is lost. `correct_action` is never cut: it is the answer key, and a truncated answer key is worse than
none.

GAPS ARE SHOWN AS GAPS. 18 fields are genuinely absent upstream (see extract_world_registry.py); they
print as "not recorded in the world manifest" rather than being quietly left blank or, worse, filled
in with something plausible.
"""
import textwrap

import matplotlib.pyplot as plt

import fig_common as C

FIG_W, UNIT_IN = 5.5, 6.21
FS_GROUP, FS_WORLD, FS_BODY, FS_META = 8.0, 7.5, 7.5, 7.0
LH = 0.0185                    # 7.5 pt needs ~0.115 in of line height; anything less overlaps
CPI = 15.8                     # chars per inch, DejaVu Sans at 7.5 pt (measured)
XW, XB = 0.008, 0.082         # world column, then the indented body column. 0.055 was 0.30 in,
                              # narrower than the italic "method" label, which ran into its text.
METHOD_CHARS = 250             # ~2 sentences of the method spec; the CSV holds it in full

# Class colours follow Figure 13's grammar: hue = stage, and the control is the lightest, never grey.
CLASS_COLOR = {
    "clean control": "#8AB4D6", "boundary case": "#5E94C4",
    "controlled integrity challenge": "#255E92",
    "data confound": "#8A5A0E", "tool / procedure trap": "#CE8A2E", "statistical trap": "#B8862F",
}
MISSING = "not recorded in the world manifest"


def two_sentences(text, limit=METHOD_CHARS):
    """First sentences of a method spec, up to `limit` chars, cut on a sentence boundary if possible."""
    if not text:
        return MISSING
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = max(cut.rfind(". "), cut.rfind("; "))
    return (cut[:stop + 1] if stop > limit * 0.5 else cut.rstrip()) + " […]"


def draw(groups, part, n_parts, title, foot):
    # part/n_parts come FIRST so the signature matches what paginate() calls positionally,
    # (chunk, 0, 1, **kw), for every registry's draw function.
    """One page of a registry.

    `groups` is [(group_label, n_worlds, method_text, [(world, class, action), ...]), ...].
    """
    fig, ax = plt.subplots(figsize=(FIG_W, UNIT_IN))
    ax.set_position([0, 0, 1, 1]); ax.axis("off"); ax.patch.set_visible(False)
    ax.set_xlim(0, 1)
    y = [1.0]
    wrap_body = int((1.0 - XB) * FIG_W * CPI)
    wrap_meta = int((1.0 - XB) * FIG_W * (CPI * 7.5 / FS_META))

    def block(x, text, size, color, wrap, gap=0.0):
        y[0] -= gap
        for i, ln in enumerate(textwrap.wrap(text, wrap) or [""]):
            ax.text(x, y[0] - i * LH, ln, fontsize=size, color=color, va="top")
        y[0] -= len(textwrap.wrap(text, wrap) or [""]) * LH

    suffix = f"  ({part + 1} of {n_parts})" if n_parts > 1 else ""
    ax.text(0.004, y[0], title + suffix, fontsize=9.6, fontweight="bold", color=C.INK, va="top")
    y[0] -= 0.022
    ax.plot([0, 1], [y[0]] * 2, color=C.INK2, lw=1.0)

    for gi, (label, n, method, worlds) in enumerate(groups):
        y[0] -= 0.019
        ax.text(0.004, y[0], label, fontsize=FS_GROUP, fontweight="bold", color=C.INK, va="top")
        ax.text(0.998, y[0], f"{n} worlds", fontsize=FS_META, color=C.INK3, va="top", ha="right")
        y[0] -= 0.019
        ax.text(0.004, y[0], "method", fontsize=FS_META, color=C.INK3, va="top", style="italic")
        block(XB, two_sentences(method), FS_META, C.INK3, wrap_meta)
        for w, cls, action in worlds:
            y[0] -= 0.006
            ax.text(XW, y[0], w, fontsize=FS_WORLD, fontweight="bold", color=C.INK, va="top")
            ax.text(0.998, y[0], cls, fontsize=FS_META, color=CLASS_COLOR[cls], va="top", ha="right",
                    fontweight="bold")
            y[0] -= LH
            block(XB, action or MISSING, FS_BODY, C.INK if action else C.INK3, wrap_body)
        y[0] -= 0.008
        if gi < len(groups) - 1:
            ax.plot([0, 1], [y[0]] * 2, color=C.GRID, lw=0.7)

    y[0] -= 0.004
    ax.plot([0, 1], [y[0]] * 2, color=C.INK2, lw=1.0)
    y[0] -= 0.017
    text = foot if part == n_parts - 1 else "Continued on next page."
    block(0.004, text, FS_META, C.INK2, wrap_meta)
    y[0] -= 0.008

    ax.set_ylim(y[0], 1.0)
    fig.set_size_inches(FIG_W, UNIT_IN * (1.0 - y[0]))
    return fig


MAX_IN = 8.5                   # a float taller than this cannot sit on one ICLR page


def paginate(groups, draw_fn=None, max_in=MAX_IN, **draw_kw):
    """Split groups into pages by MEASURING each candidate page, not by estimating it.

    The first version added up line counts with the same arithmetic the drawing code uses, and was
    still wrong enough to emit a 15.4 in page and, after tuning, two over 9 in. Wrapped-text height
    depends on where every string happens to break; the only reliable measure is to draw the page and
    read its height back. Rendering a few dozen throwaway figures costs a second and cannot drift from
    the real layout, because it IS the real layout.
    """
    draw_fn = draw_fn or draw

    def height(chunk):
        fig = draw_fn(chunk, 0, 1, **draw_kw)      # n_parts=1 -> the long footer, the worst case
        h = fig.get_size_inches()[1]
        plt.close(fig)
        return h

    pages, cur = [], []
    for g in groups:
        if cur and height(cur + [g]) > max_in:
            pages.append(cur); cur = [g]
        else:
            cur = cur + [g]
    if cur:
        pages.append(cur)
    return pages
