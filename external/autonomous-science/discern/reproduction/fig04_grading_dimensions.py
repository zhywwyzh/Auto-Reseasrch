"""Figure 4 -- the grading dimensions, every stage, every model.

REPLACES SIX ARTIFACTS: F04A/B/C (clean-vs-injected, clean outcomes, injected process), F06A
(confound vs trap), F08A/B (L3 D-Q-N and the seven axes). Those said one thing each about one stage;
this says all of it in one grid, which is what a reader needs to compare a model's profile ACROSS
stages rather than flipping between panels.

MODELLED ON BIOMNIBENCH FIGURE 4(b) -- "percentage of available rubric points earned along the six
evaluation dimensions" -- generalised from one stage to three, and on DISCOVERYWORLD TABLE 4's
principle that an agent is never reduced to one number.

WHY THE ROWS ARE GROUPED THE WAY THEY ARE, and this is a finding, not a layout choice:

  * CLEAN SPECIFICITY and PERTURBED HANDLING are measured IDENTICALLY at L1 and L2 and are shown as
    paired sub-cells, blue L1 next to amber L2. That parallel is real: every L2 track carries exactly
    three clean worlds (24 in total) against 79 perturbed, mirroring L1's 8 clean against 71 perturbed.
    Two-sided calibrated trust is therefore measured twice on the same substrates, at two stages.
  * THE FOUR RUBRIC CATEGORIES ARE NOW MEASURED AT BOTH L1 AND L2, and this is new. Until the
    2026-08-26 L2 meta-review, L2 had no shared vocabulary -- four tracks recorded no state at all and
    three more recorded only "OK" -- so recognition, response and calibration could not be computed
    benchmark-wide and these rows had to be L1-only. The meta-review closed that: it maps all 612
    canonical L2 cells onto four shared [0,1] dimensions, so each category can be shown as a paired
    sub-cell, blue L1 beside amber L2. L1's counterparts come from its 12-state machine, which has
    always been benchmark-wide.
    CAVEAT that belongs in the caption, not a footnote: the four L2 dimensions are a DECOMPOSITION of
    the recorded grades, not four independent measurements. Where a legacy grader stored only a ladder
    and a flag, methodological response and result calibration fall back to documented functions of the
    recorded score, so they are partly collinear with analytical correctness by construction.
  * THE L3 ROWS ARE THE SEVEN GRADED AXES, ordered D, then the five Q axes, then N -- the order in
    which the composite actually combines them (mean of D, aggregate Q, N), so the five Q axes visibly
    belong to one term.
  * HYPOTHESIS PRODUCED sits immediately before novelty, and it is a RATE, not a graded axis. Novelty
    is only recorded when a model commits: 52 of the 131 graded outputs are an ABSTAIN-* state with
    no N at all. Reading the novelty row alone therefore compares models on different denominators and
    is actively misleading -- GPT-5.6-sol and Claude look nearly tied (1.25 vs 1.24 mean N) while
    GPT-5.6-sol declined on 18 of 22 worlds and Claude on 4. The novelty row is labelled
    "| committed" for the same reason. Their product, P(commit) x E[N | commit], is the discovery
    YIELD and is Figure 6B's subject; it is deliberately not a row here, because it is a derived
    reporting statistic and not something any grader scored.
  * TWO GATE EXCLUSIONS, TWO REPRESENTATIONS, and a denominator trap. cf_gwas/cf_GSTM1/kimi-k3 carries
    an explicit CONFOUNDED-EXCLUDED state, while bulk_rnaseq/cf_cytokine_flip/claude-opus-5 is simply
    ABSENT from the extract. A denominator that filters only on the state label gets Claude wrong; one
    that counts rows gets Kimi wrong. Both are handled here.

Everything is PERCENTAGE OF AVAILABLE POINTS, so a row is comparable across models and rows are
comparable to each other. Hue is the stage, exactly as in Figure 3; intensity is the value.

AUTHORED AT FINAL SIZE: 5.5 in wide, every glyph >= 7.5 pt, canvas sized to the drawn content.

Caption draft, kept here so figure and caption stay in sync:

    Figure 4: What each stage measures, by model. Cells give the percentage of available points earned
    on each grading dimension. Clean specificity and perturbed handling are measured identically at L1
    and L2 and appear as paired sub-cells (blue L1, amber L2): every L2 track carries three clean
    worlds against a perturbed remainder, mirroring L1's one clean world per track, so two-sided
    calibrated trust is measured twice on the same substrates. The process rows are L1-only because L2
    has no shared state vocabulary -- L1 resolves every task through one benchmark-wide state machine,
    while at L2 four tracks record no state and three more record only "OK". The seven L3 axes are
    ordered D, the five Q axes, then N, the order in which the L3 composite combines them. Columns are
    in a frozen model order, not by rank.

Run: .venv_bench/bin/python fig04_grading_dimensions.py
"""
import collections
import statistics
import matplotlib.pyplot as plt
import fig_common as C

