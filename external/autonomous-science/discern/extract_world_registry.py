"""Extract the per-world registry that the appendix tables T05/T06 are built from.

WHY THIS EXISTS. The appendix needs, for every one of the 79 L1 and 102 L2 worlds, what was altered,
what the agent should verify, and what a proportionate response is. Writing that prose for 181 worlds
would produce an appendix describing what I believe the benchmark does. It is already on disk: each
world's RUN MANIFEST carries `correct_action`, `expected_method`, `canonical_checks` and `issue_type`,
written by the world builder that made the world. So this extracts, and never authors.

THE JOIN IS THE HARD PART, and it is done on evidence rather than on string surgery. Manifests name a
run's analysis `task` ("bulk_de", "gwas_signal_eda") while the scored CSVs name a `family` ("de",
"signal-eda"); no rule maps one to the other across all eight tracks. Instead each manifest run is
matched to the family whose NON-CLEAN world set it reproduces -- "clean" exists in every family, so
the perturbed labels identify the family uniquely. A run that matches no family, or two, is reported
rather than guessed at.

WHAT IS DELIBERATELY NOT REPAIRED. Three gaps are real and are emitted as gaps, not filled:
  * scRNA L2 has no `expected_method` on some worlds;
  * cf_gwas L2 has no `correct_action` on most of its worlds (it has `expected_method` for all);
  * scRNA's L2 manifests carry one extra world -- `scrna_l2_resolution_trap_run` is a single-cell
    RE-RUN of `resolution_trap`, already present in `scrna_l2_composition_run`, so it is dropped by
    the canonical join rather than counted as a 103rd world.
An empty cell in the appendix is honest; a plausible sentence I wrote is not. `world_registry_gaps.csv`
lists every one so the count is visible instead of implicit.

The canonical world list is the SCORED CSV, never the manifest directory: a manifest may hold re-runs,
pilots and abandoned cells, and only what was scored is a benchmark task.

Run: .venv_bench/bin/python extract_world_registry.py
"""
import collections
import csv
import glob
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ["level", "track", "track_display", "family", "world", "class", "is_control",
          "correct_action", "expected_method", "canonical_checks", "source_manifest"]

# L1 class, taken from the manifest's `issue_present` flag rather than inferred from the world NAME.
# The name-based rule ("abstain" in the label) happened to produce the right 8/7/64 split, but it got
# there by coincidence and it mislabelled the KIND: protein's `missing_hydrogens` is a heavy-atom
# X-ray structure, which the manifest describes as normal preparation rather than corruption. The
# builder already recorded the authoritative answer; reading it is both correct and, unlike a name
# heuristic, still correct for worlds nobody has added yet.
#
# "controlled integrity challenge", not "controlled defect": several of these 64 are conditions a
# competent analyst must RECOGNISE AND HANDLE, not damage someone inflicted on the file.
def l1_class(world, issue_present):
    if issue_present:
        return "controlled integrity challenge"
    return "clean control" if world == "clean" else "boundary case"


L2_CLASS = {"none": "clean control", "data-confound": "data confound",
            "tool-trap": "tool / procedure trap", "statistical": "statistical trap"}


def _filled(row):
    return sum(1 for f in ("correct_action", "expected_method", "canonical_checks") if row[f])


def load_csv(name):
    with open(os.path.join(BASE, "results", name)) as fh:
        return list(csv.DictReader(fh))


def manifest_cells(pattern):
    """-> {(track, run_dir): [cell, ...]} for every manifest under `pattern`."""
    out = collections.OrderedDict()
    for path in sorted(glob.glob(os.path.join(BASE, pattern))):
        rel = os.path.relpath(path, BASE)
        track, run = rel.split(os.sep)[1], rel.split(os.sep)[4]
        try:
            doc = json.load(open(path))
        except (json.JSONDecodeError, OSError):
            continue
        cells = doc if isinstance(doc, list) else doc.get("cells", [])
        cells = [c for c in cells if isinstance(c, dict) and c.get("world_label")]
        if cells:
            out.setdefault((track, run), []).extend((c, rel) for c in cells)
    return out


