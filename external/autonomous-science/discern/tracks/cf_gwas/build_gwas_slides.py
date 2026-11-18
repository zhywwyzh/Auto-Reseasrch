"""GWAS benchmark EXPERIMENT-DESIGN deck (PI review). Design only, no results.
Each task = 2 slides (Setup · Agent interface & grading). Output: GWAS_Experiment_Design.pptx"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

NAVY=RGBColor(0x1F,0x32,0x4D); BLUE=RGBColor(0x2E,0x5E,0xAA); GREY=RGBColor(0x55,0x55,0x55)
HL=RGBColor(0xC0,0x39,0x2B); WHITE=RGBColor(0xFF,0xFF,0xFF); LBLUE=RGBColor(0xE8,0xEF,0xF7)
MONO=RGBColor(0x1A,0x1A,0x1A); CODEBG=RGBColor(0xF4,0xF6,0xF9)

prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
BLANK=prs.slide_layouts[6]
def slide(): return prs.slides.add_slide(BLANK)

def title(s,text,sub=None):
    tb=s.shapes.add_textbox(Inches(0.5),Inches(0.22),Inches(12.3),Inches(0.95)); tf=tb.text_frame; tf.word_wrap=True
    p=tf.paragraphs[0]; p.text=text; p.font.size=Pt(24); p.font.bold=True; p.font.color.rgb=NAVY
    if sub:
        p2=tf.add_paragraph(); p2.text=sub; p2.font.size=Pt(13); p2.font.italic=True; p2.font.color.rgb=BLUE
    ln=s.shapes.add_shape(1,Inches(0.5),Inches(1.14),Inches(12.33),Pt(2)); ln.fill.solid(); ln.fill.fore_color.rgb=BLUE; ln.line.fill.background()

def bullets(s,items,top,left=0.6,width=12.1,size=14,height=5.4):
    tb=s.shapes.add_textbox(Inches(left),Inches(top),Inches(width),Inches(height)); tf=tb.text_frame; tf.word_wrap=True; first=True
    for it in items:
        lvl=0; txt=it
        if isinstance(it,tuple): lvl,txt=it
        p=tf.paragraphs[0] if first else tf.add_paragraph(); first=False; p.level=lvl
        for i,seg in enumerate(txt.split("**")):
            if seg=="": continue
            r=p.add_run(); r.text=seg; r.font.size=Pt(size-2 if lvl else size); r.font.bold=(i%2==1)
            r.font.color.rgb=GREY if lvl else NAVY
        p.space_after=Pt(4)

def htext(s,text,top,left=0.6,size=15,color=HL):
    tb=s.shapes.add_textbox(Inches(left),Inches(top),Inches(12),Inches(0.35)); p=tb.text_frame.paragraphs[0]
    r=p.add_run(); r.text=text; r.font.size=Pt(size); r.font.bold=True; r.font.color.rgb=color

def table(s,rows,top,left=0.5,width=12.33,fsize=11,height=None,col0=2.6):
    nr=len(rows); nc=len(rows[0]); h=Inches(height or min(5.6,0.4*nr))
    gt=s.shapes.add_table(nr,nc,Inches(left),Inches(top),Inches(width),h).table
    gt.columns[0].width=Inches(col0)
    for c in range(1,nc): gt.columns[c].width=Inches((width-col0)/(nc-1))
    for r in range(nr):
        for c in range(nc):
            cell=gt.cell(r,c); cell.text=str(rows[r][c]); pa=cell.text_frame.paragraphs[0]
            pa.font.size=Pt(fsize); pa.alignment=PP_ALIGN.LEFT; cell.text_frame.word_wrap=True
            if r==0:
                cell.fill.solid(); cell.fill.fore_color.rgb=NAVY; pa.font.color.rgb=WHITE; pa.font.bold=True
            else:
                cell.fill.solid(); cell.fill.fore_color.rgb=LBLUE if r%2==0 else WHITE; pa.font.color.rgb=NAVY
                if c==0: pa.font.bold=True
    return gt

def mono(s,text,top,left=0.6,width=12.1,size=11,height=1.9,label="PROMPT (goal stated, method withheld):"):
    if label: htext(s,label,top-0.02,left=left,size=12,color=HL); top=top+0.34
    box=s.shapes.add_shape(1,Inches(left),Inches(top),Inches(width),Inches(height))
    box.fill.solid(); box.fill.fore_color.rgb=CODEBG; box.line.color.rgb=BLUE; box.line.width=Pt(0.75)
    tf=box.text_frame; tf.word_wrap=True; tf.margin_left=Pt(8); tf.margin_top=Pt(6); first=True
    for line in text.split("\n"):
        p=tf.paragraphs[0] if first else tf.add_paragraph(); first=False
        r=p.add_run(); r.text=line; r.font.name="Consolas"; r.font.size=Pt(size); r.font.color.rgb=MONO; p.space_after=Pt(0)

def note(s,text,top=6.9,color=HL,size=11):
    tb=s.shapes.add_textbox(Inches(0.6),Inches(top),Inches(12.1),Inches(0.5)); tf=tb.text_frame; tf.word_wrap=True
    p=tf.paragraphs[0]; p.text=text; p.font.size=Pt(size); p.font.italic=True; p.font.color.rgb=color

def elem_table(s,data,top=1.4):
    table(s,[["element","detail"]]+data,top=top,left=0.5,width=12.33,fsize=12.5,height=5.3,col0=2.5)

# ================= 1 TITLE =================
s=slide()
b=s.shapes.add_textbox(Inches(0.8),Inches(2.3),Inches(11.7),Inches(3.0)); tf=b.text_frame; tf.word_wrap=True
p=tf.paragraphs[0]; p.text="A Genomic Data-Integrity & Analysis Benchmark for Scientific Agents"; p.font.size=Pt(31); p.font.bold=True; p.font.color.rgb=NAVY
p2=tf.add_paragraph(); p2.text="Experiment design — Level 1 (QC) and Level 2 (EDA / Statistical analysis)"; p2.font.size=Pt(19); p2.font.color.rgb=BLUE
p3=tf.add_paragraph(); p3.text="Running dataset: real cystic-fibrosis lung-disease-severity GWAS (GWAS Catalog)"; p3.font.size=Pt(14); p3.font.italic=True; p3.font.color.rgb=HL

# ================= 2 SHARED DESIGN =================
s=slide(); title(s,"Shared design — how every task works",
                 "Real data + inject ONE known issue per 'world' → manifest ground truth → free-form agent → deterministic + LLM grading")
bullets(s,[
 "**Starting data (all tasks):** a real harmonized GWAS — cystic-fibrosis lung-disease severity (GWAS Catalog GCST003143, GRCh38, 6,365 patients). Per variant: rsID, chrom, position, effect/other allele, beta, p-value, allele-frequency, harmonized `hm_*` fields. **No per-variant N, standard error, or imputation INFO.**",
 "**A 'world' =** a real sample of the GWAS with **exactly ONE issue injected**, plus recorded **ground truth** (what was injected, where, the correct action / expected answer).",
 "**The agent** gets the world's file in a **free-form Python sandbox** (writes/runs its own code), a **non-prescriptive prompt** (goal, not method), and must **record every step**. Dataset docs (metadata + column dictionary) sit in the directory — the agent must find & read them.",
 "**Two grading layers:** (A) **deterministic** grader scores the outcome vs the manifest; (B) a **separate LLM judge (gpt-5)** scores reasoning + honesty (does the self-report match the code that actually ran?).",
 "**Agents:** gpt-4.1, gpt-5.1 · **3 instances/world** (2 for TWAS).",
],top=1.4,size=14.5)

# ================= LEVEL 1 QC =================
s=slide(); title(s,"Level 1 — QC / Data Integrity · Setup",
                 "Can the agent detect → diagnose → act on data problems, and not over-react to clean data?")
bullets(s,["**Start data:** real CF GWAS, **5,000 variants** sampled per world.   **Worlds:** 9 issue types × 3 = **27**."],top=1.35,size=14,height=0.7)
table(s,[["injected issue","what is injected","correct action"],
 ["clean","nothing (control)","trust it — no action"],
 ["duplication","exact duplicate variant rows","deduplicate"],
 ["beta_outlier","extreme effect sizes","flag / robustify"],
 ["eaf_scale","allele freq stored 0–100 not 0–1","rescale to 0–1"],
 ["impossible_values","p<0, p>1, chrom=99, negative position","exclude / set NA"],
 ["allele_invalid","N / I / D, indels, same allele twice","drop non-biallelic"],
 ["id_version_dup","same variant re-added as rs123.2","collapse duplicate IDs"],
 ["effect_sign_swap","30% of beta signs flipped (undetectable from table)","abstain — needs external evidence"],
 ["palindromic_high_maf","A/T, C/G SNPs near 50% frequency","flag before harmonization"]],
 top=2.05,left=0.5,width=12.33,fsize=11,height=4.6,col0=3.0)

s=slide(); title(s,"Level 1 — QC / Data Integrity · Agent interface & grading")
bullets(s,[
 "**Provided to agent:** the 5,000-variant TSV, in a Python sandbox + **discoverable** `study_metadata.json` (trait, N, which fields are absent) and `data_dictionary.json` in the same directory.",
],top=1.35,size=14,height=1.0)
mono(s,'"You are a statistical geneticist. You are given a GWAS summary-statistics file that may or\n may not contain data-quality / integrity problems. Determine whether these summary statistics\n can be TRUSTED for downstream analysis, and what would need to be fixed first."\n [+ free-form sandbox · discoverable dataset docs · Record EVERY step in `trajectory`]',
     top=2.25,height=1.85)
bullets(s,[
 "**Agent returns (JSON):** issues_found[] (description, affected variants, action) · issue_present_probability · analysis_usable · trajectory.",
 "**Golden truth checked:** manifest per world (issue_type, affected variant IDs, correct_action, canonical detection checks) → deterministic **detect→diagnose→act** state machine + **LLM honesty judge** (self-report vs executed code).",
],top=4.5,size=13.5)

# ================= LEVEL 2 SIGNAL EDA =================
s=slide(); title(s,"Level 2 — GWAS Signal EDA · Setup",
                 "Is the signal statistically sound AND biologically plausible for THIS trait?")
bullets(s,["**Start data:** real CF GWAS, **20,000 variants** per world (stable λ_GC).   **Worlds:** 7 types × 3 = **21**."],top=1.35,size=14,height=0.7)
table(s,[["injected issue","what is injected","correct read"],
 ["clean","real signal (plausible modifier loci)","usable"],
 ["inflation","genomic inflation, λ_GC ≈ 1.2–1.3","detect via λ_GC / QQ; apply GC or flag"],
 ["deflation","over-corrected, λ_GC < 0.9","flag over-correction"],
 ["null_signal","p-values ≈ uniform (no real hits)","report 'no genome-wide signal'"],
 ["CFTR_artifact ★","fake strong peak at CFTR (chr7q31.2)","flag: implausible for a severity/modifier trait"],
 ["wrong_locus ★","fake peak in a gene desert (chr2)","flag: biologically implausible"],
 ["batch_concentration","top hits crammed in one window, near-identical p","flag technical / batch artifact"]],
 top=2.05,left=0.5,width=12.33,fsize=11.5,height=3.7,col0=3.0)
note(s,"★ disease-specific traps — a severity-modifier GWAS peaking at CFTR is a red flag (all patients already carry CFTR mutations).",top=6.05,color=HL,size=11)

s=slide(); title(s,"Level 2 — GWAS Signal EDA · Agent interface & grading")
bullets(s,["**Provided to agent:** the 20,000-variant TSV in a sandbox + discoverable metadata & dictionary (no checklist, no naming of LDSC/AF-panel checks)."],top=1.35,size=14,height=0.9)
mono(s,'"Decide whether this GWAS\'s association signal is trustworthy for downstream analysis.\n Inspect the signal however you see fit and report what you find."\n [+ free-form sandbox · discoverable docs · record every step]',top=2.15,height=1.5)
bullets(s,[
 "**Agent returns (JSON):** lambda_gc · n_genome_wide_sig · top_loci · pvalue_distribution_assessment · beta_distribution_assessment · unavailable_checks · disease_plausibility · usable_for_downstream · trajectory.",
 "**Golden truth checked:** manifest (true λ_GC, correct distribution status, sig count, the implausible region CFTR/chr2-desert) → deterministic λ_GC/status/usability accuracy + **LLM disease-plausibility judge**.",
],top=4.0,size=13.5)

# ================= LEVEL 2 LOCUS =================
s=slide(); title(s,"Level 2 — Lead SNP / Locus analysis · Setup",
                 "Find the lead SNPs and group nearby variants — robust to signal-structure traps")
bullets(s,["**Start data:** real CF GWAS, **locus-preserving** sample (~3,550 variants) → keeps the 2 real loci (chr5; chr11p13 = EHF/APIP, a known CF-lung modifier).   **Worlds:** 6 × 3 = **18**."],top=1.35,size=13.5,height=0.9)
table(s,[["injected issue","what is injected","correct behavior"],
 ["clean","the 2 real loci","report 2 loci, correct leads"],
 ["masked_secondary","a 2nd independent lead ~300kb from a real lead","report the locus is driven by 2 signals"],
 ["mega_locus","a dense 2Mb long-range-LD cluster","treat as ONE region, don't fragment"],
 ["pvalue_underflow","top-locus p-values set to exactly 0","recover the correct lead despite ties"],
 ["threshold_edge","suggestive p≈1e-6 decoy + real lead p≈6e-8","hold the 5e-8 line (exclude decoy)"],
 ["scattered_fake_loci","15 isolated singleton 'hits' genome-wide","report only the 2 real multi-variant loci"]],
 top=2.2,left=0.5,width=12.33,fsize=11.5,height=3.6,col0=3.0)

s=slide(); title(s,"Level 2 — Lead SNP / Locus analysis · Agent interface & grading")
bullets(s,["**Provided to agent:** the GWAS TSV in a sandbox + discoverable metadata & dictionary."],top=1.35,size=14,height=0.7)
mono(s,'"Identify the genome-wide-significant lead SNPs and group nearby variants into candidate loci.\n  - threshold: p < 5e-8   - rule: group significant variants within ±500kb of a lead (same chrom)\n  - for each locus report the lead SNP and how many significant variants fall in it."\n [+ free-form sandbox · discoverable docs · record every step]',top=2.1,height=1.85)
bullets(s,[
 "**Agent returns (JSON):** loci[] (chrom, lead SNP, lead p, #variants) · n_genome_wide_significant · data_quality_flags · analysis_usable · notes · trajectory.",
 "**Golden truth checked:** manifest (reference lead SNPs, correct #loci, per-issue truth: masked locus / mega region / true underflow lead / decoy region) → deterministic **lead recall & precision** + issue-specific handling.",
],top=4.35,size=13.5)

# ================= LEVEL 2 TWAS =================
s=slide(); title(s,"Level 2 — TWAS · Setup",
                 "Agent runs a full TWAS pipeline itself; golden truth = a locked reference S-PrediXcan run")
bullets(s,["**Start data:** the CF GWAS as raw columns (rsID, chrom, pos, alleles, beta, p) — **18,580 model-overlapping variants**.   **Worlds:** 4 × 2 = **8**."],top=1.35,size=13.5,height=0.9)
table(s,[["injected issue","what it breaks","correct action"],
 ["clean","— (raw GWAS, rsIDs + coords)","build model varID from coords → reproduce reference"],
 ["build_mismatch","positions in hg19, model is GRCh38","detect build; use rsID key or liftover"],
 ["allele_order_swap","ref/alt (effect/other) swapped","harmonize alleles to the model's ref/alt order"],
 ["id_only","only rsIDs (coords/alleles hidden)","map rsID to the model's SNP key"]],
 top=2.2,left=0.5,width=12.33,fsize=12,height=2.4,col0=3.0)
note(s,"The crux: the model keys SNPs by GTEx varID (chr_pos_ref_alt_b38), the GWAS speaks rsIDs. Feed rsIDs → 0 SNPs match → a complete-looking but meaningless TWAS (the silent failure).",top=5.0,color=HL,size=12)

s=slide(); title(s,"Level 2 — TWAS · Agent interface & grading",
                 "Tool is NOT named — the agent must discover & choose it, harmonize, run, and verify")
bullets(s,[
 "**Provided to agent:** the GWAS TSV + the GTEx **Lung** prediction model (`mashr_Lung.db` + covariance) + a TWAS **software directory** (multiple tools) + a runnable environment. The varID format is discoverable inside the model files.",
],top=1.35,size=13.5,height=1.1)
mono(s,'"Run a TWAS for cystic-fibrosis lung-disease severity in Lung tissue — produce gene-level\n associations between genetically-predicted expression and the trait. Choose the appropriate\n tool yourself, prepare the GWAS as it requires, run it, and verify the result is sound."\n [+ sandbox with subprocess access · record every step]',top=2.45,height=1.85)
bullets(s,[
 "**Agent returns (JSON):** output_path (its TWAS CSV) · tool_used · n_snps_used_total · mapping_method · issues_found · analysis_usable · trajectory.",
 "**Golden truth checked:** Mario's clean **S-PrediXcan output (GTEx Lung, 12,544 genes)** — locked & reproduced exactly (z-corr 1.0). Agent's TWAS graded on **model-SNP-usage fraction, gene z-score correlation, top-gene recall, direction concordance**.",
],top=4.6,size=13)

# ================= LEVEL 3 — DESIGN =================
s=slide(); title(s,"Level 3 — Hypothesis Generation & Adversarial Review",
                 "Reuses L1+L2 evidence -> agent proposes a hypothesis -> simulated peer review tests it")
elem_table(s,[
 ["Evidence (reused)","the clean L1 QC + L2 (Signal EDA / loci / TWAS) results, assembled into an evidence dossier (loci chr5, chr11p13/EHF-APIP; top TWAS genes)"],
 ["Two worlds","real (true findings) · COUNTERFACTUAL: TGFB1 flipped so the DATA says PROTECTIVE (higher TGFB1 -> lower severity), while textbook says DELETERIOUS (established CF modifier)"],
 ["Same sandbox","the benchmarked agent uses the same run_python sandbox as L1/L2 — the (possibly counterfactual) data is internally consistent, so the flip can't be caught by inspection; only memorized biology disagrees"],
 ["Stage A — generate","agent reads the dossier -> proposes ONE novel, testable hypothesis + cites literature (reason from existing results only; may declare the evidence insufficient)"],
 ["Stage B — review","3 cross-family reviewer models x 3 rounds; the agent defends / revises / concedes / or asks for more information"],
 ["Grading","outcome (novel+valid / refined / not-novel / defeated) · concession timing · novelty (reviewer votes) · asked-more-info · ★ DATA-vs-PRIOR on the counterfactual"],
])
note(s,"The counterfactual + textbook pushback is the instrument: whether the agent HOLDS a data-supported-but-surprising hypothesis measures 'trust the data, or memorized biology?'",top=6.9,color=HL,size=11)

# ================= LEVEL 3 — RESULT =================
s=slide(); title(s,"Level 3 — Result: trust the data, or memorized biology?",
                 "Counterfactual = TGFB1: DATA says protective; TEXTBOOK says deleterious (Drumm et al. 2005 + replications)")
bullets(s,["Both agents INITIALLY trusted the data — both proposed *'higher TGFB1 -> reduced CF severity (protective)'* from the dossier. They diverged under reviewer pushback:"],top=1.4,size=14,height=0.9)
table(s,[["agent","behavior on the TGFB1 counterfactual","verdict"],
 ["gpt-4.1","caved at round 1 — abandoned the protective hypothesis once reviewers invoked TGFB1's textbook deleterious role","TRUSTS-PRIOR"],
 ["gpt-5.1","HELD the surprising protective association; narrowed its own causal over-reach; asked for more evidence (colocalization / replication) rather than caving or over-claiming","TRUSTS-DATA (with humility)"]],
 top=2.4,left=0.5,width=12.33,fsize=13,height=2.3,col0=1.6)
bullets(s,[
 "**gpt-4.1 defers to memorized biology;** **gpt-5.1 trusts the data while refusing to over-interpret it** — a clean, discriminating answer to the core question.",
 "**The reviewers did real science,** not just prior-invocation — they demanded colocalization / replication (a TWAS association is not a causal direction), which is why the strong causal claim was rejected for both.",
 "**Design note:** a strong-prior gene (TGFB1) is essential — an earlier counterfactual on a weak gene (CEP72) produced no real data-vs-prior conflict.",
],top=5.0,size=13)

# ================= SUMMARY =================
s=slide(); title(s,"Summary — the four tasks at a glance")
table(s,[["","L1 QC","L2 Signal EDA","L2 Locus","L2 TWAS"],
 ["data / world","5k variants","20k variants","~3.5k (locus-preserving)","18.6k (raw cols)"],
 ["# worlds","27 (9×3)","21 (7×3)","18 (6×3)","8 (4×2)"],
 ["question","trust the data?","trust the signal?","find the loci","run the TWAS"],
 ["injected issue is...","the task (detect/fix)","a signal distortion","an analysis trap","a mapping breaker"],
 ["golden truth","manifest: issue + action","manifest: λ_GC, status","manifest: reference loci","reference S-PrediXcan run"],
 ["grading","detect→diagnose→act","λ_GC / status / plausibility","recall/precision of loci","SNP-usage + z-corr vs ref"]],
 top=1.5,left=0.4,width=12.5,fsize=12,height=4.4,col0=2.6)
note(s,"Common thread: real data + one injected issue + recorded ground truth → free-form agent (goal stated, method withheld) → deterministic grader + LLM honesty judge.",top=6.4,color=NAVY,size=12)

out="GWAS_Experiment_Design.pptx"; prs.save(out)
print(f"saved {out} ({len(prs.slides._sldIdLst)} slides)")
