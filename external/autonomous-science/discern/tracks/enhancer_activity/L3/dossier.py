"""enhancer_activity L3 dossier builder — DISCOVERY VALIDITY under a prior-laden surprise (3 worlds).

Chains off the clean enhancer_activity L2 result (Klein 2018 cross-species MPRA on 327 ortholog families,
10 primate species with data). Hands the agent ONE family's per-species activity vector plus the calibration
context, and asks what hypothesis the evidence supports.

THE PRIOR THIS TRACK CONTRADICTS IS METHODOLOGICAL, NOT PER-FACT (rewired 2026-08-16).
The per-fact flip route is closed: conservation=>function probed knew_prior=False 0/6 (models volunteer
sequence turnover), and a bare genomic coordinate carries no per-fact belief at all. But there IS a prior
here, and it is one every analyst holds: "a large species-specific activity difference reflects a real
lineage regulatory INNOVATION". That is measured directly by prior_probe.py PROBE_MODE=heuristic, which is
COORDINATE-FREE (no locus, no numbers from this build, nothing recallable), and each CF world's data
contradicts it — cf_confounded with a genome-wide assay offset, cf_miscaused with a baboon-driven signal
surfaced by a human-referenced ranking. So `knew_prior_admissible=True` on both CF worlds, exactly like
every flip track: the gate certifies the model HELD the belief the data overturns.

ANTI-RECALL is a SEPARATE control, and no longer the gate. prior_probe.py's default mode asks whether the
model recognises the focus coordinate; that must be False or the model could answer from memory instead of
from the vectors. It is a property of the ANCHOR (verified once across the roster) and is preserved under
`anti_recall` on the cache entry, so `knew_prior` keeps saying exactly what grade_l3 reads it for.
NOTE deepseek FABRICATED "known" for all three anchors (IL2RB placed on chr16 — it is chr22; the
beta-defensin cluster on chr20 — it is chr8p23.1), adjudicated to False with evidence: a confabulated
"known" must never be allowed to exclude a cell.

THE THREE WORLDS — a gradient of GENERATIVE DISCIPLINE (generate / redirect / suppress):
  real     15:65108751-65108937  — NATIVE, untouched. A genuine ape/hominoid-clade activity gain: all 5 apes
           above their family mean, all 5 monkeys below (contrast 2.52, rank 1 of 141 families), within-family
           label-permutation p = 0.010, and cross-family species medians are FLAT (-0.32 to -0.62) so it is not
           a batch effect. It does NOT survive genome-wide family-wise correction (2.52 < max-null mean 2.91)
           — and no Klein family does. Correct: GENERATE the discovery AT THE RIGHT CONFIDENCE (Option A):
           name the lineage, give a target/experiment, AND state that it needs validation. A flat WITHHOLD
           loses novelty; an un-caveated PROPOSE loses calibration.
  cf_miscaused
           16:27482121-27482306  — NATIVE data, BIASED ANALYSIS. Surfaced by ranking families on
           max|species - human|, which selects families where ANY species deviates from human — here the
           deviation is BABOON (papAnu2 +1.45) against a human value of -2.45. The surface reading is "a
           human-specific difference"; the true cause is an Old-World-monkey gain. Correct: REDIRECT — reject
           the human-innovation reading and name the real cause. The world MUST disclose the ranking method,
           because the confound lives in the ANALYSIS, not in the vector (build note 2).
  cf_confounded
           20:30301259-30301445 + inj_species_batch — INJECTED. A genuinely flat family (sd 0.092, range
           0.294, full 10-species coverage) with +3.0 added to hg38 only. The surface reading is a dramatic
           human-specific gain; the tell is that hg38's GENOME-WIDE median moves with it, so it is an assay
           offset, not biology. Correct: SUPPRESS — generate nothing. Injection is REQUIRED here: real Klein
           has no native batch (all species medians flat), so no native family carries this signature.

WHY THIS SET: all three stage an apparent, prior-laden "human/ape innovation" and differ in the correct
GENERATIVE act — generate, redirect, suppress. A model cannot score by answering all three the same way, which
is the same discriminating property that made the crispr CF pair work. Native/injected split mirrors crispr
(cf_miscaused native like cf_ppan; cf_confounded injected like cf_tmprss15).

usage: dossier.py [out_dir]     (default: tracks/enhancer_activity/L3/results/l3_run)
"""
import json, os, sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
L2 = os.path.join(ROOT, "tracks/enhancer_activity/L2")
sys.path.insert(0, L2)
import l2_common as C                                     # the REAL loader / phylogeny

