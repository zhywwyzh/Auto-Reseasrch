"""protein_ddg L1 world-builder — inject ONE structure-prep defect per world as a DELTA on the real substrate.

ONE world per issue-type (clean + 9), n=1, consistent with every other track. Each world emits a per-cell DIRECTORY
(the agent's `data_dir`) holding ONE real structure file (.pdb or .cif) + structure_meta.json, and appends a manifest
cell carrying the ground truth the SHARED grade_generic reads: issue_type / issue_present / canonical_checks /
diagnose_keywords / action_keywords / correct_action / affected_entities (+ requires_external_evidence /
abstention_question for the abstain control). See grade_generic.py.

CLEAN control + chain protein = GB1 2QMT (real 1.05 A X-ray). The L1-CLEANED DATASET is what flows L1->L2->L3, so the
suite is CENTERED on GB1: clean, abstain, missing_atoms, steric_clash, heteroatom_ligand, non_standard_residue and
numbering_reconciliation are all hosted on real GB1 2QMT; multi_model uses the real GB1 NMR ensemble 3GB1.

Crambin 1EJG is kept for EXACTLY TWO worlds where GB1 physically cannot supply an honest DELTA (2QMT has NEITHER
explicit hydrogens NOR alternate conformations):
  - missing_hydrogens -> crambin (delete its 419 real H; 2QMT has no H to remove -> no honest delta on GB1).
  - unresolved_altloc -> crambin (re-introduce its REAL A/B/C conformers; 2QMT has no altloc atoms).

Run build_substrate.py first (writes data/clean/gb1.pdb + data/clean/crambin.pdb). Then:  world_builder.py
"""
import os, sys, json, shutil, copy
import numpy as np
import pdb_utils as P

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
CLEAN = os.path.join(HERE, "data", "clean")
RUN_DIR = os.path.join(HERE, "L1", "results", "protein_ddg_l1_run")
BB = {"N", "CA", "C", "O", "CB"}                       # backbone + CB retained when truncating a side chain

