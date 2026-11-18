"""Unified model layer for the benchmark harness (harness-v2).

One place that (a) routes model FAMILIES -- gpt-*/o* -> OpenAI, claude-* -> Anthropic; (b) runs the sealed
sandbox tool-loop identically for every level; (c) handles reps-friendly temperature. All runners/graders
call this instead of talking to a provider SDK directly, so adding a family or a repeat is a one-liner.

Env: OPENAI_API_KEY for gpt-*/o*; ANTHROPIC_API_KEY for claude-* (else claude calls raise a clear error).
"""
import os, json, re, shutil, subprocess, tempfile, time, random

_openai = None
_anthropic = None

# ---- transient-error RETRY (503/429/5xx/network) with exponential backoff + jitter ----------------------
# A single flaky call (Gemini 503 "high demand", a dropped connection) was killing whole model runs. Wrap
# every provider .create() in _retry so transient failures back off and retry instead of aborting the run.
_RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 520, 522, 524, 529}

def _is_transient(e):
    s = getattr(e, "status_code", None) or getattr(getattr(e, "response", None), "status_code", None)
    if s in _RETRY_STATUS:
        return True
    n = type(e).__name__.lower()
    return any(k in n for k in ("timeout", "connection", "internalserver", "ratelimit",
                                "serviceunavailable", "overloaded", "unavailable", "apierror"))

def _retry(make, tries=6, base=2.0, cap=45.0):
    """Call make(); on a TRANSIENT error, back off (base*2^i + jitter, capped) and retry up to `tries`."""
    for i in range(tries):
        try:
            return make()
        except Exception as e:
            if i == tries - 1 or not _is_transient(e):
                raise
            time.sleep(min(cap, base * (2 ** i)) + random.uniform(0, 1.0))

# ---- token + wall-time + call METER ---------------------------------------------------------------------
# Efficiency instrumentation: a caller brackets a task with reset_meter()/get_meter() and every chat()/
# run_agent() API call inside adds its usage. Per-model breakdown separates the BENCHMARKED agent's own
# cost (generation+defense) from shared infra (reviewers/judge). Returns None if no meter is active, so
# metering is fully opt-in and never changes any return signature.
_meter = None

def reset_meter():
    """Start (or restart) the active meter. Call once at the START of a task you want costed."""
    global _meter
    _meter = {"in": 0, "out": 0, "total": 0, "calls": 0, "by_model": {}, "_t0": time.perf_counter()}
    return _meter

def get_meter():
    """Snapshot the active meter with elapsed wall_s; None if reset_meter() was never called."""
    if _meter is None:
        return None
    m = {k: v for k, v in _meter.items() if k != "_t0"}
    m["wall_s"] = round(time.perf_counter() - _meter["_t0"], 3)
    return m

def _add_usage(u, model):
    """Fold one provider `usage` object into the active meter (OpenAI prompt/completion_tokens OR Responses/
    Anthropic input/output_tokens). No-op when no meter is active or usage is missing (e.g. CLI fallback)."""
    if _meter is None:
        return
    it = getattr(u, "input_tokens", None) or getattr(u, "prompt_tokens", None) or 0
    ot = getattr(u, "output_tokens", None) or getattr(u, "completion_tokens", None) or 0
    tt = getattr(u, "total_tokens", None) or (it + ot)
    _meter["in"] += it; _meter["out"] += ot; _meter["total"] += tt; _meter["calls"] += 1
    bm = _meter["by_model"].setdefault(model, {"in": 0, "out": 0, "calls": 0})
    bm["in"] += it; bm["out"] += ot; bm["calls"] += 1

def _claude_cli_bin():
    return shutil.which("claude")

