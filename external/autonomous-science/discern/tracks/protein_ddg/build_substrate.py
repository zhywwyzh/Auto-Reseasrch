"""protein_ddg L1 substrate builder — carve the REAL clean structure from a downloaded PDB.

NON-NEGOTIABLE (ADD_A_TRACK.md §1): the clean substrate is REAL public data; L1 issues are injected as DELTAs on it.

CLEAN SUBSTRATE = GB1, PDB 2QMT (Frericks Schmidt et al. 2007, 1.05 A X-ray of the 56-residue B1 domain of
streptococcal protein G). GB1 is the CHAIN PROTEIN: only the L1-CLEANED DATASET flows L1->L2->L3 (no QC verdicts
travel), so the structure L1 certifies clean must be the SAME protein L2/L3 predict ddG on — and that is GB1,
because it is a canonical Tsuboyama/Rocklin 2023 mega-scale folding-stability domain (measured ddG ground truth
exists). 2QMT chain A is a single model, has NO alternate conformations, and its heavy atoms are byte-honest real
deposited coordinates — so the CLEAN control has NO synthetic tell. (X-ray structures carry no explicit hydrogens;
routine protonation before energy calc is normal downstream prep, NOT a data-integrity defect of the deposited file.)

AUXILIARY SUBSTRATE = CRAMBIN, PDB 1EJG (Jelsch et al. 2000, 0.54 A). Kept ONLY for the two defect worlds GB1
physically cannot host as an honest DELTA: 1EJG is the one small domain in our download carrying REAL explicit
HYDROGEN atoms (419 H, chain A) AND REAL alternate conformations (A/B/C altloc atoms) — the two facts the
missing_hydrogens / unresolved_altloc worlds need to be genuine deltas rather than synthesized controls (2QMT has
neither). Every other world is re-hosted on GB1; multi_model uses the real GB1 NMR ensemble 3GB1.

Structures come from RCSB (files.rcsb.org). The Rocklin/Tsuboyama 2023 data (Zenodo 10.5281/zenodo.7992926) is the
DOWNSTREAM L2/L3 ddG truth; L1 needs only the real structure.

Output (tracks/protein_ddg/data/clean/):
  gb1.pdb + structure_meta.json          -> the CLEAN control (the dataset that flows to L2/L3)
  crambin.pdb + crambin_meta.json        -> auxiliary substrate for missing_hydrogens / unresolved_altloc
  data/data_dictionary.json
usage: build_substrate.py   (raw PDBs 2QMT / 3GB1 / 1EJG must be in data/raw/ — downloaded from files.rcsb.org)
"""
import os, sys, json, urllib.request
import pdb_utils as P

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
CLEAN = os.path.join(HERE, "data", "clean")
RCSB = "https://files.rcsb.org/download/{}"

# CLEAN control = GB1 2QMT. Real downstream ddG target: a WELL-ORDERED buried core substitution, GB1 Leu7 -> Ala
# (LEU7 mean B ~11.6 A^2, buried in the beta1 strand). The claimed WT identity is CORRECT here (LEU at author-position
# 7) — only the numbering_reconciliation world perturbs it. GB1 flows L1->L2->L3.
META = {"structure_id": "2QMT", "source": "RCSB PDB (https://files.rcsb.org/download/2QMT.pdb)",
        "protein": "protein G B1 domain (GB1)", "chain": "A", "resolution_A": 1.05, "method": "X-RAY DIFFRACTION",
        "target_site": 7, "numbering": "author", "target_mutation": "L7A", "claimed_wt_residue": "LEU",
        "task_note": "Point-mutation folding-stability (ddG) prediction on GB1; verify the structure is analysis-ready "
                     "(complete heavy atoms, single-conformer, single-model, standard residues, clash-free, mutation "
                     "site unambiguously located) before ddG. Adding hydrogens is routine prep, not a defect."}

# AUXILIARY substrate meta (crambin 1EJG): used ONLY by the missing_hydrogens / unresolved_altloc worlds. Real
# crambin ddG target Leu18 -> Ala (buried core); claimed WT (LEU@18) is CORRECT on this structure.
CRAMBIN_META = {"structure_id": "1EJG", "source": "RCSB PDB (https://files.rcsb.org/download/1EJG.pdb)",
        "protein": "crambin", "chain": "A", "resolution_A": 0.54, "method": "X-RAY DIFFRACTION",
        "target_site": 18, "numbering": "author", "target_mutation": "L18A", "claimed_wt_residue": "LEU",
        "task_note": "Point-mutation folding-stability (ddG) prediction; verify the structure is analysis-ready before ddG."}