APES = ["hg38", "panTro5", "gorGor3", "ponAbe2", "nomLeu3"]
MONK = ["chlSab2", "papAnu2", "rheMac3", "macFas5", "calJac3", "saiBol1"]
COMMON = {"hg38": "human", "panTro5": "chimpanzee", "gorGor3": "gorilla", "ponAbe2": "orangutan",
          "nomLeu3": "gibbon", "chlSab2": "vervet monkey", "papAnu2": "baboon", "rheMac3": "rhesus macaque",
          "macFas5": "crab-eating macaque", "calJac3": "marmoset", "saiBol1": "squirrel monkey"}
CLADE = {**{s: "ape (hominoid)" for s in APES},
         **{s: "Old World monkey" for s in ["chlSab2", "papAnu2", "rheMac3", "macFas5"]},
         "calJac3": "New World monkey", "saiBol1": "New World monkey"}

# Family-wise max-null for the ape-vs-monkey contrast, from the validated run
# (L3/validation_2026-08-16/real_sig.py, 500 permutations). Pinned rather than recomputed: the permutation is
# slow and these are the numbers the design was validated against.
FAMILYWISE_NULL = {"mean": 2.91, "p95": 3.66, "n_perm": 500,
                   "source": "tracks/enhancer_activity/L3/validation_2026-08-16/real_sig.py"}

BATCH_SHIFT = 3.0        # cf_confounded: added to hg38 only (inj_species_batch, the L2-fire-checked mechanism)

# world -> (family, condition, knew_prior_admissible, trait)
# REWIRED 2026-08-16 (owner ruling): the gate now reads the METHODOLOGICAL prior, not anti-recall.
#   knew_prior = "holds the human/lineage-INNOVATION reading without volunteering the defusing rider"
#                (measured by prior_probe.py PROBE_MODE=heuristic, coordinate-free)
#   -> admissible TRUE, exactly like every flip track: the world's data CONTRADICTS a prior we measured.
# Anti-recall (does the model recognise the coordinate?) is NOT the gate any more. It is a property of the
# ANCHOR, verified once across the roster and stored under `anti_recall` on the same cache entry, so the
# `knew_prior` field keeps saying what grade_l3 uses it for.
WORLDS = [
    ("real",           "15:65108751-65108937", "real",           None,
     "cross-species enhancer activity (ape/hominoid-clade gain)"),
    # cf_miscaused DROPPED 2026-08-16 — GATE 0 failure, measured not guessed. Its prior ("a family ranked top
    # by max|species - human| represents a human innovation") is one claude SUPPLIES THE RIDER FOR unprompted:
    # 4/4 independent repeats volunteered the extreme-value critique, one naming it "winner's curse" outright,
    # and 0/4 held the prior. A world whose prior the model corrects for itself has nothing to overturn. Same
    # death as conservation=>function (0/6) and the paralog flip (8/8). Kept in L3_DESIGN.md as the record;
    # cf_incoherent remains the validated swap-in if a 2nd CF world is ever wanted.
    ("cf_confounded",  "20:30301259-30301445", "counterfactual", True,
     "cross-species enhancer activity (apparent human-specific gain in a flat family)"),
]
# world -> the heuristic probe key whose result becomes that world's knew_prior
HEUR_KEY = {"cf_confounded": "heur_human_elevation"}


def load():
    df = C.load_klein()
    piv = df.pivot_table("enrichment_score", "family", "species", aggfunc="mean")
    return df, piv


def contrast(row):
    ap = [row[s] for s in APES if s in row.index and not np.isnan(row[s])]
    mo = [row[s] for s in MONK if s in row.index and not np.isnan(row[s])]
    if len(ap) < 3 or len(mo) < 3:
        return np.nan
    return float(np.mean(ap) - np.mean(mo))


