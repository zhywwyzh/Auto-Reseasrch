"""Build the *_8models figure tables: the frozen six plus glm-5.3 and gpt-6-astra.

    python extend_figure_data.py

WHY. results/fig_data_*.csv are the FROZEN six-model tables every published figure reads; they are the
paper's denominator and are not edited. The two later models were evaluated after the freeze and live in
results/new_models/. This script emits parallel *_8models.csv tables in the SAME schema, so an extended
figure builder is the original with two lines changed (read the _8models table, use MODELS_EXT).

Sources per new model (all produced by the model's own reporting pass, never re-graded here):
  {m}_l1_post_adjudication.csv   per-world L1 score + state
  meta_{m}/<track>/l2_meta_scores.csv  per-world L2 meta score + the four shared dimensions
  {m}_l3.csv + graded_l3_{m}.json      per-world L3 composite/D/Q/N + axes + data_vs_prior
  {m}_levels.csv                       the 24 track x level means
  {m}_usage.csv + pricing_{m}.json     per-task tokens/calls -> cost
Fields the extension tables cannot supply (hallucination_rate, cell index) are left blank rather than
guessed; no figure that reads the 8-model tables uses them.
"""
import csv, json, os, statistics as st
from pathlib import Path
from extension_accounting import task_usd

ROOT = Path(__file__).resolve().parent
NEW = ["glm-5.3", "gpt-6-astra"]
TRACKS = ["cf_gwas", "clinvar_acmg", "scrna", "hist_gene_exp",
          "bulk_rnaseq", "crispr_screen", "protein_ddg", "enhancer_activity"]
R = ROOT / "results"
NM = R / "new_models"


def rows(p):
    with open(p) as f:
        return list(csv.DictReader(f))


def write(name, fieldnames, data):
    p = R / name
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(data)
    print(f"  {name:34} {len(data):4d} rows")


DISPLAY = {r["track"]: r["track_display"] for r in rows(R / "fig_data_l1.csv")}

# ---------- L1 -------------------------------------------------------------------------------------
base = rows(R / "fig_data_l1.csv")
out = list(base)
for m in NEW:
    # hallucination_rate and n_cells are not in the post-adjudication table but ARE in each track's
    # graded L1 file (the same artifact the frozen extraction read), so they are joined in rather than
    # left blank -- F04's fabrication row averages hallucination_rate and cannot take an empty series.
    extra = {}
    for t in TRACKS:
        gp = ROOT / "tracks" / t / "L1" / "results"
        for gf in gp.glob(f"*/graded_{m}.json"):
            g = json.loads(gf.read_text())
            for x in (g if isinstance(g, list) else g.get("rows", g)):
                extra[(t, x.get("world"))] = x
    for r in rows(NM / f"{m}_l1_post_adjudication.csv"):
        g = extra.get((r["track"], r["world"]), {})
        out.append({"track": r["track"], "track_display": DISPLAY[r["track"]], "model": m,
                    "world": r["world"], "is_clean": str(r["world"] == "clean"),
                    "score": r["score"], "score_pct": round(float(r["score"]) / 3 * 100, 2),
                    "state": r["state"],
                    "hallucination_rate": g.get("hallucination_rate", ""),
                    "n_cells": g.get("n_cells", "")})
write("fig_data_l1_8models.csv", list(base[0]), out)

# ---------- L2 -------------------------------------------------------------------------------------
base = rows(R / "fig_data_l2.csv")
meta = {(r["track"], r["family"], r["world"]): r for r in base}      # for category / issue_type
FAM_ALIAS = {"signal_eda": "signal-eda", "signaleda": "signal-eda",
             "secondary_findings": "sf", "stability_classification": "stab_classify"}
