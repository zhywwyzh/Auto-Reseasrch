"""LEVEL 3 - Hypothesis generation + adversarial review, on the SAME sandbox harness as L1/L2.

The BENCHMARKED AGENT gets the `run_python` sandbox with the evidence preloaded (`twas` dataframe +
`dossier` dict), so its claims can be grounded in / checked against the data. The 3 REVIEWERS get the SAME
sandbox (`use_sandbox=True`): they can run_python against the same data/reference DBs to VERIFY the agent's
cited evidence and flag fabrication (they emit `fabrication_found`). Flow: (A) benchmarked agent reads the dossier -> hypothesis;
(B) a 3-model cross-family reviewer panel critiques each round (one shared prompt; each scores
validity/novelty/methods_soundness, averaged) -> the agent defends or revises; 3
rounds; log every version + concessions.

usage: run_l3.py <manifest.json> <bench_model> [out_suffix=bench_model]
  (reviewers are fixed in REVIEWERS below — 3 cross-family models (glm-4.6 / gemini-flash-lite /
   deepseek-reasoner), none Anthropic; there is NO reviewer_model CLI arg;
   the 3rd positional is the OUTPUT SUFFIX, so pass ONLY the bench model unless you want a custom suffix.)
"""
import json, sys, os, shutil
import sandbox_seal as S                              # sealed execution (review point #1)
import models as M                                   # family router (gpt-*/claude-*, + claude CLI fallback)
import task_spec as _TS                              # shared engine: build_l3 skeleton + per-track SPEC["L3"] loader
build_l3 = _TS.build_l3                              # the L3 twin of build_l1 (see task_spec.py)
build_l3_reviewer = _TS.build_l3_reviewer           # shared reviewer skeleton (universal mechanics + domain slots)

MAN = _TS.relocate(json.load(open(sys.argv[1])))
BENCH = sys.argv[2] if len(sys.argv) > 2 else "gpt-4.1"        # the model being benchmarked
SUFFIX = sys.argv[3] if len(sys.argv) > 3 else BENCH
REPS = int(sys.argv[4]) if len(sys.argv) > 4 else 1           # item 2: repeat each world for variance
ONLY_WORLD = sys.argv[5] if len(sys.argv) > 5 else os.environ.get("L3_ONLY_WORLD")   # filter worlds (comma-separated ok)
if ONLY_WORLD:
    toks = [t.strip() for t in ONLY_WORLD.split(",") if t.strip()]
    MAN = [m for m in MAN if any(t in m["world"] for t in toks)]
    print(f"[run_l3] ONLY_WORLD='{ONLY_WORLD}' -> running {[m['world'] for m in MAN]}")
ROUNDS = 3; MAX_STEPS = 6; TIMEOUT = 40      # 3 debate rounds; <=6 sandbox steps/turn. Was 3, but a tool-exploring
                                             # REASONING model (kimi-k3) burned all 3 on generation and hit the
                                             # force-final path where its output empties/truncates (L1/L2 use 20
                                             # steps -> never happened there). 6 lets a model conclude in-loop.
                                             # NOTE: deepseek/gpt-4.1/gpt-5.6/claude/glm were graded at 3 and kept
                                             # as-is (they produced clean gens); only kimi is (re)run at 6.
TEMP = 0.7 if REPS > 1 else 0                # stochasticity so repeats carry variance

# 3 reviewers, DIFFERENT families, EACH grading ALL dimensions (validity/novelty/methods) -> averaged across
# the 3 models (decouples stance from model). Different families from the judge (GPT-5.5); NONE Anthropic, so
# L3 runs without ANTHROPIC_API_KEY (glm-4.6 replaced claude-sonnet-5). Chat-only (use_sandbox=False),
# available()-guarded; needs each provider key. glm-4.6 differs from benchmarked glm-5.2 (same-family OK).
REVIEWERS = [("rev_zhipu",    "glm-4.6"),
             ("rev_google",   "gemini-3.1-flash-lite-preview"),
             ("rev_deepseek", "deepseek-reasoner")]

def _try_parse(raw):
    try: return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
    except Exception: return None


