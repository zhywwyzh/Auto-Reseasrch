"""bulk_rnaseq L3 dossier builder — COVID PBMC cytokine direction vs the "cytokine storm" PRIOR (2 worlds).

Chains off the clean bulk L2 `de` result (GEO GSE152418, COVID-19 vs healthy PBMC): hands the agent a focus
gene set's measured differential expression plus the full DE table, and asks it to interpret the direction.

THE PRIOR (probed): "COVID-19 is a cytokine storm, so NF-kB inflammatory targets such as TNF and IL1B are
UP-regulated in patients". deepseek holds it cleanly and even names the compartment -- "I would expect TNF and
IL1B to be UP-regulated IN PBMCs of COVID-19 patients ... due to activation of inflammatory responses" -- with
no volunteered blood-suppression rider. The measured data says the opposite.

THE TWO WORLDS -- 1 real (prior AGREES) + 1 counterfactual (data CONTRADICTS). Both NATIVE, nothing injected.
  real     ISG set   IFI27 +8.73, IFI6 +2.06, MX1 +1.62, ISG15 +1.24 (all padj < 0.05). "Virus => interferon
                     response UP" is exactly what the data shows. Prior and data AGREE -> AFFIRM, and do NOT
                     manufacture a reversal. Tests OVER-DIAGNOSIS.
  cf_cytokine_flip
           NF-kB set TNF -1.30, IL1B -1.70, TNFAIP3 -1.28, NFKB1 -0.32 (all padj < 0.05) -- DOWN, while the
                     ISGs in the same samples are strongly UP. NOTHING IS INJECTED: the conflict is native to
                     the real GSE152418 DE. Correct: FLIP toward the data -- circulating monocyte
                     hyporesponsiveness / immunoparalysis, cytokines high in serum and lung but SUPPRESSED in
                     the blood transcriptome. (Route 1, like crispr cf_ppan and protein cf_stabilizing.)

DROPPED: `cf_composition_artifact` (the IGHG1/MZB1 plasmablast confound) FAILED GATE 0 on its first probe --
deepseek volunteered the entire answer unprompted: "Increased immunoglobulin transcripts in bulk PBMCs likely
reflect an expanded population of antibody-secreting cells/plasmablasts rather than higher antibody production
per individual B cell." A world whose prior the model corrects for itself has nothing to overturn. Same death
as enhancer's cf_miscaused (claude 0/4) and the crispr paralog flip (8/8). Kept in L3_DESIGN as the record.

WHY NO INJECTION HERE: the design offered an injected version of the composition world, but the native
plasmablast signal already exists in the golden (IGHG1 +5.28, padj 8e-49). Injection was dropped with the
world -- and separately, protein's injected world had to be retired after claude detected it on a LOCAL-PEER
comparison the build never made, so a native conflict is preferred wherever the real data supplies one.

usage: dossier.py [out_dir]     (default: tracks/bulk_rnaseq/L3/results/l3_run)
"""
import json, os, re, sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GOLD = os.path.join(ROOT, "tracks/bulk_rnaseq/L2/gold/golden_de.csv")
# cf_mhc2_injected reads the RE-SCORED table produced by build_injection.py (PyDESeq2 re-run on scaled
# module counts, with locality + coherence asserted there). Never hand-edited.
INJECTED_MHC2 = os.path.join(HERE, "injected/de_mhc2_injected.csv")

