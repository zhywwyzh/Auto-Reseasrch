"""Salvage truncated-but-present claude finals into gradeable outputs — WITHOUT re-running.

For each n=1 cell whose output is `_noncompliant` (the old max_tokens=2000 truncation), read the trace's
`final_raw`, REPAIR the truncated JSON (trim to the last complete field + close open brackets), and write the
repaired object as the output json so the existing graders can read it. Cells that are already compliant
(freshly re-run) are skipped; cells with an empty final (unrepairable) are left for re-run.

Repaired outputs are flagged `_salvaged: true` + `_answer_truncated: true` (claude was cut off mid-answer, so
it is mildly UNDER-credited on the last field) and keep their existing `_meta`.

usage:  python salvage_claude.py <run_dir> [model=claude-opus-5] [--apply]
"""
import json, os, sys

RUN = sys.argv[1]
MODEL = next((a for a in sys.argv[2:] if not a.startswith("--")), "claude-opus-5")
APPLY = "--apply" in sys.argv

def _closers(s):
    st = []; ins = esc = False
    for ch in s:
        if ins:
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == '"': ins = False
        else:
            if ch == '"': ins = True
            elif ch == '{': st.append('}')
            elif ch == '[': st.append(']')
            elif ch in '}]' and st: st.pop()
    return ('"' if ins else '') + ''.join(reversed(st))

def repair(raw):
    if not raw or '{' not in raw: return None
    s = raw[raw.index('{'):]
    for end in range(len(s), 0, -1):
        if end < len(s) and s[end - 1] not in ',}]"': continue
        cc = s[:end].rstrip().rstrip(',')
        try: return json.loads(cc + _closers(cc))
        except: continue
    return None

man = json.load(open(f"{RUN}/manifest.json"))          # n=1 selection
salv = skip_ok = empty = 0
for m in man:
    out = m["agent_output"].replace(".json", f"_{MODEL}.json")
    tr = out.replace(".json", ".trace.json")
    if not os.path.exists(out): continue
    d = json.load(open(out))
    if not d.get("_noncompliant"):                     # already compliant (fresh re-run) -> leave it
        skip_ok += 1; continue
    fr = json.load(open(tr)).get("final_raw") or "" if os.path.exists(tr) else ""
    rep = repair(fr)
    if rep is None:
        empty += 1; print(f"  [re-run needed] {os.path.basename(out)} (empty/unrepairable)"); continue
    rep["_meta"] = d.get("_meta")                      # keep the backfilled efficiency meta
    rep["_salvaged"] = True; rep["_answer_truncated"] = True
    salv += 1
    if APPLY: json.dump(rep, open(out, "w"), indent=1)
    print(f"  [salvage] {os.path.basename(out):<44} recovered {len(rep)-3} answer keys")

print(f"\n{RUN}: salvaged {salv} | already-compliant {skip_ok} | need re-run {empty}"
      + ("" if APPLY else "   (DRY-RUN — add --apply to write)"))
