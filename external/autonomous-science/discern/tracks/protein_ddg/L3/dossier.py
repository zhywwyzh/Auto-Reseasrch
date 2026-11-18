"""protein_ddg L3 dossier builder — MEASURED ddG vs the ESM/biophysical PRIOR (3 worlds: 1 real + 2 CF).

Chains off the clean protein_ddg L2 result: hands the agent one focus mutation's MEASURED stability change
(Tsuboyama/Rocklin 2023, GB1) alongside the ESM2-650M prediction, the burial/secondary-structure context, and
the two load-bearing L2 lessons -- then asks it to INTERPRET the measurement.

SIGN CONVENTION (Tsuboyama, used throughout): ddG > 0 = MORE stable; ddG < 0 = destabilizing.
ESM log-likelihood ratio: higher = more favourable. They correlate POSITIVELY on this substrate.

THE TWO L2 LESSONS THIS TRACK CHAINS FROM (both measured, both in the dossier):
  L2 (2) anti-symmetry bias: ESM's sign-accuracy on STABILIZING mutations is 0.00 while on destabilizing ones
     it is 1.00 -- the model is structurally blind to stabilization. That is the precise reason a large
     negative ESM LLR is NOT evidence against a measured stabilizing ddG.
  L2 (3) burial dominance: |corr| burial 0.488 > hydrophobicity 0.309 -- burial is the dominant determinant,
     so the focus residue's relative SASA is the mechanistic key.

THE THREE WORLDS -- one native conflict, one injected, pointing OPPOSITE ways:
  real     A26E   measured -3.06 (destabilizing), ESM -7.52, rsa 0.00 (buried).  Probe: 4/4 models say
                  DESTABILIZE -- and they are right. Prior, ESM and measurement all AGREE, so there is no
                  surprise to find. Tests OVER-DIAGNOSIS: burying a charge is textbook destabilizing; do not
                  manufacture a discovery. Nothing is injected.
  cf_stabilizing
           L5F    measured +1.82 (STABILIZING), ESM -4.32 (says destabilizing), rsa 0.01 (fully buried).
                  Probe: 4/4 models say DESTABILIZE with ZERO volunteered relief/repacking caveats -- a
                  unanimous, commonly-WRONG per-fact prior, so this clears ADD_A_TRACK GATE 0. NOTHING IS
                  INJECTED: the conflict is native to the real Tsuboyama measurement. Correct: FLIP toward
                  the measurement (core repacking gain), and cite the L2 anti-symmetry lesson as the reason
                  ESM cannot be trusted here.
  cf_destabilizing_injected
           Q2T    measured 0.000 natively (a conservative, solvent-exposed surface substitution; rsa 0.49),
                  ESM -1.26. Probe: 4/4 models answer NEGLIGIBLE -- correct, and firmly held. There is NO
                  conflict until we make one, so the ddG is INJECTED to -3.60 (Route 2, mirroring the GWAS
                  `cf_zscore` and crispr TMPRSS15 constructions). Correct: FLIP toward the measurement in the
                  OPPOSITE direction -- a substitution you believe is harmless is strongly destabilizing in
                  this protein.

WHY THE TWO CF WORLDS POINT OPPOSITE WAYS: a model cannot score by always resolving conflicts the same way
("trust the measurement toward destabilizing", or reflexive contrarianism toward ESM). It must follow the
evidence each time. Same design as crispr, where it separated models a single CF world could not.

INJECTION LOCALITY: ddG is the MEASURED endpoint -- ESM LLR, relative SASA and secondary structure are all
computed independently of it, so altering one mutation's ddG cannot perturb any other row. build() ASSERTS
this rather than assuming it (see _assert_injection_local).

usage: dossier.py [out_dir]     (default: tracks/protein_ddg/L3/results/l3_run)
"""
import csv, json, os, sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
L2 = os.path.join(ROOT, "tracks/protein_ddg/L2")
GOLDEN = os.path.join(L2, "golden/gb1_ddg_golden.csv")
STRUCT = os.path.join(ROOT, "tracks/protein_ddg/data/clean/gb1.pdb")

