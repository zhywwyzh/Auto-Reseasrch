"""clinvar_acmg L2 — WORLD builder. Builds clean + confound worlds for the 3 sub-tasks by injecting the golden
target variants (+ per-world confound corruptions) into the L1 REAL base VCF. The agent sees the world VCF +
mounted references (gnomAD/ClinVar/CADD via ro_paths) and must run the analysis; graded vs the golden manifest.

Reuses: L1 clean base (results/clinvar_l1_run/data/cell000/variants.vcf) as the proband background; the golden
truths in l2/gold_*.json. Run OUTSIDE the sandbox (no network needed — uses local golden + base).

out: results/clinvar_l2_{classify,prioritize,sf}_run/{data/cellNNN/variants.vcf, manifest.json}
"""
import os, json, re, copy, random
random.seed(7)

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = os.path.join(ROOT, "results", "clinvar_l1_run", "data", "cell000", "variants.vcf")
GOLD = os.path.join(HERE, "l2")
SAMPLE = "PROBAND_01"

# extra INFO fields the injected targets may carry (some are the CONFOUND — misleading vs the mounted references)
EXTRA_HDR = [
    '##INFO=<ID=TARGET,Number=0,Type=Flag,Description="A variant the task asks you to assess">',
    '##INFO=<ID=CSQ,Number=1,Type=String,Description="Provided molecular consequence annotation (VERIFY against a reference; may be on a non-canonical transcript)">',
    '##INFO=<ID=REVEL,Number=1,Type=Float,Description="Provided REVEL in-silico score (VERIFY; may be miscalibrated)">',
    '##INFO=<ID=CLINVAR_ECHO,Number=1,Type=String,Description="A single-submitter ClinVar echo (check review status/stars before trusting)">',
]


def load_base():
    hdr, recs = [], []
    for ln in open(BASE):
        (hdr if ln.startswith("#") else recs).append(ln.rstrip("\n"))
    return hdr, recs


def parse_variant(v):                    # "19:11113359T>C" -> ("chr19", 11113359, "T", "C")
    m = re.match(r"(\w+):(\d+)([ACGT]+)>([ACGT]+)", v)
    c, p, r, a = m.group(1), int(m.group(2)), m.group(3), m.group(4)
    return ("chr" + c if not c.startswith("chr") else c), p, r, a


def fmt_sample(gt="0/1", dp=60, ab=0.5, gq=99):
    ad_alt = max(1, int(round(dp * ab))); ad_ref = dp - ad_alt
    return f"{gt}:{dp}:{ad_ref},{ad_alt}:{gq}"


def rec_line(chrom, pos, ref, alt, info, smp, rsid=".", qual=800.0, filt="PASS"):
    return f"{chrom}\t{pos}\t{rsid}\t{ref}\t{alt}\t{qual}\tPASS\tGT:DP:AD:GQ\t{smp}" if False else \
        f"{chrom}\t{pos}\t{rsid}\t{ref}\t{alt}\t{qual}\t{filt}\t{info}\tGT:DP:AD:GQ\t{smp}"


def target_line(t, extra_info=None, gt="0/1", quality="clean"):
    chrom, pos, ref, alt = parse_variant(t["variant"])
    info = [f"GENE={t['gene']}", "TARGET"]
    if extra_info:
        info += extra_info
    if quality == "artifact":                       # low-quality / strand-biased artifact signature
        smp = fmt_sample(gt, dp=12, ab=0.18, gq=25); filt = "PASS"; qual = 45.0
        info += ["FS=61.2", "MQ=32.0", "SOR=4.1"]
    else:
        smp = fmt_sample(gt, dp=random.randint(45, 90), ab=0.5, gq=99); filt = "PASS"; qual = round(random.uniform(600, 1200), 1)
    return rec_line(chrom, pos, ref, alt, ";".join(info), smp, qual=qual, filt=filt)


# human-readable "why this distractor/trap is wrong" text, so the derived correct_action reads naturally
_WHY = {"artifact": "it is a low-quality sequencing artifact (strand bias / low depth), not a real variant",
        "common_lof": "it is far too common in gnomAD to cause a rare Mendelian disorder",
        "clean": "it lies in a gene unrelated to the proband's phenotype",
        "het_recessive": "it is a single heterozygous hit in a recessive gene (not biallelic)",
        "artifact_lof": "it is a sequencing artifact, not a real loss-of-function call",
        "out_of_scope": "its gene is not on the ACMG SF v3.2 reportable list",
        "vus_overreport": "it is a VUS, not Pathogenic/Likely-pathogenic",
        "af_benign": "it is benign / too common in gnomAD"}
