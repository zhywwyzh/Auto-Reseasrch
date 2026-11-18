"""Harness-v2 unified runner for L1 + L2 tasks (items 2+3+4).

Replaces the four near-duplicate runners (run_gwas_sandbox / signaleda / task2 / twas): ONE loop that reads
the world manifest, runs each world through the SEALED sandbox via models.run_agent (family-routed, so gpt-*
and claude-* both work), and repeats each world `reps` times for variance. Output per (world, model, rep):
  <run_dir>/out_cell<NNN>_<model>_rep<r>.json   (+ .trace.json ; TWAS also persists produced/*.csv)

usage: run_level.py <spec_name> <level> <model> [reps]
  level in {L1, signaleda, locus, twas}
"""
import json, sys, os, shutil, glob, re, hashlib
import task_spec as T
import sandbox_seal as S
import models as M

SPEC = T.load(sys.argv[1]); LEVEL = sys.argv[2]; MODEL = sys.argv[3]
REPS = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else SPEC.get("reps", 1)
# optional: run ONLY specific cells (for targeted re-runs / smoke tests). e.g. --cells 0,22
CELLS = (set(int(x) for x in sys.argv[sys.argv.index("--cells") + 1].split(","))
         if "--cells" in sys.argv else None)
TEMP = 0.7 if REPS > 1 else 0                     # need stochasticity for repeats to carry variance
GEN_SYS = SPEC.get(
    "agent_system",
    "You are a careful computational biologist. Do the task with the sandbox and return ONLY the requested JSON."
)

def std_hdr(p):
    return (f"import pandas as pd, numpy as np\nfrom scipy import stats\n"
            f"pd.set_option('display.width',220); pd.set_option('display.max_columns',30)\n"
            f"df = pd.read_csv({p!r}, sep='\\t', compression='gzip', low_memory=False)\n")

def twas_hdr(p):
    return (f"import pandas as pd, numpy as np, subprocess, os, sys\n"
            f"df = pd.read_csv({p!r}, sep='\\t', compression='gzip', low_memory=False)\n")

def vcf_hdr(p):                                   # VCF tracks: no df preload (VCF isn't a flat table); give path + pysam
    return (f"import pysam, pandas as pd, numpy as np, os\n"
            f"vcf_path = {p!r}   # the VCF to QC (parse it yourself; pysam.VariantFile or plain text)\n")

def scrna_hdr(p):                                 # scRNA tracks: no preload; the agent gets a 10x .tar.gz to unpack
    return ("import pandas as pd, numpy as np, os, tarfile, gzip, glob\nimport scipy.io as sio, scipy.sparse as sp\n"
            f"data_dir = {p!r}   # a 10x download directory: a .tar.gz archive of the matrix trio "
            "(matrix.mtx.gz + barcodes.tsv.gz + features.tsv.gz, inside gene_bc_matrices/hg19/) PLUS "
            "study_metadata.json alongside\n"
            "# EXTRACT the .tar.gz yourself (tarfile) into data_dir, then load the matrix "
            "(scanpy.read_10x_mtx on the extracted dir, or scipy.io.mmread on matrix.mtx.gz)\n")

def pdb_hdr(p):                                   # protein-structure tracks: no preload; hand the agent a dir with a PDB/mmCIF file to parse with Biopython
    return ("import os, glob, json\nimport numpy as np\n"
            "import warnings; warnings.filterwarnings('ignore')\n"
            "from Bio.PDB import PDBParser, MMCIFParser\nfrom Bio.PDB.MMCIF2Dict import MMCIF2Dict\n"
            f"data_dir = {p!r}   # a directory holding ONE protein structure file (structure.pdb or structure.cif) "
            "PLUS structure_meta.json alongside\n"
            "# locate + parse the structure YOURSELF: PDBParser(QUIET=True) for .pdb, MMCIFParser(QUIET=True) for .cif "
            "(MMCIF2Dict exposes raw auth_seq_id vs label_seq_id); read structure_meta.json for the intended mutation\n")

def pdb_l2_hdr(p):                                # protein_ddg L2: a world dir with structure.pdb + task_meta.json + mutation file(s) (NOT L1's structure_meta.json)
    return ("import os, glob, json\nimport numpy as np, pandas as pd\n"
            "import warnings; warnings.filterwarnings('ignore')\n"
            "from Bio.PDB import PDBParser\n"
            f"data_dir = {p!r}   # world directory: structure.pdb + task_meta.json (has `sequence`, `structure`, the "
            "stated ΔΔG convention/units) + mutations.csv / mutations_ddg.csv / provided_features.csv as present\n"
            "# read task_meta.json + the mutation file(s) yourself; a sequence LM is available (`import esm, torch`); "
            "Bio.PDB.SASA.ShrakeRupley gives burial\n")

def histone_hdr(p):                               # histone tracks: no preload (a directory containing BigWigs, RNA, and annotations)
    return (
        "import os, glob\n"
        "import pandas as pd, numpy as np\n"
        "from scipy import stats\n"
        "import pyBigWig\n"
        f"dataset_dir = {p!r}\n"
        "histone_dir = os.path.join(dataset_dir, 'histone')\n"
        "expression_dir = os.path.join(dataset_dir, 'expression')\n"
        "reference_dir = os.path.join(dataset_dir, 'reference')\n"
    )

def hist_tab_hdr(p):                              # hist L2 table sub-tasks (regression/effect_ranking): plain-CSV df preload
    return ("import os, glob\nimport pandas as pd, numpy as np\nfrom scipy import stats\n"
            f"df = pd.read_csv({p!r})   # the per-gene table (its directory may hold additional related files)\n")

def hist_dir_hdr(p):                              # hist L2 quantify: world dir with meta.json + genes.csv + alignments/
    return ("import os, glob, json, subprocess, sys\nimport pandas as pd, numpy as np\nfrom scipy import stats\nimport pysam\n"
            f"world_dir = {p!r}   # world directory: meta.json (target mark + layout) + genes.csv + alignments/ (ChIP BAM + input-control BAM, indexed)\n")

def bulk_l2_hdr(p):                               # bulk_rnaseq L2: world dir with meta.json + counts/DE-table + metadata (+ prepared artifacts)
    return ("import os, glob, json\nimport pandas as pd, numpy as np\nfrom scipy import stats\n"
            f"world_dir = {p!r}   # world directory: meta.json describes the task inputs; list the files yourself\n")