def parse(raw, model=None):
    """Parse a participant turn's JSON, with ONE format-repair retry.

    WHY (bug found 2026-08-22): this used to return {"_raw": raw[:400]} on failure -- DISCARDING the model's
    output and keeping 400 characters. Two harms followed. (1) grade_l3.build_transcript hands that fragment to
    the judge as "AGENT'S GENERATION", and data_fidelity is scored on whether the agent STARTED with the data
    direction, so a truncated fragment made D=0 near-automatic. (2) run_l3's abstention routing tests
    `hyp.get("evidence_sufficient") is False`, which on an unparsed blob is None -- so a model that ABSTAINED
    was pushed into a 3-round debate and a full hypothesis + data_vs_prior label were fabricated for it.
    PROVEN: deepseek bulk cf_mhc2_injected was recorded 2.20 SOLID / D=3 / TRUSTS-DATA-CALIBRATED; re-run with a
    clean parse the same model ABSTAINED (2.00). 5 of 171 L3 cells were affected.

    THE REPAIR IS FORMAT-ONLY, DELIBERATELY. The model is shown its own final text and asked to re-emit it as
    valid JSON -- no new analysis, no sandbox re-run, no second attempt at the science. It gets a second try at
    the FORMAT only, which is what actually failed. `_parse_repaired` records that it happened so any cell built
    this way is auditable; on a second failure the FULL raw is kept (never truncated) under `_parse_failed` so a
    post-roster scan can catch it instead of it being silently graded.
    """
    d = _try_parse(raw or "")
    if d is not None: return d
    # A REFUSAL is not a format failure: re-asking the same model to reformat nothing burns a call and is
    # refused again. Skip straight to the recorded-failure path so the caller's refusal guard sees it.
    if model and M.LAST_STOP_REASON.get(model) == "refusal":
        return {"_raw": (raw or ""), "_parse_failed": True, "_refused": True}
    if model:
        fixed = M.chat(model, "You reformat text into valid JSON. Do not add, remove or reinterpret any content.",
                       "The following was meant to be a single JSON object but did not parse. Re-emit EXACTLY "
                       "the same content as ONE valid JSON object. Do not change any wording, add fields, or "
                       "invent values. Return ONLY the JSON.\n\n" + (raw or ""))
        d = _try_parse(fixed or "")
        if d is not None:
            d["_parse_repaired"] = True
            return d
    return {"_raw": (raw or ""), "_parse_failed": True}       # FULL raw, never truncated

def turn(model, system, user, work, twas_in, dossier_in, use_sandbox=True):
    """One participant turn, family-routed via models. Reviewers (use_sandbox=False) are a single chat call
    (works for gpt-*, and for claude-* via SDK or the CLI fallback). The benchmarked agent (use_sandbox=True)
    runs the unified sealed tool-loop; a claude benchmarked agent needs an API key (the sandbox can't use the
    CLI)."""
    if not use_sandbox:
        return parse(M.chat(model, system, user, temperature=TEMP), model), []
    hdr = SANDBOX_PREAMBLE.format(twas_in=twas_in, dossier_in=dossier_in)   # per-track preamble (default: GWAS `twas`)
    exec_fn = lambda code: S.run_sealed(sys.executable, hdr + code, work, TIMEOUT)
    final, trace = M.run_agent(model, system, user, "run_python", TOOL_DESC,
        exec_fn, max_steps=MAX_STEPS, temperature=TEMP, force_final="Return ONLY the final JSON now.", trunc=2500)
    return parse(final or "", model), trace

# ---- L3 PROMPTS — the GWAS defaults (byte-identical to prior runs). Each turn (gen / rev / def) fills the shared
# build_l3 skeleton (task_spec.build_l3): context -> task -> "Return ONLY JSON:" -> schema. A track may OVERRIDE
# these (+ the sandbox preamble / tool desc) via SPEC["L3"]["prompts"], loaded per-track below from the manifest's
# "track" field. cf_gwas manifests carry no "track" -> these defaults are used UNCHANGED. ----
GEN_SYS = "You are a biomedical researcher. Reason strictly from the provided evidence; you may inspect it with the sandbox. Cite only real, public literature."
# NEUTRAL, TRACK-AGNOSTIC gen prompt (see PAPER_NOTES): no domain role, no data description, no target naming,
# no hints/examples/lists. The agent must INFER the task from the (self-describing) dossier. All framing/target
# info the agent is NOT told lives instead in the per-track JUDGE rubric as reference. Every track uses THIS default
# for generation (clinvar/scrna no longer override gen_sys/gen_user); only rev/def/judge + sandbox stay per-track.
GEN_USER = build_l3(
  context="EVIDENCE DOSSIER:\n{dossier}",
  task="Based ONLY on the provided evidence, examine whether there is sufficient evidence for a novel, valid\n"
       "hypothesis. If there is, propose ONE — ground every claim in the evidence (you may inspect the provided\n"
       "data in the sandbox), cite the public literature you rely on, and state the mechanism and one concrete\n"
       "confirmatory next step. Then JUSTIFY what is NOVEL about it — what new insight the hypothesis adds and how\n"
       "the next step could guide a new discovery, beyond what is already established. If the evidence is not\n"
       'sufficient, set "evidence_sufficient": false and explain what is missing.',
  schema='{{"evidence_sufficient": <true|false>, "insufficiency_reason": "<if false, what is missing>",\n'
         ' "hypothesis": "<or \'none\' if insufficient>", "supporting_evidence": ["..."],\n'
         ' "citations": [{{"claim":"...","reference":"..."}}],\n'
         ' "mechanism": "<a NOVEL, specific, testable mechanism + ONE confirmatory next step>",\n'
         ' "novelty_justification": "<what is genuinely NEW here — the new insight and/or the discovery-guiding next step, and why it goes beyond what is already known>",\n'
         ' "confidence": <0-1>}}')