FIG_W, UNIT_IN, TOP_U, BOT_U = 5.5, 6.21, 1.0, -0.70
RAMP = {
    "L1": ["#EDF3F9", "#D3E3F0", "#AFCCE4", "#7FAED2", "#4F87BC", "#255E92", "#123C63"],
    "L2": ["#FDF4E7", "#F8E3C3", "#F0CB93", "#E4AC5C", "#CE8A2E", "#A5670F", "#6F4408"],
    "L3": ["#EDF6F0", "#D2E9DA", "#AAD5BC", "#7CBB97", "#4C9C71", "#2A7A50", "#14532D"],
}
DARK_FROM = 4
FS_VAL, FS_LAB, FS_HEAD, FS_GRP = 7.5, 7.5, 7.6, 7.5

l1 = C.load("fig_data_l1.csv")
l2 = C.load("fig_data_l2.csv")
l3 = C.load("fig_data_l3.csv")

def l2_macro(rows, key):
    families = collections.defaultdict(list)
    for row in rows:
        if row.get(key) is not None:
            families[(row["track"], row["family"])].append(row[key])
    tracks = collections.defaultdict(list)
    for (track, family), values in families.items():
        tracks[track].append(statistics.mean(values))
    return statistics.mean(statistics.mean(v) for v in tracks.values()) if tracks else None

# ---- shared L1/L2 dimensions: identical definitions, both stages -----------------------------------
def split(rows, model, clean):
    if rows is l2:
        selected = [r for r in rows if r["model"] == model
                    and str(r["world"]).lower().startswith("clean") == clean]
        return 100 * l2_macro(selected, "score") / 3
    v = [r["score"] for r in rows if r["model"] == model and r["score"] is not None
         and (str(r["world"]).lower().startswith("clean")) == clean]
    return 100 * statistics.mean(v) / 3 if v else None


SHARED = {}
for m in C.MODEL_ORDER:
    SHARED[("clean specificity", m)] = (split(l1, m, True), split(l2, m, True))
    SHARED[("perturbed handling", m)] = (split(l1, m, False), split(l2, m, False))

# ---- the four shared rubric categories, L1 from the state machine and L2 from the meta-review -------
ST = collections.Counter((r["model"], r["state"]) for r in l1 if not r["is_clean"])
NP = {m: sum(v for (mm, _s), v in ST.items() if mm == m) for m in C.MODEL_ORDER}
ACT = {"DIAGNOSE-AND-ACT", "DIAGNOSE-AND-ACT-PARTIAL"}
DIAG = ACT | {"DIAGNOSE-NOT-ACT"}
BLIND = {"MISS", "NONCOMPLIANT"}
HALL = {m: statistics.mean([r["hallucination_rate"] for r in l1 if r["model"] == m
                            and r["hallucination_rate"] is not None]) for m in C.MODEL_ORDER}
# L1 counterparts of the four categories. MISCAL = the states where the model's confidence was wrong in
# either direction: it invented a defect, or it declared usable data unusable. That is exactly what L2's
# result_calibration measures, so the pair is like-for-like.
MISCAL = {"OVER-DIAGNOSE", "FALSE-UNUSABLE", "OVER-CAUTIOUS", "NONCOMPLIANT"}
NALL = {m: len([r for r in l1 if r["model"] == m]) for m in C.MODEL_ORDER}
SHARED4 = {}
for m in C.MODEL_ORDER:
    n = NP[m]
    l1v = {
        "analytical correctness": 100 * statistics.mean(
            [r["score"] for r in l1 if r["model"] == m and r["score"] is not None]) / 3,
        "issue recognition": 100 * sum(ST[(m, s)] for s in DIAG) / n,
        "methodological response": 100 * sum(ST[(m, s)] for s in ACT) / n,
        "result calibration": 100 * (1 - sum(1 for r in l1 if r["model"] == m
                                             and r["state"] in MISCAL) / NALL[m]),
    }
    for lab, key in (("analytical correctness", "analytical_correctness"),
                     ("issue recognition", "issue_recognition"),
                     ("methodological response", "methodological_response"),
                     ("result calibration", "result_calibration")):
        v = l2_macro([r for r in l2 if r["model"] == m], key)
        SHARED4[(lab, m)] = (l1v[lab], 100 * v if v is not None else None)