def crispr_l2_hdr(p):                             # crispr_screen L2: world dir with counts.tsv.gz + meta.json (+ prepared artifact); CEG/NEG/align mounted ro
    return ("import os, glob, json\nimport pandas as pd, numpy as np\nfrom scipy import stats\n"
            f"world_dir = {p!r}   # world directory: meta.json gives the counts file + CEGv2/NEGv1/alignment resource paths; list the files yourself\n")

def orbital_l1_hdr(p):
    """Orbital L1: preload the agent-visible QC inputs."""
    return (
        "import os, json\n"
        "import pandas as pd, numpy as np\n"
        "from scipy import stats\n"
        f"world_dir = {p!r}\n"
        "df = pd.read_csv(os.path.join(world_dir, 'observations.csv.gz'))\n"
        "observer_ephemeris = pd.read_csv(os.path.join(world_dir, 'observer_ephemeris.csv.gz'))\n"
        "observation_meta = json.load(open(os.path.join(world_dir, 'observation_meta.json')))\n"
    )




def calorimetry_l1_hdr(p):
    """Calorimetry L1: preload ThermoML heat-capacity QC inputs."""
    return (
        "import os, json\n"
        "import pandas as pd, numpy as np\n"
        "from scipy import stats\n"
        f"world_dir = {p!r}\n"
        "df = pd.read_csv(os.path.join(world_dir, 'heat_capacity.csv.gz'))\n"
        "measurement_meta = json.load(open(os.path.join(world_dir, 'measurement_meta.json')))\n"
    )


def oscillations_l1_hdr(p):
    """Oscillations L1: preload the agent-visible pendulum QC inputs."""
    return (
        "import os, json\n"
        "import pandas as pd, numpy as np\n"
        "from scipy import stats\n"
        f"world_dir = {p!r}\n"
        "df = pd.read_csv(os.path.join(world_dir, 'pendulum.csv.gz'))\n"
        "measurement_meta = json.load(open(os.path.join(world_dir, 'measurement_meta.json')))\n"
    )


def nuclear_decay_l1_hdr(p):
    """Nuclear-decay L1: preload the agent-visible Co-60 QC inputs."""
    return (
        "import os, json\n"
        "import pandas as pd, numpy as np\n"
        "from scipy import stats\n"
        f"world_dir = {p!r}\n"
        "df = pd.read_csv(os.path.join(world_dir, 'radiation.csv.gz'), low_memory=False)\n"
        "measurement_meta = json.load(open(os.path.join(world_dir, 'measurement_meta.json')))\n"
    )


def calorimetry_l2_hdr(p):
    """Calorimetry L2: preload equilibrium-analysis inputs."""
    return (
        "import os, sys, json\n"
        "import pandas as pd, numpy as np\n"
        "from scipy import stats\n"
        f"world_dir = {p!r}\n"
        "df = pd.read_csv(os.path.join(world_dir, 'heat_capacity.csv.gz'))\n"
        "problem = json.load(open(os.path.join(world_dir, 'problem.json')))\n"
        "analysis_config = json.load(open(os.path.join(world_dir, 'analysis_config.json')))\n"
        "sys.path.insert(0, world_dir)\n"
        "import calorimetry_runtime\n"
    )


def oscillations_l2_hdr(p):
    """Oscillations L2: preload pendulum system-identification inputs."""
    return (
        "import os, sys, json\n"
        "import pandas as pd, numpy as np\n"
        "from scipy import stats\n"
        f"world_dir = {p!r}\n"
        "df = pd.read_csv(os.path.join(world_dir, 'trajectories.csv.gz'))\n"
        "problem = json.load(open(os.path.join(world_dir, 'problem.json')))\n"
        "analysis_config = json.load(open(os.path.join(world_dir, 'analysis_config.json')))\n"
        "sys.path.insert(0, world_dir)\n"
        "import pendulum_runtime\n"
    )


def nuclear_decay_l2_hdr(p):
    """Nuclear-decay L2: preload decay-fitting inputs and gold-free runtime."""
    return (
        "import os, sys, json\n"
        "import pandas as pd, numpy as np\n"
        "from scipy import stats\n"
        f"world_dir = {p!r}\n"
        "df = pd.read_csv(os.path.join(world_dir, 'decay_measurements.csv.gz'))\n"
        "problem = json.load(open(os.path.join(world_dir, 'problem.json')))\n"
        "analysis_config = json.load(open(os.path.join(world_dir, 'analysis_config.json')))\n"
        "sys.path.insert(0, world_dir)\n"
        "import decay_runtime\n"
    )


def orbital_l2_hdr(p):
    """Orbital L2: preload the public analysis interface and world inputs."""
    return (
        "import os, sys, json\n"
        "import pandas as pd, numpy as np\n"
        "from scipy import stats\n"
        f"world_dir = {p!r}\n"
        "df = pd.read_csv(os.path.join(world_dir, 'observations.csv.gz'))\n"
        "problem = json.load(open(os.path.join(world_dir, 'problem.json')))\n"
        "geometry_config = json.load(open(os.path.join(world_dir, 'geometry_config.json')))\n"
        "sys.path.insert(0, world_dir)\n"
        "import orbit_runtime\n"
    )



def enhancer_l2_hdr(p):                           # enhancer_activity L2: world dir with enhancer_table.csv + meta.json (cross-species divergence)
    return ("import os, glob, json, re\nimport pandas as pd, numpy as np\nfrom scipy import stats\n"
            f"world_dir = {p!r}   # world directory: meta.json describes enhancer_table.csv (coordinate, enrichment_score, sequence); family = coordinate minus _<assembly>\n")

def enhancer_hdr(p):                              # enhancer-activity tracks: no preload; hand the agent a RAW .xlsx to parse
    return ("import os, re\nimport pandas as pd, numpy as np\nfrom scipy import stats\n"
            f"xlsx_path = {p!r}   # a raw .xlsx workbook (original Klein-2018 Supplementary File 2 format)\n"
            "# PARSE it yourself: pd.read_excel(xlsx_path, sheet_name='S4 All ortholog scores', header=1) (openpyxl installed).\n"
            "# Sheet 'S4 All ortholog scores': ROW 0 is a title, the REAL header is ROW 1, data start ROW 2. Each\n"
            "# 'Enhancer Coordinates (hg19)' is a STRING '<chrom>:<start>-<end>_<assembly>' (parse chrom/start/end/assembly out).\n")

