"""enhancer_activity L1 world-builder — inject ONE known QC defect per world into the REAL clean cross-species
enhancer-activity table (raw S4 .xlsx) + write manifest ground truth.

ONE world per issue-type (n=1, like every track). Emits, per world, an enhancer table in the ORIGINAL S4 .xlsx
format (title row + header row + coordinate-STRING + sequence — the agent parses it), and appends a manifest cell
carrying the ground truth the SHARED grade_generic reads: issue_type / issue_present / canonical_checks /
diagnose_keywords / action_keywords / correct_action / affected_entities (+ requires_external_evidence for abstain).

Clean base = the REAL Klein STARR-seq table (build_substrate.py -> data/clean/enhancer_clean.xlsx); each defect is a
sharp DELTA on it, expressed on the coordinate STRING and/or the fetched sequence. The abstain control uses a DISTINCT
real slice (enhancer_abstain.xlsx — genuinely repeat-rich but real active enhancers) so BOTH clean-family worlds are
genuine data with NO synthetic tell.

Run build_substrate.py first, then:  world_builder.py
"""
import os, sys, re, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_substrate import parse_coord, write_s4_xlsx, SHEET, CANON_ASM, CANON_CHR, RAW  # reuse the raw-format writer + parser

DATA = os.path.join(HERE, "data"); CLEAN = os.path.join(DATA, "clean")
RUN_DIR = os.path.join(HERE, "L1/results/enhancer_l1_run")
CLEAN_XLSX = os.path.join(CLEAN, "enhancer_clean.xlsx")
ABSTAIN_XLSX = os.path.join(CLEAN, "enhancer_abstain.xlsx")
SEQ_CACHE = os.path.join(RAW, "klein_2018_s4_with_sequences.csv")            # for reusing the REAL fetch_failed rows
COMP = str.maketrans("ACGTacgtN", "TGCAtgcaN")
SCAFFOLDS = ["Un_KI270742v1", "17_KI270729v1_random", "14_GL000009v2_random",  # real UCSC unplaced/unlocalized scaffolds
             "Un_GL000195v1", "1_KI270711v1_random", "9_KI270720v1_random"]    # (bare-chrom form, matching the id format)


def revcomp(s):
    return str(s).translate(COMP)[::-1]

def mk(chrom, start, end, asm):
    return f"{chrom}:{start}-{end}_{asm}"

def load(path):
    df = pd.read_excel(path, sheet_name=SHEET, header=1)                      # header on row 1 (row 0 = title)
    df = df.rename(columns={df.columns[0]: "coordinate", df.columns[1]: "enrichment", df.columns[2]: "sequence"})
    return df[["coordinate", "enrichment", "sequence"]].reset_index(drop=True)


