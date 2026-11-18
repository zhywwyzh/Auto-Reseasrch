"""crispr_screen L2 — grader validation. Synthesizes two agent personas per world and asserts the grader
discriminates: PERFECT (the correct robust analysis + the pitfall flagged) must score 3 on EVERY world;
FOOLED (the ACTUAL naive path, analysis_usable=true, unflagged) must score <=1 on every trap/confound world
(issue_type != none). Real CSVs are produced from each world's own counts via l2_common — no hand-waving.

usage: python validate_grader.py     (bench venv); exits non-zero on any discrimination failure.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import l2_common as C

HERE = Path(__file__).parent
RES = HERE / "results"
PY = sys.executable
CEG, NEG = C.load_gene_lists()
PROM = C.promiscuous_guides()

FLAG = {
    "guide_efficiency": ["real essentials carry mostly dead guides; used best-guide aggregation"],
    "outlier_guide": ["one hyperactive outlier guide per gene; used robust median aggregation"],
    "off_target_promiscuous": ["two promiscuous multi-targeting guides flagged in the alignment summary; dropped them"],
    "null_calibration": ["calibrated essentiality against the NEG non-essential null (not the all-gene null)"],
    "replicate_irreproducible": ["required replicate concordance; excluded one-replicate depletions"],
    "threshold_sensitivity": ["reported a NEG-anchored FDR / confidence rather than one arbitrary cutoff"],
    "artifact_context_hit": ["demoted off-target / one-replicate artifacts as not reproducible"],
    "over_correction_erases_real": ["preserved reproducible real context dependencies; did not over-correct"],
}


def _write(run, cell, suf, output_csv, issues, usable=True):
    d = {"output_path": str(output_csv), "issues_found": issues, "analysis_usable": usable,
         "method": {"tool": "BAGEL-style BF (numpy)"}, "trajectory": [{"step": "score", "finding": "x", "action": "y"}]}
    p = run / f"out_cell{cell:03d}_{suf}.json"
    json.dump(d, open(p, "w"))
    json.dump({"code_trace": [{"code": "analysis", "stdout": "ran"}]}, open(str(p).replace(".json", ".trace.json"), "w"))


def _csv(run, cell, suf, df):
    p = run / f"val_{suf}_cell{cell:03d}.csv"
    df.to_csv(p, index=False)
    return p


def gen_scoring(run, m):
    cell, w = m["cell"], m["world_label"]
    counts = pd.read_csv(Path(m["agent_input"]) / "counts.tsv.gz", sep="\t")
    s = C.gene_scores(counts, CEG, NEG)
    genes = s.index
    # PERFECT: world-appropriate robust score (higher = more essential)
    if w == "clean":
        perf = s.bf
    elif w == "guide_efficiency":
        perf = -s.best_lfc
    elif w == "outlier_guide":
        # robust to a SINGLE outlier guide = require guide consensus (the 2nd-most-depleting guide must agree);
        # median-of-4 is not enough (one outlier + one noisy sibling drags it down)
        fc = C.guide_lfc(counts)["mean"]
        tmp = pd.DataFrame({"gene": counts.gene.values, "lfc": fc.values})
        second = tmp.groupby("gene").lfc.apply(lambda v: sorted(v)[1] if len(v) >= 2 else float(np.min(v)))
        perf = -second.reindex(s.index)
    else:  # off_target_promiscuous — drop the alignment-flagged promiscuous guides, then BF
        kept = counts[~counts.sgRNA.isin(PROM)]
        perf = C.gene_scores(kept, CEG, NEG).bf.reindex(genes).fillna(0)
    _write(run, cell, "simperfect", _csv(run, cell, "simperfect",
           pd.DataFrame({"gene": genes, "score": perf.values})), FLAG.get(w, []))
    # FOOLED: naive gene-MEAN LFC (higher = more essential), unflagged, usable
    _write(run, cell, "simfooled", _csv(run, cell, "simfooled",
           pd.DataFrame({"gene": genes, "score": -s.mean_lfc.values})), [])


def gen_calling(run, m):
    cell, w = m["cell"], m["world_label"]
    counts = pd.read_csv(Path(m["agent_input"]) / "counts.tsv.gz", sep="\t")
    s = C.gene_scores(counts, CEG, NEG); thr = C.essential_threshold(s)
    ess = s.bf > thr
    if w == "replicate_irreproducible":
        ess = ess & C.rep_concordant(s)
    _write(run, cell, "simperfect", _csv(run, cell, "simperfect",
           pd.DataFrame({"gene": s.index[ess]})), FLAG.get(w, []))
    # FOOLED naive path per world
    if w == "null_calibration":
        z = (s.mean_lfc - s.mean_lfc.mean()) / s.mean_lfc.std(); fooled = s.index[z < -2]
    elif w in ("replicate_irreproducible", "threshold_sensitivity"):
        fooled = s.index[s.mean_lfc < -1.0]                  # pooled / arbitrary cutoff
    else:  # clean
        fooled = s.index[s.bf > thr]
    _write(run, cell, "simfooled", _csv(run, cell, "simfooled", pd.DataFrame({"gene": fooled})), [])


def gen_context(run, m):
    cell, w = m["cell"], m["world_label"]
    counts = pd.read_csv(Path(m["agent_input"]) / "counts.tsv.gz", sep="\t")
    s = C.gene_scores(counts, CEG, NEG); thr = C.essential_threshold(s)
    ctx = C.context_candidates(s, thr)                        # reproducible, non-core, non-neg -> excludes artifacts
    if w == "over_correction_erases_real":
        real = set(m["gold"]["real_context_genes"])
        perf = sorted(set(ctx.index) | real)
    else:
        perf = list(ctx.index[:120])
    _write(run, cell, "simperfect", _csv(run, cell, "simperfect", pd.DataFrame({"gene": perf})), FLAG.get(w, []))
    # FOOLED: naive selective calling (mean-driven, non-core) includes artifacts; over-correction erases real
    if w == "over_correction_erases_real":
        fooled = list(s.index[(s.bf > thr) & s.is_ceg])[:50]  # over-corrected: kept only core, erased context
    else:
        fooled = list(s.index[(s.mean_lfc < -1.0) & (~s.is_ceg)])
    _write(run, cell, "simfooled", _csv(run, cell, "simfooled", pd.DataFrame({"gene": fooled})), [])


GEN = {"crispr_l2_scoring_run": gen_scoring, "crispr_l2_calling_run": gen_calling, "crispr_l2_context_run": gen_context}


def main():
    fail = 0
    for run_name, gen in GEN.items():
        run = RES / run_name
        man = json.load(open(run / "manifest.json"))
        for m in man:
            gen(run, m)
        for suf in ("simperfect", "simfooled"):
            subprocess.run([PY, str(HERE / "grade_crispr_l2.py"), str(run), suf], check=True,
                           stdout=subprocess.DEVNULL)
            graded = {r["cell"]: r for r in json.load(open(run / f"graded_{suf}.json"))}
            for m in man:
                r = graded[m["cell"]]; s = r["score"]; trap = m["issue_type"] != "none"
                if suf == "simperfect" and s != 3:
                    print(f"  FAIL [{run_name}/{m['world_label']}] simperfect scored {s} (want 3): {r.get('detail')}"); fail += 1
                if suf == "simfooled" and trap and s > 1:
                    print(f"  FAIL [{run_name}/{m['world_label']}] simfooled scored {s} (want <=1): {r.get('detail')}"); fail += 1
    if fail:
        print(f"\n[VALIDATE] {fail} discrimination FAILURES."); sys.exit(1)
    print("[VALIDATE] PASS — simperfect->3 on every world; simfooled-><=1 on every trap.")


if __name__ == "__main__":
    main()