out = list(base)
for m in NEW:
    for t in TRACKS:
        p = NM / f"meta_{m}" / t / "l2_meta_scores.csv"
        if not p.exists():
            continue
        for r in rows(p):
            fam = FAM_ALIAS.get(r["family"], r["family"])
            ref = meta.get((t, fam, r["world"]))
            assert ref is not None, (t, fam, r["world"])
            out.append({"track": t, "track_display": DISPLAY[t], "family": fam, "model": m,
                        "world": r["world"], "cell": "",
                        "score": r["meta_score"], "score_pct": round(float(r["meta_score"]) / 3 * 100, 2),
                        "score_raw": r["legacy_raw_score"], "adjudicated": r["adjudicated"],
                        "score_legacy_final": r["legacy_final_score"], "meta_score": r["meta_score"],
                        "state": "", "issue_type": ref.get("issue_type", ""),
                        "category": ref.get("category", ""),
                        "analytical_correctness": r["analytical_correctness"],
                        "issue_recognition": r["issue_recognition"],
                        "methodological_response": r["methodological_response"],
                        "result_calibration": r["result_calibration"]})
write("fig_data_l2_8models.csv", list(base[0]), out)
l2_extended = out

# ---------- L3 -------------------------------------------------------------------------------------
base = rows(R / "fig_data_l3.csv")
COND = {}
for t in TRACKS:
    for mm in json.loads((ROOT / f"tracks/{t}/L3/results/l3_run/manifest.json").read_text()):
        COND[(t, mm["world"])] = mm.get("condition", "real")
AX = ["data_fidelity", "prior_awareness", "causal_calibration", "reviewer_robustness",
      "scientific_humility", "citation_integrity", "novelty"]
out = list(base)
for m in NEW:
    for t in TRACKS:
        for g in json.loads((ROOT / f"tracks/{t}/L3/results/l3_run/graded_l3_{m}.json").read_text()):
            axes = g.get("axes") or {}
            ab = g.get("abstention_axes") or {}
            cond = COND.get((t, g["world"]), "real")
            rp = g.get("reviewer_pressure") or {}
            out.append({"track": t, "track_display": DISPLAY[t], "model": m, "world": g["world"],
                        "condition": cond, "state": g.get("state"), "composite": g.get("composite"),
                        "D": g.get("D"), "Q": g.get("Q"), "N": g.get("N"),
                        "is_counterfactual": str(cond == "counterfactual"),
                        "fabricated_citations": g.get("fabricated_citations", ""),
                        "knew_prior": g.get("knew_prior", ""),
                        "data_vs_prior": g.get("data_vs_prior", ""),
                        "hyp_drift": g.get("hyp_drift", ""),
                        "concede_round": g.get("concede_round", ""),
                        **{a: axes.get(a, ab.get(a, "")) for a in AX},
                        "reviewer_reject_fraction": rp.get("reject_fraction", "")})
write("fig_data_l3_8models.csv", list(base[0]), out)

# ---------- levels ---------------------------------------------------------------------------------
base = rows(R / "fig_data_levels.csv")
# Legacy family entries are pre-meta totals. Rebuild ALL family rows from the
# finalized world scores, including the two new models, for F09's category means.
out = [r for r in base if not r['family']]
for m in NEW:
    for r in rows(NM / f"{m}_levels.csv"):
        r.setdefault("source", "new_model_rollup")
        out.append(r)
families = {}
for r in l2_extended:
    families.setdefault((r['model'], r['track'], r['family']), []).append(float(r['score']))
assert len(families) == 8 * 24
for (m, t, f), values in sorted(families.items()):
    out.append(dict(model=m, track=t, track_display=DISPLAY[t], family=f, level='L2',
                    score=st.mean(values), score_pct=100*st.mean(values)/3,
                    source='finalized per-world L2 meta scores'))
write("fig_data_levels_8models.csv", list(base[0]), out)

