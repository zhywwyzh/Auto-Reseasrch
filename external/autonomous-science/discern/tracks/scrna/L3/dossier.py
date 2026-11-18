"""scRNA L3 dossier builder — the OUT-OF-CONTEXT-MARKER flip (see L3_DESIGN.md / TRACKS_PLAN Track 2).

Chains off the clean L2 result: hands the agent the L2 cell-type map + a per-cluster marker-mean table (which the
agent can also inspect as the `markers` dataframe in the sandbox) and asks it to INTERPRET a focus population — what
cell type it is and what an out-of-context marker implies. The counterfactual surfaces a MYELOID (monocyte) cluster
whose CD4 mRNA is genuinely HIGHER than the CD4 T cluster's — because CD4 mRNA really is higher in monocytes than in
T cells (sc2marker, Kohl et al. 2022; verified in THIS pbmc3k substrate: mono~0.43 vs CD4 T~0.17). So the flip is
EMPIRICALLY TRUE at the RNA level, not injected — a sandbox check AGREES with the dossier; only the memorized prior
("CD4 = the T-helper marker") disagrees. Trusting the data => the population is monocytic and its CD4 is real myeloid
biology (NOT T cells, NOT a T-cell doublet/contaminant); trusting the prior => relabel it CD4 T / dismiss the CD4.

This is NOT a bare relabel: the agent must explain what the population represents and what the out-of-context marker
implies, defended vs reviewers invoking "CD4 is the textbook T-helper marker". (CD8A->B was DROPPED — biologically
false, un-flippable.)

usage: dossier.py [out_dir]     (default: tracks/scrna/L3/results/l3_run)
"""
import json, os, sys, csv, glob, tarfile, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GT = json.load(open(os.path.join(ROOT, "tracks/scrna/L2/ground_truth/ground_truth.json")))
CLEAN = os.path.join(ROOT, "tracks/scrna/L2/results/scrna_l2_composition_run/data/cell000")  # L2-clean world (= L1 clean)

# marker panel spanning all lineages + the flip marker CD68 (higher in non-classical than classical monocytes here)
PANEL = ["CD14", "LYZ", "FCN1", "S100A8", "CD68",          # myeloid (+ CD68 = the flip marker)
         "CD3D", "CD3E", "IL7R", "CCR7", "CD4",            # CD4 T
         "CD8A", "CD8B",                                    # CD8 T
         "MS4A1", "CD79A",                                  # B
         "NKG7", "GNLY",                                    # NK
         "FCGR3A", "MS4A7",                                 # FCGR3A mono
         "FCER1A", "CST3",                                  # DC
         "PPBP", "PF4"]                                     # platelet


def marker_means_by_type():
    """Per-cell-type mean log-norm expression for PANEL, computed from the real clean matrix (internal consistency)."""
    import scanpy as sc, numpy as np, pandas as pd
    tgz = glob.glob(os.path.join(CLEAN, "*.tar.gz"))
    tmp = tempfile.mkdtemp()
    if tgz:
        tarfile.open(tgz[0]).extractall(tmp)
        base = os.path.dirname(glob.glob(os.path.join(tmp, "**", "matrix.mtx*"), recursive=True)[0])
    else:
        base = os.path.dirname(glob.glob(os.path.join(CLEAN, "**", "matrix.mtx*"), recursive=True)[0])
    a = sc.read_10x_mtx(base, var_names="gene_symbols", cache=False); a.var_names_make_unique()
    sc.pp.normalize_total(a, target_sum=1e4); sc.pp.log1p(a)
    lab = pd.read_csv(os.path.join(ROOT, "tracks/scrna/L2/ground_truth/cell_labels.csv"))
    y = lab["cell_type"].values[:a.n_obs]; a = a[:len(y)]
    out = {}
    for g in PANEL:
        if g in a.var_names:
            col = np.asarray(a[:, g].X.todense()).ravel()
            out[g] = pd.DataFrame({"t": y, "e": col}).groupby("t")["e"].mean().round(3).to_dict()
    types = sorted({t for g in out for t in out[g]})
    return {t: {g: out[g].get(t, 0.0) for g in PANEL if g in out} for t in types}


