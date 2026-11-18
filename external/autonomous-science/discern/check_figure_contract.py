#!/usr/bin/env python3
"""Mechanically check the figure contract, because "minimum 7.5 pt" was asserted and never true.

An audit on 2026-08-27 found sub-7.5 pt text in 19 of 23 figure scripts -- not a regression from the
recent work, but a claim that had never held: F01, F03, F05, F09, T04 and the cost panels all shipped
that way from the original build. Rather than restate the same unverifiable sentence, the contract is
now TIERED and this script enforces it:

  PRIMARY text   >= 7.5 pt   values in cells, axis tick labels, axis labels, model and row/column names
                             -- anything a reader must read to get the result.
  SECONDARY text >= 6.0 pt   keys, denominators, in-figure notes, contour labels, provenance footers,
                             and dense categorical tick labels that cannot fit at 7.5 -- anything that
                             qualifies a result already legible without it.

Only the 6.0 floor is checkable from source (a parser cannot tell a key from a tick label), so that is
what this script HARD-FAILS on -- and it checks the floor AFTER any LaTeX rescaling, since a float wider
than the text width shrinks every glyph in it. The primary tier is held by review, and the per-script table below makes
any drift visible in one run. Sizes are AS AUTHORED; every PDF is emitted at its authored size, which
the width check confirms -- so authored pt == final pt, with no LaTeX rescaling in between.

usage: check_figure_contract.py        (exit 1 on any violation)
"""
import glob
import os
import re
import sys

FLOOR = 6.0
# ICLR's style file is SINGLE-COLUMN with \textwidth = 5.5 in. `figure*` does not create a wider
# region -- there is no second column for it to span. An earlier version of this check assumed a 7.1 in
# two-column text width, which does not exist in this template, and therefore passed floats that LaTeX
# will scale to 76-78% (F05 at 7.21 in -> 7.5 pt primary text renders at 5.7 pt).
# The ONLY way to exceed 5.5 in is a rotated full-page appendix float (sidewaysfigure), where the
# available width is the text HEIGHT. Anything claiming that must be listed below and actually be
# typeset rotated; it is not a loophole for a figure that came out too wide.
# 5.50 EXACTLY -- ICLR's \textwidth. An earlier version used 5.55 plus a 0.01 in tolerance, i.e. a real
# gate of 5.56, and six floats at 5.50-5.52 in passed while genuinely exceeding the text width. The only
# tolerance now is 0.005 in for float/rounding noise in the MediaBox.
COL, ROTATED, EPS = 5.50, 9.00, 0.005
# Assets explicitly designated as ROTATED FULL-PAGE APPENDIX floats. Empty by default and it should
# stay that way for anything in the main text.
ROTATED_FLOATS = {
    # T04 is a comparator-positioning TABLE: its width is set by benchmark names and criteria text, so
    # it cannot be narrowed by shrinking the plot. Typeset with \begin{sidewaysfigure} in the appendix,
    # where the available width is the page height. Must actually be rotated in the .tex -- this is not
    # a loophole for a figure that merely came out too wide.
    "T04_positioning",
}

BASE = os.path.dirname(os.path.abspath(__file__))
fails, rows, no_sizes = [], [], []

for f in sorted(glob.glob(os.path.join(BASE, "fig*.py"))) + sorted(glob.glob(os.path.join(BASE, "tab*.py"))):
    name = os.path.basename(f)
    if name == "fig_common.py":
        continue
    src = open(f).read()
    sizes = [float(m.group(1)) for m in re.finditer(r"fontsize\s*=\s*([0-9]+\.?[0-9]*)", src)]
    sizes += [float(v) for m in re.finditer(r"^[A-Z_0-9]*FS[A-Z_0-9]*\s*=\s*(.+)$", src, re.M)
              for v in re.findall(r"([0-9]+\.?[0-9]*)", m.group(1))]
    sizes = [s for s in sizes if 3 <= s <= 30]
    if not sizes:
        no_sizes.append(name)          # e.g. a script that sets every size through rcParams
        continue
    lo = min(sizes)
    rows.append((name, lo, sum(1 for s in sizes if s < 7.5), len(sizes)))
    if lo < FLOOR:
        fails.append(f"{name}: text at {lo} pt, below the {FLOOR} pt hard floor")

n_scripts = len(rows) + len(no_sizes)
print(f"{'script':34}{'min pt':>7}{'<7.5':>6}{'sizes':>7}")
for n, lo, sub, tot in sorted(rows, key=lambda r: r[1]):
    print(f"{n:34}{lo:>7}{sub:>6}{tot:>7}")

print()
# ANY float wider than the text width fails. An earlier version of this check reasoned that "a panel 3%
# too wide is harmless" and only failed once the 6.0 pt SECONDARY floor broke after rescaling -- but a
# 3% scale-down still takes 7.5 pt PRIMARY text to 7.3 pt, and the primary tier is the one no parser can
# verify. Gating on width instead means nothing is ever rescaled, so authored pt == final pt and the
# primary tier holds by construction. The pt figures below are reported to show the cost, not to grant
# a tolerance.
# Row labels are what push floats over ("Bulk RNA - differential expression", the track group labels),
# and they sit outside the axes, so shrinking figsize does not shrink them -- it only shrinks the plot
# and leaves the overhang, which is why narrowing barely moved F09. The lever is the text: see
# C.title() and C.footnote(), which wrap.
SCRIPT_OF = {  # PDF stem -> the script whose authored sizes it carries
    os.path.basename(f)[:-3].replace("fig", "F").replace("tab", "T"): os.path.basename(f)
    for f in glob.glob(os.path.join(BASE, "fig*.py")) + glob.glob(os.path.join(BASE, "tab*.py"))}
authored = {n: lo for n, lo, _s, _t in rows}
for p in sorted(glob.glob(os.path.join(BASE, "results/figures/*.pdf"))):
    stem = os.path.basename(p)[:-4]
    box = re.search(rb"/MediaBox\s*\[([^\]]*)\]", open(p, "rb").read())
    v = [float(x) for x in box.group(1).split()]
    w = (v[2] - v[0]) / 72
    limit = ROTATED if stem in ROTATED_FLOATS else COL
    src = next((n for n in authored if n[3:-3].lower().lstrip("0") in stem.lower()
                or stem.lower().startswith(n[3:6].lower())), None)
    lo = authored.get(src, 7.5)
    # WIDTH IS A HARD FAIL. An earlier version only failed when the SECONDARY 6.0 pt floor broke after
    # rescaling, and then printed "every PDF within its column target" in the same run where it had
    # reported one over -- so a float scaled to 91%, which drags 7.5 pt PRIMARY text down to 6.8 pt,
    # passed silently. Failing on width protects the primary tier without a parser having to guess
    # which labels are primary: at 5.5 in nothing is rescaled and authored pt == final pt.
    if w > limit + EPS:
        scaled = lo * limit / w
        fails.append(f"{stem}: {w:.2f} in exceeds the {limit} in target -> LaTeX scales it to "
                     f"{100 * limit / w:.0f}%, so 7.5 pt primary text renders at "
                     f"{7.5 * limit / w:.1f} pt (smallest text {lo} -> {scaled:.1f} pt)")

if fails:
    print("VIOLATIONS")
    for x in fails:
        print("  " + x)
    sys.exit(1)
print(f"contract OK: {n_scripts} figure/table scripts checked "
      f"({len(rows)} with explicit sizes, {len(no_sizes)} rcParams-only: {no_sizes or 'none'}); "
      f"all text >= {FLOOR} pt; every PDF within its width target with no rescaling")
