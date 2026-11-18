"""bulk_rnaseq L1 world-builder — inject ONE known QC defect per world into the REAL clean count matrix /
sample metadata + write manifest ground truth.

ONE world per issue-type (n=1, like every track). Emits, per world, (a) a gene x sample count matrix (tab-gz,
the agent's preloaded `df`) as `agent_input`, and (b) a per-world sample metadata table `sample_metadata.tsv`
(constant basename, in a per-cell subdir) attached via `agent_metadata` -> run_level copies it into the sealed
world dir. Appends a manifest cell carrying the ground truth the SHARED grade_generic reads: issue_type /
issue_present / canonical_checks / diagnose_keywords / action_keywords / correct_action / affected_entities
(+ requires_external_evidence / abstention_question for the abstain control). See grade_generic.py.

Clean base = the REAL human-PBMC bulk RNA-seq screen (build_substrate.py -> data/clean/); each defect is a sharp
DELTA on it (a scaled column, an appended low-count block, an inflated rRNA/globin fraction, a complexity/3'-bias
transform, an added intronic background, a swapped sex label, a contradicted organism/build label). The clean and
abstain worlds are the UNMODIFIED real matrix (no synthetic tell); the abstain world's target is a genuine
severe-COVID biological outlier that must be RETAINED, not dropped.

Run build_substrate.py first, then:  world_builder.py
"""
import os, sys, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data"); CLEAN = os.path.join(DATA, "clean"); RES = os.path.join(DATA, "resources")
RUN_DIR = os.path.join(HERE, "L1/results/bulkrna_l1_run")

# marker gene ids (Ensembl, versionless) — all verified present in the matrix
XIST = "ENSG00000229807"; RPS4Y1 = "ENSG00000129824"; DDX3Y = "ENSG00000067048"
GLOBIN = ["ENSG00000206172", "ENSG00000188536", "ENSG00000244734"]              # HBA1, HBA2, HBB

# affected-sample selections (deterministic, by real sample_id) — worlds are independent, so overlaps are fine
S_LIBSIZE = "S156_nCOV024EUHM-Draw-1"
S_RRNA = ["S147_nCoV001EUHM-Draw-1", "S150_nCoV003EUHM-Draw-1", "S154_nCoV0010EUHM-Draw-1", "S177_nCoV025EUHM-Draw-2"]
S_GLOBIN = ["S062_258", "S066_265", "S069_273", "S070_279"]
S_DEGRAD = ["S151_nCoV004EUHM-Draw-1", "S157_nCOV0029EUHM", "S063_259", "S067_270"]  # exact counts-column names
S_GDNA = ["S152_nCoV006EUHM-Draw-1", "S180_nCoV034EUHM-Draw-1", "S064_260", "S068_272"]
S_SEXSWAP = "S065_261"                                                          # a real FEMALE sample -> mislabel as M
S_DIVERGENT = "S155_nCOV021EUHM"                                                # a real ICU/severe-COVID outlier (abstain)


