"""Canonical figure-data extraction -- step 1 of FIGURES_2_5_PLAN.md's implementation sequence.

Reads ONLY live (non-archived) graded artifacts plus results/final_scores.json, and emits the tables
every fig_*.py reads. Nothing downstream parses a graded file directly, so no two figures can disagree
about a number.

    results/figure_data_long.csv   the long table the plan specifies
    results/fig_data_l1.csv        one row per L1 task   (score + state + clean/injected)
    results/fig_data_l2.csv        one row per L2 task   (score + state + issue_type)
    results/fig_data_l2_comp.csv   one row per L2 COMPONENT measurement (long)
    results/fig_data_l3.csv        one row per L3 world  (composite, D/Q/N, seven axes)
    results/fig_data_levels.csv    the POST-ADJUDICATION level means from final_scores.json

TWO AUTHORITIES, AND THEY DO NOT AGREE -- this is deliberate and must be respected by every figure:
  * final_scores.json / the *_final_*scores.csv files are POST-adjudication and are the authority for
    any MODEL x TRACK or MODEL x FAMILY mean (Figures 2 and 4).
  * the graded_*.json files are PRE-adjudication; they are the ONLY source of per-world scores, state
    labels and component fields (Figures 3, 5, 6, 7).
  * They differ in 36 of 48 L1 model-track cells, by up to 0.9 points. So a per-world panel and a
    track-mean panel are NOT interchangeable, and any figure built from graded scores says so in its
    footnote. State-label COUNTS are unaffected by adjudication and need no such caveat.
"""
import csv, json, glob, os, collections

BASE = os.path.dirname(os.path.abspath(__file__))
ROSTER = ["gpt-4.1", "gpt-5.6-sol", "claude-opus-5", "deepseek-v4-pro", "glm-5.2", "kimi-k3"]
SKIP = ("_abandoned", "_archive", "_prev", "_dropped", "_mislabeled", "_presearch", "_stale",
        "_solver_first")
# ABANDONED PROBES that are not underscore-prefixed. final_scores.json COVERAGE EXCEPTION 2 records
# scrna_l2_resolution_trap_run as a 1-cell probe whose world was merged into the canonical five-world
# composition run and is NOT part of the scRNA L2 roll-up. It survives on disk with a single gpt-4.1
# graded row, so leaving it in gives gpt-4.1 103 L2 worlds against 102 for every other model and drags
# its L2 mean down by a world nobody else was asked. Excluded by name because the path does not signal it.
SKIP_RUNS = ("scrna_l2_resolution_trap_run",)
TRACK_DISPLAY = {"protein_ddg": "Protein", "enhancer_activity": "Enhancer", "bulk_rnaseq": "Bulk RNA",
                 "cf_gwas": "GWAS", "clinvar_acmg": "ClinVar", "scrna": "scRNA",
                 "hist_gene_exp": "Histone", "crispr_screen": "CRISPR"}
# tracks/orbital/ is NOT one of the eight DISCERN tracks (it is a separate exercise that happens to use
# the same harness and the same roster model names, so nothing about its paths or filenames excludes it).
# Anything globbing tracks/* must name the eight explicitly.
TRACKS = tuple(TRACK_DISPLAY)
# final_scores.json uses a THIRD spelling for some tracks; map once, here, and never again.
TRACK_SCORES_KEY = {"cf_gwas": "GWAS", "clinvar_acmg": "clinvar", "scrna": "scRNA",
                    "crispr_screen": "crispr_screen", "enhancer_activity": "enhancer_activity",
                    "hist_gene_exp": "hist_gene_exp", "protein_ddg": "protein_ddg",
                    "bulk_rnaseq": "bulk_rnaseq"}
# Component fields that exist as structured numbers, with their maxima. Never parse prose (plan step 7).
COMPONENTS = {
    "core_score": 3, "lambda_ok": 1, "assess_ok": 1, "third_axis": 1, "qualified": 1,
    "plausibility_ok": 1, "exec_score": 2, "interp_score": 1, "recall": 1, "precision": 1,
    "issue_handled": 1, "z_corr": 1, "snp_frac": 1, "top_recall": 1, "sign_ok": 1,
    "spearman": 1, "auroc": 1, "bal_acc": 1, "pred_stab_frac": 1, "golden_dominant": 1, "handled": 1,
}
# Family names come from the run directory, which for two tracks does not match the vocabulary used by
# final_scores.json `levels` (and therefore by every figure keyed on family). Normalise once, here, so
# fig_data_l2.csv and fig_data_levels.csv can be joined on (track, family) without per-figure aliasing.
FAMILY_ALIAS = {("cf_gwas", "task2"): "locus", ("cf_gwas", "signaleda"): "signal-eda",
                ("bulk_rnaseq", "bulk_de"): "de", ("bulk_rnaseq", "bulk_gsea"): "gsea",
                ("bulk_rnaseq", "bulk_structure"): "structure"}
