#!/usr/bin/env python3
"""REFERENCE SOLVER for enhancer_activity L2 (3 analyses, cross-species DATA-CONFOUND focus).

Golden = the clean output of each analysis on the real Klein 11-species substrate. Every confound world must FIRE
(naive/trust-input answer wrong, robust/verify-input answer recovers). Writes gold/gold_solver.json + golden CSVs;
exits NON-ZERO on any failure. Run with the bench venv.
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import l2_common as C

HERE = Path(__file__).parent
GOLD = HERE / "gold"; GOLD.mkdir(exist_ok=True)
CHECKS = []
def check(name, ok, detail):
    CHECKS.append((name, bool(ok), detail)); print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
def jac(a, b): return len(a & b) / max(1, len(a | b))


def solve_divergence(df):
    clean = C.turnover_set(df)
    C.family_divergence(df).assign(is_turnover=lambda t: t.index.isin(clean)).reset_index().rename(
        columns={"index": "family"}).to_csv(GOLD / "golden_divergence.csv", index=False)
    check("divergence clean solvable", 20 <= len(clean) <= 120, f"{len(clean)} turnover families of {df.family.nunique()}")
    g = {"clean": {"n_turnover": len(clean), "turnover_families": sorted(clean), "thr": C.TURNOVER_THR, "min_species": C.MIN_SPECIES},
         "golden_csv": str(GOLD / "golden_divergence.csv"), "n_families": int(df.family.nunique())}

    d, i = C.inj_species_batch(df); naive = C.turnover_set(d); spur = naive - clean
    dz = d.copy(); dz["z"] = C.per_species_z(dz); z0 = df.copy(); z0["z"] = C.per_species_z(z0)
    zthr = float(np.quantile(z0.groupby("family").z.agg(lambda x: x.max()-x.min()).dropna(), 1-len(clean)/df.family.nunique()))
    gz = dz.groupby("family").agg(r=("z", lambda x: x.max()-x.min()), n=("z", "size"))
    rob = set(gz[(gz.r > zthr) & (gz.n >= C.MIN_SPECIES)].index) - clean
    check("species_batch fires", len(spur) >= 40 and len(rob) <= 0.15*len(spur),
          f"+{i['offset']} on {i['species']}: naive spurious={len(spur)} -> per-species-z {len(rob)}")
    g["species_batch_confound"] = {"species": i["species"], "offset": i["offset"], "naive_spurious": len(spur), "robust_spurious": len(rob), "z_thr": round(zthr, 3)}

    d, i = C.inj_enrichment_outlier(df); naive = C.turnover_set(d); fake = [f for f in i["families"] if f in naive]
    det = set(C.flag_implausible(d)); rob = C.turnover_set(d.drop(index=list(det))); still = [f for f in i["families"] if f in rob]
    check("enrichment_outlier fires", len(fake) >= 0.7*len(i["families"]) and len(still) <= 0.2*len(i["families"]),
          f"naive {len(fake)}/{len(i['families'])} fake -> flag {len(det)} implausible -> {len(still)} fake")
    g["enrichment_outlier"] = {"families": i["families"], "naive_fake": len(fake), "robust_fake": len(still), "n": len(i["families"])}

    d, i = C.inj_phylo_pseudoreplication(df); naive = C.turnover_set(d); fake = [f for f in i["families"] if f in naive]
    rob = C.clade_robust_turnover(d); still = [f for f in i["families"] if f in rob]
    check("phylo_pseudoreplication fires", len(fake) >= 0.6*len(i["families"]) and len(still) <= 0.35*len(i["families"]),
          f"single sister-pair jump: naive {len(fake)}/{len(i['families'])} fake -> clade-robust {len(still)} fake")
    g["phylo_pseudoreplication"] = {"families": i["families"], "naive_fake": len(fake), "robust_fake": len(still), "n": len(i["families"])}

    d, i = C.inj_species_duplicate(df); naive = C.turnover_set(d); fake = [f for f in i["families"] if f in naive]
    dd = d.drop_duplicates(["family", "species"]); rob = C.turnover_set(dd); still = [f for f in i["families"] if f in rob]
    dup_fams = C.one_per_species_ok(d)
    check("species_duplicate fires", len(fake) >= 0.6*len(i["families"]) and len(still) <= 0.2*len(i["families"]) and len(dup_fams) >= 0.8*len(i["families"]),
          f"dup-species: naive {len(fake)}/{len(i['families'])} fake -> one-per-species dedup {len(still)}; {len(dup_fams)} flagged dup")
    g["species_duplicate"] = {"families": i["families"], "naive_fake": len(fake), "robust_fake": len(still), "n": len(i["families"])}
    return g


def solve_conservation(df):
    cons = C.family_conservation(df)
    gold_set = C.conserved_set(C.gc_adjust_conservation(cons))          # GC-adjusted = the correct conserved set
    cons.assign(cons_gc_adj=C.gc_adjust_conservation(cons), is_conserved=lambda t: t.index.isin(gold_set)).reset_index().rename(
        columns={"index": "family"}).to_csv(GOLD / "golden_conservation.csv", index=False)
    check("conservation clean solvable", 40 <= len(gold_set) <= 120, f"{len(gold_set)} conserved families of {len(cons)}")
    g = {"clean": {"n_conserved": len(gold_set), "conserved_families": sorted(gold_set), "frac": 0.25},
         "golden_csv": str(GOLD / "golden_conservation.csv"), "n_families": int(len(cons))}

    from scipy.stats import spearmanr
    rho = spearmanr(cons.gc, cons.cons).correlation
    j = jac(C.conserved_set(cons.cons), gold_set)                       # raw %-identity vs GC-adjusted
    # premise-based handling world: GC measurably biases the conservation estimate -> the skill is ADJUSTING for GC
    check("gc_conservation_bias premise holds", abs(rho) >= 0.2,
          f"corr(GC,conservation)={rho:+.3f} (|.|>=.2 -> GC biases the %-identity estimate; raw-vs-adjusted set jaccard {j:.2f}); adjust for GC")
    g["gc_conservation_bias"] = {"gc_cons_corr": round(float(rho), 3), "raw_vs_adjusted_jaccard": round(j, 3), "note": "GC biases raw %-identity conservation; regress it out"}

    d, i = C.inj_alignment_quality(df); cons2 = C.family_conservation(d)
    naive2 = C.conserved_set(C.gc_adjust_conservation(cons2))
    dropped = [f for f in i["families"] if f in gold_set and f not in naive2]   # truncation kicked them out of conserved
    bad = C.bad_alignment_families(cons2)
    detected = [f for f in i["families"] if f in bad]
    check("alignment_quality fires", len(dropped) >= 0.5*len(i["families"]) and len(detected) >= 0.7*len(i["families"]),
          f"truncated orthologs drop {len(dropped)}/{len(i['families'])} out of the conserved set; length-het flags {len(detected)}")
    g["alignment_quality"] = {"families": i["families"], "naive_dropped": len(dropped), "flagged": len(detected), "n": len(i["families"])}

    # conservation_as_proxy: aggregate conservation~activity is null -> "conserved => active" is a false prior
    rho_ca = spearmanr(cons.cons, cons.act_range).correlation
    check("conservation_as_proxy premise holds", abs(rho_ca) < 0.15,
          f"corr(conservation, activity-divergence)={rho_ca:+.3f} ~ null -> conserved != active-here (L3 feeder)")
    g["conservation_as_proxy"] = {"cons_activity_corr": round(float(rho_ca), 3), "note": "data decouples conservation from activity; do not impose conserved=>active"}
    return g


def solve_ranking(df):
    gold_set = C.active_family_set(df)
    df.groupby("family").enrichment_score.max().rename("family_activity").reset_index().assign(
        is_active=lambda t: t.family.isin(gold_set)).to_csv(GOLD / "golden_ranking.csv", index=False)
    check("ranking clean solvable", 20 <= len(gold_set) <= 120, f"{len(gold_set)} active families of {df.family.nunique()}")
    g = {"clean": {"n_active": len(gold_set), "active_families": sorted(gold_set), "frac": 0.15},
         "golden_csv": str(GOLD / "golden_ranking.csv"), "n_families": int(df.family.nunique())}

    n = int(df.family.nunique() * 0.15)
    naive = C.naive_row_top_families(df, n)                              # per-row top-n -> families (double-counts)
    top_rows = df.nlargest(n, "enrichment_score")
    dup_frac = 1 - top_rows.family.nunique() / len(top_rows)
    check("ortholog_family_leakage fires", jac(naive, gold_set) <= 0.7 and dup_frac >= 0.3,
          f"per-row top-{n} spans {top_rows.family.nunique()} families ({dup_frac:.0%} ortholog dups); "
          f"jaccard(per-row-families, family-dedup)={jac(naive, gold_set):.2f}")
    g["ortholog_family_leakage"] = {"n_top": n, "row_top_dup_frac": round(float(dup_frac), 3), "jaccard": round(jac(naive, gold_set), 3)}

    d, i = C.inj_duplicate_rows(df); naive_frac = (d.enrichment_score > d.enrichment_score.quantile(0.9)).mean()
    dd = d.drop_duplicates(["coordinate", "enrichment_score"]); rob_set = C.active_family_set(dd)
    naive_set = C.naive_row_top_families(d, n)
    check("duplicate_contamination fires", len(d) - len(dd) >= 30 and jac(naive_set, gold_set) <= 0.75,
          f"{len(d)-len(dd)} exact-duplicate rows injected; dedup recovers the active-family set (jaccard {jac(rob_set, gold_set):.2f})")
    g["duplicate_contamination"] = {"n_dup": i["n_dup"], "recovered_jaccard": round(jac(rob_set, gold_set), 3)}

    # reference_species_bias: rank families by activity-relative-to-human vs absolute family activity
    piv = df.pivot_table("enrichment_score", "family", "species", aggfunc="mean")
    if C.REFERENCE_SPECIES in piv.columns:
        rel = (piv.sub(piv[C.REFERENCE_SPECIES], axis=0)).abs().max(axis=1)   # max deviation from human
        ref_top = set(rel.sort_values(ascending=False).head(int(df.family.nunique()*0.15)).index)
        j = jac(ref_top, gold_set)
        check("reference_species_bias fires", j <= 0.6,
              f"human-referenced activity ranking differs from absolute (jaccard {j:.2f}) -> human-outlier bias")
        g["reference_species_bias"] = {"jaccard_vs_absolute": round(j, 3)}
    return g


def main():
    df = C.load_klein()
    gold = {"divergence": solve_divergence(df), "conservation": solve_conservation(df), "ranking": solve_ranking(df)}
    n_fail = sum(1 for _, ok, _ in CHECKS if not ok)
    gold["_verification"] = [{"check": n, "pass": ok, "detail": d} for n, ok, d in CHECKS]
    json.dump(gold, open(GOLD / "gold_solver.json", "w"), indent=1, default=float)
    print(f"\n[gold] {len(CHECKS)-n_fail}/{len(CHECKS)} checks passed")
    if n_fail:
        print(f"[SOLVER] {n_fail} FAILURES — DO NOT freeze worlds."); sys.exit(1)
    print("[SOLVER] ALL CHECKS PASSED.")


if __name__ == "__main__":
    main()