L1_PROMPT = """You are a statistical geneticist. You are given a GWAS summary-statistics file that may or may not contain data-quality / integrity problems. Determine whether these summary statistics can be TRUSTED for downstream analysis (e.g. TWAS), and what would need to be fixed first.

Dataset path: {path}   (tab-separated, gzip-compressed; one row per variant)
Its directory may contain additional files describing the dataset.

You have a Python sandbox: call run_python(code) to run any analysis (you may also read other files in the dataset's directory). The dataframe is preloaded as `df` (pandas as pd, numpy as np, scipy.stats as stats; statsmodels/sklearn importable). Only text you print is returned — plots are NOT rendered, so print numeric summaries.

Record EVERY step and analysis you actually perform in `trajectory` — each check you ran, what it showed, and your conclusion (include checks that turned up nothing). Then return ONLY a JSON object (no prose):
{{"issues_found": [{{"description": "<what is wrong, in your words, or 'none'>",
                    "affected_entities": ["<variant_id or column, if identifiable>"],
                    "action": "<what you would do about it, or 'none'>"}}],
 "issue_present_probability": <0-1>,
 "analysis_usable": <true|false>,
 "trajectory": [{{"step": "<what you examined>", "finding": "<what you found>", "action": "<what you concluded/did>"}}]}}"""

SIG_PROMPT = """You are a statistical geneticist doing exploratory QC on a GWAS BEFORE any downstream analysis.
Trait: {trait}.

GOAL: decide whether this GWAS's association signal is trustworthy for downstream analysis. Inspect the
signal however you see fit and report what you find.

Dataset path: {path}   (tab-separated, gzip; one row per variant)
Its directory may contain additional files describing the dataset.

Python sandbox: call run_python(code); `df` is preloaded (pandas/numpy/scipy); you may also read other
files in the dataset's directory. Only printed text returns; no plots. Record EVERY step and analysis you
actually perform in `trajectory` — each check you ran, what it showed, and your conclusion (include checks
that turned up nothing). Then return ONLY this JSON:
{{"findings": "<your assessment of whether the signal is statistically sound and trustworthy for \
downstream analysis, with the specific evidence you found>",
 "usable_for_downstream": <true|false>,
 "trajectory": [{{"step": "<what you examined>", "finding": "<what you found>", "action": "<conclusion>"}}]}}"""

LOCUS_PROMPT = """You are a statistical geneticist analyzing GWAS summary statistics for {trait}.

GOAL: identify the genome-wide-significant lead SNPs and group nearby variants into candidate loci.
- Genome-wide significance threshold: p < 5e-8.
- Distance-based locus rule: group significant variants within +-500kb of a lead SNP on the same chromosome.
- For each locus report the lead SNP and how many significant variants fall in it (is it one variant or many?).

Dataset path: {path}   (tab-separated, gzip; one row per variant)
Its directory may contain additional files describing the dataset.

Python sandbox: call run_python(code); `df` is preloaded (pandas/numpy/scipy); you may also read other
files in the dataset's directory. Only printed text returns; no plots. Run whatever you consider
appropriate. Record EVERY step and analysis you actually perform in `trajectory` — each check you ran,
what it showed, and your conclusion (include checks that turned up nothing). Then return ONLY this JSON:
{{"loci": [{{"chromosome": <int>, "lead_variant_id": "<id>", "lead_pos": <int>, "lead_pval": <float>,
            "n_variants_in_locus": <int>}}],
 "n_genome_wide_significant": <int>,
 "data_quality_flags": ["<any integrity problem you found and acted on, or empty>"],
 "analysis_usable": <true|false>,
 "notes": "<brief: is signal concentrated/broad; did corruption affect it>",
 "trajectory": [{{"step": "<what you examined>", "finding": "<what you found>", "action": "<what you did>"}}]}}"""

TWAS_PROMPT = """You are a statistical geneticist. GOAL: run a transcriptome-wide association study (TWAS) for \
{trait} in {tissue} tissue — produce gene-level associations between genetically-predicted expression and \
the trait.

Available in the environment:
- GWAS summary statistics: {path}   (tab-separated, gzip; also preloaded as the dataframe `df`)
- A GTEx {tissue} gene-expression prediction model: {model_db}
  and its SNP covariance file: {cov}
- TWAS software is installed under: {software}   (choose the appropriate tool yourself)

Prepare the GWAS as your chosen tool requires, run the TWAS, and verify the result is sound. You have a \
Python sandbox (run_python) with subprocess access — write files and run commands as needed. Your only \
writable location is the current working directory (`.`); write all outputs there. CRITICAL: \
only the interpreter you are already running in (`sys.executable`) has the tools' dependencies — always \
invoke Python tools as `[sys.executable, "<tool>.py", ...]`. Do NOT use "/usr/bin/python3", "python3" or \
"python" (they lack the dependencies and will fail). Record EVERY step and analysis you perform in `trajectory`.

Return ONLY this JSON:
{{"output_path": "<absolute path to your final TWAS output CSV>", "tool_used": "<tool / command you ran>",
 "n_snps_used_total": <int or null>, "mapping_method": "<how you matched the GWAS SNPs to the model>",
 "issues_found": ["<any data problem you detected and had to fix, or empty>"],
 "analysis_usable": <true|false>,
 "trajectory": [{{"step": "<what you did>", "finding": "<what you found>", "action": "<what you concluded/did>"}}]}}"""

# ---- SHARED L2 PROMPT SKELETON (all tracks, all L2 sub-tasks fill the same sections) --------------------
# One structure -> role -> GOAL -> environment -> sandbox -> the trajectory instruction -> "Return ONLY this
# JSON:" -> schema. Each track supplies ONLY its slot values (role/goal/environment/sandbox/schema) via its
# spec's L2[sub]["info"]; build_l2 fills the $slots (string.Template, ignores {}) and run_level's later
# .format() fills {path}/{trait}/{tissue}/... . This is the L2 twin of task_spec.build_l1 -> no drift, and a
# new track just adds an `info` dict. (L1 is untouched.)
from string import Template as _Tmpl
L2_SKELETON = _Tmpl(
"""You are a $role. GOAL: $goal

$environment

$sandbox
Record EVERY step and analysis you actually perform in `trajectory` — each check you ran, what it showed, \
and your conclusion (include checks that turned up nothing). Return ONLY this JSON:
$schema""")

