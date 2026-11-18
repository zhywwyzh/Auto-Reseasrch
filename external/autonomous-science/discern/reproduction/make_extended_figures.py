"""Generate the *_8models variants of every roster-dependent figure, by rewriting each frozen builder
to read the extended table and the extended model list.

    python make_extended_figures.py [name ...]

The frozen builders and their outputs are never modified: each is read, three mechanical substitutions
are applied in memory (model list, input table, output name), and the result is executed. Anything a
builder does beyond those three things -- layout, annotation, footnotes -- is inherited unchanged, so
the extended figure is the same figure with two more rows/points.
"""
import re, sys, runpy, tempfile, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JOBS = {
    "F04B_clean_outcomes":            "fig04B_clean_outcomes.py",
    "F04C_injected_process":          "fig04C_injected_process.py",
    "F04A_stage_pressure":            "fig04A_stage_pressure.py",
    "F04_grading_dimensions":         "fig04_grading_dimensions.py",
    "F05_l2_family_discontinuity":    "fig05_l2_family_discontinuity.py",
    "F11_code_functionality":         "fig11_code_functionality.py",
    "E1_quality_vs_cost":             "fig_E1_quality_vs_cost.py",
    "E2_cost_by_level":               "fig_E2_cost_by_level.py",
    "E3_effort_vs_spend":             "fig_E3_effort_vs_spend.py",
    "E4_abstain_vs_commit":           "fig_E4_abstain_vs_commit.py",
    # F09/F10 rank task categories by the ACROSS-MODEL mean, so adding models redefines the ordering
    # and the difficulty bins. They are built here for completeness; the six-model versions remain the
    # ones the text's difficulty statements refer to until that text is updated.
    "F09_task_difficulty":            "fig09_task_difficulty.py",
    "F10_cost_by_difficulty":         "fig10_cost_by_difficulty.py",
}
# Explicit label offsets for the post-freeze models, per figure, where the generic fallback overlaps.
NEW_LABEL_OFFSETS = {
    # Astra sits at (0.69, 78.1) with Kimi 4c to its left and Claude up-right: the only clear space is
    # straight below it (nothing between y=63 and y=75 at that x). GLM-5.3 (0.58, 70.4) takes the gap to
    # its right, which is empty until Kimi at a different height.
    # Kimi (0.65, 78.2) and Astra (0.69, 78.1) are effectively the same point, so BOTH labels are
    # placed here: Kimi up-LEFT (overriding its frozen up-right offset, which this figure alone needs)
    # and Astra up-RIGHT. GLM-5.3 sits below its own dot.
    "E1_quality_vs_cost": '{"glm-5.3": (0, -20), "gpt-6-astra": (0, 18), "kimi-k3": (12, -9), "claude-opus-5": (0, 12)}',
    "E3_effort_vs_spend": '{"glm-5.3": (8, 4, "left"), "gpt-6-astra": (8, -6, "left")}',
}

TABLES = ["fig_data_l1.csv", "fig_data_l2.csv", "fig_data_l3.csv", "fig_data_levels.csv",
          "fig_data_l2_comp.csv", "efficiency_by_model.csv", "efficiency_by_cell.csv"]
EXT = {t: t.replace(".csv", "_8models.csv") for t in TABLES}