# ---------------- GROUND TRUTH per issue = the grading contract (what a competent QC must CHECK / DIAGNOSE / DO) ----
# canonical_checks = the QC computation that reveals it (matched against executed code); diagnose_keywords = naming
# the defect; action_keywords = the proportionate remedy. All keyword/regex-graded by grade_generic (0-3).
GT = {
 "clean": dict(present=False,
   canonical_checks=["sequence", "assembly", "start", "end", "duplicat", "len\\("],
   diagnose_keywords=[], action_keywords=[],
   correct_action="No defect — the enhancer table is well-formed; proceed to activity/conservation analysis, do not invent a problem.",
   affected=[]),
 "sequence_fetch_failure": dict(present=True,
   canonical_checks=["isna|isnull|missing|empty|notna", "sequence", "\\bN\\b|NNN|'N'|count.*N|run.*N|fraction.*N", "fetch"],
   diagnose_keywords=["fetch fail", "failed fetch", "missing sequence", "empty sequence", "null sequence",
                      "n-?run", "runs? of n", "stretch of n", "n content", "unfetched", "sequence not fetched",
                      "masked", "ambiguous base"],
   action_keywords=["re-?fetch", "refetch", "re-?download", "drop", "exclude", "remove", "impute", "flag",
                    "recover from reference", "fetch again"],
   correct_action="Some sequences are missing (failed fetch) or contain runs of N; re-fetch or drop those rows before analysis.",
   affected=[]),
 "assembly_build_mismatch": dict(present=True,
   canonical_checks=["assembly", "hg19", "build", "suffix|split|_.*assembl", "duplicat.*assembl|assembl.*duplicat|value_counts"],
   diagnose_keywords=["assembly mismatch", "wrong assembly", "build mismatch", "hg19", "foreign build", "wrong build",
                      "unexpected assembly", "duplicate assembly", "same assembly.*twice", "two hg38", "mislabel.*assembl",
                      "assembly.*not.*(one of|expected|valid)", "invalid assembly"],
   action_keywords=["correct the assembly", "re-?label", "fix the assembly", "drop", "exclude", "re-?lift",
                    "re-?map to hg38", "flag", "verify the assembly", "harmonize.*assembl"],
   correct_action="Some rows carry a wrong assembly suffix (a foreign build like hg19, and a species duplicated within one enhancer family); correct the assembly label / drop them before cross-species comparison.",
   affected=[]),
 "liftover_failure": dict(present=True,
   canonical_checks=["chrom", "scaffold|contig|random|_KI|_GL|chrUn|Un_|unplaced|canonical", "liftover|lift over|lift-?over|unmapp", "isin.*chr|not in"],
   diagnose_keywords=["liftover fail", "lift-?over fail", "unmapp", "cannot be lifted", "not liftable", "unplaced",
                      "scaffold", "contig", "non-?canonical chrom", "random chromosome", "unlocalized", "does not lift"],
   action_keywords=["drop", "exclude", "remove", "flag", "re-?lift", "cannot use", "exclude unmapp", "discard unliftable"],
   correct_action="Some cross-species coordinates sit on unplaced scaffolds / non-canonical chromosomes that cannot be lifted to a common frame; drop or re-lift them.",
   affected=[]),
 "coordinate_off_by_one": dict(present=True,
   canonical_checks=["start", "end", "start\\s*[<>]|>\\s*end|start.*end", "span|end\\s*-\\s*start|off.?by.?one", "len\\("],
   diagnose_keywords=["off-?by-?one", "off by one", "0-?based", "1-?based", "start\\s*>\\s*end", "start greater than end",
                      "reversed coordinate", "coordinate error", "span.*(one|1).*(short|off)", "half-?open", "inverted interval"],
   action_keywords=["fix the coordinate", "correct the coordinate", "re-?compute", "swap start", "adjust.*(start|end)",
                    "add 1|subtract 1|\\+1|-1", "drop", "exclude", "flag", "re-?parse"],
   correct_action="Some coordinates are off-by-one (0-vs-1-based: span disagrees with sequence length by 1) or have start>end; fix the coordinate arithmetic before use.",
   affected=[]),
 "strand_rc_inconsistency": dict(present=True,
   canonical_checks=["reverse|revcomp|complement|reverse.?complement", "reference|hg38_reference|forward|strand|orient", "sequence", "==|match|compare"],
   diagnose_keywords=["reverse complement", "reverse-?complement", "revcomp", "wrong strand", "strand inconsistency",
                      "opposite strand", "orientation", "sequence is the reverse", "minus strand", "flipped strand",
                      "reverse-?complemented"],
   action_keywords=["reverse-?complement", "revcomp", "re-?extract", "correct the strand", "flip", "re-?fetch",
                    "fix orientation", "flag", "drop", "re-?orient"],
   correct_action="Some hg38 sequences are stored reverse-complemented relative to the forward reference (wrong strand extracted); reverse-complement them back / re-extract on the + strand.",
   affected=[]),
 "duplicate_family_leakage": dict(present=True,
   canonical_checks=["duplicat|drop_duplicates|\\.duplicated", "coordinate|sequence", "value_counts|groupby|nunique", "identical|same sequence|leak"],
   diagnose_keywords=["duplicate coordinate", "duplicated coordinate", "duplicate row", "duplicate sequence",
                      "identical sequence", "family leakage", "cross-?species leakage", "leak", "paralog",
                      "same enhancer.*twice", "repeated coordinate", "orthologs? .*identical"],
   action_keywords=["de-?duplicate", "dedup", "drop_duplicates", "drop", "remove duplicate", "exclude",
                    "group.*split|split by (family|enhancer)", "collapse", "flag", "keep one"],
   correct_action="There are duplicate coordinates and identical ortholog sequences (cross-species family leakage that would contaminate a train/test split); de-duplicate and split by enhancer family.",
   affected=[]),
 "seqlen_span_mismatch": dict(present=True,
   canonical_checks=["len\\(|str\\.len|length", "span|end\\s*-\\s*start", "!=|mismatch|compare|diff", "sequence"],
   diagnose_keywords=["length mismatch", "seq.*len.*(mismatch|!=|differ|disagree)", "sequence length.*(span|coordinate)",
                      "span.*(mismatch|!=|differ)", "truncated sequence", "sequence.*(too short|too long)",
                      "len.*(!=|not equal).*(end|start|span)", "coordinate span.*sequence"],
   action_keywords=["re-?fetch", "refetch", "drop", "exclude", "remove", "re-?extract", "trim", "flag",
                    "fix.*(length|coordinate)", "re-?download"],
   correct_action="For some rows len(sequence) != coordinate span (end-start) — a truncated/extended fetch; re-fetch or drop those rows.",
   affected=[]),
 "abstain_repeat_rich": dict(present=False, requires_external_evidence=True,
   abstention_question=("A cross-species enhancer-activity table contains a subset of enhancers whose SEQUENCES are "
                        "genuinely REPEAT-RICH / LOW-COMPLEXITY (long homopolymer runs, dominant di/tri-nucleotide "
                        "repeats) yet carry a real, POSITIVE STARR-seq activity score. Is this low-complexity content a "
                        "DATA ARTIFACT (a bad fetch / mapping/masking artifact) that should be flagged and DISCARDED, or "
                        "is it a REAL, active enhancer sequence that should be RETAINED? The correct answer is that it is "
                        "REAL biology — enhancers can be repeat-rich / low-complexity — and the rows must NOT be discarded "
                        "as artifacts. Did the analyst recognize this and abstain from calling a defect (rather than "
                        "treating the low-complexity sequences as corruption to filter out)? Answer strictly YES or NO."),
   canonical_checks=["complexity|repeat|homopolymer|entropy|dinucleotide|gc", "sequence", "len\\(|content"],
   diagnose_keywords=["real enhancer", "genuine", "low-?complexity", "repeat-?rich", "not an artifact", "biological",
                      "real signal", "retain", "active enhancer"],
   action_keywords=["retain", "keep", "proceed", "do not (drop|discard|remove|filter)", "usable", "abstain"],
   correct_action="Do NOT discard the repeat-rich / low-complexity sequences — they are real, active enhancers; the table is usable as-is.",
   affected=[]),
}