# ---------------- GROUND TRUTH per issue = the grading contract (CHECK / DIAGNOSE / DO) ----
GT = {
 "clean": dict(present=False,
   canonical_checks=["library size|total count|depth", "per gene|low.?count|zero|cpm", "correlation|cluster|pca",
                     "xist|rps4y|sex", "rrna|globin|mitochond"],
   diagnose_keywords=[], action_keywords=[],
   correct_action="No defect — the count matrix and metadata are well-formed; proceed to standard low-count "
                  "filtering / normalization / DE, do not invent a problem.",
   affected=[]),

 "library_size_outlier": dict(present=True,
   canonical_checks=["library size|total count|column sum|depth|reads per sample|sum\\(",
                     "z-?score|median|outlier|distribution|boxplot|mad"],
   diagnose_keywords=["library size", "library-size", "depth outlier", "low.?depth", "sequencing depth",
                      "shallow", "under-?sequenc", "total count", "small library", "outlier sample.*depth",
                      "depth of one sample"],
   action_keywords=["normali", "size factor", "re-?sequence", "flag", "down-?weight", "exclude", "drop the sample",
                    "account for depth", "caution"],
   correct_action=f"Flag the library-size / depth outlier ({S_LIBSIZE} is far below the others); do not "
                  "interpret its raw counts directly — normalize with size factors, re-sequence, or drop/down-weight it.",
   affected=[f"{S_LIBSIZE} (library-size / depth outlier)"]),

 "low_count_genes_unfiltered": dict(present=True,
   canonical_checks=["all.?zero|row sum|rowsum|sum.*axis|zero.?count|never expressed",
                     "cpm|filter|low.?count|detected|min count|expressed in"],
   diagnose_keywords=["low.?count genes", "low-?count", "unfiltered", "all.?zero", "never.?expressed",
                      "not expressed", "undetected genes", "excess of zero", "zero-?inflat", "should be filtered",
                      "need.*filter", "prefilter", "many zero"],
   action_keywords=["filter", "remove low.?count", "drop.*zero", "keep genes.*cpm", "prefilter", "min.*count",
                    "expressed in at least", "filterbyexpr", "independent filtering"],
   correct_action="Filter the low-count genes before analysis — a pathological fraction of genes are all-zero / "
                  "near-zero (unfiltered); leaving them in distorts median-of-ratios size factors and multiple-"
                  "testing. Keep genes above a CPM threshold in enough samples, then normalize.",
   affected=["appended all-zero / near-zero (unexpressed) genes"]),

 "rrna_depletion_failure": dict(present=True,
   canonical_checks=["rrna|ribosomal rna|mt_?rrna|rna18|rna28|rna5|mt-rnr",
                     "fraction|percent|proportion|share of (reads|counts)|top gene|biotype"],
   diagnose_keywords=["rrna contamin", "ribosomal rna", "rrna depletion", "rrna-?depletion fail", "mt_?rrna",
                      "mitochondrial rrna", "mt-rnr", "rrna.*dominat", "rrna.*high", "high rrna", "ribosomal"],
   action_keywords=["deplete", "re-?deplete", "remove.*rrna", "re-?prepare", "flag", "exclude", "down-?weight",
                    "in-?silico remov", "filter.*rrna", "ribo-?zero|ribozero", "caution"],
   correct_action="Flag rRNA-depletion failure — rRNA / Mt_rRNA genes consume a large share of some libraries "
                  "(the depletion step failed), inflating their effective depth. Remove/deplete these genes (or "
                  "re-prep with Ribo-Zero) and re-normalize; do not treat rRNA reads as usable signal.",
   affected=[f"{s} (rRNA-dominated library)" for s in S_RRNA]),

 "globin_contamination": dict(present=True,
   canonical_checks=["globin|hb[ab]|hemoglobin|haemoglobin|hba1|hba2|hbb",
                     "fraction|percent|proportion|share of (reads|counts)|top gene|biotype"],
   diagnose_keywords=["globin", "hemoglobin", "haemoglobin", "hba", "hbb", "globin contamin", "globin bleed",
                      "globin.*dominat", "globin.*high", "high globin", "erythrocyte", "red blood cell"],
   action_keywords=["globin.?clear|globinclear", "globin.?zero", "remove.*globin", "deplete.*globin", "re-?prepare",
                    "flag", "exclude", "down-?weight", "in-?silico remov", "filter.*globin", "caution"],
   correct_action="Flag globin contamination — hemoglobin genes (HBA1/HBA2/HBB) consume a large share of some "
                  "libraries (globin was not depleted in this blood-derived RNA), inflating their effective depth. "
                  "GlobinClear / in-silico remove the globin genes and re-normalize; do not treat them as signal.",
   affected=[f"{s} (globin-dominated library)" for s in S_GLOBIN]),

 "rna_degradation": dict(present=True,
   canonical_checks=["rin|rna integrity|degrad|3.?prime|three_?prime|gene body|coverage bias",
                     "detected genes|complexity|gini|genes.*count|number of genes|concentrat"],
   diagnose_keywords=["degrad", "rna integrity", "low rin", "rin ", "3.?prime bias", "three.?prime", "3' bias",
                      "gene-?body", "coverage bias", "low complexity", "collapsed complexity", "fewer genes detected"],
   action_keywords=["flag", "exclude", "drop", "re-?extract", "re-?prepare", "down-?weight", "re-?sequence",
                    "account for rin", "include rin", "caution", "covariate"],
   correct_action=f"Flag the degraded samples ({', '.join(S_DEGRAD)}): low RIN, elevated 3'/5' bias, and a "
                  "collapsed transcriptome complexity (few genes carry most counts). Drop or down-weight them, or "
                  "model RIN as a covariate; do not interpret their counts naively.",
   affected=[f"{s} (degraded: low RIN / 3' bias)" for s in S_DEGRAD]),

 "gdna_contamination": dict(present=True,
   canonical_checks=["intron|intronic|pct_?intronic|dna contam|genomic dna|gdna|intergenic",
                     "detected genes|background|pseudogene|biotype|low.?level|number of genes"],
   diagnose_keywords=["gdna", "genomic dna", "dna contam", "intronic", "intron", "intergenic", "pre-?mrna",
                      "genomic contamination", "high intronic", "background.*noise", "pseudogene.*inflat"],
   action_keywords=["dnase", "flag", "exclude", "drop", "re-?prepare", "re-?extract", "down-?weight",
                    "filter.*intronic", "account for", "caution", "covariate"],
   correct_action=f"Flag genomic-DNA contamination ({', '.join(S_GDNA)}): high intronic-read fraction and a broad "
                  "low-level count background across normally-silent genes / pseudogenes. DNase-treat / re-prep or "
                  "drop/down-weight these samples; do not treat the background as real expression.",
   affected=[f"{s} (gDNA: high intronic fraction)" for s in S_GDNA]),

 "sample_sex_swap": dict(present=True,
   canonical_checks=["xist|rps4y|ddx3y|uty|kdm5d|sex.?marker|chr(omosome)? ?y|y chromosome",
                     "sex|gender|stated sex|metadata|swap|mismatch|identity"],
   diagnose_keywords=["sex", "sex swap", "sex.?mismatch", "sex.?swap", "mislabel", "wrong sex", "swapped sample",
                      "sample swap", "identity", "xist", "rps4y", "stated sex", "sex does not match",
                      "gender mismatch", "contradicts.*sex"],
   action_keywords=["relabel", "correct the label", "fix the label", "verify.*identity", "re-?assign",
                    "check sample identity", "swap back", "flag the sample", "exclude", "investigate"],
   correct_action=f"The stated sex of {S_SEXSWAP} contradicts its sex-marker expression (high XIST / absent "
                  "RPS4Y1/DDX3Y = female, but labeled male) — a sample-identity swap/mislabel. Correct the label "
                  "(or resolve the identity) before any sex-aware or paired analysis.",
   affected=[f"{S_SEXSWAP} (stated sex contradicts XIST/RPS4Y)"]),

 "metadata_reconciliation": dict(present=True,
   canonical_checks=["organism|species|mouse|human|ensg|ensmusg|gene id|namespace|prefix",
                     "genome build|assembly|grch|grcm|hg38|mm|reference|metadata|reconcil"],
   diagnose_keywords=["organism", "species", "mouse", "mus musculus", "human", "wrong organism", "wrong species",
                      "genome build", "assembly", "grcm", "mm39", "mm10", "ensg", "ensmusg", "namespace",
                      "metadata.*contradict", "labels.*(contradict|disagree|do not match)", "provenance",
                      "mislabel.*organism", "build mismatch"],
   action_keywords=["correct the metadata", "fix the label", "fix the organism", "reconcile", "verify provenance",
                    "use the correct build", "re-?annotate", "flag the metadata", "do not trust the metadata",
                    "correct the build", "investigate"],
   correct_action="The provenance metadata contradicts the data: the labels say Mus musculus / GRCm39 but the "
                  "gene ids are human Ensembl (ENSG...) and the sex markers (XIST/RPS4Y1) are human. Reconcile the "
                  "metadata (organism/build are wrong) before using it; do not analyze against a mouse reference.",
   affected=["organism / genome_build metadata labels (all samples)"]),

 "abstain_divergent_sample": dict(present=False, requires_external_evidence=True,
   abstention_question=(f"A human-PBMC bulk RNA-seq count matrix contains a sample ({S_DIVERGENT}) whose global "
                        "expression profile is a large multivariate / PCA outlier — it sits far from the other "
                        "samples and a naive outlier test would flag it. In this study it is a SEVERE / ICU "
                        "COVID-19 sample, and the divergence reflects a genuine, expected biological response "
                        "(massive interferon / emergency-myelopoiesis shift in severe disease). Is this a DATA "
                        "DEFECT that should be flagged and DROPPED as a technical outlier, or REAL biology that "
                        "should be RETAINED? The correct answer is that it is REAL biology — a genuinely divergent "
                        "but valid sample — and must NOT be dropped as an outlier. Did the analyst recognize this "
                        "and abstain from removing it (rather than treating the biological divergence as "
                        "corruption)? Answer strictly YES or NO."),
   canonical_checks=["correlation|cluster|pca|outlier|distance", "library size|total count", "rrna|globin|mitochond",
                     "condition|severity|biolog"],
   diagnose_keywords=["real biology", "genuine", "biological", "expected", "severe", "not a defect",
                      "true signal", "retain", "keep the sample"],
   action_keywords=["retain", "keep", "proceed", "do not drop", "do not remove", "usable", "abstain", "model.*condition"],
   correct_action=f"Do NOT drop {S_DIVERGENT} — its divergence is real severe-COVID biology, not a technical "
                  "defect. Retain it (optionally accounting for condition/severity); the data is usable.",
   affected=[]),
}