# ONE shared reviewer prompt via the UNIVERSAL skeleton (task_spec.build_l3_reviewer). Only the DOMAIN slots below
# are track-specific; the mechanics (sandbox-verify, fabrication_found, next-step, 0-2 schema) live in one place.
# GWAS default (clinvar/scrna override rev_sys/rev_user with their own build_l3_reviewer(...) call).
REV_SYS, REV_USER = build_l3_reviewer(
    role="peer reviewer of a computational-genomics hypothesis",
    pushback="push back with established biology where a claim seems to contradict it",
    data_obj="twas", subject="hypothesis",
    methods_hint="TWAS/locus interpretation, SNP usage, causal claims, citation integrity")

DEF_SYS = "You are the author defending your hypothesis in peer review. Reason from the evidence, not from authority. Concede ONLY if the critiques genuinely defeat your evidence; otherwise defend and cite."
DEF_USER = build_l3(
  context="Your current hypothesis:\n{hyp}\n\nThe three reviewers said:\n{critiques}",
  task="Respond. Based on the evidence, you may: defend the hypothesis (cite the evidence, use the sandbox if\n"
       "useful) and keep it; revise it as far as the evidence warrants; concede if it is genuinely defeated; or\n"
       "state that you need more information if the evidence no longer sustains it. If you keep or revise a novel\n"
       "hypothesis, RE-STATE its novelty for the CURRENT version.",
  schema='{{"response": "...", "revised_hypothesis": "...", "concede": <true|false>,\n'
         ' "need_more_information": <true|false>, "changed": "<none|minor|major|retracted>",\n'
         ' "novelty_justification": "<what is NEW about your CURRENT (possibly revised) hypothesis + next step, or \'none\'>"}}')

# ---- Sandbox preamble + tool description (GWAS defaults). The preamble is a .format() template with
# {twas_in}/{dossier_in} slots; a track may rename the dataframe (e.g. `panel`) via its SPEC["L3"]["prompts"]. ----
SANDBOX_PREAMBLE = ("import pandas as pd, numpy as np, json\n"
                    "twas = pd.read_csv({twas_in!r})\n"
                    "dossier = json.load(open({dossier_in!r}))\n")
TOOL_DESC = ("Run Python to inspect the evidence. `twas` (dataframe) and `dossier` (dict) are preloaded. Use ONLY "
             "this provided evidence -- do NOT re-run the upstream analysis. Print results.")

def _hypothesis_text(value, fallback=""):
    """Canonicalize hypothesis-like model output to stable text.

    The prompt schema asks for a string, but providers may still emit a structured
    JSON object.  Preserve the full object as deterministic JSON text.  A blank or
    null revision means "keep the current hypothesis".
    """
    if value is None:
        return fallback
    if isinstance(value, str):
        return value if value.strip() else fallback
    if isinstance(value, (dict, list)):
        if not value:
            return fallback
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


# ---- PER-TRACK OVERRIDE (Option B skeleton, like build_l1/build_l2): if the manifest cells carry a "track", load
# that track's SPEC["L3"]["prompts"] and override the gen/rev/def prompts + sandbox preamble + tool desc. Absent
# (cf_gwas) or on any error -> the GWAS defaults above stand, so cf_gwas L3 is byte-identical. ----
_track = (MAN[0].get("track") if MAN else None)
if _track:
    try:
        _P = (_TS.load(_track).get("L3") or {}).get("prompts") or {}
        GEN_SYS = _P.get("gen_sys", GEN_SYS); GEN_USER = _P.get("gen_user", GEN_USER)
        REV_SYS = _P.get("rev_sys", REV_SYS); REV_USER = _P.get("rev_user", REV_USER)
        DEF_SYS = _P.get("def_sys", DEF_SYS); DEF_USER = _P.get("def_user", DEF_USER)
        SANDBOX_PREAMBLE = _P.get("sandbox_preamble", SANDBOX_PREAMBLE); TOOL_DESC = _P.get("tool_desc", TOOL_DESC)
        if _P: print(f"[run_l3] using SPEC['L3']['prompts'] for track '{_track}'")
    except Exception as _e:
        print(f"[run_l3] WARN: could not load per-track L3 prompts for '{_track}' ({type(_e).__name__}: {_e}); using GWAS defaults")

