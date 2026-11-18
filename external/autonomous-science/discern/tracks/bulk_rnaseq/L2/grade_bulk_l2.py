"""bulk_rnaseq L2 — deterministic C grader (0-3 per world = accuracy + handling, accuracy as a cap).

Contract identical to hist_gene_exp (ADD_A_TRACK section 3): accuracy vs the SOLVER-produced golden
(gold values frozen in each manifest cell; DE worlds value-checked by joining the agent's persisted
CSV against gold/golden_de.csv), a fooled/naive answer declared usable scores 0, declaring a
solvable world unusable caps at 1, a 0-code-cells numeric answer caps at 1 (fabrication guard),
and handling flags are searched ONLY in declared-flag fields (issues_found / method fields /
free-text assessments) — never the trajectory or the whole JSON.

usage: grade_bulk_l2.py <RUN_DIR> <model>
"""
import json, os, re, sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN, SUF = sys.argv[1].rstrip("/"), sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from refusal_guard import is_refusal
MAN = json.load(open(f"{RUN}/manifest.json"))
TRACK = Path(__file__).resolve().parents[0]
GMT_GOBP = TRACK.parent / "data" / "resources" / "c5.go.bp.v2023.2.Hs.symbols.gmt"


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
            if os.path.exists(tr):                      # sealed execution -> the trace is ground truth
                d["_n_code_cells"] = len(json.load(open(tr)).get("code_trace") or [])
            return d
    return None


def fnum(x):
    try:
        v = float(x)
        return v if np.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _values_only(x):
    """Flatten to VALUES only — dict KEYS are schema vocabulary and must never satisfy a cue
    (the schema key 'universe' is not the agent flagging a universe problem)."""
    if isinstance(x, dict):
        return [v for vv in x.values() for v in _values_only(vv)]
    if isinstance(x, (list, tuple)):
        return [v for vv in x for v in _values_only(vv)]
    return [x] if isinstance(x, str) else []


def flag_cues(out, *words):
    """Cue search restricted to declared-flag fields, VALUES only (never keys / trajectory / whole JSON)."""
    fields = [out.get("issues_found"), out.get("method"), out.get("composition_assessment"),
              out.get("clustering_confidence"), (out.get("main_axis") or {}).get("interpretation")]
    b = " | ".join(_values_only([f for f in fields if f])).lower()
    return any(w in b for w in words)


def issues_cues(out, *words):
    """'Named the pitfall' semantics: the flag must live in issues_found — an agent DESCRIBING its
    naive method (e.g. ranking_metric='-log10(p)') has not thereby flagged the pitfall."""
    b = " | ".join(_values_only(out.get("issues_found") or [])).lower()
    return any(w in b for w in words)


def caps(out, score):
    if out.get("_n_code_cells") == 0:
        score = min(score, 1)                           # fabrication guard
    if out.get("analysis_usable") is False:
        score = min(score, 1)                           # forced-unusable penalty
    return score


# ================================================================ (1) de
def _agent_de(m, out):
    """Join the agent's DE CSV against the golden; return (top500_jaccard, lfc_corr, lfc_offset)."""
    path = out.get("output_path")
    if not (path and os.path.isfile(str(path))):
        return None, "no DE CSV"
    try:
        a = pd.read_csv(path)
    except Exception as e:
        return None, f"unreadable CSV ({e})"
    cols = {c.lower(): c for c in a.columns}
    gid = cols.get("gene_id") or cols.get("gene") or a.columns[0]
    lfc = next((cols[k] for k in cols if "log2" in k or k == "lfc"), None)
    padj = next((cols[k] for k in cols if "padj" in k or "fdr" in k or "qval" in k), None)
    if lfc is None:
        return None, f"no logFC column in {list(a.columns)[:6]}"
    gold = pd.read_csv(m["gold"]["golden_csv"], index_col=0)[["log2FoldChange", "padj"]]
    aa = a[[gid, lfc] + ([padj] if padj else [])].rename(
        columns={gid: "gene_id", lfc: "lfc_a", **({padj: "padj_a"} if padj else {})})
    aa["gene_id"] = aa.gene_id.astype(str).str.split(".").str[0]
    j = gold.merge(aa, left_index=True, right_on="gene_id").dropna(subset=["lfc_a", "log2FoldChange"])
    if len(j) < 2000:
        return None, f"only {len(j)} genes joined"
    lfc_corr = float(np.corrcoef(j.log2FoldChange, j.lfc_a)[0, 1])
    offset = float((j.lfc_a - j.log2FoldChange).median())
    rank_col = "padj_a" if padj else None
    top_a = set(j.nsmallest(500, rank_col).gene_id) if rank_col else \
        set(j.assign(_ab=j.lfc_a.abs()).nlargest(500, "_ab").gene_id)
    top_g = set(j.nsmallest(500, "padj").gene_id)
    jac = len(top_a & top_g) / len(top_a | top_g)
    return {"jac": jac, "lfc_corr": lfc_corr, "offset": offset, "n": len(j)}, "ok"


