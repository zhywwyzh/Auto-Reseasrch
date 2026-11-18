"""crispr_screen L1 substrate builder — carve the REAL clean pooled-CRISPR-KO essentiality screen.

NON-NEGOTIABLE (ADD_A_TRACK.md §1): the clean substrate is REAL public data; L1 issues are injected as DELTAS
on it (never synthesize the clean control — a synthetic tell becomes a false "defect").

SOURCE (real, public, Hart lab / BAGEL2): a genome-scale pooled CRISPR-KO fitness screen of HAP1 cells with the
TKOv3 library (Hart et al. 2017 G3; BAGEL2, Kim & Hart 2021 Genome Medicine). The raw guide-level read-count
matrix + gold essential/nonessential reference sets are distributed in the hart-lab/bagel GitHub repo:
  - readcounts:  pipeline-script-example/HAP1-TKOv3-EXAMPLE.txt   (70,877 guides x [GENE_CLONE, GENE, T0_-,
                 T3_A/B/C, T18_A/B/C, T18_A/B/C_Starved] — plasmid T0 + endpoint replicates at 3 & 18 doublings)
  - CEGv2.txt:   684 CORE-ESSENTIAL genes (Hart 2017)         — essentiality ground truth
  - NEGv1.txt:   927 NON-ESSENTIAL genes (Hart 2014)          — non-essential ground truth
  - TKOv3_align_summary_REAGENT_ID.txt: per-guide genomic alignment map (primary target + multi-targeting /
                 off-target genes) — the library re-mapping reference (used by the guide->gene mis-annotation
                 and promiscuous-guide worlds).  build_substrate.py just DOWNLOADS these into data/ (idempotent).

Clean slices written to data/clean/  (real HAP1 TKOv3, T0 plasmid + 3 endpoint replicates):
  counts_clean.tsv.gz        columns: sgRNA gene T0 rep1 rep2 rep3   (endpoints = T18_A/B/C)
  counts_strong_real.tsv.gz  same columns but endpoints = T18_*_Starved (a DISTINCT real condition with a strong,
                             replicate-consistent essentiality signal — the substrate for the abstain control).
Also writes data/data_dictionary.json and data/study_metadata.json (generic; identical across worlds — no leak).

usage: build_substrate.py            (requires network the FIRST time to fetch the raw files; then offline)
"""
import os, sys, json, gzip, urllib.request
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RAW = os.path.join(DATA, "raw"); RES = os.path.join(DATA, "resources"); CLEAN = os.path.join(DATA, "clean")

GH = "https://raw.githubusercontent.com/hart-lab/bagel/master"
SOURCES = {  # (dest_dir, url) — all REAL public files from hart-lab/bagel
    os.path.join(RAW, "HAP1-TKOv3-EXAMPLE.txt"): f"{GH}/pipeline-script-example/HAP1-TKOv3-EXAMPLE.txt",
    os.path.join(RAW, "HAP1-TKOv3-EXAMPLE-SCREENINFO.txt"): f"{GH}/pipeline-script-example/HAP1-TKOv3-EXAMPLE-SCREENINFO.txt",
    os.path.join(RES, "CEGv2.txt"): f"{GH}/CEGv2.txt",
    os.path.join(RES, "NEGv1.txt"): f"{GH}/NEGv1.txt",
    os.path.join(RES, "TKOv3_align_summary_REAGENT_ID.txt"): f"{GH}/data/libraries_for_multi_targeting_correction/TKOv3_align_summary_REAGENT_ID.txt",
}


def _fetch(dest, url):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"[substrate] downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def build():
    for dest, url in SOURCES.items():
        _fetch(dest, url)
    os.makedirs(CLEAN, exist_ok=True)
    raw = pd.read_csv(os.path.join(RAW, "HAP1-TKOv3-EXAMPLE.txt"), sep="\t")

    def slice_out(endpoints, name):
        out = raw[["GENE_CLONE", "GENE"] + ["T0_-"] + endpoints].copy()
        out.columns = ["sgRNA", "gene", "T0", "rep1", "rep2", "rep3"]
        p = os.path.join(CLEAN, name)
        out.to_csv(p, sep="\t", index=False, compression="gzip")
        print(f"[substrate] wrote {name}: {out.shape[0]} guides x {out.shape[1]} cols "
              f"(T0 mean {out['T0'].mean():.0f} rds/guide; endpoints {endpoints})")
        return out

    slice_out(["T18_A", "T18_B", "T18_C"], "counts_clean.tsv.gz")                     # main clean substrate
    slice_out(["T18_A_Starved", "T18_B_Starved", "T18_C_Starved"], "counts_strong_real.tsv.gz")  # abstain substrate

    json.dump({
        "sgRNA": "guide identifier, formatted <GENE>_<20bp protospacer sequence> (the library reagent id)",
        "gene": "gene the guide is annotated to target (library annotation)",
        "T0": "plasmid / initial library read count (reference timepoint, before selection)",
        "rep1": "endpoint read count, replicate 1 (after ~18 population doublings)",
        "rep2": "endpoint read count, replicate 2",
        "rep3": "endpoint read count, replicate 3",
        "_note": "raw integer read counts (one row per guide). Depletion of a guide from T0 to endpoint indicates "
                 "its target gene is required for fitness. Non-targeting/safe-harbor control guides target EGFP, "
                 "LacZ and luciferase (not in the genome).",
    }, open(os.path.join(DATA, "data_dictionary.json"), "w"), indent=1)

    json.dump({
        "assay": "pooled CRISPR-Cas9 knockout fitness (essentiality) screen",
        "cell_line": "HAP1", "library": "TKOv3 (Toronto KnockOut v3)", "cas": "Cas9",
        "design": "plasmid/T0 + 3 endpoint replicates (~18 doublings)", "genome_build": "hg38",
        "n_guides": int(raw.shape[0]), "guides_per_gene": "~4",
        "reference_sets": {"core_essential": "CEGv2.txt (684 genes, Hart 2017)",
                            "non_essential": "NEGv1.txt (927 genes, Hart 2014)",
                            "library_alignment": "TKOv3_align_summary_REAGENT_ID.txt (per-guide genomic alignments)"},
        "source": "hart-lab/bagel (GitHub); Hart et al. 2017 G3 7:2719; BAGEL2 Kim & Hart 2021 Genome Med 13:2",
    }, open(os.path.join(DATA, "study_metadata.json"), "w"), indent=1)
    print(f"[substrate] resources ready in {RES}; dictionary + metadata written to {DATA}")


if __name__ == "__main__":
    build()