# ---------------- GROUND TRUTH per issue = the grading contract (CHECK / DIAGNOSE / DO) --------------------------
GT = {
 "clean": dict(present=False,
   canonical_checks=["missing atom|complete|atom count|expected atoms", "hydrogen|protonat", "altloc|alternate conform",
                     "clash|contact|distance", "hetatm|heteroatom|water|ligand", "chain break|gap|continuity",
                     "b.?factor|occupanc"],
   diagnose_keywords=[], action_keywords=[],
   correct_action="No data-integrity defect — GB1 (2QMT) chain A is a complete (all standard-residue heavy atoms), "
                  "single-conformer, single-model, standard-residue X-ray structure; proceed to ddG prep. Adding "
                  "hydrogens before energy work is routine preparation of any X-ray structure, NOT a defect to flag.",
   affected=[]),
 "missing_atoms": dict(present=True,
   # JUDGMENT: the missing atoms are AT THE MUTATION SITE (LEU7). The WT reference state of ddG(L7A) needs the COMPLETE
   # native LEU7, so a truncated side chain at the site is NOT ignorable and "we mutate it to Ala anyway" is WRONG.
   canonical_checks=["missing atom|absent atom|incomplete residue|expected atoms|side.?chain|cg\\b|cd1|cd2",
                     "resid.*7|residue 7|position 7|site|mutation site|target|leu7|leu ?7"],
   diagnose_keywords=["missing side.?chain", "missing atom", "incomplete residue", "truncated side.?chain",
                      "absent.*(cg|cd1|cd2)", "leu7.*incomplete|incomplete.*leu7", "side.?chain.*(site|mutation)"],
   action_keywords=["rebuild.*(side.?chain|leu7|residue 7|site|mutation)", "rebuild", "model.* missing",
                    "add.*(cg|cd1|cd2|missing atom)", "complete the side.?chain", "reconstruct.*side.?chain", "pdbfixer", "scwrl"],
   correct_action="The mutation-site residue LEU7 is missing its side-chain atoms (CG, CD1, CD2). ddG(L7A) needs the "
                  "COMPLETE native LEU7 as the wild-type reference, so the truncated side chain AT THE SITE must be "
                  "REBUILT (PDBFixer/SCWRL) before ddG — it is NOT a minor/ignorable defect, and 'we mutate it to Ala "
                  "anyway so it doesn't matter' is wrong (the WT state still requires the full LEU7 side chain).",
   affected=["A/LEU7 (the mutation site) is missing side-chain atoms CG, CD1, CD2"]),
 "missing_hydrogens": dict(present=True,
   # JUDGMENT (settled prep-awareness): heavy-atom-only is the NORMAL delivered X-ray state, NOT a corruption to
   # reject. The correct call is to ADD H / ASSIGN PROTONATION STATES as required prep; rejecting the file as
   # unusable/corrupt is the wrong judgment, and a bare "no H present" (no action) is only detection.
   canonical_checks=["hydrogen|element ?== ?.?H|no ?H|count.*H|zero H|0 H", "protonat|prep|energy|force ?field|reduce|pdb2pqr"],
   diagnose_keywords=["no hydrogen", "missing hydrogen", "not protonated", "unprotonated", "hydrogens absent",
                      "lacks hydrogen", "requires protonation", "must be protonated", "protonation.*(required|needed|prep)"],
   action_keywords=["add hydrogen", "protonat", "reduce", "h\\+\\+", "propka", "pdb2pqr", "openmm.* addhydrogen",
                    "pdbfixer", "assign.*protonation", "titrat"],
   correct_action="A heavy-atom-only structure (no hydrogens) is the NORMAL delivered X-ray state, NOT a corruption to "
                  "reject — the required prep is to ADD hydrogens and ASSIGN protonation states (Reduce/PDB2PQR/"
                  "PDBFixer/PROPKA), including titratable residues in the mutation-site (LEU18) environment, before any "
                  "energy-based ddG. Flagging the file as unusable/corrupt over the absent H is the wrong judgment.",
   affected=["all residues lack hydrogens (heavy-atom-only) — protonation is required PREP, not a data-integrity defect"]),
 "steric_clash": dict(present=True,
   # JUDGMENT: the ~0.9 A sub-VDW clash sits AT THE MUTATION SITE (a LEU7 side-chain atom overlaps a first-shell
   # neighbour), so it corrupts the local ddG environment and MUST be resolved locally -- it is NOT a disulfide, NOT a
   # dismissible "minor contact", and does NOT justify a blanket rebuild of the otherwise-clean structure.
   canonical_checks=["clash|steric|overlap|bad contact", "distance|vdw|van der waals|< ?[12]\\.|angstrom|0\\.9"],
   diagnose_keywords=["steric clash", "clash", "atomic overlap", "bad contact", "overlapping atoms", "vdw overlap",
                      "sub.?vdw", "hard clash"],
   action_keywords=["minimiz", "relax", "repair.*clash", "fix.* clash", "resolve.*clash", "rebuild.*side.?chain",
                    "energy minimiz", "refine.* geometry", "remodel"],
   correct_action="A genuine sub-VDW steric clash (~0.9 A non-bonded contact) sits AT the mutation site — a LEU7 "
                  "side-chain atom overlaps a first-shell neighbour. Because it corrupts the local ddG environment of "
                  "the site, it MUST be resolved by LOCAL energy minimization / side-chain rebuild at the site before "
                  "ddG. It is not a disulfide and not a dismissible 'minor contact', and it does NOT warrant a blanket "
                  "rebuild of the whole (otherwise clean) structure.",
   affected=["a sub-VDW (~0.9 A) clash between a LEU7 (mutation-site) side-chain atom and a first-shell neighbour"]),
 "unresolved_altloc": dict(present=True,
   # JUDGMENT: the alternate conformations sit AT THE MUTATION SITE (ILE7, altloc A occ 0.55 / B occ 0.45). The correct
   # action is to SELECT the single HIGHEST-OCCUPANCY conformer (A) at the site so the WT reference and the I7V mutation
   # act on ONE unambiguous side chain. Bare "altlocs present", keeping both, or picking arbitrarily scores low.
   canonical_checks=["altloc|alternate conform|alternate location|alt ?conf|\\.altloc|get_altloc", "occupanc"],
   diagnose_keywords=["altloc", "alternate conformation", "alternate location", "multiple conformers", "two conformers",
                      "partial occupancy", "a/b conformer", "conformer.*(site|mutation|7)|(site|mutation|7).*conformer"],
   action_keywords=["highest.?occupan", "select.*(single )?conformer", "pick.*conformer", "choose.*conformer",
                    "keep.*(conformer|altloc) ?a\\b", "resolve.* altloc", "collapse.*conformer", "single conformer"],
   correct_action="The mutation-site residue (ILE7) is modeled in TWO alternate conformations (altloc A occ 0.55, "
                  "altloc B occ 0.45). Before ddG you must SELECT the SINGLE highest-occupancy conformer (A) AT THE "
                  "SITE, so the WT reference and the I7V mutation are applied to ONE unambiguous side chain — do NOT "
                  "keep both (double-counting atoms), do NOT pick arbitrarily, and note the ambiguity is AT the site.",
   affected=["ILE7 (the mutation site) has A/B alternate conformers (occ 0.55/0.45); further altlocs at residues 12, 13"]),
 "multi_model": dict(present=True,
   # JUDGMENT: an NMR ensemble has NO single coordinate set. The correct action is to SELECT ONE representative model
   # and JUSTIFY it by how well it represents the mutation site (site 7 is well-ordered across the ensemble; the model
   # closest to the ensemble mean at the site is the principled pick). "32 models present" (detection) or blindly
   # taking model 1 / averaging all models scores low -- note "first model" is deliberately NOT an action keyword.
   canonical_checks=["model|ensemble|nmr|nummodel|n_?models|len\\(.*model|get_models",
                     "which model|per.?model|representative|site|resid.*7|rmsf|coverage"],
   diagnose_keywords=["multiple models", "nmr ensemble", "multi.?model", "more than one model", "ensemble of",
                      "32 models", "no single coordinate"],
   action_keywords=["select.*(representative|single|one).* model", "choose.* model", "representative model",
                    "model.*(best|closest).*(site|mean|ensemble)", "model.*(cover|carr|represent).*site",
                    "justif.*model", "pick.* model.*(because|site|represent|closest)"],
   correct_action="The file is a 32-model NMR ensemble (3GB1) — there is NO single coordinate set for ddG. Select ONE "
                  "representative model and JUSTIFY the choice by how well it represents the mutation site: site 7 is "
                  "well-ordered across the ensemble (CA RMSF ~0.05 A), and the model whose site-7 geometry is closest "
                  "to the ensemble mean (model 4) is the principled representative (model 1 is acceptable ONLY if "
                  "justified by that site-level agreement). Merely reporting '32 models', blindly using model 1, or "
                  "averaging all models is not sufficient.",
   affected=["32-model NMR ensemble; no single coordinate set — pick the model best representing the mutation site (7)"]),
 "heteroatom_ligand": dict(present=True,
   canonical_checks=["hetatm|heteroatom|water|hoh|ligand|ion|solvent", "resname|record"],
   diagnose_keywords=["water", "hoh", "heteroatom", "hetatm", "ligand", "ion", "solvent molecules", "isopropanol", "phosphate", "mpd"],
   action_keywords=["strip.* water", "remove.* water", "remove.* hetatm", "delete.* solvent", "drop.* ion", "decide.* ligand", "clean.* solvent"],
   correct_action="Strip the crystallographic waters and cryoprotectant/buffer ligands (decide whether any is relevant) before ddG.",
   affected=["real 2QMT HETATM: crystallographic waters (HOH) + ligands IPA (isopropanol), MRD (MPD), PO4 (phosphate)"]),
 "non_standard_residue": dict(present=True,
   # JUDGMENT: MSE is selenomethionine = a MODIFIED form of MET, NOT a buffer/hetero-ligand and NOT an unknown/foreign
   # residue. Recognize it as MET and CONVERT/treat as such (SE->SD, retain). It is written as HETATM at the
   # N-terminus, so naively stripping "all HETATM" truncates the chain, and rejecting it as unknown is the wrong call.
   # diagnose_keywords deliberately require MSE=selenomethionine=MET (a bare "non-standard/unknown residue" is the
   # WRONG judgment and earns no diagnose credit).
   canonical_checks=["mse|selenomethionine|modified residue|hetatm|resname", "met|methionine|selenium|se\\b|sd\\b"],
   diagnose_keywords=["selenomethionine", "mse.*(is|=|->|to|as).*met", "modified.*(met|methionine)",
                      "seleno.*methionine", "mse.*methionine", "modified methionine"],
   action_keywords=["convert.* met", "treat.* as met", "mse.*->.*met", "map.* to methionine", "rename.* mse.*met",
                    "se.*->.*sd", "standardiz.*met", "keep.*mse.*(as )?met"],
   correct_action="MSE is selenomethionine — a MODIFIED form of MET (selenium replaces the S-delta sulfur), NOT a "
                  "buffer/hetero-ligand and NOT an unknown residue. Recognize it as MET and convert/treat it as such "
                  "(SE->SD, retain the residue) before ddG. It is the N-terminal residue written as HETATM, so naively "
                  "stripping it as a HETATM ligand would truncate the chain, and flagging it as a foreign/unknown "
                  "residue to reject is the wrong judgment.",
   affected=["MSE1 (selenomethionine, written as HETATM) = modified MET1 — convert to MET, do NOT strip as a ligand"]),
 "numbering_reconciliation": dict(present=True,
   # JUDGMENT: a SUBTLE off-by-one -- auth_seq_id = label_seq_id + 1. The task claims site 7 = LEU (L7A), but AUTHOR
   # position 7 in the file is ILE (label 6), a near-isosteric LEU look-alike; the true LEU7 (label 7) is at AUTHOR 8.
   # The model must reconcile label vs auth (SEQRES vs ATOM) AND verify the WT identity at the site -- a bare "author
   # numbering present" note, or accepting author-7 (ILE) as the site, scores low.
   canonical_checks=["auth|label|seq_?id|numbering|offset|renumber|off.?by.?one|seqres.*atom|atom.*seqres",
                     "wt|wild.?type|residue identity|resname|expected residue|leu|ile|claimed"],
   diagnose_keywords=["auth.*label|label.*auth", "off.?by.?one|offset", "seqres.*atom|atom.*seqres",
                      "wt mismatch|wild.?type mismatch|wrong residue|identity mismatch|does not match",
                      "ile.*(not|!=|vs|instead).*leu|leu.*(not|!=|vs|expected).*ile|residue.*7.*ile|ile.*(at|position).*7"],
   action_keywords=["reconcile", "remap", "map.* auth.* label", "verify.* wt|verify.* residue|verify.* identity",
                    "confirm.* residue|confirm.* identity", "renumber", "align.* numbering", "check.* identity",
                    "correct.*(site|residue).*(before|mutation)"],
   correct_action="The mmCIF author numbering (auth_seq_id) is offset by +1 from the label/SEQRES numbering (a subtle "
                  "off-by-one). The task claims the mutation site (7) is LEU (L7A), but the residue at AUTHOR position 7 "
                  "is ILE (label 6) — a near-isosteric LEU look-alike; the true LEU7 (label 7) sits at AUTHOR position "
                  "8. Before ddG you must reconcile label_seq_id vs auth_seq_id (SEQRES<->ATOM) AND verify the WT "
                  "identity at the intended site, mapping L7A onto the correct LEU — do NOT accept author-7 (ILE) as "
                  "the site.",
   affected=["auth_seq_id = label_seq_id + 1 (subtle off-by-one)",
             "author position 7 is ILE (look-alike), not the claimed LEU; the true LEU7 is at author 8"]),
 "abstain": dict(present=False, requires_external_evidence=True,
   abstention_question=("The structure is GB1, the B1 domain of protein G (2QMT). Its surface turns/loops — e.g. the "
        "beta1-beta2 turn around Lys10-Thr11 and the loop around Asp40-Glu42 — show the HIGHEST B-factors of the chain "
        "and genuine conformational mobility: this is REAL, biologically flexible surface, not a modelling error. For "
        "a ddG calculation at a WELL-ORDERED buried core site (e.g. Leu7), should the analyst REJECT or 'repair'/"
        "truncate the structure because of these flexible loops, or RETAIN it and proceed? The correct answer is "
        "RETAIN — genuine flexibility (high B-factor / a mobile loop) is not a data-integrity defect to fix; only note "
        "it as a local confidence caveat. It CANNOT be resolved from the coordinates alone."),
   canonical_checks=["b.?factor|temperature factor|flexib|disorder|mobile|loop", "occupanc|complete|atom count"],
   diagnose_keywords=["real flexibility", "genuine flexib", "mobile loop", "high b.?factor but real", "not a defect", "biological flexibility"],
   action_keywords=["retain", "keep", "do not repair", "do not reject", "proceed", "note.* caveat", "abstain"],
   correct_action="Do NOT reject/repair the structure over the genuinely flexible high-B GB1 surface loops; RETAIN it and note the local flexibility as a caveat.",
   affected=["GB1 mobile surface loops (beta1-beta2 turn near Lys10-Thr11; loop near Asp40-Glu42), high B-factor but real"]),
}