INJECT = {"V54I": -3.600}          # world -> injected ddG. See module docstring (Route 2).

# Side-chain volumes (Zamyatnin 1972, A^3) -- used ONLY to compute the within-position ddG~volume check that
# the `real` ground truth cites. Not shown to the agent.
VOL = {'A':88.6,'R':173.4,'N':114.1,'D':111.1,'C':108.5,'E':138.4,'Q':143.8,'G':60.1,'H':153.2,'I':166.7,
       'L':166.7,'K':168.6,'M':162.9,'F':189.9,'P':112.7,'S':89.0,'T':116.1,'W':227.8,'Y':193.6,'V':140.0}


def pos_panel(df, pos):
    """Within-position (LOCAL PEER GROUP) stats for the focus residue.

    The `real` ground truth REQUIRES these numbers: they are what establishes that at this position the
    charge-burial mechanism is NOT the discriminating factor (ruling 2026-08-19, see DSD['real']). Computed
    from the golden at build time rather than hard-coded, so the ground-truth text can never drift from the data.
    """
    p = df[df.pos == pos]
    ch = p[p["mut"].isin(list("DEKR"))].ddg_measured
    am = p[p["mut"].isin(list("QN"))].ddg_measured
    return {"n_pos": int(len(p)),
            "span": round(float(p.ddg_measured.max() - p.ddg_measured.min()), 2),
            "sd_pos": round(float(p.ddg_measured.std()), 3),
            "r_vol": round(float(p.ddg_measured.corr(p["mut"].map(VOL))), 3),
            "charged_mean": round(float(ch.mean()), 3),
            "amide_mean": round(float(am.mean()), 3)}


MAXASA = {'A':129,'R':274,'N':195,'D':193,'C':167,'E':223,'Q':225,'G':104,'H':224,'I':197,'L':201,'K':236,
          'M':224,'F':240,'P':159,'S':155,'T':172,'W':285,'Y':263,'V':174}
T21 = {'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLU':'E','GLN':'Q','GLY':'G','HIS':'H','ILE':'I',
       'LEU':'L','LYS':'K','MET':'M','PHE':'F','PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V'}

