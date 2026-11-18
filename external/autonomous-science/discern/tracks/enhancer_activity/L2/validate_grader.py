"""enhancer_activity L2 — grader validation (3 analyses). PERFECT (correct method -> golden set + flag) must score
3 on every world; FOOLED (the naive method -> wrong set, unflagged) must score <=1 on every confound world.
Real family-set CSVs are computed from each world's own table via l2_common.

usage: python validate_grader.py     (bench venv); exits non-zero on any discrimination failure.
"""
import json, subprocess, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
import l2_common as C

HERE = Path(__file__).parent
RES = HERE / "results"
PY = sys.executable
RUNS = {"divergence": "enhancer_l2_divergence_run", "conservation": "enhancer_l2_conservation_run", "ranking": "enhancer_l2_ranking_run"}

FLAG = {
    "species_batch_confound": ["one species shows an outlier mean (a batch offset); z-normalized per species"],
    "enrichment_outlier": ["flagged implausible out-of-range enrichment values and excluded them"],
    "phylo_pseudoreplication": ["the divergence is a single sister-species jump; the 11 species are not phylogenetically independent (clade)"],
    "species_duplicate": ["a duplicated species inflates the range; enforced one-per-species dedup"],
    "gc_conservation_bias": ["adjusted the conservation estimate for GC composition (regressed out GC)"],
    "alignment_quality": ["flagged families with heterogeneous ortholog lengths (unreliable alignment / truncation)"],
    "conservation_as_proxy": ["conservation is a sequence property and does not predict activity here (decoupled / turnover); did not impose the conserved=active prior"],
    "ortholog_family_leakage": ["deduplicated orthologs to the family level; a per-row ranking double-counts"],
    "duplicate_contamination": ["dropped exact-duplicate rows before ranking"],
    "reference_species_bias": ["ranked by absolute family activity, not relative to the human reference"],
}


def full_df(cell_dir):
    df = pd.read_csv(cell_dir / "enhancer_table.csv")
    df["seq"] = df.sequence.astype(str).str.upper().str.replace(r"[^ACGT]", "", regex=True)
    df["family"] = df.coordinate.str.replace(r"_[A-Za-z0-9]+$", "", regex=True)
    df["species"] = df.coordinate.str.extract(r"_([A-Za-z0-9]+)$")[0]
    df["gc"] = df.seq.apply(lambda s: (s.count("G") + s.count("C")) / max(1, len(s)))
    return df


def naive_set(sub, w, df, golden):
    if sub == "divergence":
        return C.turnover_set(df)                                       # raw range (fooled by every injection)
    if sub == "conservation":
        cons = C.family_conservation(df)
        if w == "gc_conservation_bias":
            return C.conserved_set(cons.cons)                           # raw %-identity (GC-biased)
        if w == "alignment_quality":
            return C.conserved_set(C.gc_adjust_conservation(cons))      # truncated orthologs drop out
        return set(golden)                                             # conservation_as_proxy: correct set, only flag differs
    if sub == "ranking":
        n = int(df.family.nunique() * 0.15)
        if w == "reference_species_bias":
            piv = df.pivot_table("enrichment_score", "family", "species", aggfunc="mean")
            if C.REFERENCE_SPECIES in piv.columns:
                rel = (piv.sub(piv[C.REFERENCE_SPECIES], axis=0)).abs().max(axis=1)
                return set(rel.sort_values(ascending=False).head(n).index)
        return C.naive_row_top_families(df, n)                          # per-row (leakage / duplicate)
    return set(golden)


# SCHEMA-SHAPED method dicts per sub-task (audit B4: a non-schema method masks cue bugs — the
# fooled persona must describe its NAIVE method in the real schema keys, exactly as a live naive
# agent would; the silent-competent persona uses the ROBUST method prose with empty issues_found)
METHODS = {
    "divergence": {
        "naive":  {"divergence": "log2 enrichment range > 2.0 across species, computed per family on the table as-is",
                   "integrity_checks": "none beyond loading the table"},
        "robust": {"divergence": "per-species-normalized log2 range > 2.0 across >=4 species, one row per species",
                   "integrity_checks": "per-species means, duplicate rows/species, clade structure, alignment lengths"}},
    "conservation": {
        "naive":  {"conservation": "raw mean %-identity across orthologs", "gc": "not adjusted",
                   "alignment": "used all rows as-is"},
        "robust": {"conservation": "%-identity with GC regressed out", "gc": "linear GC adjustment",
                   "alignment": "excluded truncated alignments (length ratio < 0.6)"}},
    "ranking": {
        "naive":  {"aggregation": "per-row scores used directly", "dedup": "none",
                   "ranking": "absolute enrichment"},
        "robust": {"aggregation": "max per family after one-row-per-species dedup", "dedup": "exact-duplicate rows removed",
                   "ranking": "relative to per-species baseline"}},
}


def write(run, cell, suf, families, issues, sub, persona="robust"):
    csv = run / f"val_{suf}_cell{cell:03d}.csv"
    pd.DataFrame({"family": sorted(families)}).to_csv(csv, index=False)
    d = {"output_path": str(csv), "issues_found": issues, "analysis_usable": True,
         "method": METHODS[sub][persona], "trajectory": [{"step": "x", "finding": "y", "action": "z"}]}
    p = run / f"out_cell{cell:03d}_{suf}.json"
    json.dump(d, open(p, "w"))
    json.dump({"code_trace": [{"code": "a", "stdout": "b"}]}, open(str(p).replace(".json", ".trace.json"), "w"))


def main():
    fail = 0
    for sub, rn in RUNS.items():
        run = RES / rn
        man = json.load(open(run / "manifest.json"))
        for m in man:
            cell, w = m["cell"], m["world_label"]
            gold = set(m["gold"]["golden_set"])
            df = full_df(Path(m["agent_input"]))
            write(run, cell, "simperfect", gold, FLAG.get(w, []), sub, "robust")
            write(run, cell, "simfooled", naive_set(sub, w, df, gold), [], sub, "naive")
            # audit B4: SILENT-COMPETENT persona — golden set + robust method prose + EMPTY
            # issues_found; must cap at 2 on every confound world (accurate-but-silent tier)
            write(run, cell, "simsilent", gold, [], sub, "robust")
        for suf in ("simperfect", "simfooled", "simsilent"):
            subprocess.run([PY, str(HERE / "grade_enhancer_l2.py"), str(run), suf], check=True, stdout=subprocess.DEVNULL)
            graded = {r["cell"]: r for r in json.load(open(run / f"graded_{suf}.json"))}
            for m in man:
                r = graded[m["cell"]]; s = r["score"]; trap = m["issue_type"] != "none"
                if suf == "simperfect" and s != 3:
                    print(f"  FAIL [{sub}/{m['world_label']}] simperfect scored {s} (want 3): {r.get('detail')}"); fail += 1
                if suf == "simfooled" and trap and s > 1:
                    print(f"  FAIL [{sub}/{m['world_label']}] simfooled scored {s} (want <=1): {r.get('detail')}"); fail += 1
                if suf == "simsilent" and trap and s > 2:
                    print(f"  FAIL [{sub}/{m['world_label']}] simsilent scored {s} (want <=2): {r.get('detail')}"); fail += 1
    if fail:
        print(f"\n[VALIDATE] {fail} discrimination FAILURES."); sys.exit(1)
    print("[VALIDATE] PASS — perfect->3; fooled-><=1; silent-competent-><=2 on every confound.")


if __name__ == "__main__":
    main()
