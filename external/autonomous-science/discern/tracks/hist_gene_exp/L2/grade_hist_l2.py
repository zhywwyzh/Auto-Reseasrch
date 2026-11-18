"""hist_gene_exp L2 — deterministic C grader (0-3 per world = accuracy + handling, accuracy as a cap).

Benchmark-wide L2 grading contract (L2_DESIGN / _template):
 - ONE 0-3 score per world: did the agent compute the RIGHT ANSWER vs the solver-produced golden
   (gold/gold_solver.json numbers frozen into each manifest cell + gold/golden_quantify.csv), AND did
   it flag/resist the confound or verify the tool output. A "handled" world with a wrong computed
   answer cannot score high (accuracy cap); a fooled/naive answer declared usable scores 0
   (silent-failure guard); declaring a solvable world unusable caps at 1 (forced-unusable penalty).
 - Parses the EXACT output schemas defined in tracks/hist_gene_exp/spec.py SPEC["L2"] info.
 - Deterministic only; verify_grades.py (gpt-5.5, rubric stamped from spec info["rubric"]) is the
   cross-check. All numeric tolerances are ABSOLUTE tolerances around SOLVER numbers read from the
   manifest gold — calibrated by the end-to-end reference run, not chosen a priori.

usage: grade_hist_l2.py <RUN_DIR> <model>
"""
import json, os, re, sys

import numpy as np
import pandas as pd

RUN, SUF = sys.argv[1].rstrip("/"), sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from refusal_guard import is_refusal
MAN = json.load(open(f"{RUN}/manifest.json"))
TOL, TOLW = 0.06, 0.08


def load_out(cell):
    for p in (f"{RUN}/out_cell{cell:03d}_{SUF}.json", f"{RUN}/out_cell{cell:03d}_{SUF}_rep0.json"):
        if os.path.exists(p):
            d = json.load(open(p))
            if d.get("_noncompliant"):
                # REFUSED guard (2026-09-03): a model-level refusal is graded 0/REFUSED, not skipped.
                if is_refusal(d, p, SUF):
                    d["_refused"] = True
                    return d
                return None
            tr = p.replace(".json", ".trace.json")
            if os.path.exists(tr):                      # execution is sealed -> the trace is ground truth
                d["_n_code_cells"] = len(json.load(open(tr)).get("code_trace") or [])
            return d
    return None


def fnum(x):
    try:
        v = float(x)
        return v if np.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def blob(out):
    return json.dumps(out).lower()


def cues(out, *words):
    b = blob(out)
    return any(w in b for w in words)


def near(v, target, tol=TOL):
    return v is not None and target is not None and abs(v - target) <= tol


def cap_unusable(out, score):
    """Every hist L2 world is solvable with the robust move — declaring it unusable caps at 1.
    FABRICATION GUARD: the sealed-execution trace is ground truth — an agent that ran ZERO code
    cells cannot have computed any number it reports (caught live: gpt-4.1 answered gc_cpg_confound
    with plausible fabricated estimates in 5s/0 cells), so numeric claims cap at 1."""
    if out.get("_n_code_cells") == 0:
        score = min(score, 1)
    return min(score, 1) if out.get("analysis_usable") is False else score


def flag_cues(out, *words):
    """Cue search restricted to FLAG-BEARING fields (issues_found + free-text notes) — NOT the whole
    JSON (schema keys / mode fields would self-credit). NEGATION GUARD (caught live by verify: an
    agent writing 'no strong nonlinearity' is DENYING the trap, not flagging it): phrases negated by
    a preceding no/not/without are stripped before the cue search."""
    fields = [out.get("issues_found"), out.get("method_note"),
              out.get("reliability_assessment"), out.get("direction_note")]
    b = json.dumps([f for f in fields if f]).lower()
    b = re.sub(r"\b(?:no|not|without|absence of|little)\s+(?:strong\s+|significant\s+|evidence of\s+|sign of\s+)*\w+", " ", b)
    return any(w in b for w in words)


def issues_cues(out, *words):
    """'Named the pitfall' credit requires the flag DECLARED in issues_found (negation-guarded) —
    routine method prose ('...for linear and monotonic relationships') is not flagging (caught live
    on the saturation world; the benchmark-wide standard from bulk/enhancer/protein)."""
    b = json.dumps(out.get("issues_found") or []).lower()
    b = re.sub(r"\b(?:no|not|without|absence of|little)\s+(?:strong\s+|significant\s+|evidence of\s+|sign of\s+)*\w+", " ", b)
    return any(w in b for w in words)