# world -> (mutation, condition, knew_prior_admissible, trait)
#   knew_prior=True ALWAYS means "holds the prior this world overturns":
#     cf_stabilizing            True — must believe L5F DESTABILIZES (4/4 do); the measurement says +1.82
#     cf_destabilizing_injected True — must believe Q2T is NEGLIGIBLE (4/4 do); the injected ddG says -3.60
WORLDS = [
    ("real",                       "A26E", "real",           None, "GB1 fold stability (buried charge — prior, ESM and measurement AGREE)"),
    ("cf_stabilizing",             "L5F",  "counterfactual", True, "GB1 fold stability (buried core repacking — measured STABILIZING, ESM says otherwise)"),
    # ANCHOR CHANGED Q2T -> V54C (2026-08-16). Q2T is solvent-EXPOSED (rsa 0.488) with weak ESM (-1.26), so an
    # injected -3.60 was biophysically incoherent and DETECTABLE: kimi rejected it with five strands, incl.
    # "every other exposed mutation below -2.9 is a Pro/Gly substitution" and "residual from the ddG~ESM trend
    # is -3.2". Three models then tied at 2.50 for detecting the artifact -- the world measured artifact-
    # detection, the OPPOSITE of the flip it claims to test. V54C is fully BURIED (rsa 0.000), where 49 real
    # non-Pro/Gly mutations already sit below -2.9 (F30A: rsa 0.020, ESM -0.14, ddG -3.44 -- buried, weak ESM,
    # strongly destabilising). The injection is now indistinguishable from real measurements.
    # cf_destabilizing_injected DROPPED 2026-08-16. Anchor history: Q2T -> V54C -> V54I, each change driven by
    # a measured gate result, and the world still failed a coherence check none of them caught.
    #   Q2T  (rsa 0.488, exposed): prior held 4/4 but the injection was DETECTABLE -- kimi rejected -3.60 with
    #        five strands incl. "every other exposed mutation below -2.9 is a Pro/Gly substitution".
    #   V54C (buried): magnitude coherent, but FAILED the prior gate 3/3 -- a buried Val->Cys LOSES volume, so
    #        a large negative ddG CONFIRMS the prior instead of contradicting it.
    #   V54I (buried): prior gate PASSED 5/6 and the magnitude sits inside the panel-wide distribution of
    #        buried mutations (49 real non-Pro/Gly below -2.9). BUT claude rejected it on a WITHIN-POSITION
    #        comparison the build never made: at position 54 the injected -3.600 makes a CONSERVATIVE Val->Ile
    #        the most destabilising of all 19 substitutions -- below V54D (-3.343), V54E (-3.327), V54P
    #        (-3.263), V54G (-2.897) -- while natively V54I is +0.062, rank 16/19, and every hydrophobic
    #        substitution there (C +0.027, L +0.177, M +0.366, F +0.771) is neutral-to-stabilising. Chemically
    #        implausible, and the same failure class as Q2T.
    # LESSON (now a project rule): an injected value must be coherent against its LOCAL PEER GROUP -- the other
    # substitutions at the same position / the other guides for the same gene -- not merely against the global
    # distribution. Checking only the global distribution cost two anchors here.
    # The track keeps `real` + `cf_stabilizing` (2 worlds), which also removes glm's per-model exclusion, so all
    # 6 models now score on an identical world set.
]


def burial():
    from Bio.PDB import PDBParser
    from Bio.PDB.SASA import ShrakeRupley
    s = PDBParser(QUIET=True).get_structure("gb1", STRUCT)
    ShrakeRupley().compute(s[0], level="R")
    out = {}
    for i, r in enumerate(list(s[0]["A"]), start=1):
        aa = T21.get(r.get_resname())
        if aa:
            out[i] = round(r.sasa / MAXASA[aa], 3)
    return out


def table():
    g = pd.read_csv(GOLDEN)
    g["mutation"] = g.wt + g.pos.astype(str) + g.mut
    g["rel_sasa"] = g.pos.map(burial())
    return g


def _assert_injection_local(base, inj, focus):
    """The injected ddG must alter EXACTLY ONE row. ESM LLR / rel_sasa / every other mutation are computed
    independently of ddG, so this should hold by construction -- but crispr taught us to MEASURE locality,
    not assume it (injecting a NEGv1 gene there silently moved 380 other genes' Bayes factors)."""
    a = base.set_index("mutation"); b = inj.set_index("mutation")
    assert list(a.index) == list(b.index), "row set changed"
    diff = [m for m in a.index if not np.allclose(a.loc[m, "ddg_measured"], b.loc[m, "ddg_measured"])]
    assert diff == [focus], f"injection leaked: rows changed = {diff}"
    for col in ("esm_clean_llr", "rel_sasa"):
        assert np.allclose(a[col].values, b[col].values, equal_nan=True), f"{col} perturbed by the injection"
    return len(a) - 1


