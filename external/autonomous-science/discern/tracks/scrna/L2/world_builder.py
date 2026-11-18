"""scRNA L2 (analysis-under-confound) WORLD builder — builds clean + confound worlds for the 3 sub-tasks by
injecting ONE analysis-level confound (as a delta) into the L1 CLEAN matrix (the chain: L1 clean world cell000 =
2,700 real pbmc3k cells). Each world is delivered in the SAME 10x .tar.gz format as L1 (matrix trio packed under
gene_bc_matrices/hg19/ + study_metadata.json alongside); the agent extracts it and runs scanpy itself.

Sub-tasks (TRACKS_PLAN Track 2 L2):
  annotation  : cluster -> cell-type annotation.  worlds: clean / batch_as_cluster / doublet_cluster / ambient_marker
  marker_de   : markers / DE between cell types.   worlds: clean / ambient_false_marker / pseudoreplication
  composition : composition / integration.         worlds: clean / doublet_as_type / batch_confound / over_integration

Each world's manifest cell carries the golden truth grade_scrna_l2.py reads (gold + sub_task) + the SHARED fields
verify_grades.py reads (issue_present / correct_action / affected_entities / expected_method / verify_rubric — the
last two stamped by stamp_methods.py from spec.py info["rubric"]). Reuses the L1 packaging (10x .tar.gz).

Reference (grading ground truth, NOT given to the agent): tracks/scrna/L2/ground_truth/ (built by build_ground_truth.py).
Run OUTSIDE the sandbox with the bench venv (scipy/numpy/pandas):  python tracks/scrna/L2/world_builder.py
"""
import os, sys, json, gzip, tarfile, tempfile, shutil, glob
import numpy as np
import pandas as pd
import scipy.io as sio
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
GT_DIR = os.path.join(HERE, "ground_truth")
CLEAN_WORLD = os.path.join(os.path.dirname(HERE), "L1/results/scrna_l1_run/data/cell000")  # L1 clean world (2700 real cells)
RESULTS = os.path.join(HERE, "results")

RUN_DIRS = {"annotation":  os.path.join(RESULTS, "scrna_l2_annotation_run"),
            "marker_de":   os.path.join(RESULTS, "scrna_l2_marker_de_run"),
            "composition": os.path.join(RESULTS, "scrna_l2_composition_run")}

BASE_META = {"species": "human", "genome": "hg19", "chemistry": "10x 3' v1", "assay": "scRNA-seq", "tissue": "PBMC"}
ARCHIVE = "gene_bc_matrices.tar.gz"           # same neutral 10x-style download name as L1 (no state tell)


# ------------------------------- load the L1 CLEAN matrix (genes x cells) + curated labels -------------------------------
def load_clean():
    tf = [f for f in os.listdir(CLEAN_WORLD) if f.endswith(".tar.gz")][0]
    tmp = tempfile.mkdtemp(prefix="scl2_")
    with tarfile.open(os.path.join(CLEAN_WORLD, tf)) as t:
        t.extractall(tmp)
    mfile = glob.glob(tmp + "/**/matrix.mtx.gz", recursive=True)[0]
    mdir = os.path.dirname(mfile)
    mat = sio.mmread(mfile).tocsc()                                     # genes x cells (10x MatrixMarket)
    feats = [ln.split("\t") for ln in gzip.open(os.path.join(mdir, "features.tsv.gz"), "rt").read().splitlines()]
    gn = [f[1] if len(f) > 1 else f[0] for f in feats]
    bc = gzip.open(os.path.join(mdir, "barcodes.tsv.gz"), "rt").read().splitlines()
    shutil.rmtree(tmp, ignore_errors=True)
    # curated per-cell labels (barcode -> cell_type), aligned by barcode to the matrix columns
    lab = pd.read_csv(os.path.join(GT_DIR, "cell_labels.csv"), index_col=0)
    ct = lab["cell_type"].to_dict()
    cell_types = np.array([ct.get(b, "?") for b in bc])
    return mat, gn, bc, feats, cell_types


def rows_for(symbols, gn):
    S = set(s.upper() for s in symbols)
    return [i for i, g in enumerate(gn) if g.upper() in S]