L1_ONLY = {m2: 100 * (1 - HALL[m2]) for m2 in C.MODEL_ORDER}

# ---- L3 axes, in composite order: D, the five Q axes, then N ---------------------------------------
AXES = [("data_fidelity", "D  evidence fidelity"), ("prior_awareness", "Q  prior awareness"),
        ("causal_calibration", "Q  causal calibration"), ("reviewer_robustness",
                                                          "Q  response to critique"),
        ("scientific_humility", "Q  scientific humility"), ("citation_integrity",
                                                            "Q  citation integrity"),
        ("novelty", "N  valid novelty | committed")]

# Commitment rate: committed / eligible, where eligible EXCLUDES both gate exclusions (see the docstring
# -- one is a state label, the other a missing row, so neither filter alone is correct).
COMMIT = {}
for m in C.MODEL_ORDER:
    elig = [r for r in l3 if r["model"] == m and r["state"] != "CONFOUNDED-EXCLUDED"]
    com = [r for r in elig if not str(r["state"]).startswith("ABSTAIN")]
    COMMIT[m] = 100 * len(com) / len(elig) if elig else None
L3_ROWS = {}
for m in C.MODEL_ORDER:
    for key, lab in AXES:
        v = [r[key] for r in l3 if r["model"] == m and r.get(key) is not None
             and r["state"] != "CONFOUNDED-EXCLUDED"
             and not str(r["state"]).startswith("ABSTAIN")]
        L3_ROWS[(lab, m)] = 100 * statistics.mean(v) / 3 if v else None


def shade(stage, v):
    r = RAMP[stage]
    i = min(len(r) - 1, max(0, int(v / 100 * len(r))))
    return r[i], ("white" if i >= DARK_FROM else C.INK)


# XL 0.265: the longest row labels ("methodological response", "N  valid novelty | committed") ran
# right up against the first value cell at 0.245. CW trimmed so XL + 6*CW still lands inside 1.0.
XL, CW = 0.265, 0.122
RH, GAPY = 0.021, 0.004
xs = [XL + i * CW for i in range(len(C.MODEL_ORDER))]

fig, ax = plt.subplots(figsize=(FIG_W, UNIT_IN * (TOP_U - BOT_U)))
ax.set_position([0.0, 0.0, 1.0, 1.0])
ax.axis("off")
ax.patch.set_visible(False)
ax.set_xlim(0, 1); ax.set_ylim(BOT_U, TOP_U)

# Panel letter: 4A and 4B are stacked as one float, so each half needs to announce itself.
ax.text(0.004, TOP_U - 0.004, "B.  Grading dimensions", fontsize=8.6, fontweight="bold",
        color=C.INK, va="top")
top = TOP_U - 0.056
for m, x in zip(C.MODEL_ORDER, xs):
    ax.text(x + CW / 2, top + 0.006, C.SHORT[m], ha="center", va="bottom", fontsize=FS_HEAD,
            color=C.INK)
ax.plot([0, XL + len(C.MODEL_ORDER) * CW], [top - 0.010] * 2, color=C.INK2, lw=1.0)

y = top - 0.010


def group(label, note=None):
    """Section heading, with its note on its OWN LINE.

    The note used to be placed at a fixed x offset on the heading's baseline, which assumed every
    heading was short. "two-sided trust" ran into "clean vs perturbed, both stages" and "shared rubric"
    into "L1 state machine - L2 meta-review". Stacking removes the assumption entirely.
    """
    global y
    y -= 0.026
    ax.text(0.004, y, label, fontsize=FS_GRP, color=C.INK, fontweight="bold", va="center")
    if note:
        y -= 0.015
        ax.text(0.004, y, note, fontsize=7.0, color=C.INK3, va="center")
    y -= 0.008


