"""enhancer_activity L1 substrate builder — carve the REAL clean cross-species enhancer-activity table from the
ORIGINAL Klein 2018 supplementary workbook and DELIVER it in the ORIGINAL .xlsx FORMAT (raw QC, like scrna L1 =
raw 10x .tar.gz / hist L1 = raw BigWigs; the agent must parse the raw Excel itself).

NON-NEGOTIABLE (ADD_A_TRACK.md §1): the clean substrate is REAL public data; L1 issues are injected as DELTAS on
it (never synthesize the clean control — a synthetic tell becomes a false "defect").

SOURCE (real, published):
  - ORIGINAL: cross_species_task/data_not_ready/klein_2018_supp_file_2.xlsx
    Klein JC, Keith A, Rogers TJ, et al. "Functional characterization of enhancer evolution in the primate
    lineage." Genome Biology 2018;19:99. PMID 30045748.
    CITATION CORRECTED 2026-08-29 (verified against PubMed). This file previously read
    "Klein JD et al. 2018 (Science 357:eaan6203)" — wrong author initial, wrong journal, and an article id
    that returns no PubMed record. See the note at the metadata write below before rebuilding.
    Supplementary File 2, a 9-sheet workbook. Sheet "S4 All ortholog scores" = the enhancer-activity table:
      row 0 = title  "Table S4. Ortholog Scores"
      row 1 = header ["Enhancer Coordinates (hg19)", "Enrichment Score"]
      rows 2+ = data: col0 = a COORDINATE STRING  "<chrom>:<start>-<end>_<assembly>"  (chrom/start/end/assembly all
                embedded in ONE string; assembly suffix = the ortholog's species genome, e.g. hg38 / panTro5 /
                gorGor3 / ponAbe2 / macFas5 / rheMac3 / papAnu2 / chlSab2 / calJac3 / nomLeu3 / saiBol1, or an
                ancestral node N2..N10), col1 = STARR-seq enrichment score (log2; >0 = active enhancer).
      -> NO separate chrom/start/end/assembly columns, NO sequence column: raw format.  Requires openpyxl.
  - SEQUENCES (real, fetched at prep time from the UCSC DAS/REST API per assembly — see
    cross_species_task/prep/fetch_VISTA_sequences.py, same UCSC getData/sequence logic): cached in
    cross_species_task/klein_2018_s4_with_sequences.csv  (coordinate -> sequence + sequence_fetch_error + seq_len).
    We REUSE this cache (join on the raw coordinate string) so the build needs NO network. Rows the prep could not
    fetch carry sequence_fetch_error='fetch_failed' (real QC realism, reused in the fetch-failure world).

DELIBERATELY NOT USED as the substrate: klein_2018_s4_with_sequences.csv itself — it is a heavily pre-processed
DERIVATIVE (coordinate already parsed into chrom/start/end/assembly columns, renamed headers). L1 is RAW-data QC,
so the substrate must be the most-original format (the .xlsx). The CSV is used ONLY as the cached sequence lookup.

Clean substrate written to data/clean/  (S4 .xlsx format preserved: title row + header row + coordinate-STRING,
with the fetched `sequence` appended as a third column — the agent must still parse the raw Excel):
  enhancer_clean.xlsx    the clean cross-species enhancer table (well-formed real rows only)
  enhancer_abstain.xlsx  a DISTINCT real slice: genuinely repeat-rich / low-complexity but GENUINE (active,
                         positive-enrichment) enhancers — the abstain control (BOTH clean-family worlds are real
                         data with NO synthetic tell).
Resources written to data/resources/ (mounted read-only; see spec.py):
  hg38_reference_loci.tsv    coordinate -> forward-strand sequence for the human (hg38) enhancer loci (= the real
                             fetched hg38 sequences). The orientation reference for the strand/reverse-complement world.
  hg19ToHg38.over.chain.gz   liftOver chain (copied for provenance / L2 cross-species alignment instrument).
  gpn_msa_variant_scores.jsonl  GPN-MSA precomputed conservation/variant scores (L2 feature; provenance).
  vista_nt_logreg_oracle.joblib NT-logreg activity oracle (L2 instrument; provenance).
  vista_clean_with_labels.csv   VISTA enhancer labels (L2 truth; provenance).
Also writes data/data_dictionary.json + data/study_metadata.json (generic; identical across worlds — no leak).

usage: build_substrate.py        (offline: reuses the cached fetch; requires openpyxl + pandas)
"""
import os, re, json, shutil
import numpy as np
import pandas as pd
from collections import Counter
from openpyxl import Workbook

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RAW = os.path.join(DATA, "raw"); RES = os.path.join(DATA, "resources"); CLEAN = os.path.join(DATA, "clean")

