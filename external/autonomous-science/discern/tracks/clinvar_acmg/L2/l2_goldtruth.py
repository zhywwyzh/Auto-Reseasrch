"""clinvar_acmg L2 — GOLDEN-TRUTH builder (reference solvers run end-to-end at BUILD time).

Produces the 3 golden ground truths by RUNNING a reference solver per sub-task on REAL evidence — which also
proves each analysis is solvable with the mounted toolset (gnomAD AF, CADD, ClinVar MC consequence + stars).

  stage 1: pull >=2-star ClinVar SNV target pool across the L1 panel genes (binned path/VUS/benign)
  stage 2: annotate a curated subset with gnomAD AF (popmax+global+FILTER) + CADD PHRED + consequence (MC)
  stage 3: run the 3 reference solvers -> golden truth (classify / prioritize / secondary_findings)

Run OUTSIDE the sandbox (needs network). Reuses the L1 panel genes.
"""
import os, json, re, random
import pysam

CA = "/etc/ssl/certs/ca-certificates.crt"
os.environ.setdefault("CURL_CA_BUNDLE", CA); os.environ.setdefault("SSL_CERT_FILE", CA)
random.seed(42)

CLINVAR = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz"
GNOMAD  = "https://storage.googleapis.com/gcp-public-data--gnomad/release/4.1/vcf/genomes/gnomad.genomes.v4.1.sites.chr{c}.vcf.bgz"
CADD    = "https://krishna.gs.washington.edu/download/CADD/v1.7/GRCh38/whole_genome_SNVs.tsv.gz"
OUT = os.path.join(os.path.dirname(__file__), "l2")

GENES = [
    ("LDLR",  "19", 11089362,  11133820,  "AD", True),
    ("APOB",  "2",  21001429,  21044073,  "AD", True),
    ("BRCA1", "17", 43044295,  43125483,  "AD", True),
    ("BRCA2", "13", 32315474,  32400266,  "AD", True),
    ("TP53",  "17", 7668402,   7687550,   "AD", True),
    ("MLH1",  "3",  36993350,  37050846,  "AD", True),
    ("MSH2",  "2",  47403067,  47485000,  "AD", True),
    ("CFTR",  "7",  117480025, 117668665, "AR", False),
    ("HBB",   "11", 5225464,   5229395,   "AR", False),
    ("HFE",   "6",  26087280,  26098571,  "AR", False),
    ("PAH",   "12", 102836889, 102958410, "AR", False),
]
GENE_HPO = {"LDLR": "familial hypercholesterolemia (elevated LDL-C, tendon xanthomas)"}

SPLICE_SO = ("splice_donor", "splice_acceptor")
LOF_SO = ("stop_gained", "frameshift", "start_lost", "nonsense")


def bin3(clnsig):
    s = str(clnsig)
    if "Pathogenic" in s and "Conflicting" not in s: return "path"
    if "Benign" in s and "Conflicting" not in s:     return "benign"
    if "Uncertain_significance" in s:                 return "vus"
    return None


def stars2(rev):
    r = str(rev)
    return ("reviewed_by_expert_panel" in r or "practice_guideline" in r or "multiple_submitters" in r)


def consequence(mc):
    s = str(mc).lower()
    for t in SPLICE_SO:
        if t in s: return "splice"      # canonical splice -> PVS1 by position
    for t in LOF_SO:
        if t in s: return "LOF"
    if "missense" in s: return "missense"
    if "synonymous" in s: return "synonymous"
    return "other"


# ---------- stage 1 ----------
def fetch_targets():
    vf = pysam.VariantFile(CLINVAR)
    pool = []
    for gene, chrom, s, e, inh, sf in GENES:
        for rec in vf.fetch(chrom, s, e):
            if not rec.ref or len(rec.ref) != 1:
                continue
            alts = [a for a in (rec.alts or []) if len(a) == 1]
            if len(alts) != 1:
                continue
            b = bin3(rec.info.get("CLNSIG"))
            if not b or not stars2(rec.info.get("CLNREVSTAT")):
                continue
            pool.append(dict(gene=gene, chrom=chrom, pos=rec.pos, ref=rec.ref, alt=alts[0], bin=b,
                             csq=consequence(rec.info.get("MC")), clnsig=str(rec.info.get("CLNSIG")),
                             stars=str(rec.info.get("CLNREVSTAT")), inheritance=inh, is_sf=sf))
    return pool


# ---------- stage 2: annotate a curated subset ----------
def gnomad_af(items):
    by_c = {}
    for it in items:
        by_c.setdefault(it["chrom"], []).append(it)
    for c, its in by_c.items():
        gv = pysam.VariantFile(GNOMAD.format(c=c))   # open remote chrom file once
        for it in its:
            it["af_global"], it["af_popmax"], it["gnomad_filter"] = (0.0, 0.0, "absent")
            for rec in gv.fetch("chr" + c, it["pos"] - 1, it["pos"]):   # tiny per-variant window (chr-prefixed)
                for i, a in enumerate(rec.alts or []):
                    if rec.pos == it["pos"] and rec.ref.upper() == it["ref"] and a.upper() == it["alt"]:
                        g = rec.info.get("AF"); gmax = rec.info.get("AF_grpmax")
                        it["af_global"] = float(g[i] if isinstance(g, tuple) else g) if g is not None else 0.0
                        it["af_popmax"] = float(gmax[0] if isinstance(gmax, tuple) else gmax) if gmax is not None else 0.0
                        it["gnomad_filter"] = ";".join(rec.filter.keys()) or "PASS"


