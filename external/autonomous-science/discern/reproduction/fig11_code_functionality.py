"""Figure 11 -- what the executed code actually DID: functionality distribution of 13,539 code cells.

Modelled on NewtonBench Figure 6, "Functionality distribution for code usage". Their version answers
what an agent uses its code budget for; ours answers the question that matters for this benchmark:
**how much of the executed work is independent verification of a tool's output?**

That is the sharpest thing DISCERN claims to grade -- not whether a tool was invoked, but whether its
plausible output was checked against the data. Until now it was only visible in the scores. Here it is
visible in the code.

Result: the verification share ranges from 2.7% of GPT-4.1's cells to 11.4% of GLM-5.2's -- a four-fold
spread in how much of the work is spent checking rather than producing.

METHOD AND ITS LIMITS. This is a SURFACE classifier over the raw `code` string in each trace cell:
word-boundary regexes, first match wins, priority order as listed in RULES. It does not read semantics.
Two things follow and are shown on the figure rather than buried:
  * verification is split into "explicit" (recompute / cross-check / verify / sanity-check /
    independently) and "assert only", because a bare `assert` is often defensive rather than scientific.
    677 of 869 verification cells carry explicit language; 190 are assert-only.
  * `other` is 0.3% of cells, so the taxonomy covers the corpus rather than hiding a residue.
Plotting-only cells are near-zero (2 of 13,539) because the sandbox is headless -- a real property of
the environment, not a classifier failure.

Run: .venv_bench/bin/python fig10_code_functionality.py
"""
import collections
import glob
import json
import os
import re
import matplotlib.pyplot as plt
import fig_common as C

BASE = os.path.dirname(os.path.abspath(__file__))
EXPLICIT = re.compile(r"\b(recompute|recomputed|cross[_ -]?check|sanity[_ -]?check|double[_ -]?check|"
                      r"independently|verify|verification)\b")
ASSERTISH = re.compile(r"\b(assert|allclose|isclose|np\.testing)\b")
RULES = [
    ("stats", r"\b(scipy\.stats|statsmodels|ttest|mannwhitneyu|wilcoxon|fisher_exact|chi2|pearsonr|"
              r"spearmanr|linregress|multipletests|fdr|benjamini|ols|logit|pvalue|p_value|kstest|"
              r"shapiro)\b"),
    ("tool", r"\b(pydeseq2|DeseqDataSet|deseq|scanpy|anndata|gseapy|esm|torch|pysam|liftover|bagel|"
             r"MMCIF|pyBigWig|pybedtools)\b"),
    ("qc", r"\b(isna|isnull|notna|dropna|duplicated|describe|value_counts|dtypes|nunique|outlier|"
           r"missing|zscore|iqr|quantile)\b"),
    ("viz", r"\b(matplotlib|pyplot|seaborn|savefig)\b"),
    ("wrangle", r"\b(merge|groupby|pivot|astype|concat|reindex|rename)\b"),
    ("inspect", r"\b(read_csv|read_table|read_json|listdir|glob|head|shape|columns|print)\b"),
]
ORDER = ["verify_explicit", "verify_assert", "qc", "stats", "tool", "wrangle", "inspect", "viz",
         "other"]
LABEL = {"verify_explicit": "verify (explicit)", "verify_assert": "verify (assert only)",
         "qc": "QC / diagnostics", "stats": "statistics", "tool": "domain tool call",
         "wrangle": "data wrangling", "inspect": "inspect / load", "viz": "plotting",
         "other": "other"}
FILL = {"verify_explicit": "#1B6B50", "verify_assert": "#7FBFA3", "qc": "#20618F",
        "stats": "#5E94C4", "tool": "#B4CFE4", "wrangle": "#E8C9A0", "inspect": "#E8A33D",
        "viz": "#C9C9C9", "other": "#9B9B9B"}


def classify(code):
    if EXPLICIT.search(code):
        return "verify_explicit"
    if ASSERTISH.search(code):
        return "verify_assert"
    for name, pat in RULES:
        if re.search(pat, code):
            return name
    return "other"