def build_l2(**slots):
    return L2_SKELETON.safe_substitute(**slots)          # leaves {path}/{trait}/{{}} for run_level's later .format()

# per-level config: which run_dir, prompt, header, interpreter, read-only mounts, budget.
# The prompt is read from the task's spec ("prompt" key) if present, else the built-in GWAS default below
# -> a NEW track supplies its own prompts via task_spec; the CF prototype uses the defaults unchanged.
def _l2p(t, default=None):                                    # L2 prompt: build from the track's `info` slots if
    return build_l2(**t["info"]) if t.get("info") else t.get("prompt", default)   # present, else legacy prompt string

def cfg(level):
    L2 = SPEC.get("L2", {})                                   # L1-only tracks (e.g. a new track mid-build) have no L2 yet
    if level == "L1":
        kind = SPEC["L1"].get("input_kind", "gwas_tsv")          # "vcf"->pysam path; "scrna"->10x matrix-dir path; else df preload
        if kind == "calorimetry":
            return dict(
                run_dir=SPEC["L1"]["run_dir"],
                prompt=SPEC["L1"].get("prompt", L1_PROMPT),
                hdr=calorimetry_l1_hdr,
                py=SPEC["L1"].get("sandbox_py", sys.executable),
                ro=SPEC["L1"].get("ro_paths", []),
                docs=False,
                steps=20,
                twas=False,
                fmt={},
                tool_desc=SPEC["L1"].get(
                    "tool_desc",
                    "Execute Python to inspect the calorimetry world directory."
                ),
            )

        if kind == "oscillations":
            return dict(
                run_dir=SPEC["L1"]["run_dir"],
                prompt=SPEC["L1"].get("prompt", L1_PROMPT),
                hdr=oscillations_l1_hdr,
                py=SPEC["L1"].get("sandbox_py", sys.executable),
                ro=SPEC["L1"].get("ro_paths", []),
                docs=False,
                steps=20,
                twas=False,
                fmt={},
                tool_desc=SPEC["L1"].get(
                    "tool_desc",
                    "Execute Python to inspect the pendulum measurement world directory."
                ),
            )
        if kind == "nuclear_decay":
            return dict(
                run_dir=SPEC["L1"]["run_dir"],
                prompt=SPEC["L1"].get("prompt", L1_PROMPT),
                hdr=nuclear_decay_l1_hdr,
                py=SPEC["L1"].get("sandbox_py", sys.executable),
                ro=SPEC["L1"].get("ro_paths", []),
                docs=False,
                steps=20,
                twas=False,
                fmt={},
                tool_desc=SPEC["L1"].get(
                    "tool_desc",
                    "Execute Python to inspect the nuclear-decay measurement world directory."
                ),
            )

        if kind == "orbital":
            return dict(
                run_dir=SPEC["L1"]["run_dir"],
                prompt=SPEC["L1"].get("prompt", L1_PROMPT),
                hdr=orbital_l1_hdr,
                py=SPEC["L1"].get("sandbox_py", sys.executable),
                ro=SPEC["L1"].get("ro_paths", []),
                docs=False,
                steps=20,
                twas=False,
                fmt={},
                tool_desc=SPEC["L1"].get(
                    "tool_desc",
                    "Execute Python to inspect the orbital world directory."
                ),
            )

        return dict(run_dir=SPEC["L1"]["run_dir"], prompt=SPEC["L1"].get("prompt", L1_PROMPT),
                    hdr=(vcf_hdr if kind == "vcf" else scrna_hdr if kind == "scrna" else pdb_hdr if kind == "pdb" else histone_hdr if kind == "histone" else enhancer_hdr if kind == "enhancer" else std_hdr),
                    py=sys.executable,
                    ro=SPEC["L1"].get("ro_paths", []), docs=True, steps=20, twas=False, fmt={},
                    tool_desc=(SPEC["L1"].get("tool_desc") if kind in ("vcf", "scrna", "pdb", "histone", "crispr", "bulkrna", "enhancer") else None))
    if level == "signaleda":
        return dict(run_dir=L2["signaleda"]["run_dir"], prompt=_l2p(L2["signaleda"], SIG_PROMPT),
                    hdr=std_hdr, py=sys.executable, ro=[], docs=True, steps=20, twas=False, fmt={"trait": SPEC["trait"]})
    if level == "locus":
        return dict(run_dir=L2["locus"]["run_dir"], prompt=_l2p(L2["locus"], LOCUS_PROMPT),
                    hdr=std_hdr, py=sys.executable, ro=[], docs=True, steps=20, twas=False, fmt={"trait": SPEC["trait"]})
    if level == "twas":
        t = L2["twas"]
        return dict(run_dir=t["run_dir"], prompt=_l2p(t, TWAS_PROMPT), hdr=twas_hdr, py=t["sandbox_py"],
                    ro=[t["software"], t["model_db"], t["cov"]], docs=False, steps=20, twas=True,   # 20: TWAS subprocess+harmonization is binding (kimi hit 14-18); others use <=6
                    fmt={"trait": SPEC["trait"], "tissue": t["tissue"], "model_db": t["model_db"],
                         "cov": t["cov"], "software": t["software"]})
    if level in L2 and SPEC["L1"].get("input_kind") == "vcf":   # clinvar-style VCF L2 sub-tasks (classify/prioritize/secondary_findings)
        t = L2[level]
        return dict(run_dir=t["run_dir"], prompt=_l2p(t, t.get("prompt")), hdr=vcf_hdr, py=sys.executable,
                    ro=t.get("ro_paths", []), docs=True, steps=20, twas=False, fmt={},
                    tool_desc=("Execute Python. `vcf_path` = the proband VCF (parse with pysam). The task lists "
                               "read-only reference DBs (gnomAD/ClinVar/CADD/hg38) — query them yourself with "
                               "pysam.VariantFile/TabixFile/FastaFile. Print results."))
    if level in L2 and SPEC["L1"].get("input_kind") == "scrna":  # scrna analysis-under-confound L2 sub-tasks (annotation/marker_de/composition)
        t = L2[level]
        return dict(run_dir=t["run_dir"], prompt=_l2p(t, t.get("prompt")), hdr=scrna_hdr, py=sys.executable,
                    ro=t.get("ro_paths", []), docs=True, steps=20, twas=False, fmt={},
                    tool_desc=("Execute Python. `data_dir` = the ABSOLUTE path to a 10x download directory -- your CWD "
                               "is its PARENT, so always join paths onto `data_dir` rather than using bare filenames. "
                               "EXTRACT the .tar.gz (tarfile), "
                               "then load with scanpy.read_10x_mtx and run the pipeline. scanpy/leidenalg/igraph/"
                               "anndata + pandas/numpy/scipy are importable; study_metadata.json sits alongside. "
                               "Print numeric summaries (no plots)."))
    if level in L2 and SPEC["L1"].get("input_kind") == "bulkrna":  # bulk_rnaseq analysis-under-confound L2 (de/gsea/structure)
        t = L2[level]
        return dict(run_dir=t["run_dir"], prompt=_l2p(t, t.get("prompt")), hdr=bulk_l2_hdr,
                    py=t.get("sandbox_py", sys.executable), ro=t.get("ro_paths", []), docs=False,
                    steps=20, twas=False, fmt={}, timeout=t.get("call_timeout"), persist=t.get("persist"),
                    tool_desc=("Execute Python. The pre-set variable `world_dir` is the ABSOLUTE path to the world directory holding the inputs -- your CWD is its PARENT, so always join paths onto `world_dir` rather than using bare filenames. Read meta.json for the task inputs and "
                               "file layout. pydeseq2 / gseapy / sklearn / statsmodels / scipy / pandas are "
                               "importable. Write files to the working directory. Print results."))
    if level in L2 and SPEC["L1"].get("input_kind") == "histone":  # hist_gene_exp analysis-under-confound L2 (regression/quantify/effect_ranking)
        t = L2[level]
        return dict(run_dir=t["run_dir"], prompt=_l2p(t, t.get("prompt")),
                    hdr=(hist_dir_hdr if t.get("dir_input") else hist_tab_hdr),
                    py=t.get("sandbox_py", sys.executable), ro=t.get("ro_paths", []), docs=False,
                    steps=20, twas=False, fmt={}, timeout=t.get("call_timeout"), persist=t.get("persist"),
                    tool_desc=("Execute Python. The pre-set variable `world_dir` is the ABSOLUTE path to the world directory holding the inputs -- your CWD is its PARENT, so always join paths onto `world_dir` rather than using bare filenames. Read meta.json for the target mark "
                               "and layout; pysam is importable and peak/coverage CLIs (macs3, deepTools "
                               "bamCompare/bamCoverage, samtools) are on PATH (invoke via subprocess). "
                               "Write files to the working directory. Print results."
                               if t.get("dir_input") else
                               "Execute Python on the per-gene table `df`. Print results."))
    if level in L2 and SPEC["L1"].get("input_kind") == "crispr":  # crispr_screen analysis-under-confound L2 (scoring/calling/context)
        t = L2[level]
        return dict(run_dir=t["run_dir"], prompt=_l2p(t, t.get("prompt")), hdr=crispr_l2_hdr,
                    py=t.get("sandbox_py", sys.executable), ro=t.get("ro_paths", []), docs=False,
                    steps=20, twas=False, fmt={}, timeout=t.get("call_timeout"), persist=t.get("persist"),
                    tool_desc=("Execute Python. The pre-set variable `world_dir` is the ABSOLUTE path to the world directory holding the inputs -- your CWD is its PARENT, so always join paths onto `world_dir` rather than using bare filenames. Read meta.json for the counts file + the "
                               "CEGv2/NEGv1/alignment resource paths. numpy / scipy / sklearn / statsmodels / "
                               "pandas are importable (no CRISPR-specific tool is installed — implement the "
                               "analysis yourself). Write files to the working directory. Print results."))
    if level in L2 and SPEC["L1"].get("input_kind") == "enhancer":  # enhancer_activity analysis-under-confound L2 (cross-species divergence)
        t = L2[level]
        return dict(run_dir=t["run_dir"], prompt=_l2p(t, t.get("prompt")), hdr=enhancer_l2_hdr,
                    py=t.get("sandbox_py", sys.executable), ro=t.get("ro_paths", []), docs=False,
                    steps=20, twas=False, fmt={}, timeout=t.get("call_timeout"), persist=t.get("persist"),
                    tool_desc=("Execute Python. The pre-set variable `world_dir` is the ABSOLUTE path to the world directory holding the inputs -- your CWD is its PARENT, so always join paths onto `world_dir` rather than using bare filenames. Read meta.json for enhancer_table.csv "
                               "(coordinate, enrichment_score, sequence). numpy / scipy / sklearn / pandas / "
                               "Biopython are importable. Write files to the working directory. Print results."))
    if level in L2 and SPEC["L1"].get("input_kind") == "pdb":   # protein_ddg L2 sub-tasks (ddg_predict/stab_classify/feature_effect)
        t = L2[level]
        return dict(run_dir=t["run_dir"], prompt=_l2p(t, t.get("prompt")), hdr=pdb_l2_hdr, py=t.get("sandbox_py", sys.executable),
                    ro=t.get("ro_paths", []), docs=False, steps=20, twas=False, fmt={},   # docs=False: L1 data_dictionary describes structure_meta.json (absent in L2 worlds)
                    timeout=t.get("call_timeout"),                                          # ESM 2.5GB checkpoint load needs >60s
                    env_extra=t.get("env_extra"),                                           # TORCH_HOME so torch.hub finds the ro-mounted ESM cache under sealed HOME
                    tool_desc=("Execute Python. `data_dir` = the ABSOLUTE path to the world directory -- your CWD is "
                               "its PARENT, so always join paths onto `data_dir` rather than using bare filenames. "
                               "It holds: structure.pdb + task_meta.json "
                               "(read `sequence`, `structure`, the stated ΔΔG convention/units) + mutations.csv / "
                               "mutations_ddg.csv / provided_features.csv as present. A sequence language model is "
                               "available: `import esm, torch; model,alph = esm.pretrained.esm2_t33_650M_UR50D()` — the "
                               "weights are cached read-only (TORCH_HOME is set for you) — plus Biopython (SASA via "
                               "Bio.PDB.SASA.ShrakeRupley, geometry), sklearn, scipy, pandas, numpy. Print results."))
    if level in L2 and SPEC["L1"].get("input_kind") == "nuclear_decay":
        t = L2[level]
        return dict(
            run_dir=t["run_dir"],
            prompt=_l2p(t, t.get("prompt")),
            hdr=nuclear_decay_l2_hdr,
            py=t.get("sandbox_py", sys.executable),
            ro=t.get("ro_paths", []),
            docs=False,
            steps=20,
            twas=False,
            fmt={},
            timeout=t.get("call_timeout"),
            persist=t.get("persist"),
            tool_desc=(
                "Execute Python. `world_dir` is the ABSOLUTE path to the "
                "nuclear-decay analysis world directory. `df`, `problem`, "
                "`analysis_config`, and `decay_runtime` are already preloaded. "
                "Use `decay_runtime.fit_world(world_dir, model=..., "
                "weighting=..., timescale=...)` for the numerical fit. "
                "Inspect the measurements, uncertainties, prepared decay-law "
                "choice, and requested physical timescale rather than blindly "
                "trusting the defaults. No network. Print numeric diagnostics."
            ),
        )

    if level in L2 and SPEC["L1"].get("input_kind") == "calorimetry":
        t = L2[level]

        return dict(
            run_dir=t["run_dir"],
            prompt=_l2p(t, t.get("prompt")),
            hdr=calorimetry_l2_hdr,
            py=t.get("sandbox_py", sys.executable),
            ro=t.get("ro_paths", []),
            docs=False,
            steps=t.get("max_steps", 20),
            twas=False,
            fmt={},
            timeout=t.get("call_timeout"),
            persist=t.get("persist"),
            tool_desc=(
                "Execute Python. `world_dir` is the ABSOLUTE path to the "
                "calorimetry-analysis world directory. `df`, `problem`, "
                "`analysis_config`, and `calorimetry_runtime` are already "
                "preloaded. `df` contains the real copper heat-capacity "
                "measurements. Read the supplied heptane enthalpy, entropy, "
                "and heat-capacity files from world_dir as needed. Verify "
                "the prepared analysis against the actual phase-resolved "
                "thermodynamic evidence rather than accepting it blindly. "
                "`calorimetry_runtime.analyze_world(world_dir)` provides "
                "a gold-free candidate analysis under selected assumptions; "
                "you may inspect its source/interface or implement another "
                "scientifically sound method. Print numerical diagnostics; "
                "no plots and no network."
            ),
        )

    if level in L2 and SPEC["L1"].get("input_kind") == "oscillations":
        t = L2[level]
        return dict(
            run_dir=t["run_dir"],
            prompt=_l2p(t, t.get("prompt")),
            hdr=oscillations_l2_hdr,
            py=t.get("sandbox_py", sys.executable),
            ro=t.get("ro_paths", []),
            docs=False,
            steps=20,
            twas=False,
            fmt={},
            timeout=t.get("call_timeout"),
            persist=t.get("persist"),
            tool_desc=(
                "Execute Python. `world_dir` is the ABSOLUTE path to the "
                "pendulum-analysis world directory. `df`, `problem`, "
                "`analysis_config`, and `pendulum_runtime` are already "
                "preloaded. Use the supplied measurements, metadata, prepared "
                "settings, and numerical helper as needed to perform and "
                "validate the analysis. Inspect the runtime's public interface "
                "or source when useful. Do not use validation trajectories "
                "for coefficient fitting. No network. Print numeric diagnostics."
            ),
        )

    if level in L2 and SPEC["L1"].get("input_kind") == "orbital":
        t = L2[level]
        return dict(
            run_dir=t["run_dir"],
            prompt=_l2p(t, t.get("prompt")),
            hdr=orbital_l2_hdr,
            py=t.get("sandbox_py", sys.executable),
            ro=t.get("ro_paths", []),
            docs=False,
            steps=20,
            twas=False,
            fmt={},
            timeout=t.get("call_timeout"),
            persist=t.get("persist"),
            tool_desc=(
                "Execute Python. `world_dir` is the ABSOLUTE path to the "
                "orbital-analysis world directory. `df`, `problem`, "
                "`geometry_config`, and `orbit_runtime` are already preloaded. "
                "Use `orbit_runtime.fit_world(world_dir, likelihood=..., "
                "observer_mode=...)` for orbit fitting; do not reimplement the "
                "N-body solver. Inspect the DATA/configuration to choose the "
                "appropriate statistical and observer settings. No network. "
                "Print numeric diagnostics."
            ),
        )

    raise SystemExit(f"unknown level '{level}' (use L1|signaleda|locus|twas|<clinvar/scrna/histone/pdb L2 sub-task>; L3 -> run_l3.py)")