# ---------------- injection functions: take clean lines (list[str]) + return output lines / files -----------------
def _gb1_lines():                                                # CLEAN chain protein (GB1 2QMT) — base for most worlds
    return P.read_atoms(os.path.join(CLEAN, "gb1.pdb"))

def _crambin_lines():                                            # AUX substrate (crambin 1EJG, real H + collapsed altlocs)
    return P.read_atoms(os.path.join(CLEAN, "crambin.pdb"))

def inj_clean(lines):
    return lines

def inj_missing_atoms(lines, site=7):
    """On GB1: truncate the MUTATION-SITE residue (LEU7) to its backbone+CB heavy atoms — i.e. delete its side-chain
    atoms CG, CD1, CD2. The completeness defect is now AT the ddG site: the WT reference state of ddG(L7A) needs the
    full native LEU7, so the missing side chain must be rebuilt (it is not ignorable)."""
    out = []
    for l in lines:
        if P.resseq(l) == site and P.name(l) not in BB and P.element(l) != "H":
            continue                                           # drop LEU7 side-chain heavy atoms (CG, CD1, CD2)
        if P.resseq(l) == site and P.element(l) == "H" and P.name(l) not in ("H", "HA", "HB", "HB1"):
            continue                                           # drop orphaned side-chain H (no-op on GB1: no H)
        out.append(l)
    return out