# real source files (repo siblings) — recorded here as exact provenance
SIB = "/workspace"
SRC_XLSX = f"{SIB}/cross_species_task/data_not_ready/klein_2018_supp_file_2.xlsx"
SRC_SEQ_CACHE = f"{SIB}/cross_species_task/klein_2018_s4_with_sequences.csv"      # cached UCSC fetch (reused, not re-downloaded)
SRC_CHAIN = f"{SIB}/cross_species_task_refine/data/raw/chains/hg19ToHg38.over.chain.gz"
SRC_GPN = f"{SIB}/cross_species_task_refine/data/processed/gpn_variant_scores.jsonl"
SRC_ORACLE = f"{SIB}/cross_species_task/vista_nt_logreg_oracle.joblib"
SRC_VISTA = f"{SIB}/cross_species_task/vista_clean_with_labels.csv"

SHEET = "S4 All ortholog scores"
TITLE = "Table S4. Ortholog Scores"
HEADER = ["Enhancer Coordinates (hg19)", "Enrichment Score", "sequence"]     # + fetched sequence column
CANON_ASM = {"hg38", "panTro5", "gorGor3", "ponAbe2", "macFas5", "rheMac3",
             "papAnu2", "chlSab2", "calJac3", "nomLeu3", "saiBol1"}          # the 11 real ortholog genome assemblies
CANON_CHR = {str(i) for i in range(1, 23)} | {"X", "Y"}


def parse_coord(c):
    """'<chrom>:<start>-<end>_<assembly>' -> (chrom, start, end, assembly) or None."""
    m = re.match(r"^([^:]+):(\d+)-(\d+)_(.+)$", str(c))
    return (m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)) if m else None


def write_s4_xlsx(df, path):
    """Write [coordinate, enrichment, sequence] in the ORIGINAL S4 raw layout: row0 title, row1 header, rows2+ data."""
    wb = Workbook(); ws = wb.active; ws.title = SHEET
    ws.append([TITLE, None, None])
    ws.append(HEADER)
    for _, r in df.iterrows():
        seq = r["sequence"]
        ws.append([r["coordinate"], float(r["enrichment"]), (None if pd.isna(seq) else str(seq))])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wb.save(path)


def lowcomp(seq):
    """(longest homopolymer run, top-dinucleotide fraction) — a simple low-complexity / repeat-richness signature."""
    s = str(seq)
    hp = max((len(m.group(0)) for m in re.finditer(r"(.)\1*", s)), default=0)
    di = [s[i:i + 2] for i in range(len(s) - 1)]
    top = (max(Counter(di).values()) / len(di)) if di else 0.0
    return hp, top


