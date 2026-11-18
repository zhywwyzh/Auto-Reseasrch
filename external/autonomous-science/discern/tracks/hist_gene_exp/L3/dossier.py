"""hist_gene_exp L3 dossier builder — BIVALENT CHROMATIN vs the "H3K4me3 => expressed" PRIOR (3 worlds).

Chains off the clean L2 `quantify` result: hands the agent one focus gene's promoter chromatin (input-normalized
H3K4me3 and H3K27me3, plus the RAW coverage both were derived from) and its measured expression, then asks it to
interpret the combination.

THE PRIOR (probed, and it SURVIVES GATE 0 — the one remaining per-fact flip in the project):
  "strong promoter H3K4me3 => the gene is expressed". Probed with prediction-eliciting phrasing on the 6-model
  roster: DUSP4 6/6, DEPTOR 6/6, PBX3 6/6 hold it. Contrast enhancer conservation (0/6) and the crispr paralog
  flip (8/8 False), both of which died because models VOLUNTEER the rider. Here a generic "H3K4me3 isn't always
  active" caveat appended to an *expressed* prediction is NOT gene-specific knowledge and does NOT exclude the
  cell — the probe adjudicates the REASON, not a keyword (see prior_probe.py).

THE THREE WORLDS — 1 native + 2 GWAS-style injected, and the two injections are MIRROR IMAGES:
  real     DUSP4   NATIVE, nothing injected. H3K4me3 3.98 (strong) BUT input-normalized H3K27me3 +1.22 over a
                   +/-10 kb window, and expression is near-zero. A genuine BIVALENT/poised promoter.
                   Correct: FLIP toward the data — the K4me3 does NOT imply expression here; propose
                   poised-chromatin + a PRC2/EZH2-inhibition reactivation experiment.
  cf_textbook_holds
           DEPTOR  INJECTED — the real K27me3 is STRIPPED (ChIP counts set to the input level so the
                   input-normalized ratio collapses to ~0) and expression is raised to an active level.
                   The prior now HOLDS. Correct: AFFIRM — do not flip just because the last gene was bivalent.
  cf_artifact_bivalency
           UFD1    INJECTED — spurious K27me3 RAW coverage is ADDED, matched by an equal rise in the INPUT
                   control, so raw K27me3 looks substantial while the input-normalized ratio stays ~0.
                   Correct: VERIFY, then DON'T flip — input-normalize and reject the apparent bivalency.

WHY THIS SET: one L2 skill, three different correct outcomes. The same `no_input_normalization` /
`broad_mark_narrow_default` competence that lets a model SEE the true bivalency in `real` is what lets it REJECT
the fake bivalency in `cf_artifact`. An always-affirm model fails `real`; an always-flip-on-K27me3 model fails
`cf_artifact`; a model that flips on raw coverage without normalizing fails `cf_artifact` specifically.

INJECTION DISCIPLINE (per L3_DESIGN "cf-world-two-routes", the GWAS `cf_zscore` construction transposed from
z = effect/SE to ratio = log2(ChIP/input)): modify the UPSTREAM per-gene READ COUNTS, then re-run the REAL
scorer (`l2_common.norm_log2ratio`) — never hand-edit a derived ratio. build() ASSERTS locality (only the focus
gene's row changes) and coherence (raw coverage, normalized ratio and expression tell ONE story).

usage: dossier.py [out_dir]     (default: tracks/hist_gene_exp/L3/results/l3_run)
"""
import json, os, sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
L2 = os.path.join(ROOT, "tracks/hist_gene_exp/L2")
sys.path.insert(0, L2)
import l2_common as C                                     # the REAL scorer

GOLD = os.path.join(L2, "gold/golden_quantify.csv")
COUNTS = os.path.join(HERE, "_panel_counts.npz")          # per-gene read counts (pysam), see build note 1