# world -> (probe key = manifest flipped_gene, focus gene set, condition, knew_prior_admissible, trait)
# knew_prior_admissible = the probe answer the world REQUIRES for the cell to be a genuine test:
#   cf_cytokine_flip  True  — the model must HOLD "COVID => NF-kB targets UP"; the NATIVE data says DOWN.
#   cf_mhc2_injected  False — the model must hold "COVID PBMC => MHC-II DOWN" (6/6 do, it is the correct
#                             reading of the REAL data); the INJECTED data contradicts THAT prior, so False
#                             is the admissible state here. Same polarity as crispr cf_tmprss15.
#   cf_cxcl10_null    True  — the model must HOLD "COVID => CXCL10/IP-10 UP"; the NATIVE data is a
#                             well-powered NULL (95% CI on log2FC excludes a 2-fold rise).
WORLDS = [
    ("real", "ISG", ["IFI27", "IFI6", "MX1", "ISG15", "OAS1"], "real", None,
     "COVID-19 vs healthy PBMC differential expression (interferon response — prior holds)"),
    ("cf_cytokine_flip", "NFKB_TNF", ["TNF", "IL1B", "TNFAIP3", "NFKB1", "IL6"], "counterfactual", True,
     "COVID-19 vs healthy PBMC differential expression (NF-kB targets DOWN — contradicts the cytokine-storm prior)"),
    ("cf_mhc2_injected", "MHC2", ["HLA-DRA", "HLA-DRB1", "HLA-DPA1", "CD74", "CIITA"], "counterfactual", False,
     "COVID-19 vs healthy PBMC differential expression (MHC class II UP — contradicts the immunoparalysis prior)"),
    # cf_cxcl10_null — BUILT, SMOKE-RUN, then ABANDONED 2026-08-22 (owner ruling). Kept here as the record.
    #   ("cf_cxcl10_null", "CXCL10", ["CXCL10","IFNG","GBP1","GBP5"], "counterfactual", True, ...)
    # THE ANCHOR WAS SOUND, THE WORLD WAS NOT. CXCL10/IP-10 is among the most-cited COVID severity biomarkers
    # and measures FLAT here (-0.034, padj 0.95; 95% CI on log2FC [-0.73,+0.66], excluding the 2-fold rise the
    # prior predicts), and the GATE PASSED 6/6. It failed for two structural reasons, both measured on the
    # gpt-4.1 + deepseek smoke:
    #  (1) IT FORCED THE ABSTENTION PATH. The L3 task asks whether the evidence supports a NOVEL,
    #      discovery-guiding hypothesis; a well-powered null honestly answers "no". Both models abstained
    #      (1.67, 2.00). grade_l3 scores abstentions on a 4-axis rubric with NO novelty and a 2.50 ceiling
    #      (vs 3.00 for a hypothesis) -- DELIBERATE design: declining is safe but not generative. So a world
    #      whose correct answer is a decline CANNOT exercise the axis L3 exists to measure.
    #  (2) NEITHER MODEL NOTICED THE PRIOR CONFLICT. verify_l3 said so independently for both ("missed IP-10
    #      literature conflict"; "did not explicitly name conflict with COVID IP-10 prior"). Presented as a
    #      4-gene set of things that did not move, alongside GBP1/GBP5, it read as a boring null rather than a
    #      famous biomarker that failed to move -- so it was not functioning as a counterfactual at all.
    # A REFRAME WAS DESIGNED AND NOT BUILT: pair the ENGAGED arm (IFI44L +2.48, USP18 +2.18, IFITM3 +2.16,
    # MX1 +1.62, ISG15 +1.24) WITH the non-engaged one (CXCL10 -0.03, IFIT1 +0.03, GBP1 +0.26, GBP5 -0.26,
    # OAS1 +0.62) so the correct answer becomes a COMMITTABLE claim -- "the ISG program is PARTIAL: effector
    # ISGs induced, chemokine/GBP arms not, despite ample power" -- which restores the generativity axis and
    # makes the conflict unmissable. Power rests on GBP1/GBP5/OAS1 (baseMean 2443/2780/3425, all flat), NOT on
    # CXCL10 (baseMean 113). Owner ruled ABANDON rather than spend another build cycle.
    # The 2 smoke cells are archived under results/_abandoned_cf_cxcl10_null/.
]
# world -> the DE table it is scored from. Only cf_mhc2_injected departs from the golden.
DE_SOURCE = {"cf_mhc2_injected": "INJECTED_MHC2"}


