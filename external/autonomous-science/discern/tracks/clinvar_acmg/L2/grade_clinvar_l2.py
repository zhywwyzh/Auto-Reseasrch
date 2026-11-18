"""clinvar_acmg L2 — C grader (0-3 per world, aligned with L1 grade_generic + GWAS L2) vs the golden truth in each world's manifest.
Handles all 3 sub-tasks (dispatched by manifest 'sub_task'):
  classify           : focal/confound target reached the correct 3-bin class (robust to the confound)
  prioritize         : top pick == the true causal (planted distractor demoted)
  secondary_findings : reported set == the reportable P/LP-in-SF set (precision AND recall)

usage: grade_clinvar_l2.py <run_dir> <model_suffix>
"""
import sys, os, json, re

RUN, SUF = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from refusal_guard import is_refusal
MAN = json.load(open(f"{RUN}/manifest.json"))


def load_out(cell):
    p = f"{RUN}/out_cell{cell:03d}_{SUF}.json"
    if not os.path.exists(p):
        p = f"{RUN}/out_cell{cell:03d}.json"
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p))
    except Exception:
        return None


def vkey(v):                          # normalize "chr19:11113359 T>C" / "19:11113359T>C" -> (19,11113359,T,C)
    m = re.search(r"(\w+?):(\d+)\s*([ACGT]+)\s*>\s*([ACGT]+)", str(v).replace("chr", ""))
    return (m.group(1), int(m.group(2)), m.group(3), m.group(4)) if m else str(v)


BIN = {"pathogenic": "path", "p": "path", "lp": "path", "likely_pathogenic": "path", "path": "path",
       "benign": "benign", "b": "benign", "lb": "benign", "likely_benign": "benign",
       "vus": "vus", "uncertain": "vus", "uncertain_significance": "vus"}


def to_bin(c):
    c = str(c).strip().lower().replace(" ", "_")
    for k, v in BIN.items():
        if k in c:
            return v
    return None


# 0-3 scale (aligned with L1 grade_generic + GWAS L2). Adjacent-bin tolerance for classify.
RANK = {"path": 2, "vus": 1, "benign": 0}
def adjacent(a, b):
    return a is not None and b is not None and abs(RANK.get(a, -9) - RANK.get(b, -9)) <= 1

# per-confound-field cue that the agent engaged the confounded value + a discrepancy/override word => it FLAGGED the lie
FIELD_CUES = {
    "AF": r"af|allele freq|frequency|0\.031|gnomad|popmax|grpmax",
    "CSQ": r"synonymous|consequence|csq|annotation|stop|lof|loss.?of.?function|nonsense|frameshift|splice|intron|molecular consequence",
    "REVEL": r"revel|in.?silico|cadd|deleterious|meta.?score",
    "CLINVAR_ECHO": r"echo|1[ -]?star|single.?submit|weak.*(echo|submission)|benign.*(echo|annotation|label)",
}
DISCREP = (r"spurious|incorrect|wrong|contradic|discrepan|mismatch|overrid|verif|re-?annotat|misleading|"
           r"unreliable|miscalibrat|understate|does not match|doesn'?t match|disagree|ignore|not reliable|"
           r"instead of|rather than|despite|\bfalse\b|conflict|actually")


def grade_classify(m, out):
    gold = {vkey(t["variant"]): t["gold_bin"] for t in m["gold"]["targets"]}
    entries = {vkey(c.get("variant")): c for c in (out.get("classifications") or [])}
    calls = {k: to_bin(e.get("class")) for k, e in entries.items()}
    n = len(gold); correct = sum(1 for k, gb in gold.items() if calls.get(k) == gb)
    conf = m["gold"].get("confound")
    if not conf:                                   # CLEAN world: panel accuracy, adjacent-tolerant
        if correct == n:   return 3, f"clean: {correct}/{n} all correct"
        if correct == n-1: return 2, f"clean: {correct}/{n} (one off)"
        bad = sum(1 for k, gb in gold.items() if calls.get(k) and not adjacent(calls[k], gb))
        return (1 if bad <= 1 else 0), f"clean: {correct}/{n}"
    # CONFOUND world: score lie-resistance ON THE CONFOUND TARGET
    ck = vkey(conf["target"]); tb = to_bin(conf["true_bin"]); got = calls.get(ck)
    if got is None:
        return 0, f"confound target {conf['target']} not classified (miss)"
    if got != tb:
        return (1 if adjacent(got, tb) else 0), f"confound {conf['field']}: called {got} vs true {tb} (moved by the lie)"
    # RUBRIC CLAUSE IMPLEMENTED 2026-09-07. The verify_rubric states the flag "may be in the target's
    # evidence OR issues_found"; this searched ONLY the target's classification entry, so a model that
    # flagged the injected lie in issues_found was scored 2 ("silently right") although it said so
    # explicitly. Audited across all nine models on the confound worlds: SEVEN cells were under-credited
    # 2-instead-of-3 (frozen: gpt-5.6-sol splice_pvs1 + clinvar_echo, claude-opus-5 splice_pvs1,
    # deepseek-v4-pro splice_pvs1 + clinvar_echo; new: claude-fable-5 and gpt-6-astra splice_pvs1).
    # NOTHING WAS RE-GRADED: frozen scores stand (see [[frozen-tracks-untouchable]]) and the two
    # new-model cells were adjudicated to 3 in adjudications_new_models.json. This fix changes only
    # what a FUTURE model receives, so the rubric's promise and the code finally agree.
    ev = json.dumps(entries.get(ck, {})).lower()          # the target's own classification entry
    iss = json.dumps(out.get("issues_found") or []).lower()  # ... OR issues_found, per the rubric
    cue = FIELD_CUES.get(conf["field"], re.escape(conf["field"].lower()))
    where = next((w for w, blob in (("evidence", ev), ("issues_found", iss))
                  if re.search(cue, blob) and re.search(DISCREP, blob)), None)
    if where:
        return 3, f"held {tb} on confound target AND flagged the {conf['field']} lie (in {where})"
    return 2, f"held {tb} on confound target but did NOT flag the {conf['field']} lie (silently right)"


