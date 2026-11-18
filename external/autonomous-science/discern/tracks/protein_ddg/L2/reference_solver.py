#!/usr/bin/env python3
"""REFERENCE SOLVER for protein_ddg L2 — the single source of truth for the golden + the solver-first fire-checks.

Regenerates  L2/golden/{gb1_ddg_golden.csv, rubric_reference.json}  from first principles:
  Tsuboyama/Rocklin 2023 GB1 (1PGA) MEASURED ΔΔG  ->  aligned to the L1 substrate 2QMT  +  ESM2-650M reference LLR,
and then ASSERTS every world's trap actually fires. Exits NON-ZERO if any fire-check fails, so a future edit that
silently breaks a trap (or the golden) is caught in CI. Run with the bench venv (torch + esm + Biopython).

  python reference_solver.py            # rebuild golden/ (re-runs ESM) + run all fire-checks
  python reference_solver.py --check    # fire-checks only against the EXISTING golden (no ESM)

Sign convention (Tsuboyama): ddg_measured > 0 = MORE stable; destabilizing = negative. ESM LLR higher = more stable
-> they correlate POSITIVELY (a NEGATIVE correlation means a flipped/inverted read -> the ① sign trap).
"""
import os, sys, json, io, zipfile, urllib.request
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from Bio.PDB import PDBParser, PPBuilder, Selection
from Bio.PDB.SASA import ShrakeRupley

HERE = os.path.dirname(os.path.abspath(__file__)); GOLDDIR = f"{HERE}/golden"
os.makedirs(GOLDDIR, exist_ok=True)   # the solver must be able to rebuild from nothing (2026-08-16:
                                      # golden/ was lost and the rebuild failed only because it assumed the dir)
STRUCT = f"{os.path.dirname(HERE)}/data/clean/gb1.pdb"
RAW_CACHE = f"{GOLDDIR}/tsub_1pga_ddg.csv"                     # tiny cached Tsuboyama 1PGA per-site ΔΔG matrix
GOLDEN = f"{GOLDDIR}/gb1_ddg_golden.csv"; RUBREF = f"{GOLDDIR}/rubric_reference.json"
ZENODO = "https://zenodo.org/records/7992926/files/Data_tables_for_figs.zip?download=1"
ESM_MODEL = "esm2_t33_650M_UR50D"
MAXASA = {'A':129,'R':274,'N':195,'D':193,'C':167,'E':223,'Q':225,'G':104,'H':224,'I':197,'L':201,'K':236,'M':224,'F':240,'P':159,'S':155,'T':172,'W':285,'Y':263,'V':174}
KD = {'A':1.8,'R':-4.5,'N':-3.5,'D':-3.5,'C':2.5,'E':-3.5,'Q':-3.5,'G':-0.4,'H':-3.2,'I':4.5,'L':3.8,'K':-3.9,'M':1.9,'F':2.8,'P':-1.6,'S':-0.8,'T':-0.7,'W':-0.9,'Y':-1.3,'V':4.2}
T21 = {'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLU':'E','GLN':'Q','GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F','PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V'}

def gb1_2qmt_seq():
    s = PDBParser(QUIET=True).get_structure("gb1", STRUCT)
    return "".join(str(pp.get_sequence()) for pp in PPBuilder().build_peptides(s[0]["A"]))

def load_tsuboyama_1pga():
    """Cached 1PGA per-site ΔΔG matrix; download + extract from Zenodo if the cache is absent."""
    if os.path.exists(RAW_CACHE):
        return pd.read_csv(RAW_CACHE)
    print("[solver] cache miss -> downloading Tsuboyama figs tables (~24 MB) from Zenodo ...", flush=True)
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(ZENODO, timeout=300).read()))
    with z.open("Data_tables_for_figs/dG_site_feature_Fig3.csv") as fh:
        df = pd.read_csv(fh)
    df.columns = [c.strip() for c in df.columns]
    ddg = [c for c in df.columns if c.startswith("ddg_")]
    g = df[df["pdb_name"].astype(str).str.startswith("1PGA")].drop_duplicates("pos").sort_values("pos")[["pos", "wt_aa"] + ddg]
    g.to_csv(RAW_CACHE, index=False); print(f"[solver] cached 1PGA ΔΔG -> {RAW_CACHE} ({len(g)} sites)")
    return g

def align_measured(tsub, qmt):
    """Align Tsuboyama 1PGA to the 2QMT domain and emit (pos[1-based on 2QMT], wt, mut, ddg_measured)."""
    tsub = tsub.sort_values("pos").reset_index(drop=True); tseq = "".join(tsub.wt_aa)
    off = max(range(0, max(1, len(tseq) - len(qmt) + 1)),
              key=lambda o: sum(qmt[i] == tseq[o + i] for i in range(min(len(qmt), len(tseq) - o))))
    ident = sum(qmt[i] == tseq[off + i] for i in range(min(len(qmt), len(tseq) - off)))
    assert ident >= len(qmt) - 3, f"1PGA<->2QMT alignment too poor ({ident}/{len(qmt)})"
    base = int(tsub.pos.iloc[0]); gpos = tsub.set_index("pos"); ddg = [c for c in tsub.columns if c.startswith("ddg_")]
    rows = []
    for i in range(len(qmt)):
        tp = base + off + i
        if tp in gpos.index:
            wt = qmt[i]
            for c in ddg:
                mt = c.split("_")[1]
                if mt != wt and pd.notna(gpos.loc[tp, c]):
                    rows.append((i + 1, wt, mt, float(gpos.loc[tp, c])))
    return pd.DataFrame(rows, columns=["pos", "wt", "mut", "ddg_measured"])