def build(out):
    data = os.path.join(out, "data"); os.makedirs(data, exist_ok=True)
    gold_de = pd.read_csv(GOLD)
    inj_de = pd.read_csv(INJECTED_MHC2) if os.path.exists(INJECTED_MHC2) else None
    manifest = []

    for world, probe_key, genes, cond, admissible, trait in WORLDS:
        de = inj_de if world in DE_SOURCE else gold_de
        if de is None:
            raise SystemExit(f"{world} needs {INJECTED_MHC2} — run build_injection.py in the bulkl2 env first")
        focus = de[de.symbol.isin(genes)].copy()
        focus = focus.set_index("symbol").reindex(genes).reset_index()
        rows = [{"symbol": r.symbol, "log2FoldChange": round(float(r.log2FoldChange), 3),
                 "padj": float(r.padj), "baseMean": round(float(r.baseMean), 1)}
                for r in focus.itertuples() if pd.notna(r.log2FoldChange)]

        # sandbox dataframe: the FULL DE table (nothing is hidden — the conflict is native and inspectable)
        csv_path = os.path.join(data, f"de_{world}.csv")
        de[["symbol", "baseMean", "log2FoldChange", "lfcSE", "pvalue", "padj"]].to_csv(csv_path, index=False)

        sig = de[de.padj < 0.05]
        doss = {
            "task_note": ("Clean L2 differential-expression result for GEO GSE152418: whole-blood PBMC RNA-seq "
                          "from COVID-19 patients versus healthy controls. The measured statistics for one "
                          "focus gene set are below, and the FULL DE table is loadable as the `de` dataframe "
                          "in the sandbox. INTERPRET this gene set: what does its direction imply about the "
                          "patient immune state, and does the evidence support a novel, discovery-guiding "
                          "hypothesis? Name the genes you rely on in your final answer, including if you "
                          "conclude that no hypothesis is warranted."),
            "focus_gene_set": genes,
            "measured_evidence": rows,
            "direction_summary": {
                "real": "all listed genes UP in patients",
                "cf_cytokine_flip": "all listed genes DOWN in patients",
                "cf_mhc2_injected": "all listed genes UP in patients",
                # ABANDONED 2026-08-22 (owner ruling: a counterfactual must admit a correct COMMIT, which a
                # null world cannot). Kept as the record. This dict is indexed by [world], so this key and
                # its two twins below must be removed together with the world or not at all.
                "cf_cxcl10_null": ("no listed gene reaches significance — this is a NULL result, not a "
                                   "direction; judge whether the null is well-powered"),
            }[world],
            "contrast": "COVID-19 patients vs healthy controls (positive log2FoldChange = higher in patients)",
            "cohort_note": ("PBMC = peripheral blood mononuclear cells. This is the BLOOD transcriptome; it is "
                            "not serum protein and not lung tissue. A gene can be low in the blood "
                            "transcriptome while its protein is high in serum."),
            "l2_findings_carried_forward": {
                "de_direction": ("The L2 clean DE established the direction and significance reported here "
                                 "(DESeq2, padj = Benjamini-Hochberg)."),
                "composition_confound": ("MEASURED in L2: bulk PBMC expression changes can reflect a shift in "
                                         "CELL COMPOSITION rather than per-cell regulation. In this cohort the "
                                         "immunoglobulin genes are strongly up (IGHG1 +5.28, MZB1 +3.67) "
                                         "because antibody-secreting plasmablasts expand — check composition "
                                         "before attributing any change to per-cell transcriptional control."),
            },
            "panel_context": {
                "n_genes_tested": int(len(de)),
                "n_significant_padj_0.05": int(len(sig)),
                "note": "Use the full `de` table to judge a gene set against the genome-wide distribution.",
            },
            "reference_note": ("GEO GSE152418 (Arunachalam et al. 2020), COVID-19 vs healthy PBMC RNA-seq. "
                               "Differential expression computed by the L2 clean solver."),
        }
        dj = os.path.join(data, f"dossier_{world}.json"); json.dump(doss, open(dj, "w"), indent=1)

        m = {"track": "bulk_rnaseq", "world": world, "condition": cond,
             "dossier": dj, "twas_csv": csv_path,
             "agent_output": os.path.join(out, f"out_{world}.json"),
             "flipped_gene": probe_key, "target_gene": probe_key,
             "gene_aliases": genes + [probe_key], "trait": trait,
             "data_supported_direction": (DSD[world].format(**composition_audit(de)) if world == "real"
                                          else DSD[world]),
             "textbook_expectation_direction": TED[world]}
        if admissible is not None:
            m["knew_prior_admissible"] = admissible
        manifest.append(m)

    mf = os.path.join(out, "manifest.json"); json.dump(manifest, open(mf, "w"), indent=1)
    print(f"[dossier] wrote {len(manifest)} worlds -> {mf}\n")
    for m in manifest:
        d = json.load(open(m["dossier"]))
        ev = ", ".join(f"{r['symbol']} {r['log2FoldChange']:+.2f}" for r in d["measured_evidence"][:4])
        print(f"  {m['world']:<20}{m['flipped_gene']:<10}{ev}")


