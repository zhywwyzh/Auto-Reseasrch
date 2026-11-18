"""clinvar_acmg L2 — build LOCAL, panel-region tabix subsets of the reference DBs so the SEALED sandbox can
mount them offline (ro_paths). The agent queries these via pysam (tool/evidence selection). Run OUTSIDE the
sandbox (needs network). Writes to tracks/clinvar_acmg/L2/l2/resources/.
"""
import os, sys
import pysam

CA = "/etc/ssl/certs/ca-certificates.crt"
os.environ.setdefault("CURL_CA_BUNDLE", CA); os.environ.setdefault("SSL_CERT_FILE", CA)

CLINVAR = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz"
GNOMAD  = "https://storage.googleapis.com/gcp-public-data--gnomad/release/4.1/vcf/genomes/gnomad.genomes.v4.1.sites.chr{c}.vcf.bgz"
CADD    = "https://krishna.gs.washington.edu/download/CADD/v1.7/GRCh38/whole_genome_SNVs.tsv.gz"
RES = os.path.join(os.path.dirname(__file__), "l2", "resources")

# panel genes (no-chr naming, matches ClinVar/CADD). gnomAD is chr-prefixed.
GENES = [
    ("LDLR", "19", 11089362, 11133820), ("APOB", "2", 21001429, 21044073),
    ("BRCA1", "17", 43044295, 43125483), ("BRCA2", "13", 32315474, 32400266),
    ("TP53", "17", 7668402, 7687550), ("MLH1", "3", 36993350, 37050846),
    ("MSH2", "2", 47403067, 47485000), ("CFTR", "7", 117480025, 117668665),
    ("HBB", "11", 5225464, 5229395), ("HFE", "6", 26087280, 26098571),
    ("PAH", "12", 102836889, 102958410),
]


def ckey(chrom):
    x = chrom.replace("chr", "")
    return int(x) if x.isdigit() else 99


def write_sorted_vcf(header_text, lines, out):
    """lines: list of (ckey, pos, vcf_line_str). tabix needs coordinate-sorted input."""
    lines.sort(key=lambda t: (t[0], t[1]))
    tmp = out + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(header_text if header_text.endswith("\n") else header_text + "\n")
        for _, _, ln in lines:
            fh.write(ln if ln.endswith("\n") else ln + "\n")
    pysam.tabix_compress(tmp, out, force=True); os.remove(tmp)
    pysam.tabix_index(out, preset="vcf", force=True)


def subset_clinvar(out):
    src = pysam.VariantFile(CLINVAR)      # single file, all contigs (no-chr naming)
    lines = []
    for gene, c, s, e in GENES:
        for rec in src.fetch(c, s, e):
            lines.append((ckey(rec.chrom), rec.pos, str(rec)))
    write_sorted_vcf(str(src.header), lines, out)
    print(f"  [ClinVar] wrote {out}  ({len(lines)} records)")


def subset_gnomad(out):
    by_c = {}
    for gene, c, s, e in GENES:
        by_c.setdefault(c, []).append((gene, s, e))
    hdr = str(pysam.VariantFile(GNOMAD.format(c=list(by_c)[0])).header)   # per-chrom files share one header
    lines = []
    for c, regions in by_c.items():
        gv = pysam.VariantFile(GNOMAD.format(c=c))
        for gene, s, e in regions:
            for rec in gv.fetch("chr" + c, s, e):
                lines.append((ckey(rec.chrom), rec.pos, str(rec)))
            print(f"  [gnomAD] {gene}: cumulative {len(lines)}")
    write_sorted_vcf(hdr, lines, out)
    print(f"  [gnomAD] wrote {out}  ({len(lines)} records)")


def subset_cadd(out):
    tb = pysam.TabixFile(CADD)
    header = list(tb.header)
    rows = []
    for gene, c, s, e in GENES:
        for row in tb.fetch(c, s, e):
            f = row.split("\t", 2)
            rows.append((ckey(f[0]), int(f[1]), row))
        print(f"  [CADD] {gene}: cumulative {len(rows)} rows")
    rows.sort(key=lambda t: (t[0], t[1]))               # tabix needs contiguous, position-sorted
    tmp = out + ".tmp"
    with open(tmp, "w") as fh:
        for h in header:
            fh.write(h + "\n")
        for _, _, row in rows:
            fh.write(row + "\n")
    pysam.tabix_compress(tmp, out, force=True); os.remove(tmp)
    pysam.tabix_index(out, seq_col=0, start_col=1, end_col=1, meta_char="#", force=True, zerobased=False)
    print(f"  [CADD] wrote {out}  ({len(rows)} rows)")


def main():
    os.makedirs(RES, exist_ok=True)
    print("subsetting ClinVar ..."); subset_clinvar(f"{RES}/clinvar.panel.vcf.gz")
    print("subsetting gnomAD ...");  subset_gnomad(f"{RES}/gnomad.panel.vcf.gz")
    print("subsetting CADD ...");    subset_cadd(f"{RES}/cadd.panel.tsv.gz")
    print("done -> " + RES)


if __name__ == "__main__":
    main()