def esm_reference_llr(qmt, keys):
    import torch, esm; torch.set_num_threads(8)
    model, alph = getattr(esm.pretrained, ESM_MODEL)(); model.eval()
    _, _, toks = alph.get_batch_converter()([("gb1", qmt)])
    with torch.no_grad():
        lp = torch.log_softmax(model(toks)["logits"], dim=-1)[0]
    return {(p, w, m): float(lp[p, alph.get_idx(m)] - lp[p, alph.get_idx(w)]) for p, w, m in keys}

def burial_map():
    s = PDBParser(QUIET=True).get_structure("gb1", STRUCT); ShrakeRupley().compute(s, level="R")
    return {r.id[1]: 1 - min(1.0, r.sasa / MAXASA[T21[r.resname]])
            for r in Selection.unfold_entities(s[0]["A"], "R") if r.resname in T21}

def build_golden():
    qmt = gb1_2qmt_seq()
    gold = align_measured(load_tsuboyama_1pga(), qmt)
    llr = esm_reference_llr(qmt, list(zip(gold.pos, gold.wt, gold.mut)))
    gold["esm_clean_llr"] = [llr[(p, w, m)] for p, w, m in zip(gold.pos, gold.wt, gold.mut)]
    gold.to_csv(GOLDEN, index=False)
    print(f"[solver] wrote golden -> {GOLDEN}  ({len(gold)} mutations)")
    return gold

def fire_checks(gold):
    """Assert every world's trap fires. Returns list of (name, ok, detail)."""
    bmap = burial_map()
    g = gold.copy(); g["burial"] = g.pos.map(lambda p: bmap.get(p, 0.5))
    g["dHphob"] = [KD[w] - KD[m] for w, m in zip(g.wt, g.mut)]
    R = []
    # ① sign_convention: correct read correlates +; the flipped-label read inverts
    rho = spearmanr(g.ddg_measured, g.esm_clean_llr).correlation
    R.append(("① sign_convention", rho > 0.20 and spearmanr(g.ddg_measured, -g.esm_clean_llr).correlation < -0.10,
              f"correct ρ={rho:+.3f}, flipped ρ={-rho:+.3f} (need +>.20 / flip<-.10)"))
    # ② anti-symmetry / threshold: ESM calls ~everything destabilizing -> misses stabilizing, chance at threshold 0
    destab = g[g.ddg_measured < -0.5]; stab = g[g.ddg_measured > 0.5]
    a_d = (destab.esm_clean_llr < 0).mean(); a_s = (stab.esm_clean_llr > 0).mean()
    R.append(("② anti_symmetry", a_s < 0.15 and a_d > 0.85,
              f"sign-acc destab={a_d:.2f} stab={a_s:.2f} (need destab>.85 / stab<.15 = bias fires)"))
    # ③ omitted_burial: burial is the dominant determinant (|corr| beats hydrophobicity)
    cb = abs(np.corrcoef(g.ddg_measured, g.burial)[0, 1]); ch = abs(np.corrcoef(g.ddg_measured, g.dHphob)[0, 1])
    R.append(("③ omitted_burial", cb > ch and cb > 0.35,
              f"|corr| burial={cb:.3f} > hydrophobicity={ch:.3f} (burial must dominate)"))
    # ④ misjoined_burial: a MIS-JOINED (permuted) burial column collapses below hydrophobicity -> a naive agent that
    #    trusts the provided feature ranks the WRONG determinant; correct = recompute rSASA. (deterministic permutation)
    cbp = abs(np.corrcoef(g.ddg_measured, g.burial.values[np.random.default_rng(20240607).permutation(len(g))])[0, 1])
    R.append(("④ misjoined_burial", cbp < ch and ch > 0.20,
              f"|corr| mis-joined burial={cbp:.3f} < hydrophobicity={ch:.3f} (naive trusts it -> wrong feature)"))
    return R

def write_rubric_reference(gold):
    from sklearn.metrics import roc_auc_score
    sp = spearmanr(gold.ddg_measured, gold.esm_clean_llr).correlation
    pe = float(np.corrcoef(gold.ddg_measured, gold.esm_clean_llr)[0, 1])
    m = (gold.ddg_measured < -0.5) | (gold.ddg_measured > 0.5); sub = gold[m]
    auc = roc_auc_score((sub.ddg_measured > 0).astype(int), sub.esm_clean_llr)
    big = gold[gold.ddg_measured.abs() > 1.0]
    ref = dict(n_mutations=int(len(gold)), tool=f"{ESM_MODEL} wt-marginal LLR (higher=more stable, non-circular)",
               golden_source="Tsuboyama2023 1PGA aligned to 2QMT (Zenodo 7992926, figs table) — regenerated by reference_solver.py",
               sign_convention="ddg_measured>0 = MORE stable (destabilizing = negative)",
               clean_magnitude_pearson=round(pe, 3), clean_magnitude_spearman=round(float(sp), 3),
               clean_direction_AUROC=round(float(auc), 3),
               clean_sign_acc_large_effect=round(float(((big.esm_clean_llr > 0) == (big.ddg_measured > 0)).mean()), 3))
    json.dump(ref, open(RUBREF, "w"), indent=1); print(f"[solver] wrote rubric reference -> {RUBREF}")