def set_suffix(bc, k):                                                  # 10x convention: barcode suffix encodes GEM well / batch
    return [f"{b.rsplit('-', 1)[0]}-{k}" for b in bc]


# ------------------------------- 10x packaging (mirrors tracks/scrna/world_builder.py _write_world) -------------------------------
def write_world(run_dir, cell, mat, gn, bc, feats, meta):
    d = os.path.join(run_dir, "data", f"cell{cell:03d}")
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d, exist_ok=True)
    stage = tempfile.mkdtemp(prefix="scw_"); inner = os.path.join(stage, "gene_bc_matrices", "hg19")
    os.makedirs(inner, exist_ok=True)
    with gzip.open(os.path.join(inner, "matrix.mtx.gz"), "wb") as f:
        sio.mmwrite(f, sp.csc_matrix(mat), field="integer")
    with gzip.open(os.path.join(inner, "barcodes.tsv.gz"), "wt") as f:
        f.write("\n".join(bc) + "\n")
    ids = [feats[i][0] if i < len(feats) else gn[i] for i in range(len(gn))]
    with gzip.open(os.path.join(inner, "features.tsv.gz"), "wt") as f:
        f.write("\n".join(f"{ids[i]}\t{gn[i]}\tGene Expression" for i in range(len(gn))) + "\n")
    with tarfile.open(os.path.join(d, ARCHIVE), "w:gz") as tf:
        tf.add(os.path.join(stage, "gene_bc_matrices"), arcname="gene_bc_matrices")
    shutil.rmtree(stage, ignore_errors=True)
    json.dump(meta, open(os.path.join(d, "study_metadata.json"), "w"), indent=1)
    return d


# ------------------------------- confound injections (deltas on the clean matrix) -------------------------------
def inj_batch_as_cluster(mat, gn, bc, ct, rng):
    """Inject a strong TECHNICAL batch effect that forms a SPURIOUS cluster: pick a cross-lineage subset (~28% of
    cells, spanning ALL cell types) as 'batch 2' and boost a fixed module of ~45 genes hard in them. The module is
    shared across lineages, so batch-2 cells split into their own leiden cluster driven by the batch signature (NOT
    biology). Correct handling = recognize it as a batch artifact (one batch, technical module, mixed lineages) and
    integrate/regress it out — do NOT invent a new cell type for it."""
    m = mat.tolil(); n = mat.shape[1]
    b2 = rng.choice(n, size=int(0.28 * n), replace=False)
    module = rng.choice(mat.shape[0], size=45, replace=False)           # arbitrary technical module (a batch signature)
    for c in b2:
        col = m[:, c].toarray().ravel().astype(int)
        col[module] = col[module] + rng.poisson(60, size=len(module))   # strong shared boost -> dominates the embedding
        m[:, c] = col.reshape(-1, 1)
    batch = np.ones(n, int); batch[b2] = 2
    bc2 = [f"{b.rsplit('-', 1)[0]}-{batch[i]}" for i, b in enumerate(bc)]
    return m.tocsc(), gn, bc2, dict(batch_frac2=float(len(b2) / n))


def _make_doublets(mat, gn, bc, ct, rng, n_doublets):
    """Synthesize a population of T-B DOUBLETS: each = the sum of a random T cell + a random B cell -> co-expresses
    the mutually-exclusive lineage markers CD3D/CD3E (T) AND MS4A1/CD79A (B). They form a cluster; correct handling =
    call them DOUBLETS (not a novel 'T-B' cell type)."""
    t_idx = np.where(np.isin(ct, ["CD4 T", "CD8 T"]))[0]
    b_idx = np.where(ct == "B")[0]
    a = rng.choice(t_idx, size=n_doublets); b = rng.choice(b_idx, size=n_doublets)
    dm = (mat[:, a] + mat[:, b]).tocsc()
    m = sp.hstack([mat, dm]).tocsc()
    bc2 = list(bc) + [f"DOUBLET{i:03d}-1" for i in range(n_doublets)]
    return m, bc2


def inj_doublet_cluster(mat, gn, bc, ct, rng):
    m, bc2 = _make_doublets(mat, gn, bc, ct, rng, n_doublets=70)
    return m, gn, bc2, dict(n_doublets=70)