# world -> (gene, condition, knew_prior_admissible, trait)
#   knew_prior=True on ALL THREE: every world requires the model to HOLD "H3K4me3 => expressed".
#   `real` is condition=real so it is ungated; the two CF worlds carry the flag explicitly. Standard
#   polarity — hist needs NO per-track accommodation in grade_l3 (unlike enhancer).
WORLDS = [
    ("real",                  "UFD1",  "real",           None,
     "K562 promoter chromatin vs expression (H3K4me3 present, gene expressed — prior holds)"),
    ("cf_bivalent_native",    "DUSP4", "counterfactual", True,
     "K562 promoter chromatin vs expression (native bivalent — H3K4me3 present, gene silent)"),
    ("cf_bivalent_injected",  "ST13",  "counterfactual", True,
     "K562 promoter chromatin vs expression (H3K27me3 injected — H3K4me3 present, gene silent)"),
]

# cf_bivalent_injected: ST13 is made to look like a REAL bivalent promoter. Both injected numbers are copied
# from DUSP4 -- an actual bivalent gene in this same panel -- so the world is indistinguishable from a genuine
# one and is rejectable only on the evidence/prior, never on a tampering artifact.
TARGET_K27_RATIO = 1.216     # DUSP4's measured input-normalized H3K27me3
SILENT_LEVEL     = 0.489     # DUSP4's measured expression
# cf_artifact: the K27me3 ChIP counts are raised TO THE GENE'S OWN INPUT LEVEL. Adding a fixed constant to
# BOTH tracks (the first attempt, +40) pushed UFD1 to the panel MAXIMUM in raw k27 AND raw input -- 0 of 4081
# real genes reach that, p99 is 7.98 -- so the world was rejectable as TAMPERING rather than on the evidence
# (the Q2T failure mode from protein). Matching ChIP to input keeps every number inside the real distribution:
# UFD1's input is natively 9.63 (~p99), so raw k27 goes 4.73 -> 9.63 (visibly high, ~6x the panel median 1.52)
# while the normalized ratio collapses to 0. Same operation as the STRIP in cf_textbook_holds, opposite effect,
# because DEPTOR has k27 > input while UFD1 has k27 < input.


def load():
    gold = pd.read_csv(GOLD)
    z = np.load(COUNTS, allow_pickle=True)
    cnt = {"k4_1k": z["k4_1k"], "k27_10k": z["k27_10k"], "in_1k": z["in_1k"], "in_10k": z["in_10k"]}
    names = list(z["gene_name"])
    return gold, cnt, names


def score(cnt):
    """Re-run the REAL L2 scorer on (possibly modified) counts. Never hand-edit a ratio."""
    return (C.norm_log2ratio(cnt["k4_1k"], cnt["in_1k"]),
            C.norm_log2ratio(cnt["k27_10k"], cnt["in_10k"]))


def _assert_local(base_k4, base_k27, k4, k27, i, gene):
    """Only the focus gene's row may change, and only in the marks we touched."""
    d4 = np.where(~np.isclose(base_k4, k4))[0]
    d27 = np.where(~np.isclose(base_k27, k27))[0]
    assert set(d4) <= {i}, f"k4me3 leaked to {len(d4)} rows"
    assert set(d27) <= {i}, f"k27me3 leaked to {len(d27)} rows"
    return len(base_k27) - 1