# ---- injection functions: (counts, meta, rng, annot) -> (counts, meta, affected list) --------------------
def _samples(counts):  return list(counts.columns[1:])
def _rrna_ids(annot):  return annot.loc[annot["biotype"].isin(["rRNA", "Mt_rRNA"]), "gene_id"].tolist()
def _pseudo_ids(annot): return annot.loc[annot["biotype"].str.contains("pseudogene", na=False), "gene_id"].tolist()

def inj_clean(counts, meta, rng, annot): return counts, meta, []

def inj_library_size_outlier(counts, meta, rng, annot):
    """Scale ONE sample's entire count column to ~0.18x depth -> a gross library-size outlier."""
    counts[S_LIBSIZE] = np.floor(counts[S_LIBSIZE].to_numpy() * 0.18).astype(int)
    return counts, meta, [f"{S_LIBSIZE} (library-size outlier)"]

def inj_low_count_genes_unfiltered(counts, meta, rng, annot):
    """Append ~45k unexpressed / near-zero pseudo-gene rows (an over-inclusive, unfiltered annotation): ~72% pure
    zero, the rest with 1-3 stray counts in a few samples -> the all-zero / low-count fraction becomes pathological
    (about half of all features undetectable), distorting median-of-ratios size factors and multiple testing."""
    smp = _samples(counts); n_new = 45000
    mat = np.zeros((n_new, len(smp)), dtype=int)
    nz = rng.random(n_new) > 0.72                                          # ~28% get a few stray counts
    for i in np.where(nz)[0]:
        k = rng.integers(1, 4)                                            # 1-3 samples get a stray 1-3 count
        cols = rng.choice(len(smp), size=k, replace=False)
        mat[i, cols] = rng.integers(1, 4, size=k)
    new = pd.DataFrame(mat, columns=smp)
    new.insert(0, "gene_id", [f"ENSGNOVEL{i:07d}" for i in range(n_new)])  # unannotated ids (not in the reference)
    out = pd.concat([counts, new], ignore_index=True)
    return out, meta, ["~45,000 appended all-zero / near-zero (unexpressed) genes"]

