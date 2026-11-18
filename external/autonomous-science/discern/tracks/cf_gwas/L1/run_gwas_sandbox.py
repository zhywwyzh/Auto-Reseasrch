"""GWAS QC sandbox runner: the agent gets a Python sandbox (run_python) + a NON-prescriptive prompt
(no QC checklist). It runs whatever analysis it wants on a GWAS summary-statistics file that may or
may not contain data-integrity problems, then returns structured JSON. Logs the full code+stdout
trajectory for the deterministic grader + honesty check. Same output schema as V3 so judge_v3 works.

usage: run_gwas_sandbox.py <manifest.json> <model> [out_suffix]
"""
import json, sys, subprocess, os, shutil
from openai import OpenAI
import sandbox_seal as S                              # sealed execution (review point #1)

MAN = json.load(open(sys.argv[1])); MODEL = sys.argv[2] if len(sys.argv) > 2 else "gpt-4.1"
SUFFIX = sys.argv[3] if len(sys.argv) > 3 else MODEL
MAX_STEPS = 14; TIMEOUT = 60
client = OpenAI()

DATADIR = "/workspace/discern-benchmark/tracks/cf_gwas/data/gwas_cys_fib"
DOCS = ["study_metadata.json", "data_dictionary.json"]   # placed ALONGSIDE the data for the agent to discover

PROMPT = """You are a statistical geneticist. You are given a GWAS summary-statistics file that may or may \
not contain data-quality / integrity problems. Determine whether these summary statistics can be TRUSTED \
for downstream analysis (e.g. TWAS), and what would need to be fixed first.

Dataset path: {path}   (tab-separated, gzip-compressed; one row per variant)
Its directory may contain additional files describing the dataset.

You have a Python sandbox: call run_python(code) to run any analysis (you may also read other files in \
the dataset's directory). The dataframe is preloaded as `df` (pandas as pd, numpy as np, scipy.stats as \
stats; statsmodels/sklearn importable). Only text you print is returned — plots are NOT rendered, so \
print numeric summaries.

Record EVERY step and analysis you actually perform in `trajectory` — each check you ran, what it \
showed, and your conclusion (include checks that turned up nothing). Then return ONLY a JSON object (no prose):
{{"issues_found": [{{"description": "<what is wrong, in your words, or 'none'>",
                    "affected_entities": ["<variant_id or column, if identifiable>"],
                    "action": "<what you would do about it, or 'none'>"}}],
 "issue_present_probability": <0-1>,
 "analysis_usable": <true|false>,
 "trajectory": [{{"step": "<what you examined>", "finding": "<what you found>", "action": "<what you concluded/did>"}}]}}"""

RUN_PY = [{"type": "function", "function": {
    "name": "run_python",
    "description": "Execute Python on the GWAS dataframe `df` (pandas/numpy/scipy). Print results.",
    "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}}]

def hdr_for(in_path):
    return (f"import pandas as pd, numpy as np\nfrom scipy import stats\n"
            f"pd.set_option('display.width',220); pd.set_option('display.max_columns',30)\n"
            f"df = pd.read_csv({in_path!r}, sep='\\t', compression='gzip', low_memory=False)\n")

def sandbox(cells, in_path, work):                  # sealed: only `work` (input+docs) is visible, no net
    return S.run_sealed(sys.executable, hdr_for(in_path) + "\n".join(cells), work, TIMEOUT)

def parse(raw):
    try:
        s = raw[raw.index("{"):raw.rindex("}") + 1]; return json.loads(s)
    except Exception:
        return None

os.makedirs(os.path.dirname(MAN[0]["agent_output"]), exist_ok=True)
DOC_SRCS = [f"{DATADIR}/{_f}" for _f in DOCS if os.path.exists(f"{DATADIR}/{_f}")]   # discoverable, allowed
done = 0
for m in MAN:
    out_path = m["agent_output"].replace(".json", f"_{SUFFIX}.json")
    work, path = S.make_world_dir(m["agent_input"], docs=DOC_SRCS)   # isolated dir; `path` is in-sandbox
    prompt = PROMPT.format(path=path)
    messages = [{"role": "user", "content": prompt}]
    cells, code_trace, final = [], [], None
    for step in range(1, MAX_STEPS + 1):
        kw = dict(model=MODEL, messages=messages, tools=RUN_PY, tool_choice="auto")
        if not MODEL.startswith(("gpt-5", "o1", "o3", "o4")): kw["temperature"] = 0
        msg = client.chat.completions.create(**kw).choices[0].message
        if not msg.tool_calls:
            final = msg.content; break
        messages.append({"role": "assistant", "content": msg.content,
                         "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})
        for tc in msg.tool_calls:
            code = json.loads(tc.function.arguments or "{}").get("code", "")
            stdout, ok = sandbox(cells + [code], path, work)  # keep the cell only if it succeeded
            if ok: cells.append(code)
            code_trace.append({"code": code, "stdout": stdout})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": stdout[-3500:]})
    if final is None:
        messages.append({"role": "user", "content":
                         "Analysis budget reached. Stop running code and return ONLY the final JSON object now."})
        fk = dict(model=MODEL, messages=messages)
        if not MODEL.startswith(("gpt-5", "o1", "o3", "o4")): fk["temperature"] = 0
        final = client.chat.completions.create(**fk).choices[0].message.content
    d = parse(final or "") or {"issues_found": [], "issue_present_probability": None,
                               "trajectory": [], "_noncompliant": True}
    json.dump(d, open(out_path, "w"), indent=1)
    json.dump({"model": MODEL, "world_label": m["world_label"], "issue_type": m["issue_type"],
               "n_code_cells": len(code_trace), "code_trace": code_trace, "prompt": prompt, "final_raw": final},
              open(out_path.replace(".json", ".trace.json"), "w"), indent=1)
    if not d.get("_noncompliant"): done += 1
    shutil.rmtree(work, ignore_errors=True)
    print(f"cell{m['cell']:03d} {m['world_label']:<20} p_issue={d.get('issue_present_probability')} "
          f"usable={d.get('analysis_usable')} cells={len(code_trace)} {'OK' if not d.get('_noncompliant') else 'BAD'}")
print(f"\nmodel={MODEL} compliant={done}/{len(MAN)}")
