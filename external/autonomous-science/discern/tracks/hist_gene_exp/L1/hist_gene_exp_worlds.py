"""Track 1: Histone marks -> gene expression — L1 world builder.

Builds sealed data-integrity QC worlds from the REAL K562 substrate (ENCODE histone BigWigs + GENCODE v29 +
K562 RSEM RNA-seq). One defect injected per world as a DELTA on the real data; large BigWigs are hard-linked
into each world and a private copy is written only for the track a defect actually modifies (see _private_copy).

n=1 convention: VARIANTS_PER_ISSUE seeds are built into manifest_full.json; seed 0 is frozen into the active
manifest.json (matches clinvar/scrna). Single source of truth: build() calls inject() for every world.

Usage: python tracks/hist_gene_exp/L1/hist_gene_exp_worlds.py  [--only cell0,cell1,...]
"""
import json, os, shutil, gzip, sys
from pathlib import Path
import numpy as np
import pyBigWig

TRACK_DIR = Path(__file__).resolve().parents[1]
CLEAN = TRACK_DIR / "data" / "raw"
RUN = TRACK_DIR / "L1" / "results" / "hist_qc_run"
DATA_DIR = RUN / "data"
VARIANTS_PER_ISSUE = 1                              # always 1 world per issue (n=1 convention, all tracks)

ISSUES = [
    "clean",
    "low_signal_to_noise",
    "missing_input_control",
    "blacklist_contamination",
    "batch_effect",
    "duplicate_samples",
    "expression_unit_error",
    "metadata_reconciliation",
    "reference_validation",
    "antibody_efficiency_abstain",
]

REQUIRED_FILES = [
    Path("reference/gencode.v29.gtf.gz"),
    Path("expression/k562_rna.tsv"),
    Path("histone/k562_h3k4me3.bigWig"),
    Path("histone/k562_h3k27ac.bigWig"),
    Path("histone/k562_h3k27me3.bigWig"),
]
RNA_REL = Path("expression/k562_rna.tsv")
GTF_REL = Path("reference/gencode.v29.gtf.gz")
H3K4ME3 = Path("histone/k562_h3k4me3.bigWig")
H3K27AC = Path("histone/k562_h3k27ac.bigWig")
H3K27ME3 = Path("histone/k562_h3k27me3.bigWig")

TPM_COLUMNS = ["TPM", "pme_TPM", "TPM_ci_lower_bound", "TPM_ci_upper_bound"]
TPM_SCALE_FACTORS = [100.0, 1000.0, 10000.0]

# A few REAL ENCODE hg38 blacklist v2 high-signal artifact regions (subset) — where ChIP artifacts pile up.
BLACKLIST_HG38 = [
    ("chr1", 124450000, 124460000), ("chr1", 143180000, 143280000),
    ("chr2", 90390000, 90420000),   ("chr9", 43860000, 43900000),
    ("chr16", 46380000, 46420000),  ("chr19", 24550000, 24600000),
    ("chr21", 8210000, 8260000),    ("chrX", 58550000, 58600000),
]


def validate_clean_substrate():
    missing = [CLEAN / rp for rp in REQUIRED_FILES if not (CLEAN / rp).is_file()]
    if missing:
        raise FileNotFoundError("Clean histone substrate incomplete:\n" + "\n".join(f"  - {p}" for p in missing))


