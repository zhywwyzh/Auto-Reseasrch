"""Track 3 (Clinical variant / ACMG) — build the CLEAN L1 substrate from REAL public data.

Lesson learned the hard way: a purely SYNTHETIC single-sample VCF is effectively impossible to make
indistinguishable from real data to a frontier model. Over ~4 iterations, models correctly flagged one
population-genetics tell after another (impossible rare homozygotes -> all-heterozygous genome -> het:hom
ratio ~27 -> rare-variant density -> gene-body coordinate errors -> implausible gnomAD-popmax AF spectrum),
and two frontier models ended up with CONTRADICTORY requirements (one needs many high-AF sites to fix het:hom,
the other rejects the resulting high median AF). The robust fix is to stop synthesizing and start from REAL
data, which has no tells by construction.

Design (hybrid, all the load-bearing fields are REAL):
  - CHROM/POS/REF/ALT/GT   <- GIAB HG001 (NA12878) v4.2.1 benchmark VCF, fetched per gene region via the tabix
                              index (no full download). Real coordinates, real left-alignment, real het:hom,
                              real per-individual variant load, real population genetics.
  - INFO.AF (gnomAD popmax) <- gnomAD v4.1 genomes sites AF_grpmax, fetched per region. Real AF spectrum.
  - DP/GQ/QUAL/AD/FS/MQ/... <- realistic SYNTHESIS. We deliberately do NOT copy GIAB's own quality fields
                              (DP in the hundreds-thousands, GQ>99, QUAL=const 50) because THOSE are a GIAB
                              fingerprint. Synthesized clinical-callset quality was never flagged as a tell.

Requires network at BUILD time only (build runs outside the sandbox). The agent/sandbox reads the already
materialized per-cell VCFs, so runtime is unaffected and stays offline/sealed.

out: tracks/clinvar_acmg/L1/data/{clinical_clean.vcf, study_metadata.json, data_dictionary.json}
"""
import os, json, random
import pysam

HG38 = "/workspace/private-data/dna_token/hg38.fa"
OUT = os.path.join(os.path.dirname(__file__), "data")
SAMPLE = "PROBAND_01"
random.seed(42)                                   # reproducible substrate (frozen n=1 instantiation later)

# htslib libcurl needs the CA bundle to range-fetch the indexed remote VCFs over HTTPS.
_CA = "/etc/ssl/certs/ca-certificates.crt"
if os.path.exists(_CA):
    os.environ.setdefault("CURL_CA_BUNDLE", _CA)
    os.environ.setdefault("SSL_CERT_FILE", _CA)

GIAB = ("https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/NA12878_HG001/"
        "NISTv4.2.1/GRCh38/HG001_GRCh38_1_22_v4.2.1_benchmark.vcf.gz")
GNOMAD = ("https://storage.googleapis.com/gcp-public-data--gnomad/release/4.1/vcf/genomes/"
          "gnomad.genomes.v4.1.sites.{chrom}.vcf.bgz")

# clinically-important genes, CORRECTED GRCh38 gene-body windows (MSH2 was 3.8x too wide before -> variants
# spilled into neighbouring loci and a model cross-referenced them as mis-annotated). We fetch REAL variants
# only inside these windows, so gene labels are correct by construction.
GENES = [
    ("CFTR",  "chr7",  117480025, 117668665),
    ("BRCA1", "chr17", 43044295,  43125483),
    ("BRCA2", "chr13", 32315474,  32400266),
    ("HBB",   "chr11", 5225464,   5229395),
    ("HFE",   "chr6",  26087280,  26098571),
    ("LDLR",  "chr19", 11089362,  11133820),
    ("MLH1",  "chr3",  36993350,  37050846),
    ("MSH2",  "chr2",  47403067,  47485000),      # tightened to the ~82kb MSH2 body (was ...47709830)
    ("TP53",  "chr17", 7668402,   7687550),
    ("PAH",   "chr12", 102836889, 102958410),
    ("APOB",  "chr2",  21001429,  21044073),
]
BASES = "ACGT"
MAX_PER_GENE = 40                                 # subsample cap -> realistic panel load (~300-400 total)