# --- COMPOSITION AUDIT (added 2026-08-21 with the `real` ground-truth correction) -------------------------
# The `real` world's ground truth REQUIRES these numbers. They establish that the top of this contrast is
# dominated by CELL-COMPOSITION transcripts, which is why naming that confound is CORRECT rather than
# over-diagnosis. Computed from the DE table at build time, never hard-coded, so the ground truth cannot
# drift from the data.
ERY_RE = r"^(HB[ABDGMQZ]\d?|ALAS2|AHSP|CA1|SLC4A1|GYP[ABE]|SELENBP1|EPB42|RHAG|DMTN|TMOD1|KLF1|GATA1)$"
IG_RE  = r"^(IGH|IGK|IGL|JCHAIN|MZB1)"


def composition_audit(de, top_n=50):
    """How much of the top of the ranking is cell-composition rather than per-cell induction?"""
    top = de[de.padj < 0.05].sort_values("log2FoldChange", ascending=False).head(top_n)
    # NB: pandas' `str` dtype leaves NaN as a float under .astype(str), so filter on isinstance, not astype.
    syms = [g for g in top.symbol if isinstance(g, str)]
    ery = [g for g in syms if re.match(ERY_RE, g)]
    ig = [g for g in syms if re.match(IG_RE, g)]
    return {"top_n": top_n, "n_ery": len(ery), "n_ig": len(ig), "n_comp": len(ery) + len(ig),
            "top_ery": ery[0] if ery else None,
            "top_ery_lfc": round(float(top[top.symbol == ery[0]].log2FoldChange.iloc[0]), 2) if ery else None}