def inj_missing_hydrogens(lines):
    return [l for l in lines if P.element(l) != "H"]

def inj_steric_clash(lines, site=7):
    """Create a hard sub-VDW clash (0.90 A) AT THE MUTATION SITE: move the closest MUTATION-SITE (LEU7) heavy atom into
    its nearest genuinely NON-BONDED heavy-atom neighbour (a first-shell residue). Exclude sulfur, require the partner
    >=3 residues away and a starting separation > 2.6 A so the moved pair is a true non-bonded contact, not a covalent
    bond. The clash therefore corrupts the local ddG environment OF THE SITE."""
    heavy = [(i, l) for i, l in enumerate(lines) if P.element(l) not in ("H", "S")]
    coords = {i: np.array(P.xyz(l)) for i, l in heavy}
    best = None
    for ia, la in heavy:
        if P.resseq(la) != site or P.name(la) in ("N", "CA", "C", "O"):    # move a SITE SIDE-CHAIN atom (keep backbone)
            continue
        for ib, lb in heavy:
            if P.resseq(lb) == site:
                continue
            if abs(P.resseq(la) - P.resseq(lb)) < 3:           # skip bonded / near-neighbour residues
                continue
            d = np.linalg.norm(coords[ia] - coords[ib])
            if d > 2.6 and (best is None or d < best[0]):
                best = (d, ia, ib)
    _, ia, ib = best
    pa, pb = coords[ia], coords[ib]
    v = pb - pa; v = v / (np.linalg.norm(v) or 1.0)
    newa = pb - v * 0.90                                       # move the SITE atom ia to 0.90 A from neighbour ib
    out = list(lines)
    out[ia] = P.set_coords(out[ia], float(newa[0]), float(newa[1]), float(newa[2]))
    return out