L3_AXES = ["data_fidelity", "prior_awareness", "causal_calibration", "reviewer_robustness",
           "scientific_humility", "citation_integrity", "novelty"]


def live(p):
    """A canonical run dir never starts with '_'.

    The named SKIP list is not enough: superseded variants sit beside the canonical run under names
    like `_q2t_anchor` (protein) and `_2reviewer_panel` (crispr), and matching only known names let
    them through, double-counting worlds for some models and not others. Every archived/superseded run
    dir in this repo is underscore-prefixed and no canonical one is, so that is the rule.
    """
    if any(s in p for s in SKIP):
        return False
    if os.path.basename(os.path.dirname(p)) in SKIP_RUNS:
        return False
    return not os.path.basename(os.path.dirname(p)).startswith("_")


def model_of(fname):
    hits = [m for m in ROSTER if m in fname]
    return max(hits, key=len) if hits else None


def family_of(path, level):
    """The L2 analysis family is the run-dir name with the track and boilerplate stripped."""
    run = os.path.basename(os.path.dirname(path))
    for junk in ("_run", "l2_", "L2_"):
        run = run.replace(junk, "")
    for t in list(TRACK_DISPLAY) + ["gwas", "bulk_rna", "bulkrna", "hist", "histone", "crispr",
                                    "enhancer", "protein_ddg", "protein", "clinvar", "scrna"]:
        if run.startswith(t + "_"):
            run = run[len(t) + 1:]
        elif run == t:
            run = "all"
    return run.strip("_") or "all"


def num(v):
    if isinstance(v, bool):
        return float(v)
    return float(v) if isinstance(v, (int, float)) else None