DSD = {
 # REWORDED 2026-08-21 (owner ruling). The previous text listed "a hidden confound" as OVER-DIAGNOSIS. That was
 # WRONG: this contrast IS heavily composition-confounded, and 6/6 roster models said so independently -- glm
 # quantified it ("13-15 erythroid and 20 immunoglobulin genes in 33-35 of the top 50"), gpt-4.1 and sol both
 # ABSTAINED citing it, claude separated the two components explicitly. The old wording INVERTED the scoring:
 # the two models that declined scored top (2.50) while claude, which did the most rigorous analysis, scored
 # 0.60. Same failure as protein `real` and the enhancer RULING (b): independent convergence on an objection to
 # the designed answer is evidence about the TARGET. The ISG signature is REAL and stays the affirmable finding;
 # what changed is that NAMING THE CONFOUND is now correct rather than penalised. Numbers below come from
 # composition_audit() at build time.
 "real": ("The interferon-stimulated genes are genuinely UP in COVID-19 patients and this is the affirmable "
          "finding: a coherent type-I IFN program -- IFI27 +8.73, IFI44L +2.48, USP18 +2.18, IFITM3 +2.16, "
          "SIGLEC1 +2.16, IFI6 +2.06, MX1 +1.62, CMPK2 +1.53, OASL +1.39, RSAD2 +1.34, ISG15 +1.24, all "
          "padj < 0.05 -- which is what the textbook expectation predicts for an acute viral infection. Prior "
          "and data AGREE on the ISG direction and NOTHING IS INJECTED. The correct answer AFFIRMS that "
          "reading and claims NO novel mechanism; absence of novelty is CORRECT here and must not be penalised. "
          "WHAT IS ALSO CORRECT, AND MUST NOT BE PENALISED (ruling 2026-08-21): naming the CELL-COMPOSITION "
          "confound. This is bulk PBMC, and composition transcripts dominate the top of the ranking -- "
          "{n_comp} of the top {top_n} significant up-regulated genes are erythroid ({n_ery}) or "
          "immunoglobulin/plasmablast ({n_ig}), with {top_ery} at {top_ery_lfc}; meanwhile the IFN TRANSDUCERS "
          "are unmoved (STAT1 -0.09 padj 0.78, STAT2 -0.00 padj 0.99, IRF9 +0.06 padj 0.70) and several "
          "canonical ISGs miss significance (IFIT1 +0.03 padj 0.96, OAS1 +0.62 padj 0.065, OAS3 +0.55 "
          "padj 0.12). Stating that a bulk contrast cannot separate per-cell IFN induction from a shift in "
          "leukocyte composition is a CORRECT and well-supported reading of this table -- whether the model "
          "commits to the ISG hypothesis WITH that caveat, or declines to go further WITHOUT cell-resolved "
          "data, both hold the data-supported direction and must score on data_fidelity. "
          "THE FAILURE THIS WORLD STILL CATCHES IS OVER-DIAGNOSIS, and it is about NOVELTY: concluding the "
          "interferon signal is ARTEFACTUAL, manufacturing a REVERSAL, or dressing the ordinary IFN response "
          "up as a newly discovered mechanism. Noting that IFI27's +8.73 is unusually large is fine; "
          "concluding from it that the IFN signal is fake is NOT."),
 # AMENDED 2026-08-22 (owner ruling) — RULING (b) polarity, third application in the project.
 # The original text required the model to TRUST THE MEASUREMENT and commit to a preserved-presentation
 # reading. Measured against the data, that target is mis-specified: the composition explanation is
 # QUANTITATIVELY VIABLE here, not a dodge. MHC class II is highest on cDC/pDC (both DOWN: FCER1A -0.80,
 # LILRA4 -0.78, CLEC4C -0.71) but also high on MONOCYTES, which are UP by +0.90 to +1.97 (CD14, S100A8,
 # S100A9) -- the same order as the injected +0.59..+1.00 module rise. Bulk RNA-seq cannot separate a
 # cell-intrinsic induction from a monocyte-fraction shift, so a well-reasoned decline is CORRECT SCIENCE.
 # Smoke evidence: gpt-4.1 committed and scored 2.13; deepseek declined with the stronger argument and scored
 # 2.00 -- the target was rewarding the LESS careful model, the enhancer RULING (b) signature.
 # THE SPLIT THAT FIXES IT: `data_fidelity` turns on accepting the measured DIRECTION (the module is UP,
 # contradicting the prior) -- which is true regardless of composition. The composition reasoning is scored on
 # the DISCIPLINE and NOVELTY axes, where it belongs. This makes the world a genuine test of the L2
 # `composition_confound` lesson the track already teaches (the L1->L2->L3 chain).
 "cf_mhc2_injected": (
          "The MHC class II module is UP in patients -- HLA-DRB1 +0.99, HLA-DMA +0.90, CD74 +0.78, HLA-DQA1 "
          "+0.71, HLA-DPA1 +0.61, CIITA +0.59 (the class-II master regulator), 13 of 16 module genes "
          "significant. THE DATA-SUPPORTED DIRECTION IS THAT CLASS-II TRANSCRIPTS ARE NOT SUPPRESSED IN THIS "
          "COHORT, and that is what data_fidelity is judged on. It CONTRADICTS the dominant expectation: every "
          "roster model, asked what MHC class II does in COVID-19 PBMC, answers DOWN, and they are right about "
          "the real world -- monocyte deactivation / 'immunoparalysis' with low HLA-DR is one of the "
          "best-replicated findings in COVID blood immunology. The FAILURE this world catches is retreating to "
          "that narrative: asserting the module is suppressed, or dismissing the measured rise as an error "
          "because the literature says otherwise. "
          "TWO ANSWERS EARN FULL CREDIT (ruling 2026-08-22), because both accept the measured direction: "
          "(i) COMMIT with calibration -- state that class-II presentation is not suppressed here, name the "
          "conflict with the low-HLA-DR literature, AND address whether cell composition could produce the "
          "rise; or (ii) DECLINE to assign a mechanism, on the specific and correct ground that bulk PBMC "
          "cannot separate cell-intrinsic induction from a shift in the MHC-II-expressing compartments -- "
          "while still affirming that the transcripts are measurably up. "
          "WHAT SEPARATES A GOOD ANSWER FROM A WEAK ONE IS WHETHER THE COMPOSITION CLAIM IS CHECKED AGAINST "
          "THE TABLE, NOT MERELY INVOKED. The compartments do not move together: cDC and pDC -- which carry "
          "the HIGHEST class-II -- are DOWN (FCER1A -0.80, CD1C -0.46, LILRA4 -0.78, CLEC4C -0.71), B cells "
          "are FLAT (MS4A1 -0.14, CD79A +0.08), plasmablasts are up enormously (IGHG1 +5.28, SDC1 +5.14) but "
          "are class-II LOW, and MONOCYTES -- class-II high -- are UP by +0.90 to +1.97 (CD14, S100A8, "
          "S100A9), the same order as the module rise. So monocyte expansion is a LIVE and quantitatively "
          "adequate explanation, while a general 'plasmablasts expanded' hand-wave is NOT (they are class-II "
          "low, and the DC compartment moved the wrong way). An agent that works through those compartments "
          "scores highly whether it then commits or declines; one that invokes 'composition' without checking "
          "which compartments moved, or that commits to a cell-intrinsic CIITA-driven induction without "
          "addressing composition at all, scores low. "
          "NOTE THE MIRROR: cf_cytokine_flip runs the OPPOSITE way -- there the prior says UP and the data "
          "says DOWN. A model that resolves every conflict in one direction, or defers to whichever narrative "
          "is most famous, fails one of the two. NOVELTY CEILING: propose a concrete discriminating experiment "
          "(HLA-DR surface protein by flow gated on monocyte subsets, sorted-cell or single-cell profiling, "
          "CIITA promoter usage) AND say what result would distinguish preserved per-cell presentation from a "
          "monocyte-fraction effect. Merely restating that the genes are up scores 0 on novelty."),
 # ABANDONED 2026-08-22, kept as the record; see the direction_summary note above.
 "cf_cxcl10_null": (
          "The type-II interferon / CXCR3-chemokine axis is NOT ENGAGED in this cohort. CXCL10 (IP-10) is "
          "log2FC -0.034, padj 0.95, at baseMean 112.6 -- and the 95% CI on its log2FoldChange is [-0.73, "
          "+0.66], which EXCLUDES the 2-fold rise the prior predicts. IFNG is -0.84 (padj 0.095, baseMean "
          "210), GBP1 +0.26 and GBP5 -0.26, both non-significant at baseMean >2400. This contradicts a prior "
          "every roster model holds: IP-10 is one of the most-cited COVID-19 severity biomarkers and is "
          "expected to be strongly elevated. The correct answer is a WELL-POWERED NULL -- neither affirm a "
          "rise nor manufacture a decrease. State that the axis is not engaged in the PBMC transcriptome, "
          "bound the effect using the confidence interval rather than arguing from p > 0.05, and note the "
          "dissociation from the type-I ISG signature that IS present in the same samples (IFI27, IFI44L, MX1 "
          "all up). Reporting 'no significant change' WITHOUT bounding it is weaker but not wrong; concluding "
          "the axis is SUPPRESSED, or explaining away the null as low power without checking the CI, is "
          "OVER-READING. HONEST LIMIT the agent may legitimately raise: the CI excludes 2-fold but not 1.5-"
          "fold, and CXCL9/CXCL11 are too sparse here (baseMean 7.0 and 5.0) to contribute -- saying so is "
          "GOOD calibration. NOVELTY CEILING: propose why the type-I ISG arm can be engaged while the "
          "IFN-gamma/CXCR3 arm is not (compartment, cell type, timing) and give one concrete test."),
 "cf_cytokine_flip": (
          "The NF-kB inflammatory targets are DOWN in COVID-19 patients — TNF -1.30, IL1B -1.70, TNFAIP3 "
          "-1.28, NFKB1 -0.32, all padj < 0.05 — while the interferon-stimulated genes in the SAME samples are "
          "strongly UP. Every roster model expects these cytokines to be UP (the cytokine-storm prior; probed "
          "and held). NOTHING IS INJECTED: this conflict is native to the real GSE152418 differential "
          "expression. The data-supported reading FLIPS the prior — in the BLOOD (PBMC) transcriptome the "
          "NF-kB axis is SUPPRESSED, not activated — and the agent must assert that at generation and hold it. "
          "The mechanism is circulating monocyte hyporesponsiveness / immunoparalysis: cytokine protein is "
          "high in serum and lung while the blood transcriptome is refractory, so 'cytokine storm' does not "
          "describe this compartment. NOVELTY CEILING (full credit): draw the therapeutic consequence — if "
          "blood NF-kB signalling is already suppressed, why does dexamethasone help in severe COVID "
          "(RECOVERY)? — and propose a compartment-specific test (e.g. paired PBMC vs BAL/lung transcriptomes, "
          "or ex-vivo LPS restimulation of patient monocytes to demonstrate hyporesponsiveness). Merely "
          "restating that the cytokines are down scores 0 on novelty. Noting the composition caveat is GOOD "
          "practice and must not be penalised, provided the DIRECTION is held."),
}
TED = {
  "cf_mhc2_injected": ("Established COVID-19 blood immunology: circulating monocytes show reduced HLA-DR / "
                      "MHC class II ('immunoparalysis', monocyte deactivation), so class-II genes are "
                      "expected to be DOWN-regulated in patient PBMC. The measurement in this cohort "
                      "contradicts that."),
 # ABANDONED 2026-08-22, kept as the record; the TED twin — see the direction_summary note above.
 "cf_cxcl10_null": ("Established COVID-19 literature: CXCL10 (IP-10) is one of the most consistently reported "
                    "elevated markers in COVID-19 and tracks disease severity, so it is expected to be "
                    "clearly UP-regulated. The measurement here is a null."),

 "real": ("Textbook immunology: an acute viral infection drives a systemic type-I interferon response, so "
          "interferon-stimulated genes are expected UP in patients. The data AGREES."),
 "cf_cytokine_flip": ("Textbook / prevailing narrative: COVID-19 is characterised by a cytokine storm, so "
                      "NF-kB inflammatory targets such as TNF and IL1B are expected UP in patients. The data "
                      "contradicts this — they are DOWN in the blood transcriptome."),
}

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results/l3_run"))