def link_or_copy(source, destination):
    """Hard-link when possible (avoids duplicating multi-GB BigWigs); fall back to copy. NEVER modify a
    hard-linked file in place — an injection that changes a file must _private_copy it first."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def create_clean_world(destination):
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for rp in REQUIRED_FILES:
        link_or_copy(CLEAN / rp, destination / rp)


def _private_copy(world, rel):
    """Break the hard link for one file so it can be modified without touching the real substrate. Returns dst path."""
    dst = world / rel
    if dst.exists():
        dst.unlink()
    shutil.copy2(CLEAN / rel, dst)
    return dst


def _gt(issue, present, correct_action, canonical=None, diagnose=None, action=None, affected=None,
        requires_external_evidence=False, abstention_question=None, extra=None):
    """Assemble a COMPLETE ground-truth dict (every world returns the same shape -> build() is uniform)."""
    return {
        "issue_type": issue if present else "none",
        "issue_present": present,
        "affected_entities": affected or [],
        "correct_action": correct_action,
        "analysis_usable": True,
        "abstain_expected": bool(requires_external_evidence),
        "requires_external_evidence": bool(requires_external_evidence),
        "abstention_question": abstention_question,
        "canonical_checks": canonical or [],
        "diagnose_keywords": diagnose or [],
        "action_keywords": action or [],
        "manifest_extra": extra or {},
    }


# --------------------------- BigWig streaming transform (per-chrom; memory-safe) -----------------------------
def _rewrite_bigwig(world, mark_rel, value_fn):
    """Write a private copy of `mark_rel` applying value_fn(chrom,start,end,value)->new_value per interval.
    Streams one chromosome at a time. Preserves the header's chrom set/order."""
    src = CLEAN / mark_rel
    dst = world / mark_rel
    if dst.exists():
        dst.unlink()                                              # drop the hard link
    bw_in = pyBigWig.open(str(src))
    chroms = list(bw_in.chroms().items())
    bw_out = pyBigWig.open(str(dst), "w")
    bw_out.addHeader(chroms)
    for chrom, _clen in chroms:
        iv = bw_in.intervals(chrom)
        if not iv:
            continue
        starts = np.empty(len(iv), dtype=np.int64); ends = np.empty(len(iv), dtype=np.int64)
        vals = np.empty(len(iv), dtype=np.float64)
        for i, (s, e, v) in enumerate(iv):
            starts[i] = s; ends[i] = e; vals[i] = value_fn(chrom, s, e, v)
        bw_out.addEntries([chrom] * len(iv), starts.tolist(), ends=ends.tolist(),
                          values=vals.astype(float).tolist())
    bw_in.close(); bw_out.close()
    return dst


# --------------------------------------- injection functions ------------------------------------------------
def inj_clean(world, seed):
    return _gt("clean", False,
               "No injected data-integrity defect. Perform routine QC (chrom naming, signal ranges, promoter join, "
               "expression units) and proceed with promoter-level histone-mark vs gene-expression analysis.")


def inj_low_signal_to_noise(world, seed):
    """Degrade ONE active-mark track (H3K27ac): compress peak dynamic range + add a uniform background floor so
    signal-to-background (FRiP-like) collapses. A real poor-enrichment ChIP track."""
    floor = [3.0, 6.0, 10.0][seed % 3]
    scale = [0.35, 0.25, 0.15][seed % 3]
    _rewrite_bigwig(world, H3K27AC, lambda c, s, e, v: v * scale + floor)
    return _gt("low_signal_to_noise", True,
               "Recognize the H3K27ac track has poor signal-to-background (compressed peaks + high uniform floor); "
               "flag it as low-quality/low-enrichment and do not trust its peak calls; consider re-ChIP or exclude.",
               canonical=["signal-to-noise", "FRiP", "background", "enrichment", "peak", "dynamic range", "distribution"],
               diagnose=["low signal-to-noise", "poor enrichment", "high background", "flat", "compressed", "low quality track", "s/n"],
               action=["flag", "exclude", "low-quality", "re-chip", "do not trust", "down-weight"],
               affected=["histone/k562_h3k27ac.bigWig"],
               extra={"degraded_track": "k562_h3k27ac.bigWig", "scale": scale, "floor": floor})


def inj_missing_input_control(world, seed):
    """The experiment metadata declares a matched INPUT/control track (required for enrichment normalization),
    but that file is absent from the directory -> enrichment cannot be validated/normalized."""
    meta = {
        "cell_line": "K562", "genome_build": "GRCh38", "assay": "ChIP-seq",
        "marks": ["H3K4me3", "H3K27ac", "H3K27me3"],
        "input_control": "k562_input_control.bigWig",
        "normalization": "fold-change over matched input control",
        "note": "Signal tracks are provided; enrichment is defined relative to the matched input control.",
    }
    (world / "histone" / "experiment_metadata.json").write_text(json.dumps(meta, indent=1))
    return _gt("missing_input_control", True,
               "The metadata references a matched input/control track (k562_input_control.bigWig) required for "
               "enrichment normalization, but it is absent. Flag the missing input control; enrichment/fold-change "
               "cannot be validated without it — obtain the input before calling enrichment.",
               canonical=["input", "control", "normaliz", "fold-change", "enrichment", "metadata", "files present"],
               diagnose=["missing input", "no input control", "input absent", "control track missing", "no matched control"],
               action=["obtain input", "flag missing", "cannot normalize", "acquire control", "do not call enrichment"],
               affected=["histone/k562_input_control.bigWig (referenced but absent)"],
               extra={"declares_input": "k562_input_control.bigWig"})


