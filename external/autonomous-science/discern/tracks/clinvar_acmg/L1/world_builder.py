"""Track 3 (Clinical variant / ACMG) — L1 world builder.

Inject ONE known data-integrity defect per world into the clean clinical VCF (build_substrate.py). Each of the
10 issue-types is built at `variants_per_issue` seeds (distinct injections) → the n=3 instances that give the
across-issue mean +/- SD (select_n1 freezes one later). Emits per-world VCFs + a manifest with ground truth in
the SAME schema the CF-GWAS L1 uses, so grade_generic.py runs UNCHANGED.

The agent's L1 job (sealed): validate/normalize/QC-filter/harmonize the VCF, quantify what's affected, and
recommend a PROPORTIONATE fix — or ABSTAIN when nothing is wrong. REF alleles in the clean world agree with
hg38.fa (a read-only resource the agent may consult), so reference/build defects are genuinely detectable.

usage: world_builder.py            # writes results/clinvar_l1_run/{data/*.vcf, manifest.json, manifest_full.json}
"""
import os, json, random, copy

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # benchmark root
CLEAN = os.path.join(os.path.dirname(__file__), "data", "clinical_clean.vcf")
META = os.path.join(os.path.dirname(__file__), "data", "study_metadata.json")
RUN = os.path.join(BASE, "results", "clinvar_l1_run")
HG38 = "/workspace/private-data/dna_token/hg38.fa"
VARIANTS_PER_ISSUE = 3

ISSUES = ["clean", "low_coverage", "strand_bias", "contamination", "build_mismatch",
          "af_scale", "duplicate_variants", "metadata_reconciliation", "reference_validation", "abstain_vus"]

# Per-issue keyword lists that the manifest-driven grader (grade_generic) uses to score the DEFECT worlds'
# detect->diagnose->act state machine (canonical_checks=det, diagnose_keywords=dia, action_keywords=act). Without
# these, every detected defect caps at NOTICE-WRONG (1). Regex-friendly substrings, matched case-insensitively.
KEYWORDS = {
    "low_coverage": {"canonical_checks": ["DP", "depth", "read depth", "FORMAT", "GQ", "genotype quality", r"\bAD\b", "sample"],
        "diagnose_keywords": ["low depth", "low coverage", "shallow", "insufficient depth", "DP <", "DP below", "under-covered", "low-depth"],
        "action_keywords": ["filter", "flag", "exclude", "remove low", "depth threshold", "low-confidence"]},
    "strand_bias": {"canonical_checks": ["FS", "strand", "SOR", "SB"],
        "diagnose_keywords": ["strand bias", "strand artifact", "high FS", "fisher strand", "strand-bias"],
        "action_keywords": ["filter", "flag", "strand", "exclude", "remove"]},
    "contamination": {"canonical_checks": ["allele balance", "AB", "AD", "VAF", "heteroz"],
        "diagnose_keywords": ["contaminat", "allele balance", "cross-sample", "skew", "off-balance", "VAF", "under-dispers"],
        "action_keywords": ["flag", "reject", "contaminat", "not trust", "untrustworthy", "unusable", "re-sequence"]},
    "build_mismatch": {"canonical_checks": ["reference", "REF", "fetch", "FastaFile", "faidx", "build"],
        "diagnose_keywords": ["build", "mismatch", "GRCh37", "hg19", "coordinate", "wrong build", "systematic", "reference mismatch", "liftover"],
        "action_keywords": ["liftover", "remap", "re-?map", r"\blift\b", "harmoniz", "convert", "regenerat", "repair",
                             "re-?annotat", "quarantin", "re-?verif", "reject", "re-?call", "correct.*coordinat"]},
    "af_scale": {"canonical_checks": ["AF", "frequency", "> 1", "percent"],
        "diagnose_keywords": ["scale", "percent", "fraction", "af > 1", "af>1", "greater than 1", "impossible frequency", "> 1.0"],
        "action_keywords": ["rescale", "divide", "/100", "normaliz", "convert", "scale"]},
    "duplicate_variants": {"canonical_checks": ["duplicat", "CHROM", "POS", "value_counts", "unique"],
        "diagnose_keywords": ["duplicat", "repeated", "same position", "identical", "redundant"],
        "action_keywords": ["dedup", "drop", "remove", "collapse", "de-duplicat"]},
    # TIGHTENED: the defect is study_metadata.json contradicting the VCF (PROBAND_07/n=3/GRCh37 vs the real
    # PROBAND_01/1/GRCh38). Loose keywords ("metadata","build") falsely credited unrelated findings (e.g. "missing
    # ##assembly provenance metadata"). Require (a) the CODE actually read the metadata file, AND (b) the report
    # name the SPECIFIC injected contradiction — terms that only appear if the agent found it.
    "metadata_reconciliation": {"canonical_checks": ["study_metadata", "os.listdir", "listdir", "metadata.json", "load(open"],
        "diagnose_keywords": ["proband_07", "grch37", "n_samples", "sample count", "3 sample", "reported sample",
                              "metadata.*contradict", "metadata.*disagree", "metadata.*mismatch", "stated.*build.*grch"],
        "action_keywords": ["reconcile", "flag.*metadata", "correct.*metadata", "verify.*metadata", "trust the vcf", "resolve"]},
    "reference_validation": {"canonical_checks": ["reference", "REF", "fetch", "FastaFile", "left-align", "normaliz", "rsID"],
        "diagnose_keywords": ["REF", "mismatch", "reference", "left-align", "not normaliz", "indel", "rsid", "does not match"],
        "action_keywords": ["left-align", "normaliz", "fix", "flag", "correct", "re-align", "drop"]},
}