_CTX = {"classify": "clinical germline variant classification (ACMG) of a proband gene panel",
        "prioritize": "diagnostic variant prioritization for a proband phenotype",
        "secondary_findings": "ACMG SF v3.2 secondary-findings reporting"}


def derive_judge_fields(sub_task, world_label, gold):
    """Derive the SHARED ground-truth fields (issue_type / correct_action / affected_entities /
    trait_context) from this track's gold blocks, so verify_grades.py scores against real ground truth instead
    of generic fallbacks. expected_method is stamped separately (from task_spec, via stamp_methods.py)."""
    issue_type = "none" if world_label == "clean" else world_label
    ctx = _CTX[sub_task]
    if sub_task == "classify":
        conf = gold.get("confound")
        if not conf:
            action = ("Classify all panel variants by ACMG using the mounted references (gnomAD AF, ClinVar "
                      "CLNSIG+review stars, CADD); report the correct 3-bin call for each.")
            return dict(issue_type=issue_type, correct_action=action, affected_entities=[], trait_context=ctx)
        action = (f"The provided {conf['injected']} on {conf['target']} ({conf['gene']}) is FALSE / misleading. "
                  f"Verify it against the mounted references and classify the variant {conf['true_bin'].upper()} "
                  f"anyway; do NOT let the in-VCF annotation override the reference evidence, and flag the "
                  f"discrepancy explicitly.")
        return dict(issue_type=issue_type, correct_action=action, affected_entities=[conf["target"]], trait_context=ctx)
    if sub_task == "prioritize":
        ds = gold.get("distractors") or []
        causal = gold.get("causal_variant")
        if not ds:
            action = f"Rank the true causal variant {causal} #1 for the proband's phenotype."
            return dict(issue_type=issue_type, correct_action=action, affected_entities=[], trait_context=ctx)
        parts = "; ".join(f"{d['variant']} ({d['gene']}) — {_WHY.get(d['kind'],'a distractor')}" for d in ds)
        action = (f"Rank the true causal variant {causal} #1 for the proband's phenotype and DEMOTE the "
                  f"distractor(s): {parts}. Name the reason each distractor is not causal.")
        return dict(issue_type=issue_type, correct_action=action,
                    affected_entities=[d["variant"] for d in ds], trait_context=ctx)
    if sub_task == "secondary_findings":
        trap = gold.get("trap")
        rep = gold.get("reportable") or []
        if not trap:
            action = f"Report exactly the {len(rep)} reportable P/LP-in-SF-gene secondary findings; report nothing else."
            return dict(issue_type=issue_type, correct_action=action, affected_entities=[], trait_context=ctx)
        action = (f"Report exactly the {len(rep)} reportable P/LP-in-SF secondary findings and do NOT report "
                  f"{trap['variant']} ({trap['gene']}) because {_WHY.get(trap['world'],'it is not reportable')}; "
                  f"justify the exclusion.")
        return dict(issue_type=issue_type, correct_action=action, affected_entities=[trap["variant"]], trait_context=ctx)
    return dict(issue_type=issue_type, correct_action="run the analysis correctly and report honestly",
                affected_entities=[], trait_context=ctx)


def write_world(run_dir, cell, world_label, sub_task, base_hdr, base_recs, inject_lines, gold, meta_extra=None):
    cdir = os.path.join(run_dir, "data", f"cell{cell:03d}"); os.makedirs(cdir, exist_ok=True)
    # header: base header + extra INFO defs, keep the #CHROM line last
    body = [h for h in base_hdr if not h.startswith("#CHROM")]
    chromline = [h for h in base_hdr if h.startswith("#CHROM")][0]
    hdr = body + EXTRA_HDR + [chromline]
    # merge + sort by (chrom index, pos)
    def key(l):
        f = l.split("\t"); c = f[0][3:]; return (int(c) if c.isdigit() else 99, int(f[1]))
    allrecs = sorted(base_recs + inject_lines, key=key)
    vcf = os.path.join(cdir, "variants.vcf")
    open(vcf, "w").write("\n".join(hdr + allrecs) + "\n")
    meta = {"sample_id": SAMPLE, "assembly_build": "GRCh38", "assay": "targeted clinical gene panel"}
    if meta_extra:
        meta.update(meta_extra)
    json.dump(meta, open(os.path.join(cdir, "study_metadata.json"), "w"), indent=1)
    jf = derive_judge_fields(sub_task, world_label, gold)      # SHARED ground-truth fields (consumed by verify_grades.py)
    return {"cell": cell, "world_label": world_label, "sub_task": sub_task, "task": f"clinvar_{sub_task}",
            "agent_input": vcf, "agent_metadata": os.path.join(cdir, "study_metadata.json"),
            "agent_output": os.path.join(run_dir, f"out_cell{cell:03d}.json"),
            "issue_present": world_label != "clean", "requires_external_evidence": False,
            "gold": gold, **jf}