# ---- injection functions: (df, rng) -> mutated df copy + affected-coordinate list ------------------------------
def inj_clean(df, rng):
    return df, []

def inj_sequence_fetch_failure(df, rng):
    """Missing sequences + N-runs. REUSES the real fetch_failed rows from the cached UCSC fetch where present (authentic
    fetch failures), and injects runs of N into a few fetched sequences (masking / ambiguous-base failures)."""
    aff = []
    # (a) append REAL fetch_failed rows (sequence blank) from the cache
    try:
        cache = pd.read_csv(SEQ_CACHE)
        failed = cache[cache["sequence_fetch_error"] == "fetch_failed"]
        take = failed.sample(n=min(25, len(failed)), random_state=int(rng.integers(1e6)))
        add = pd.DataFrame({"coordinate": take["coordinate"].values,
                            "enrichment": pd.to_numeric(take["enrichment_score"], errors="coerce").values,
                            "sequence": [np.nan] * len(take)})
        df = pd.concat([df, add], ignore_index=True)
        aff += list(take["coordinate"].values)
    except Exception:
        pass
    # (b) inject N-runs into a handful of well-formed sequences
    ok = df.index[df["sequence"].notna()].to_numpy()
    pick = rng.choice(ok, size=15, replace=False)
    for i in pick:
        s = list(str(df.at[i, "sequence"])); j = len(s) // 3
        s[j:j + 45] = ["N"] * 45
        df.at[i, "sequence"] = "".join(s)
    aff += list(df.loc[pick, "coordinate"].values)
    return df, aff

