"""crispr_screen L2 — substrate provenance. RUN ONCE before reference_solver.py.

Unlike bulk_rnaseq (which filters/annotates genes into data/processed), the crispr L2 substrate IS the L1-clean
guide-count table itself (data/clean/counts_clean.tsv.gz) — analysis-ready as-is — plus the mounted CEGv2/NEGv1
gold lists + the TKOv3 alignment summary. So this step only VALIDATES the substrate loads and records provenance;
it writes NOTHING the agent sees and never modifies L1. The golden is produced by reference_solver.py.

usage: python build_l2_substrate.py     (bench venv)
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import l2_common as C

HERE = Path(__file__).parent
C.PROC.mkdir(parents=True, exist_ok=True)


def main():
    counts = C.load_counts()
    ceg, neg = C.load_gene_lists()
    prom = C.promiscuous_guides()
    assert set(["sgRNA", "gene", "T0", *C.REPS]).issubset(counts.columns), "unexpected counts schema"
    ng = counts.gene.nunique()
    prov = {
        "substrate": "HAP1 / TKOv3 pooled CRISPR-KO fitness screen (L1-clean counts, reused read-only)",
        "counts": str(C.CLEAN), "n_guides": int(len(counts)), "n_genes": int(ng),
        "reps": C.REPS, "reference_sets": {"CEGv2": str(C.CEG_F), "NEGv1": str(C.NEG_F), "alignment": str(C.ALIGN_F)},
        "n_ceg": len(ceg), "n_neg": len(neg), "n_promiscuous_guides": len(prom),
        "ceg_guides": int(counts.gene.isin(ceg).sum()), "neg_guides": int(counts.gene.isin(neg).sum()),
        "tool": "BAGEL-style Bayes Factor (numpy/scipy) — non-circular via external CEG/NEG gold lists; "
                "MAGeCK/Chronos/CRISPRcleanR not installed",
        "golden": "produced by reference_solver.py -> gold/gold_solver.json + gold/golden_{scores,essential,context}.csv",
        "note": "single-line reframe of the DepMap CN-artifact / cross-line-panel design (not constructible on a "
                "near-haploid single line with no CN profile); L1 is never modified.",
    }
    json.dump(prov, open(C.PROC / "l2_provenance.json", "w"), indent=1)
    print(f"[substrate] validated: {len(counts)} guides x {ng} genes; CEG={len(ceg)} NEG={len(neg)} "
          f"promiscuous={len(prom)}")
    print(f"[substrate] provenance -> {C.PROC / 'l2_provenance.json'}")


if __name__ == "__main__":
    main()