# =========================== CLASSIFY ===========================
def build_classify():
    run_dir = os.path.join(ROOT, "results", "clinvar_l2_classify_run")
    hdr, recs = load_base()
    cl = json.load(open(f"{GOLD}/gold_classify.json"))
    pick = lambda pred: next(t for t in cl if pred(t))
    panel = [
        pick(lambda t: t["csq"] == "LOF" and t["gold_bin"] == "path"),
        pick(lambda t: t["csq"] == "missense" and t["gold_bin"] == "path" and (t["cadd"] or 0) >= 25),
        pick(lambda t: t["csq"] == "splice" and t["gold_bin"] == "path"),
        pick(lambda t: t["gold_bin"] == "vus"),
        pick(lambda t: t["gold_bin"] == "benign"),
    ]
    gold_panel = [{"variant": t["variant"], "gene": t["gene"], "gold_bin": t["gold_bin"]} for t in panel]
    manifest = []
    # world -> (focal index, extra INFO on that focal target) ; clean has none
    WORLDS = {
        "clean":                (None, None),
        "af_confound":          (1, ["AF=0.031"]),                        # provided common AF; gnomAD says rare
        "consequence_confound": (0, ["CSQ=synonymous_variant"]),          # LOF mislabeled; ClinVar MC says stop_gained
        "splice_pvs1":          (2, ["CSQ=intron_variant"]),              # canonical splice understated; ClinVar MC says splice_donor
        "insilico_confound":    (1, ["REVEL=0.04"]),                      # low REVEL; CADD says high
        "clinvar_echo":         (0, ["CLINVAR_ECHO=Benign|1_star_single_submitter"]),  # weak echo contradicts strong evidence
    }
    for cell, (w, (focal, extra)) in enumerate(WORLDS.items()):
        lines = []
        for i, t in enumerate(panel):
            lines.append(target_line(t, extra_info=extra if i == focal else None))
        # record WHICH target carries the injected lie + the lie itself, so the grader can score
        # lie-resistance on that specific variant (not conflate it with unrelated hard calls).
        confound = None
        if focal is not None:
            field = extra[0].split("=")[0]                              # AF / CSQ / REVEL / CLINVAR_ECHO
            confound = {"target": panel[focal]["variant"], "gene": panel[focal]["gene"],
                        "field": field, "injected": extra[0], "true_bin": panel[focal]["gold_bin"]}
        manifest.append(write_world(run_dir, cell * 3, w, "classify", hdr, recs, lines,
                                     gold={"targets": gold_panel, "confound": confound}))
    json.dump(manifest, open(os.path.join(run_dir, "manifest.json"), "w"), indent=1)
    print(f"classify: {len(manifest)} worlds -> {run_dir}  (panel: {[g['gold_bin'] for g in gold_panel]})")


# =========================== PRIORITIZE ===========================
def build_prioritize():
    run_dir = os.path.join(ROOT, "results", "clinvar_l2_prioritize_run")
    hdr, recs = load_base()
    pr = json.load(open(f"{GOLD}/gold_prioritize.json"))
    causal = pr["causal"]; hpo = pr["phenotype"]
    cl = json.load(open(f"{GOLD}/gold_classify.json"))
    # distractor material from golden pool (real variants)
    benign = [t for t in cl if t["gold_bin"] == "benign"][:2]
    nonpheno_lof = next(t for t in cl if t["csq"] == "LOF" and t["gold_bin"] == "path" and t["gene"] != "LDLR")
    common = next((t for t in cl if (t["af_global"] or 0) > 0.01), benign[0])
    gold = {"causal_variant": causal["variant"], "phenotype": hpo}
    meta = {"phenotype_hpo": hpo, "note": "Rank candidate causal variants for this proband's phenotype."}
    causal_t = {"variant": causal["variant"], "gene": "LDLR"}
    manifest = []
    WORLDS = {
        "clean":               [],
        "artifact_highimpact": [("artifact", nonpheno_lof)],             # flashy LOF but artifact quality
        "af_distractor":       [("common_lof", common)],                 # common variant w/ LOF-ish impact
        "phenotype_mismatch":  [("clean", nonpheno_lof)],               # real high-impact but wrong gene for HPO
        "inheritance_mismatch":[("het_recessive", next(t for t in cl if t["gene"] == "CFTR" and t["gold_bin"] == "path"))],
    }
    # why each distractor kind is NOT causal -> cue words the grader looks for in the agent's rationale
    REASON = {"artifact": ["artifact", "low.?qual", "strand", "DP", "GQ", "allele balance", "FS"],
              "common_lof": ["common", "frequen", "gnomad", "too high", "AF", "polymorph"],
              "clean": ["phenotype", "wrong gene", "not.*associat", "unrelated", "HPO", "does not fit"],
              "het_recessive": ["recessiv", "heterozyg", "carrier", "single.*allele", "biallelic", "inheritance"]}
    for cell, (w, extras) in enumerate(WORLDS.items()):
        lines = [target_line(causal_t, gt="0/1")]                        # the true causal, always present
        distractors = []
        for kind, t in extras:
            q = "artifact" if kind == "artifact" else "clean"
            lines.append(target_line({"variant": t["variant"], "gene": t["gene"]}, quality=q))
            distractors.append({"variant": t["variant"], "gene": t["gene"], "kind": kind,
                                "reason_cues": REASON.get(kind, [])})
        gw = dict(gold, distractors=distractors)
        manifest.append(write_world(run_dir, cell * 3, w, "prioritize", hdr, recs, lines, gold=gw, meta_extra=meta))
    json.dump(manifest, open(os.path.join(run_dir, "manifest.json"), "w"), indent=1)
    print(f"prioritize: {len(manifest)} worlds -> {run_dir}  (causal={causal['variant']})")