def _claude_cli(system, user, model, timeout=240):
    """No-API-key fallback for CHAT roles (reviewer / judge / probe): one-shot, single-turn, tool-free
    generation via the Claude Code CLI (`claude -p`), authenticated by the user's existing Claude Code login.
    NOT usable for the benchmarked-agent role — that must run inside OUR sealed sandbox, which the CLI cannot.
    Runs in an empty temp cwd with --max-turns 1 so it stays a pure text response."""
    b = _claude_cli_bin()
    if not b:
        raise RuntimeError("claude-* requested with no ANTHROPIC_API_KEY and no `claude` CLI on PATH. "
                           "Set ANTHROPIC_API_KEY, or install + log in to the Claude Code CLI.")
    prompt = f"{system}\n\n{user}" if system else user
    with tempfile.TemporaryDirectory(prefix="claude_cli_") as d:
        cmd = [b, "-p", prompt, "--output-format", "json", "--model", model, "--max-turns", "1"]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=d, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"claude CLI failed (rc={r.returncode}): {(r.stderr or r.stdout)[-300:]}")
    out = (r.stdout or "").strip()
    try:                                                    # headless json: {"type":"result","result":"..."}
        j = json.loads(out)
        if isinstance(j, dict):
            return j.get("result") or j.get("text") or out
        if isinstance(j, list) and j:
            return j[-1].get("result") or j[-1].get("text") or out
    except Exception:
        pass
    return out

# Per-request timeout so a HUNG socket (server went quiet mid-request -> CLOSE-WAIT) fails fast and _retry can
# re-issue, instead of blocking on the SDK's 600s default x retries (~1h). connect fast; read generous enough for
# a slow reasoner turn (deepseek/glm reasoning can take a couple min) but far below the old default.
def _timeout():
    import httpx
    # read timeout scales with AGENT_MAX_TOKENS (2026-09-05): a reasoning model at ~33 tok/s needs ~4 min per
    # 8k tokens; 300 s was sized for the old 8192 ceiling and would turn a legitimate long think under the
    # raised ceiling into a timeout casualty. Hung-socket protection is preserved -- just at a ceiling-proportional
    # bound -- and _retry remains the single retry layer.
    # Factor 3.0 (was 1.25): glm-5.3's preflight heavy call at the 32768 ceiling took 2,501 s wall -- the first
    # attempt timed out at 1,500 s and _retry paid the whole reasoning cost AGAIN. A timeout that is too short is
    # therefore the more expensive failure (billed tokens, then a repeat). 3600 s at 32768: a hung socket now
    # costs up to an hour of wall time, a legitimate long think never becomes a timeout casualty.
    read_s = max(300.0, 300.0 * AGENT_MAX_TOKENS / 8192 * 3.0)
    return httpx.Timeout(connect=15.0, read=read_s, write=30.0, pool=15.0)

def _oa():
    global _openai
    if _openai is None:
        from openai import OpenAI
        _openai = OpenAI(timeout=_timeout(), max_retries=0)   # _retry() is the single authoritative retry layer
    return _openai

# OpenAI-COMPATIBLE providers: family prefix -> (base_url, api_key_env). These expose an OpenAI-style API, so
# the same OpenAI SDK client (with a base_url) routes them. Add a family = one line here + set its key.
OPENAI_COMPAT = {
    "gemini":   ("https://generativelanguage.googleapis.com/v1beta/openai/", "GEMINI_API_KEY"),
    "deepseek": ("https://api.deepseek.com",                                 "DEEPSEEK_API_KEY"),
    "glm":      ("https://open.bigmodel.cn/api/paas/v4",                     "ZHIPU_API_KEY"),
    "kimi":     ("https://api.moonshot.ai/v1",                               "MOONSHOT_API_KEY"),
    "grok":     ("https://api.x.ai/v1",                                      "XAI_API_KEY"),
    "qwen":     ("https://dashscope.aliyuncs.com/compatible-mode/v1",        "DASHSCOPE_API_KEY"),
}
_compat_clients = {}

def _family(m):
    for fam in OPENAI_COMPAT:
        if m.startswith(fam):
            return fam
    return "anthropic" if m.startswith("claude") else "openai"   # gpt-*/o*/default -> openai