# ---- tiny VCF model -------------------------------------------------------------------------------
def parse(path):
    hdr, recs = [], []
    for ln in open(path):
        if ln.startswith("#"):
            hdr.append(ln.rstrip("\n")); continue
        c = ln.rstrip("\n").split("\t")
        info = dict(kv.split("=", 1) for kv in c[7].split(";") if "=" in kv)
        smp = dict(zip(c[8].split(":"), c[9].split(":")))
        recs.append({"chrom": c[0], "pos": int(c[1]), "id": c[2], "ref": c[3], "alt": c[4],
                     "qual": c[5], "filter": c[6], "info": info, "fmt": c[8].split(":"), "smp": smp})
    return hdr, recs


def render(hdr, recs):
    out = list(hdr)
    for r in recs:
        info = ";".join(f"{k}={v}" for k, v in r["info"].items())
        smp = ":".join(str(r["smp"][k]) for k in r["fmt"])
        out.append("\t".join([r["chrom"], str(r["pos"]), r["id"], r["ref"], r["alt"],
                              str(r["qual"]), r["filter"], info, ":".join(r["fmt"]), smp]))
    return "\n".join(out) + "\n"


def eid(r):                                     # entity id for affected_entities
    return r["id"] if r["id"].startswith("rs") else f"{r['chrom']}:{r['pos']}"


# ---- injections (each returns (recs, header, affected_ids, correct_action, meta_override, usable, abstain)) ----
def inj_clean(recs, hdr, meta, rng):
    return recs, hdr, [], "none — data passes QC; proceed", None, True, False