def build(out):
    data = os.path.join(out, "data"); os.makedirs(data, exist_ok=True)
    base = table()
    manifest = []

    for world, mut, cond, admissible, trait in WORLDS:
        df = base.copy()
        injected = mut in INJECT and world.endswith("_injected")
        native_ddg = float(base.loc[base.mutation == mut, "ddg_measured"].iloc[0])
        if injected:
            df.loc[df.mutation == mut, "ddg_measured"] = INJECT[mut]
            n_untouched = _assert_injection_local(base, df, mut)
        r = df[df.mutation == mut].iloc[0]
        ddg, llr, rsa = float(r.ddg_measured), float(r.esm_clean_llr), float(r.rel_sasa)

        # sandbox dataframe: EVERY measured mutation (the focus row included) so the agent can situate it
        csv_path = os.path.join(data, f"stability_{world}.csv")
        df[["mutation", "pos", "wt", "mut", "ddg_measured", "esm_clean_llr", "rel_sasa"]].to_csv(csv_path, index=False)

        stab = df[df.ddg_measured > 0]
        doss = {
            "task_note": ("Clean L2 result for a GB1 (protein G B1 domain) deep mutational stability study. "
                          "The MEASURED stability change for one focus mutation is given below, together with "
                          "the ESM2-650M prediction and the structural context. The full measured table is "
                          "loadable as the `stability` dataframe in the sandbox, and the GB1 structure is in "
                          "the world directory. INTERPRET this measurement: is it credible, what does it mean "
                          "for this residue, and does the evidence support any novel, discovery-guiding "
                          "hypothesis?"),
            "focus_mutation": mut,
            "measured_evidence": {
                "ddg_measured": round(ddg, 3),
                "sign_convention": "ddG > 0 = MORE stable; ddG < 0 = destabilizing (Tsuboyama/Rocklin 2023)",
                "interpretation": "STABILIZING" if ddg > 0 else "DESTABILIZING",
                "esm2_650M_llr": round(llr, 3),
                "esm_says": "destabilizing" if llr < 0 else "stabilizing",
                "esm_note": ("ESM log-likelihood ratio is an UNCALIBRATED rank proxy, not kcal/mol. Higher = "
                             "more favourable. On this substrate ESM and the measurement correlate POSITIVELY, "
                             "so a disagreement in SIGN is meaningful, not a units artifact."),
                "relative_sasa": rsa,
                "burial": "buried (core)" if rsa < 0.15 else ("partially buried" if rsa < 0.35 else "solvent-exposed"),
                "wt_residue": r.wt, "mutant_residue": r.mut, "position": int(r.pos),
            },
            "l2_findings_carried_forward": {
                "anti_symmetry_bias": ("MEASURED in L2 on this same dataset: ESM's sign-accuracy is 1.00 on "
                                       "DESTABILIZING mutations but 0.00 on STABILIZING ones. ESM is "
                                       "structurally blind to stabilization, so a negative ESM LLR is weak "
                                       "evidence against a measured stabilizing value."),
                "burial_dominance": ("MEASURED in L2: |corr| with ddG is 0.488 for burial vs 0.309 for "
                                     "hydrophobicity — burial is the dominant determinant of stability change."),
            },
            "dataset_context": {
                "n_measured_mutations": int(len(df)),
                "n_stabilizing": int(len(stab)),
                "frac_stabilizing": round(len(stab) / len(df), 3),
                "note": ("Stabilizing mutations are a real minority class in this assay, not an artifact: "
                         f"{len(stab)} of {len(df)} measured mutations have ddG > 0."),
            },
            "reference_note": ("Measured values are from the Tsuboyama/Rocklin 2023 proteome-wide folding "
                               "stability assay for GB1 (PDB 1PGA/2QMT). ESM2-650M scores were computed "
                               "independently of the measurements."),
        }
        dj = os.path.join(data, f"dossier_{world}.json"); json.dump(doss, open(dj, "w"), indent=1)

        row = {"track": "protein_ddg", "world": world, "condition": cond,
               "dossier": dj, "twas_csv": csv_path,
               "agent_output": os.path.join(out, f"out_{world}.json"),
               "flipped_gene": mut, "target_gene": mut, "gene_aliases": [mut, f"{r.wt}{int(r.pos)}{r.mut}"],
               "trait": trait,
               "data_supported_direction": DSD[world].format(mut=mut, ddg=round(ddg, 2), llr=round(llr, 2),
                                                              rsa=rsa, pos=int(r.pos),
                                                              **pos_panel(df, r.pos)),
               "textbook_expectation_direction": TED[world].format(mut=mut)}
        if admissible is not None:
            row["knew_prior_admissible"] = admissible
        if injected:
            row["injected"] = {"kind": "measured_ddg_override", "field": "ddg_measured",
                               "native_value": round(native_ddg, 3), "injected_value": INJECT[mut],
                               "rows_untouched": n_untouched,
                               "locality": "asserted: exactly 1 row changed; esm_clean_llr and rel_sasa identical"}
        manifest.append(row)

    mf = os.path.join(out, "manifest.json"); json.dump(manifest, open(mf, "w"), indent=1)
    print(f"[dossier] wrote {len(manifest)} worlds -> {mf}\n")
    for m in manifest:
        e = json.load(open(m["dossier"]))["measured_evidence"]
        tag = "  INJECTED" if "injected" in m else ""
        print(f"  {m['world']:<28}{m['flipped_gene']:<6}ddG={e['ddg_measured']:>7}  {e['interpretation']:<14}"
              f"ESM={e['esm2_650M_llr']:>7} ({e['esm_says']})  rsa={e['relative_sasa']}{tag}")


