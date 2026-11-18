"""hist_gene_exp L2 — substrate builder (run ONCE, before the reference solver).

Produces the two real substrates the L2 sub-tasks run on:

1. PANEL BAM SUBSETS (sub-task (2) `quantify` — the tool-trap sub-task):
   data/raw/alignments_panel/{h3k4me3,h3k27me3,input}.panel.bam (+ .bai)
   = the real ENCODE K562 alignments (H3K4me3 ENCFF633WWH / ENCSR000AKU, H3K27me3 ENCFF190OWE /
     ENCSR000AKQ, input control ENCFF226FKB / ENCSR000AKY — SAME control experiment for both marks),
   subset to a fixed chromosome panel so MACS3/deepTools runs fit a sandbox cell.
   Panel motivation: chr9+chr22 carry K562's BCR-ABL amplification (real copy-number distortion ->
   the input-normalization trap has a real substrate); chr11+chr17 are gene-rich "normal" background;
   chr8 adds the 8q24 (MYC) region.

2. MULTI-PREDICTOR PER-GENE TABLE (sub-tasks (1) `regression` + (3) `effect_ranking`):
   data/processed/l2_gene_table.csv
   one row per expressed GENCODE v29 gene: promoter-level mark signal (the ENCODE fold-change-over-
   control bigWigs, +-1kb TSS mean — the track's L1 convention), DNase, promoter GC content + CpG
   observed/expected (computed from hg38 — the common-cause covariate for the gc_cpg_confound world),
   log1p(TPM) expression and log1p gene length.

Everything downstream (reference_solver.py -> golden truth -> world_builder.py -> grader thresholds)
derives from these two files. Provenance is written alongside as *_provenance.json.

usage: /workspace/home/miniconda3/envs/histl2/bin/python build_l2_substrate.py
"""
import csv, gzip, json, os, subprocess, sys
from pathlib import Path

import numpy as np
import pyBigWig
import pysam

TRACK = Path(__file__).resolve().parents[1]
RAW = TRACK / "data" / "raw"
ALN = RAW / "alignments"
PANEL_DIR = RAW / "alignments_panel"
PROC = TRACK / "data" / "processed"
PILOT = Path("/workspace/newton_genomics_pilot/realdata")
HG38 = "/workspace/private-data/dna_token/hg38.fa"

PANEL = ["chr8", "chr9", "chr11", "chr17", "chr22"]
PROM = 1000                                  # +-1kb TSS window — the track's L1/build_substrate convention

BAMS = {                                     # local name -> (ENCODE file(s), experiment, description)
    # h3k27me3 POOLS both replicates: the broad-domain trap needs depth (rep1 alone = 1.9M panel reads on
    # the 2026-08 chr-panel audit — too shallow for MACS3 broad-domain evidence; rep1+rep2 ~= doubles it).
    "h3k4me3":  (["ENCFF633WWH"], "ENCSR000AKU", "H3K4me3 ChIP-seq K562 rep1 filtered alignments (Bernstein/Broad)"),
    "h3k27me3": (["ENCFF190OWE", "ENCFF692KQZ"], "ENCSR000AKQ", "H3K27me3 ChIP-seq K562 rep1+rep2 POOLED filtered alignments (Bernstein/Broad)"),
    "input":    (["ENCFF226FKB"], "ENCSR000AKY", "control (input) K562 rep1 filtered alignments — the SAME control experiment ENCODE pairs with both marks"),
}
SAMTOOLS = str(Path(sys.executable).parent / "samtools")


def subset_bams():
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    prov = {"panel": PANEL, "source": {}}
    for name, (accs, exp, desc) in BAMS.items():
        out = PANEL_DIR / f"{name}.panel.bam"
        parts = []
        for acc in accs:
            src = ALN / f"{acc}.bam"
            if not (ALN / f"{acc}.bam.bai").exists():
                subprocess.run([SAMTOOLS, "index", "-@4", str(src)], check=True)
            part = PANEL_DIR / f".{name}.{acc}.part.bam"
            subprocess.run([SAMTOOLS, "view", "-@4", "-b", "-o", str(part), str(src)] + PANEL, check=True)
            parts.append(part)
        if len(parts) == 1:
            parts[0].rename(out)
        else:
            subprocess.run([SAMTOOLS, "merge", "-f", "-@4", str(out)] + [str(p) for p in parts], check=True)
            for p in parts:
                p.unlink()
        subprocess.run([SAMTOOLS, "index", "-@4", str(out)], check=True)
        n = int(subprocess.run([SAMTOOLS, "view", "-c", str(out)], check=True,
                               capture_output=True, text=True).stdout.strip())
        prov["source"][name] = {"encode_files": accs, "experiment": exp, "desc": desc, "panel_reads": n}
        print(f"[panel] {name}: {'+'.join(accs)} -> {out.name}  {n:,} reads on {'+'.join(PANEL)}")
    json.dump(prov, open(PANEL_DIR / "panel_provenance.json", "w"), indent=1)