def inj_low_coverage(recs, hdr, meta, rng):
    hit = rng.sample(recs, max(1, len(recs) // 7))
    for r in hit:
        dp = rng.randint(3, 8); r["smp"]["DP"] = str(dp)
        a = min(int(r["smp"]["AD"].split(",")[1]), dp); r["smp"]["AD"] = f"{dp-a},{a}"
        r["smp"]["GQ"] = str(rng.randint(6, 20))
    return (recs, hdr, [eid(r) for r in hit],
            "flag/filter the low-depth (DP<~10-15) genotypes as unreliable; do NOT interpret them", None, True, False)

def inj_strand_bias(recs, hdr, meta, rng):
    hit = rng.sample(recs, max(1, len(recs) // 8))
    for r in hit:
        r["info"]["FS"] = str(round(rng.uniform(40, 90), 3))
    return recs, hdr, [eid(r) for r in hit], "flag the high-strand-bias (FS) calls as likely strand artifacts", None, True, False

def inj_contamination(recs, hdr, meta, rng):
    # genome-wide allele-balance skew: het calls sit at VAF ~0.2-0.35 (not ~0.5) -> cross-sample contamination
    het = [r for r in recs if r["smp"]["GT"] == "0/1"]
    for r in het:
        dp = int(r["smp"]["DP"]); a = int(round(dp * rng.uniform(0.18, 0.34)))
        r["smp"]["AD"] = f"{dp-a},{a}"
    return (het and recs, hdr, [eid(r) for r in het[:20]],
            "recognize the genome-wide allele-balance skew (het VAF far below 0.5) as sample CONTAMINATION; "
            "genotypes are untrustworthy — do not interpret before resolving", None, False, False)

def inj_build_mismatch(recs, hdr, meta, rng):
    # SYSTEMATIC: shift every position by a fixed offset -> REF no longer matches hg38 anywhere, while metadata
    # still claims GRCh38. Detectable by validating REF against the reference for many/most variants.
    off = rng.choice([+9973, -10247, +15631])
    for r in recs:
        r["pos"] = r["pos"] + off
    return (recs, hdr, ["<systematic: ~all variants>"],
            "detect that REF alleles disagree with the GRCh38 reference SYSTEMATICALLY -> wrong build/"
            "coordinates; lift over (or re-map) before any interpretation", None, False, False)

def inj_af_scale(recs, hdr, meta, rng):
    # AF given as PERCENT not fraction -> values 0-100, many >1 (impossible for a frequency)
    for r in recs:
        r["info"]["AF"] = str(round(float(r["info"]["AF"]) * 100, 4))
    return (recs, hdr, ["<all AF values>"],
            "recognize AF is on a PERCENT scale (values >1) not a fraction; rescale by /100 before frequency "
            "filtering", None, True, False)

def inj_duplicate_variants(recs, hdr, meta, rng):
    dups = rng.sample(recs, max(1, len(recs) // 12))
    recs2 = recs + [copy.deepcopy(d) for d in dups]
    recs2.sort(key=lambda r: (r["chrom"], r["pos"]))
    return recs2, hdr, [eid(r) for r in dups], "identify and drop the duplicate variant records (same CHROM/POS/REF/ALT)", None, True, False

def inj_metadata_reconciliation(recs, hdr, meta, rng):
    # DATA is clean; the stated METADATA contradicts it (wrong sample id + n_samples + build label).
    mo = dict(meta); mo["sample_id"] = "PROBAND_07"; mo["n_samples"] = 3
    mo["assembly_build"] = "GRCh37"; mo["note"] = "metadata as received from the referring lab"
    return (recs, hdr, ["<metadata vs VCF: sample_id / n_samples / build>"],
            "reconcile the metadata against the VCF: the stated sample_id, n_samples, and assembly_build "
            "contradict the actual file (1 sample 'PROBAND_01'; REF agrees with GRCh38) — flag the metadata "
            "error, do not alter the (clean) calls", mo, True, False)

def inj_reference_validation(recs, hdr, meta, rng):
    # a FEW targeted records are invalid: wrong REF, a non-left-aligned indel, an rsID<->coord swap
    hit = rng.sample(recs, 4)
    aff = []
    for i, r in enumerate(hit):
        aff.append(eid(r))
        if i == 0:                                              # wrong REF (typo)
            r["ref"] = {"A": "T", "C": "G", "G": "C", "T": "A"}.get(r["ref"][0], "A") + r["ref"][1:]
        elif i == 1:                                            # non-left-aligned indel (redundant leading base)
            r["ref"], r["alt"] = "G" + r["ref"], "G" + r["alt"]; r["pos"] -= 0
        elif i == 2:                                            # rsID that cannot correspond to this coordinate
            r["id"] = "rs80338720"                              # a known unrelated dbSNP id
        else:                                                   # REF longer than the reference supports
            r["ref"] = r["ref"] + "ACGT"[rng.randint(0, 3)]
    return (recs, hdr, aff,
            "validate each record against the reference: fix/flag the REF-allele that disagrees with hg38, "
            "left-align the non-normalized indel, and flag the rsID that does not match its coordinate", None, True, False)

# The abstain_vus world data is a genuinely clean VCF (no injected defect). It is NOT graded like `clean`
# (where usable=True alone earns 3); it is graded on the abstention 3-tier so the agent must EXPLICITLY
# recognize the trap — that the data is clean AND that any pathogenicity call needs EXTERNAL evidence — to earn
# the top tier. That grading intent is carried by `requires_external_evidence=True` + this `abstention_question`
# on the manifest (see build()); recognized_limit() in grade_generic judges it. No variant is injected.
ABSTAIN_QUESTION = (
    "A single-sample clinical gene-panel VCF was QC'd and the DATA is clean (no integrity defect). Did the "
    "analyst EXPLICITLY recognize BOTH that (a) no data-integrity fix is warranted (do not fabricate a defect) "
    "AND (b) determining the clinical SIGNIFICANCE / pathogenicity of these variants requires EXTERNAL evidence "
    "(ClinVar / literature / functional or segregation data) beyond this file — i.e. explicitly ABSTAIN rather "
    "than either invent a data problem or assert pathogenicity? A generic 'data looks usable' that does NOT "
    "acknowledge the external-evidence / uncertain-significance limit does NOT count. Answer strictly YES or NO.")


def inj_abstain_vus(recs, hdr, meta, rng):
    # NO defect and NO variant injected — the world data is a genuinely clean VCF. The 'trap' is graded, not
    # injected: abstain_vus is scored on the abstention 3-tier (requires_external_evidence, see build()), so the
    # agent must EXPLICITLY recognize the abstention limit (ABSTAIN_QUESTION) to earn 3; a bare 'looks clean'
    # earns 2; fabricating a defect / calling it unusable earns 0.
    return (recs, hdr, [],
            "ABSTAIN: the VCF is well-formed and QC-clean — do not fabricate an integrity defect. Explicitly "
            "note that variant pathogenicity/significance cannot be determined from this file and needs EXTERNAL "
            "evidence (ClinVar / literature / functional / segregation), i.e. beyond L1 data QC.",
            None, True, True)

INJECT = {"clean": inj_clean, "low_coverage": inj_low_coverage, "strand_bias": inj_strand_bias,
          "contamination": inj_contamination, "build_mismatch": inj_build_mismatch, "af_scale": inj_af_scale,
          "duplicate_variants": inj_duplicate_variants, "metadata_reconciliation": inj_metadata_reconciliation,
          "reference_validation": inj_reference_validation, "abstain_vus": inj_abstain_vus}


def build():
    hdr0, recs0 = parse(CLEAN)
    meta0 = json.load(open(META))
    os.makedirs(f"{RUN}/data", exist_ok=True)
    full = []
    cell = 0
    for issue in ISSUES:
        for seed in range(VARIANTS_PER_ISSUE):
            rng = random.Random(1000 * ISSUES.index(issue) + seed)
            recs = copy.deepcopy(recs0)
            recs, hdr, aff, action, mo, usable, abstain = INJECT[issue](recs, list(hdr0), meta0, rng)
            cdir = f"{RUN}/data/cell{cell:03d}"; os.makedirs(cdir, exist_ok=True)   # per-cell dir -> clean, discoverable names
            vcf_path = f"{cdir}/variants.vcf"
            open(vcf_path, "w").write(render(hdr, recs))
            meta_path = f"{cdir}/study_metadata.json"                              # standard name the agent can find
            json.dump(mo or meta0, open(meta_path, "w"), indent=1)
            full.append({
                "cell": cell, "seed": seed, "source": "clinvar_acmg_synthetic",
                "task_type": "clinical_vcf_qc", "trait_context": "clinical germline variant interpretation",
                "n_rows": len(recs), "agent_input": vcf_path, "agent_metadata": meta_path,
                "agent_output": f"{RUN}/out_cell{cell:03d}.json",
                "reference_fasta": HG38,                       # read-only resource the agent may consult
                "world_label": issue, "issue_type": ("none" if issue in ("clean", "abstain_vus") else issue),
                "issue_present": not (issue in ("clean", "abstain_vus")),
                "affected_entities": aff, "correct_action": action,
                "analysis_usable": usable, "abstain_expected": abstain,
                # abstention worlds are graded on the 3-tier (OVER-DIAGNOSE 0 / ABSTAIN-OK 2 / ABSTAIN-RECOGNIZED
                # 3) — NOT the clean-world specificity path — so the agent must EXPLICITLY recognize the limit.
                "requires_external_evidence": abstain,
                "abstention_question": ABSTAIN_QUESTION if issue == "abstain_vus" else None,
                # keyword lists for grade_generic's defect state-machine (empty for clean/abstain worlds)
                "canonical_checks": KEYWORDS.get(issue, {}).get("canonical_checks", []),
                "diagnose_keywords": KEYWORDS.get(issue, {}).get("diagnose_keywords", []),
                "action_keywords": KEYWORDS.get(issue, {}).get("action_keywords", []),
            })
            cell += 1
    json.dump(full, open(f"{RUN}/manifest_full.json", "w"), indent=1)
    n1 = [e for e in full if e["seed"] == 0]                    # n=1 frozen: first seed of each issue
    json.dump(n1, open(f"{RUN}/manifest.json", "w"), indent=1)
    print(f"wrote {len(full)} worlds ({len(ISSUES)} issues x {VARIANTS_PER_ISSUE} seeds) -> {RUN}")
    print(f"  manifest.json = n=1 ({len(n1)} cells), manifest_full.json = {len(full)} cells")
    for e in n1:
        print(f"  [{e['cell']:>3}] {e['world_label']:<24} present={e['issue_present']!s:<5} "
              f"usable={e['analysis_usable']!s:<5} abstain={e['abstain_expected']!s:<5} n_aff={len(e['affected_entities'])}")


if __name__ == "__main__":
    build()
