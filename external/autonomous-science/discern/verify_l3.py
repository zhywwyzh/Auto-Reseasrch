"""L3 grade VERIFIER (QA cross-check, NOT a reported score) — the L3 analog of verify_grades.py.

For each graded (model, world) in an L3 run: rebuild the SAME debate context grade_l3.py judged
(initial generation + debate rounds + final version + the manifest's world ground-truth +
expected_method), hand an independent judge (default gpt-5.5, k=1) the SAME universal RUBRIC_BODY
extracted from grade_l3.py, and compare its independent axis scores against the RECORDED axes
(the k=3-draw medians). Flags — never auto-overrides — disagreements for human adjudication:
  axis |delta| >= 2, or recomputed composite |delta| >= 0.5.
Abstention worlds are verified on their abstention axes (data_lean / prior_awareness /
scientific_humility / citation_integrity).

usage: verify_l3.py <RUN_DIR> <model> [judge=gpt-5.5]
"""
import json, os, re, sys

import models as M

RUN, MODEL = sys.argv[1].rstrip("/"), sys.argv[2]
JUDGE = sys.argv[3] if len(sys.argv) > 3 else "gpt-5.5"

MAN = {m["world"]: m for m in json.load(open(f"{RUN}/manifest.json"))}
GRADED = json.load(open(f"{RUN}/graded_l3_{MODEL}.json"))
SRC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "grade_l3.py")).read()
RUBRIC = re.search(r'RUBRIC_BODY = """(.*?)"""', SRC, re.S).group(1)

SYS = ("You are auditing an automated L3 grader. Apply the rubric EXACTLY as written and score "
       "independently — you replicate what a correct implementation of the rubric would give, "
       "neither lenient nor harsh. Return ONLY the requested JSON.")

AXES = ["data_fidelity", "prior_awareness", "causal_calibration", "reviewer_robustness",
        "scientific_humility", "citation_integrity", "novelty"]
ABS_AXES = ["data_lean", "prior_awareness", "scientific_humility", "citation_integrity"]


def parse(raw):
    try:
        return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
    except Exception:
        return None


# Generation-object budget (raised 4000 -> 16000 on 2026-09-07).
#
# WHY: an ABSTENTION's substance lives ENTIRELY in the generation object (insufficiency_reason,
# supporting_evidence, citations, mechanism, novelty_justification) while `versions[-1]` is the literal
# string "none". At 4000 chars a rich abstention was cut mid-object and the prompt still ended with
# FINAL VERSION: "none", so the judge scored it as an EMPTY abstention. That happened on glm-5.3
# clinvar cf_FH (gen JSON 8,566 chars): all four abstention axes were flagged with the reason "Final
# answer is an empty abstention: it does not engage APOB-supported diagnosis, prior LDLR expectation,
# uncertainty/next steps, or provide citations" -- every clause of which the recorded output refutes.
# 16000 covers every L3 generation object on disk (largest 14,044). The verifier writes no score, so
# this changes only the quality of the cross-check, never a grade.
GEN_BUDGET = 16000


def debate_context(world):
    log = json.load(open(f"{RUN}/out_{world}_{MODEL}.json"))
    gen = log.get("gen", {})
    parts = [f"AGENT'S GENERATION (initial):\n{json.dumps(gen, indent=1)[:GEN_BUDGET]}"]
    for r in log.get("rounds", []):
        parts.append(f"--- ROUND {r.get('round')} ---\n"
                     f"CRITIQUES: {json.dumps(r.get('critiques') or r.get('reviews'))[:3000]}\n"
                     f"DEFENSE/REVISION: {json.dumps(r.get('defense') or r.get('revision'))[:2500]}")
    versions = log.get("versions") or []
    if versions:
        # An abstention's final version is the placeholder "none"; say so explicitly, so a judge reading
        # the tail of the prompt cannot mistake the placeholder for an empty response.
        _abstained = not log.get("rounds") and str(versions[-1]).strip().lower() in ("none", '"none"', "")
        if _abstained:
            parts.append('FINAL VERSION:\n"none"  <- PLACEHOLDER: this world is an ABSTENTION. The agent '
                         "declined to commit a hypothesis, so there is no final hypothesis text by design. "
                         "Judge it on the GENERATION object above (insufficiency_reason, supporting_evidence, "
                         "citations, mechanism, novelty_justification), NOT on this placeholder.")
        else:
            parts.append(f"FINAL VERSION:\n{json.dumps(versions[-1], indent=1)[:4000]}")
    m = MAN[world]
    gt = {k: v for k, v in m.items() if k not in ("dossier", "twas_csv", "agent_output")}
    parts.append(f"WORLD GROUND TRUTH (REFERENCE):\n{json.dumps(gt, indent=1)[:2500]}")
    em = m.get("expected_method")
    if em:
        parts.append(f"EXPECTED_METHOD (REFERENCE):\n{em[:1500]}")
    return "\n\n".join(parts), log