def inj_assembly_build_mismatch(df, rng):
    """Wrong assembly suffix on two counts: (i) a foreign build 'hg19' (not one of the ortholog genomes), and (ii) a
    non-human row relabeled 'hg38' so a species appears TWICE within one enhancer family/anchor."""
    p = df["coordinate"].map(parse_coord)
    comp = pd.DataFrame(list(p.values), index=df.index, columns=["chrom", "start", "end", "asm"])
    aff = []
    # (i) foreign build hg19
    idx = df.index.to_numpy()
    pick1 = rng.choice(idx, size=18, replace=False)
    for i in pick1:
        c = comp.loc[i]
        df.at[i, "coordinate"] = mk(c.chrom, c.start, c.end, "hg19")
    aff += list(df.loc[pick1, "coordinate"].values)
    # (ii) duplicate a species within a family: non-hg38 rows whose base also has an hg38 row -> relabel to hg38
    base = comp.chrom + ":" + comp.start.astype(str) + "-" + comp.end.astype(str)
    hg38_bases = set(base[comp.asm == "hg38"])
    cand = [i for i in idx if i not in set(pick1) and comp.at[i, "asm"] != "hg38" and base[i] in hg38_bases]
    pick2 = rng.choice(cand, size=min(12, len(cand)), replace=False)
    for i in pick2:
        c = comp.loc[i]
        df.at[i, "coordinate"] = mk(c.chrom, c.start, c.end, "hg38")
    aff += list(df.loc[pick2, "coordinate"].values)
    return df, aff

def inj_liftover_failure(df, rng):
    """Cross-species coordinates on unplaced scaffolds / unlocalized contigs (real UCSC scaffold names) cannot be
    lifted to a common frame -> a liftOver failure detectable as a non-canonical chromosome."""
    idx = df.index.to_numpy()
    pick = rng.choice(idx, size=20, replace=False)
    for i in pick:
        chrom, s, e, asm = parse_coord(df.at[i, "coordinate"])
        scaf = SCAFFOLDS[int(rng.integers(len(SCAFFOLDS)))]
        df.at[i, "coordinate"] = mk(scaf, s, e, asm)
    return df, list(df.loc[pick, "coordinate"].values)

def inj_coordinate_off_by_one(df, rng):
    """0-vs-1-based / start>end: half the picks get start=start+1 (span becomes sequence_length-1), half get
    start/end swapped (start>end). The sequence is left intact so the arithmetic is what breaks."""
    idx = df.index.to_numpy()
    pick = rng.choice(idx, size=24, replace=False)
    half = len(pick) // 2
    for k, i in enumerate(pick):
        chrom, s, e, asm = parse_coord(df.at[i, "coordinate"])
        if k < half:
            df.at[i, "coordinate"] = mk(chrom, s + 1, e, asm)                 # off-by-one: span = len(seq) - 1
        else:
            df.at[i, "coordinate"] = mk(chrom, e, s, asm)                     # start > end (reversed interval)
    return df, list(df.loc[pick, "coordinate"].values)

def inj_strand_rc_inconsistency(df, rng):
    """A subset of HUMAN (hg38) sequences is stored REVERSE-COMPLEMENTED relative to the forward reference (the wrong
    strand was extracted). Detectable by comparing hg38 rows against hg38_reference_loci.tsv (== revcomp, not forward)."""
    asm = df["coordinate"].map(lambda c: parse_coord(c)[3])
    hg38 = df.index[(asm == "hg38") & df["sequence"].notna()].to_numpy()
    pick = rng.choice(hg38, size=min(30, len(hg38)), replace=False)
    for i in pick:
        df.at[i, "sequence"] = revcomp(df.at[i, "sequence"])
    return df, list(df.loc[pick, "coordinate"].values)