def _ensure_raw(ids=("2QMT", "3GB1", "1EJG")):
    os.makedirs(RAW, exist_ok=True)
    for i in ids:
        for ext in (".pdb", ".cif"):
            dst = os.path.join(RAW, i + ext)
            if not os.path.exists(dst):
                print(f"[substrate] downloading {i}{ext}")
                req = urllib.request.Request(RCSB.format(i + ext), headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=120) as r, open(dst, "wb") as f:
                    f.write(r.read())


def collapse_altlocs(lines):
    """Collapse to ONE conformer PER RESIDUE (not per atom). For each residue pick the altLoc with the highest total
    occupancy, keep only atoms whose altLoc is blank or that label, force a single resname (the chosen conformer's
    identity), blank the altLoc, set occupancy 1.00 -> a chemically consistent single-conformer chain. (2QMT has NO
    altlocs so this is a no-op there; 1EJG carries real Pro22/Ser22, Ile25/Leu25 microheterogeneity it must resolve.)
    """
    from collections import Counter
    byres = {}
    for l in lines:
        byres.setdefault((P.chain(l), P.resseq(l), P.icode(l)), []).append(l)
    out = []
    for key, atoms in byres.items():
        alt_occ = {}
        for a in atoms:
            if a[16] != " ":
                alt_occ[a[16]] = alt_occ.get(a[16], 0.0) + P.occ(a)
        if alt_occ:
            target = max(alt_occ, key=lambda k: (alt_occ[k], k == "A", -ord(k)))
            tnames = [P.resname(a) for a in atoms if a[16] == target]
            rid = Counter(tnames).most_common(1)[0][0] if tnames else P.resname(atoms[0])
            kept = [a for a in atoms if a[16] in (" ", target)]
        else:
            rid, kept = P.resname(atoms[0]), atoms
        for a in kept:
            out.append(P.set_resname(P.set_occ(P.set_altloc(a, " "), 1.00), rid))
    out.sort(key=lambda a: int(a[6:11]))
    return out


def build():
    _ensure_raw()
    os.makedirs(CLEAN, exist_ok=True)

    # ---- CLEAN control = GB1 2QMT chain A, STANDARD-residue protein polymer only (drop all HETATM waters/ligands).
    #      2QMT has no altlocs -> collapse is a no-op; heavy atoms kept byte-honest (no atom-name re-justification).
    gb1_src = os.path.join(RAW, "2QMT.pdb")
    gb1_atoms = [l for l in P.read_atoms(gb1_src) if P.chain(l) == "A" and P.resname(l) in P.STD_AA]
    gb1_clean = collapse_altlocs(gb1_atoms)
    P.write_pdb(os.path.join(CLEAN, "gb1.pdb"), gb1_clean, cryst=P.cryst1(gb1_src))
    json.dump(META, open(os.path.join(CLEAN, "structure_meta.json"), "w"), indent=1)

    # ---- AUXILIARY = crambin 1EJG chain A, altlocs collapsed, real heavy atoms + real hydrogens kept.
    cr_src = os.path.join(RAW, "1EJG.pdb")
    cr_atoms = [l for l in P.read_atoms(cr_src) if P.chain(l) == "A" and P.resname(l) in P.STD_AA]
    cr_clean = collapse_altlocs(cr_atoms)
    P.write_pdb(os.path.join(CLEAN, "crambin.pdb"), cr_clean, cryst=P.cryst1(cr_src))
    json.dump(CRAMBIN_META, open(os.path.join(CLEAN, "crambin_meta.json"), "w"), indent=1)

    json.dump({"<structure>.pdb / .cif": "one real protein structure (PDB or mmCIF) to QC before ddG",
               "structure_meta.json": "structure_id, chain, resolution, method, and the intended point-mutation "
                                      "site + claimed wild-type residue for the downstream ddG task",
               "note": "the structure file is the object of QC; parse it with Biopython (Bio.PDB PDBParser / "
                       "MMCIFParser). Standard-residue heavy atoms present + single conformer + single model = "
                       "analysis-ready (adding hydrogens before energy work is routine prep, not a defect)."},
              open(os.path.join(HERE, "data", "data_dictionary.json"), "w"), indent=1)

    nHg = sum(1 for l in gb1_clean if P.element(l) == "H")
    nHc = sum(1 for l in cr_clean if P.element(l) == "H")
    print(f"[substrate] CLEAN=GB1 -> {CLEAN}/gb1.pdb  ({len(gb1_clean)} atoms, {nHg} H, "
          f"{len(set(P.reskey(l) for l in gb1_clean))} residues)")
    print(f"[substrate] AUX=crambin -> {CLEAN}/crambin.pdb  ({len(cr_clean)} atoms, {nHc} H, "
          f"{len(set(P.reskey(l) for l in cr_clean))} residues)")
    return CLEAN


if __name__ == "__main__":
    build()