def _sig(p):
    """Content fingerprint of a file: (size, md5). Used to tell a model-CREATED/MODIFIED artifact from a
    world input the model merely left in place -- mtime alone is unreliable because copytree preserves it
    and a model can rewrite a file to identical bytes."""
    try:
        b = open(p, "rb").read()
        return (len(b), hashlib.md5(b).hexdigest())
    except Exception:
        return None

def parse(raw):
    """Robust JSON extraction: tolerate ```code fences```, leading/trailing prose, and (via strict=False) raw
    control characters inside strings -- so a CORRECT answer with a formatting fumble isn't false-flagged
    non-compliant. (Real non-compliance = no {...} at all, or genuinely unparseable structure.)
    Also recovers a final answer that leaked as a Python `result = {...}` dict inside tool-call markup
    (e.g. deepseek's DSML tool-call tokens, printed via json.dumps): strips the tokens and falls back to
    ast.literal_eval on the balanced dict, which tolerates Python True/False/None literals."""
    if not raw:
        return None
    raw = re.sub(r"</?｜｜DSML｜｜[^>]*>", "", raw)   # strip leaked deepseek DSML tool-call tokens
    s = re.sub(r"```[a-zA-Z]*", "", raw.strip())          # drop markdown code fences
    try:
        s = s[s.index("{"):s.rindex("}") + 1]             # slice first{ .. last} -> tolerates surrounding prose
    except ValueError:
        return None
    for kw in ({}, {"strict": False}):                    # strict=False: allow unescaped control chars in strings
        try:
            return json.loads(s, **kw)
        except Exception:
            pass
    # Fallback: a leaked tool-call answer is a Python dict literal (True/False/None) -> json.loads fails.
    # Extract the balanced dict after a `result` assignment (else the outer slice) via ast.literal_eval.
    import ast
    for anchor in (raw.find("result"), raw.find("{")):
        if anchor < 0:
            continue
        i = raw.find("{", anchor)
        if i < 0:
            continue
        depth = 0
        for j in range(i, len(raw)):
            if raw[j] == "{":
                depth += 1
            elif raw[j] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = ast.literal_eval(raw[i:j + 1])
                        if isinstance(obj, dict) and obj:
                            return obj
                    except Exception:
                        pass
                    break
    # G8d salvage: the reply is a well-formed answer TRUNCATED mid-JSON because it hit AGENT_MAX_TOKENS
    # (claude-opus-5 crispr calling:c3 — 7,150 chars, 14 '{' vs 13 '}', cut inside the FINAL `trajectory`
    # array). Every earlier top-level field is complete, and `trajectory` is excluded from cue searches by
    # the flag-scope rule, so the gradeable content is intact. Recover it by dropping the incomplete tail
    # (back to the last completed top-level "key": value pair) and closing the object.
    # STRICTLY ADDITIVE: only runs after every parse above has failed, so it can turn unparseable into
    # parseable but can never change an already-valid parse -> no effect on task difficulty.
    # G8d salvage: UNCLOSED-CONTAINER emission. claude-opus-5 (crispr calling:c3) opened `"method": {`
    # and never closed it, so every later top-level field (issues_found / analysis_usable / trajectory)
    # nested INSIDE method and the root object never terminated -> unparseable, scored 0, despite the
    # deliverable (a 17,944-row CSV) existing and being persisted. parse()'s stated policy is that "a
    # CORRECT answer with a formatting fumble isn't false-flagged non-compliant"; a missing brace is
    # exactly that. Repair in two deterministic steps, each audit-flagged:
    #   (1) append the closers the open-container stack still needs;
    #   (2) if the SCHEMA keys are absent at root but present in exactly one nested dict, hoist them
    #       (never overwriting a key already at root).
    # STRICTLY ADDITIVE: only reached after every parse above failed, so it can never alter a valid parse.
    SCHEMA = ("analysis_usable", "issues_found")
    stack, instr, esc = [], False, False
    for ch in s:
        if instr:
            if esc:          esc = False
            elif ch == "\\": esc = True
            elif ch == '"':  instr = False
            continue
        if ch == '"':    instr = True
        elif ch in "{[": stack.append(ch)
        elif ch in "}]":
            if stack: stack.pop()
    if instr or not stack:
        return None
    repaired = s + "".join("}" if c == "{" else "]" for c in reversed(stack))
    try:
        obj = json.loads(repaired, strict=False)
    except Exception:
        return None
    if not isinstance(obj, dict) or not obj:
        return None
    obj["_brace_repaired"] = True
    if not any(k in obj for k in SCHEMA):                 # schema swallowed by a nested dict -> hoist it
        nested = [v for v in obj.values() if isinstance(v, dict) and any(k in v for k in SCHEMA)]
        if len(nested) == 1:
            for k, v in nested[0].items():
                obj.setdefault(k, v)
            obj["_schema_hoisted"] = True
    return obj