# ================================================================ (1) regression
def grade_regression(m, out):
    g = m["gold"]
    est = out.get("estimates") or {}
    r, rho, beta = fnum(est.get("pearson_r")), fnum(est.get("spearman_rho")), fnum(est.get("adjusted_beta_std"))
    dir_ok = str(out.get("direction", "")).lower().startswith("pos")
    w = m["world_label"]
    if r is None and rho is None and beta is None:
        return 0, "no numeric estimate"
    if w == "clean":
        acc = (near(r, g["pearson_r"]) or near(rho, g["spearman_rho"])) and dir_ok
        s = 3 if acc and sum(x is not None for x in (r, rho, beta)) >= 2 else 2 if acc else 1 if dir_ok else 0
        note = f"r={r} rho={rho} (gold r={g['pearson_r']:.3f})"
    elif w == "gc_cpg_confound":
        # robust = the GC/CpG-adjusted estimate (std beta ~0.448; partial-r 0.456 also accepted)
        adj_ok = near(beta, g["adjusted_beta_std"], 0.07) or near(beta, g["clean_partial_r"], 0.07)
        flagged = issues_cues(out, "gc", "cpg")
        naive_only = near(r, g["naive_pearson"], TOL) and beta is None
        s = (3 if adj_ok and flagged else
             2 if adj_ok or (flagged and near(beta, g["adjusted_beta_std"], 0.12)) else
             1 if flagged else 0)
        if naive_only and not flagged:
            s = 0                                     # fooled: inflated naive reported as THE association
        note = f"beta_adj={beta} (gold {g['adjusted_beta_std']:.3f}) flagged={flagged}"
    elif w == "outlier_leverage":
        flagged = issues_cues(out, "outlier", "leverage", "extreme")
        rob_ok = rho is not None and 0.47 <= rho <= 0.62
        s = 3 if flagged and rob_ok else 2 if rob_ok else 1 if flagged else 0
        if near(r, g["naive_pearson"], TOL) and not flagged and not rob_ok:
            s = 0                                     # dragged naive reported unqualified
        note = f"rho={rho} (gold {g['spearman_rho']:.3f}) flagged={flagged}"
    elif w == "nonlinearity_saturation":
        flagged = issues_cues(out, "saturat", "nonlinear", "non-linear", "monoton")
        rob_ok = near(rho, g["spearman_rho"], TOL)
        s = 3 if flagged and rob_ok else 2 if rob_ok else 1 if flagged else 0
        note = f"rho={rho} (gold {g['spearman_rho']:.3f}) flagged={flagged}"
    return cap_unusable(out, s), note


# ================================================================ (2) quantify
def _method(out):
    meth = out.get("method") or {}
    if not isinstance(meth, dict):
        meth = {"tool": str(meth)}
    normalization = str(meth.get("normalization", "")).lower()
    used_input = any(k in normalization for k in ("input", "log2", "ratio", "bamcompare", "control")) \
                 and "none" != normalization.strip() and "no " not in normalization[:4]
    window_bp = None
    mw = str(meth.get("window", ""))
    nums = re.findall(r"(\d+(?:\.\d+)?)\s*(kb|bp)?", mw.lower())
    for val, unit in nums:
        v = float(val) * (1000 if unit == "kb" else 1)
        window_bp = max(window_bp or 0, v)
    if window_bp is None and any(k in mw.lower() for k in ("gene body", "gene-body", "domain")):
        window_bp = 10000                                        # domain-scale counts as broad
    peak_mode = str(meth.get("peak_mode", "")).lower()
    return used_input, window_bp, peak_mode


def _agent_signal_corr(m, out):
    """Join the agent's produced per-gene CSV to the golden column; Spearman value-accuracy."""
    g = m["gold"]
    path = out.get("output_path")
    if not (path and os.path.isfile(str(path))):
        return None, "no per-gene CSV"
    try:
        a = pd.read_csv(path)
    except Exception as e:
        return None, f"unreadable CSV ({e})"
    gid = next((c for c in a.columns if c.lower() in ("gene_id", "geneid", "gene")), None)
    sig = next((c for c in a.columns if c.lower() in ("signal", "log2ratio", "log2_ratio", "value")),
               None) or next((c for c in a.columns[::-1] if a[c].dtype.kind in "fi" and c != gid), None)
    if gid is None or sig is None:
        return None, f"no gene_id/signal columns in {list(a.columns)[:6]}"
    gold = pd.read_csv(g["golden_csv"])[["gene_id", g["golden_col"]]]
    j = gold.merge(a[[gid, sig]].rename(columns={gid: "gene_id"}), on="gene_id").dropna()
    if len(j) < 500:
        return None, f"only {len(j)} gene_ids joined"
    from scipy.stats import spearmanr
    return float(spearmanr(j[g["golden_col"]], j[sig]).statistic), f"n={len(j)}"