def left_normalize(fa, chrom, pos, ref, alt):
    """Defensive left-align (GIAB indels are already normalized, but keep it for safety). pos is 1-based."""
    while True:
        while len(ref) > 1 and len(alt) > 1 and ref[-1] == alt[-1]:
            ref, alt = ref[:-1], alt[:-1]
        if ref[-1] == alt[-1] and (len(ref) == 1 or len(alt) == 1) and pos > 1:
            prev = fa.fetch(chrom, pos - 2, pos - 1).upper()
            if prev not in BASES:
                break
            ref, alt, pos = prev + ref, prev + alt, pos - 1
            continue
        break
    while len(ref) > 1 and len(alt) > 1 and ref[0] == alt[0]:
        ref, alt, pos = ref[1:], alt[1:], pos + 1
    return pos, ref, alt


def fetch_giab_variants(giab, chrom, start, end):
    """Real biallelic PASS calls with a carrier GT (0/1 or 1/1) in [start,end]. Returns list of dicts."""
    out = []
    for rec in giab.fetch(chrom, start, end):
        alts = rec.alts or []
        if len(alts) != 1:                                    # biallelic only
            continue
        alt = alts[0]
        ref = rec.ref
        if not ref or not alt or ref == alt:
            continue
        if len(ref) > 50 or len(alt) > 50:                    # skip large/complex events
            continue
        if any(b not in BASES for b in ref.upper()) or any(b not in BASES for b in alt.upper()):
            continue
        gt = rec.samples[0].get("GT")
        if gt in ((0, 1), (1, 0)):
            zg = "0/1"
        elif gt == (1, 1):
            zg = "1/1"
        else:
            continue                                          # skip 0/0, missing, multiallelic-encoded
        out.append(dict(chrom=chrom, pos=rec.pos, ref=ref.upper(), alt=alt.upper(), gt=zg))
    return out


def gnomad_af_map(chrom, start, end):
    """Map (pos,ref,alt) -> real gnomAD GLOBAL AF over the region. We use the global AF (not popmax/AF_grpmax):
    popmax is 1.0 for alleles fixed in ANY subpopulation, which then contradicts a heterozygous EUR proband
    (a real-but-confusing cross-population artifact a model flags as GT/AF inconsistency). Global AF is the
    standard clinical annotation and is ~never 1.0 for a variant the proband carries as a het."""
    afmap = {}
    gvf = pysam.VariantFile(GNOMAD.format(chrom=chrom))
    for rec in gvf.fetch(chrom, start, end):
        af = rec.info.get("AF")
        if af is None:
            continue
        for i, a in enumerate(rec.alts or []):
            val = af[i] if isinstance(af, tuple) else af
            if val is not None:
                afmap[(rec.pos, rec.ref.upper(), a.upper())] = float(val)
    return afmap


