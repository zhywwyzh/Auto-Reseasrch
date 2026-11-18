"""Backfill an efficiency `_meta` into claude-opus-5's ALREADY-RUN outputs (no re-run) so the reused n=1 cells
carry token/time/call data like a freshly-metered run would.

RECOVERED = REAL:
  * calls   = n_code_cells + 1 (final) -- exact from the trace.
  * wall_s  = gap between consecutive trace-file mtimes (the run was serial); the first world in each level uses
              that level's start timestamp from the driver log.
ESTIMATED  (no token record ever existed; tiktoken absent -> chars/4 proxy):
  * tokens  = replay the accumulating message context the tool-loop actually sent (system + user + prior
              tool_use code + prior tool_result stdout TRUNCATED to 3500 chars, exactly as run_agent sent it).
              Assistant prose alongside tool_use was not stored -> OUTPUT is a slight underestimate.
CALIBRATION: the recovered worlds are EXACTLY what the real $50 Anthropic bill covered, so we compare the
proxy's implied cost to $50 and report the factor (and store calibrated tokens) -> billing-consistent estimate.

usage:  python recover_meta.py [--apply]   (default dry-run; --apply writes `_meta` into the output jsons)
"""
import json, os, sys, glob, datetime as dt

GEN_SYS = "You are a careful computational biologist. Do the task with the sandbox and return ONLY the requested JSON."
TRUNC = 3500                       # run_agent truncates each tool_result stdout to the last 3500 chars
MODEL = "claude-opus-5"
PRICE_IN, PRICE_OUT = 5.0, 25.0    # $/M tokens, opus-class (for the $50 reconciliation only)
REAL_BILL = 50.0                   # user-reported Anthropic spend for the recovered worlds
APPLY = "--apply" in sys.argv
# level run_dir -> driver-log start "HH:MM:SS" (UTC); only levels claude actually ran
LEVELS = {"results/gwas_qc_run": "05:30:50", "results/gwas_signaleda_run": "06:35:00",
          "results/gwas_task2_run": "07:34:39"}

def toks(s): return max(1, round(len(s or "") / 4))     # transparent chars/4 proxy (no tiktoken)

def hms_epoch(ref_epoch, hms):                          # "HH:MM:SS" on the same UTC day as ref_epoch -> epoch
    d = dt.datetime.fromtimestamp(ref_epoch, dt.timezone.utc).date()
    h, m, s = map(int, hms.split(":"))
    return dt.datetime(d.year, d.month, d.day, h, m, s, tzinfo=dt.timezone.utc).timestamp()

def est_tokens(tr):
    """Reconstruct (in,out) tokens for one world by replaying the accumulating context run_agent sent."""
    sys_t, usr_t = toks(GEN_SYS), toks(tr.get("prompt", ""))
    ctx = 0; tin = tout = 0
    for c in tr.get("code_trace", []):
        tin += sys_t + usr_t + ctx                      # this step's input = system + user + accumulated history
        tout += toks(c.get("code", "")) + 15            # assistant tool_use(code) [+overhead]; prose not stored
        ctx += toks(c.get("code", "")) + toks((c.get("stdout", "") or "")[-TRUNC:])   # cell joins context
    tin += sys_t + usr_t + ctx                          # final call
    tout += toks(tr.get("final_raw", "") or "")
    return tin, tout

rows, SUM_IN, SUM_OUT = [], 0, 0
for rd, start in LEVELS.items():
    traces = sorted(glob.glob(f"{rd}/out_cell*_{MODEL}.trace.json"),
                    key=lambda p: int(p.split("out_cell")[1][:3]))
    prev_m = None
    for i, tp in enumerate(traces):
        tr = json.load(open(tp)); mt = os.path.getmtime(tp)
        base = hms_epoch(mt, start) if i == 0 else prev_m
        wall = round(max(0.0, mt - base), 1); prev_m = mt
        tin, tout = est_tokens(tr); calls = len(tr.get("code_trace", [])) + 1
        SUM_IN += tin; SUM_OUT += tout
        rows.append((rd, tp, tr.get("world_label", "?"), calls, wall, tin, tout))

raw_cost = PRICE_IN * SUM_IN / 1e6 + PRICE_OUT * SUM_OUT / 1e6
factor = REAL_BILL / raw_cost if raw_cost else 1.0      # scale proxy tokens to reconcile with the real bill

print(f"=== recovered {len(rows)} claude worlds (L1+EDA+partial Locus = what the ${REAL_BILL:.0f} bill covered) ===")
by_lvl = {}
for rd, tp, wl, calls, wall, tin, tout in rows:
    by_lvl.setdefault(rd, [0, 0, 0.0, 0, 0])
    a = by_lvl[rd]; a[0] += 1; a[1] += calls; a[2] += wall; a[3] += tin; a[4] += tout
for rd, (n, c, w, ti, to) in by_lvl.items():
    print(f"  {rd:<28} worlds={n:<3} calls={c:<4} wall={w/60:5.1f}min  est_tok={ti+to:>8,} "
          f"(cal {(ti+to)*factor:>8,.0f})")
print(f"\n  proxy total tokens: in={SUM_IN:,} out={SUM_OUT:,} -> implied ${raw_cost:.2f} at ${PRICE_IN}/${PRICE_OUT}/M")
print(f"  reconciles to real ${REAL_BILL:.0f} with calibration factor = {factor:.2f}  "
      f"(<1 = proxy over-counts, >1 = under-counts)")

if APPLY:
    for rd, tp, wl, calls, wall, tin, tout in rows:
        out = tp.replace(".trace.json", ".json")
        if not os.path.exists(out):
            print(f"  [skip] no output json for {tp}"); continue
        d = json.load(open(out))
        if isinstance(d, dict):
            d["_meta"] = {"in": tin, "out": tout, "total": tin + tout, "calls": calls, "wall_s": wall,
                          "by_model": {MODEL: {"in": tin, "out": tout, "calls": calls}},
                          "in_cal": round(tin * factor), "out_cal": round(tout * factor),
                          "total_cal": round((tin + tout) * factor),
                          "source": "recovered", "tokens": "estimated", "token_proxy": "chars/4",
                          "calibration_factor": round(factor, 3), "wall_s_source": "trace-mtime"}
            json.dump(d, open(out, "w"), indent=1)
    print(f"\nAPPLIED: wrote `_meta` (real calls+wall_s, estimated+calibrated tokens) into {len(rows)} output jsons.")
else:
    print("\nDRY-RUN: re-run with --apply to write `_meta` into the output jsons.")