def patch(src, out_name):
    s = src
    s = "import fig_common_ext as _X\n" + s
    # 1. model list -> extended
    s = re.sub(r"\bC\.MODEL_ORDER\b", "_X.MODELS", s)
    s = re.sub(r"\bC\.SHORT\b", "_X.SHORT", s)
    s = re.sub(r"\bC\.FULL\b", "_X.FULL", s)
    s = re.sub(r"\bC\.COLOR\b", "_X.COLOR", s)
    # 2a. the E-series read the frozen cost record via C.efficiency(); point them at the extended one
    s = s.replace("C.efficiency()", "__import__('json').load(open("
                  "__import__('os').path.join(__import__('os').path.dirname("
                  "__import__('os').path.abspath('fig_common.py')), 'results/efficiency_8models.json')))")
    # 2. input tables -> extended, only where an extended table exists on disk
    for t, e in EXT.items():
        if (ROOT / "results" / e).exists():
            s = s.replace(f'"{t}"', f'"{e}"').replace(f"'{t}'", f"'{e}'")
    # 2b. Per-model label-offset dicts are hand-tuned for the frozen six and KeyError on a new model.
    # Two fixes: give every lookup a fallback, and inject explicit offsets for the new models where the
    # generic fallback would collide. E1 is the case that needs it -- Astra ($0.69, 78.1) and Kimi
    # ($0.65, 78.2) are four cents and 0.1 points apart, so both cannot take the default "above".
    s = re.sub(r"\b(label_offset|lab|OFF)\[m\]", r"\1.get(m, list(\1.values())[0])", s)
    # E1 also keys horizontal alignment off a second dict; give Astra an explicit one so its label
    # starts to the right of its marker instead of straddling Kimi's.
    if out_name.startswith("E1_"):
        s = s.replace('BM = E["by_model"]', 'BM = E["by_model"]\nfor _r in C.load("token_efficiency_8models.csv"):\n    if _r["model"] in BM:\n        BM[_r["model"]]["score_chain_pct"] = float(_r["overall"])\n        BM[_r["model"]]["usd_per_quality_point"] = BM[_r["model"]]["usd_per_assigned_task"] / float(_r["overall"])')
        s = s.replace('ax.set_ylim(34, 82)', 'ax.set_ylim(34, 88)')
        s = s.replace('ax.set_xlim(0.028, 2.0)', 'ax.set_xlim(0.028, 2.4)')
        s = s.replace('first-party list rates, 2026-08-24.', 'Model-specific recorded list rates (Aug–Sep 2026).')
        s = s.replace('align = {', 'align = {"gpt-6-astra": "center", "glm-5.3": "center", ', 1)
        s = s.replace('"claude-opus-5": "left"', '"claude-opus-5": "center"')
    inject = NEW_LABEL_OFFSETS.get(out_name.replace("_8models", ""))
    if inject:
        s = re.sub(r"^(label_offset|lab|OFF)( = \{.*?\})$",
                   lambda mo: mo.group(0) + "\n" + mo.group(1) + ".update(" + inject + ")",
                   s, count=1, flags=re.S | re.M)
    # 3. output name -> _8models
    # Explicit presentation adaptations, kept separate from data-source substitutions.
    if out_name == 'F04_grading_dimensions_8models':
        s = s.replace('XL, CW = 0.265, 0.122', 'XL, CW = 0.265, 0.091')
        s = s.replace('_X.SHORT[m], ha="center", va="bottom"',
                      '_X.SHORT[m].replace("GPT-6 Astra", "GPT-6\\nAstra").replace("GPT-5.6", "GPT-5.6\\nSol"), ha="center", va="bottom"')
        s = s.replace('TOP_U - 0.056', 'TOP_U - 0.075')
    if out_name == 'F04A_stage_pressure_8models':
        s = s.replace('"right": 0.995', '"right": 0.975')
    # F04B/F04C carry six-model totals as string literals; derive them from the loaded rows instead.
    if out_name == 'F04B_clean_outcomes_8models':
        s = s.replace('"Only 16 of 48 clean controls are accepted correctly"',
                      'f"Only {tot[\'CLEAN-CORRECT\']} of {N} clean controls are accepted correctly"')
    if out_name == 'F04C_injected_process_8models':
        s = s.replace('"Right of each bar: correct diagnose-and-act, out of 71. 426 injected evaluations in "',
                      'f"Right of each bar: correct diagnose-and-act, out of 71. {len(rows)} injected evaluations in "')
        s = s.replace('"total, 229 of them diagnose-and-act.\\nNine raw state labels, uncollapsed. GPT-4.1\'s "',
                      'f"total, {sum(cnt[(m, \'DIAGNOSE-AND-ACT\')] for m in _X.MODELS)} of them diagnose-and-act.\\nNine raw state labels, uncollapsed. GPT-4.1\'s "')
    if out_name == 'F05_l2_family_discontinuity_8models':
        s = s.replace('eight tracks, six models', 'eight tracks, eight models')
    if out_name == 'F09_task_difficulty_8models':
        s = s.replace('ax.text(99, hard[0] - 0.05,', 'ax.text(99, (hard[0] if hard else 0) - 0.05,')
        s = s.replace('"Two task types defeat every model"',
                      'f"{len(hard)} task categories score below 50 for every model"')
        s = s.replace('ax.set_title(f"{len(hard)} task categories score below 50 for every model", loc="left", pad=10)',
                      'C.title(ax, f"{len(hard)} task categories score below 50 for every model")')
    if out_name == 'F10_cost_by_difficulty_8models':
        s = s.replace('"Only half the roster spends more on harder work"', '"Recorded effort across empirical difficulty bands"')
    if out_name == 'E4_abstain_vs_commit_8models':
        s = s.replace('figsize=(3.6, 2.9)', 'figsize=(5.15, 3.2)')
        s = s.replace('ax.set_title(f"Declining is {lo:.1f}–{hi:.1f}× cheaper than committing", loc="left")',
                      'C.title(ax, "Token use: abstained vs committed hypotheses")')
        start = s.index('C.footnote(ax,')
        end = s.index('C.tidy(ax)', start)
        s = s[:start] + 'C.footnote(ax, "Second tick row: abstained / eligible outcomes; exclusions omitted.\\nAstra has one committed hypothesis: its median is one observation.\\nToken use is descriptive, not a causal estimate of the effect of abstaining.", y=-0.30)\n' + s[end:]
    s = re.sub(r'(C\.save\(\s*fig\s*,\s*)(["\'])([A-Za-z0-9_]+)\2', rf'\1\g<2>{out_name}\g<2>', s)
    return s


def main():
    want = sys.argv[1:] or list(JOBS)
    ok, bad = [], []
    for name in want:
        script = JOBS[name]
        src = (ROOT / script).read_text()
        patched = patch(src, f"{name}_8models")
        fd, tmp = tempfile.mkstemp(dir=ROOT, suffix=".py", prefix="_ext_")
        os.write(fd, patched.encode()); os.close(fd)
        try:
            runpy.run_path(tmp, run_name="__main__")
            ok.append(name)
        except Exception as e:
            bad.append((name, f"{type(e).__name__}: {e}"))
        finally:
            os.unlink(tmp)
    print(f"\nbuilt {len(ok)}/{len(want)}")
    for n, e in bad:
        print(f"  FAILED {n}: {e[:200]}")


if __name__ == "__main__":
    main()