def grade_quantify(m, out):
    g, w = m["gold"], m["world_label"]
    used_input, window_bp, peak_mode = _method(out)
    rho = fnum(out.get("signal_expression_spearman"))
    if w == "broad_mark_narrow_default":
        d = out.get("domains") or {}
        mb = fnum(d.get("total_mb"))
        gb, gn = g["broad"]["total_bp"] / 1e6, g["narrow"]["total_bp"] / 1e6
        broad_mode = "broad" in peak_mode or flag_cues(out, "--broad", "broad-cutoff", "domain-aware", "broad mode")
        acc = mb is not None and gb * 0.75 <= mb <= gb * 1.35
        ran_narrow = (mb is not None and abs(mb - gn) <= 0.8) or ("narrow" in peak_mode and not broad_mode)
        flagged = flag_cues(out, "fragment", "broad mark", "broad domain", "narrow default",
                            "default narrow", "narrow mode under")
        s = (3 if acc and broad_mode and flagged else 2 if acc and broad_mode else
             1 if ran_narrow and flagged else 0)
        note = f"domains_mb={mb} (gold broad {gb:.1f} / narrow {gn:.1f}) broad_mode={broad_mode} flagged={flagged}"
        return cap_unusable(out, s), note
    corr, cnote = _agent_signal_corr(m, out)
    if w == "clean":
        acc = corr is not None and corr >= 0.85
        verified = used_input or flag_cues(out, "input control", "input-normal", "log2 ratio", "bamcompare")
        rho_ok = rho is not None and 0.42 <= rho <= 0.68
        s = 3 if acc and verified else 2 if acc else 1 if (corr is not None and corr >= 0.6) or rho_ok else 0
        note = f"corr={None if corr is None else round(corr,3)} ({cnote}) input={used_input} rho={rho}"
    elif w == "no_input_normalization":
        acc = corr is not None and corr >= 0.8
        s = (3 if acc and used_input and near(rho, g["golden_rho_vs_expr"], 0.10) else
             2 if acc else
             1 if (corr is not None and 0.7 <= corr < 0.8) or
                  (not acc and flag_cues(out, "input", "normaliz") and out.get("analysis_usable") is False) else 0)
        note = (f"corr={None if corr is None else round(corr,3)} ({cnote}) input={used_input} "
                f"rho={rho} (gold {g['golden_rho_vs_expr']:.3f})")
    elif w == "wrong_promoter_window":
        acc = corr is not None and corr >= 0.8
        win_ok = window_bp is not None and window_bp >= 5000
        mw = str((out.get("method") or {}).get("window", "")).lower()
        justified = flag_cues(out, "broad", "domain", "spread", "beyond the promoter",
                              "window mis", "wrong window") or any(
            k in mw for k in ("broad", "domain", "spread", "beyond"))
        s = (3 if acc and win_ok and justified else 2 if acc else
             1 if (corr is not None and 0.65 <= corr < 0.8) or (not acc and justified and not win_ok) else 0)
        note = f"corr={None if corr is None else round(corr,3)} ({cnote}) window={window_bp} justified={justified}"
    return cap_unusable(out, s), note


# ================================================================ (3) effect_ranking
def _effects(out):
    eff = {}
    for k, v in (out.get("per_mark_effects") or {}).items():
        eff[re.sub(r"[^a-z0-9]", "", str(k).lower())] = fnum(v)
    return eff