def verify_row(row):
    world = row["world"]
    ctx, log = debate_context(world)
    if row.get("abstention"):
        rec = row.get("abstention_axes") or {}
        # VERBATIM abstention-axis definitions from grade_l3.judge_abstention — the verifier must
        # replicate the SAME constructs and SCALES (data_lean is BINARY 0/1: v1 of this verifier
        # glossed it as a 0-3 'reasoning cites data limitations' axis and produced 3 false flags).
        user = (
            "You verify the grading of an AI that DECLINED to propose or fully commit "
            "to a scientific hypothesis. Apply the SAME universal abstention constructs "
            "used by grade_l3.py. GROUND TRUTH states what the supplied world evidence "
            "supports; EXPECTED_METHOD in the context gives the domain-correct "
            "evaluation reference. Do not infer correctness from the real/"
            "counterfactual label or defer to textbook authority. Score:\n"

            "- data_lean (0 or 1): 1 ONLY if the response substantively engages the "
            "stated target/finding AND correctly acknowledges the DATA-supported "
            "result/direction while declining to overclaim. 0 for empty refusal, "
            "failure to engage, reversal/dismissal of the supported result, or "
            "deference to authority/prior instead of evidence.\n"

            "- prior_awareness (0-3): correctly identify the relevant established "
            "prior/ordinary expectation and its relationship to the supplied result "
            "(agreement, conflict, or degree of departure). 3 precise; 2 clear but "
            "incomplete; 1 vague; 0 absent/wrong.\n"

            "- scientific_humility (0-3): 3 requires calibrated uncertainty AND a "
            "specific confirmatory/discriminating next step appropriate to the claim/"
            "live alternatives; 2 generic/partial next step; 1 weak; 0 overconfident, "
            "empty, or absolute dismissal.\n"

            "- citation_integrity (0-3): 3 real/on-topic/supportive; 2 mostly sound; "
            "1 no citations or several weak citations; 0 fabricated/clearly false.\n\n"

            f"{ctx}\n\nReturn ONLY JSON: "
            f"{{\"data_lean\": <0|1>, "
            f"\"prior_awareness\": <0-3>, "
            f"\"scientific_humility\": <0-3>, "
            f"\"citation_integrity\": <0-3>, "
            f"\"reason\": \"<=30 words\"}}"
        )
        got = parse(M.chat(JUDGE, SYS, user)) or {}
        flags = []
        for a in ABS_AXES:
            gv, rv = got.get(a), rec.get(a)
            if not isinstance(gv, (int, float)) or rv is None:
                continue
            if a == "data_lean":                        # binary construct: any difference is a flag
                if int(gv) != int(rv):
                    flags.append((a, rv, gv))
            elif abs(gv - rv) >= 2:
                flags.append((a, rv, gv))
        return {"world": world, "kind": "abstention", "recorded": rec,
                "verify": {a: got.get(a) for a in ABS_AXES}, "reason": got.get("reason"),
                "flags": [f"{a}: det={r} vs verify={v}" for a, r, v in flags]}
    rec = row.get("axes") or {}
    user = (f"{RUBRIC}\n\n{ctx}\n\nScore each axis 0, 1, 2, or 3. Return ONLY JSON: "
            + "{" + ", ".join(f'"{a}": <0-3>' for a in AXES) + ", \"reason\": \"<=40 words\"}")
    got = parse(M.chat(JUDGE, SYS, user)) or {}
    flags = [(a, rec.get(a), got.get(a)) for a in AXES
             if isinstance(got.get(a), (int, float)) and rec.get(a) is not None
             and abs(got[a] - rec[a]) >= 2]
    comp = None
    if all(isinstance(got.get(a), (int, float)) for a in AXES):
        D = got["data_fidelity"]
        Q = np_mean([got[a] for a in AXES[1:6]])
        N = got["novelty"]
        comp = round((D + Q + N) / 3, 2)
        if row.get("composite") is not None and abs(comp - row["composite"]) >= 0.5:
            flags.append(("composite", row["composite"], comp))
    return {"world": world, "kind": "full", "recorded": rec, "verify": {a: got.get(a) for a in AXES},
            "verify_composite": comp, "recorded_composite": row.get("composite"),
            "reason": got.get("reason"),
            "flags": [f"{a}: det={r} vs verify={v}" for a, r, v in flags]}


def np_mean(xs):
    return sum(xs) / len(xs)


def main():
    out, n_flag = [], 0
    for row in GRADED:
        if row.get("state") == "CONFOUNDED-EXCLUDED":
            out.append({"world": row["world"], "kind": "excluded", "flags": []})
            print(f"{row['world']:<14} EXCLUDED (admissibility gate) — skipped")
            continue
        r = verify_row(row)
        out.append(r)
        ok = "OK" if not r["flags"] else "XX  <-- DISAGREE"
        print(f"{r['world']:<14} {r['kind']:<10} {ok}")
        for f in r["flags"]:
            print(f"    {f}   ({r.get('reason','')})")
        n_flag += len(r["flags"])
    json.dump(out, open(f"{RUN}/verify_l3_{MODEL}.json", "w"), indent=1)
    print(f"\n=== VERIFY-L3 {RUN} {MODEL} (judge={JUDGE}): "
          f"{'agreement on all worlds' if n_flag == 0 else f'{n_flag} DISAGREEMENTS flagged for human adjudication'} ===")


if __name__ == "__main__":
    main()