def main():
    l1_rows = load_csv("fig_data_l1.csv")
    l2_rows = load_csv("fig_data_l2.csv")
    m0 = l1_rows[0]["model"]
    disp = {r["track"]: r["track_display"] for r in l1_rows + l2_rows}

    # ---- canonical world lists, from the SCORED data ------------------------------------------
    l1_canon = {(r["track"], r["world"]): r for r in l1_rows if r["model"] == m0}
    l2_canon = {}
    for r in l2_rows:
        l2_canon.setdefault((r["track"], r["family"], r["world"]), r)
    fam_worlds = collections.defaultdict(set)
    for tr, fam, w in l2_canon:
        fam_worlds[(tr, fam)].add(w)

    out, gaps, notes = [], [], []

    # ---- L1: joins directly on (track, world_label) --------------------------------------------
    l1_man = {}
    for (track, _run), cells in manifest_cells("tracks/*/L1/results/*/manifest.json").items():
        for c, rel in cells:
            l1_man.setdefault((track, c["world_label"]), (c, rel))
    for (tr, w), r in sorted(l1_canon.items()):
        c, rel = l1_man.get((tr, w), ({}, ""))
        if not c:
            notes.append(f"L1 {tr}/{w}: no manifest cell")
        if "issue_present" not in c:
            raise SystemExit(f"L1 {tr}/{w}: manifest has no issue_present; class cannot be derived")
        cls = l1_class(w, c["issue_present"])
        row = {"level": "L1", "track": tr, "track_display": disp[tr], "family": "",
               "world": w, "class": cls, "is_control": cls == "clean control",
               "correct_action": c.get("correct_action", ""),
               "expected_method": c.get("expected_method", ""),
               "canonical_checks": " | ".join(c.get("canonical_checks", []) or []),
               "source_manifest": rel}
        out.append(row)
        for f in ("correct_action", "expected_method"):
            if not row[f]:
                gaps.append({"level": "L1", "track": tr, "family": "", "world": w, "missing": f})

    # ---- L2: each run is matched to the family whose NON-CLEAN worlds it reproduces -------------
    l2_seen = {}
    for (track, run), cells in manifest_cells("tracks/*/L2/results/*/manifest*.json").items():
        if track not in disp:                       # physics tracks: no authoritative registry yet
            continue
        labels = {c["world_label"] for c, _ in cells}
        perturbed = labels - {"clean"}
        hits = [fam for (tr, fam), ws in fam_worlds.items()
                if tr == track and perturbed and perturbed <= ws]
        if len(hits) != 1:
            notes.append(f"L2 {track}/{run}: matched {len(hits)} families for {sorted(perturbed)}"
                         f" -- dropped (re-run, pilot or abandoned cells)")
            continue
        fam = hits[0]
        for c, rel in cells:
            key = (track, fam, c["world_label"])
            if key not in l2_canon:                 # in a manifest but never scored: not a task
                notes.append(f"L2 {track}/{fam}/{c['world_label']}: manifest-only, not scored")
                continue
            cls = L2_CLASS[l2_canon[key]["issue_type"]]
            row = {"level": "L2", "track": track, "track_display": disp[track], "family": fam,
                   "world": c["world_label"], "class": cls, "is_control": cls == "clean control",
                   "correct_action": c.get("correct_action", ""),
                   "expected_method": c.get("expected_method", ""),
                   "canonical_checks": " | ".join(c.get("canonical_checks", []) or []),
                   "source_manifest": rel}
            # A world can appear in BOTH manifest.json and manifest_full.json for the same run, and
            # the two are not always equally complete. Keep whichever carries more of the fields the
            # appendix prints, so a thin duplicate cannot mask a populated one.
            prev = l2_seen.get(key)
            if prev is None or _filled(row) > _filled(prev):
                l2_seen[key] = row

    for row in l2_seen.values():
        out.append(row)
        for f in ("correct_action", "expected_method"):
            if not row[f]:
                gaps.append({"level": "L2", "track": row["track"], "family": row["family"],
                             "world": row["world"], "missing": f})

    seen = {(r["level"], r["track"], r["family"], r["world"]) for r in out}
    missing2 = [k for k in l2_canon if ("L2",) + k not in seen]
    for tr, fam, w in missing2:
        notes.append(f"L2 {tr}/{fam}/{w}: scored but no manifest cell")
        out.append({"level": "L2", "track": tr, "track_display": disp[tr], "family": fam, "world": w,
                    "class": L2_CLASS[l2_canon[(tr, fam, w)]["issue_type"]],
                    "is_control": l2_canon[(tr, fam, w)]["issue_type"] == "none",
                    "correct_action": "", "expected_method": "", "canonical_checks": "",
                    "source_manifest": ""})
        for f in ("correct_action", "expected_method"):
            gaps.append({"level": "L2", "track": tr, "family": fam, "world": w, "missing": f})

    out.sort(key=lambda r: (r["level"], r["track_display"], r["family"], r["world"] != "clean",
                            r["world"]))
    with open(os.path.join(BASE, "results/world_registry.csv"), "w", newline="") as fh:
        w_ = csv.DictWriter(fh, FIELDS); w_.writeheader(); w_.writerows(out)
    with open(os.path.join(BASE, "results/world_registry_gaps.csv"), "w", newline="") as fh:
        w_ = csv.DictWriter(fh, ["level", "track", "family", "world", "missing"])
        w_.writeheader(); w_.writerows(gaps)

    n1 = sum(1 for r in out if r["level"] == "L1")
    n2 = sum(1 for r in out if r["level"] == "L2")
    assert n1 == len(l1_canon) and n2 == len(l2_canon), f"registry {n1}+{n2} != canonical"
    print(f"world_registry.csv: {n1} L1 + {n2} L2 = {n1 + n2} worlds")
    g = collections.Counter((r["level"], r["track"], r["missing"]) for r in gaps)
    print(f"world_registry_gaps.csv: {len(gaps)} empty fields")
    for (lv, tr, f), n in sorted(g.items()):
        print(f"   {lv} {tr:18s} {f:16s} {n}")
    for n in notes:
        print(f"   note: {n}")


if __name__ == "__main__":
    main()