def inj_unresolved_altloc(lines, site=7):
    """Re-introduce crambin's REAL alternate conformations (raw 1EJG) AT THE MUTATION SITE (ILE7, real A/B conformers)
    plus two further real-altloc residues, collapse the rest. `lines` = the collapsed crambin clean chain. The kept
    altloc atoms are genuine deposited coordinates + occupancies, so the conformer ambiguity now sits ON the ddG site."""
    KEEP = {site, 12, 13}                                       # ILE7 (site, real A/B) + residues 12,13 (real A/B) in 1EJG
    raw = [l for l in P.read_atoms(os.path.join(RAW, "1EJG.pdb")) if P.chain(l) == "A" and P.resname(l) in P.STD_AA]
    out = []
    for l in lines:                                            # start from the collapsed clean chain
        if P.resseq(l) not in KEEP:
            out.append(l)
    for l in raw:                                              # add the REAL multi-altloc atoms for the KEEP residues
        if P.resseq(l) in KEEP:
            out.append(l)
    out.sort(key=lambda a: (P.resseq(a), a[12:16], a[16]))
    return out

def inj_heteroatom(lines):
    """On GB1: retain the REAL crystallographic HETATM records deposited in 2QMT chain A — waters (HOH) plus the
    cryoprotectant/buffer ligands IPA (isopropanol), MRD (MPD) and PO4 (phosphate). Zero fabrication: these are the
    genuine deposited solvent/ligand atoms the clean control strips out."""
    out = list(lines)
    het = [l for l in P.read_atoms(os.path.join(RAW, "2QMT.pdb"), records=("HETATM",)) if P.chain(l) == "A"]
    out.extend(het)
    return out