def inj_ambient_marker(mat, gn, bc, ct, rng):
    """Ambient 'soup' spreads a LINEAGE marker across ALL cells: add a low-but-nonzero amount of the monocyte markers
    LYZ + S100A8 to every cell (uniform ambient background). Naive annotation may over-call monocyte identity on T/B/NK
    cells; correct handling = recognize the spread is ambient contamination (uniform, low, cross-lineage), not real."""
    m = mat.tolil(); rows = rows_for(["LYZ", "S100A8"], gn) or [0]; n = mat.shape[1]
    for r in rows:
        add = rng.poisson(9, size=n)                                    # uniform ambient bleed across every cell
        col = np.asarray(m[r, :].todense()).ravel().astype(int) + add
        m[r, :] = col.reshape(1, -1)
    return m.tocsc(), gn, list(bc), dict(ambient_genes=["LYZ", "S100A8"])


def inj_ambient_false_marker(mat, gn, bc, ct, rng):
    """Ambient HBB (hemoglobin — classic PBMC soup from lysed RBCs) added at a FIXED count to every cell. Because low-
    count cells (platelets) then carry a high HBB FRACTION (after per-cell normalization), HBB surfaces as a spurious TOP
    'marker' of the low-complexity platelet cluster in rank_genes_groups. Correct handling = recognize HBB as ambient/RBC
    contamination, not a real marker."""
    m = mat.tolil(); rows = rows_for(["HBB", "HBA1"], gn) or [0]; n = mat.shape[1]
    for r in rows:
        add = rng.poisson(15, size=n)                                  # strong uniform ambient bleed -> dominates low-count cells' fraction
        col = np.asarray(m[r, :].todense()).ravel().astype(int) + add
        m[r, :] = col.reshape(1, -1)
    return m.tocsc(), gn, list(bc), dict(ambient_gene="HBB")


def inj_pseudoreplication(mat, gn, bc, ct, rng):
    """Relabel into 6 donors x 2 conditions (donors 1-3 = ctrl, 4-6 = treat) with a RANDOM (biologically null) condition
    split, AND give each donor its own real expression signature (per-donor gene scaling) so donors genuinely vary. There
    is NO systematic condition effect, but a per-cell DE test treats cells as replicates -> the random donor variation
    aligned with the 3-vs-3 split gets called as hundreds of 'significant' condition genes (pseudoreplication inflation,
    Squair 2021); the correct pseudobulk-per-donor test (6 points) reports ~none. Correct handling = pseudobulk per donor."""
    n = mat.shape[1]; ngene = mat.shape[0]; donor = rng.integers(1, 7, size=n)   # 6 donors (suffix -1..-6)
    m = mat.tocsc().astype(float); blocks, idxs = [], []
    for dn in range(1, 7):
        cells = np.where(donor == dn)[0]; idxs.append(cells)
        scale = np.ones(ngene); sig = rng.choice(ngene, size=400, replace=False)
        scale[sig] = rng.uniform(0.3, 3.0, size=400)                   # donor-specific expression signature (real between-donor variance)
        blocks.append(sp.diags(scale) @ m[:, cells])
    allcols = sp.hstack(blocks).tocsc(); inv = np.argsort(np.concatenate(idxs))
    m2 = allcols[:, inv]; m2.data = np.round(m2.data)
    bc2 = [f"{b.rsplit('-', 1)[0]}-{donor[i]}" for i, b in enumerate(bc)]
    return m2.tocsc().astype(int), gn, bc2, dict(donors=6, cond_ctrl=[1, 2, 3], cond_treat=[4, 5, 6])