def cadd_phred(items):
    tb = pysam.TabixFile(CADD)
    for it in items:
        it["cadd"] = None
        for row in tb.fetch(it["chrom"], it["pos"] - 1, it["pos"]):
            f = row.split("\t")   # chrom pos ref alt raw phred
            if int(f[1]) == it["pos"] and f[2] == it["ref"] and f[3] == it["alt"]:
                it["cadd"] = float(f[5]); break


# ---------- stage 3: reference solvers ----------
def solve_classify(t):
    """Simplified ACMG 3-bin from real evidence -> used to CONFIRM the >=2-star ClinVar gold is evidence-supported."""
    af = t.get("af_global") or 0.0; cadd = t.get("cadd") or 0.0; csq = t["csq"]
    # benign anchors
    if af >= 0.05:                              return "benign"   # BA1
    if af >= 0.01:                              return "benign"   # BS1
    # pathogenic anchors
    if csq in ("LOF", "splice") and af < 1e-4:  return "path"     # PVS1 (LOF or canonical splice) + PM2
    if csq == "missense" and cadd >= 25 and af < 1e-4: return "path"  # PP3 + PM2 (moderate)
    if csq == "synonymous" and cadd < 15:       return "benign"   # BP4/BP7-ish
    return "vus"


def build():
    os.makedirs(OUT, exist_ok=True)
    print("stage 1: target pool ..."); pool = fetch_targets()
    json.dump(pool, open(f"{OUT}/target_pool.json", "w"))
    from collections import Counter
    print(f"  pool={len(pool)} {dict(Counter(t['bin'] for t in pool))}")

    # ---- curate a small classify set: per gene, a few clean missense/LOF spanning the 3 bins ----
    curated = []
    for gene, *_ in GENES:
        g = [t for t in pool if t["gene"] == gene and t["csq"] in ("LOF", "splice", "missense", "synonymous")]
        for b in ("path", "vus", "benign"):
            cand = [t for t in g if t["bin"] == b]
            curated += random.sample(cand, min(2, len(cand)))
    print(f"stage 2: annotating {len(curated)} curated targets (gnomAD AF + CADD) ...")
    gnomad_af(curated); cadd_phred(curated)

    # ---- classify golden truth: keep targets where the reference solver AGREES with ClinVar gold (solvable/clean) ----
    for t in curated:
        t["solver_bin"] = solve_classify(t)
    clean = [t for t in curated if t["solver_bin"] == t["bin"]]
    classify_gold = [dict(gene=t["gene"], variant=f"{t['chrom']}:{t['pos']}{t['ref']}>{t['alt']}", csq=t["csq"],
                          af_global=t.get("af_global"), af_popmax=t.get("af_popmax"), cadd=t.get("cadd"),
                          stars=t["stars"], gold_bin=t["bin"], clnsig=t["clnsig"]) for t in clean]
    json.dump(classify_gold, open(f"{OUT}/gold_classify.json", "w"), indent=1)
    agree = len(clean)
    print(f"  CLASSIFY golden: {agree}/{len(curated)} targets where reference-solver bin == ClinVar gold "
          f"(solvable/clean) -> {OUT}/gold_classify.json")

    # ---- prioritize golden truth: pick a real rare LOF/path LDLR variant as the dominant causal for FH ----
    ldlr = [t for t in clean if t["gene"] == "LDLR" and t["bin"] == "path"
            and (t.get("af_global") or 0) < 1e-4]
    causal = ldlr[0] if ldlr else None
    prioritize_gold = None
    if causal:
        prioritize_gold = dict(phenotype=GENE_HPO["LDLR"],
                               causal=dict(gene="LDLR", variant=f"{causal['chrom']}:{causal['pos']}{causal['ref']}>{causal['alt']}",
                                           csq=causal["csq"], af_global=causal.get("af_global"), cadd=causal.get("cadd"),
                                           gold_bin="path", reason="rare pathogenic LDLR variant matching FH phenotype (dominant, single-hit causal)"))
        json.dump(prioritize_gold, open(f"{OUT}/gold_prioritize.json", "w"), indent=1)
        print(f"  PRIORITIZE golden: causal = LDLR {causal['pos']} ({causal['csq']}, AF={causal.get('af_global')}) -> {OUT}/gold_prioritize.json")
    else:
        print("  PRIORITIZE golden: no rare LOF/path LDLR found in curated set (widen curation)")

    # ---- secondary_findings golden truth: real path variants in SF genes, rare, that pass the solver ----
    sf_true = [dict(gene=t["gene"], variant=f"{t['chrom']}:{t['pos']}{t['ref']}>{t['alt']}", csq=t["csq"],
                    af_global=t.get("af_global"), gold_bin="path")
               for t in clean if t["is_sf"] and t["bin"] == "path" and (t.get("af_global") or 0) < 1e-3]
    json.dump({"reportable": sf_true}, open(f"{OUT}/gold_secondary_findings.json", "w"), indent=1)
    print(f"  SECONDARY-FINDINGS golden: {len(sf_true)} reportable P/LP-in-SF variants -> {OUT}/gold_secondary_findings.json")


if __name__ == "__main__":
    build()