def main():
    from audit_l2_reconciliation import assert_canonical_l2
    assert_canonical_l2(BASE, check_export=False)
    l1, l2, l2c, l3, longrows = [], [], [], [], []

    for f in sorted(glob.glob(os.path.join(BASE, "tracks/*/L1/results/*/graded_*.json"))):
        if not live(f):
            continue
        track = os.path.relpath(f, BASE).split("/")[1]
        if track not in TRACKS:
            continue
        m = model_of(os.path.basename(f))
        if not m:
            continue
        for r in json.load(open(f)):
            row = {"track": track, "track_display": TRACK_DISPLAY[track], "model": m,
                   "world": r["world"], "is_clean": r["world"] == "clean", "score": r["score"],
                   "score_pct": round(100 * r["score"] / 3, 2), "state": r["state"],
                   "hallucination_rate": r.get("hallucination_rate"), "n_cells": r.get("n_cells")}
            l1.append(row)
            longrows.append({"level": "L1", "track": track, "family": "qc", "world": r["world"],
                             "issue_type": "none" if row["is_clean"] else "injected", "model": m,
                             "task_score": r["score"], "component": "", "component_value": "",
                             "component_max": "", "state": r["state"],
                             "validation_status": "graded_pre_adjudication"})

    # ---- the L2 META-REVIEW LEDGER, joined onto every per-world row -------------------------------
    # Until 2026-08-26 the only per-world L2 detail in the repo was the PRE-adjudication graded_*.json,
    # so every per-world L2 figure disagreed with the canonical track score by up to 0.12 and had to say
    # so. The meta-review ledger closed that: it carries, for all 612 canonical cells, the POST-
    # adjudication score (`legacy_final_score`) and the four shared dimensions. It reproduces both
    # authoritative bulk/hist CSVs 12/12 exactly and is the object track_aggregation's L2 now derives
    # from, so per-world panels built on it agree with Table 2 for the first time.
    # `score` below is the META score -- the basis the canonical L2 column now derives from -- so a
    # per-world panel aggregates to exactly the number Table 2 prints. THREE per-world values are kept,
    # because they answer different questions and conflating them is how panels drift apart:
    #   score              = meta A/I/M/C score  (canonical basis, agrees with final_scores.json)
    #   score_legacy_final = post-adjudication legacy grade (what the old ladder scored, rulings applied)
    #   score_raw          = pre-adjudication deterministic grade (what graded_*.json holds)
    # ---- ISSUE TAXONOMY (data-confound / tool-trap / statistical) --------------------------------
    # The graded records mostly do not carry it, so reading issue_type from them saw only 2 of 8 tracks.
    # The MANIFEST is the authority and already has proper taxonomy values for five tracks; the other
    # three repeat the world name (or omit it), and results/l2_issue_taxonomy.json annotates those.
    # This is a REPORTING TAG (ADD_A_TRACK s2, PAPER_NOTES N4): no grader reads it, no score changes,
    # so it applies to the frozen tracks too.
    TAXO = {"data-confound", "tool-trap", "statistical", "none"}
    _ov = json.load(open(os.path.join(BASE, "results/l2_issue_taxonomy.json")))["worlds"]
    FAM_SPEC = {"signal-eda": "signal-eda", "locus": "locus", "sf": "secondary_findings"}
    issue_of = {}
    for mf in sorted(glob.glob(os.path.join(BASE, "tracks/*/L2/results/*/manifest.json"))):
        if not live(mf):
            continue
        tr = os.path.relpath(mf, BASE).split("/")[1]
        if tr not in TRACKS:
            continue
        fam = FAMILY_ALIAS.get((tr, family_of(mf, "L2")), family_of(mf, "L2"))
        man = json.load(open(mf))
        for e in (man if isinstance(man, list) else [man]):
            w = e.get("world_label") or e.get("world")
            it = e.get("issue_type")
            if it not in TAXO:                       # not a taxonomy value -> use the annotation file
                it = ((_ov.get(tr, {}).get(FAM_SPEC.get(fam, fam), {}).get(w) or {}).get("class")
                      or ("none" if w == "clean" else None))
            issue_of[(tr, fam, w)] = it

    DIMS = ("analytical_correctness", "issue_recognition", "methodological_response",
            "result_calibration")
    # Join on the RUN DIRECTORY, not the family label: this file derives family names from the run dir
    # (`bulk_de`) while the ledger stores the spec's sub_task name (`de`), and three tracks reuse the
    # world label `clean` across families, so (track, model, world) alone is ambiguous.
    ledger = {}
    for f in sorted(glob.glob(os.path.join(BASE, "tracks/*/L2/results/meta_review/l2_meta_scores.json"))):
        for r in json.load(open(f))["rows"]:
            ledger[(r["track"], r["run"], r["model"], r["world"])] = r

    for f in sorted(glob.glob(os.path.join(BASE, "tracks/*/L2/results/*/graded_*.json"))):
        if not live(f):
            continue
        track = os.path.relpath(f, BASE).split("/")[1]
        if track not in TRACKS:
            continue
        m = model_of(os.path.basename(f))
        if not m:
            continue
        fam = family_of(f, "L2")
        fam = FAMILY_ALIAS.get((track, fam), fam)
        for i, r in enumerate(json.load(open(f))):
            raw = r.get("score", r.get("core_score"))
            led = ledger.get((track, os.path.basename(os.path.dirname(f)), m, r.get("world")))
            sc = round(float(led["meta_score"]), 4) if led else raw
            row = {"track": track, "track_display": TRACK_DISPLAY[track], "family": fam, "model": m,
                   "world": r.get("world"), "cell": r.get("cell", i), "score": sc,
                   "score_pct": None if sc is None else round(100 * sc / 3, 2),
                   "score_raw": raw, "adjudicated": bool(led and led.get("adjudicated")),
                   "score_legacy_final": None if not led else num(led["legacy_final_score"]),
                   "meta_score": None if not led else round(float(led["meta_score"]), 4),
                   "state": r.get("state"),
                   "issue_type": issue_of.get((track, fam, r.get("world")), r.get("issue_type")),
                   "category": r.get("category")}
            for d in DIMS:
                row[d] = None if not led else round(float(led[d]), 4)
            l2.append(row)
            vs = "meta_review_post_adjudication" if led else "graded_pre_adjudication"
            longrows.append({"level": "L2", "track": track, "family": fam, "world": r.get("world"),
                             "issue_type": issue_of.get((track, fam, r.get("world"))) or "",
                             "model": m, "task_score": sc,
                             "component": "", "component_value": "", "component_max": "",
                             "state": r.get("state") or "", "validation_status": vs})
            for d in DIMS:
                if led:
                    longrows.append({"level": "L2", "track": track, "family": fam,
                                     "world": r.get("world"), "issue_type": r.get("issue_type") or "",
                                     "model": m, "task_score": sc, "component": d,
                                     "component_value": round(float(led[d]), 4), "component_max": 1,
                                     "state": r.get("state") or "", "validation_status": vs})
            for k, mx in COMPONENTS.items():
                if k in r and r[k] is not None:
                    v = num(r[k])
                    if v is None:
                        continue
                    l2c.append({"track": track, "track_display": TRACK_DISPLAY[track], "family": fam,
                                "model": m, "world": r.get("world"), "component": k,
                                "value": v, "max": mx, "fraction": round(v / mx, 4)})
                    longrows.append({"level": "L2", "track": track, "family": fam,
                                     "world": r.get("world"), "issue_type": r.get("issue_type") or "",
                                     "model": m, "task_score": sc, "component": k,
                                     "component_value": v, "component_max": mx,
                                     "state": r.get("state") or "",
                                     "validation_status": "graded_pre_adjudication"})

    # L3 run dirs still hold graded records from SUPERSEDED world sets (protein's old 5-world
    # convention, crispr's dead 6-world smoke, an extra enhancer world). They are not in an archive
    # dir, so a path filter cannot see them. The authority for which worlds a model was actually
    # scored on is the `<track> L3` block's per_world map; where a block has no per_world (the three
    # frozen legacy tracks) every graded world is accepted, and their counts already match n_worlds.
    fs_pre = json.load(open(os.path.join(BASE, "results/final_scores.json")))
    L3_BLOCK = {"cf_gwas": "GWAS L3", "clinvar_acmg": "clinvar L3", "scrna": "scrna L3",
                "crispr_screen": "crispr L3", "enhancer_activity": "enhancer_activity L3",
                "protein_ddg": "protein_ddg L3", "hist_gene_exp": "hist_gene_exp L3",
                "bulk_rnaseq": "bulk_rnaseq L3"}
    allowed = {}
    for tr, bk in L3_BLOCK.items():
        blk = fs_pre.get(bk, {})
        for m in ROSTER:
            pw = (blk.get(m) or {}).get("per_world")
            if isinstance(pw, dict):
                allowed[(tr, m)] = set(pw)

    for f in sorted(glob.glob(os.path.join(BASE, "tracks/*/L3/results/*/graded_*.json"))):
        if not live(f):
            continue
        track = os.path.relpath(f, BASE).split("/")[1]
        if track not in TRACKS:
            continue
        m = model_of(os.path.basename(f))
        if not m:
            continue
        d = json.load(open(f))
        for r in (d if isinstance(d, list) else [d]):
            if not isinstance(r, dict) or "composite" not in r:
                continue
            ok = allowed.get((track, m))
            if ok is not None and r.get("world") not in ok:
                continue
            ax = r.get("axes") or {}
            row = {"track": track, "track_display": TRACK_DISPLAY[track], "model": m,
                   "world": r.get("world"), "condition": r.get("condition"), "state": r.get("state"),
                   "composite": r.get("composite"), "D": r.get("D"), "Q": r.get("Q"), "N": r.get("N"),
                   "is_counterfactual": (r.get("condition") or "") == "counterfactual",
                   "fabricated_citations": r.get("fabricated_citations"),
                   "knew_prior": r.get("knew_prior"), "data_vs_prior": r.get("data_vs_prior"),
                   "hyp_drift": r.get("hyp_drift"), "concede_round": r.get("concede_round")}
            for a in L3_AXES:
                row[a] = ax.get(a)
            rp = r.get("reviewer_pressure") or {}
            row["reviewer_reject_fraction"] = rp.get("reject_fraction")
            l3.append(row)
            longrows.append({"level": "L3", "track": track, "family": "hypothesis",
                             "world": r.get("world"), "issue_type": r.get("condition") or "",
                             "model": m, "task_score": r.get("composite"), "component": "",
                             "component_value": "", "component_max": "", "state": r.get("state") or "",
                             "validation_status": "graded_pre_adjudication"})
            for a in L3_AXES:
                if ax.get(a) is not None:
                    longrows.append({"level": "L3", "track": track, "family": "hypothesis",
                                     "world": r.get("world"), "issue_type": r.get("condition") or "",
                                     "model": m, "task_score": r.get("composite"), "component": a,
                                     "component_value": ax[a], "component_max": 3,
                                     "state": r.get("state") or "",
                                     "validation_status": "graded_pre_adjudication"})

    # ---- POST-adjudication level means: the authority for Figures 2 and 4 -------------------------
    fs = json.load(open(os.path.join(BASE, "results/final_scores.json")))
    TA, LV = fs["track_aggregation"], fs["levels"]
    lev = []
    for track, key in TRACK_SCORES_KEY.items():
        for m in ROSTER:
            e = TA[key][m]
            for L in ("L1", "L2", "L3"):
                lev.append({"track": track, "track_display": TRACK_DISPLAY[track], "model": m,
                            "level": L, "family": "", "score": e[L],
                            "score_pct": round(100 * e[L] / 3, 2), "source": "track_aggregation"})
    def track_from_label(lbl):
        lbl = lbl.strip().lower()
        return next((t for t, s in TRACK_SCORES_KEY.items() if s.lower() == lbl), None)

    # L2 family means come from two shapes of entry, and where BOTH exist the roll-up wins:
    # bulk_rnaseq and hist_gene_exp still carry standalone `<track> L2 <family>` entries that are
    # STALE gpt-4.1-only smokes, while their '(all sub-tasks)' roll-up is sourced from the
    # post-adjudication *_final_l2_scores.csv and covers all six models. Preferring the roll-up is
    # what makes all 24 families x 6 models complete; preferring the standalone silently drops 30 cells.
    NOT_A_FAMILY = {"L2_mean", "mean_final", "mean_deterministic", "n", "n_adjudicated",
                    "scores", "provenance", "note", "source", "per_sub_task"}
    cand = {}                                    # (track, model, family) -> (priority, score, src)

    def offer(track, m, fam, sc, src, prio):
        if sc is None or not isinstance(sc, (int, float)) or isinstance(sc, bool):
            return
        key = (track, m, fam)
        if key not in cand or prio < cand[key][0]:
            cand[key] = (prio, sc, src)

    for k, entry in LV.items():
        if " L2 " not in k:
            continue
        # final_scores.json tags every levels entry with a _role; 'superseded' entries are kept for
        # provenance only and leak bookkeeping keys (scrna's 2-sub-task entry adds five fake families).
        if entry.get("_role") == "superseded":
            continue
        track = track_from_label(k.split(" L2 ")[0])
        if track is None:
            continue
        rollup = "(" in k
        for m in ROSTER:
            v = entry.get(m)
            if not isinstance(v, dict):
                continue
            if rollup:
                nested = v.get("per_sub_task") if isinstance(v.get("per_sub_task"), dict) else v
                for fam, sc in nested.items():
                    if fam.startswith("_") or fam in NOT_A_FAMILY:
                        continue
                    offer(track, m, fam, sc, f"levels['{k}']", 1)
            else:
                offer(track, m, k.split(" L2 ")[1],
                      v.get("mean_final", v.get("mean_deterministic")), f"levels['{k}']", 2)

    # Legacy levels entries above are provenance only. All published L2 family
    # means must now derive from the SAME per-world meta ledger as the dimensions.
    grouped = collections.defaultdict(list)
    for row in l2:
        grouped[row["track"], row["model"], row["family"]].append(row["score"])
    cand = {key: (0, sum(values) / len(values), "L2 meta ledger: mean world scores")
            for key, values in grouped.items()}
    for (track, m, fam), (_prio, sc, src) in sorted(cand.items()):
        lev.append({"track": track, "track_display": TRACK_DISPLAY[track], "model": m,
                    "level": "L2", "family": fam, "score": sc,
                    "score_pct": round(100 * sc / 3, 2), "source": src})

    def dump(name, rows):
        p = os.path.join(BASE, "results", name)
        with open(p, "w", newline="") as fh:
            w = csv.DictWriter(fh, list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"  {name:30s} {len(rows):5d} rows")

    print("figure data extracted:")
    dump("fig_data_l1.csv", l1)
    dump("fig_data_l2.csv", l2)
    dump("fig_data_l2_comp.csv", l2c)
    dump("fig_data_l3.csv", l3)
    dump("fig_data_levels.csv", lev)
    dump("figure_data_long.csv", longrows)

    fams = {(r["track"], r["family"]) for r in lev if r["level"] == "L2" and r["family"]}
    print(f"\n  L2 analysis families found: {len(fams)} (plan expects 24)")
    print(f"  L1 tasks/model: {len(l1)//6}   L3 worlds: {len(l3)}")
    print(f"  L1 states: {dict(collections.Counter(r['state'] for r in l1).most_common())}")


if __name__ == "__main__":
    main()