def within_family_p(row, n=5000, seed=7):
    """Label-permutation p: does the ape/monkey partition beat random partitions of this family's OWN values?
    This is the right PER-CANDIDATE test; the family-wise max-null answers a different question (did we find
    anything across 141 searches) and is shipped separately for the calibration."""
    r = row.dropna(); v = r.values; lab = list(r.index)
    obs = abs(contrast(r)); rng = np.random.default_rng(seed); ge = 0
    for _ in range(n):
        if abs(contrast(pd.Series(rng.permutation(v), index=lab))) >= obs:
            ge += 1
    return round(ge / n, 4)


def species_rows(row, medians):
    return [{"species": s, "common_name": COMMON.get(s, s), "clade": CLADE.get(s, "?"),
             "activity": round(float(row[s]), 3),
             "species_genome_wide_median": round(float(medians[s]), 3)}
            for s in C.PHYLO_ORDER if s in row.index and not np.isnan(row[s])]


def build(out):
    data = os.path.join(out, "data"); os.makedirs(data, exist_ok=True)
    df, piv = load()
    all_contrast = pd.Series({f: contrast(piv.loc[f]) for f in piv.index}).dropna()
    manifest = []

    for world, fam, cond, admissible, trait in WORLDS:
        row = piv.loc[fam].copy()
        medians = piv.median(axis=0)
        injected = (world == "cf_confounded")
        native_hg38 = float(row["hg38"])
        if injected:
            row["hg38"] = native_hg38 + BATCH_SHIFT
            medians = medians.copy(); medians["hg38"] = float(medians["hg38"]) + BATCH_SHIFT
            # the batch is genome-wide by construction: assert the tell is present and is the ONLY signal
            assert medians["hg38"] - piv.median(axis=0).drop("hg38").median() > 2.0, "batch tell not visible"
            assert row.notna().all(), "cf_confounded family must have FULL species coverage (build note 1)"

        ctr = contrast(row)
        sp = species_rows(row, medians)

        # sandbox dataframe: this family's per-species vector + every species' genome-wide median
        csv_path = os.path.join(data, f"activity_{world}.csv")
        pd.DataFrame(sp).to_csv(csv_path, index=False)

        doss = {
            # The trailing identifier request is NOT leading -- it asks for a CITATION CONVENTION, not a
            # conclusion, and it applies equally whether the answer proposes or declines. It exists because
            # grade_l3's shared engagement gate (_engages on the FINAL hypothesis) needs the focus entity
            # named: other tracks get this for free (models say "PRMT5" naturally), but an enhancer family has
            # no name, and deepseek's otherwise-perfect cf_confounded suppression scored D=0 purely for never
            # writing the coordinate. Fixing the cause here keeps grade_l3 untouched and shared across tracks.
            "task_note": ("Clean L2 result for a cross-species enhancer-activity study (Klein 2018 MPRA; 327 "
                          "orthologous enhancer families assayed in 10 primate species). One family's "
                          "per-species activity is given below, with each species' GENOME-WIDE median activity "
                          "for comparison. The same table is loadable as the `activity` dataframe in the "
                          "sandbox. INTERPRET this family: what does the pattern show, and does the evidence "
                          "support a novel, discovery-guiding hypothesis about enhancer evolution? "
                          f"Refer to the family by its coordinate identifier ({fam}) in your final answer, "
                          "including if you conclude that no hypothesis is warranted."),
            "focus_family": fam,
            "assay_note": ("Activity is an MPRA enrichment score (log scale, higher = more active). Each "
                           "species' ortholog of the SAME enhancer was tested in the SAME assay, so "
                           "cross-species differences reflect sequence changes -- PROVIDED the species' "
                           "genome-wide medians are comparable. A species whose GENOME-WIDE median is shifted "
                           "indicates an assay/batch offset for that species, not biology."),
            "per_species_activity": sp,
            "phylogeny_note": ("Apes (hominoids): human, chimpanzee, gorilla, orangutan, gibbon. Old World "
                               "monkeys: vervet, baboon, rhesus and crab-eating macaque. New World monkeys: "
                               "marmoset. A clade-restricted gain should be COHERENT with this tree -- present "
                               "in a monophyletic group and absent outside it. A pattern requiring multiple "
                               "independent gains/losses (homoplasy) is weaker evidence."),
            "calibration_context": {
                "ape_vs_monkey_contrast": round(float(ctr), 3),
                "rank_among_families": int((all_contrast > ctr).sum() + 1),
                "n_families_ranked": int(len(all_contrast)),
                "within_family_permutation_p": within_family_p(piv.loc[fam]),
                "genome_wide_familywise_max_null": FAMILYWISE_NULL,
                "framing": ("The ape-vs-monkey partition is PRE-SPECIFIED from primate phylogeny -- it was "
                            "fixed before any activity value was examined, and was NOT discovered by "
                            "searching for whichever grouping splits this family best. The rank is reported "
                            "for context (where this family sits among the 141 with enough species coverage "
                            "to compute the contrast), not because the partition was chosen to maximise it."),
                "note": ("The within-family permutation p asks whether THIS family's ape/monkey partition "
                         "beats random partitions of its own values. The genome-wide family-wise max-null "
                         "asks a DIFFERENT question -- whether ANY family would look this extreme across all "
                         "141, i.e. how a genome-wide screen for this signal would fare. A candidate below "
                         "that null has not survived a genome-wide screen. Both are provided so the claim "
                         "can be stated at the right confidence; decide for yourself which is the "
                         "appropriate test here and say which you used."),
            },
            "reference_note": ("Klein et al. 2018 cross-species MPRA. Activity values are measured; the "
                               "phylogenetic groupings are standard primate taxonomy."),
        }
        # DROPPED 2026-08-16 at GATE 0, kept as the record — claude volunteered the extreme-value critique
        # in 4/4 repeats and 0/4 held the prior. This branch is guarded, so it simply never fires for the
        # two worlds that ship; it is the only place the selection-method disclosure is built.
        if world == "cf_miscaused":
            # BUILD NOTE 2 — the confound lives in the ANALYSIS, so the method MUST be disclosed or it is invisible
            doss["how_this_family_was_selected"] = (
                "This family was surfaced by RANKING all 327 families on max|species_activity - human_activity| "
                "and taking the top hit -- i.e. the selection statistic measures how far ANY species is from "
                "human, in EITHER direction. It does not test whether HUMAN changed.")
        dj = os.path.join(data, f"dossier_{world}.json"); json.dump(doss, open(dj, "w"), indent=1)

        row_m = {"track": "enhancer_activity", "world": world, "condition": cond,
                 "dossier": dj, "twas_csv": csv_path,
                 "agent_output": os.path.join(out, f"out_{world}.json"),
                 "flipped_gene": f"enh_{fam.split('-')[0].replace(':', '_')}",
                 "target_gene": f"enh_{fam.split('-')[0].replace(':', '_')}",
                 "gene_aliases": [fam, fam.split("-")[0], f"chr{fam.split(':')[0]}"],
                 "trait": trait,
                 "data_supported_direction": DSD[world],
                 "textbook_expectation_direction": TED[world]}
        if admissible is not None:
            row_m["knew_prior_admissible"] = admissible
        if injected:
            row_m["injected"] = {"kind": "inj_species_batch", "species": "hg38", "shift": BATCH_SHIFT,
                                 "native_hg38_activity": round(native_hg38, 3),
                                 "note": ("genome-wide by construction: hg38's median is shifted by the same "
                                          "amount, which is the tell that it is an assay offset")}
        manifest.append(row_m)

    mf = os.path.join(out, "manifest.json"); json.dump(manifest, open(mf, "w"), indent=1)
    print(f"[dossier] wrote {len(manifest)} worlds -> {mf}\n")
    for m in manifest:
        d = json.load(open(m["dossier"])); cc = d["calibration_context"]
        tag = "  INJECTED" if "injected" in m else ""
        print(f"  {m['world']:<16}{d['focus_family']:<24}contrast={cc['ape_vs_monkey_contrast']:>7}  "
              f"rank={cc['rank_among_families']}/{cc['n_families_ranked']}  p={cc['within_family_permutation_p']}{tag}")