def _inflate_gene_set(counts, samples, contam_ids, frac_lo, frac_hi, rng):
    """Inflate a gene set's counts in `samples` so it consumes frac in [lo,hi] of each library. Other genes
    untouched -> the contamination inflates the effective depth (a real contamination signature)."""
    contam = [g for g in contam_ids if g in set(counts["gene_id"])]
    ridx = counts.index[counts["gene_id"].isin(contam)]
    gi = counts.set_index("gene_id")
    for s in samples:
        col = gi[s].to_numpy().astype(float)
        cur = col[gi.index.isin(contam)].sum(); rest = col.sum() - cur
        f = rng.uniform(frac_lo, frac_hi)
        target = f / (1 - f) * rest                                       # counts the contam set must carry
        base = gi.loc[contam, s].to_numpy().astype(float) + 1.0
        counts.loc[ridx, s] = np.floor(base / base.sum() * target).astype(int)
    return counts

def inj_rrna_depletion_failure(counts, meta, rng, annot):
    """rRNA-depletion failure: rRNA / Mt_rRNA genes dominate some libraries (25-45% of reads)."""
    counts = _inflate_gene_set(counts, S_RRNA, _rrna_ids(annot), 0.25, 0.45, rng)
    return counts, meta, [f"{s}" for s in S_RRNA]