def row(label, getter, stages):
    """One dimension row; `stages` is 1 or 2 stage keys, drawn as sub-cells left to right."""
    global y
    y -= RH + GAPY
    cy = y + RH / 2
    ax.text(0.004, cy, label, fontsize=FS_LAB, color=C.INK, va="center")
    sw = CW / len(stages)
    for m, x in zip(C.MODEL_ORDER, xs):
        vals = getter(m)
        for k, (stage, v) in enumerate(zip(stages, vals if isinstance(vals, tuple) else (vals,))):
            sx = x + k * sw
            if v is None:
                ax.text(sx + sw / 2, cy, "–", ha="center", va="center", fontsize=FS_VAL,
                        color=C.INK3)
                continue
            face, ink = shade(stage, v)
            ax.add_patch(plt.Rectangle((sx + 0.0012, y + 0.0012), sw - 0.0024, RH - 0.0024,
                                       facecolor=face, edgecolor="none"))
            ax.text(sx + sw / 2, cy, f"{v:.0f}", ha="center", va="center", fontsize=FS_VAL,
                    color=ink)


group("two-sided trust", "clean vs perturbed, both stages")
for lab in ("clean specificity", "perturbed handling"):
    row(lab, lambda m, lab=lab: SHARED[(lab, m)], ("L1", "L2"))
group("shared rubric", "L1 state machine · L2 meta-review")
for lab in ("analytical correctness", "issue recognition", "methodological response",
            "result calibration"):
    row(lab, lambda m, lab=lab: SHARED4[(lab, m)], ("L1", "L2"))
group("integrity", "L1 only")
row("no fabrication", lambda m: L1_ONLY[m], ("L1",))
group("L3 axes", "composite = mean(D, mean of Q, N)")
for _key, lab in AXES:
    if lab.startswith("N "):
        row("hypothesis produced", lambda m: COMMIT[m], ("L3",))
    row(lab, lambda m, lab=lab: L3_ROWS[(lab, m)], ("L3",))

y -= 0.014
ax.plot([0, XL + len(C.MODEL_ORDER) * CW], [y] * 2, color=C.INK2, lw=1.0)

_y_end = y - 0.010
ax.set_ylim(_y_end, TOP_U)
fig.set_size_inches(FIG_W, UNIT_IN * (TOP_U - _y_end))

rows_out = []
for lab in ("clean specificity", "perturbed handling"):
    for m in C.MODEL_ORDER:
        a, b = SHARED[(lab, m)]
        rows_out.append({"group": "two-sided trust", "dimension": lab, "model": C.FULL[m],
                         "L1_pct": None if a is None else round(a, 2),
                         "L2_pct": None if b is None else round(b, 2), "L3_pct": None})
for lab in ("analytical correctness", "issue recognition", "methodological response",
            "result calibration"):
    for m in C.MODEL_ORDER:
        a, b = SHARED4[(lab, m)]
        rows_out.append({"group": "shared rubric", "dimension": lab, "model": C.FULL[m],
                         "L1_pct": None if a is None else round(a, 2),
                         "L2_pct": None if b is None else round(b, 2), "L3_pct": None})
for m in C.MODEL_ORDER:
    rows_out.append({"group": "integrity", "dimension": "no fabrication", "model": C.FULL[m],
                     "L1_pct": round(L1_ONLY[m], 2), "L2_pct": None, "L3_pct": None})
for _k, lab in AXES:
    if lab.startswith("N "):
        for m in C.MODEL_ORDER:
            rows_out.append({"group": "L3 axes", "dimension": "hypothesis produced",
                             "model": C.FULL[m], "L1_pct": None, "L2_pct": None,
                             "L3_pct": round(COMMIT[m], 2)})
    for m in C.MODEL_ORDER:
        v = L3_ROWS[(lab, m)]
        rows_out.append({"group": "L3 axes", "dimension": lab, "model": C.FULL[m], "L1_pct": None,
                         "L2_pct": None, "L3_pct": None if v is None else round(v, 2)})
C.save(fig, "F04_grading_dimensions", rows_out,
       ["group", "dimension", "model", "L1_pct", "L2_pct", "L3_pct"])