def _oa_client(model):
    """OpenAI-SDK client for `model`: the default OpenAI endpoint for gpt-*/o*, else an OpenAI-COMPATIBLE
    endpoint (base_url + provider key) for gemini/deepseek/glm/kimi/grok/qwen."""
    fam = _family(model)
    if fam in OPENAI_COMPAT:
        if fam not in _compat_clients:
            from openai import OpenAI
            base, keyenv = OPENAI_COMPAT[fam]
            _compat_clients[fam] = OpenAI(base_url=base, api_key=os.environ.get(keyenv) or "MISSING",
                                          timeout=_timeout(), max_retries=0)   # fail hung sockets fast; _retry owns retries
        return _compat_clients[fam]
    return _oa()

def _an():
    global _anthropic
    if _anthropic is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("claude-* requested but ANTHROPIC_API_KEY is not set. "
                               "Add it to ~/.openai_env (or the env) to enable cross-family models/reviewers.")
        import anthropic
        _anthropic = anthropic.Anthropic()
    return _anthropic

def is_claude(m):   return m.startswith("claude")
def _no_temp(m):    # reasoning models reject/ignore temperature (send none -> provider default)
    return (m.startswith(("gpt-5", "gpt-6", "o1", "o3", "o4", "kimi")) or "reasoner" in m
            or "thinking" in m or m.endswith("-r1"))

def _key_present(model):
    if is_claude(model):
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    fam = _family(model)
    return bool(os.environ.get(OPENAI_COMPAT[fam][1])) if fam in OPENAI_COMPAT else bool(os.environ.get("OPENAI_API_KEY"))

def available(model):
    """Usable in a CHAT role (reviewer/judge/probe)? claude-* also works via the Claude CLI without a key."""
    if is_claude(model):
        return bool(os.environ.get("ANTHROPIC_API_KEY")) or bool(_claude_cli_bin())
    return _key_present(model)

def available_for_agent(model):
    """Usable as the BENCHMARKED agent (sandbox tool-loop)? Needs the family's API key (no CLI fallback)."""
    return _key_present(model)


LAST_STOP_REASON = {}   # model -> stop_reason of its most recent chat() call ("refusal" when a safety
                        # layer declined). Set alongside the return value so callers that must distinguish
                        # "the model declined" from "the model answered X" (prior probes: a refusal is NOT
                        # evidence about the model's prior) can consult it WITHOUT changing chat()'s
                        # return contract. Added 2026-09-03 after claude-fable-5 refusals were silently
                        # scored knew_prior=False from a truncated fragment.


CAP_HIT = {}            # model -> True if any agent turn of the current run_agent call ended with finish/stop 'length'

def _note_stop(model, stop):
    """Record a provider stop/finish reason from an AGENT turn (run_agent), sticky on refusal.

    Added 2026-09-04. run_agent previously recorded nothing, so a refused agent turn was
    indistinguishable from an empty final — the failure mode that made glm-5.3's 65,942-token
    cf_gwas L3 turn look like a refusal while claude-fable-5's genuine 0-token refusals looked the
    same. 'refusal' (Anthropic) and 'content_filter' (OpenAI-compatible) both mean the safety layer
    declined; sticky because the harness retries a refused turn and a later benign finish_reason
    would otherwise erase the evidence.
    """
    if stop == "length":
        CAP_HIT[model] = True          # persisted as `_cap_hit` on outputs; completeness_report.py lists these cells
    if stop in ("refusal", "content_filter"):
        LAST_STOP_REASON[model] = "refusal"
    elif LAST_STOP_REASON.get(model) != "refusal":
        # Record the LATEST non-refusal reason (2026-09-05; previously the FIRST, which made every persisted
        # `_stop_reason` read "tool_calls" and hid that glm-5.3's force-final turns were ending in "length" --
        # the reasoning budget exhausting the shared max_tokens before any visible answer was emitted).
        LAST_STOP_REASON[model] = stop