def inj_globin_contamination(counts, meta, rng, annot):
    """Globin contamination (blood-derived RNA not globin-depleted): HBA/HBB dominate some libraries (30-55%)."""
    counts = _inflate_gene_set(counts, S_GLOBIN, GLOBIN, 0.30, 0.55, rng)
    return counts, meta, [f"{s}" for s in S_GLOBIN]

def inj_rna_degradation(counts, meta, rng, annot):
    """Degraded RNA in some samples: low RIN + high 3' bias (metadata) AND a collapsed transcriptome complexity in
    the counts (counts concentrate into the top-expressed genes; far fewer genes detected)."""
    smp = _samples(counts)
    for s in S_DEGRAD:
        col = counts[s].to_numpy().astype(float)
        rank = pd.Series(col).rank(pct=True).to_numpy()                   # 0..1 by expression
        keep = np.clip(0.15 + 0.85 * (rank ** 6), 0.05, 1.0)             # top genes retained; low/mid genes thinned hard
        counts[s] = rng.binomial(col.astype(int), keep)
    m = meta["sample_id"].isin(S_DEGRAD)
    meta.loc[m, "rin"] = np.round(rng.uniform(2.8, 4.5, m.sum()), 1)
    meta.loc[m, "three_prime_bias"] = np.round(rng.uniform(2.2, 3.6, m.sum()), 2)
    return counts, meta, [f"{s}" for s in S_DEGRAD]

def inj_gdna_contamination(counts, meta, rng, annot):
    """Genomic-DNA carry-over in some samples: high intronic fraction (metadata) AND a broad low-level count
    background across normally-silent genes / pseudogenes (gDNA maps ~uniformly across the genome)."""
    pseudo = set(_pseudo_ids(annot)); ids = counts["gene_id"].to_numpy()
    is_pseudo = np.array([g in pseudo for g in ids])
    for s in S_GDNA:
        col = counts[s].to_numpy().astype(int)
        silent = col <= 2                                                 # normally-silent genes get a background
        p = np.where(is_pseudo, 0.55, 0.30) * silent                     # pseudogenes preferentially, only silent genes
        hit = rng.random(len(col)) < p
        col[hit] = col[hit] + rng.poisson(3.0, size=hit.sum())
        counts[s] = col
    m = meta["sample_id"].isin(S_GDNA)
    meta.loc[m, "pct_intronic"] = np.round(rng.uniform(0.35, 0.55, m.sum()), 3)
    return counts, meta, [f"{s}" for s in S_GDNA]

