"""LEVEL 2 - Task B runner: TWAS (Design A, tool-agnostic). The agent is given a GWAS + the GTEx model
files + a software directory, and must RUN a TWAS itself: pick the right tool, harmonize the GWAS into the
model's variant space, run it, verify soundness. Same harness as the other L2 runners, except the sandbox
executes in the `metaxcan` conda env (so the agent can run the TWAS tool via subprocess).

usage: run_gwas_twas_sandbox.py <manifest.json> <model> [out_suffix]
"""
import json, sys, subprocess, os, shutil, glob
from openai import OpenAI
import sandbox_seal as S                              # sealed execution (review point #1)

MAN = json.load(open(sys.argv[1])); MODEL = sys.argv[2] if len(sys.argv) > 2 else "gpt-4.1"
SUFFIX = sys.argv[3] if len(sys.argv) > 3 else MODEL
MAX_STEPS = 16; TIMEOUT = 150
client = OpenAI()

SANDBOX_PY = "/workspace/home/miniconda3/envs/metaxcan/bin/python"          # env that can run the TWAS tool
SOFTWARE = "/workspace/discern-benchmark/MetaXcan/software"
MODEL_DB = "/workspace/discern-benchmark/tracks/cf_gwas/L2/predictdb_gtex_v8/eqtl/mashr/mashr_Lung.db"
COV = "/workspace/discern-benchmark/tracks/cf_gwas/L2/predictdb_gtex_v8/eqtl/mashr/mashr_Lung.txt.gz"

PROMPT = """You are a statistical geneticist. GOAL: run a transcriptome-wide association study (TWAS) for \
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

RUN_PY = [{"type": "function", "function": {"name": "run_python",
    "description": "Execute Python (with subprocess access) in the TWAS environment. `df` is the GWAS. Print results.",
    "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}}]

def hdr_for(in_path):
    return (f"import pandas as pd, numpy as np, subprocess, os, sys\n"
            f"df = pd.read_csv({in_path!r}, sep='\\t', compression='gzip', low_memory=False)\n")

def sandbox(cells, in_path, work):                  # sealed: work (rw) + software/model/cov (ro); no net
    return S.run_sealed(SANDBOX_PY, hdr_for(in_path) + "\n".join(cells), work, TIMEOUT,
                        ro_paths=[SOFTWARE, MODEL_DB, COV],
                        env_extra={"PATH": os.path.dirname(SANDBOX_PY)})

def parse(raw):
    try: return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
    except Exception: return None

RUNDIR = os.path.dirname(MAN[0]["agent_output"]); os.makedirs(RUNDIR, exist_ok=True)
PRODUCED = os.path.join(RUNDIR, "produced"); os.makedirs(PRODUCED, exist_ok=True)  # persisted agent CSVs
done = 0
for m in MAN:
    out_path = m["agent_output"].replace(".json", f"_{SUFFIX}.json")
    work, path = S.make_world_dir(m["agent_input"])   # isolated writable dir; `path` is the in-sandbox input
    prompt = PROMPT.format(trait=m.get("trait_context", "a trait"), tissue=m.get("tissue", "the relevant"),
                           path=path, model_db=MODEL_DB, cov=COV, software=SOFTWARE)
    messages = [{"role": "user", "content": prompt}]; cells, trace, final = [], [], None
    for step in range(1, MAX_STEPS + 1):
        kw = dict(model=MODEL, messages=messages, tools=RUN_PY, tool_choice="auto")
        if not MODEL.startswith(("gpt-5", "o1", "o3", "o4")): kw["temperature"] = 0
        msg = client.chat.completions.create(**kw).choices[0].message
        if not msg.tool_calls: final = msg.content; break
        messages.append({"role": "assistant", "content": msg.content,
                         "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})
        for tc in msg.tool_calls:
            code = json.loads(tc.function.arguments or "{}").get("code", "")
            so, ok = sandbox(cells + [code], path, work)
            if ok: cells.append(code)
            trace.append({"code": code, "stdout": so})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": so[-3500:]})
    if final is None:
        messages.append({"role": "user", "content": "Budget reached. Return ONLY the final JSON now."})
        fk = dict(model=MODEL, messages=messages)
        if not MODEL.startswith(("gpt-5", "o1", "o3", "o4")): fk["temperature"] = 0
        final = client.chat.completions.create(**fk).choices[0].message.content
    d = parse(final or "") or {"_noncompliant": True, "trajectory": []}
    # The agent wrote inside the sealed `work` dir; persist its TWAS CSV so the grader can read it later,
    # and rewrite output_path to the persisted location. Prefer the file the agent reported; else newest CSV.
    reported = d.get("output_path")
    cand = None
    if reported:
        for c in (reported, os.path.join(work, os.path.basename(reported))):
            if os.path.isfile(c): cand = c; break
    if cand is None:
        csvs = sorted(glob.glob(os.path.join(work, "**", "*.csv"), recursive=True), key=os.path.getmtime)
        cand = csvs[-1] if csvs else None
    if cand and os.path.isfile(cand):
        dest = os.path.join(PRODUCED, f"cell{m['cell']:03d}_{SUFFIX}.csv")
        shutil.copy2(cand, dest); d["output_path"] = dest
    else:
        d["output_path"] = reported          # keep whatever the agent claimed (grader will score NO-OUTPUT)
    json.dump(d, open(out_path, "w"), indent=1)
    json.dump({"model": MODEL, "world_label": m["world_label"], "n_code_cells": len(trace),
               "code_trace": trace, "prompt": prompt, "final_raw": final},
              open(out_path.replace(".json", ".trace.json"), "w"), indent=1)
    if not d.get("_noncompliant"): done += 1
    shutil.rmtree(work, ignore_errors=True)
    print(f"cell{m['cell']:03d} {m['world_label']:<18} tool={str(d.get('tool_used'))[:22]} "
          f"snps={d.get('n_snps_used_total')} usable={d.get('analysis_usable')} cells={len(trace)} "
          f"{'OK' if not d.get('_noncompliant') else 'BAD'}")
print(f"\nmodel={MODEL} compliant={done}/{len(MAN)}")
