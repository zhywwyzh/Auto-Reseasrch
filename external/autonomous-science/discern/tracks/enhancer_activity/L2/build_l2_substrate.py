"""enhancer_activity L2 — substrate provenance. RUN ONCE before reference_solver.py.

The L2 substrate IS the L1-clean Klein cross-species table (data/raw/klein_2018_s4_with_sequences.csv), analysis-
ready as-is. This step only VALIDATES it loads and records provenance (incl. the feasibility-gate reframe rationale);
it writes NOTHING the agent sees and never modifies L1.

usage: python build_l2_substrate.py     (bench venv)
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import l2_common as C

C.PROC.mkdir(parents=True, exist_ok=True)


def main():
    df = C.load_klein()
    clean = C.turnover_set(df)
    prov = {
        "substrate": "Klein 2018 cross-species STARR-seq enhancer activity (L1 raw, reused read-only)",
        "table": str(C.RAW), "n_rows": int(len(df)), "n_families": int(df.family.nunique()),
        "n_species": int(df.species.nunique()), "enrichment_range": [float(df.enrichment_score.min()), float(df.enrichment_score.max())],
        "n_turnover_families": len(clean), "turnover_thr": C.TURNOVER_THR, "min_species": C.MIN_SPECIES,
        "focus": "minimal, DATA-CONFOUND-focused single sub-task (cross-species divergence)",
        "reframe": "feasibility gate: FIMO/HOMER/liftOver not installed, GPN-MSA variant->enhancer mapping missing, "
                   "and (fire-checked) seq->activity has no signal / per-species scales uniform / conservation~activity "
                   "null on this substrate -> the designed tool-traps do not fire. What fires = input-integrity "
                   "confounds that corrupt the divergence conclusion (species batch, out-of-range values, coverage). "
                   "ortholog_mispairing dropped (undetectable: real primate orthologs no more sequence-similar than "
                   "random). L1 never modified.",
        "golden": "produced by reference_solver.py -> gold/gold_solver.json + gold/golden_divergence.csv",
    }
    json.dump(prov, open(C.PROC / "l2_provenance.json", "w"), indent=1)
    print(f"[substrate] validated: {len(df)} rows x {df.family.nunique()} families x {df.species.nunique()} species; "
          f"{len(clean)} turnover families")
    print(f"[substrate] provenance -> {C.PROC / 'l2_provenance.json'}")


if __name__ == "__main__":
    main()
