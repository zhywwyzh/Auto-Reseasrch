"""Single source of truth: which grader scores which L2 family (and L1) of which track.

    python -c "import graders; print(graders.grader_for('scrna', 'annotation'))"

Three shell drivers (queue_model_tracks.sh, resume_model_track_then_queue.sh, rerun_cells_after_chain.sh)
used to each carry a private bash `case` map; the queue's copy lacked an scrna arm and died on an unbound
variable after scrna's L1 grade (2026-09-04), silently dropping five tracks. One map, one place.
Adding a track = one line here (plus its spec.py). Adding a MODEL needs no edit anywhere in this file.
"""
import sys

L1_GRADER = "grade_generic.py"

L2_GRADER = {
    "cf_gwas":           {"signaleda": "tracks/cf_gwas/L2/grade_gwas_signaleda.py",
                          "locus":     "tracks/cf_gwas/L2/grade_gwas_task2.py",
                          "twas":      "tracks/cf_gwas/L2/grade_gwas_twas.py"},
    "clinvar_acmg":      {"*": "tracks/clinvar_acmg/L2/grade_clinvar_l2.py"},
    "scrna":             {"*": "tracks/scrna/L2/grade_scrna_l2.py"},
    "bulk_rnaseq":       {"*": "tracks/bulk_rnaseq/L2/grade_bulk_l2.py"},
    "hist_gene_exp":     {"*": "tracks/hist_gene_exp/L2/grade_hist_l2.py"},
    "crispr_screen":     {"*": "tracks/crispr_screen/L2/grade_crispr_l2.py"},
    "enhancer_activity": {"*": "tracks/enhancer_activity/L2/grade_enhancer_l2.py"},
    "protein_ddg":       {"ddg_predict":    "tracks/protein_ddg/L2/grade_ddg_predict.py",
                          "stab_classify":  "tracks/protein_ddg/L2/grade_stab_classify.py",
                          "feature_effect": "tracks/protein_ddg/L2/grade_feature.py"},
}


def grader_for(track, family):
    """Repo-relative grader path for (track, family); family 'L1' -> the generic L1 grader.
    Raises KeyError with a clear message instead of returning nothing (the bash failure mode)."""
    if family == "L1":
        return L1_GRADER
    fams = L2_GRADER.get(track)
    if fams is None:
        raise KeyError(f"graders.py: no L2 grader map for track {track!r} -- add it to L2_GRADER")
    g = fams.get(family) or fams.get("*")
    if not g:
        raise KeyError(f"graders.py: no grader for {track}/{family} -- add it to L2_GRADER")
    return g


if __name__ == "__main__":
    print(grader_for(sys.argv[1], sys.argv[2]))


def graded_prefix(run_dir, model):
    """The `graded_*` filename PREFIX that this family's grader actually wrote, for verify_grades.py.

    Graders do not all name their output after the family: protein_ddg/feature_effect writes
    `graded_feature_*` and cf_gwas/locus writes `graded_task2_*`. The three shell drivers each guessed
    `graded` then `graded_<family>`, so verify SILENTLY FAILED (FileNotFoundError) on those two families
    -- protein_ddg/feature_effect for glm-5.3 was graded but never cross-checked (found 2026-09-06).
    Discover the prefix from what is on disk instead of guessing; raise if nothing matches.
    """
    import glob, os
    hits = glob.glob(os.path.join(run_dir, f"graded_*_{model}.json")) + \
           glob.glob(os.path.join(run_dir, f"graded_{model}.json"))
    if not hits:
        raise KeyError(f"graders.py: no graded file for model {model!r} in {run_dir} -- grade before verify")
    # longest prefix wins: `graded_stab_classify_<m>.json` before a bare `graded_<m>.json`
    return sorted((os.path.basename(h)[:-len(f"_{model}.json")] if h.endswith(f"_{model}.json") else "graded")
                  for h in hits)[-1]