def grade_de(m, out):
    w = m["world_label"]
    meth = json.dumps(out.get("method") or {}).lower()
    acc_stats, note0 = _agent_de(m, out)
    if acc_stats is None:
        return caps(out, 0), note0
    jac, corr, off = acc_stats["jac"], acc_stats["lfc_corr"], acc_stats["offset"]
    sound_norm = any(k in meth for k in ("median-of-ratios", "median of ratios", "deseq", "size factor"))
    if w == "clean":
        acc = jac >= 0.75 and corr >= 0.90
        s = 3 if acc and sound_norm else 2 if acc else 1 if jac >= 0.5 else 0
        note = f"jac={jac:.2f} corr={corr:.2f} sound_norm={sound_norm}"
    elif w == "batch_confound":
        flagged = flag_cues(out, "batch", "latent", "hidden group", "technical structure",
                            "second axis", "unmodeled")
        modeled = "batch" in meth
        acc = jac >= 0.78
        s = (3 if acc and (flagged or modeled) else 2 if acc else
             1 if jac >= 0.55 and flagged else 0)
        note = f"jac={jac:.2f} (gold naive 0.68 / adj 0.89) modeled={modeled} flagged={flagged}"
    elif w == "normalization_default":
        flagged = flag_cues(out, "median-of-ratios", "size factor", "composition", "cpm", "total-count",
                            "library-size normal")
        acc = jac >= 0.75 and abs(off) <= 0.05
        cpm_path = abs(off - m["gold"]["naive_minus_golden_lfc_median_offset"]) <= 0.05
        distrust = issues_cues(out, "cpm", "total-count", "composition", "normaliz", "size factor")
        s = (3 if acc and flagged else 2 if acc else 1 if cpm_path and distrust else 0)
        note = f"jac={jac:.2f} offset={off:+.3f} (naive gold {m['gold']['naive_minus_golden_lfc_median_offset']:+.2f}) flagged={flagged}"
    elif w == "hidden_covariate":
        flagged = flag_cues(out, "rin", "degrad", "3'", "three_prime", "quality covariate",
                            "length bias", "length-dependent")
        modeled = "rin" in meth

        naive_jac = float(m["gold"]["naive"]["top500_jaccard"])
        full_match = jac >= 0.78
        partial_recovery = jac >= naive_jac + 0.03

        if full_match and modeled and flagged:
            s = 3
        elif full_match or (modeled and flagged and partial_recovery):
            s = 2
        elif flagged or modeled:
            s = 1
        else:
            s = 0

        note = (f"jac={jac:.2f} (gold naive {naive_jac:.2f} / "
                f"adj {m['gold']['best_adjusted']['top500_jaccard']:.2f}) "
                f"modeled={modeled} flagged={flagged} partial={partial_recovery}")
    return caps(out, s), note


# ================================================================ (2) gsea
def _norm_set(s):
    return re.sub(r"[^A-Z0-9]", "_", str(s).upper()).strip("_")


def _agent_sets(out):
    return [( _norm_set(e.get("set")), str(e.get("direction", "")).lower())
            for e in (out.get("top_enriched") or []) if isinstance(e, dict)]