def build(out):
    data = os.path.join(out, "data"); os.makedirs(data, exist_ok=True)
    by_type = marker_means_by_type()                      # {cell_type: {gene: mean}}
    cd4 = {t: by_type[t].get("CD4", 0.0) for t in by_type}
    print("[dossier] CD4 mRNA by cell type:", " ".join(f"{t}={v}" for t, v in sorted(cd4.items(), key=lambda x: -x[1])))
    CANON = GT["canonical_markers"]                        # textbook marker->type reference (NOT the computed means)
    manifest = []

    # DE-LEADED design: the focus cluster is presented UNLABELED (marker profile only, neutral id). The agent must
    # (a) annotate it itself and (b) NOTICE any surprising marker on its own — CD4 is NOT pointed at, and the query's
    # own true cell type is excluded from the reference so it cannot string-match a label. Reference = canonical
    # marker DEFINITIONS + the OTHER cell types' real means (context), never the query's type.
    def emit(world, cond, query_type, flipped_gene, dsd, ted, trait):
        qid = "cluster_Q"
        query_profile = {g: by_type[query_type][g] for g in by_type[query_type]}
        ref_types = [t for t in by_type if t != query_type]                       # exclude the query's own type
        ref_rows = [{"cell_type": t, **by_type[t]} for t in ref_types]
        query_row = {"cell_type": qid, **query_profile}
        doss = {
            "task_note": ("Clean L2 result for a 10x PBMC dataset: one unannotated cluster (cluster_Q) is given as its "
                          "mean log-norm expression across a marker panel, alongside canonical marker definitions and "
                          "the already-annotated cell types' mean-expression profiles (all loadable as the `markers` "
                          "dataframe in the sandbox). The task is to INTERPRET cluster_Q: annotate it to a canonical "
                          "PBMC cell type from its marker profile, and determine whether the RNA-level data support "
                          "any novel observation or hypothesis about it."),
            "canonical_markers": CANON,
            "annotated_cell_type_profiles": {t: by_type[t] for t in ref_types},
            "unannotated_cluster": {"cluster_id": qid, "marker_means": query_profile},
        }
        dj = os.path.join(data, f"dossier_{world}.json"); json.dump(doss, open(dj, "w"), indent=1)
        cj = os.path.join(data, f"markers_{world}.csv")
        rows = ref_rows + [query_row]
        with open(cj, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        manifest.append({"track": "scrna", "world": world, "condition": cond,
                         "dossier": dj, "twas_csv": cj, "agent_output": os.path.join(out, f"out_{world}.json"),
                         "flipped_gene": flipped_gene, "data_supported_direction": dsd,
                         "textbook_expectation_direction": ted, "trait": trait})

    # ---- W0: REAL control — cluster_Q is a genuine CD4 T cluster (CD3D/IL7R high, CD4 low/consistent). Correct
    # annotation = CD4 T; nothing surprising. Tests OVER-DIAGNOSIS: the agent must NOT invent a fake anomaly. ----
    emit("real", "real", "CD4 T", "CD3D", trait="PBMC cluster annotation (control)",
         dsd=("Real world: cluster_Q is CD4 T cells — high CD3D/CD3E/IL7R, and CD4 mRNA is LOW (~0.17) and consistent "
              "with a lymphoid profile. Nothing about the profile is anomalous; the correct answer is CD4 T cells with "
              "no manufactured surprise. Flagging a fake anomaly here is over-diagnosis."),
         ted=("Textbook: CD3D/IL7R-high lymphocytes are T cells; cluster_Q is an unremarkable CD4 T cluster "
              "consistent with expectation."))

    # ---- cf_cd68_mono: cluster_Q is the non-classical (FCGR3A/CD16+) monocyte cluster (unlabeled). CD68 — textbook a
    # classical-monocyte/macrophage marker — is actually HIGHER here than in classical CD14+ monocytes. The agent must
    # annotate it non-classical monocyte AND notice + explain that its CD68 exceeds the classical-monocyte reference. ----
    cd68 = {t: by_type[t].get("CD68", 0.0) for t in by_type}
    emit("cf_cd68_mono", "counterfactual", "FCGR3A Mono", "CD68",
         trait="PBMC cluster annotation (CD68-high non-classical monocyte)",
         dsd=(f"cluster_Q is a NON-CLASSICAL (CD16+/FCGR3A+) monocyte: FCGR3A/MS4A7/LST1 mark it, with lower CD14 than "
              f"classical monocytes. Its CD68 mRNA (~{cd68.get('FCGR3A Mono')}) is HIGHER than the CLASSICAL CD14+ "
              f"monocyte reference (~{cd68.get('CD14 Mono')}) — contradicting the textbook that CD68 is a classical-"
              f"monocyte/macrophage marker. The surprising marker the agent should notice is CD68. Correct reading: "
              f"cluster_Q is a non-classical monocyte and its elevated CD68 is REAL (non-classical monocytes are the "
              f"more macrophage-like subset), NOT evidence it is the classical/macrophage population."),
         ted=("Textbook: CD68 is the canonical classical-monocyte / macrophage marker, so higher CD68 reads as the "
              "classical CD14+ monocyte (or macrophage) population, not the non-classical subset."))

    # ---- cf_cd16_mono: SAME non-classical monocyte cluster_Q, but the flip is CD16/FCGR3A — a textbook NK marker that
    # is actually high on non-classical monocytes. The agent must recognize cluster_Q is a MONOCYTE (LYZ/CST3/S100A8+,
    # no GNLY/NKG7 cytotoxic markers), NOT reflexively call it NK from the high CD16. (Same cluster as cf_cd68, graded
    # against the CD16 prior instead of the CD68 prior; the agent-facing dossier is identical, the flip target differs.) ----
    cd16 = {t: by_type[t].get("FCGR3A", 0.0) for t in by_type}   # CD16 = FCGR3A gene
    emit("cf_cd16_mono", "counterfactual", "FCGR3A Mono", "CD16",
         trait="PBMC cluster annotation (CD16-high, reflexively NK)",
         dsd=(f"cluster_Q is a NON-CLASSICAL monocyte: LYZ/CST3/S100A8 and MS4A7/LST1 mark it as myeloid, with NO "
              f"cytotoxic lymphocyte markers (GNLY/NKG7 low). Its CD16 (FCGR3A) is high (~{cd16.get('FCGR3A Mono')}, "
              f"comparable to / above NK ~{cd16.get('NK')}) — CD16 is textbook an NK marker, so the reflex is to call "
              f"cluster_Q an NK cell. Correct reading: cluster_Q is a NON-CLASSICAL MONOCYTE and its CD16 is REAL "
              f"myeloid biology (non-classical monocytes are CD16+), NOT evidence it is an NK cell."),
         ted=("Textbook: CD16 (FCGR3A) is a classic NK-cell marker, so a CD16-high cluster reads as NK cells."))

    mf = os.path.join(out, "manifest.json"); json.dump(manifest, open(mf, "w"), indent=1)
    print(f"[dossier] wrote {len(manifest)} worlds -> {mf} (DE-LEADED: cluster_Q unlabeled, no CD4 pointer)")
    for m in manifest:
        q = json.load(open(m["dossier"]))["unannotated_cluster"]["marker_means"]
        print(f"  {m['world']:<12} {m['condition']:<14} cluster_Q CD14={q.get('CD14')} LYZ={q.get('LYZ')} CD4={q.get('CD4')} CD3D={q.get('CD3D')}  flipped_gene={m['flipped_gene']}")
    return mf


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results/l3_run")
    os.makedirs(out, exist_ok=True)
    build(out)
