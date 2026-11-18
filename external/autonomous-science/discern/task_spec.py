"""Per-level TASK-SPEC template (harness-v2, item 3).

A "task spec" declares everything a NEW coherent analysis needs to run the L1->L2->L3 pipeline: the clean
data substrate, which issues to inject at each level, the ground-truth parameters, and the tool/model paths.
Injection LOGIC lives in the world-builders (a registry keyed by issue name); the spec is purely declarative,
so porting the benchmark to another dataset = fill in a second SPEC dict (no code changes to runners/graders).

Fill one SPEC per dataset. Run:  python run_level.py <spec_name> <L1|L2|L3> <model> [--reps N]
Every level reads: reps, models (gpt-*/claude-*), and its own issue/analysis/gene list from here.
"""

# ---- CF-GWAS reference instance (the pilot dataset) ------------------------------------------------------
from pathlib import Path
from release_paths import relocate
BASE = str(Path(__file__).resolve().parent)

# ================= SHARED L1 PROMPT SKELETON (ALL TRACKS) =================================================
# Every L1 QC task shares this SAME structure + the SAME output contract; a new track supplies only its domain
# SLOTS (role / subject / object / downstream / input_line / resources / sandbox). This keeps L1 prompts
# consistent across tracks and prevents drift — do NOT hand-write a fresh L1 prompt per track; call build_l1().
# Two-stage templating: build_l1() fills the $slots now (string.Template, ignores braces); run_level fills the
# remaining {path} and reduces the {{...}} JSON later via str.format — so leave {path}/{{}} untouched in slots.
import os
from string import Template

L1_OUTPUT_SCHEMA = (
    '{{"issues_found": [{{"description": "<what is wrong, in your words, or \'none\'>",\n'
    '                    "affected_entities": ["<id / coordinate / column, if identifiable>"],\n'
    '                    "action": "<what you would do about it, or \'none\'>"}}],\n'
    ' "issue_present_probability": <0-1>,\n'
    ' "analysis_usable": <true|false>,\n'
    ' "trajectory": [{{"step": "<what you examined>", "finding": "<what you found>", "action": "<concluded/did>"}}]}}')

L1_SKELETON = Template(
    "You are $role. You are given $subject that may or may not contain data-integrity / QC problems. "
    "Determine whether $object can be TRUSTED for $downstream, and what would need to be fixed first.\n\n"
    "$input_line$resources\n\n"
    "You have a Python sandbox: call run_python(code). $sandbox Only text you print is returned; plots are NOT "
    "rendered.\n\n"
    "Record EVERY check you run in `trajectory` (including checks that turned up nothing). Then return ONLY this "
    "JSON:\n" + L1_OUTPUT_SCHEMA)

def build_l1(**slots):
    slots.setdefault("resources", "")                         # optional extra-resources line (default: none)
    return L1_SKELETON.safe_substitute(**slots)               # leaves {path} + {{}} for run_level's later .format()

# ================= SHARED L3 PROMPT SKELETON (ALL TRACKS) =================================================
# The L3 twin of build_l1 / run_level.build_l2. Every L3 debate turn (generate / review / defend) fills the SAME
# structure: context -> task -> "Return ONLY JSON:" -> schema. Tracks supply the per-turn context/task/schema
# wording via SPEC["L3"]["prompts"] (built with build_l3); the root run_l3/grade_l3 read them per-track. Leaves
# {dossier}/{hyp}/{rnd}/{critiques} + the {{}} JSON braces for the later .format() in each turn.
L3_SKELETON = Template("$context\n\n$task\n\nReturn ONLY JSON:\n$schema")

def build_l3(context, task, schema):
    return L3_SKELETON.safe_substitute(context=context, task=task, schema=schema)


def build_l3_reviewer(role, pushback, data_obj, subject, methods_hint):
    """SHARED L3 reviewer skeleton. The UNIVERSAL mechanics live HERE ONCE -- sandbox-verify, `fabrication_found`,
    next-step scoring, the fixed 0-2 dimension schema, no-defer -- so they cannot drift across per-track copies.
    A track supplies ONLY its domain slots; returns (rev_sys, rev_user).
      role        : reviewer identity, e.g. 'reviewer of a single-cell cell-type annotation'
      pushback    : the domain-prior pressure clause, e.g. "push back with established immunology ('CD4 is ...')"
      data_obj    : the sandbox dataframe the reviewer verifies against ('markers' / 'panel' / 'twas')
      subject     : what is under review, for the header ('interpretation' / 'molecular diagnosis' / 'hypothesis')
      methods_hint: domain guidance for the methods_soundness dimension
    """
    rev_sys = (
        "You are an expert " + role + ". Critique it rigorously, then GRADE it on three dimensions. Reason strictly "
        "from the evidence; " + pushback + ". You have the SAME sandbox + `" + data_obj + "` evidence the agent used "
        "-- inspect it with run_python to VERIFY the agent's cited values and FLAG anything FABRICATED or "
        "unsupported. Do not defer to other reviewers.")
    rev_user = build_l3(
        context="EVIDENCE DOSSIER:\n{dossier}\n\n" + subject.upper() + " UNDER REVIEW (round {rnd}):\n{hyp}",
        task=("Critique it -- VERIFY its cited evidence against the `" + data_obj + "` data in the sandbox (flag any "
              "fabricated/unsupported value), and assess whether the proposed confirmatory next step is a VALID test "
              "and whether it opens a NOVEL, discovery-guiding direction -- then grade EACH dimension 0/1/2 "
              "(2 = strong, 0 = poor)."),
        schema=('{{"critique": "...",\n'
                '  "validity": <0-2>,           /* is every claim supported by the evidence (VERIFIED in the sandbox)? */\n'
                '  "novelty": <0-2>,            /* genuinely new (2) vs already-established/published (0); incl. whether the next step opens a novel direction */\n'
                '  "methods_soundness": <0-2>,  /* ' + methods_hint + '; incl. whether the next step is a valid test */\n'
                '  "fabrication_found": "<any cited value/evidence you VERIFIED against the data to be FALSE or unsupported, or \'none\'>",\n'
                '  "already_published_as": "<prior work or \'none\'>",\n'
                '  "recommend_reject": <true|false>}}'))
    return rev_sys, rev_user

# ================= SHARED CONFIG (all tracks) =================
MODELS = ["gpt-4.1", "gpt-5.6-sol", "claude-opus-5", "deepseek-v4-pro",
          "glm-5.2", "kimi-k3", "glm-5.3", "gpt-6-astra", "claude-fable-5"]
EFFICIENCY = {"token_budget": {"L1": 60000, "L2": 150000, "L3": 250000},
              "record": ["total_tokens", "wall_s", "n_calls", "n_code_cells"]}

# ================= TRACK REGISTRY =================
# Each track ships tracks/<name>/spec.py exposing a module-level `SPEC` dict. load() imports it by path so the
# root engine has ZERO per-track content. A new track needs no edit here — just add its folder + spec.py.
def load(name):
    import importlib.util
    p = os.path.join(BASE, "tracks", name, "spec.py")
    spec = importlib.util.spec_from_file_location(f"{name}_spec", p)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return relocate(mod.SPEC)