C = cfg(LEVEL)
if not M.available_for_agent(MODEL):
    raise SystemExit(f"[skip] no credential for {MODEL}'s family (set the API key first).")
MAN = T.relocate(json.load(open(f"{C['run_dir']}/manifest.json")))
if CELLS is not None:
    MAN = [m for m in MAN if m["cell"] in CELLS]
    print(f"[--cells] restricted to {len(MAN)} world(s): cells {sorted(m['cell'] for m in MAN)}")
DOC_SRCS = [f"{SPEC['docs_dir']}/{d}" for d in SPEC["docs"] if os.path.exists(f"{SPEC['docs_dir']}/{d}")] if C["docs"] else []
TOOL_DESC = (C.get("tool_desc") or
             ("Execute Python (with subprocess access) in the TWAS env. `df` is the GWAS. Print results."
              if C["twas"] else "Execute Python on the GWAS dataframe `df`. Print results."))
PERSIST = C["twas"] or C.get("persist")            # copy the produced CSV out of the sealed workdir for value-grading
PRODUCED = os.path.join(C["run_dir"], "produced"); os.makedirs(PRODUCED, exist_ok=True) if PERSIST else None

print(f"=== run_level {SPEC['name']} / {LEVEL} / {MODEL} / reps={REPS} (temp={TEMP}) : {len(MAN)} worlds ===")
done = 0
for m in MAN:
    for rep in range(REPS):
        # HARDENING (2026-09-05): a harness exception inside one cell used to propagate out of the level and
        # kill every cell behind it (glm-5.3 list-shaped tool arguments took scrna L1 4-9 and annotation 3;
        # clinvar prioritize 9,12). Now: retry the cell once from a fresh world; if it fails again, write a
        # <out>.harness_error.json SIDECAR (never an out file, so the cell reads as MISSING to graders and
        # completeness_report.py flags it for re-run) and move on.
        for _attempt in (1, 2):
            try:
                extra = [m["agent_metadata"]] if m.get("agent_metadata") and os.path.exists(m["agent_metadata"]) else []
                work, in_path = S.make_world_dir(m["agent_input"], docs=DOC_SRCS + extra)   # +per-cell metadata (VCF tracks)
                env_extra = C.get("env_extra") or ({"PATH": os.path.dirname(C["py"])} if C["twas"] else None)
                exec_fn = (lambda code, w=work, ip=in_path:
                           S.run_sealed(C["py"], C["hdr"](ip) + code, w,
                                        C.get("timeout") or (150 if C["twas"] else 60),   # per-sub-task override (e.g. hist quantify: MACS3 needs >60s)
                                        ro_paths=C["ro"], env_extra=env_extra))
                # G8c: fingerprint every file the world SHIPPED, so the persist step can tell a model-produced
                # CSV from an input the model merely left untouched (see the PERSIST block below).
                pre_sig = {os.path.realpath(p): _sig(p)
                           for p in glob.glob(os.path.join(work, "**", "*"), recursive=True) if os.path.isfile(p)}
                prompt = C["prompt"].format(path=in_path, **C["fmt"])
                M.reset_meter()                                       # efficiency: token/time/call meter for THIS task
                final, trace = M.run_agent(MODEL, GEN_SYS, prompt, "run_python", TOOL_DESC, exec_fn,
                                           max_steps=C["steps"], temperature=TEMP)
                meta = M.get_meter()
                d = parse(final or "") or {"_noncompliant": True, "trajectory": []}
                if isinstance(d, dict): d["_meta"] = meta            # tokens/wall_s/calls travel with the graded output
                # Provider stop reason for THIS agent call (models._note_stop, sticky on refusal/content_filter).
                # refusal_guard.is_refusal trusts this key when present, instead of inferring a refusal from an
                # empty final -- a shape that glm-5.3 produces after 60k+ output tokens without refusing anything.
                _stop = M.LAST_STOP_REASON.get(MODEL)
                if isinstance(d, dict): d["_stop_reason"] = _stop; d["_cap_hit"] = bool(M.CAP_HIT.get(MODEL))
                if PERSIST:                         # persist the produced CSV out of the sealed workdir for grading
                    # BUGFIX (G8c): the newest-CSV fallback used to glob the WHOLE workdir, so a run that produced
                    # nothing persisted the world's own INPUT table as `output_path` -- the grader then scored the
                    # input as if it were the model's answer. Persist only files the model actually created or
                    # modified, compared against the pre-run snapshot taken above.
                    rep_tag = f"cell{m['cell']:03d}_{MODEL}_rep{rep}"
                    reported = d.get("output_path"); cand = None
                    def _is_new(p):
                        return _sig(p) != pre_sig.get(os.path.realpath(p))
                    if reported:
                        _base = os.path.basename(str(reported))
                        for c in (reported, os.path.join(work, _base)):
                            if os.path.isfile(c) and _is_new(c): cand = c; break
                        if cand is None:                # declared basename written somewhere else under the workdir
                            same = [p for p in glob.glob(os.path.join(work, "**", _base), recursive=True) if _is_new(p)]
                            cand = sorted(same, key=os.path.getmtime)[-1] if same else None
                    # BUGFIX (2026-09-06): the newest-CSV fallback used to run even when the model DECLARED a path it
                    # never wrote, silently handing the grader whichever intermediate the model saved last. glm-5.3
                    # declared essential_genes.csv in all four crispr calling cells and never created it; for two of
                    # them the fallback persisted its 17,621-row gene-score table, which value-checked as
                    # recall=0.97/negFP=0.95 -- a score for the wrong artifact, and a masked phantom-deliverable claim.
                    # Now: a declared-but-unwritten path is RECORDED (`_output_path_unwritten`, output_path=None) and
                    # never substituted; the newest-CSV fallback is reserved for models that produced a CSV but
                    # reported no path at all.
                    elif cand is None:
                        csvs = [p for p in glob.glob(os.path.join(work, "**", "*.csv"), recursive=True) if _is_new(p)]
                        cand = sorted(csvs, key=os.path.getmtime)[-1] if csvs else None
                    if cand and os.path.isfile(cand):
                        dest = os.path.join(PRODUCED, f"{rep_tag}.csv"); shutil.copy2(cand, dest); d["output_path"] = dest
                    elif reported:                  # model NAMED an output it never actually wrote -> record the claim
                        d["_output_path_unwritten"] = reported; d["output_path"] = None
                _suf = MODEL if REPS == 1 else f"{MODEL}_rep{rep}"   # no _rep suffix at reps=1 (graders read <model>)
                out_path = m["agent_output"].replace(".json", f"_{_suf}.json")
                json.dump(d, open(out_path, "w"), indent=1)
                json.dump({"model": MODEL, "world_label": m.get("world_label", m.get("world")), "rep": rep,
                           "n_code_cells": len(trace), "code_trace": trace, "prompt": prompt, "final_raw": final,
                           "meta": meta, "stop_reason": _stop},
                          open(out_path.replace(".json", ".trace.json"), "w"), indent=1)
                if not d.get("_noncompliant"): done += 1
                shutil.rmtree(work, ignore_errors=True)
                _tok = (meta or {}).get("total", 0)
                print(f"cell{m['cell']:03d} {str(m.get('world_label', m.get('world'))):<20} rep{rep} "
                      f"cells={len(trace)} tok={_tok} {(meta or {}).get('wall_s', 0)}s "
                      f"{'OK' if not d.get('_noncompliant') else 'BAD'}")
                break
            except Exception as _e:
                import traceback as _tb
                _err = _tb.format_exc()
                try: shutil.rmtree(work, ignore_errors=True)
                except Exception: pass
                if _attempt == 1:
                    print(f"cell{m['cell']:03d} rep{rep} HARNESS-ERROR attempt 1 ({type(_e).__name__}: {str(_e)[:120]}) -- retrying once")
                    continue
                _suf = MODEL if REPS == 1 else f"{MODEL}_rep{rep}"
                _side = m["agent_output"].replace(".json", f"_{_suf}.harness_error.json")
                json.dump({"model": MODEL, "cell": m["cell"], "world": m.get("world_label", m.get("world")),
                           "error": f"{type(_e).__name__}: {_e}", "traceback": _err[-4000:],
                           "meta": M.get_meter(), "stop_reason": M.LAST_STOP_REASON.get(MODEL)},
                          open(_side, "w"), indent=1)
                print(f"cell{m['cell']:03d} rep{rep} HARNESS-ERROR persisted -> {_side}  (no out file written; re-run this cell)")
print(f"\n{SPEC['name']}/{LEVEL} model={MODEL} reps={REPS} compliant={done}/{len(MAN)*REPS}")