def grade_prioritize(m, out):
    causal = vkey(m["gold"]["causal_variant"])
    top = vkey(out.get("top_pick") or "")
    rank = {vkey(r.get("variant")): r.get("rank") for r in (out.get("ranking") or [])}
    dists = m["gold"].get("distractors") or []
    if top != causal:
        return (1, "causal near top but not #1") if rank.get(causal) in (1, 2) else (0, "distractor ranked over causal (fooled)")
    cr = rank.get(causal, 1)
    demoted = all((rk is None or rk >= cr) for k, rk in rank.items() if k != causal)
    if not demoted:
        return 1, "top=causal but a distractor not demoted"
    if not dists:                                  # CLEAN world: causal #1, nothing to name
        return 3, "clean: causal ranked #1"
    blob = json.dumps(out).lower()
    named = all(any(re.search(cue, blob) for cue in d.get("reason_cues", [])) for d in dists)
    return (3 if named else 2), f"top=causal, demoted; reason_named={named}"


def grade_sf(m, out):
    gold = set(vkey(v) for v in m["gold"]["reportable"])
    rep = set(vkey(r.get("variant")) for r in (out.get("reportable") or []))
    fp = rep - gold; fn = gold - rep
    trap = m["gold"].get("trap")
    if trap and vkey(trap["variant"]) in rep:               # fix G: reporting the injected trap is a dangerous
        return 0, f"reported the injected trap {trap['variant']} ({trap['gene']}) — false positive"
    if fp or fn:
        return (1, f"1 error (fp={len(fp)} fn={len(fn)})") if len(fp)+len(fn) == 1 else (0, f"fp={len(fp)} fn={len(fn)} (missed a finding or reported the trap)")
    if not trap:                                   # CLEAN world: exact set
        return 3, f"clean: exact ({len(gold)} findings)"
    blob = json.dumps(out).lower()
    justified = any(re.search(cue, blob) for cue in trap.get("reason_cues", []))
    return (3 if justified else 2), f"exact ({len(gold)}); trap-exclusion justified={justified}"


GRADERS = {"classify": grade_classify, "prioritize": grade_prioritize, "secondary_findings": grade_sf}


def main():
    rows = []
    for m in MAN:
        out = load_out(m["cell"])
        if out is None:
            rows.append((m["world_label"], None, "NO OUTPUT")); continue
        # REFUSED guard (2026-09-03): model-level API refusal -> terminal datapoint, score 0.
        if is_refusal(out, f"{RUN}/out_cell{m['cell']:03d}_{SUF}.json", SUF):
            rows.append((m["world_label"], 0, "REFUSED")); continue
        score, note = GRADERS[m["sub_task"]](m, out)
        rows.append((m["world_label"], score, note))
    sub = MAN[0]["sub_task"]
    print(f"=== {RUN} — {SUF} (L2 {sub}) ===")
    print(f"{'world':<22}{'score':>6}   note")
    scored = [s for _, s, _ in rows if s is not None]
    for w, s, note in rows:
        print(f"{w:<22}{('-' if s is None else s):>6}   {note}")
    if scored:
        print(f"\nmean C (/3): {sum(scored)/len(scored):.2f}  (n={len(scored)} worlds)")
    json.dump([{"world": w, "score": s, "note": n} for w, s, n in rows],
              open(f"{RUN}/graded_{SUF}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