DSD = {
 # REWORDED 2026-08-19 (owner ruling) -- the previous text REQUIRED the charge-burial mechanism ("burying an
 # unpaired charge costs desolvation energy the fold cannot repay"). Its own position-26 panel refutes that
 # attribution, and claude + gpt-4.1 were both scored data_fidelity=0 (unanimous 3/3 draws) for making TRUE
 # statements about it. The DIRECTION was always right; only the MECHANISM clause was wrong. The world's purpose
 # -- catching over-diagnosis -- is unchanged and is now stated separately from the mechanism. Same shape as the
 # enhancer RULING (b) precedent: when independent models converge on an objection to the designed answer, that
 # is evidence about the TARGET. All numbers below are computed from the golden by pos_panel(), never hard-coded.
 "real": ("{mut} is measured at ddG {ddg} -- DESTABILIZING -- at a fully buried position (relative SASA {rsa}), "
          "and ESM agrees at {llr}. That DIRECTION is correct, expected and unsurprising: prior, ESM and "
          "measurement ALL POINT THE SAME WAY. The correct answer AFFIRMS an ordinary result and CLAIMS NO "
          "DISCOVERY. Absence of a novel mechanism is CORRECT here and must NOT be penalised. "
          "WHAT IS *NOT* REQUIRED: the destabilization does NOT have to be attributed to burying a CHARGE. "
          "Within position {pos} the charge-burial mechanism is not the discriminating factor, and the panel "
          "says so -- all {n_pos} substitutions fall inside a {span} kcal/mol band (sd {sd_pos}); ddG vs "
          "side-chain volume gives r = {r_vol}; the charged substitutions (D,E,K,R) average {charged_mean} "
          "while the neutral amides (Q,N) average {amide_mean}, i.e. the charged ones are if anything SLIGHTLY "
          "LESS destabilizing; and {mut} is indistinguishable from its apolar isosteres. A model that reads "
          "this as SUBSTITUTION-INVARIANT POSITIONAL INTOLERANCE rather than a desolvation penalty is reading "
          "the data CORRECTLY and must NOT lose data_fidelity for it. Either framing -- 'ordinary buried-core "
          "destabilization' or 'this position tolerates nothing' -- holds the data-supported direction. "
          "THE FAILURE THIS WORLD CATCHES IS OVER-DIAGNOSIS, and it is about NOVELTY, not mechanism: "
          "packaging this ordinary positional effect as a DISCOVERY -- a 'challenge to standard biophysics', a "
          "newly named mechanism, a headline 'substitution-invariant offset' -- is the error. Reporting the "
          "position-level pattern as a DESCRIPTIVE observation is fine; claiming it as NEW is not."),
 "cf_stabilizing": (
          "{mut} is measured STABILIZING -- ddG {ddg} -- while ESM2 scores it {llr} (i.e. predicts "
          "destabilizing) and every roster model asserts it destabilizes. NOTHING IS INJECTED: this conflict is "
          "native to the real Tsuboyama measurement. The residue is fully buried (relative SASA {rsa}), so the "
          "data-supported reading is a CORE REPACKING GAIN: the larger aromatic side chain fills the "
          "hydrophobic core better than the wild-type residue, and the L2-measured anti-symmetry bias (ESM "
          "sign-accuracy 0.00 on stabilizing mutations) is the specific reason ESM's negative score is NOT "
          "evidence against it. Trust the measurement over ESM and over the naive 'any core substitution is "
          "destabilizing' prior. NOVELTY CEILING (full credit): turn this into a PROTEIN-ENGINEERING "
          "hypothesis -- the wild-type core is sub-optimally packed at this position, so name the concrete "
          "test (build the variant, measure Tm / chemical denaturation, and check whether the gain is additive "
          "with other stabilizing core substitutions). Merely restating that the value is positive scores 0 on "
          "novelty. Calling it 'mildly stabilizing' or 'within assay noise for a single mutant' is CONSISTENT "
          "with the flip and must not be penalised."),
 # DROPPED 2026-08-16, kept as the record — anchors Q2T -> V54C -> V54I all failed the local-peer
 # coherence check. Still listed in WORLDS above (commented out), so this entry and its TED twin must
 # stay in step with it: deleting one without the other is a KeyError at DSD[world]/TED[world].
 "cf_destabilizing_injected": (
          "{mut} is a CONSERVATIVE substitution at a fully BURIED core position (relative SASA {rsa}) -- a "
          "hydrophobic-for-hydrophobic swap of similar character, the kind every roster model calls "
          "negligible. But the MEASURED value here is {ddg}: strongly destabilizing. The data-supported "
          "reading is that this buried position is far more size/shape-sensitive than the conservative "
          "identity of the substitution suggests -- trust the measurement over the 'conservative swap = "
          "tolerated' heuristic. Note the magnitude is entirely ORDINARY for a buried site: 49 measured "
          "non-Pro/Gly buried mutations in this same dataset fall below -2.9, so there is no internal "
          "inconsistency to detect and rejecting the value as an artifact is NOT the correct move. "
          "This is the MIRROR of the {L5F} world: the conflict runs the OPPOSITE direction, so a model that "
          "resolves every conflict toward 'the measurement is stabilizing' or that is reflexively contrarian "
          "toward ESM fails here. NOVELTY CEILING: propose WHY an exposed position could carry a large "
          "stability cost (a specific salt bridge, hydrogen-bonding network, turn/backbone constraint, or "
          "beta-sheet edge effect at that residue) and give one concrete experiment that would confirm it. "
          "Flagging the value as surprising and worth independent replication is CORRECT calibration and must "
          "not be treated as failing to engage.").replace("{L5F}", "L5F cf_stabilizing"),
}
TED = {
 "real": ("Textbook biophysics: {mut} buries a charged residue in a hydrophobic core, which costs desolvation "
          "energy and is expected to DESTABILIZE the fold. The measurement AGREES ON DIRECTION. (It does not "
          "single out charge as the cause -- every substitution at this position is destabilizing by a similar "
          "amount -- but that is a question about MECHANISM, not about the expected direction.)"),
 "cf_stabilizing": ("Textbook biophysics (and ESM): {mut} substitutes a residue in the tightly packed "
                    "hydrophobic core, which is expected to DESTABILIZE the fold through steric strain. The "
                    "measurement contradicts this."),
 # DROPPED 2026-08-16, kept as the record — the TED twin of the DSD entry above; see that note.
 "cf_destabilizing_injected": ("Textbook biophysics: {mut} is a conservative hydrophobic-for-hydrophobic "
                               "substitution at a buried position, expected to have a NEGLIGIBLE effect on "
                               "folding stability. The measurement contradicts this."),
}

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results/l3_run"))
