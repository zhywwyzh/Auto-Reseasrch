"""enhancer_activity L2 — world builder (3 analyses, cross-species DATA-CONFOUND focus).
RUN ONLY AFTER reference_solver.py exits 0. Worlds are DIRECTORIES: meta.json + enhancer_table.csv (clean or the
injected DELTA). Golden sets are NEVER in agent-visible dirs.

  results/enhancer_l2_divergence_run/     clean/species_batch/enrichment_outlier/phylo_pseudoreplication/species_duplicate
  results/enhancer_l2_conservation_run/   clean/gc_conservation_bias/alignment_quality/conservation_as_proxy
  results/enhancer_l2_ranking_run/        clean/ortholog_family_leakage/duplicate_contamination/reference_species_bias

usage: python world_builder.py     (bench venv)
"""
import json, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))          # repo root -> task_spec
import l2_common as C
import task_spec as _T

HERE = Path(__file__).parent
RES = HERE / "results"
GOLD = json.load(open(HERE / "gold" / "gold_solver.json"))
assert all(c["pass"] for c in GOLD["_verification"]), "FAILED fire checks — re-run reference_solver.py."
DF = C.load_klein()
# SELF-STAMP expected_method + verify_rubric from the spec (no separate stamp_methods step; stamp-drop bug fixed)
_L2SPEC = _T.load("enhancer_activity")["L2"]
def _stamp(sub):
    return {"expected_method": _L2SPEC[sub]["expected_method"], "verify_rubric": _L2SPEC[sub]["info"]["rubric"]}
CTX = "Klein 2018 cross-species STARR-seq enhancer activity (real; 11 primate species, ~327 ortholog families)"


def cell(run, n):
    d = run / "data" / f"cell{n:03d}"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d


def build(sub, run_name, task, family_key, worlds):
    """worlds = list of (label, itype, df_or_None, gold_extra, tell, note, correct_action). df None => clean DF."""
    run = RES / run_name
    g = GOLD[sub]
    golden_set = g["clean"][family_key]
    manifest = []
    for n, (label, itype, dfw, gkey, tell, note, action) in enumerate(worlds):
        d = cell(run, n)
        C.agent_view(dfw if dfw is not None else DF).to_csv(d / "enhancer_table.csv", index=False)
        json.dump({"task": task, "layout": {"enhancer_table": "enhancer_table.csv (coordinate, enrichment_score, "
                   "sequence); one row per species-ortholog; family = coordinate minus the trailing _<assembly>"},
                   "context": CTX}, open(d / "meta.json", "w"), indent=1)
        gold = {**(g.get(gkey, {}) if gkey else {}), "golden_csv": g["golden_csv"], "golden_set": golden_set}
        row = {"cell": n, "task": f"enhancer_{sub}", "sub_task": sub, "world_label": label, "issue_type": itype,
               "agent_input": str(d), "agent_output": str(run / f"out_cell{n:03d}.json"), "gold": gold,
               "correct_action": action, **_stamp(sub)}
        if tell:
            row["confound_tell"] = tell
        if note:
            row["note"] = note
        manifest.append(row)
    json.dump(manifest, open(run / "manifest.json", "w"), indent=1)
    print(f"[{sub}] {len(manifest)} worlds -> {run}/manifest.json")