def build():
    os.makedirs(OUT, exist_ok=True)
    fa = pysam.FastaFile(HG38)
    giab = pysam.VariantFile(GIAB)
    rows = []
    for gene, chrom, start, end in GENES:
        variants = fetch_giab_variants(giab, chrom, start, end)
        if len(variants) > MAX_PER_GENE:
            # STRATIFIED subsample: preserve the gene's real het:hom ratio. A plain random.sample can zero out a
            # gene's few homozygotes (BRCA1/TP53 are ~99% het in a healthy proband), producing an ABSOLUTE
            # all-het chromosome that a model flags as "sample mixing" — even though it's real biology.
            hets = [v for v in variants if v["gt"] == "0/1"]
            homs = [v for v in variants if v["gt"] == "1/1"]
            frac = MAX_PER_GENE / len(variants)
            n_hom = min(len(homs), round(len(homs) * frac))
            n_het = min(len(hets), MAX_PER_GENE - n_hom)
            n_hom = min(len(homs), MAX_PER_GENE - n_het)      # top up if het-limited
            variants = sorted(random.sample(hets, n_het) + random.sample(homs, n_hom), key=lambda v: v["pos"])
        afmap = gnomad_af_map(chrom, start, end) if variants else {}
        for v in variants:
            pos, ref, alt, gt = v["pos"], v["ref"], v["alt"], v["gt"]
            if len(ref) != len(alt):
                pos, ref, alt = left_normalize(fa, chrom, pos, ref, alt)
            af = afmap.get((pos, ref, alt)) or afmap.get((v["pos"], v["ref"], v["alt"]))
            if af is None:                                    # novel / absent from gnomAD
                if gt == "1/1":
                    continue                                 # a novel hom-alt would read as an impossible rare-hom
                af = round(random.uniform(0.0001, 0.005), 6)  # realistic rare/novel het candidate
            af = round(float(af), 6)
            # --- realistic clinical-callset quality (synthesized; NOT GIAB's fingerprinted DP/GQ/QUAL) ---
            dp = max(12, int(random.gammavariate(6.0, 9.0)))
            # Allele balance must be TIGHTLY consistent with the (real) GT — a het with 90% alt reads reads as
            # internally inconsistent. het: AB ~ Beta(34,34) (mean 0.5, SD ~0.06, no extremes). hom-alt: only a
            # few ref reads from sequencing error (~1.5%). A binomial(dp,0.5) SD ~0.11 occasionally throws a het
            # out to 0.1/0.9, which a thorough model flags.
            if gt == "0/1":
                ab = random.betavariate(34, 34)               # ref-fraction ~ 0.35..0.65
                ad_alt = min(max(int(round(dp * ab)), 1), dp - 1)
            else:                                             # 1/1 -> almost all alt reads (<=~3% ref from seq error)
                ad_ref = min(sum(1 for _ in range(dp) if random.random() < 0.01), 3)
                ad_alt = dp - ad_ref
            ad_ref = dp - ad_alt
            gq = min(99, max(20, int(random.gauss(70, 15))))
            qual = round(max(30.0, gq * 8 + dp * 3 + random.gauss(0, 25)), 1)
            fs = round(random.expovariate(0.8), 3)
            mq = round(min(60.0, random.gauss(59.0, 1.5)), 1)
            qd = round(min(35.0, max(2.0, qual / dp + random.gauss(0, 1.5))), 2)
            mqrs = round(random.gauss(0.0, 1.0), 3)
            rprs = round(random.gauss(0.0, 1.0), 3)
            sor = round(min(2.9, max(0.1, random.gauss(1.1, 0.55))), 3)
            rsid = "." if random.random() < 0.12 else f"rs{random.randint(10_000_000, 99_999_999)}"
            rows.append(dict(chrom=chrom, pos=pos, rsid=rsid, ref=ref, alt=alt, gene=gene,
                             dp=dp, gt=gt, ad=f"{ad_ref},{ad_alt}", gq=gq, qual=qual, fs=fs, mq=mq,
                             qd=qd, mqrs=mqrs, rprs=rprs, sor=sor, af=af))
    # de-dup any position collisions and sort
    seen = set()
    uniq = []
    for r in sorted(rows, key=lambda r: (int(r["chrom"][3:]) if r["chrom"][3:].isdigit() else 99, r["pos"])):
        key = (r["chrom"], r["pos"], r["ref"], r["alt"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    rows = uniq

    hdr = [
        "##fileformat=VCFv4.2",
        "##reference=GRCh38",
        "##source=HaplotypeCaller",
        '##INFO=<ID=AF,Number=A,Type=Float,Description="gnomAD v4.1 genomes global allele frequency (fraction)">',
        '##INFO=<ID=GENE,Number=1,Type=String,Description="Overlapping gene symbol">',
        '##INFO=<ID=MQ,Number=1,Type=Float,Description="RMS mapping quality">',
        '##INFO=<ID=FS,Number=1,Type=Float,Description="Phred-scaled Fisher strand bias">',
        '##INFO=<ID=QD,Number=1,Type=Float,Description="Variant Confidence/Quality by Depth">',
        '##INFO=<ID=MQRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt vs. Ref read mapping qualities">',
        '##INFO=<ID=ReadPosRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of Alt vs. Ref read position bias">',
        '##INFO=<ID=SOR,Number=1,Type=Float,Description="Symmetric Odds Ratio of 2x2 contingency table to detect strand bias">',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
        '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read depth">',
        '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allelic depths (ref,alt)">',
        '##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Genotype quality">',
        '##FILTER=<ID=PASS,Description="All filters passed">',
        '##FILTER=<ID=LowQual,Description="Low quality variant call">',
    ]
    present_contigs = sorted({r["chrom"] for r in rows}, key=lambda c: int(c[3:]) if c[3:].isdigit() else 99)
    for c in present_contigs:
        hdr.append(f"##contig=<ID={c},length={fa.get_reference_length(c)},assembly=GRCh38>")
    hdr.append("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t" + SAMPLE)

    lines = list(hdr)
    for r in rows:
        info = (f"AF={r['af']};GENE={r['gene']};MQ={r['mq']};FS={r['fs']};QD={r['qd']};"
                f"MQRankSum={r['mqrs']};ReadPosRankSum={r['rprs']};SOR={r['sor']}")
        fmt = "GT:DP:AD:GQ"
        smp = f"{r['gt']}:{r['dp']}:{r['ad']}:{r['gq']}"
        lines.append(f"{r['chrom']}\t{r['pos']}\t{r['rsid']}\t{r['ref']}\t{r['alt']}\t{r['qual']}\tPASS\t{info}\t{fmt}\t{smp}")

    vcf_path = os.path.join(OUT, "clinical_clean.vcf")
    open(vcf_path, "w").write("\n".join(lines) + "\n")

    meta = {"sample_id": SAMPLE, "assembly_build": "GRCh38",
            "reported_ancestry": "EUR", "n_samples": 1,
            "assay": "targeted clinical gene panel (autosomal disease genes)",
            "variant_caller": "GATK HaplotypeCaller", "af_source": "gnomAD v4.1 genomes global AF (fraction 0-1)",
            "note": "Single-proband targeted autosomal gene panel. Coordinates on GRCh38; REF alleles agree "
                    "with the reference. Sex chromosomes are not part of this panel."}
    json.dump(meta, open(os.path.join(OUT, "study_metadata.json"), "w"), indent=1)

    dd = {"CHROM/POS": "GRCh38 coordinates (1-based)", "ID": "dbSNP rsID",
          "REF/ALT": "reference / alternate allele (VCF convention, left-aligned)",
          "INFO.AF": "gnomAD v4.1 genomes global allele frequency as a FRACTION in [0,1]",
          "INFO.GENE": "overlapping gene symbol", "INFO.FS": "Phred strand-bias (high => strand artifact)",
          "INFO.MQ": "RMS mapping quality (low => alignment concern)",
          "FORMAT.DP": "read depth", "FORMAT.AD": "allelic depths ref,alt", "FORMAT.GQ": "genotype quality"}
    json.dump(dd, open(os.path.join(OUT, "data_dictionary.json"), "w"), indent=1)

    het = sum(1 for r in rows if r["gt"] == "0/1")
    hom = sum(1 for r in rows if r["gt"] == "1/1")
    print(f"wrote {vcf_path}  ({len(rows)} REAL variants across {len({r['gene'] for r in rows})} genes)")
    print(f"  indels: {sum(1 for r in rows if len(r['ref'])!=len(r['alt']))}  | het: {het}  hom: {hom}  het:hom={het/max(hom,1):.2f}")
    print(f"  gnomAD-annotated: {sum(1 for r in rows if r['af']>=0.005)}  rare/novel: {sum(1 for r in rows if r['af']<0.005)}")
    print(f"  wrote study_metadata.json + data_dictionary.json")
    bad = 0
    for r in rows:
        if fa.fetch(r["chrom"], r["pos"]-1, r["pos"]-1+len(r["ref"])).upper() != r["ref"]:
            bad += 1
    print(f"  REF-vs-hg38 mismatches in CLEAN (must be 0): {bad}")


if __name__ == "__main__":
    build()
