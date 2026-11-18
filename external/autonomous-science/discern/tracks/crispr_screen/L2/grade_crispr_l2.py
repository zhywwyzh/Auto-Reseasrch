"""crispr_screen L2 grader (C axis, 0-3). Deterministic; value-checks the agent's produced CSV against the
solver golden (CEGv2/NEGv1-anchored) and credits confound-handling only from declared-flag fields.

Score ladder (uniform): 3 = correct answer (recovered the golden truth on the world's trap) AND flagged/
handled the pitfall; 2 = correct silently; 1 = naive-but-flagged / partial; 0 = naive result declared usable
(the silent failure). FABRICATION GUARD: 0 code cells -> cap 1. Forced-unusable -> cap 1. Flag credit routes
ONLY through issues_found / method / notes (never trajectory / schema keys).

usage: grade_crispr_l2.py <RUN_DIR> <model>
"""
import json, os, sys, re
import numpy as np, pandas as pd

RUN, SUF = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from refusal_guard import is_refusal


def load_out(cell):
    p = f"{RUN}/out_cell{cell:03d}_{SUF}.json"
    if not os.path.exists(p):
        return None
    d = json.load(open(p))
    if d.get("_noncompliant"):
        # REFUSED guard (2026-09-03): a model-level refusal is graded 0/REFUSED, not skipped.
        if is_refusal(d, p, SUF):
            d["_refused"] = True
            return d
        return None
    tr = p.replace(".json", ".trace.json")
    if os.path.exists(tr):                                   # sealed trace = ground truth
        d["_n_code_cells"] = len(json.load(open(tr)).get("code_trace") or [])
    return d


def caps(out, score):
    if out.get("_n_code_cells") == 0:
        score = min(score, 1)                               # fabrication guard
    if out.get("analysis_usable") is False:
        score = min(score, 1)                               # forced-unusable penalty
    return score


def _values_only(x):
    acc = []
    def rec(v):
        if isinstance(v, dict):
            [rec(u) for u in v.values()]
        elif isinstance(v, (list, tuple)):
            [rec(u) for u in v]
        elif v is not None:
            acc.append(str(v))
    rec(x); return acc


def flag_cues(out, *words):
    """Cue search restricted to declared-flag fields, VALUES only (never keys / trajectory / whole JSON)."""
    fields = [out.get("issues_found"), out.get("method_note"),
              out.get("reliability_assessment"), out.get("notes")]
    b = " | ".join(_values_only([f for f in fields if f])).lower()
    return any(w in b for w in words)


def agent_table(out):
    """Load the agent's produced CSV (gene + score/essential) from output_path; tolerant to column names."""
    p = out.get("output_path")
    if not p or not os.path.exists(p):
        return None
    try:
        df = pd.read_csv(p)
    except Exception:
        return None
    cols = {c.lower(): c for c in df.columns}
    gc = next((cols[k] for k in cols if k in ("gene", "gene_id", "symbol")), None)
    if gc is None:
        return None
    df = df.rename(columns={gc: "gene"})
    df["gene"] = df["gene"].astype(str)
    return df


def golden(m):
    return pd.read_csv(m["gold"]["golden_csv"])


# ---------------------------------------------------------------- (1) scoring
def grade_scoring(m, out):
    df = agent_table(out)
    if df is None:
        return 0, "no score CSV"
    sc = next((c for c in df.columns if c.lower() in ("score", "bf", "essentiality", "lfc", "dependency")), None)
    if sc is None or len(df) < 5000:
        return 0, "no usable per-gene score"
    g = golden(m).set_index("gene")
    thr = m["gold"]["essential_thr"]
    n_ess = int((g.bf > thr).sum())                          # golden essential-set size (NEG-anchored)
    full = df.set_index("gene")[sc].astype(float)
    j = full.to_frame("s").join(g[["bf", "is_ceg", "is_neg"]], how="inner").dropna(subset=["s"])
    if j.is_ceg.sum() < 50 or j.is_neg.sum() < 50:
        return 0, "score does not cover the gold genes"
    orient = 1.0 if np.corrcoef(j.s.values, j.bf.values)[0, 1] >= 0 else -1.0   # higher = more essential
    full_o = orient * full
    w = m["world_label"]
    if w == "clean":
        from sklearn.metrics import roc_auc_score
        jj = j.assign(so=orient * j.s)
        au = roc_auc_score(jj.is_ceg[jj.is_ceg | jj.is_neg].astype(int), jj.so[jj.is_ceg | jj.is_neg])
        return (3 if au >= 0.9 else 2 if au >= 0.8 else 1 if au >= 0.65 else 0), f"clean AUROC={au:.3f}"
    ess_set = set(full_o.sort_values(ascending=False).head(n_ess).index)   # agent's essential call = top N_ess
    aff = [x for x in m["gold"]["affected"] if x in full_o.index]
    if not aff:
        return 1, "affected genes absent from CSV"
    ess = m["gold"]["truth"].startswith("essential")
    correct = np.mean([(a in ess_set) == ess for a in aff])  # recovered the trap on the affected genes
    cue = {"guide_efficiency": ("efficien", "dead guide", "best guide", "best-guide", "rra", "robust aggreg",
                                "guide-level", "low-activity"),
           "outlier_guide": ("outlier", "hyperactive", "median", "trimmed", "robust aggreg", "off-target"),
           "off_target_promiscuous": ("off-target", "off target", "promiscu", "multi-target", "multitarget",
                                      "alignment", "drop", "remap")}[w]
    flagged = flag_cues(out, *cue)
    if correct >= 0.7:
        return (3 if flagged else 2), f"recovered {correct:.0%} of affected; flagged={flagged}"
    return (1 if flagged else 0), f"recovered only {correct:.0%} of affected (naive); flagged={flagged}"


