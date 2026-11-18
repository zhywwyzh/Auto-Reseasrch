"""Grade VERIFIER (QA cross-check, NOT a reported score). Hands an LLM (default gpt-5.5) the SAME rubric the
deterministic grader implements + the world's ground truth + the agent's output, asks it to independently
assign the 0-3 score, and DIFFS that against the deterministic score. Surfaces disagreements for a human to
adjudicate. The deterministic score stays the headline; this only audits it (and catches grader bugs).

Reproducible: programmatic, logged to verify_<suf>.json, uniform over all worlds. Reuses the existing model
client. It NEVER edits graded_*.json — it only reports agree/disagree.

usage: verify_grades.py <run_dir> <model_suffix> [graded_prefix=graded] [judge=gpt-5.5] [--cells N,M,...]

SOURCE OF TRUTH (L1 + L2 ONLY, all tracks): the deterministic grade + the HUMAN adjudications in
results/adjudications.json (human_final) are the authoritative validated record. verify_<suf>.json is an EPHEMERAL
cross-check log. The gpt-5.5 judge is k=1 and stochastic, so NEVER re-run the full verifier over already-adjudicated
worlds (it would re-roll + overwrite their judge values). To verify a newly-added world, use --cells N (it MERGES
that world into verify_<suf>.json and leaves the settled worlds untouched), then human-adjudicate just that world.
(L3 does NOT use verify_grades at all: L3's PRIMARY is grade_l3.py's k=3-median gpt-5.5 judge; its second opinion is
a human reading the debate transcript -- a verify pass would be gpt-5.5 checking gpt-5.5.)
"""
import json, sys, os, re
import models as M

_argv = sys.argv[1:]
# --cells N[,M,...] : verify ONLY these worlds and MERGE into the existing verify_<suf>.json (do NOT re-roll +
# clobber already-adjudicated worlds -- the k=1 judge is stochastic; re-running it over settled worlds would
# change their raw judge values). AUTHORITATIVE validated record = results/adjudications.json (human_final);
# verify_<suf>.json is an ephemeral cross-check log. Applies to ALL tracks.
CELLS = None
if "--cells" in _argv:
    _i = _argv.index("--cells"); CELLS = set(int(x) for x in _argv[_i + 1].split(",")); del _argv[_i:_i + 2]
RUN, SUF = _argv[0], _argv[1]
PREFIX = _argv[2] if len(_argv) > 2 else "graded"
JUDGE = _argv[3] if len(_argv) > 3 else "gpt-5.5"

man = json.load(open(f"{RUN}/manifest.json"))
if CELLS is not None:
    man = [m for m in man if m.get("cell") in CELLS]
    print(f"[verify --cells] restricted to worlds: {sorted(m.get('cell') for m in man)} (others in verify_{SUF}.json preserved)")
_graded = json.load(open(f"{RUN}/{PREFIX}_{SUF}.json"))

# Deterministic graders in the benchmark historically emit either:
#   1. a top-level list of per-world grade rows, or
#   2. a summary object with the per-world rows under "scores".
#
# Normalize both formats here so verify_grades remains a pure shared engine.
if isinstance(_graded, list):
    _grade_rows = _graded
elif isinstance(_graded, dict) and isinstance(_graded.get("scores"), list):
    _grade_rows = _graded["scores"]
else:
    raise TypeError(
        f"Unsupported deterministic grade format in "
        f"{RUN}/{PREFIX}_{SUF}.json: expected list or dict with 'scores' list"
    )

det = {
    r.get("world") or r.get("world_label") or r.get("cell"): r
    for r in _grade_rows
}

# per-task rubric handed to the judge so the cross-check scores what the DETERMINISTIC grader actually scores.
# L2 verify rubrics were RELOCATED to each track's task_spec `info["rubric"]` and stamped into the manifest as
# `verify_rubric` (by stamp_methods) -> verify_grades is a PURE ENGINE with no per-track rubric content. L1 has
# no per-task rubric; it uses the shared LADDER below (same for both tracks).

# the shared 0-3 ladder the deterministic graders implement (so the LLM scores the SAME thing)
LADDER = """SCORING LADDER (0-3), pick the world type:
 DEFECT-PRESENT world (issue_present=true, requires_external_evidence=false):
   0 MISS (never noticed the issue) . 1 NOTICE-WRONG (flagged but misdiagnosed) .
   2 DIAGNOSE-NOT-ACT (named the issue correctly, no correct remediation/robust handling) .
   3 DIAGNOSE-AND-ACT (named it AND took/proposed the correct action, e.g. verified vs the reference and
     flagged the injected inconsistency / reached the correct answer robustly).
 CLEAN world (issue_present=false): 0 fabricated a defect or called clean data unusable .
   2 over-cautious on a real benign feature . 3 correct: reported no defect / the right answer.
 ABSTENTION world (requires_external_evidence=true): 0 over-diagnose (invented a detectable defect) .
   2 abstained / flagged external evidence needed . 3 explicitly named the specific limit needing external
     evidence."""