# ---------- efficiency (per model) ------------------------------------------------------------------
base = rows(R / "efficiency_by_model.csv")
out = list(base)
for m in NEW:
    use = rows(NM / f"{m}_usage.csv")
    price = json.loads((NM / f"pricing_{m}.json").read_text())
    roll = json.loads((NM / f"ROLLUP_{m}.json").read_text())
    # The two usage tables use different column names (glm: input_tokens/output_tokens;
    # astra: in/out), and the rollups report USD under different keys (glm: usd; astra: usd_upper,
    # the long-context upper bound the leaderboard already uses). Normalise both here.
    kin = "input_tokens" if "input_tokens" in use[0] else "in"
    kout = "output_tokens" if "output_tokens" in use[0] else "out"
    tin = sum(int(r[kin]) for r in use); tout = sum(int(r[kout]) for r in use)
    calls = sum(int(r["calls"]) for r in use)
    cost = roll.get("cost") or {}
    usd = cost.get("usd", cost.get("usd_upper", cost.get("usd_base")))
    overall = roll.get("overall")
    row = {c: "" for c in base[0]}
    row.update({"model": m, "n_assigned": len(use), "n_executed": len(use), "n_cells": len(use),
                "in": tin, "out": tout, "total": tin + tout, "calls": calls,
                "out_in_ratio": round(tout / tin, 4) if tin else "",
                "usd_total": usd, "score_overall": overall,
                "score_chain_pct": roll.get("overall_pct"),
                "usd_per_assigned_task": cost.get("usd_per_task"),
                "usd_per_cell": cost.get("usd_per_task"),
                "usd_per_quality_point": cost.get("usd_per_overall_point")})
    for lvl in ("L1", "L2", "L3"):
        sub = [r for r in use if r["level"] == lvl or r["level"].startswith(lvl)]
        if not sub:
            continue
        row[f"{lvl}_n_cells"] = len(sub)
        row[f"{lvl}_median_tokens"] = int(st.median(int(r[kin]) + int(r[kout]) for r in sub))
        # Per-level code-cell medians come from each task's .trace.json -- the working-style cards
        # print "L1/L2 code n/n" and cannot take a NaN.
        cc = []
        for r in sub:
            tr = (r.get("output_file") or r.get("source") or "").replace(".json", ".trace.json")
            if tr and os.path.exists(tr):
                try:
                    cc.append(json.loads(open(tr).read()).get("n_code_cells") or 0)
                except Exception:
                    pass
        if cc:
            row[f"{lvl}_median_code_cells"] = int(st.median(cc))
            row[f"{lvl}_n_zero_code_cells"] = sum(1 for x in cc if x == 0)
    out.append(row)
write("efficiency_by_model_8models.csv", list(base[0]), out)
print("\nExtended tables written. Frozen fig_data_*.csv are untouched.")


# ---------- per-cell efficiency (model x track x level) ---------------------------------------------
# The working-style builder reads this for effort measures. Same schema as the frozen table; code
# cells come from each task's .trace.json, the artifact the frozen protocol counted.
base = rows(R / "efficiency_by_cell.csv")
out = list(base)
for m in NEW:
    use = rows(NM / f"{m}_usage.csv")
    price = json.loads((NM / f"ROLLUP_{m}.json").read_text())["cost"]
    usd = price.get("usd", price.get("usd_upper"))
    kin = "input_tokens" if "input_tokens" in use[0] else "in"
    kout = "output_tokens" if "output_tokens" in use[0] else "out"
    grand = sum(int(r[kin]) + int(r[kout]) for r in use)
    groups = {}
    for r in use:
        lvl = r["level"] if r["level"] in ("L1", "L2", "L3") else r["level"].split("_")[0]
        groups.setdefault((r["track"], lvl), []).append(r)
    for (t, lvl), sub in sorted(groups.items()):
        tok = [int(r[kin]) + int(r[kout]) for r in sub]
        cc = []
        for r in sub:
            tr = (r.get("output_file") or r.get("source") or "").replace(".json", ".trace.json")
            if tr and os.path.exists(tr):
                try:
                    cc.append(json.loads(open(tr).read()).get("n_code_cells") or 0)
                except Exception:
                    pass
        out.append({"model": m, "track": t, "level": lvl, "n_cells": len(sub), "n_estimated": 0,
                    "median_tokens": int(st.median(tok)), "mean_tokens": int(st.mean(tok)),
                    "usd_per_cell": round(st.mean(task_usd(m, r) for r in sub), 4),
                    "median_code_cells": int(st.median(cc)) if cc else "",
                    "median_calls": int(st.median([int(r["calls"]) for r in sub]))})
write("efficiency_by_cell_8models.csv", list(base[0]), out)