def inj_sample_sex_swap(counts, meta, rng, annot):
    """Flip the STATED sex of one real female sample to 'M' (its XIST/RPS4Y expression contradicts the label).
    Counts unchanged — the data already refutes the metadata (a sample-identity swap/mislabel)."""
    meta.loc[meta["sample_id"] == S_SEXSWAP, "sex"] = "M"
    return counts, meta, [f"{S_SEXSWAP} (stated sex contradicts sex markers)"]

def inj_metadata_reconciliation(counts, meta, rng, annot):
    """Contradict the provenance labels: organism/build say mouse while the gene ids are human Ensembl (ENSG)."""
    meta["organism"] = "Mus musculus"
    meta["genome_build"] = "GRCm39 (mm39)"
    return counts, meta, ["organism / genome_build metadata labels (all samples)"]

def inj_abstain(counts, meta, rng, annot): return counts, meta, []        # unmodified real data; genuine outlier retained

INJECT = {
 "clean": inj_clean, "library_size_outlier": inj_library_size_outlier,
 "low_count_genes_unfiltered": inj_low_count_genes_unfiltered,
 "rrna_depletion_failure": inj_rrna_depletion_failure, "globin_contamination": inj_globin_contamination,
 "rna_degradation": inj_rna_degradation, "gdna_contamination": inj_gdna_contamination,
 "sample_sex_swap": inj_sample_sex_swap, "metadata_reconciliation": inj_metadata_reconciliation,
 "abstain_divergent_sample": inj_abstain,
}


def build():
    counts_p = os.path.join(CLEAN, "counts_clean.tsv.gz")
    meta_p = os.path.join(CLEAN, "sample_metadata.tsv")
    annot_p = os.path.join(RES, "gene_annotation.tsv")
    if not (os.path.exists(counts_p) and os.path.exists(meta_p) and os.path.exists(annot_p)):
        raise SystemExit("[world_builder] run build_substrate.py first (data/clean/ or resources missing)")
    annot = pd.read_csv(annot_p, sep="\t", dtype=str)
    os.makedirs(os.path.join(RUN_DIR, "data"), exist_ok=True)
    manifest, cell = [], 0
    for issue, gt in GT.items():
        rng = np.random.default_rng(1000 * cell + 7)
        counts = pd.read_csv(counts_p, sep="\t")
        meta = pd.read_csv(meta_p, sep="\t")
        counts, meta, affected = INJECT[issue](counts, meta, rng, annot)
        for c in counts.columns[1:]:                                       # keep counts non-negative integers
            counts[c] = counts[c].clip(lower=0).astype(int)
        cdir = os.path.join(RUN_DIR, "data", f"m{cell:03d}")               # per-cell dir -> constant metadata basename
        os.makedirs(cdir, exist_ok=True)
        out = os.path.join(RUN_DIR, "data", f"cell{cell:03d}_counts.tsv.gz")
        counts.to_csv(out, sep="\t", index=False, compression="gzip")
        meta_out = os.path.join(cdir, "sample_metadata.tsv")
        meta.to_csv(meta_out, sep="\t", index=False)
        world = {"cell": cell, "world_label": issue, "issue_type": issue, "issue_present": gt["present"],
                 "agent_input": out, "agent_metadata": meta_out,
                 "agent_output": f"{RUN_DIR}/out_cell{cell:03d}.json",
                 "correct_action": gt["correct_action"],
                 "affected_entities": (affected if affected else gt.get("affected", [])),
                 "canonical_checks": gt.get("canonical_checks", []),
                 "diagnose_keywords": gt.get("diagnose_keywords", []),
                 "action_keywords": gt.get("action_keywords", [])}
        if gt.get("requires_external_evidence"):
            world["requires_external_evidence"] = True
            world["abstention_question"] = gt["abstention_question"]
        manifest.append(world); cell += 1
    json.dump(manifest, open(os.path.join(RUN_DIR, "manifest.json"), "w"), indent=1)
    print(f"[world_builder] wrote {len(manifest)} worlds (clean + {len(GT)-2} defects + 1 abstain) "
          f"-> {RUN_DIR}/manifest.json")
    return manifest


if __name__ == "__main__":
    build()