def shipped_checks(gold):
    """ARTIFACT-mode fire checks (audit fix): verify the SHIPPED worlds fire, not just the mechanism —
    fire_checks() samples/permutes the full golden with its own seeds, which can drift from what the
    world builders actually froze. These checks read the run-dir manifests + world files directly."""
    import glob
    R = []
    gk = {f"{r.wt}{r.pos}{r.mut}".upper(): (r.ddg_measured, r.esm_clean_llr) for r in gold.itertuples()}
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

    def world_rho(muts):
        pairs = [gk[x.upper()] for x in muts if x.upper() in gk]
        if len(pairs) < 8:
            return None
        from scipy.stats import spearmanr
        return float(spearmanr([a for a, _ in pairs], [b for _, b in pairs]).correlation)

    mp = os.path.join(base, "ddg_predict_run", "manifest.json")
    if os.path.exists(mp):
        for m in json.load(open(mp)):
            rho = world_rho(m.get("mutations") or [])
            R.append((f"shipped ddg/{m['world_label']}", rho is not None and rho > 0.10,
                      f"per-world correct-tool rho={None if rho is None else round(rho,3)} (grader bar = 0.6x this)"))
    mp = os.path.join(base, "stab_classify_run", "manifest.json")
    if os.path.exists(mp):
        for m in json.load(open(mp)):
            muts = [x.upper() for x in (m.get("mutations") or []) if x.upper() in gk]
            frac_stab = (sum(1 for x in muts if gk[x][0] > 0) / len(muts)) if muts else None
            gt = m.get("ground_truth", {})
            if gt.get("anti_symmetry_exposed"):
                ok = frac_stab is not None and frac_stab >= 0.4     # stabilizing-heavy set: the wt-pref bias must bite
                R.append((f"shipped stab/{m['world_label']}", ok, f"frac_stabilizing={frac_stab:.2f} (bias-exposing)"))
            else:
                R.append((f"shipped stab/{m['world_label']}", frac_stab is not None,
                          f"frac_stabilizing={None if frac_stab is None else round(frac_stab,2)}"))
    mp = os.path.join(base, "feature_effect_run", "manifest.json")
    if os.path.exists(mp):
        for m in json.load(open(mp)):
            gt = m.get("ground_truth", {})
            cd = m.get("agent_input")
            pf = os.path.join(cd, "provided_features.csv") if cd else None
            md = os.path.join(cd, "mutations_ddg.csv") if cd else None
            if gt.get("misjoined_burial") and pf and os.path.exists(pf) and os.path.exists(md):
                f = pd.read_csv(pf); d = pd.read_csv(md)
                j = f.merge(d, on=[c for c in ("mutation",) if c in f.columns and c in d.columns])                     if "mutation" in f.columns else pd.concat([f, d], axis=1)
                bcol = next((c for c in j.columns if "buri" in c.lower() or "sasa" in c.lower()), None)
                hcol = next((c for c in j.columns if "hphob" in c.lower() or "hydroph" in c.lower()), None)
                dcol = next((c for c in j.columns if "ddg" in c.lower()), None)
                if bcol and hcol and dcol:
                    cb = abs(float(j[bcol].corr(j[dcol]))); ch = abs(float(j[hcol].corr(j[dcol])))
                    R.append(("shipped feat/misjoined_burial", cb < ch - 0.1,
                              f"|corr| shipped burial={cb:.3f} < dHphob={ch:.3f} (naive ranks the wrong feature)"))
    return R


def main():
    check_only = "--check" in sys.argv
    gold = pd.read_csv(GOLDEN) if check_only else build_golden()
    if not check_only:
        write_rubric_reference(gold)
    print("\n=== FIRE-CHECKS (solver-first; every trap must fire) ===")
    R = fire_checks(gold); allok = True
    for name, ok, detail in R:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:18s} {detail}")
        allok = allok and ok
    if not allok:
        print("\nFIRE-CHECK FAILED — a trap does not fire / the golden drifted. Fix before running models.")
        sys.exit(1)
    print("\n=== SHIPPED-WORLD CHECKS (artifact mode) ===")
    for name, ok, detail in shipped_checks(gold):
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:32s} {detail}")
        allok = allok and ok
    if not allok:
        print("\nSHIPPED-WORLD CHECK FAILED — the frozen worlds drifted from the verified mechanism.")
        sys.exit(1)
    print("\nALL FIRE-CHECKS PASS — golden is regenerable + every trap fires (mechanism AND shipped artifacts).")

if __name__ == "__main__":
    main()