# =========================== SECONDARY FINDINGS ===========================
def build_sf():
    run_dir = os.path.join(ROOT, "results", "clinvar_l2_sf_run")
    hdr, recs = load_base()
    sf = json.load(open(f"{GOLD}/gold_secondary_findings.json"))["reportable"]
    cl = json.load(open(f"{GOLD}/gold_classify.json"))
    true_findings = sf[:5]                                               # inject 5 real P/LP-in-SF as the true set
    gold = {"reportable": [f["variant"] for f in true_findings]}
    base_lines = [target_line({"variant": f["variant"], "gene": f["gene"]}) for f in true_findings]
    nonsf_path = next(t for t in cl if t["gene"] in ("CFTR", "HBB", "HFE", "PAH") and t["gold_bin"] == "path")
    vus_sf = next(t for t in cl if t["gene"] in ("BRCA1","BRCA2","TP53","MLH1","MSH2","LDLR","APOB") and t["gold_bin"] == "vus")
    benign_sf = next(t for t in cl if t["gene"] in ("BRCA1","BRCA2","TP53","MLH1","MSH2","LDLR","APOB") and t["gold_bin"] == "benign")
    lof_sf = next(t for t in cl if t["gene"] in ("BRCA1","BRCA2","TP53","MLH1","MSH2") and t["csq"] == "LOF")
    WORLDS = {
        "clean":          [],
        "artifact_lof":   [("artifact", lof_sf)],                        # false LOF (artifact quality) in an SF gene
        "out_of_scope":   [("clean", nonsf_path)],                       # real P/LP in a NON-SF gene
        "vus_overreport": [("clean", vus_sf)],                           # VUS in an SF gene
        "af_benign":      [("clean", benign_sf)],                        # benign (common) in an SF gene
    }
    # why the injected trap must NOT be reported -> cue words the grader looks for as justification
    TRAP_REASON = {"artifact_lof": ["artifact", "low.?qual", "strand", "DP", "GQ", "allele balance", "FS", "false"],
                   "out_of_scope": ["not.*SF", "non.?SF", "not on the.*list", "out of scope", "not reportable gene"],
                   "vus_overreport": ["vus", "uncertain", "not.*pathogenic", "insufficient"],
                   "af_benign": ["benign", "common", "frequen", "gnomad", "AF"]}
    manifest = []
    for cell, (w, extras) in enumerate(WORLDS.items()):
        lines = list(base_lines)
        trap = None
        for kind, t in extras:
            lines.append(target_line({"variant": t["variant"], "gene": t["gene"]},
                                     quality="artifact" if kind == "artifact" else "clean"))
            trap = {"variant": t["variant"], "gene": t["gene"], "world": w,
                    "reason_cues": TRAP_REASON.get(w, [])}
        gw = dict(gold, trap=trap)
        manifest.append(write_world(run_dir, cell * 3, w, "secondary_findings", hdr, recs, lines, gold=gw,
                                     meta_extra={"note": "Report reportable ACMG-SF secondary findings (P/LP in SF genes only)."}))
    json.dump(manifest, open(os.path.join(run_dir, "manifest.json"), "w"), indent=1)
    print(f"secondary_findings: {len(manifest)} worlds -> {run_dir}  (true set size={len(true_findings)})")


if __name__ == "__main__":
    build_classify()
    build_prioritize()
    build_sf()
