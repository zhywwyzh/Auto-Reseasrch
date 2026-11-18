"""scrna L1 world-builder — inject ONE known QC defect per world into the clean 10x matrix + write manifest GT.

Each issue -> `variants_per_issue` worlds (different-seed injections). Emits, per world, a 10x matrix directory
(the agent's `matrix_dir`) + a per-world study_metadata.json, and appends a manifest cell carrying the ground truth
the SHARED grade_generic reads: issue_type / issue_present / canonical_checks / diagnose_keywords / action_keywords
/ correct_action / affected_entities (+ requires_external_evidence for the abstain control). See grade_generic.py.

Run build_substrate.py first (writes tracks/scrna/data/clean/). Then:  world_builder.py [n_variants=3]
"""
import os, sys, json, gzip, tarfile, tempfile, shutil
import numpy as np
import scipy.io as sio
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data"); CLEAN = os.path.join(DATA, "clean")
RUN_DIR = os.path.join(HERE, "L1/results/scrna_l1_run")

# ---------------- GROUND TRUTH per issue = the grading contract (what a competent QC must CHECK / DIAGNOSE / DO) ----
# canonical_checks = the QC computation that reveals it; diagnose_keywords = naming the defect; action_keywords = the
# proportionate remedy. correct_action = short human-readable remedy. All keyword-graded by grade_generic (0-3).
GT = {
 "clean": dict(present=False, canonical_checks=["knee", "mitochond", "n_genes", "total count"],
   diagnose_keywords=[], action_keywords=[], correct_action="No defect — proceed to standard QC; do not invent a problem.",
   affected=[]),
 "empty_droplets": dict(present=True,
   canonical_checks=["barcode-rank", "knee", "umi", "total count", "n_genes per cell"],
   diagnose_keywords=["empty droplet", "empty droplets", "ambient-only barcode", "below the knee", "not real cells"],
   action_keywords=["filter", "threshold", "remove", "knee cutoff", "min counts", "cellranger --expect-cells"],
   correct_action="Set an empty-droplet cutoff (knee / EmptyDrops) and drop barcodes below it.",
   affected=["low-count barcodes below the knee"]),
 "high_mito": dict(present=True,
   canonical_checks=["percent mito", "%mt", "MT-", "mitochondrial fraction"],
   diagnose_keywords=["high mitochond", "dying", "apoptotic", "stressed cells", "high %mt"],
   action_keywords=["filter", "threshold", "pct_counts_mt", "remove high-mito", "mito cutoff"],
   correct_action="Flag high-%mito barcodes (dying cells) and filter above a mito threshold.",
   affected=["barcodes with elevated mitochondrial fraction"]),
 "high_hemoglobin": dict(present=True,
   canonical_checks=["percent hemoglobin", "HBB", "HBA", "%hb", "hemoglobin genes"],
   diagnose_keywords=["hemoglobin", "erythrocyte", "red blood cell", "RBC contamination", "rbc lysis"],
   action_keywords=["filter", "remove", "hemoglobin fraction", "exclude RBC", "hb cutoff"],
   correct_action="Flag high-hemoglobin barcodes (RBC/erythrocyte contamination) and filter them.",
   affected=["barcodes with high hemoglobin-gene fraction"]),
 "doublets": dict(present=True,
   canonical_checks=["total counts", "n_genes", "co-expression", "marker co-expression", "high UMI"],
   diagnose_keywords=["doublet", "multiplet", "two cells", "co-express exclusive", "CD3E and CD14"],
   action_keywords=["remove", "filter", "scrublet", "doubletfinder", "flag doublets"],
   correct_action="Flag suspected doublets (high UMI + exclusive-marker co-expression) and remove them.",
   affected=["high-UMI barcodes co-expressing mutually-exclusive lineage markers"]),
 "ambient_rna": dict(present=True,
   canonical_checks=["ambient", "soup", "empty-droplet profile", "background expression"],
   diagnose_keywords=["ambient rna", "soup", "contamination", "background", "cell-free rna"],
   action_keywords=["soupx", "cellbender", "decontaminate", "correct ambient", "remove background"],
   correct_action="Estimate the ambient profile from empty droplets and decontaminate (SoupX/CellBender).",
   affected=["all barcodes (shared ambient background)"]),
 "feature_type_contamination": dict(present=True,
   canonical_checks=["feature_type", "features.tsv", "Antibody Capture", "modality", "feature classes"],
   diagnose_keywords=["antibody capture", "hashtag", "HTO", "CRISPR", "non-GEX features", "multimodal rows"],
   action_keywords=["split", "subset to Gene Expression", "separate modality", "remove non-GEX rows"],
   correct_action="Split the feature matrix by feature_type; keep only Gene Expression rows for GEX analysis.",
   affected=["feature rows whose feature_type is not Gene Expression"]),
 "count_complexity": dict(present=True,
   canonical_checks=["total counts distribution", "n_genes", "counts per gene", "library complexity", "outlier"],
   diagnose_keywords=["count outlier", "complexity", "intronic inflation", "count-mode", "abnormal library size"],
   action_keywords=["filter outliers", "MAD threshold", "min/max counts", "exclude complexity outliers"],
   correct_action="Flag total-count / complexity outliers (MAD-based) and filter them before normalization.",
   affected=["barcodes with outlier total-count / n_genes"]),
 "metadata_reconciliation": dict(present=True,
   canonical_checks=["study_metadata", "gene naming", "species", "chemistry", "feature count vs stated"],
   diagnose_keywords=["metadata mismatch", "species mismatch", "chemistry mismatch", "stated vs data",
                      "labeled human but", "expected cells"],
   action_keywords=["reconcile", "correct metadata", "verify species", "flag mismatch", "do not trust label"],
   correct_action="Reconcile stated metadata (species/chemistry/expected_cells) with the data; flag the mismatch.",
   affected=["study_metadata fields inconsistent with the matrix"]),
 "abstain_low_rna": dict(present=False, requires_external_evidence=True,
   abstention_question=("A subpopulation of barcodes has genuinely LOW RNA content (few genes / low UMIs) but is a "
                        "REAL cell type (platelets / neutrophils), not empty droplets or low-quality cells. Should "
                        "the analyst DISCARD them as a QC defect, or RETAIN them? The correct answer is RETAIN "
                        "(do not over-filter on n_genes)."),
   canonical_checks=["n_genes", "total counts", "known low-RNA cell types", "platelet/neutrophil markers"],
   diagnose_keywords=["real cell type", "platelet", "neutrophil", "genuinely low-RNA", "do not over-filter"],
   action_keywords=["retain", "keep", "do not filter", "lower n_genes threshold", "abstain"],
   correct_action="Do NOT discard the low-RNA population — platelets/neutrophils are real; adjust the n_genes floor.",
   affected=["a genuine low-RNA cell population (platelets/neutrophils)"]),
}

