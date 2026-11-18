"""LEVEL 2 - Task A runner: GWAS Signal EDA (disease-aware). Non-prescriptive sandbox; the agent must
sanity-check the association signal (lambda_GC, p-value distribution, sig counts, beta distribution, top
hits) AND assess biological plausibility for the trait, then give a usability verdict + structured JSON.

usage: run_gwas_signaleda_sandbox.py <manifest.json> <model> [out_suffix]
"""
import json, sys, subprocess, os, shutil
from openai import OpenAI
import sandbox_seal as S                              # sealed execution (review point #1)

MAN = json.load(open(sys.argv[1])); MODEL = sys.argv[2] if len(sys.argv) > 2 else "gpt-4.1"
SUFFIX = sys.argv[3] if len(sys.argv) > 3 else MODEL
MAX_STEPS = 14; TIMEOUT = 60
client = OpenAI()
DATADIR = "/workspace/discern-benchmark/tracks/cf_gwas/data/gwas_cys_fib"
DOCS = ["study_metadata.json", "data_dictionary.json"]   # placed alongside the data for the agent to discover

PROMPT = """You are a statistical geneticist doing exploratory QC on a GWAS BEFORE any downstream analysis.
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

RUN_PY = [{"type": "function", "function": {"name": "run_python",
    "description": "Execute Python on the GWAS dataframe `df`. Print results.",
    "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}}]

def hdr_for(in_path):
    return (f"import pandas as pd, numpy as np\nfrom scipy import stats\n"
            f"pd.set_option('display.width',220); pd.set_option('display.max_columns',30)\n"
            f"df = pd.read_csv({in_path!r}, sep='\\t', compression='gzip', low_memory=False)\n")

def sandbox(cells, in_path, work):                  # sealed: only `work` (input+docs) is visible, no net
    return S.run_sealed(sys.executable, hdr_for(in_path) + "\n".join(cells), work, TIMEOUT)

def parse(raw):
    try: return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
    except Exception: return None

os.makedirs(os.path.dirname(MAN[0]["agent_output"]), exist_ok=True)
DOC_SRCS = [f"{DATADIR}/{_f}" for _f in DOCS if os.path.exists(f"{DATADIR}/{_f}")]   # discoverable, allowed
done = 0
for m in MAN:
    out_path = m["agent_output"].replace(".json", f"_{SUFFIX}.json")
    work, path = S.make_world_dir(m["agent_input"], docs=DOC_SRCS)   # isolated dir; `path` is in-sandbox
    prompt = PROMPT.format(trait=m.get("trait_context", "a trait"), path=path)
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
        messages.append({"role": "user", "content": "Analysis budget reached. Return ONLY the final JSON now."})
        fk = dict(model=MODEL, messages=messages)
        if not MODEL.startswith(("gpt-5", "o1", "o3", "o4")): fk["temperature"] = 0
        final = client.chat.completions.create(**fk).choices[0].message.content
    d = parse(final or "") or {"_noncompliant": True, "trajectory": []}
    json.dump(d, open(out_path, "w"), indent=1)
    json.dump({"model": MODEL, "world_label": m["world_label"], "n_code_cells": len(trace),
               "code_trace": trace, "prompt": prompt, "final_raw": final},
              open(out_path.replace(".json", ".trace.json"), "w"), indent=1)
    if not d.get("_noncompliant"): done += 1
    shutil.rmtree(work, ignore_errors=True)
    print(f"cell{m['cell']:03d} {m['world_label']:<20} usable={d.get('usable_for_downstream')} "
          f"cells={len(trace)} {'OK' if not d.get('_noncompliant') else 'BAD'}")
print(f"\nmodel={MODEL} compliant={done}/{len(MAN)}")