def inj_blacklist_contamination(world, seed):
    """Inject extreme artifactual signal spikes at REAL ENCODE hg38 blacklist regions in H3K27ac -> ultra-high
    outlier signal at known-problematic loci that must be excluded before analysis."""
    spike = [3000.0, 8000.0, 15000.0][seed % 3]
    bl = BLACKLIST_HG38
    def vfn(c, s, e, v):
        for (bc, bs, be) in bl:
            if c == bc and s < be and e > bs:
                return spike
        return v
    _rewrite_bigwig(world, H3K27AC, vfn)
    return _gt("blacklist_contamination", True,
               "Extreme artifactual signal spikes sit at ENCODE blacklist / known-problematic regions (values far "
               "above the track max). Flag them as blacklist artifacts and exclude those regions (overlap with the "
               "ENCODE blacklist) before peak calling / promoter aggregation.",
               canonical=["blacklist", "artifact", "outlier", "extreme signal", "ENCODE blacklist", "exclude regions", "max"],
               diagnose=["blacklist", "artifact", "extreme outlier", "signal spike", "problematic region", "anomalous high signal"],
               action=["exclude", "remove blacklist", "filter regions", "mask", "intersect blacklist"],
               affected=[f"{c}:{s}-{e}" for (c, s, e) in bl],
               extra={"spiked_track": "k562_h3k27ac.bigWig", "spike_value": spike, "n_regions": len(bl)})


def inj_batch_effect(world, seed):
    """One mark (H3K4me3) carries a global normalization/batch scale offset relative to the others -> combining
    marks or applying a common signal threshold is confounded unless per-track normalized."""
    factor = [4.0, 6.0, 0.2][seed % 3]
    _rewrite_bigwig(world, H3K4ME3, lambda c, s, e, v: v * factor)
    return _gt("batch_effect", True,
               "The H3K4me3 track is on a different global signal scale (a normalization/batch offset) than the "
               "other marks. Flag the scale/batch inconsistency and normalize per-track (quantile / to a common "
               "reference) before comparing marks or setting a shared signal threshold.",
               canonical=["scale", "normaliz", "batch", "distribution", "range", "comparable", "quantile"],
               diagnose=["batch", "scale mismatch", "different normalization", "signal scale", "not comparable", "global shift"],
               action=["normalize", "quantile", "rescale", "per-track", "harmonize", "common reference"],
               affected=["histone/k562_h3k4me3.bigWig"],
               extra={"rescaled_track": "k562_h3k4me3.bigWig", "factor": factor})


def inj_duplicate_samples(world, seed):
    """Duplicate a block of gene rows in the RNA table (same gene_id appears twice) -> duplicate entries that
    break gene-keyed joins and inflate row counts."""
    dst = _private_copy(world, RNA_REL)
    lines = dst.read_text().splitlines()
    header, body = lines[0], lines[1:]
    ndup = [500, 1000, 2000][seed % 3]
    dup = body[:ndup]                                             # duplicate the first ndup gene rows verbatim
    out = [header] + body + dup
    dst.write_text("\n".join(out) + "\n")
    return _gt("duplicate_samples", True,
               f"{ndup} gene rows are exact duplicates (same gene_id appears twice) in the RNA table. Detect the "
               "duplicated gene entries and de-duplicate before joining expression to promoter signal.",
               canonical=["duplicate", "gene_id", "unique", "row count", "value_counts"],
               diagnose=["duplicate", "duplicated genes", "repeated gene_id", "non-unique", "duplicate rows"],
               action=["deduplicate", "drop duplicates", "remove duplicates", "unique"],
               affected=["expression/k562_rna.tsv (gene_id column)"],
               extra={"n_duplicated_rows": ndup})