# ---- injection functions: (mat[genes x cells] csc, gene_names, barcodes, meta, rng) -> mutated copies ----
HB_GENES = ("HBB", "HBA1", "HBA2", "HBD", "HBG1", "HBG2")
def _mt_rows(gn): return [i for i, g in enumerate(gn) if g.upper().startswith("MT-")]
def _hb_rows(gn): return [i for i, g in enumerate(gn) if g.upper() in HB_GENES]

def inj_clean(mat, gn, bc, meta, rng): return mat, gn, bc, meta
def inj_high_mito(mat, gn, bc, meta, rng):
    """Apoptotic/dying signature done the BIOPHYSICALLY CORRECT way: MT% rises because the CYTOPLASM is lost, NOT
    because mitochondrial transcripts are amplified. So we binomially thin ONLY the non-MT genes (varied survival
    fraction -> a CONTINUUM of MT%) and leave every MT count UNTOUCHED (real values, natural per-gene proportions,
    never exceeding a real cell). This removes both prior tells: no 'MT inflated ~45x' and no uniform-MT-gene / bimodal
    signature. (An apoptotic cell is genuinely low-complexity, low-UMI — that is the real phenotype.)"""
    rows = _mt_rows(gn) or [0]; nonmt = np.ones(mat.shape[0], bool); nonmt[rows] = False
    m = mat.tolil(); cells = rng.choice(mat.shape[1], size=mat.shape[1] // 8, replace=False)
    for c in cells:
        col = m[:, c].toarray().ravel().astype(int)
        col[nonmt] = rng.binomial(col[nonmt], rng.uniform(0.06, 0.25))    # cytoplasm lost (continuum) but not to debris; MT kept as-is -> MT% clearly elevated, cells still recognizable
        m[:, c] = col.reshape(-1, 1)
    return m.tocsc(), gn, bc, meta
def inj_high_hb(mat, gn, bc, meta, rng):
    """Erythrocyte/RBC contamination: an RBC is HEMOGLOBIN-DOMINATED with very little other mRNA. Suppress the
    non-Hb transcriptome (binomial thin) then set Hb high -> high Hb fraction AND a depleted non-Hb profile (a real
    RBC). NOT a normal cell + Hb (whose non-Hb distribution is identical to normal cells = fabricated tell)."""
    m = mat.tolil(); rows = _hb_rows(gn) or [0]; cells = rng.choice(mat.shape[1], size=mat.shape[1]//10, replace=False)
    for c in cells:
        col = rng.binomial(m[:, c].toarray().ravel().astype(int), rng.uniform(0.10, 0.30))   # little non-Hb RNA
        for r in rows: col[r] += int(rng.integers(500, 2000))                                 # Hb dominates
        m[:, c] = col.reshape(-1, 1)
    return m.tocsc(), gn, bc, meta
def inj_doublets(mat, gn, bc, meta, rng):                   # synthesize doublets = sum of two random cells
    n = mat.shape[1]; k = max(20, n // 20); a = rng.choice(n, k); b = rng.choice(n, k)
    m = mat.tocsc(); m[:, a] = m[:, a] + m[:, b]
    return m, gn, bc, meta
def inj_feature_type(mat, gn, bc, meta, rng):               # append Antibody-Capture feature rows into the GEX matrix
    n = mat.shape[1]; extra = sp.csc_matrix(rng.integers(0, 50, size=(8, n)))
    m = sp.vstack([mat, extra]).tocsc()
    gn2 = list(gn) + [f"ADT_{x}" for x in ("CD3", "CD4", "CD8", "CD14", "CD19", "CD56", "PTPRC", "HTO1")]
    meta = dict(meta, _feature_types=["Gene Expression"] * len(gn) + ["Antibody Capture"] * 8)
    return m, gn2, bc, meta
def inj_count(mat, gn, bc, meta, rng):
    """Total-count / library-size outliers: inflate a few cells to ~8-30x depth by Poisson RESAMPLING (not an exact
    scalar multiple, which would make the cell an exact integer clone of a real one) -> a genuine high-count outlier
    with real sampling noise."""
    m = mat.tolil(); cells = rng.choice(mat.shape[1], size=max(10, mat.shape[1] // 40), replace=False)
    for c in cells:
        col = m[:, c].toarray().ravel().astype(float) * rng.uniform(8, 30)
        m[:, c] = rng.poisson(col).astype(int).reshape(-1, 1)
    return m.tocsc(), gn, bc, meta
def inj_metadata(mat, gn, bc, meta, rng):                   # stated species/chemistry contradict the data
    return mat, gn, bc, dict(meta, species="mouse", chemistry="10x 3' v3", expected_cells=200)
# ---- 3 realism-sensitive worlds: use the substrate's REAL empty-droplet tail (barcode-rank), not synthetic tells ----
def _umi(mat): return np.asarray(mat.sum(0)).ravel()
def _empty_idx(mat): return np.argsort(_umi(mat))[:mat.shape[1] // 2]          # bottom-half by UMI = the real empties
def _real_idx(mat): return np.argsort(-_umi(mat))[:mat.shape[1] // 2]

def inj_empty_droplets(mat, gn, bc, meta, rng):
    """BLUR the knee: swell a third of the real empty droplets 3-8x so their UMIs land in the ambiguous 1-2k zone
    and masquerade as cells -> a naive count-threshold includes them; only a proper knee/EmptyDrops analysis (they
    are ambient-only, low gene diversity) separates them."""
    m = mat.tolil(); empt = _empty_idx(mat); swell = rng.choice(empt, size=len(empt) // 3, replace=False)
    for c in swell:
        m[:, c] = (m[:, c].toarray().ravel() * int(rng.integers(3, 8))).reshape(-1, 1)
    return m.tocsc(), gn, bc, meta

def inj_ambient_rna(mat, gn, bc, meta, rng, soup=None):
    """Add a STRONG shared ambient background (the empty-droplet SOUP profile) to every cell -> ~15-30% of each
    cell's UMIs become ambient contamination (the tell: empties and cells share their top genes). `soup` is the
    empty-droplet mean profile, precomputed in build() BEFORE empties are filtered out."""
    if soup is None or soup.sum() == 0: return mat, gn, bc, meta
    m = mat.tolil(); umi = _umi(mat)
    for c in range(mat.shape[1]):
        scale = rng.uniform(0.15, 0.30) * max(int(umi[c]), 1) / soup.sum()
        m[:, c] = (m[:, c].toarray().ravel() + np.round(soup * scale).astype(int)).reshape(-1, 1)
    return m.tocsc(), gn, bc, meta

def inj_abstain_low_rna(mat, gn, bc, meta, rng):
    """Inject a REAL low-RNA population — PLATELETS (PPBP/PF4 high, very few genes). A naive n_genes filter discards
    them; the correct answer is RETAIN (they are real, not empty droplets). Abstention control."""
    plt = [i for i, g in enumerate(gn) if g.upper() in ("PPBP", "PF4", "GP9", "ITGA2B", "TUBB1")]
    n = mat.shape[1]; cells = rng.choice(_real_idx(mat), size=max(30, n // 30), replace=False); m = mat.tolil()
    for c in cells:
        col = np.zeros(mat.shape[0], int)
        for r in (plt or [0]): col[r] = int(rng.integers(120, 450))           # platelet markers DOMINATE (PPBP/PF4 very high in real platelets)
        ng = int(rng.integers(120, 280))                                      # low gene diversity, but UMI OVERLAPS the real low tail (no gap)
        for r in rng.choice(mat.shape[0], ng, replace=False): col[r] = max(col[r], int(rng.integers(1, 5)))
        m[:, c] = col.reshape(-1, 1)                                          # real platelet: low n_genes, UMI ~700-2500 sits inside the distribution
    return m.tocsc(), gn, bc, dict(meta, _abstain="platelet-like low-RNA population injected (PPBP/PF4 high) — REAL, RETAIN")

INJECT = {"clean": inj_clean, "empty_droplets": inj_empty_droplets, "high_mito": inj_high_mito,
          "high_hemoglobin": inj_high_hb, "doublets": inj_doublets, "ambient_rna": inj_ambient_rna,
          "feature_type_contamination": inj_feature_type, "count_complexity": inj_count,
          "metadata_reconciliation": inj_metadata, "abstain_low_rna": inj_abstain_low_rna}


def _read_clean():
    mat = sio.mmread(os.path.join(CLEAN, "matrix.mtx.gz")).tocsc()
    gn = [ln.split("\t")[1] if "\t" in ln else ln for ln in gzip.open(os.path.join(CLEAN, "features.tsv.gz"), "rt").read().splitlines()]
    bc = gzip.open(os.path.join(CLEAN, "barcodes.tsv.gz"), "rt").read().splitlines()
    meta = json.load(open(os.path.join(CLEAN, "study_metadata.json")))
    feats = [ln.split("\t") for ln in gzip.open(os.path.join(CLEAN, "features.tsv.gz"), "rt").read().splitlines()]
    return mat, gn, bc, meta, feats


ARCHIVE = "gene_bc_matrices.tar.gz"                    # neutral 10x-style download name (NOT "raw"/"filtered" -> no state tell); extracts to gene_bc_matrices/hg19/<trio>
def _write_world(cell, mat, gn, bc, meta, feats):
    """Write the world as a RAW 10x download: the matrix trio (matrix.mtx.gz + barcodes.tsv.gz + features.tsv.gz)
    packed inside a .tar.gz (the agent must extract it itself), plus study_metadata.json alongside (separate sheet).
    This exercises archive-format handling, not just a pre-unpacked matrix dir."""
    d = os.path.join(RUN_DIR, "data", f"cell{cell:03d}")
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d, exist_ok=True)   # wipe first -> no stale files survive a rebuild (e.g. a renamed archive)
    stage = tempfile.mkdtemp(prefix="scw_"); inner = os.path.join(stage, "gene_bc_matrices", "hg19")
    os.makedirs(inner, exist_ok=True)
    with gzip.open(os.path.join(inner, "matrix.mtx.gz"), "wb") as f: sio.mmwrite(f, sp.csc_matrix(mat), field="integer")
    with gzip.open(os.path.join(inner, "barcodes.tsv.gz"), "wt") as f: f.write("\n".join(bc) + "\n")
    ftypes = meta.get("_feature_types") or ["Gene Expression"] * len(gn)
    ids = [feats[i][0] if i < len(feats) else gn[i] for i in range(len(gn))]
    with gzip.open(os.path.join(inner, "features.tsv.gz"), "wt") as f:
        f.write("\n".join(f"{ids[i]}\t{gn[i]}\t{ftypes[i]}" for i in range(len(gn))) + "\n")
    with tarfile.open(os.path.join(d, ARCHIVE), "w:gz") as tf:
        tf.add(os.path.join(stage, "gene_bc_matrices"), arcname="gene_bc_matrices")
    shutil.rmtree(stage, ignore_errors=True)
    json.dump({k: v for k, v in meta.items() if not k.startswith("_")},
              open(os.path.join(d, "study_metadata.json"), "w"), indent=1)
    return d


def build(nvar=1, only=None):                       # only=set of cell indices -> rebuild ONLY those world dirs (others untouched); manifest still full (GT is deterministic)
    if not os.path.exists(CLEAN):
        raise SystemExit("[world_builder] run build_substrate.py first (tracks/scrna/data/clean/ missing)")
    os.makedirs(os.path.join(RUN_DIR, "data"), exist_ok=True)
    matF, gn0, bc0, meta0, feats = _read_clean()                        # full substrate: real cells + empty droplets
    # CLEAN base = the REAL cells only (empties filtered) -> clean is truly clean; each issue is a sharp DELTA on it.
    real = _real_idx(matF)
    matR = matF[:, real].tocsc(); bcR = [bc0[i] for i in real]
    # _real_idx returns UMI-SORTED indices -> matR columns would be ordered by UMI (barcode<->UMI rho=-1), a
    # synthetic tell (real 10x barcodes are not UMI-ordered). Shuffle the column order to destroy that correlation.
    _sh = np.random.default_rng(2024).permutation(matR.shape[1])
    matR = matR[:, _sh].tocsc(); bcR = [bcR[i] for i in _sh]
    soup = np.asarray(matF[:, _empty_idx(matF)].mean(1)).ravel()        # ambient profile (from empties, before filtering)
    manifest, cell = [], 0
    for issue, gt in GT.items():
        for v in range(nvar):
            rng = np.random.default_rng(1000 * cell + 7)
            # only empty_droplets keeps the empty droplets in the matrix (that's its defect); everything else = real cells
            if only is None or cell in only:
                base, bcb = (matF, bc0) if issue == "empty_droplets" else (matR, bcR)
                if issue == "ambient_rna":
                    mat, gn, bc, meta = inj_ambient_rna(base.copy(), list(gn0), list(bcb), dict(meta0), rng, soup)
                else:
                    mat, gn, bc, meta = INJECT[issue](base.copy(), list(gn0), list(bcb), dict(meta0), rng)
                d = _write_world(cell, mat, gn, bc, meta, feats)
            else:
                d = os.path.join(RUN_DIR, "data", f"cell{cell:03d}")     # leave this world's data untouched
            world = {"cell": cell, "world_label": issue, "issue_type": issue, "issue_present": gt["present"],
                     "agent_input": d, "agent_output": f"{RUN_DIR}/out_cell{cell:03d}.json",
                     "correct_action": gt["correct_action"], "affected_entities": gt.get("affected", []),
                     "canonical_checks": gt.get("canonical_checks", []),
                     "diagnose_keywords": gt.get("diagnose_keywords", []),
                     "action_keywords": gt.get("action_keywords", [])}
            if gt.get("requires_external_evidence"):
                world["requires_external_evidence"] = True; world["abstention_question"] = gt["abstention_question"]
            manifest.append(world); cell += 1
    json.dump(manifest, open(os.path.join(RUN_DIR, "manifest.json"), "w"), indent=1)
    print(f"[world_builder] wrote {len(manifest)} worlds ({len(GT)} issues x {nvar}) -> {RUN_DIR}/manifest.json")
    return manifest


if __name__ == "__main__":
    nvar = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1
    only = (set(int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(","))
            if "--only" in sys.argv else None)
    build(nvar, only=only)