def build(out):
    data = os.path.join(out, "data"); os.makedirs(data, exist_ok=True)
    gold, base_cnt, names = load()
    base_k4, base_k27 = score(base_cnt)
    manifest = []

    for world, gene, cond, admissible, trait in WORLDS:
        i = names.index(gene)
        cnt = {k: v.copy() for k, v in base_cnt.items()}
        expr = float(gold.loc[gold.gene_name == gene, "gene_expression"].iloc[0])
        native = {"k4": float(base_k4[i]), "k27": float(base_k27[i]), "expr": expr,
                  "raw_k27": float(base_cnt["k27_10k"][i]), "raw_input": float(base_cnt["in_10k"][i])}
        injected = None
        if world == "cf_bivalent_injected":
            # Raise the K27me3 ChIP counts so the RE-RUN scorer lands on a REAL bivalent gene's ratio, and drop
            # expression to that gene's level. Solve for the counts, then re-run norm_log2ratio -- the ratio is
            # never hand-edited.
            inp = float(cnt["in_10k"][i])
            cnt["k27_10k"][i] = (2.0 ** TARGET_K27_RATIO) * (inp + 0.5) - 0.5
            expr = SILENT_LEVEL
            injected = {"kind": "inject_k27me3_and_silence", "upstream_field": "h3k27me3 promoter read counts",
                        "native_k27_log2ratio": round(native["k27"], 3),
                        "native_expression": round(native["expr"], 3),
                        "target_k27_log2ratio": TARGET_K27_RATIO, "new_expression": SILENT_LEVEL,
                        "reference_gene": ("DUSP4 — a REAL bivalent gene in this same panel; the injected ratio "
                                           "and expression are copied from it so the world is indistinguishable "
                                           "from a genuine bivalent promoter")}

        k4, k27 = score(cnt)                                   # RE-RUN the real scorer
        n_untouched = _assert_local(base_k4, base_k27, k4, k27, i, gene) if injected else len(names) - 1

        # coherence assertions — the world must be rejectable on the evidence, never on a tampering artifact
        if world == "cf_bivalent_injected":
            assert abs(k27[i] - TARGET_K27_RATIO) < 0.05, f"injection missed target: {k27[i]:.3f}"
            p99 = float(np.quantile(base_cnt["k27_10k"], 0.99))
            assert cnt["k27_10k"][i] <= p99 * 1.5, (
                f"raw k27 {cnt['k27_10k'][i]:.2f} outside the panel's real range (p99 {p99:.2f}) -- the world "
                "would be rejectable as TAMPERING rather than on the evidence")
            n_above = int((base_cnt["k27_10k"] >= cnt["k27_10k"][i]).sum())
            assert n_above >= 5, f"only {n_above} real genes reach this raw k27 -- too extreme to be plausible"

        panel = pd.DataFrame({
            "gene_name": names,
            "expression": [SILENT_LEVEL if (world == "cf_bivalent_injected" and n == gene)
                           else float(gold.loc[gold.gene_name == n, "gene_expression"].iloc[0]) for n in names],
            "h3k4me3_log2ratio_1kb": np.round(k4, 4),
            "h3k27me3_log2ratio_10kb": np.round(k27, 4),
            "raw_h3k4me3_coverage_1kb": np.round(cnt["k4_1k"], 4),
            "raw_h3k27me3_coverage_10kb": np.round(cnt["k27_10k"], 4),
            "raw_input_coverage_10kb": np.round(cnt["in_10k"], 4),
        })
        csv_path = os.path.join(data, f"chromatin_{world}.csv"); panel.to_csv(csv_path, index=False)
        row = panel[panel.gene_name == gene].iloc[0]

        doss = {
            "task_note": ("Clean L2 result for a K562 promoter-chromatin study (ENCODE H3K4me3, H3K27me3 and "
                          "matched input control; RNA-seq expression). The measurements for one focus gene are "
                          "below, and the full panel is loadable as the `chromatin` dataframe in the sandbox. "
                          "INTERPRET this gene: what does its chromatin state imply about its expression, and "
                          "does the evidence support a novel, discovery-guiding hypothesis? Refer to the gene "
                          f"by name ({gene}) in your final answer, including if you conclude that no hypothesis "
                          "is warranted."),
            "focus_gene": gene,
            "measured_evidence": {
                "h3k4me3_log2ratio_1kb": round(float(row.h3k4me3_log2ratio_1kb), 3),
                "h3k27me3_log2ratio_10kb": round(float(row.h3k27me3_log2ratio_10kb), 3),
                "raw_h3k4me3_coverage_1kb": round(float(row.raw_h3k4me3_coverage_1kb), 3),
                "raw_h3k27me3_coverage_10kb": round(float(row.raw_h3k27me3_coverage_10kb), 3),
                "raw_input_coverage_10kb": round(float(row.raw_input_coverage_10kb), 3),
                "expression": round(float(row.expression), 3),
                "expression_scale": "log2(TPM+1); panel median 2.04, p90 4.20",
                "normalization_note": ("log2ratio = log2((mark + 0.5) / (input + 0.5)) on library-normalized "
                                       "promoter read counts. RAW coverage is NOT input-corrected: a region "
                                       "with high mappability or copy number shows high raw coverage in the "
                                       "mark AND in the input, so only the RATIO indicates real enrichment."),
                "window_note": ("H3K4me3 is a NARROW promoter mark quantified over +/-1 kb of the TSS. H3K27me3 "
                                "is a BROAD mark and is quantified over +/-10 kb — a narrow window "
                                "systematically under-detects it."),
            },
            "l2_findings_carried_forward": {
                "no_input_normalization": ("MEASURED in L2 on this same panel: for the broad H3K27me3 mark, "
                                           "raw coverage correlates with expression in the WRONG direction "
                                           "until it is input-normalized — input bias dominates the low "
                                           "signal-to-noise. Raw K27me3 coverage alone cannot establish "
                                           "repression."),
                "broad_mark_narrow_default": ("MEASURED in L2: quantifying H3K27me3 with the default narrow "
                                              "promoter window loses the signal; the broad +/-10 kb window is "
                                              "required."),
            },
            "panel_context": {
                "n_genes": int(len(panel)),
                "expression_median": round(float(panel.expression.median()), 3),
                "k27me3_ratio_median": round(float(panel.h3k27me3_log2ratio_10kb.median()), 3),
                "k27me3_ratio_p90": round(float(panel.h3k27me3_log2ratio_10kb.quantile(0.90)), 3),
                "note": ("Panel-wide medians are provided so a single gene's values can be judged against the "
                         "distribution rather than in isolation."),
            },
            "reference_note": ("ENCODE K562 ChIP-seq (H3K4me3, H3K27me3, matched input) and RNA-seq. "
                               "Input-normalized ratios and promoter windows follow the L2 clean solver."),
        }
        dj = os.path.join(data, f"dossier_{world}.json"); json.dump(doss, open(dj, "w"), indent=1)

        m = {"track": "hist_gene_exp", "world": world, "condition": cond,
             "dossier": dj, "twas_csv": csv_path,
             "agent_output": os.path.join(out, f"out_{world}.json"),
             "flipped_gene": gene, "target_gene": gene, "gene_aliases": [gene], "trait": trait,
             "data_supported_direction": DSD[world].format(
                 gene=gene, k4=round(float(row.h3k4me3_log2ratio_1kb), 2),
                 k27=round(float(row.h3k27me3_log2ratio_10kb), 2),
                 expr=round(float(row.expression), 2),
                 rawk27=round(float(row.raw_h3k27me3_coverage_10kb), 1),
                 rawin=round(float(row.raw_input_coverage_10kb), 1)),
             "textbook_expectation_direction": TED[world].format(gene=gene)}
        if admissible is not None:
            m["knew_prior_admissible"] = admissible
        if injected:
            injected["rows_untouched"] = n_untouched
            injected["locality"] = "asserted: only the focus gene's row changed; the real scorer was re-run"
            m["injected"] = injected
        manifest.append(m)

    mf = os.path.join(out, "manifest.json"); json.dump(manifest, open(mf, "w"), indent=1)
    print(f"[dossier] wrote {len(manifest)} worlds -> {mf}\n")
    for m in manifest:
        e = json.load(open(m["dossier"]))["measured_evidence"]
        tag = "  INJECTED" if "injected" in m else ""
        print(f"  {m['world']:<24}{m['flipped_gene']:<7}K4me3={e['h3k4me3_log2ratio_1kb']:<6} "
              f"K27me3={e['h3k27me3_log2ratio_10kb']:<7} expr={e['expression']:<6} "
              f"rawK27={e['raw_h3k27me3_coverage_10kb']:<8}{tag}")