# tracks/ holds directories that are NOT part of DISCERN -- orbital, oscillations, calorimetry -- built
# on the same harness with the same roster model names, so nothing about their paths or filenames
# excludes them. Name the eight explicitly; a bare tracks/* glob silently mixes them in.
TRACKS = {"protein_ddg", "enhancer_activity", "bulk_rnaseq", "cf_gwas", "clinvar_acmg", "scrna",
          "hist_gene_exp", "crispr_screen"}

cnt = collections.Counter()
skipped = []
for f in sorted(glob.glob(os.path.join(BASE, "tracks/*/L*/results/*/out_*.trace.json"))):
    if os.path.relpath(f, BASE).split("/")[1] not in TRACKS:
        continue
    if os.path.basename(os.path.dirname(f)).startswith("_"):
        continue
    hits = [m for m in C.MODEL_ORDER if m in os.path.basename(f)]
    if not hits:
        continue
    model = max(hits, key=len)
    try:                                    # a truncated or 0-byte trace must not kill the figure
        with open(f) as fh:
            trace = json.load(fh).get("code_trace") or []
    except (ValueError, OSError):
        skipped.append(os.path.relpath(f, BASE))
        continue
    for cell in trace:
        cnt[(model, classify(cell.get("code") or ""))] += 1
if skipped:
    print(f"  note: skipped {len(skipped)} unreadable trace file(s): {skipped[:3]}")

n = {m: sum(cnt[(m, k)] for k in ORDER) for m in C.MODEL_ORDER}
TOTAL = sum(n.values())

# ICLR text width is 5.5 in, SINGLE COLUMN (figure* does not widen anything). Labels and
# footnotes outside the axes are added on top of figsize by the tight bbox and do not scale
# with it, so author narrower than the target. Verified by check_figure_contract.py.
fig, ax = plt.subplots(figsize=(5.05, 2.9))
for i, m in enumerate(C.MODEL_ORDER):
    left = 0.0
    for k in ORDER:
        w = 100 * cnt[(m, k)] / n[m]
        if w == 0:
            continue
        ax.barh(i, w, left=left, height=0.62, color=FILL[k], edgecolor="white", linewidth=1.1,
                zorder=3)
        left += w
    v = 100 * (cnt[(m, "verify_explicit")] + cnt[(m, "verify_assert")]) / n[m]
    ax.text(101.8, i, f"{v:.1f}%", va="center", ha="left", fontsize=7, color=C.INK,
            fontweight="bold")

handles = [plt.Rectangle((0, 0), 1, 1, color=FILL[k]) for k in ORDER]
ax.set_yticks(range(len(C.MODEL_ORDER)))
ax.set_yticklabels([f"{C.SHORT[m]}\nn={n[m]:,}" for m in C.MODEL_ORDER], fontsize=7,
                   color=C.INK, linespacing=1.5)
ax.invert_yaxis()
ax.set_xlim(0, 100); ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0", "25", "50", "75", "100%"])
ax.set_xlabel("Share of that model's executed code cells")
ax.set_title("How much of the work is checking rather than producing?", loc="left")
ax.legend(handles, [LABEL[k] for k in ORDER], loc="upper center", bbox_to_anchor=(0.5, -0.36),
          ncol=3, handlelength=1.0, columnspacing=1.2, labelspacing=0.35, fontsize=7)
C.footnote(ax, f"Right of each bar: total verification share. {TOTAL:,} executed code cells across "
               "L1 and L2. Surface classifier over the raw code\nstring — word-boundary regexes, first "
               "match wins — so it reads form, not meaning. Verification is split because a bare "
               "`assert`\nis often defensive rather than scientific. Plotting is ~0 because the "
               "sandbox is headless. 'other' is 0.3% of cells.", y=-0.72)
C.tidy(ax, axis="x")

C.save(fig, "F11_code_functionality",
       [{"model": C.FULL[m], "n_code_cells": n[m],
         **{LABEL[k]: cnt[(m, k)] for k in ORDER},
         "verify_share_pct": round(100 * (cnt[(m, "verify_explicit")] + cnt[(m, "verify_assert")])
                                   / n[m], 2)} for m in C.MODEL_ORDER],
       ["model", "n_code_cells"] + [LABEL[k] for k in ORDER] + ["verify_share_pct"])