def build():
    os.makedirs(RAW, exist_ok=True); os.makedirs(RES, exist_ok=True); os.makedirs(CLEAN, exist_ok=True)

    # 0) copy the REAL raw source + the cached fetch into the track (provenance; the substrate is derived from these)
    shutil.copy2(SRC_XLSX, os.path.join(RAW, os.path.basename(SRC_XLSX)))
    shutil.copy2(SRC_SEQ_CACHE, os.path.join(RAW, os.path.basename(SRC_SEQ_CACHE)))

    # 1) read the ORIGINAL S4 sheet raw (title row 0, header row 1, data rows 2+)
    raw = pd.read_excel(os.path.join(RAW, os.path.basename(SRC_XLSX)), sheet_name=SHEET, header=None)
    data = raw.iloc[2:].copy(); data.columns = ["coordinate", "enrichment"] + list(raw.columns[2:])
    data = data[["coordinate", "enrichment"]].dropna(subset=["coordinate"])

    # 2) attach the real fetched sequences (cached; no network) by the raw coordinate string
    cache = pd.read_csv(os.path.join(RAW, os.path.basename(SRC_SEQ_CACHE)))
    seqmap = dict(zip(cache["coordinate"], cache["sequence"]))
    errmap = dict(zip(cache["coordinate"], cache["sequence_fetch_error"]))
    p = data["coordinate"].map(parse_coord)
    data = data[p.notna()].copy(); p = p[p.notna()]
    data["chrom"] = [x[0] for x in p]; data["start"] = [x[1] for x in p]
    data["end"] = [x[2] for x in p]; data["assembly"] = [x[3] for x in p]
    data["base"] = data["chrom"] + ":" + data["start"].astype(str) + "-" + data["end"].astype(str)
    data["sequence"] = data["coordinate"].map(seqmap)
    data["fetch_error"] = data["coordinate"].map(errmap)
    data["enrichment"] = pd.to_numeric(data["enrichment"], errors="coerce")

    # 3) CLEAN filter: real, well-formed rows only (drop/repair the CSV's own faults so the control is GENUINELY clean)
    seq = data["sequence"].astype(str)
    wf = data[
        data["sequence"].notna() & seq.str.match(r"^[ACGT]+$")                 # sequence fetched, pure ACGT (no N-runs)
        & ((data["end"] - data["start"]) == seq.str.len())                    # coord span == sequence length
        & data["assembly"].isin(CANON_ASM) & data["chrom"].isin(CANON_CHR)    # a real genome assembly + a canonical chrom
        & (data["start"] < data["end"]) & data["enrichment"].notna()          # well-ordered interval + a real activity value
    ].copy()
    wf = wf.drop_duplicates("sequence").drop_duplicates("coordinate")         # no duplicate sequences/coords in the control

    # 4) reserve genuinely repeat-rich BUT genuine (active) enhancers for the abstain control; the rest = clean base
    hp, di = zip(*wf["sequence"].map(lowcomp))
    wf["hp"] = hp; wf["di"] = di
    is_rich = (wf["hp"] >= 12) & (wf["enrichment"] > 0)                       # real low-complexity + real positive activity
    abstain_rich = wf[is_rich].copy()
    base = wf[~is_rich].copy()
    # abstain slice = the real repeat-rich enhancers + a few normal rows for context (all real, all well-formed)
    normal_ctx = base.sample(n=min(20, len(base)), random_state=7)
    abstain = pd.concat([abstain_rich, normal_ctx]).drop_duplicates("coordinate").sort_values("coordinate")

    cols = ["coordinate", "enrichment", "sequence"]
    write_s4_xlsx(base[cols], os.path.join(CLEAN, "enhancer_clean.xlsx"))
    write_s4_xlsx(abstain[cols], os.path.join(CLEAN, "enhancer_abstain.xlsx"))
    print(f"[substrate] clean base: {len(base)} enhancers x {base['assembly'].nunique()} assemblies "
          f"({base['assembly'].value_counts().to_dict()})")
    print(f"[substrate] abstain slice: {len(abstain)} enhancers ({len(abstain_rich)} genuinely repeat-rich, "
          f"hp>=12 & enrichment>0; {len(normal_ctx)} normal-context)")

    # 5) resources ------------------------------------------------------------------------------------------------
    # hg38 forward-strand reference for the human enhancer loci (= the real fetched hg38 sequences) — the orientation
    # reference the strand/reverse-complement world is checked against. Covers ALL well-formed hg38 rows.
    hg38 = wf[wf["assembly"] == "hg38"][["coordinate", "sequence"]]
    hg38.to_csv(os.path.join(RES, "hg38_reference_loci.tsv"), sep="\t", index=False)
    for src in (SRC_CHAIN, SRC_GPN, SRC_ORACLE, SRC_VISTA):                   # copy L2 instruments (provenance)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(RES, os.path.basename(src)))
    # normalize copied gpn name for the spec
    if os.path.exists(os.path.join(RES, os.path.basename(SRC_GPN))):
        os.replace(os.path.join(RES, os.path.basename(SRC_GPN)), os.path.join(RES, "gpn_msa_variant_scores.jsonl"))
    print(f"[substrate] resources -> {RES}: hg38_reference_loci.tsv ({len(hg38)} loci) + chain/gpn/oracle/vista")

    # 6) generic docs (identical across all worlds -> no leak) -----------------------------------------------------
    json.dump({
        "sheet": f"'{SHEET}' of an .xlsx workbook. ROW 0 is a title ('{TITLE}'); ROW 1 is the real header; data start at ROW 2.",
        "Enhancer Coordinates (hg19)": ("one coordinate STRING per enhancer, formatted '<chrom>:<start>-<end>_<assembly>' "
            "(0-based, half-open; <assembly> is the ortholog's genome, e.g. hg38, panTro5, gorGor3, ..., or an ancestral "
            "node). Parse chrom/start/end/assembly out of this string yourself."),
        "Enrichment Score": "STARR-seq enhancer-activity enrichment (log2). > 0 indicates enhancer activity in that species.",
        "sequence": "the genomic DNA sequence fetched for the coordinate on the + (forward) strand of the named assembly.",
        "_note": ("raw enhancer-activity table (one row per species ortholog of an enhancer). Multiple rows may share the "
                  "same <chrom>:<start>-<end> (the human anchor) with different assembly suffixes = orthologs of one enhancer."),
    }, open(os.path.join(DATA, "data_dictionary.json"), "w"), indent=1)

    json.dump({
        "assay": "cross-species massively-parallel reporter (STARR-seq) enhancer-activity screen",
        "species": "10 primates + human (hg38, panTro5, gorGor3, ponAbe2, macFas5, rheMac3, papAnu2, chlSab2, calJac3, nomLeu3, saiBol1)",
        "human_frame": "hg19 (per the S4 header); ortholog coordinates carry a per-species assembly suffix",
        "measure": "log2 enrichment (enhancer activity)", "format": "original Klein-2018 Supplementary File 2, sheet S4",
        # ⚠ REBUILD NOTE: the SHIPPED data/study_metadata.json still carries the OLD, INCORRECT string
        # ("Klein JD et al. 2018, Science 357:eaan6203"). That file is what the L1 agents actually read —
        # it is quoted verbatim inside their sealed traces — so it is deliberately NOT rewritten. A rebuild
        # from this script will therefore differ from the shipped substrate in this one string. That is
        # intended: the record of what was served stays as served, and future builds get the right citation.
        "source": "Klein JC et al. 2018, Genome Biology 19:99 (Supp. File 2), PMID 30045748; sequences fetched from UCSC (getData/sequence).",
    }, open(os.path.join(DATA, "study_metadata.json"), "w"), indent=1)
    print(f"[substrate] dictionary + metadata written to {DATA}")


if __name__ == "__main__":
    build()