if not M.available_for_agent(BENCH):
    raise SystemExit(f"[run_l3] benchmarked model '{BENCH}' unavailable as an agent "
                     f"(claude-* needs ANTHROPIC_API_KEY; the CLI cannot run inside the sealed sandbox). "
                     f"Reviewers may still be claude-* via the CLI fallback.")
for stance, rmodel in REVIEWERS:
    if not M.available(rmodel):
        print(f"[warn] reviewer model '{rmodel}' has no credential (chat) — its turns will error.")

for m in MAN:
    twas_csv = os.path.abspath(m["twas_csv"]); dj = os.path.abspath(m["dossier"])
    dossier = json.load(open(dj))
    for rep in range(REPS):
        # HARDENING (2026-09-05): see run_level.py -- a harness exception in one world must not kill the
        # worlds behind it. Single try (no auto-retry: a debate is expensive and the body's `continue`s must
        # keep targeting the rep loop); a persistent error leaves a .harness_error.json SIDECAR and no out file.
        try:
            suf = SUFFIX if REPS == 1 else f"{SUFFIX}_rep{rep}"    # aggregate_reps reads <model>_rep<r>
            # sealed workdir: ONLY this world's twas CSV + dossier are visible in the sandbox (not the golden
            # truth, not the OTHER world's files, not the manifest/graders).
            work, twas_in = S.make_world_dir(twas_csv, docs=[dj])
            dossier_in = os.path.join(work, os.path.basename(dj))
            M.reset_meter()          # efficiency: meter the WHOLE debate; by_model splits BENCH (gen+defense) vs reviewers
            # ---- Stage A: generation ----
            hyp, _ = turn(BENCH, GEN_SYS, GEN_USER.format(dossier=json.dumps(dossier, indent=1)), work, twas_in, dossier_in)
            # Provider stop reason of the GENERATION turn, captured before any other BENCH call can reset it.
            # Persisted as `_stop_reason` on every L3 output so refusal_guard.is_refusal and any audit read the
            # provider's word rather than re-inferring a refusal from the output's shape.
            gen_stop = M.LAST_STOP_REASON.get(BENCH); gen_cap = bool(M.CAP_HIT.get(BENCH))
            current = _hypothesis_text(hyp.get("hypothesis", ""))
            versions = [current]
            log = {"world": m["world"], "rep": rep, "gen": hyp, "_stop_reason": gen_stop, "_cap_hit": gen_cap, "rounds": []}
            concede_round = None

            # ---- refusal: the model's own safety layer declined to generate (API stop_reason "refusal") ----
            # DISTINCT FROM ABSTENTION, and must never be scored as one: abstention is a SCIENTIFIC ACT (the
            # agent judged the evidence insufficient), whereas a refusal carries no scientific content at all.
            # Recorded and terminated here, before the debate. Without this the empty generation falls through
            # `evidence_sufficient is False` -> None and enters 3 rounds of review, and the harness fabricates a
            # debate around an empty hypothesis -- the exact harm the 2026-08-22 parse fix removed, re-entering
            # through a different door. Added 2026-09-03 (claude-fable-5 dual-use layer).
            # run_agent now records the provider stop reason (models._note_stop, 2026-09-04), so a refused
            # agent turn is a LABELLED outcome rather than an inference from an empty final. The empty-final
            # heuristic is retained ONLY as a claude-* fallback for turns predating that instrumentation:
            # glm-5.3's cf_gwas L3 `real` produced 65,942 output tokens over 10 calls and was still stamped
            # REFUSED by the old rule, while claude-fable-5's genuine refusals (verified by direct API replay:
            # stop_reason='refusal', 0 output tokens) also present as empty finals. Only the recorded stop
            # reason separates them; non-claude empty finals fall through to the parse-failed path.
            # Both branches also require the generation to have FAILED TO PARSE: a sticky content-filter on an
            # earlier tool turn followed by a parseable hypothesis is a hypothesis, and goes to the debate.
            if hyp.get("_parse_failed") and (
                    gen_stop == "refusal"
                    or (M.is_claude(BENCH) and not (hyp.get("_raw") or "").strip())):
                log.update({"refused": True, "versions": [], "concede_round": None, "_meta": M.get_meter()})
                out = m["agent_output"].replace(".json", f"_{suf}.json"); json.dump(log, open(out, "w"), indent=1)
                print(f"[{m['world']:<14} rep{rep}] REFUSED BY MODEL (no generation; not an abstention) -> {out}")
                shutil.rmtree(work, ignore_errors=True)
                continue

            # ---- abstention: the agent judged the evidence insufficient for a novel/valid hypothesis ----
            if hyp.get("evidence_sufficient") is False:
                log.update({"declared_insufficient": True, "versions": versions, "concede_round": None,
                            "_meta": M.get_meter()})
                out = m["agent_output"].replace(".json", f"_{suf}.json"); json.dump(log, open(out, "w"), indent=1)
                print(f"[{m['world']:<14} rep{rep}] DECLARED INSUFFICIENT EVIDENCE (no hypothesis) -> {out}")
                shutil.rmtree(work, ignore_errors=True)
                continue

            # ---- Stage B: 3 rounds of review ----
            for rnd in range(1, ROUNDS + 1):
                crits = {}
                for label, rmodel in REVIEWERS:
                    # GRACEFUL DEGRADATION: a reviewer model can be down (e.g. gemini 503 capacity). Don't let one
                    # flaky reviewer stall/kill the whole debate -- record the failure and proceed with the others
                    # (the _avg helper already ignores non-numeric scores, so 2/3 reviewers still yields an average).
                    try:
                        c, _ = turn(rmodel, REV_SYS, REV_USER.format(dossier=json.dumps(dossier), hyp=current, rnd=rnd),
                                    work, twas_in, dossier_in, use_sandbox=True)    # reviewers get the SAME sandbox + data/DBs -> can VERIFY the agent's evidence + catch fabrication
                        crits[label] = {**c, "_reviewer_model": rmodel}
                    except Exception as ex:
                        print(f"[warn] reviewer {label}/{rmodel} failed ({type(ex).__name__}: {str(ex)[:120]}) "
                              f"-> skipping this reviewer for world={m['world']} round={rnd}")
                        crits[label] = {"_reviewer_model": rmodel, "_error": f"{type(ex).__name__}: {str(ex)[:200]}",
                                        "recommend_reject": None, "validity": None, "novelty": None, "methods_soundness": None}
                if all("_error" in c for c in crits.values()):
                    print(f"[warn] ALL reviewers failed for world={m['world']} round={rnd} -- defense will see error stubs")
                dfd, _ = turn(BENCH, DEF_SYS, DEF_USER.format(hyp=current, critiques=json.dumps(crits, indent=1)),
                              work, twas_in, dossier_in)
                current = _hypothesis_text(dfd.get("revised_hypothesis"), current)
                versions.append(current)
                log["rounds"].append({"round": rnd, "critiques": crits, "defense": dfd})
                if dfd.get("concede") and concede_round is None:
                    concede_round = rnd
                _mv = lambda k: [c.get(k) for c in crits.values() if isinstance(c.get(k), (int, float))]
                _avg = lambda k: round(sum(_mv(k)) / len(_mv(k)), 2) if _mv(k) else None
                print(f"[{m['world']:<14} rep{rep}] round {rnd}: "
                      f"reject={sum(bool(c.get('recommend_reject')) or str(c.get('verdict', '')).lower() == 'reject' for c in crits.values())}/3 "
                      f"avg(valid/novel/methods)={_avg('validity')}/{_avg('novelty')}/{_avg('methods_soundness')} "
                      f"changed={dfd.get('changed')} concede={dfd.get('concede')}")
            log.update({"versions": versions, "concede_round": concede_round, "_meta": M.get_meter()})
            out = m["agent_output"].replace(".json", f"_{suf}.json")
            json.dump(log, open(out, "w"), indent=1)
            shutil.rmtree(work, ignore_errors=True)
            print(f"[{m['world']:<14} rep{rep}] saved -> {out}  (concede_round={concede_round})")
        except Exception as _e:
            import traceback as _tb
            try: shutil.rmtree(work, ignore_errors=True)
            except Exception: pass
            _side = m["agent_output"].replace(".json", f"_{suf}.harness_error.json")
            json.dump({"model": BENCH, "world": m["world"], "rep": rep, "error": f"{type(_e).__name__}: {_e}",
                       "traceback": _tb.format_exc()[-4000:], "meta": M.get_meter(),
                       "stop_reason": M.LAST_STOP_REASON.get(BENCH)}, open(_side, "w"), indent=1)
            print(f"[{m['world']:<14} rep{rep}] HARNESS-ERROR -> {_side}  (no out file written; re-run this world)")