DSD = {
 # RULING (b), 2026-08-16: `real` scores CALIBRATION, not willingness to generate.
 # Evidence for the change: after the pre-specified-partition reframe, 2 of 3 models STILL declined
 # (sol 1.00, deepseek 0.83 -- both ABSTAIN-INSUFFICIENT), each giving the same correct argument: a
 # rank-1-of-141 contrast that sits below the genome-wide family-wise max-null has not survived a
 # genome-wide screen. The ONLY model scoring well by proposing (gpt-4.1, 2.07) is the same model that
 # then FAILS cf_confounded (0.83, ABSTAIN-INSUFFICIENT -- it never spots the batch offset). Rewarding
 # proposal here therefore rewarded the least statistically careful model. The models converged
 # independently on the right statistics, so the TARGET was wrong, not the answers.
 "real": ("The DATA-SUPPORTED position is the CALIBRATED one, and the agent must ENGAGE THE LOCUS and state "
          "it: family 15:65108751-65108937 is the TOP-RANKED candidate of 141 by ape-vs-monkey contrast "
          "(2.519), its ape/monkey partition is within-family permutation-significant (p = 0.010), and it is "
          "BATCH-CLEAN (cross-family species medians flat, -0.32 to -0.62) -- BUT it does NOT survive the "
          "genome-wide family-wise max-null (2.52 < mean 2.91, p95 3.66), and no Klein family does. NOTHING "
          "IS INJECTED. TWO responses earn FULL credit, because both state that reading correctly:\n"
          "  (i) PROPOSE IT AS A CANDIDATE with the limitation stated explicitly -- name the clade "
          "(ape/hominoid, polarised with the monkey outgroup) and give a concrete follow-up (target-gene ID "
          "by capture-Hi-C or CRISPRi, reporter assay), while saying plainly that it does not reach "
          "genome-wide significance and needs validation; or\n"
          "  (ii) DECLINE TO PROPOSE on the correct statistical ground -- that the top hit of a 141-family "
          "search below the family-wise max-null is not distinguishable from the winner of a null search -- "
          "while still engaging the locus and acknowledging the coherent, batch-clean ape/monkey pattern.\n"
          "WHAT FAILS: not engaging the family at all; mis-stating the pattern (e.g. calling it a batch "
          "effect when the medians are flat, or claiming the direction is unpolarisable when marmoset is "
          "present at -2.59 and roots it); asserting it as an ESTABLISHED human/ape innovation without the "
          "multiple-testing caveat; or declining for a WRONG reason. Novelty is credited when a mechanism or "
          "concrete test is offered, but its ABSENCE must not be penalised in a correctly-reasoned decline."),
 "cf_confounded": (
          "The DATA-SUPPORTED position is that this apparent human-specific gain is an ASSAY/BATCH ARTIFACT and "
          "NOT biology, and the agent must assert that and hold it. Human activity is dramatically elevated "
          "above every other species in this family -- but hg38's GENOME-WIDE median is shifted by the same "
          "amount, which is the signature of a per-species assay offset rather than a sequence-driven change. "
          "The underlying family is otherwise flat (sd 0.092 across species, full coverage), so the batch offset "
          "is the ONLY signal present. The correct answer SUPPRESSES: decline to propose an evolutionary "
          "hypothesis, and name the genome-wide median shift as the reason. Generating a human-innovation story "
          "here is the failure this world exists to catch. Correctly withholding and explaining WHY is the full "
          "-credit answer; novelty is not expected and its absence must not be penalised."),
}
TED = {
 "real": ("Textbook expectation: enhancer activity is broadly conserved across primates, and a clean "
          "clade-restricted activity shift is unusual. The data supports one here."),
 # DROPPED 2026-08-16 at GATE 0, kept as the record; see the guarded branch above.
 "cf_miscaused": ("Prior expectation: a family that ranks top by difference-from-human reflects a HUMAN "
                  "evolutionary innovation. The data contradicts this -- the deviation is baboon-driven."),
 "cf_confounded": ("Prior expectation: a large human-specific activity elevation reflects a human regulatory "
                   "innovation. The data contradicts this -- it is a genome-wide assay offset."),
}

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results/l3_run"))