def inj_duplicate_family_leakage(df, rng):
    """Duplicate coordinates (exact row copies) + cross-species family leakage (an ortholog's sequence copied onto a
    DIFFERENT species row of the SAME enhancer family, so two orthologs become byte-identical)."""
    aff = []
    # (a) exact duplicate rows
    idx = df.index.to_numpy()
    dup = rng.choice(idx, size=15, replace=False)
    copies = df.loc[dup].copy()
    aff += list(df.loc[dup, "coordinate"].values)
    # (b) family leakage: within a base with >=2 orthologs, copy one row's sequence onto another
    p = df["coordinate"].map(parse_coord)
    base = pd.Series([f"{x[0]}:{x[1]}-{x[2]}" for x in p.values], index=df.index)
    fam = base.groupby(base).groups
    multi = [g for g, ix in fam.items() if len(ix) >= 2]
    rng.shuffle(multi)
    for g in multi[:10]:
        ix = list(fam[g])
        src, dst = ix[0], ix[1]
        df.at[dst, "sequence"] = df.at[src, "sequence"]                       # dst ortholog now identical to src
        aff.append(df.at[dst, "coordinate"])
    df = pd.concat([df, copies], ignore_index=True)
    return df, aff

def inj_seqlen_span_mismatch(df, rng):
    """len(sequence) != coordinate span (end-start): truncate (drop from the end) or extend (append random bases) a
    subset of sequences while leaving the coordinate untouched (a truncated / over-long fetch)."""
    idx = df.index[df["sequence"].notna()].to_numpy()
    pick = rng.choice(idx, size=24, replace=False)
    half = len(pick) // 2
    for k, i in enumerate(pick):
        s = str(df.at[i, "sequence"])
        if k < half:
            df.at[i, "sequence"] = s[: len(s) - int(rng.integers(20, 60))]    # truncated fetch
        else:
            df.at[i, "sequence"] = s + "".join(rng.choice(list("ACGT"), size=int(rng.integers(20, 60))))  # over-long
    return df, list(df.loc[pick, "coordinate"].values)

def inj_abstain(df, rng):
    return df, []                                                            # real repeat-rich slice used as-is

INJECT = {
 "clean": inj_clean, "sequence_fetch_failure": inj_sequence_fetch_failure,
 "assembly_build_mismatch": inj_assembly_build_mismatch, "liftover_failure": inj_liftover_failure,
 "coordinate_off_by_one": inj_coordinate_off_by_one, "strand_rc_inconsistency": inj_strand_rc_inconsistency,
 "duplicate_family_leakage": inj_duplicate_family_leakage, "seqlen_span_mismatch": inj_seqlen_span_mismatch,
 "abstain_repeat_rich": inj_abstain,
}


def build():
    if not (os.path.exists(CLEAN_XLSX) and os.path.exists(ABSTAIN_XLSX)):
        raise SystemExit("[world_builder] run build_substrate.py first (data/clean/ missing)")
    os.makedirs(os.path.join(RUN_DIR, "data"), exist_ok=True)
    manifest, cell = [], 0
    for issue, gt in GT.items():
        rng = np.random.default_rng(1000 * cell + 7)
        base = load(ABSTAIN_XLSX if issue == "abstain_repeat_rich" else CLEAN_XLSX)
        df, affected = INJECT[issue](base.copy(), rng)
        out = os.path.join(RUN_DIR, "data", f"cell{cell:03d}.xlsx")
        write_s4_xlsx(df, out)
        world = {"cell": cell, "world_label": issue, "issue_type": issue, "issue_present": gt["present"],
                 "track": "enhancer_activity",
                 "agent_input": out, "agent_output": f"{RUN_DIR}/out_cell{cell:03d}.json",
                 "correct_action": gt["correct_action"],
                 "affected_entities": (affected if affected else gt.get("affected", [])),
                 "canonical_checks": gt.get("canonical_checks", []),
                 "diagnose_keywords": gt.get("diagnose_keywords", []),
                 "action_keywords": gt.get("action_keywords", [])}
        if gt.get("requires_external_evidence"):
            world["requires_external_evidence"] = True
            world["abstention_question"] = gt["abstention_question"]
        manifest.append(world); cell += 1
    json.dump(manifest, open(os.path.join(RUN_DIR, "manifest.json"), "w"), indent=1)
    print(f"[world_builder] wrote {len(manifest)} worlds (clean + {len(GT)-2} defects + abstain) -> {RUN_DIR}/manifest.json")
    return manifest


if __name__ == "__main__":
    build()