# ---------------------------------------------------------------- (2) calling
def _essential_set(out):
    df = agent_table(out)
    if df is None:
        return None
    if "essential" in [c.lower() for c in df.columns]:
        ec = next(c for c in df.columns if c.lower() == "essential")
        s = df[ec].astype(str).str.lower().isin(["true", "1", "yes", "essential"])
        return set(df.gene[s])
    return set(df.gene)                                      # a bare list of essential genes


def grade_calling(m, out):
    ess = _essential_set(out)
    if ess is None or len(ess) < 50:
        return 0, "no essential-gene list"
    g = golden(m)
    ceg = set(g.gene[g.is_ceg]); neg = set(g.gene[g.is_neg])
    recall = len(ess & ceg) / max(1, len(ceg)); fp = len(ess & neg) / max(1, len(neg))
    w = m["world_label"]
    if w == "clean":
        ok = recall >= 0.85 and fp <= 0.10
        return (3 if ok else 2 if recall >= 0.75 else 1 if recall >= 0.5 else 0), f"recall={recall:.2f} negFP={fp:.2f}"
    if w == "null_calibration":
        flagged = flag_cues(out, "null", "non-essential", "neg", "calibrat", "control", "fdr", "background")
        ok = recall >= 0.9                                  # recovered the essentials the all-gene null misses
        return (3 if ok and flagged else 2 if ok else 1 if flagged else 0), f"CEG recall={recall:.2f} flagged={flagged}"
    if w == "replicate_irreproducible":
        aff = set(m["gold"]["affected"])
        leaked = len(ess & aff) / max(1, len(aff))          # artifacts wrongly called essential
        flagged = flag_cues(out, "replicat", "reproduc", "concord", "one rep", "single rep", "batch")
        ok = leaked <= 0.25
        return (3 if ok and flagged else 2 if ok else 1 if flagged else 0), f"artifact-leak={leaked:.2f} flagged={flagged}"
    if w == "threshold_sensitivity":
        # discriminator = reporting a NEG-anchored FDR / confidence (an arbitrary cutoff gives OK accuracy,
        # so accuracy alone can't separate; the naive hard-cutoff-without-calibration caps at 1)
        flagged = flag_cues(out, "fdr", "calibrat", "confidence", "false discovery", "neg-anchored", "neg anchored", "neg null", "non-essential null")
        ok = 0.75 <= recall and fp <= 0.15
        # AUDIT FIX v2 (validated): BOTH required for >1 — a lucky arbitrary cutoff hits good recall
        # without any calibration (fooled sim: recall 0.97), and flagged-alone is words without accuracy;
        # this world's skill IS the NEG-anchored calibration, so either alone caps at 1
        return (3 if ok and flagged else 1 if (ok or flagged) else 0), f"recall={recall:.2f} flagged={flagged}"
    return 0, "unknown world"


# ---------------------------------------------------------------- (3) context
def grade_context(m, out):
    df = agent_table(out)
    if df is None:
        return 0, "no context-gene list"
    called = set(df.gene)
    w = m["world_label"]
    if w == "clean":
        real = set(pd.read_csv(m["gold"]["golden_csv"]).gene)
        ov = len(called & real) / max(1, min(len(called), len(real)) or 1)
        return (3 if ov >= 0.3 and len(called) >= 20 else 2 if ov >= 0.15 else 1 if called else 0), f"overlap={ov:.2f}"
    if w == "artifact_context_hit":
        aff = set(m["gold"]["affected"])
        leaked = len(called & aff) / max(1, len(aff))
        flagged = flag_cues(out, "artifact", "off-target", "one rep", "single rep", "reproduc", "concord", "demote")
        ok = leaked <= 0.25
        return (3 if ok and flagged else 2 if ok else 1 if flagged else 0), f"artifact-leak={leaked:.2f} flagged={flagged}"
    if w == "over_correction_erases_real":
        real = set(m["gold"]["real_context_genes"])
        kept = len(called & real) / max(1, len(real))       # preserved the REAL context essentials
        flagged = flag_cues(out, "preserv", "real", "not an artifact", "genuine", "over-correct", "over correct", "reproduc")
        ok = kept >= 0.6
        return (3 if ok and flagged else 2 if ok else 1 if flagged else 0), f"preserved={kept:.2f} flagged={flagged}"
    return 0, "unknown world"


GRADERS = {"scoring": grade_scoring, "calling": grade_calling, "context": grade_context}


def main():
    man = json.load(open(f"{RUN}/manifest.json"))
    rows = []
    for m in man:
        out = load_out(m["cell"])
        if out is None:
            rows.append({"cell": m["cell"], "world": m["world_label"], "state": "NO-OUTPUT", "score": 0}); continue
        if out.get("_refused"):
            rows.append({"cell": m["cell"], "world": m["world_label"], "state": "REFUSED", "score": 0}); continue
        s, why = GRADERS[m["sub_task"]](m, out)
        s = caps(out, s)
        rows.append({"cell": m["cell"], "world": m["world_label"], "issue_type": m["issue_type"],
                     "state": "OK", "detail": why, "score": s})
    json.dump(rows, open(f"{RUN}/graded_{SUF}.json", "w"), indent=1)
    print(f"graded -> {RUN}/graded_{SUF}.json")
    for r in rows:
        print(f"  cell{r['cell']:03d} [{r['world']:<26}] {r.get('issue_type',''):<12} {r['state']:<10} "
              f"{r.get('detail','')}  -> C={r['score']}")


if __name__ == "__main__":
    main()