def main():
    RES.mkdir(exist_ok=True)
    g = GOLD

    # ---------- (1) divergence ----------
    d_sb, _ = C.inj_species_batch(DF); d_eo, _ = C.inj_enrichment_outlier(DF)
    d_ph, _ = C.inj_phylo_pseudoreplication(DF); d_du, _ = C.inj_species_duplicate(DF)
    build("divergence", "enhancer_l2_divergence_run",
          ("Cross-species activity divergence: identify the enhancer FAMILIES whose activity diverged (turned over) "
           "across species; write them to a CSV (column: family) and report output_path. VERIFY input integrity "
           "(per-species scale, implausible values, phylogenetic non-independence, one-per-species) before trusting."),
          "turnover_families", [
            ("clean", "none", None, None, None, None,
             "per-family cross-species range; call turnover at range>thr with >=min_species"),
            ("species_batch_confound", "data-confound", d_sb, "species_batch_confound",
             f"one species ({g['divergence']['species_batch_confound']['species']}) has a "
             f"+{g['divergence']['species_batch_confound']['offset']} assay offset -> naive fabricates "
             f"{g['divergence']['species_batch_confound']['naive_spurious']} spurious turnover families; per-species "
             f"normalization recovers ({g['divergence']['species_batch_confound']['robust_spurious']})", None,
             "detect the outlier per-species mean and z-normalize per species before divergence"),
            ("enrichment_outlier", "data-confound", d_eo, "enrichment_outlier",
             f"{g['divergence']['enrichment_outlier']['n']} families got one IMPLAUSIBLE out-of-range value -> naive "
             f"calls {g['divergence']['enrichment_outlier']['naive_fake']} turnover; flagging implausible values recovers", None,
             "verify value plausibility (robust range/MAD); exclude implausible out-of-range enrichment values"),
            ("phylo_pseudoreplication", "data-confound", d_ph, "phylo_pseudoreplication",
             f"turnover in {g['divergence']['phylo_pseudoreplication']['n']} families is a SINGLE sister-species jump "
             f"(one species disagrees with its phylo-neighbour) -> naive calls "
             f"{g['divergence']['phylo_pseudoreplication']['naive_fake']}, clade-robust "
             f"{g['divergence']['phylo_pseudoreplication']['robust_fake']}", None,
             "the 11 species are NOT independent; require the divergence to be consistent across a clade "
             "(neighbour agrees, or a 2nd species is deviant) — a single sister jump is correlated noise"),
            ("species_duplicate", "data-confound", d_du, "species_duplicate",
             f"{g['divergence']['species_duplicate']['n']} families have a DUPLICATED species under an extreme value "
             f"(a merge/label error) -> naive calls {g['divergence']['species_duplicate']['naive_fake']} turnover; "
             f"enforcing one-per-species (dedup) recovers", None,
             "enforce one row per species per family (dedup duplicated species) before computing divergence"),
          ])

    # ---------- (2) conservation ----------
    d_aq, _ = C.inj_alignment_quality(DF)
    build("conservation", "enhancer_l2_conservation_run",
          ("Sequence conservation: rank enhancer FAMILIES by sequence conservation of their 11-species "
           "orthologs and report the top ~25% most conserved; write them to a CSV (column: family) and report "
           "output_path. Verify your conservation estimate is methodologically sound before trusting it."),
          "conserved_families", [
            ("clean", "none", None, None, None, None,
             "per-family ortholog sequence conservation; rank the most conserved (GC-adjusted)"),
            ("gc_conservation_bias", "tool-trap", None, "gc_conservation_bias",
             f"GC content biases the raw %-identity conservation estimate "
             f"(corr {g['conservation']['gc_conservation_bias']['gc_cons_corr']}) -> GC-extreme families are "
             f"mis-ranked; regress out GC", "task-framed world: data identical to clean; graded on adjusting for GC",
             "adjust the conservation estimate for GC content (regress it out) before ranking conserved families"),
            ("alignment_quality", "data-confound", d_aq, "alignment_quality",
             f"{g['conservation']['alignment_quality']['n']} high-conservation families got a TRUNCATED ortholog -> "
             f"raw conservation drops and {g['conservation']['alignment_quality']['naive_dropped']} fall out of the "
             f"conserved set; length-heterogeneity flags {g['conservation']['alignment_quality']['flagged']}", None,
             "flag families with heterogeneous ortholog lengths (unreliable alignment) and exclude/repair them "
             "rather than mis-ranking them as non-conserved"),
            ("conservation_as_proxy", "data-confound", None, "conservation_as_proxy",
             f"sequence conservation and activity are DECOUPLED in this data "
             f"(corr {g['conservation']['conservation_as_proxy']['cons_activity_corr']} ~ null) -> do NOT read "
             f"'conserved' as 'active-here'", "task-framed world: data identical to clean; graded on reporting the "
             "real (null) conservation-activity relationship, not the memorized 'conserved=functional' prior",
             "report conservation as a SEQUENCE property; do not impose the 'conserved => active' prior — the data "
             "shows conservation does not predict activity here (the turnover phenomenon)"),
          ])

    # ---------- (3) ranking ----------
    d_dup, _ = C.inj_duplicate_rows(DF)
    build("ranking", "enhancer_l2_ranking_run",
          ("Most-active enhancers: identify the most ACTIVE enhancer FAMILIES; write them to a CSV (column: family) "
           "and report output_path. The table has one row PER SPECIES-ortholog of each family — handle the cross-"
           "species structure (do not double-count a family across its 11 species, watch for duplicate rows and "
           "human-reference bias) before ranking."),
          "active_families", [
            ("clean", "none", None, None, None, None,
             "family activity = max over species-orthologs; rank the top families (deduped to family)"),
            ("ortholog_family_leakage", "data-confound", None, "ortholog_family_leakage",
             f"a per-ROW top ranking double-counts the same family across species: the top rows span only "
             f"~{int(g['ranking']['ortholog_family_leakage']['n_top']*(1-g['ranking']['ortholog_family_leakage']['row_top_dup_frac']))} "
             f"families ({g['ranking']['ortholog_family_leakage']['row_top_dup_frac']:.0%} ortholog dups); dedup to family",
             "task-framed world: data identical to clean; graded on deduplicating orthologs to the family level",
             "aggregate to the FAMILY level (one activity per family, e.g. max over its species-orthologs) before "
             "ranking — a per-row ranking double-counts each family across its 11 species"),
            ("duplicate_contamination", "data-confound", d_dup, "duplicate_contamination",
             f"{g['ranking']['duplicate_contamination']['n_dup']} EXACT-duplicate rows of active enhancers were "
             f"injected (a merge error) -> the naive active set inflates; dropping exact duplicates recovers", None,
             "drop exact-duplicate rows (same coordinate + value) before ranking activity"),
            ("reference_species_bias", "data-confound", None, "reference_species_bias",
             f"ranking families by activity RELATIVE TO HUMAN differs from absolute activity "
             f"(jaccard {g['ranking']['reference_species_bias']['jaccard_vs_absolute']}) -> it over-ranks human-"
             f"outlier families", "task-framed world: data identical to clean; graded on ranking by ABSOLUTE family "
             "activity, not activity-relative-to-one-reference-species",
             "rank by absolute family activity (max/mean over species), not activity relative to a single reference "
             "species (human) — the reference-relative measure biases toward human-outlier families"),
          ])

    n_dc = n_tt = 0
    for r in ("enhancer_l2_divergence_run", "enhancer_l2_conservation_run", "enhancer_l2_ranking_run"):
        man = json.load(open(RES / r / "manifest.json"))
        n_dc += sum(1 for m in man if m["issue_type"] == "data-confound")
        n_tt += sum(1 for m in man if m["issue_type"] == "tool-trap")
    assert n_dc >= 1 and n_tt >= 1, "need >=1 data-confound AND >=1 tool-trap (ADD_A_TRACK)"
    print(f"[world_builder] done — {n_dc} data-confound + {n_tt} tool-trap worlds across 3 analyses")


if __name__ == "__main__":
    main()
