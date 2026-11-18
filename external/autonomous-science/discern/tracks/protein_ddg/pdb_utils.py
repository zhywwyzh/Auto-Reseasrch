"""Column-exact PDB ATOM/HETATM record helpers (protein_ddg track).

We manipulate structures by editing the fixed-column PDB records as raw 80-char strings and only splicing the
specific columns a defect touches (altloc / occupancy / coords / resname / resSeq / element). Keeping the original
name+element spacing untouched avoids any reformatting tell in the CLEAN control (Biopython's writer re-justifies
atom names, which is a synthetic fingerprint). Verification always re-parses the RESULT with Biopython independently.
PDB spec columns (1-based): record 1-6 · serial 7-11 · name 13-16 · altLoc 17 · resName 18-20 · chain 22 ·
resSeq 23-26 · iCode 27 · x 31-38 · y 39-46 · z 47-54 · occ 55-60 · bfac 61-66 · element 77-78 · charge 79-80.
"""

def is_atom(l):      return l.startswith(("ATOM  ", "HETATM"))
def name(l):         return l[12:16].strip()
def altloc(l):       return l[16]
def resname(l):      return l[17:20].strip()
def chain(l):        return l[21]
def resseq(l):       return int(l[22:26])
def icode(l):        return l[26]
def element(l):      return l[76:78].strip()
def occ(l):
    try: return float(l[54:60])
    except ValueError: return 1.0
def bfac(l):
    try: return float(l[60:66])
    except ValueError: return 0.0
def xyz(l):          return (float(l[30:38]), float(l[38:46]), float(l[46:54]))
def reskey(l):       return (l[21], l[22:26], l[26])            # chain, resSeq(raw), iCode

def _splice(l, s, e, val):
    if len(l) < e: l = l + " " * (e - len(l))
    assert len(val) == e - s, f"width {len(val)} != {e-s}"
    return l[:s] + val + l[e:]

def set_altloc(l, ch):     return _splice(l, 16, 17, ch)
def set_occ(l, o):         return _splice(l, 54, 60, f"{o:6.2f}")
def set_resname(l, rn):    return _splice(l, 17, 20, f"{rn:>3}")
def set_resseq(l, n):      return _splice(l, 22, 26, f"{n:>4}")
def set_record(l, rec):    return _splice(l, 0, 6, f"{rec:<6}")
def set_element(l, el):    return _splice(l, 76, 78, f"{el:>2}")
def set_atomname(l, nm):   return _splice(l, 12, 16, f"{nm:>4}" if len(nm) < 4 else nm[:4])
def set_coords(l, x, y, z):return _splice(l, 30, 54, f"{x:8.3f}{y:8.3f}{z:8.3f}")
def set_serial(l, s):      return _splice(l, 6, 11, f"{s:>5}")
def set_chain(l, c):       return _splice(l, 21, 22, c)
def set_bfac(l, b):        return _splice(l, 60, 66, f"{b:6.2f}")

def make(record, serial, atomname, resname, chain, resseq, x, y, z, element, occ=1.0, bfac=0.0, altloc=" "):
    """Build one column-exact ATOM/HETATM record from scratch (for injected waters/ions)."""
    l = " " * 80
    l = set_record(l, record); l = set_serial(l, serial); l = set_atomname(l, atomname)
    l = set_altloc(l, altloc); l = set_resname(l, resname); l = set_chain(l, chain)
    l = set_resseq(l, resseq); l = set_coords(l, x, y, z); l = set_occ(l, occ)
    l = set_bfac(l, bfac); l = set_element(l, element)
    return l

def renumber(lines):
    out, s = [], 0
    for l in lines:
        if is_atom(l): s += 1; l = set_serial(l, s if s < 100000 else 99999)
        out.append(l)
    return out

def read_atoms(path, records=("ATOM  ",)):
    return [l.rstrip("\n") for l in open(path) if l.startswith(records)]

def cryst1(path):
    for l in open(path):
        if l.startswith("CRYST1"): return l.rstrip("\n")
    return "CRYST1    1.000    1.000    1.000  90.00  90.00  90.00 P 1           1"

def write_pdb(path, atom_lines, cryst=None, models=None):
    """models: optional list-of-(modelnum, atom_lines) to emit a multi-MODEL file; else a single block."""
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        if cryst: f.write(cryst + "\n")
        if models is not None:
            for num, mlines in models:
                f.write(f"MODEL     {num:>4}\n")
                for l in renumber(mlines): f.write(l + "\n")
                f.write("ENDMDL\n")
        else:
            for l in renumber(atom_lines): f.write(l + "\n")
        f.write("END\n")

STD_AA = {"ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE","LEU","LYS",
          "MET","PHE","PRO","SER","THR","TRP","TYR","VAL"}