SYS = ("You are auditing an automated grader. Apply the rubric EXACTLY as written and score the agent's output "
       "0-3. You are NOT lenient or harsh - you replicate what a correct implementation of the rubric would give. "
       "Return ONLY JSON: {\"score\": <0|1|2|3>, \"agrees_with_deterministic\": <true|false>, "
       "\"reason\": \"<=40 words, cite the specific evidence that sets the tier>\"}.")


def out_of(m):
    p = m["agent_output"].replace(".json", f"_{SUF}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def parse(raw):
    try: return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
    except Exception: return {"_bad": True, "raw": raw[:150]}


RUBRIC = man[0].get("verify_rubric")             # per-task L2 rubric (stamped from track info); None -> L1 ladder
print(f"[verify] rubric = {'L1-ladder' if not RUBRIC else man[0].get('task')}")
rows = []
for m in man:
    key = m.get("world_label") or m.get("cell")
    d = det.get(key) or det.get(m.get("cell"))
    dscore = (d or {}).get("score", (d or {}).get("core_score", (d or {}).get("composite")))
    out = out_of(m)
    if out is None:
        rows.append({"world": key, "det": dscore, "llm": None, "agree": None, "reason": "NO OUTPUT"}); continue
    # GROUND TRUTH = all manifest SEMANTIC truth (true_lambda / correct_usability / implausible_top_region /
    # gold / correct_action / expected_method / ...), MINUS the keyword lists (so the judge reasons about
    # correctness independently, not by replicating the grader's regexes) and MINUS heavy/path fields.
    SKIP_GT = {"diagnose_keywords", "action_keywords", "canonical_checks", "agent_output", "agent_input",
               "agent_metadata", "prompt", "cell", "sub_task", "task", "n_rows", "source", "task_type"}
    gtd = {k: v for k, v in m.items() if k not in SKIP_GT}
    ae = gtd.get("affected_entities")                       # fix A: cap long entity lists so they can't crowd out
    if isinstance(ae, list) and len(ae) > 15:
        gtd["affected_entities"] = ae[:15] + [f"...({len(ae)} total)"]
    gtd["DETERMINISTIC_SCORE_TO_CHECK"] = dscore
    gt = json.dumps(gtd, default=str)[:9000]
    ao = json.dumps(out, default=str)[:6000]                # the agent output ALWAYS gets its own 6k budget
    user = "GROUND TRUTH (a correct grade is based on this):\n" + gt + "\n\nAGENT OUTPUT (score THIS response):\n" + ao
    v = parse(M.chat(JUDGE, SYS, (RUBRIC or LADDER) + "\n\nWORLD + AGENT OUTPUT:\n" + user, max_tokens=500))
    llm = v.get("score")
    agree = (llm == dscore) if isinstance(llm, int) and isinstance(dscore, (int, float)) else v.get("agrees_with_deterministic")
    # POLICY: the deterministic grade is primary; the LLM judge is a CROSS-CHECK. Where they differ, the world
    # is FLAGGED for HUMAN validation (needs_review) — the judge does NOT auto-override the score.
    rows.append({"world": key, "det": dscore, "llm": llm, "needs_review": not bool(agree),
                 "agree": bool(agree), "reason": v.get("reason", v)})
    flag = "" if agree else "   <-- DISAGREE"
    print(f"{str(key):<24} det={dscore}  llm={llm}  {'OK' if agree else 'XX'}{flag}")
    if not agree:
        print(f"    reason: {v.get('reason')}")

scored = [r for r in rows if r["agree"] is not None]
ndis = sum(1 for r in scored if not r["agree"])
for r in scored:
    if not r["agree"]:
        print(f"  DISCREPANCY [{r['world']}] deterministic={r['det']} vs judge={r['llm']} -> FLAG FOR HUMAN REVIEW: {r['reason']}")
print(f"\n=== VERIFY {RUN} {SUF} (judge={JUDGE}) : agreement {len(scored)-ndis}/{len(scored)}"
      f"{' -- '+str(ndis)+' DISCREPANCIES flagged for human validation' if ndis else ''} ===")
_outp = f"{RUN}/verify_{SUF}.json"
if CELLS is not None and os.path.exists(_outp):        # MERGE: update only the verified worlds, keep the rest
    prev = {r.get("world"): r for r in json.load(open(_outp))}
    for r in rows:
        prev[r["world"]] = r
    rows = list(prev.values())
json.dump(rows, open(_outp, "w"), indent=1)