def _make_coherent_doublets(mat, ct, rng, n_doublets, pair=("CD4 T", "B")):
    """Synthesize a COHERENT doublet population that forms its OWN distinct leiden cluster (unlike the diffuse
    random-pair doublets of _make_doublets used for annotation). Each doublet is a Poisson draw from the SUMMED
    mean expression profile of the two lineages (CD4 T + B) -> every doublet shares the same intermediate profile,
    co-expressing the mutually-exclusive lineage markers CD3D/CD3E/IL7R (T) AND MS4A1/CD79A (B) at a consistent
    level (~2x UMI). Because the profile is coherent, ~all of them cluster together into a single tempting
    'transitional/double-positive-looking' cluster. Correct handling = recognize it as DOUBLETS (mutually-exclusive
    lineage co-expression), NOT a novel/transitional cell type; exclude it from the composition."""
    pa = np.asarray(mat[:, np.where(ct == pair[0])[0]].mean(1)).ravel()
    pb = np.asarray(mat[:, np.where(ct == pair[1])[0]].mean(1)).ravel()
    lam = pa + pb                                                   # summed lineage profile -> the doublet expectation
    dm = sp.csc_matrix(np.array([rng.poisson(lam) for _ in range(n_doublets)]).T)
    m = sp.hstack([mat, dm]).tocsc()
    return m


def inj_doublet_as_type(mat, gn, bc, ct, rng):
    n = 140
    m = _make_coherent_doublets(mat, ct, rng, n_doublets=n, pair=("CD4 T", "B"))
    bc2 = list(bc) + [f"DBLT{i:03d}-1" for i in range(n)]           # single run (suffix -1); no batch tell
    return m, gn, bc2, dict(n_doublets=n, doublet_pair=["CD4 T", "B"],
                            t_markers=["CD3D", "CD3E", "IL7R"], b_markers=["MS4A1", "CD79A"])


def inj_batch_confound(mat, gn, bc, ct, rng):
    """Two runs whose composition difference is PERFECTLY CONFOUNDED with a technical batch effect, WITHOUT any
    metadata signpost (see the world table: metadata is generic — no 'control/case', no 'two runs', no 'compare').
    The only latent hint is the barcode suffix -1 / -2. Batch-1 (suffix -1) is enriched for T cells, batch-2 (suffix
    -2) is enriched for monocytes, AND every batch-2 cell carries a technical module boost -> the graded composition
    shift (across MANY types) co-varies perfectly with the technical batch signature. Correct handling = DISCOVER the
    two-run structure from the suffix, then judge the composition difference is UNATTRIBUTABLE (batch is inseparable
    from the grouping); do NOT report the per-batch difference as a real biological result."""
    n = mat.shape[1]; is_mono = np.isin(ct, ["CD14 Mono", "FCGR3A Mono"]); is_t = np.isin(ct, ["CD4 T", "CD8 T"])
    p2 = np.full(n, 0.5)
    p2[is_mono] = 0.85                                                  # monocytes mostly land in batch 2
    p2[is_t] = 0.15                                                     # T cells mostly in batch 1
    batch = np.where(rng.random(n) < p2, 2, 1)
    m = mat.tolil(); module = rng.choice(mat.shape[0], size=40, replace=False)
    for c in np.where(batch == 2)[0]:                                   # a real technical batch-2 signature on top
        col = m[:, c].toarray().ravel().astype(int)
        col[module] = col[module] + rng.poisson(25, size=len(module)); m[:, c] = col.reshape(-1, 1)
    bc2 = [f"{b.rsplit('-', 1)[0]}-{batch[i]}" for i, b in enumerate(bc)]
    comp2 = {t: int(((batch == 2) & (ct == t)).sum()) for t in np.unique(ct)}
    comp1 = {t: int(((batch == 1) & (ct == t)).sum()) for t in np.unique(ct)}
    return m.tocsc(), gn, bc2, dict(n_batch1=int((batch == 1).sum()), n_batch2=int((batch == 2).sum()),
                                    batch1_composition=comp1, batch2_composition=comp2)


