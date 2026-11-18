"""crispr_screen L2 — world builder. RUN ONLY AFTER reference_solver.py exits 0 (all fire checks).

RE-AUTHORED 2026-08-12 (see RECOVERY_NOTE.md): reconstruction of the canonical scoring/calling/context builder,
imports the canonical l2_common, freezes the three sub-task run dirs from gold/gold_solver.json. Worlds are
DIRECTORIES: meta.json + counts.tsv.gz (clean or the injected DELTA) + optional prepared artifact. The CEGv2/NEGv1
gold lists + the TKOv3 alignment summary are mounted read-only at their resource paths. Golden values NEVER inside
agent-visible dirs.

  results/crispr_l2_scoring_run/  (1) clean / guide_efficiency / off_target_promiscuous
  results/crispr_l2_calling_run/  (2) clean / null_calibration / replicate_irreproducible / threshold_sensitivity
  results/crispr_l2_context_run/  (3) clean / artifact_context_hit / over_correction_erases_real

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
assert all(c["pass"] for c in GOLD["_verification"]), \
    "gold_solver.json contains FAILED fire checks — re-run reference_solver.py until all pass."

# STAMP EMISSION (protein/hist/bulk lesson): write expected_method + verify_rubric into every manifest row FROM the
# spec, so a rebuild can never silently strip the verify rubrics (the recurring stamp-drop bug). No separate
# stamp_methods step required for L2 — this is the last-write authority.
_L2SPEC = _T.load("crispr_screen")["L2"]
def _stamp(sub):
    return {"expected_method": _L2SPEC[sub]["expected_method"], "verify_rubric": _L2SPEC[sub]["info"]["rubric"]}

CEG, NEG = C.load_gene_lists()
COUNTS = C.load_counts()
CONTEXT = "HAP1 TKOv3 pooled CRISPR-KO fitness screen (real); plasmid T0 + 3 endpoint replicates"
RESOURCES = {"core_essential": str(C.CEG_F), "non_essential": str(C.NEG_F),
             "library_alignment": str(C.ALIGN_F)}


def cell_dir(run, cell):
    d = run / "data" / f"cell{cell:03d}"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d


def write_counts(d, counts):
    counts.to_csv(d / "counts.tsv.gz", sep="\t", index=False, compression="gzip")


def base_meta(task, extra_layout=None):
    layout = {"counts": "counts.tsv.gz (raw integer guide counts: sgRNA, gene, T0, rep1, rep2, rep3)",
              "reference_sets": "CEGv2 / NEGv1 gold gene lists + the TKOv3 alignment summary are readable "
                                "at the absolute paths in resources"}
    if extra_layout:
        layout.update(extra_layout)
    return {"task": task, "layout": layout, "resources": RESOURCES, "context": CONTEXT}


# ================================================================ (1) scoring
def build_scoring():
    run = RES / "crispr_l2_scoring_run"
    g = GOLD["scoring"]
    task = ("Guide -> gene dependency scoring: compute a per-gene essentiality score for every gene from the "
            "guide counts, write it to a CSV (columns: gene, score; more-essential = more negative or higher-"
            "confidence, state your convention), report its absolute path in output_path, and verify the "
            "scores against the known essential/non-essential gene sets before trusting them.")
    manifest = []

    def add(cell, label, itype, counts, gold, tell=None, note=None, extra=None):
        d = cell_dir(run, cell)
        write_counts(d, counts)
        json.dump(base_meta(task, extra), open(d / "meta.json", "w"), indent=1)
        row = {"cell": cell, "task": "crispr_scoring", "sub_task": "scoring", "world_label": label,
               "issue_type": itype, "agent_input": str(d),
               "agent_output": str(run / f"out_cell{cell:03d}.json"),
               "gold": {**gold, "golden_csv": g["golden_csv"], "essential_thr": g["essential_thr"]}}
        if tell:
            row["confound_tell"] = tell
        if note:
            row["note"] = note
        row.update(_stamp(row["sub_task"]))                  # expected_method + verify_rubric from the spec
        row["correct_action"] = {
            "clean": "normalize to T0, guide LFC, aggregate to gene; verify vs CEG/NEG",
            "guide_efficiency": "a real essential can carry mostly DEAD guides; use best-guide / rank-based "
                                "(BAGEL/MAGeCK-RRA) aggregation, not a naive gene-mean that dilutes it away",
            "off_target_promiscuous": "TWO guides deplete but are flagged MULTI-TARGETING in the alignment "
                                      "summary — median cannot fix it; cross-reference the alignment and DROP "
                                      "the promiscuous guides",
        }[label]
        manifest.append(row)

    add(0, "clean", "none", COUNTS, g["clean"])
    de, _ = C.inj_guide_efficiency(COUNTS, CEG)
    add(1, "guide_efficiency", "tool-trap", de, g["guide_efficiency"],
        tell="real core-essential genes were given mostly DEAD guides (one live guide each); the naive "
             f"gene-MEAN recovers only {g['guide_efficiency']['naive_mean']}/{g['guide_efficiency']['n']} of "
             f"them, best-guide {g['guide_efficiency']['best_guide']}/{g['guide_efficiency']['n']}")
    dp, _ = C.inj_off_target_promiscuous(COUNTS, NEG)
    add(2, "off_target_promiscuous", "data-confound", dp, g["off_target_promiscuous"],
        tell="non-essential genes each have TWO guides that also map elsewhere (flagged in the alignment "
             f"summary) and deplete; robust MEDIAN still wrong ({g['off_target_promiscuous']['median_correct']}"
             f"/{g['off_target_promiscuous']['n']}); dropping the alignment-flagged guides recovers "
             f"{g['off_target_promiscuous']['drop_flagged_correct']}/{g['off_target_promiscuous']['n']}")
    json.dump(manifest, open(run / "manifest.json", "w"), indent=1)
    print(f"[scoring] {len(manifest)} worlds -> {run}/manifest.json")


# ================================================================ (2) calling
def build_calling():
    run = RES / "crispr_l2_calling_run"
    g = GOLD["calling"]
    task = ("Essential-gene calling: from the guide counts, call the set of genes essential in this screen; "
            "write the essential genes to a CSV (column: gene) and report its absolute path in output_path. "
            "Calibrate the call against the non-essential controls and verify replicate reproducibility.")
    manifest = []

    def add(cell, label, itype, counts, gold, tell=None, note=None, extra=None):
        d = cell_dir(run, cell)
        write_counts(d, counts)
        if extra:
            for fname, frame in extra.items():
                frame.to_csv(d / fname, sep="\t", index=False)
        layout_extra = {k: "prepared convenience artifact" for k in (extra or {})}
        json.dump(base_meta(task, layout_extra), open(d / "meta.json", "w"), indent=1)
        row = {"cell": cell, "task": "crispr_calling", "sub_task": "calling", "world_label": label,
               "issue_type": itype, "agent_input": str(d),
               "agent_output": str(run / f"out_cell{cell:03d}.json"),
               "gold": {**gold, "golden_csv": g["golden_csv"], "essential_thr": g["essential_thr"]}}
        if tell:
            row["confound_tell"] = tell
        if note:
            row["note"] = note
        row.update(_stamp(row["sub_task"]))                  # expected_method + verify_rubric from the spec
        row["correct_action"] = {
            "clean": "BF/precision-recall vs CEG/NEG; call essentials at a NEG-anchored FDR",
            "null_calibration": "calibrate essentiality against the NON-ESSENTIAL (NEG) null, not an all-gene "
                                "null whose variance is inflated by the essentials it contains",
            "replicate_irreproducible": "require replicate concordance; a depletion seen in ONE replicate "
                                        "only is not a real hit — do not call it from the pooled mean",
            "threshold_sensitivity": "the hit set swings with an arbitrary LFC cutoff; report a NEG-anchored "
                                     "FDR / confidence, not a single hard threshold",
        }[label]
        manifest.append(row)

    add(0, "clean", "none", COUNTS, g["clean"])
    z = C.prep_allgene_z(C.gene_scores(COUNTS, CEG, NEG))
    add(1, "null_calibration", "tool-trap", COUNTS, g["null_calibration"],
        extra={"gene_zscore_allgene.tsv": z},
        tell="a prepared per-gene z-score table computed against the ALL-GENE null rides along; a |z| cutoff "
             f"on it silently misses essentials (CEG recall {g['null_calibration']['ceg_recall_allgene_null']}"
             f" vs {g['null_calibration']['ceg_recall_neg_null']} with the NEG-anchored null)",
        note="prepared-artifact world: the raw counts are present so the robust NEG-anchored calling is possible")
    dr, _ = C.inj_replicate_irreproducible(COUNTS, NEG)
    add(2, "replicate_irreproducible", "tool-trap", dr, g["replicate_irreproducible"],
        tell="non-essential genes were made to deplete in rep1 ONLY; pooled MEAN wrongly calls "
             f"{g['replicate_irreproducible']['pooled_wrong']}/{g['replicate_irreproducible']['n']} essential, "
             f"rep-concordance {g['replicate_irreproducible']['repaware_wrong']}/{g['replicate_irreproducible']['n']}")
    add(3, "threshold_sensitivity", "statistical", COUNTS, g["threshold_sensitivity"],
        tell=f"the essential-set size swings {g['threshold_sensitivity']['swing_frac']*100:.0f}% across "
             f"LFC cutoffs [-0.5,-1.5] ({g['threshold_sensitivity']['n_at_cutoffs']}); a NEG-anchored FDR "
             "is the stable calibration",
        note="task-framed world: data identical to clean; graded on reporting a calibrated FDR/confidence "
             "rather than a single arbitrary cutoff")
    json.dump(manifest, open(run / "manifest.json", "w"), indent=1)
    print(f"[calling] {len(manifest)} worlds -> {run}/manifest.json")


# ================================================================ (3) context
def build_context():
    run = RES / "crispr_l2_context_run"
    g = GOLD["context"]
    task = ("Context-specific dependency: identify genes selectively essential in THIS line beyond the core-"
            "essential set (reproducible, real dependencies), excluding artifacts; write them to a CSV "
            "(column: gene) and report its absolute path in output_path. Do not promote artifacts, and do "
            "NOT discard a reproducible real dependency as an artifact to be corrected away.")
    manifest = []

    def add(cell, label, itype, counts, gold, tell=None, note=None):
        d = cell_dir(run, cell)
        write_counts(d, counts)
        json.dump(base_meta(task), open(d / "meta.json", "w"), indent=1)
        row = {"cell": cell, "task": "crispr_context", "sub_task": "context", "world_label": label,
               "issue_type": itype, "agent_input": str(d),
               "agent_output": str(run / f"out_cell{cell:03d}.json"),
               "gold": {**gold, "golden_csv": g["golden_csv"], "essential_thr": g["essential_thr"]}}
        if tell:
            row["confound_tell"] = tell
        if note:
            row["note"] = note
        row.update(_stamp(row["sub_task"]))                  # expected_method + verify_rubric from the spec
        row["correct_action"] = {
            "clean": "rank reproducible non-core essentials as context-specific dependencies",
            "artifact_context_hit": "a 'context-specific essential' driven by an off-target/one-replicate "
                                    "artifact must be DEMOTED (rep-concordance + robust aggregation), not "
                                    "reported as a real selective dependency",
            "over_correction_erases_real": "a reproducible non-core essential is a REAL context dependency — "
                                           "preserve it; do not filter it away as a presumed artifact",
        }[label]
        manifest.append(row)

    add(0, "clean", "none", COUNTS, g["clean"])
    da, _ = C.inj_context_artifact(COUNTS, NEG)
    add(1, "artifact_context_hit", "tool-trap", da, g["artifact_context_hit"],
        tell="non-essential genes given an off-target guide + a one-replicate spike masquerade as context-"
             f"specific essentials; naive promotes {g['artifact_context_hit']['naive_promotes']}/"
             f"{g['artifact_context_hit']['n']}, robust demotes {g['artifact_context_hit']['robust_demotes']}"
             f"/{g['artifact_context_hit']['n']}")
    add(2, "over_correction_erases_real", "statistical", COUNTS, g["over_correction_erases_real"],
        tell=f"{len(g['over_correction_erases_real']['real_context_genes'])} REAL reproducible non-core "
             "essentials must be PRESERVED; an over-aggressive artifact filter that erases them is the failure",
        note="task-framed world: data identical to clean; graded on preserving the real context dependencies")
    json.dump(manifest, open(run / "manifest.json", "w"), indent=1)
    print(f"[context] {len(manifest)} worlds -> {run}/manifest.json")


def main():
    RES.mkdir(exist_ok=True)
    build_scoring()
    build_calling()
    build_context()
    n_trap = 0
    for r in ("crispr_l2_scoring_run", "crispr_l2_calling_run", "crispr_l2_context_run"):
        n_trap += sum(1 for m in json.load(open(RES / r / "manifest.json")) if m["issue_type"] == "tool-trap")
    assert n_trap >= 1, "L2 must contain at least ONE tool trap"
    print(f"[world_builder] done — {n_trap} tool-trap worlds across the track")


if __name__ == "__main__":
    main()