# PROVIDER PARAMETER DIALECT (2026-09-07). Newer OpenAI models reject parameters older ones require:
# gpt-6-astra refuses `temperature` (only the default 1) and requires `max_completion_tokens` instead of
# `max_tokens`. Rather than hardcode a model list that must be edited for every future release, learn the
# dialect from the provider's own 400 and remember it per model, so a NEW MODEL NEEDS ONLY ITS NAME.
# Existing models never trigger this: the adaptation fires only on the specific BadRequestError text.
_DIALECT = {}            # model -> {"max_completion_tokens": bool, "no_temperature": bool}


def _responses_stop(r):
    """Map an OpenAI Responses object onto the stop vocabulary _note_stop() understands.

    Added 2026-09-07: this branch (OpenAI reasoning models via /v1/responses) recorded NOTHING, so
    LAST_STOP_REASON stayed None and refusal detection was blind for every gpt-5.x/gpt-6 agent turn --
    the same failure class that mis-stamped glm-5.3 as refusing. Responses signals a decline either as an
    output item of type "refusal" or as incomplete_details.reason == "content_filter"; a truncated turn
    reports "max_output_tokens", which is this API's spelling of finish_reason "length"."""
    try:
        for o in (getattr(r, "output", None) or []):
            if getattr(o, "type", None) == "refusal":
                return "refusal"
            for c in (getattr(o, "content", None) or []):
                if getattr(c, "type", None) == "refusal":
                    return "refusal"
        det = getattr(r, "incomplete_details", None)
        reason = getattr(det, "reason", None) if det else None
        if reason == "content_filter":
            return "refusal"
        if reason == "max_output_tokens":
            return "length"
        return getattr(r, "status", None) or "stop"
    except Exception:
        return None


def _oa_call(_m, _fn, **kw):
    """Call an OpenAI-SDK create() with `kw`, adapting parameter names to what THIS model accepts.

    Parameters are underscore-named because `kw` itself carries `model=` for the API."""
    model, fn = _m, _fn
    d = _DIALECT.setdefault(model, {})
    if d.get("max_completion_tokens") and "max_tokens" in kw:
        kw["max_completion_tokens"] = kw.pop("max_tokens")
    if d.get("no_temperature"):
        kw.pop("temperature", None)
    for _ in range(3):                       # at most one adaptation per constraint, then give up
        try:
            return fn(**kw)
        except Exception as e:
            msg = str(e)
            if "max_completion_tokens" in msg and "max_tokens" in kw:
                d["max_completion_tokens"] = True
                kw["max_completion_tokens"] = kw.pop("max_tokens")
                print(f"[models] {model}: provider requires max_completion_tokens; adapted for this run")
                continue
            if "temperature" in msg and "temperature" in kw:
                d["no_temperature"] = True
                kw.pop("temperature")
                print(f"[models] {model}: provider rejects an explicit temperature; adapted for this run")
                continue
            raise
    return fn(**kw)