def gene_annotation():
    """gene_id -> (chrom, tss, strand, gene_name) for GENCODE v29 genes."""
    genes = {}
    with gzip.open(RAW / "reference" / "gencode.v29.gtf.gz", "rt") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            f = line.split("\t")
            if f[2] != "gene":
                continue
            attr = f[8]
            gid = attr.split('gene_id "')[1].split('"')[0]
            name = attr.split('gene_name "')[1].split('"')[0] if 'gene_name "' in attr else gid
            tss = int(f[3]) if f[6] == "+" else int(f[4])
            genes[gid] = (f[0], tss, f[6], name)
    return genes


def build_gene_table():
    genes = gene_annotation()
    expr = {}
    with open(RAW / "expression" / "k562_rna.tsv") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["gene_id"].startswith("ENSG") and float(r["TPM"]) > 0:
                expr[r["gene_id"]] = (float(r["TPM"]), float(r["length"]))

    bws = {m: pyBigWig.open(str(PILOT / f"k562_{m}.bigWig"))
           for m in ("h3k4me3", "h3k27ac", "h3k27me3", "dnase")}
    fa = pysam.FastaFile(HG38)
    chroms = set(bws["h3k4me3"].chroms()) & set(fa.references)

    rows = []
    for gid, (tpm, length) in expr.items():
        if gid not in genes:
            continue
        chrom, tss, strand, name = genes[gid]
        if chrom not in chroms:
            continue
        lo, hi = max(0, tss - PROM), tss + PROM
        vals = {}
        for m, bw in bws.items():
            try:
                v = bw.stats(chrom, lo, hi, type="mean")[0]
            except Exception:
                v = None
            vals[m] = float(v or 0.0)
        seq = fa.fetch(chrom, lo, hi).upper()
        n = len(seq)
        if n == 0:
            continue
        g, c = seq.count("G"), seq.count("C")
        cg = seq.count("CG")
        gc = (g + c) / n
        cpg_oe = (cg * n / (c * g)) if (c and g) else 0.0        # CpG observed/expected (Gardiner-Garden)
        rows.append([gid, name, chrom, tss, strand,
                     round(np.log1p(vals["h3k4me3"]), 4), round(np.log1p(vals["h3k27ac"]), 4),
                     round(np.log1p(vals["h3k27me3"]), 4), round(np.log1p(vals["dnase"]), 4),
                     round(gc, 4), round(cpg_oe, 4),
                     round(np.log1p(tpm), 4), round(np.log1p(length), 4)])
    for bw in bws.values():
        bw.close()
    fa.close()

    PROC.mkdir(parents=True, exist_ok=True)
    out = PROC / "l2_gene_table.csv"
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["gene_id", "gene_name", "chrom", "tss", "strand",
                    "h3k4me3", "h3k27ac", "h3k27me3", "dnase",
                    "gc_content", "cpg_oe", "gene_expression", "gene_length"])
        w.writerows(rows)
    json.dump({
        "n_genes": len(rows), "window": f"TSS +-{PROM}bp", "signal": "log1p(mean ENCODE fold-change-over-control)",
        "tracks": "pilot realdata k562_{h3k4me3,h3k27ac,h3k27me3,dnase}.bigWig", "gc_source": HG38,
        "expression": "log1p(TPM), K562 RSEM", "annotation": "GENCODE v29 gene TSS",
    }, open(PROC / "l2_gene_table_provenance.json", "w"), indent=1)

    # quick sanity: the canonical signs must hold on the REAL table
    import pandas as pd
    df = pd.read_csv(out)
    for m in ("h3k4me3", "h3k27ac", "h3k27me3", "dnase"):
        r = np.corrcoef(df[m], df.gene_expression)[0, 1]
        print(f"[table] corr({m}, expression) = {r:+.3f}   (n={len(df)})")
    r_gc = np.corrcoef(df.gc_content, df.gene_expression)[0, 1]
    print(f"[table] corr(gc_content, expression) = {r_gc:+.3f}  (the common-cause covariate)")
    print(f"[out] {out}")


if __name__ == "__main__":
    subset_bams()
    build_gene_table()
