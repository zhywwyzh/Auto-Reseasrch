"""Shared refusal detection for graders and analyses (added 2026-09-03; provider-signal rewrite 2026-09-04).

A model-level API refusal (e.g. claude-fable-5's dual-use safety layer, Anthropic
stop_reason "refusal"; OpenAI-compatible finish_reason "content_filter") reaches a run
dir as an output JSON carrying {"_noncompliant": true}.

RULE (2026-09-04). Since models._note_stop() instrumentation, run_level.py and run_l3.py
persist the provider's own stop reason as `_stop_reason` in every output JSON. When that key is
present it is the ONLY evidence consulted: `_stop_reason == "refusal"` (normalised; covers
"content_filter") means refused, anything else means an ordinary non-compliance (the model
answered but its answer did not parse), which the graders score as NONCOMPLIANT / 0 and NOT as a
refusal. The distinction changes no score, but it changes the LABEL, and the label feeds coverage,
refusal-rate and difficulty analyses.

WHY the rewrite: the original rule inferred a refusal from the SHAPE of the output -- zero own
output tokens, or a worked loop ending in an EMPTY final_raw. That shape is verified for claude-*
refusals (direct API replay: stop_reason='refusal', 0 tokens) but it is NOT a refusal signature
for other providers. glm-5.3 on cf_gwas L3 produced 65,942 (`real`) and 73,884 (`cf_TGFB1`)
output tokens over 10 calls and then emitted an empty final; the old rule stamped both REFUSED,
and `real` re-ran to a full 3-round PASS under the instrumented harness. Two superseded
deepseek-v4-pro protein cells (62k output tokens, empty final) show the same non-refusal shape.

LEGACY FALLBACK. Outputs written before the instrumentation have no `_stop_reason`. For those,
the shape heuristic is retained ONLY for claude-* models, where it was verified at the API level
(all 73 claude-fable-5 refusals). A non-claude legacy output is never called a refusal by shape.

Under the roster protocol a refusal is a TERMINAL DATAPOINT: graders must state REFUSED and score
0 rather than let absent-field defaults hand the empty response vacuous credit, and nobody retries
or rewords the cell.

Frozen grades are unreachable through this helper: graded files are never re-run, and no
CANONICAL frozen cell is noncompliant with either legacy signature (re-verified 2026-09-04 over
all 1,924 output files: the 16 frozen-model matches are all superseded cells outside every
manifest). The 2026-09-04 rewrite was diffed against the previous rule over the same 1,924 files:
identical on every canonical cell, including all 73 claude-fable-5 refusals.
"""
import json


def is_refusal(out, out_path, model):
    """True iff this output JSON is a model-level refusal (vs an ordinary parse failure)."""
    if not (isinstance(out, dict) and out.get("_noncompliant")):
        return False
    if "_stop_reason" in out:                       # instrumented run: the provider's word is final
        return out.get("_stop_reason") == "refusal"
    if not str(model).startswith("claude"):         # legacy non-claude: shape is not a refusal signal
        return False
    own = ((out.get("_meta") or {}).get("by_model") or {}).get(model, {})
    if not own.get("out"):                          # legacy claude, instant refusal: zero own output
        return True
    try:                                            # legacy claude, work-then-refuse: empty final
        return json.load(open(out_path.replace(".json", ".trace.json"))).get("final_raw") == ""
    except Exception:
        return False