def chat(model, system, user, temperature=0, max_tokens=4096):   # 4096 so verbose reviewer/judge JSON can't truncate (same bug class as agents)
    """Single-shot chat, family-routed. Returns the text. (reviewers, judges, probes)
    claude-* -> Anthropic SDK (or Claude CLI fallback); gpt-*/o* -> OpenAI; gemini/deepseek/glm/kimi/... ->
    their OpenAI-compatible endpoint.
    Side effect: records the provider stop_reason in LAST_STOP_REASON[model]."""
    LAST_STOP_REASON.pop(model, None)
    if is_claude(model):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return _claude_cli(system, user, model)          # no-key fallback (chat roles only)
        kw = dict(model=model, max_tokens=max_tokens, system=system,
                  messages=[{"role": "user", "content": user}])
        if temperature: kw["temperature"] = temperature
        r = _retry(lambda: _an().messages.create(**kw)); _add_usage(r.usage, model)
        LAST_STOP_REASON[model] = getattr(r, "stop_reason", None)
        # opus-class models emit ThinkingBlock(s) before the answer -> select TEXT blocks, never content[0]
        return "".join(getattr(b, "text", "") for b in r.content if getattr(b, "type", None) == "text")
    kw = dict(model=model, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    if not _no_temp(model): kw["temperature"] = temperature
    r = _retry(lambda: _oa_call(model, _oa_client(model).chat.completions.create, **kw)); _add_usage(getattr(r, "usage", None), model)
    LAST_STOP_REASON[model] = getattr(r.choices[0], "finish_reason", None)
    return r.choices[0].message.content or ""


# FAIRNESS: one output-token ceiling for EVERY benchmarked agent, applied identically across families
# (Anthropic / OpenAI-Responses / OpenAI-compat-chat). Anthropic REQUIRES max_tokens; the OpenAI branches
# previously set none (provider default = effectively unbounded) -> claude was uniquely truncated at 2000.
# 8192 is generous headroom (claude finals ran ~4k chars; see PAPER_NOTES §1). NOTE: on reasoning models the
# Responses/compat budget INCLUDES hidden reasoning tokens, so if post-run metering shows any model nearing
# this ceiling, raise THIS ONE constant (keeps every model on the same budget). max_tokens is a ceiling, not
# a charge — you pay only for tokens generated, so generous headroom is ~free.
#
# RAISED 8192 -> 32768 on 2026-09-05 (glm-5.3 roster). Evidence the 8192 ceiling BOUND for the first time:
# a direct API probe returned finish_reason='length', content_len=0, reasoning_tokens=8189/8192 — the model
# spent the whole budget on hidden reasoning and emitted nothing visible; six roster cells (clinvar L1 6,
# classify 6/12/15, scrna composition 2, cf_gwas L3 `real`) failed exactly this way after 28k–162k output
# tokens. Counterfactually neutral for every FROZEN result: no frozen model's cell-mean output per call
# exceeds 3,540 (p90 <= 1,762), so none was ever near 8192. preflight_model.py's `reasoning-cap` check
# is the standing guard: it FAILS whenever a new model exhausts this ceiling on hidden reasoning.
# COUPLED to _timeout(): a 32k think at ~33 tok/s is ~16 min, so the client read timeout scales with it.
AGENT_MAX_TOKENS = 32768

# A force-final reply is USABLE only if a JSON object can be recovered from it. The old test was
# `final.strip()` (non-empty), which accepted two failure modes seen in the crispr L2 runs:
#   - deepseek emits its native <｜｜DSML｜｜tool_calls> markup as TEXT (force-final sends no `tools`,
#     so a model still mid-analysis has no tool channel and inlines the call) -> non-empty, no answer;
#   - glm returns pure narration ("I need to write the final CSV now.", repeated) -> non-empty, no answer.
# Both broke out of the retry loop on attempt 1 and were written as _noncompliant, discarding a run that
# in deepseek's case already held a complete analysis. Retrying on UNPARSEABLE (not merely empty) costs
# the model no analysis budget -- the sandbox loop is already over -- so it does not change difficulty.
# NOTE: a brace-presence test is NOT enough -- a leaked DSML tool call carries python code whose dict
# literals contain braces, so it would false-positive. Mirror run_level.parse and require an actual parse.
def _has_json_object(txt):
    if not txt or not txt.strip():
        return False
    t = re.sub(r"</?｜｜DSML｜｜[^>]*>", "", txt)          # same token strip as run_level.parse
    t = re.sub(r"```[a-zA-Z]*", "", t.strip())
    try:
        t = t[t.index("{"):t.rindex("}") + 1]
    except ValueError:
        return False
    for kw in ({}, {"strict": False}):
        try:
            return isinstance(json.loads(t, **kw), dict)
        except Exception:
            pass
    try:                                                  # python-dict literal (True/False/None) fallback
        import ast
        return isinstance(ast.literal_eval(t), dict)
    except Exception:
        return False

def run_agent(model, system, user, tool_name, tool_desc, exec_fn, max_steps=14,
              temperature=0, force_final="Analysis budget reached. Return ONLY the final JSON now.",
              trunc=3500):
    """Run a tool-using agent loop, family-routed, with ONE Python tool wired to `exec_fn`.

    exec_fn(code_str) -> (stdout_str, ok_bool). The caller supplies the SEALED sandbox as exec_fn, so this
    loop is identical for every level and both families. Notebook-safe: a failed cell is NOT kept in the
    accumulated context (one bad cell can't poison later cells). Returns (final_text, code_trace).
    """
    LAST_STOP_REASON.pop(model, None)      # per-turn; _note_stop() re-sets it, sticky on refusal
    CAP_HIT.pop(model, None)
    cells, trace, final = [], [], None
    if is_claude(model):
        tools = [{"name": tool_name, "description": tool_desc,
                  "input_schema": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}]
        msgs = [{"role": "user", "content": user}]
        for _ in range(max_steps):
            kw = dict(model=model, max_tokens=AGENT_MAX_TOKENS, system=system, tools=tools, messages=msgs)
            if temperature: kw["temperature"] = temperature
            def _claude_stream_call():
                # Anthropic requires streaming for long/high-token requests.
                # get_final_message() returns the same Message object shape
                # consumed by the existing unified tool-loop below.
                with _an().messages.stream(**kw) as stream:
                    return stream.get_final_message()
            r = _retry(_claude_stream_call); _add_usage(r.usage, model)
            _note_stop(model, getattr(r, "stop_reason", None))
            tus = [b for b in r.content if getattr(b, "type", None) == "tool_use"]
            if not tus:
                final = "".join(getattr(b, "text", "") for b in r.content); break
            # Anthropic response models may contain SDK-only fields
            # (e.g. parsed_output) that are illegal in a subsequent
            # Messages API request. Reconstruct only API-valid request blocks.
            replay_content = []
            for b in r.content:
                bt = getattr(b, "type", None)

                if bt == "text":
                    replay_content.append({
                        "type": "text",
                        "text": getattr(b, "text", "") or "",
                    })

                elif bt == "tool_use":
                    replay_content.append({
                        "type": "tool_use",
                        "id": getattr(b, "id"),
                        "name": getattr(b, "name"),
                        "input": getattr(b, "input") or {},
                    })

                elif bt == "thinking":
                    replay_content.append({
                        "type": "thinking",
                        "thinking": getattr(b, "thinking", "") or "",
                        "signature": getattr(b, "signature", "") or "",
                    })

                elif bt == "redacted_thinking":
                    replay_content.append({
                        "type": "redacted_thinking",
                        "data": getattr(b, "data", "") or "",
                    })

                else:
                    raise RuntimeError(
                        f"Unsupported Anthropic response block for replay: {bt!r}"
                    )

            msgs.append({
                "role": "assistant",
                "content": replay_content,
            })
            results = []
            for tu in tus:
                code = (tu.input or {}).get("code", "")
                so, ok = exec_fn("\n".join(cells + [code]))
                if ok: cells.append(code)
                trace.append({"code": code, "stdout": so})
                results.append({"type": "tool_result", "tool_use_id": tu.id, "content": so[-trunc:]})
            msgs.append({"role": "user", "content": results})
        if final is None:
            msgs.append({"role": "user", "content": force_final})
            final = ""
            for _ in range(3):                          # same parseability retry as the compat branch
                def _claude_force_final_stream_call():
                    with _an().messages.stream(
                        model=model,
                        max_tokens=AGENT_MAX_TOKENS,
                        system=system,
                        messages=msgs,
                    ) as stream:
                        return stream.get_final_message()

                r = _retry(_claude_force_final_stream_call)
                _add_usage(r.usage, model)
                _note_stop(model, getattr(r, "stop_reason", None))
                got = "".join(getattr(b, "text", "") for b in r.content)
                if _has_json_object(got):
                    final = got; break
                final = final or got
                msgs.append({"role": "assistant", "content": "(thinking)"})
                msgs.append({"role": "user", "content": "That reply contained no JSON object. The analysis budget "
                             "is closed and no further code will run — output ONLY the final JSON object now, "
                             "built from the results you already have."})
        return final, trace

    # OpenAI REASONING models (gpt-5.x / o-series): function tools require the /v1/responses API (Chat
    # Completions rejects tools + reasoning_effort). Use Responses so reasoning stays ON (fair benchmark).
    if _family(model) == "openai" and _no_temp(model):
        oac = _oa_client(model)
        def _rtext(r):
            t = getattr(r, "output_text", None)
            return t if t else "".join(getattr(c, "text", "") for o in r.output
                                       for c in (getattr(o, "content", None) or []) if getattr(c, "type", None) == "output_text")
        rtools = [{"type": "function", "name": tool_name, "description": tool_desc,
                   "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}]
        prev_id, pending = None, [{"role": "user", "content": user}]
        for _ in range(max_steps):
            kw = dict(model=model, instructions=system, tools=rtools, input=pending,
                      max_output_tokens=AGENT_MAX_TOKENS)   # same ceiling as every family (incl. reasoning tokens)
            if prev_id: kw["previous_response_id"] = prev_id
            r = _retry(lambda: oac.responses.create(**kw)); _add_usage(getattr(r, "usage", None), model)
            _note_stop(model, _responses_stop(r))
            prev_id = r.id
            fcs = [o for o in r.output if getattr(o, "type", None) == "function_call"]
            if not fcs:
                final = _rtext(r); break
            pending = []
            for fc in fcs:
                try:                                  # a model can emit a JSON LIST (or truncated JSON) as
                    _a = json.loads(fc.arguments or "{}")   # tool arguments -- never let that kill the level
                    code = _a.get("code", "") if isinstance(_a, dict) else ""
                except json.JSONDecodeError:
                    code = ""
                if not code:
                    so = "[tool call arguments were truncated/invalid JSON — resend a shorter call, or return the final JSON]"
                    trace.append({"code": "(truncated)", "stdout": so})
                    pending.append({"type": "function_call_output", "call_id": fc.call_id, "output": so})
                    continue
                so, ok = exec_fn("\n".join(cells + [code]))
                if ok: cells.append(code)
                trace.append({"code": code, "stdout": so})
                pending.append({"type": "function_call_output", "call_id": fc.call_id, "output": so[-trunc:]})
        if final is None:
            # BUGFIX: the loop hit max_steps on a turn that made function_calls, so prev_id OWES those outputs.
            # Send the pending function_call_outputs BEFORE the force-final message, else the Responses API 400s
            # "No tool output found for function call ..." (this killed gpt-5.6-sol's TWAS).
            _inp = pending + [{"role": "user", "content": force_final}]
            final = ""
            for _ in range(3):                          # same parseability retry as the compat branch
                r = _retry(lambda: oac.responses.create(model=model, instructions=system, previous_response_id=prev_id,
                                         input=_inp, max_output_tokens=AGENT_MAX_TOKENS))
                _add_usage(getattr(r, "usage", None), model)
                _note_stop(model, _responses_stop(r))
                got = _rtext(r)
                if _has_json_object(got):
                    final = got; break
                final = final or got
                prev_id = r.id                          # chain off the reply; pending outputs are already settled
                _inp = [{"role": "user", "content": "That reply contained no JSON object. The analysis budget is "
                         "closed and no further code will run — output ONLY the final JSON object now, built from "
                         "the results you already have."}]
        return final, trace

    # OpenAI family + OpenAI-COMPATIBLE families (gemini/deepseek/glm/kimi/...): same tool-loop.
    # NOTE: function-calling support varies across compatible endpoints — verify a compat model can drive
    # the tool-loop before benchmarking it as an AGENT (all are fine as chat-only reviewers/judges).
    oac = _oa_client(model)
    tools = [{"type": "function", "function": {"name": tool_name, "description": tool_desc,
              "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}}]
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    for _ in range(max_steps):
        kw = dict(model=model, messages=msgs, tools=tools, tool_choice="auto", max_tokens=AGENT_MAX_TOKENS)
        if not _no_temp(model): kw["temperature"] = temperature
        _r = _retry(lambda: _oa_call(model, oac.chat.completions.create, **kw)); _add_usage(getattr(_r, "usage", None), model)
        _note_stop(model, getattr(_r.choices[0], "finish_reason", None))
        msg = _r.choices[0].message
        if not msg.tool_calls:
            if msg.content and msg.content.strip():
                final = msg.content; break
            # reasoning compat model (e.g. kimi-k3) returned NO tool-call AND empty content (answer went to
            # reasoning_content / budget spent) -> nudge for the JSON and keep looping. Use a NON-EMPTY assistant
            # placeholder (some compat APIs reject an empty assistant message) to keep the turn structure valid.
            msgs.append({"role": "assistant", "content": "(thinking)"})
            msgs.append({"role": "user", "content": "Output ONLY the final JSON object now, nothing else."})
            continue
        msgs.append({"role": "assistant", "content": msg.content,
                     "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})
        for tc in msg.tool_calls:
            try:                                        # a reasoning model can TRUNCATE its tool-call args (hit the
                _args = json.loads(tc.function.arguments or "{}")                  # token cap mid-JSON) -> don't crash
                if not isinstance(_args, dict):         # glm-5.3 (2026-09-04) can emit a JSON LIST as the arguments
                    raise json.JSONDecodeError("tool arguments are not a JSON object", str(_args)[:80], 0)
                code = _args.get("code", "")
            except json.JSONDecodeError:
                # Malformed arguments (truncated, or not an object) used to raise AttributeError out of
                # run_agent and kill the WHOLE run_level process, losing every remaining cell of the level
                # (scrna L1 and L2_annotation for glm-5.3). Treat it like truncation: tell the model, continue.
                so = "[tool call arguments were truncated/invalid JSON — resend a shorter run_python call, or return the final JSON]"
                trace.append({"code": "(truncated)", "stdout": so})
                msgs.append({"role": "tool", "tool_call_id": tc.id, "content": so}); continue
            so, ok = exec_fn("\n".join(cells + [code]))
            if ok: cells.append(code)
            trace.append({"code": code, "stdout": so})
            msgs.append({"role": "tool", "tool_call_id": tc.id, "content": so[-trunc:]})
    if final is None:
        # force-final. A reasoning compat model (kimi-k3) can return EMPTY `content` here after a tool-heavy
        # loop (answer lands in reasoning_content / token budget spent); deepseek can inline its DSML
        # tool-call markup as text; glm can return pure narration. Retry up to 3x with a harder nudge until
        # a JSON object is actually recoverable (see _has_json_object). temp default makes retries
        # stochastic; same token cap each call (fair benchmark).
        msgs.append({"role": "user", "content": force_final})
        final = ""
        for _ in range(3):
            kw = dict(model=model, messages=msgs, max_tokens=AGENT_MAX_TOKENS)
            if not _no_temp(model): kw["temperature"] = temperature
            _r = _retry(lambda: _oa_call(model, oac.chat.completions.create, **kw)); _add_usage(getattr(_r, "usage", None), model)
            _note_stop(model, getattr(_r.choices[0], "finish_reason", None))
            got = _r.choices[0].message.content or ""
            if _has_json_object(got):
                final = got; break
            final = final or got                       # keep the first reply for the trace if all attempts fail
            why = ("Your reply was empty." if not got.strip() else
                   "Your reply contained no JSON object — do NOT call tools and do NOT narrate next steps; "
                   "the analysis budget is closed and no further code will run.")
            msgs.append({"role": "assistant", "content": "(thinking)"})   # non-empty; avoid empty/consecutive-user
            msgs.append({"role": "user", "content": why + " Output ONLY the final JSON object now, "
                                                         "built from the results you already have."})
    return final, trace