def inj_non_standard_residue():
    """From REAL GB1 2QMT: keep ONLY the protein polymer (drop waters + all ligands IPA/MRD/PO4), relabel MET1 -> MSE
    (SD->SE) so the ONLY non-standard residue in the world is the selenomethionine. Returns lines."""
    raw = [l for l in P.read_atoms(os.path.join(RAW, "2QMT.pdb"), records=("ATOM  ", "HETATM"))
           if P.chain(l) == "A" and P.resname(l) in P.STD_AA]
    out = []
    for l in raw:
        if P.resseq(l) == 1 and P.resname(l) == "MET":
            l = P.set_record(P.set_resname(l, "MSE"), "HETATM")
            if P.name(l) == "SD":
                l = P.set_element(P.set_atomname(l, "SE"), "SE")
        out.append(l)
    return out

def write_cif_numbering(path, lines, auth_offset=1):
    """Emit an mmCIF (from GB1) whose auth_seq_id = label_seq_id + offset (a real author-vs-label numbering hazard). A
    SUBTLE off-by-one (offset +1): Biopython's MMCIFParser keys residues on auth_seq_id, so the parsed chain runs 2-57
    while label_seq_id runs 1-56. Author position 7 is then ILE (label 6) -- a near-isosteric look-alike for the claimed
    LEU -- while the true LEU7 (label 7) sits at author 8; catching it requires SEQRES<->ATOM + WT-identity checks."""
    reskeys = []
    for l in lines:
        k = P.reskey(l)
        if k not in reskeys: reskeys.append(k)
    label_of = {k: i + 1 for i, k in enumerate(reskeys)}
    cols = ["group_PDB", "id", "type_symbol", "label_atom_id", "label_alt_id", "label_comp_id", "label_asym_id",
            "label_entity_id", "label_seq_id", "pdbx_PDB_ins_code", "Cartn_x", "Cartn_y", "Cartn_z", "occupancy",
            "B_iso_or_equiv", "pdbx_formal_charge", "auth_seq_id", "auth_comp_id", "auth_asym_id", "auth_atom_id",
            "pdbx_PDB_model_num"]
    with open(path, "w") as f:
        f.write("data_2QMT_renum\n#\n_entry.id 2QMT_renum\n#\nloop_\n")
        for c in cols: f.write(f"_atom_site.{c}\n")
        for i, l in enumerate(lines, 1):
            lab = label_of[P.reskey(l)]
            x, y, z = P.xyz(l)
            row = ["ATOM", i, P.element(l) or "C", P.name(l), ".", P.resname(l), "A", "1", lab, "?",
                   f"{x:.3f}", f"{y:.3f}", f"{z:.3f}", f"{P.occ(l):.2f}", f"{P.bfac(l):.2f}", "?",
                   lab + auth_offset, P.resname(l), "A", P.name(l), "1"]
            f.write(" ".join(str(v) for v in row) + "\n")
        f.write("#\n")