def inj_expression_unit_error(world, seed):
    """Mis-scale the TPM-family columns (TPM no longer sums to ~1e6); raw counts untouched."""
    dst = _private_copy(world, RNA_REL)
    factor = TPM_SCALE_FACTORS[seed % len(TPM_SCALE_FACTORS)]
    lines = dst.read_text().splitlines()
    header = lines[0].split("\t")
    idx = {c: header.index(c) for c in TPM_COLUMNS if c in header}
    clean_sum = 0.0
    out = ["\t".join(header)]
    for ln in lines[1:]:
        f = ln.split("\t")
        if "TPM" in idx:
            clean_sum += float(f[idx["TPM"]] or 0)
        for c, i in idx.items():
            t = f[i].strip()
            if t:
                f[i] = f"{float(t) * factor:.12g}"
        out.append("\t".join(f))
    dst.write_text("\n".join(out) + "\n")
    return _gt("expression_unit_error", True,
               f"The TPM-family columns are mis-scaled by ~{factor:g}x (TPM no longer sums to ~1e6). Verify "
               "provenance and rescale/renormalize the TPM columns before analysis; do not alter raw counts.",
               canonical=[r"\bTPM\b", "TPM sum", "sum.*TPM", "total.*TPM", "normaliz", "scale", "FPKM", "expected_count"],
               diagnose=["unit error", "scale error", "mis-scal", "inflated TPM", "TPM.*sum", "does not sum", "not normalized"],
               action=["rescal", "divide", "renormal", "correct.*unit", "correct.*scale", "verify.*provenance"],
               affected=TPM_COLUMNS,
               extra={"injected_scale_factor": factor, "clean_tpm_sum": clean_sum, "corrupted_tpm_sum": clean_sum * factor})


def inj_metadata_reconciliation(world, seed):
    """Sample metadata contradicts the data: wrong cell line / wrong genome build / swapped mark labels."""
    variants = [
        {"cell_line": "HepG2", "genome_build": "GRCh38", "assay": "ChIP-seq",
         "tracks": {"k562_h3k4me3.bigWig": "H3K4me3", "k562_h3k27ac.bigWig": "H3K27ac", "k562_h3k27me3.bigWig": "H3K27me3"},
         "_contradiction": "cell_line says HepG2 but tracks/filenames + expression are K562"},
        {"cell_line": "K562", "genome_build": "hg19", "assay": "ChIP-seq",
         "tracks": {"k562_h3k4me3.bigWig": "H3K4me3", "k562_h3k27ac.bigWig": "H3K27ac", "k562_h3k27me3.bigWig": "H3K27me3"},
         "_contradiction": "genome_build says hg19 but GENCODE v29 + coordinates are GRCh38/hg38"},
        {"cell_line": "K562", "genome_build": "GRCh38", "assay": "ChIP-seq",
         "tracks": {"k562_h3k4me3.bigWig": "H3K27me3", "k562_h3k27ac.bigWig": "H3K27ac", "k562_h3k27me3.bigWig": "H3K4me3"},
         "_contradiction": "mark labels for the h3k4me3 and h3k27me3 files are swapped vs their filenames/signal profiles"},
    ]
    v = variants[seed % 3]
    (world / "study_metadata.json").write_text(json.dumps(v, indent=1))
    return _gt("metadata_reconciliation", True,
               "The study metadata contradicts the data (" + v["_contradiction"] + "). Reconcile stated metadata "
               "(cell line / genome build / mark labels) against the actual files and data; flag and correct the mismatch.",
               canonical=["metadata", "cell line", "genome build", "hg19", "hg38", "GRCh38", "mark label", "filename"],
               diagnose=["metadata mismatch", "contradict", "wrong cell line", "wrong build", "swapped", "stated vs data", "inconsistent metadata"],
               action=["reconcile", "correct metadata", "verify", "flag mismatch", "do not trust label"],
               affected=["study_metadata.json"],
               extra={"contradiction": v["_contradiction"]})


def inj_reference_validation(world, seed):
    """The GTF reference is inconsistent with the BigWig coordinates: chromosome-naming mismatch (strip 'chr'),
    so promoter/TSS coordinates from the GTF will NOT join to the BigWig 'chr'-prefixed contigs."""
    dst = world / GTF_REL
    if dst.exists():
        dst.unlink()
    n_stripped = 0
    with gzip.open(CLEAN / GTF_REL, "rt") as fin, gzip.open(dst, "wt") as fout:
        for ln in fin:
            if ln.startswith("#"):
                fout.write(ln); continue
            if ln.startswith("chr"):
                ln = ln[3:]; n_stripped += 1                      # 'chr1\t...' -> '1\t...'
            fout.write(ln)
    return _gt("reference_validation", True,
               "The GTF reference uses Ensembl-style chromosome names ('1','2',...) while the BigWig tracks use "
               "UCSC-style ('chr1',...). Validate the reference against the data and reconcile chromosome naming "
               "before deriving promoter/TSS coordinates and joining signal to genes.",
               canonical=["chromosome name", "chr prefix", "contig", "reference", "GTF", "join", "coordinate", "build"],
               diagnose=["chrom naming", "chr prefix mismatch", "reference mismatch", "naming inconsistency", "won't join", "contig mismatch"],
               action=["reconcile naming", "add chr prefix", "harmonize contigs", "validate reference", "fix chromosome names"],
               affected=["reference/gencode.v29.gtf.gz"],
               extra={"n_lines_stripped_chr": n_stripped})