def inj_over_integration(mat, gn, bc, ct, rng):
    """HARDER over-integration trap (redesigned). Batch-2 carries a REAL, SHARP DEPLETION of B cells -- NOT a clean
    categorical absence. ~94% of B cells stay in batch-1; batch-2 keeps only a handful (~6% of B) -> a ~15x depletion
    that (a) looks like dropout/under-recovery an integration 'should' restore, and (b) contradicts the textbook prior
    that every PBMC sample has a normal B compartment. A small nonzero B count is far EASIER to dismiss as a technical
    artifact than a stark 0, so it resists the 'batch-2 has no B -> preserve it' shortcut that made the categorical
    version too easy. On TOP, batch-2 carries a STRONG technical batch signature (an 80-gene boosted module) so the two
    runs separate hard in PCA and the default 'integrate the batch away' pipeline (Harmony/scVI/BBKNN) is tempting --
    but integrating inflates the batch-2 B fraction back toward the batch-1 proportion, ERASING the real depletion.
    Metadata frames the two runs as replicates of the SAME sample. Correct handling = integrate for the technical
    effect but VERIFY via RAW marker counts that batch-2's B depletion is real, PRESERVE it, and flag it as a real
    (confounded) biological difference; do NOT report a restored ~normal B fraction in batch-2 (the fooled failure)."""
    n = mat.shape[1]; is_b = ct == "B"
    batch = np.ones(n, int)
    nonb = np.where(~is_b)[0]; to_b2 = rng.choice(nonb, size=len(nonb) // 2, replace=False)
    batch[to_b2] = 2                                                    # B cells all stay batch 1 -> batch 2 has no B
    m = mat.tolil(); module = rng.choice(mat.shape[0], size=50, replace=False)
    for c in np.where(batch == 2)[0]:                                   # STRONG technical module -> tempts integration
        col = m[:, c].toarray().ravel().astype(int)
        col[module] = col[module] + rng.poisson(35, size=len(module)); m[:, c] = col.reshape(-1, 1)
    bc2 = [f"{b.rsplit('-', 1)[0]}-{batch[i]}" for i, b in enumerate(bc)]
    return m.tocsc(), gn, bc2, dict(missing_type="B", n_b_batch1=int(is_b.sum()), n_b_batch2=0,
                                    n_batch1=int((batch == 1).sum()), n_batch2=int((batch == 2).sum()))


# ------------------------------- world tables (issue -> injector + gold + study_metadata design) -------------------------------
def _load_gt():
    gt = json.load(open(os.path.join(GT_DIR, "ground_truth.json")))
    return gt


def build_all(only_subs=None):
    mat0, gn, bc0, feats, ct = load_clean()
    gt = _load_gt()
    TRUE_TYPES = sorted(gt["cell_type_composition"].keys())            # the 8 real PBMC types
    CANON = gt["canonical_markers"]
    COMP = gt["cell_type_composition"]

    # (world_label, injector_or_None, gold_extra, meta_design) per sub-task. injector None = CLEAN (identity).
    ANNOTATION = [
        ("clean", None, {"confound": None}, {}),
        ("batch_as_cluster", inj_batch_as_cluster,
         {"confound": {"kind": "batch", "note": "a technical batch (suffix -2) with a boosted gene module forms a spurious cross-lineage cluster"}},
         {"design": "two 10x runs merged; the barcode suffix (-1 / -2) encodes the sequencing batch (GEM well)",
          "note": "cells from both batches; expect technical batch structure."}),
        ("doublet_cluster", inj_doublet_cluster,
         {"confound": {"kind": "doublet", "markers": ["CD3D", "CD3E", "MS4A1", "CD79A"],
                       "note": "a cluster of T-B doublets co-expressing mutually-exclusive lineage markers"}},
         {"note": "standard single 10x run; annotate the clusters."}),
        ("ambient_marker", inj_ambient_marker,
         {"confound": {"kind": "ambient", "gene": "LYZ",
                       "note": "monocyte markers LYZ/S100A8 spread across all cells as ambient soup"}},
         {"note": "standard single 10x run; annotate the clusters."}),
    ]
    MARKER_DE = [
        ("clean", None, {"confound": None}, {}),
        ("ambient_false_marker", inj_ambient_false_marker,
         {"confound": {"kind": "ambient", "gene": "HBB",
                       "note": "ambient HBB (RBC soup) surfaces as a spurious top marker of the low-count cluster"}},
         {"note": "standard single 10x run; find per-cell-type markers."}),
        ("pseudoreplication", inj_pseudoreplication,
         {"confound": {"kind": "pseudoreplication", "design": "6 donors x 2 conditions (random/null split)",
                       "true_de": "~none (the condition split is biologically null); cells-as-replicates inflates DE"}},
         {"design": "6 donors across 2 conditions; the barcode suffix (-1..-6) encodes the DONOR. "
                    "Donors 1-3 = control, donors 4-6 = treated.",
          "note": "perform the condition differential-expression comparison appropriately for this design."}),
    ]
    COMPOSITION = [
        ("clean", None, {"confound": None, "true_composition": COMP}, {}),
        # doublet_as_type: a COHERENT ~140-cell doublet cluster that superficially looks like a novel/transitional type.
        # No signpost — generic single-run metadata; the model must recognize it as doublets, not annotate it as a type.
        ("doublet_as_type", inj_doublet_as_type,
         {"confound": {"kind": "doublet", "markers": ["CD3D", "CD3E", "IL7R", "MS4A1", "CD79A"],
                       "note": "a coherent ~140-cell doublet cluster (CD4 T + B) co-expresses mutually-exclusive lineage "
                               "markers and superficially looks like a novel/transitional cell type; it is NOT a real type"}},
         {"note": "PBMC 10x dataset; report the cell-type composition."}),
        # batch_confound: NO signpost. Metadata is generic; the two runs (suffix -1/-2) and their confounded composition
        # difference must be DISCOVERED. Correct = flag the difference is unattributable (batch inseparable from grouping).
        ("batch_confound", inj_batch_confound,
         {"confound": {"kind": "batch", "note": "two runs (barcode suffix -1/-2, not announced) differ in composition, "
                       "but the difference is perfectly confounded with a technical batch effect -> unattributable to biology"}},
         {"note": "PBMC 10x dataset; report the cell-type composition."}),
        # over_integration: metadata frames the two runs as replicates of the SAME sample (tempts batch-correction); the
        # B-cell absence in batch-2 is NOT announced. Correct = preserve the real batch-2 B-cell absence, don't integrate it away.
        ("over_integration", inj_over_integration,
         {"confound": {"kind": "over_integration", "missing_type": "B",
                       "note": "batch-2 genuinely lacks B cells (a real, categorical population absence) but a strong "
                               "technical module makes it look like a correctable batch effect an over-integration would erase"}},
         {"design": "two sequencing runs (barcode suffix -1 / -2) of the same PBMC sample; correct any batch effects between the runs.",
          "note": "report the cell-type composition (per run where relevant)."}),
    ]

    # resolution_trap: a COMPOSITION world that is a TOOL TRAP (added as the composition sub-task's 2nd tool trap,
    # alongside over_integration). Clean data, but at the DEFAULT/low Leiden resolution two genuinely-close populations
    # MERGE (CD14 vs FCGR3A monocytes; CD8 T vs NK); the agent must VERIFY the clustering OUTPUT against markers and
    # tune resolution to recover all 8. Appended LAST so cells 0-3 keep their indices (existing outputs stay valid).
    COMPOSITION = COMPOSITION + [
        ("resolution_trap", None,
         {"confound": {"kind": "resolution",
                       "note": "TOOL TRAP: default/low clustering resolution merges CD14/FCGR3A monocytes and CD8 T/NK; "
                               "the agent must verify the clustering output against markers and tune resolution to "
                               "recover all 8 canonical types (do not accept the under-clustered default)"},
          "true_composition": COMP},
         {"note": "PBMC 10x dataset; cluster, annotate, and report the cell-type composition."}),
    ]
    INJ = {"annotation": ANNOTATION, "marker_de": MARKER_DE, "composition": COMPOSITION}
    RUBRIC_TASK = {"annotation": "scrna_annotation", "marker_de": "scrna_marker_de", "composition": "scrna_composition"}

    for sub, worlds in INJ.items():
        if only_subs and sub not in only_subs:
            continue
        run_dir = RUN_DIRS[sub]; os.makedirs(os.path.join(run_dir, "data"), exist_ok=True)
        manifest = []
        for cell, (wl, inj, gold_extra, design) in enumerate(worlds):
            rng = np.random.default_rng(1000 * cell + 17)
            if inj is None:
                mat, gnw, bcw, extra = mat0.copy(), list(gn), list(bc0), {}
            else:
                mat, gnw, bcw, extra = inj(mat0.copy(), list(gn), list(bc0), ct, rng)
            meta = dict(BASE_META, **design)
            d = write_world(run_dir, cell, mat, gnw, bcw, feats, meta)
            gold = {"true_types": TRUE_TYPES, "canonical_markers": CANON, **gold_extra}
            if extra and gold.get("confound"):                        # fold injector-reported stats into the confound record
                gold["confound"].update(extra)
            manifest.append({
                "cell": cell, "world_label": wl, "sub_task": sub, "task": RUBRIC_TASK[sub],
                "agent_input": d, "agent_metadata": os.path.join(d, "study_metadata.json"),
                "agent_output": os.path.join(run_dir, f"out_cell{cell:03d}.json"),
                "issue_present": wl != "clean", "requires_external_evidence": False,
                "gold": gold, "issue_type": ("none" if wl == "clean" else wl),
                "correct_action": _correct_action(sub, wl, gold),
                "affected_entities": _affected(sub, gold),
                "trait_context": f"single-cell {sub} of a PBMC 10x dataset"})
        json.dump(manifest, open(os.path.join(run_dir, "manifest.json"), "w"), indent=1)
        print(f"{sub}: {len(manifest)} worlds -> {run_dir}  ({[w['world_label'] for w in manifest]})")


def _correct_action(sub, wl, gold):
    conf = gold.get("confound")
    if not conf:
        base = {"annotation": "Cluster and annotate every cluster to one of the 8 canonical PBMC cell types using marker genes.",
                "marker_de": "Report the canonical marker genes per cell type; where the design supports a DE comparison, do it correctly.",
                "composition": "Report the cell-type composition (all 8 real types) matching the reference counts."}
        return base[sub]
    k = conf["kind"]
    if k == "doublet":
        return ("Recognize the co-expressing-exclusive-markers cluster as DOUBLETS (not a novel cell type); flag/remove "
                "it and annotate the 8 real types." if sub == "annotation" else
                "Do NOT count the doublet population as a cell type; flag/exclude it and report the 8 real types.")
    if k == "batch":
        return ("Recognize the batch-2 cluster as a technical batch artifact (integrate/regress it out), not a new cell type."
                if sub == "annotation" else
                "Discover the two runs from the barcode suffix (-1/-2); their composition difference is perfectly confounded "
                "with a technical batch effect, so it is NOT attributable to biology — flag it as unattributable/uninterpretable "
                "(do NOT report the per-run composition difference as a real biological result).")
    if k == "ambient":
        g = conf.get("gene", "the ambient gene")
        return (f"Recognize the spread of {g} as ambient contamination (uniform, cross-lineage); do not mis-annotate on it."
                if sub == "annotation" else
                f"Recognize {g} as an ambient/soup contaminant, not a real cell-type marker; exclude/flag it.")
    if k == "over_integration":
        return (f"Recognize that the batch-2 sharp DEPLETION of {conf.get('missing_type','a population')} cells is REAL "
                "biology (a small nonzero count, NOT technical dropout to be corrected — despite the same-sample framing and "
                "the strong batch signature); VERIFY it against raw marker counts and PRESERVE it. Integrate for the technical "
                "effect if needed, but do NOT over-integrate and restore the depleted population back toward the batch-1 proportion.")
    if k == "pseudoreplication":
        return ("Aggregate to PSEUDOBULK per donor before the condition DE contrast; do not treat cells as replicates "
                "(that inflates DE — the condition split is biologically null).")
    return "Handle the confound correctly."


def _affected(sub, gold):
    conf = gold.get("confound")
    if not conf:
        return []
    k = conf["kind"]
    return {"doublet": ["the T-B doublet population"], "batch": ["batch-2 barcodes (suffix -2)"],
            "ambient": [f"ambient gene {conf.get('gene','')}"], "over_integration": ["batch-2 (suffix -2)"],
            "pseudoreplication": ["all cells (donor/condition relabeling)"]}.get(k, [])


if __name__ == "__main__":
    subs = sys.argv[1].split(",") if len(sys.argv) > 1 else None    # optional: rebuild only these sub-tasks
    build_all(only_subs=subs)