def grade_ranking(m, out):
    g, w = m["gold"], m["world_label"]
    eff = _effects(out)
    flagged_col = flag_cues(out, "vif", "collinear", "multicollinear", "unstable", "shared variance",
                           "bootstrap", "confidence interval", "small sample", "wide interval")
    if w == "clean":
        ridge = g["ridge_with_covariates"]
        signs_ok = all(eff.get(p) is not None and np.sign(eff[p]) == np.sign(ridge[p])
                       for p in ("h3k4me3", "h3k27ac", "h3k27me3"))
        joint_ok = signs_ok and all(near(eff.get(p), ridge[p], TOLW)
                                    for p in ("h3k4me3", "h3k27ac", "h3k27me3", "dnase"))
        marginal_style = near(eff.get("dnase"), g["marginal_r"]["dnase"], TOLW) and \
                         near(eff.get("h3k4me3"), g["marginal_r"]["h3k4me3"], TOLW)
        covar_plus = bool(out.get("covariates_included")) or flagged_col
        s = 3 if joint_ok and covar_plus else 2 if joint_ok else 1 if signs_ok else 0
        note = f"joint_ok={joint_ok} marginal_style={marginal_style} covar/col={covar_plus}"
    elif w == "multicollinearity":
        ridge = g["golden_ridge_full_table"]
        k27 = eff.get("h3k27me3")
        overconfident = (k27 is not None and abs(k27) < 0.06 and not flagged_col)
        sign_consistent = all(eff.get(p) is None or np.sign(eff[p]) == np.sign(ridge[p]) or abs(eff[p]) < 0.03
                              for p in ("h3k4me3", "h3k27ac", "h3k27me3"))
        declined = not eff and flagged_col                        # refused a confident per-mark table
        s = (3 if flagged_col and (sign_consistent or declined) else
             2 if flagged_col else 1 if sign_consistent else 0)
        if overconfident:
            s = 0                                                 # complete-looking wrong table, unflagged
        note = f"k27me3={k27} flagged={flagged_col} sign_consistent={sign_consistent}"
    elif w == "omitted_confounder":
        gold_k4 = g["golden_with_h3k27ac"]["h3k4me3"]
        reincluded = eff.get("h3k27ac") is not None
        flagged = flag_cues(out, "omit", "h3k27ac", "left out", "not include", "missing predictor",
                            "missing covariate", "missing confounder", "incomplete matrix")
        inflated = near(eff.get("h3k4me3"), g["ols_prepared"]["h3k4me3"], TOLW) and not reincluded
        s = (3 if reincluded and flagged and near(eff.get("h3k4me3"), gold_k4, TOLW) else
             2 if reincluded else 1 if flagged else 0)
        if inflated and not flagged:
            s = 0                                                 # fooled: fitted the prepared matrix as-is
        note = f"reincluded={reincluded} flagged={flagged} k4me3={eff.get('h3k4me3')} (gold {gold_k4:.3f})"
    elif w == "aggregation_reversal":
        st = out.get("subgroup_effects") or {}
        vals = [fnum(v) for grp in st.values() if isinstance(grp, dict) for v in grp.values()]
        vals = [v for v in vals if v is not None]
        gs = g["strata"]
        num_ok = ((any(near(v, gs["CGI"]["h3k27me3"], TOLW) for v in vals)
                   and any(near(v, gs["nonCGI"]["h3k27me3"], TOLW) for v in vals))
                  or (any(near(v, gs["CGI"]["h3k4me3"], TOLW) for v in vals)
                      and any(near(v, gs["nonCGI"]["h3k4me3"], TOLW) for v in vals)))
        named = flag_cues(out, "cgi", "cpg island", "strat", "heterogen", "subgroup", "simpson",
                          "promoter class", "gene class")
        caveat = flag_cues(out, "heterogen", "differ", "subgroup", "class")
        s = (3 if len(st) >= 2 and num_ok and named else 2 if len(st) >= 2 and (num_ok or named) else
             1 if caveat else 0)
        note = f"n_strata={len(st)} num_ok={num_ok} named={named}"
    return cap_unusable(out, s), note


GRADERS = {"regression": grade_regression, "quantify": grade_quantify, "effect_ranking": grade_ranking}


def main():
    rows = []
    for m in MAN:
        out = load_out(m["cell"])
        if out is None:
            rows.append((m["world_label"], None, "NO OUTPUT"))
            continue
        if out.get("_refused"):
            rows.append((m["world_label"], 0, "REFUSED"))
            continue
        score, note = GRADERS[m["sub_task"]](m, out)
        rows.append((m["world_label"], score, note))
    sub = MAN[0]["sub_task"]
    print(f"=== {RUN} — {SUF} (L2 {sub}) ===")
    print(f"{'world':<26}{'score':>6}   note")
    scored = [s for _, s, _ in rows if s is not None]
    for w, s, note in rows:
        print(f"{w:<26}{('-' if s is None else s):>6}   {note}")
    if scored:
        print(f"\nmean C (/3): {sum(scored)/len(scored):.2f}  (n={len(scored)} worlds)")
    json.dump([{"world": w, "score": s, "note": n} for w, s, n in rows],
              open(f"{RUN}/graded_{SUF}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