def inj_antibody_efficiency_abstain(world, seed):
    """ABSTENTION control: the data are clean, but a question about RELATIVE ANTIBODY EFFICIENCY across marks
    cannot be answered from these files (no spike-in / input / positive control). The correct response is to
    ABSTAIN and state the external evidence needed — NOT to declare a track failed."""
    return _gt("antibody_efficiency_abstain", False,
               "Do NOT declare any track failed for 'low antibody efficiency'. Relative antibody efficiency across "
               "marks cannot be determined from these files alone (H3K27me3 is genuinely broad/low-amplitude by "
               "biology). Abstain and state that spike-in normalization / matched input / a positive control would "
               "be required to assess antibody efficiency.",
               canonical=["antibody efficiency", "spike-in", "input", "positive control", "dynamic range", "broad mark"],
               diagnose=["cannot determine", "not determinable", "insufficient", "no spike-in", "external evidence", "broad domain mark"],
               action=["abstain", "cannot assess", "need spike-in", "need external", "do not reject track", "retain"],
               requires_external_evidence=True,
               abstention_question=("Can the RELATIVE ANTIBODY EFFICIENCY across the histone marks be determined from "
                                    "the provided files? The correct answer is NO — H3K27me3's broad/low-amplitude "
                                    "profile is real biology, and antibody efficiency needs spike-in/input/positive "
                                    "controls not present here. Did the analyst ABSTAIN and name the external evidence "
                                    "needed, rather than declaring a track failed? Answer strictly YES or NO."))


INJECT = {
    "clean": inj_clean, "low_signal_to_noise": inj_low_signal_to_noise,
    "missing_input_control": inj_missing_input_control, "blacklist_contamination": inj_blacklist_contamination,
    "batch_effect": inj_batch_effect, "duplicate_samples": inj_duplicate_samples,
    "expression_unit_error": inj_expression_unit_error, "metadata_reconciliation": inj_metadata_reconciliation,
    "reference_validation": inj_reference_validation, "antibody_efficiency_abstain": inj_antibody_efficiency_abstain,
}


def inject(issue, seed, world_dir):
    """Create one world (clean base) + apply the issue's DELTA; return the COMPLETE ground-truth dict."""
    create_clean_world(world_dir)
    return INJECT[issue](world_dir, seed)


def build(only=None):
    validate_clean_substrate()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RUN.mkdir(parents=True, exist_ok=True)
    full, cell = [], 0
    for issue in ISSUES:
        for seed in range(VARIANTS_PER_ISSUE):
            wd = DATA_DIR / f"cell{cell:03d}"
            if only is None or f"cell{cell:03d}" in only or cell in only:
                gt = inject(issue, seed, wd)
            else:
                gt = None
            if gt is not None:
                full.append({
                    "cell": cell, "seed": seed, "source": "real_public_k562_epigenomic_data",
                    "task_type": "histone_expression_qc",
                    "trait_context": "K562 histone-mark signal and gene expression",
                    "agent_input": str(wd), "agent_output": str(RUN / f"out_cell{cell:03d}.json"),
                    "world_label": issue, "issue_type": gt["issue_type"], "issue_present": gt["issue_present"],
                    "affected_entities": gt["affected_entities"], "correct_action": gt["correct_action"],
                    "analysis_usable": gt["analysis_usable"], "abstain_expected": gt["abstain_expected"],
                    "requires_external_evidence": gt["requires_external_evidence"],
                    "abstention_question": gt["abstention_question"],
                    "canonical_checks": gt["canonical_checks"], "diagnose_keywords": gt["diagnose_keywords"],
                    "action_keywords": gt["action_keywords"], **gt["manifest_extra"],
                })
            cell += 1
    json.dump(full, open(RUN / "manifest_full.json", "w"), indent=2)
    manifest = [w for w in full if w["seed"] == 0]                # freeze seed 0 = active benchmark (n=1)
    json.dump(manifest, open(RUN / "manifest.json", "w"), indent=2)
    print(f"Wrote {len(full)} total worlds -> manifest_full.json")
    print(f"Active manifest ({len(manifest)} worlds, seed 0):")
    for w in manifest:
        print(f"  [{w['cell']:03d}] {w['world_label']:<26} present={w['issue_present']}")


if __name__ == "__main__":
    only = (set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None)
    build(only=only)