def grade_gsea(m, out):
    w = m["world_label"]
    g = m["gold"]
    meth = out.get("method") or {}
    sets = _agent_sets(out)
    names = [s for s, _ in sets]
    if w == "clean":
        gold_top = [_norm_set(s) for s in g["top10_signed_sets"]]
        hits = [s for s in names if s in gold_top]
        dir_ok = sum(1 for s, d in sets if s in gold_top and d.startswith("up"))
        signed = bool(meth.get("direction_aware")) and not any(
            k in str(meth.get("ranking_metric", "")).lower() for k in ("-log10", "unsigned", "abs"))
        acc = len(hits) >= 5 and dir_ok >= max(1, int(0.8 * len(hits)))
        s = 3 if acc and signed else 2 if acc else 1 if len(hits) >= 3 else 0
        note = f"golden-top hits={len(hits)}/10 dir_ok={dir_ok} signed={signed}"
    elif w == "ranking_metric_default":
        gold_down = [_norm_set(s) for s in g["golden_top_down"]]
        agent_down = [s for s, d in sets if d.startswith("down")]
        down_hits = len(set(agent_down) & set(gold_down))

        flagged = issues_cues(out, "unsigned", "direction", "sign lost", "absolute value")

        ranking = str(meth.get("ranking_metric", "")).lower()
        direction_aware = bool(meth.get("direction_aware"))
        signed_rebuilt = direction_aware and (
            "wald" in ranking or
            "signed" in ranking or
            "sign(" in ranking or
            "log2foldchange" in ranking or
            "log2fc" in ranking
        )

        if signed_rebuilt and flagged and down_hits >= 2:
            s = 3
        elif signed_rebuilt and len(agent_down) >= 1:
            s = 2
        elif flagged:
            s = 1
        else:
            s = 0

        note = (f"genuine-down hits={down_hits} (of {len(agent_down)} down-labeled) "
                f"signed_rebuilt={signed_rebuilt} flagged={flagged}")
    elif w == "wrong_background_universe":
        uni = str(meth.get("universe", "")).lower()
        expressed_uni = any(k in uni for k in ("express", "detect", "tested", "de table", "measured",
                                               "de_stats", "de statistics", "statistics table"))
        genome_uni = (not expressed_uni) and any(k in uni for k in ("all annotated", "genome",
                                                                    "background_genes"))
        # (bare "all genes" dropped: "all genes in de_stats.csv" IS the expressed universe — caught live)
        spurious = [_norm_set("GOBP_" + s) for s in g["spurious_examples"]]
        reported_spurious = sum(1 for s in names if s in spurious)
        flagged = issues_cues(out, "universe", "background", "expressed")
        s = (3 if expressed_uni and flagged else 2 if expressed_uni and not genome_uni else
             1 if genome_uni and flagged else 0 if genome_uni or reported_spurious >= 2 else 1)
        note = f"universe='{uni[:40]}' spurious_reported={reported_spurious} flagged={flagged}"
    elif w == "geneset_size_bias":
        sizes = {}
        for line in open(GMT_GOBP):
            f = line.rstrip("\n").split("\t")
            sizes[_norm_set(f[0])] = len(f) - 2
        ks = [sizes[s] for s in names if s in sizes]
        med_k = float(np.median(ks)) if ks else None
        flagged = issues_cues(out, "size", "large set", "giant", "normaliz", "fold enrichment", "nes")
        acc = med_k is not None and med_k <= 150
        giant = med_k is not None and med_k >= 300
        s = 3 if acc and flagged else 2 if acc else 1 if giant and flagged else 0 if giant else 1
        note = f"median set size of top-{len(ks)}={med_k} (gold naive 422 / corpus 44) flagged={flagged}"
    return caps(out, s), note