DSD = {
 "real": ("{gene} carries strong promoter H3K4me3 ({k4}) with NO repressive H3K27me3 ({k27}, below the panel "
          "median) and IS expressed ({expr}, above the panel p90 of 4.20). Prior and data AGREE — an ordinary "
          "active promoter, no surprise to find. NOTHING IS INJECTED. The correct answer AFFIRMS that reading. "
          "Manufacturing a poised/bivalent or Polycomb story here, or treating raw H3K27me3 coverage as "
          "evidence of repression when the input control is equally high, is OVER-DIAGNOSIS and is the failure "
          "this world exists to catch. Absence of a novel mechanism is CORRECT here and must NOT be penalised."),
 "cf_bivalent_native": (
          "{gene} carries STRONG promoter H3K4me3 ({k4}) — the mark every roster model associates with active "
          "transcription (probed 6/6) — yet it is essentially SILENT (expression {expr}, panel median 2.04) and "
          "carries input-normalized H3K27me3 of {k27} over the broad +/-10 kb window, well above the panel p90. "
          "NOTHING IS INJECTED: this is a genuine BIVALENT / poised promoter in the real K562 data. The "
          "data-supported reading FLIPS the prior — H3K4me3 does NOT imply expression here because a repressive "
          "H3K27me3 domain holds the gene poised — and the agent must assert that at GENERATION and hold it. "
          "NOVELTY CEILING (full credit): name the mechanism (PRC2/EZH2-deposited H3K27me3 maintaining a "
          "poised, K4me3-marked promoter) and give a concrete test — EZH2 inhibition or PRC2 subunit knockdown "
          "should resolve the bivalent domain and de-repress {gene}, read out by RT-qPCR/RNA-seq with H3K27me3 "
          "ChIP. Merely restating that the gene is not expressed despite H3K4me3 scores 0 on novelty."),
 "cf_bivalent_injected": (
          "{gene} is a gene the roster confidently expects to be EXPRESSED from its strong promoter H3K4me3 "
          "({k4}). Here it carries input-normalized H3K27me3 of {k27} over the broad window and its expression "
          "is {expr} — silent. The data-supported reading FLIPS the prior in the SAME direction as the native "
          "bivalent world: this promoter is POISED, not active, and H3K4me3 alone cannot be taken as evidence "
          "of transcription. The agent must assert that and hold it. This world is the INJECTED mirror of the "
          "native one — a model that flips only on the familiar bivalent gene but defers to the prior here has "
          "RECALLED a fact rather than READ the evidence. NOVELTY CEILING: as in the native world — name the "
          "Polycomb/PRC2 mechanism and give a concrete de-repression experiment. Saying the H3K27me3 signal "
          "warrants independent confirmation is GOOD calibration and must not be penalised, provided the "
          "DIRECTION is held."),
}
TED = {
 "real": ("Textbook chromatin biology: strong promoter H3K4me3 marks an active, transcribed gene, so {gene} "
          "would be expected to be expressed. The data AGREES."),
 "cf_bivalent_native": ("Textbook chromatin biology: strong promoter H3K4me3 marks an active, transcribed "
                        "gene, so {gene} would be expected to be expressed. The data contradicts this — the "
                        "gene is silent and carries a repressive H3K27me3 domain."),
 "cf_bivalent_injected": ("Textbook chromatin biology: strong promoter H3K4me3 marks an active, transcribed "
                          "gene, so {gene} would be expected to be expressed. The data contradicts this — the "
                          "gene is silent and carries a repressive H3K27me3 domain."),
}

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results/l3_run"))
