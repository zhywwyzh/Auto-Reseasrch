"""LEVEL 2 - Task 2 runner: lead-SNP / locus-level analysis in a Python sandbox. The agent is given a
GWAS sumstats file that MAY contain integrity problems, told the goal (find genome-wide-significant lead
SNPs, group nearby variants into loci with a +-500kb distance rule), and must decide its own method AND
whether any cleaning is needed first. Returns a structured loci list -> deterministic grading.

usage: run_gwas_task2_sandbox.py <manifest.json> <model> [out_suffix]
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

PROMPT = """You are a statistical geneticist analyzing GWAS summary statistics for {trait}.

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

RUN_PY = [{"type": "function", "function": {"name": "run_python",
    "description": "Execute Python on the GWAS dataframe `df`. Print results.",
    "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}}]

def hdr_for(in_path):
    return (f"import pandas as pd, numpy as np\nfrom scipy import stats\n"
            f"pd.set_option('display.width',220); pd.set_option('display.max_columns',30)\n"
            f"df = pd.read_csv({in_path!r}, sep='\\t', compression='gzip', low_memory=False)\n")

def sandbox(cells, in_path, work):
    """Sealed exec (only `work` = input+docs visible, no network). Returns (stdout, ok); ok=False if the
    run errored/timed out — the caller then does NOT keep the new cell (notebook-like, no poisoning)."""
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
            so, ok = sandbox(cells + [code], path, work)    # trial-run; keep the cell only if it succeeded
            if ok: cells.append(code)
            trace.append({"code": code, "stdout": so})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": so[-3500:]})
    if final is None:
        messages.append({"role": "user", "content": "Analysis budget reached. Return ONLY the final JSON now."})
        fk = dict(model=MODEL, messages=messages)
        if not MODEL.startswith(("gpt-5", "o1", "o3", "o4")): fk["temperature"] = 0
        final = client.chat.completions.create(**fk).choices[0].message.content
    d = parse(final or "") or {"loci": [], "_noncompliant": True, "trajectory": []}
    json.dump(d, open(out_path, "w"), indent=1)
    json.dump({"model": MODEL, "world_label": m["world_label"], "n_code_cells": len(trace),
               "code_trace": trace, "prompt": prompt, "final_raw": final},
              open(out_path.replace(".json", ".trace.json"), "w"), indent=1)
    if not d.get("_noncompliant"): done += 1
    shutil.rmtree(work, ignore_errors=True)
    print(f"cell{m['cell']:03d} {m['world_label']:<20} loci={len(d.get('loci',[]))} "
          f"correct_n={m['correct_n_loci']} flags={len(d.get('data_quality_flags',[]) or [])} cells={len(trace)} "
          f"{'OK' if not d.get('_noncompliant') else 'BAD'}")
print(f"\nmodel={MODEL} compliant={done}/{len(MAN)}")