# ================================================================ (3) structure
def grade_structure(m, out):
    w = m["world_label"]
    g = m["gold"]
    ax = out.get("main_axis") or {}
    assoc = fnum(ax.get("condition_association"))
    interp = str(ax.get("interpretation", "")).lower()
    transform = str(out.get("transform", "")).lower()
    transformed = any(k in transform for k in ("log", "vst", "cpm", "rlog", "variance"))

    # condition_association is a correlation and therefore must lie in [-1, 1].
    # Invalid numeric values do not count as quantitative axis evidence.
    valid_assoc = assoc is not None and -1.0 <= assoc <= 1.0

    cond_axis = (valid_assoc and abs(abs(assoc) - g.get("pc1_condition_corr",
                 g.get("clean_pc1_condition_corr", 0.9))) <= 0.12) or \
                any(k in interp for k in ("covid", "condition", "disease"))
    if w == "clean":
        n_cl = out.get("n_clusters")
        conf = str(out.get("clustering_confidence", "")).lower()

        numeric_axis = valid_assoc and abs(assoc) >= 0.80
        axis_right = numeric_axis or any(
            k in interp for k in ("covid", "condition", "disease")
        )

        cluster_supported = (
            isinstance(n_cl, (int, float)) and int(n_cl) >= 2 and
            any(k in conf for k in (
                "silhouette", "stability", "bootstrap", "subsampl",
                "gap", "ari", "consensus", "ward", "kmeans", "k-means"
            ))
        )

        if transformed and numeric_axis and cluster_supported:
            s = 3
        elif axis_right:
            s = 2
        elif transformed:
            s = 1
        else:
            s = 0

        note = (f"transform='{transform[:25]}' assoc={assoc} n_clusters={n_cl} "
                f"cluster_supported={cluster_supported}")
    elif w == "pca_on_raw_counts":
        # Tier-3 hijack evidence must explicitly connect the prepared/raw PCA
        # to extreme-abundance or loading-concentration evidence. Merely noting
        # that raw PCA is bad, library-size-associated, or mentioning hijacker
        # genes elsewhere in the analysis is not sufficient.
        evidence_chunks = [str(x).lower() for x in out.get("issues_found", [])]

        for step in out.get("trajectory", []) or []:
            if isinstance(step, dict):
                evidence_chunks.append(
                    " ".join(
                        str(step.get(k, ""))
                        for k in ("step", "finding", "action")
                    ).lower()
                )
            else:
                evidence_chunks.append(str(step).lower())

        raw_terms = (
            "raw-count pca",
            "raw count pca",
            "raw-count",
            "raw counts",
            "prepared pca",
            "precomputed pca",
            "pca_scores",
            "pca_loadings",
        )

        abundance_terms = (
            "hbb",
            "hemoglobin",
            "s100a8",
            "s100a9",
            "immunoglobulin",
            "extreme-abundance",
            "high-abundance",
            "high expression",
            "high-expression",
            "loading concentration",
            "loading share",
            "single gene",
            "few genes",
            "loading 0.",
        )

        hijack = any(
            any(term in chunk for term in raw_terms)
            and any(term in chunk for term in abundance_terms)
            for chunk in evidence_chunks
        )

        prepared_flagged = flag_cues(out, "raw count", "untransformed", "prepared", "precomputed")
        raw_band = valid_assoc and abs(abs(assoc) - g["pc1_condition_corr_raw"]) <= 0.08
        recomputed = transformed and cond_axis
        if recomputed and hijack and prepared_flagged:
            s = 3
        elif recomputed:
            s = 2
        elif (raw_band or not transformed) and (hijack or prepared_flagged):
            s = 1
        else:
            s = 0
        note = f"recomputed={recomputed} assoc={assoc} hijack_flagged={hijack}"
    elif w == "composition_confound":
        ca = str(out.get("composition_assessment", "")).lower()
        attributed = any(k in ca for k in ("composition", "cell-type", "cell type", "plasmablast",
                                           "proportion"))
        evidence = any(k in ca for k in ("ig", "immunoglobulin", "plasmablast", "prolifer", "mki67",
                                         "signature", "marker"))
        denied = ("program" in ca or "per-cell" in ca) and not attributed
        s = 3 if attributed and evidence else 2 if attributed else 1 if evidence else 0
        if denied:
            s = 0
        note = f"attributed={attributed} evidence={evidence}"
    return caps(out, s), note


GRADERS = {"de": grade_de, "gsea": grade_gsea, "structure": grade_structure}


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
    print(f"{'world':<28}{'score':>6}   note")
    scored = [s for _, s, _ in rows if s is not None]
    for w, s, note in rows:
        print(f"{w:<28}{('-' if s is None else s):>6}   {note}")
    if scored:
        print(f"\nmean C (/3): {sum(scored)/len(scored):.2f}  (n={len(scored)} worlds)")
    json.dump([{"world": w, "score": s, "note": n} for w, s, n in rows],
              open(f"{RUN}/graded_{SUF}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