# ---------------- world writer + manifest ------------------------------------------------------------------------
def _meta_for(issue):
    base = json.load(open(os.path.join(CLEAN, "structure_meta.json")))       # GB1 2QMT (site 7, LEU, L7A)
    if issue == "missing_hydrogens":                                        # crambin-hosted -> crambin meta (site 18)
        return json.load(open(os.path.join(CLEAN, "crambin_meta.json")))     # crambin 1EJG (site 18, LEU, L18A)
    if issue == "unresolved_altloc":                                        # crambin, altloc is AT the site -> ILE7
        cm = json.load(open(os.path.join(CLEAN, "crambin_meta.json")))
        return dict(cm, target_site=7, target_mutation="I7V", claimed_wt_residue="ILE")  # crambin ILE7 carries A/B altloc
    if issue == "multi_model":                                              # GB1 3GB1 NMR ensemble
        return dict(base, structure_id="3GB1", source="https://files.rcsb.org/download/3GB1.pdb",
                    resolution_A=None, method="SOLUTION NMR")
    if issue == "numbering_reconciliation":                                 # subtle +1 offset in the .cif; meta CLAIMS
        return dict(base, numbering="author")                              # site 7 = LEU (author), but file auth-7 = ILE
    return base                                                             # clean / abstain / missing_atoms / steric_clash /
                                                                            # heteroatom_ligand / non_standard_residue -> GB1 meta


def build():
    if not os.path.exists(os.path.join(CLEAN, "gb1.pdb")) or not os.path.exists(os.path.join(CLEAN, "crambin.pdb")):
        raise SystemExit("[world_builder] run build_substrate.py first (data/clean/gb1.pdb + crambin.pdb missing)")
    os.makedirs(os.path.join(RUN_DIR, "data"), exist_ok=True)
    gb1 = _gb1_lines()
    crambin = _crambin_lines()
    cryst_gb1 = P.cryst1(os.path.join(RAW, "2QMT.pdb"))
    cryst_cr = P.cryst1(os.path.join(RAW, "1EJG.pdb"))
    manifest, cell = [], 0
    for issue, gt in GT.items():
        d = os.path.join(RUN_DIR, "data", f"cell{cell:03d}")
        os.makedirs(d, exist_ok=True)
        if issue == "multi_model":
            shutil.copy2(os.path.join(RAW, "3GB1.pdb"), os.path.join(d, "structure.pdb"))
        elif issue == "non_standard_residue":
            P.write_pdb(os.path.join(d, "structure.pdb"), inj_non_standard_residue(), cryst=cryst_gb1)
        elif issue == "numbering_reconciliation":
            write_cif_numbering(os.path.join(d, "structure.cif"), gb1)
        elif issue == "missing_hydrogens":                                  # crambin (2QMT has no H to delete)
            P.write_pdb(os.path.join(d, "structure.pdb"), inj_missing_hydrogens(list(crambin)), cryst=cryst_cr)
        elif issue == "unresolved_altloc":                                 # crambin (2QMT has no altloc atoms)
            P.write_pdb(os.path.join(d, "structure.pdb"), inj_unresolved_altloc(list(crambin)), cryst=cryst_cr)
        else:                                                              # GB1-hosted worlds
            fn = {"clean": inj_clean, "missing_atoms": inj_missing_atoms, "steric_clash": inj_steric_clash,
                  "heteroatom_ligand": inj_heteroatom, "abstain": inj_clean}[issue]
            P.write_pdb(os.path.join(d, "structure.pdb"), fn(list(gb1)), cryst=cryst_gb1)
        json.dump(_meta_for(issue), open(os.path.join(d, "structure_meta.json"), "w"), indent=1)
        world = {"cell": cell, "world_label": issue, "issue_type": issue, "issue_present": gt["present"],
                 "agent_input": d, "agent_output": f"{RUN_DIR}/out_cell{cell:03d}.json",
                 "correct_action": gt["correct_action"], "affected_entities": gt.get("affected", []),
                 "canonical_checks": gt.get("canonical_checks", []),
                 "diagnose_keywords": gt.get("diagnose_keywords", []),
                 "action_keywords": gt.get("action_keywords", [])}
        if gt.get("requires_external_evidence"):
            world["requires_external_evidence"] = True; world["abstention_question"] = gt["abstention_question"]
        manifest.append(world); cell += 1
    json.dump(manifest, open(os.path.join(RUN_DIR, "manifest.json"), "w"), indent=1)
    print(f"[world_builder] wrote {len(manifest)} worlds ({len(GT)} issues) -> {RUN_DIR}/manifest.json")
    return manifest


if __name__ == "__main__":
    build()
