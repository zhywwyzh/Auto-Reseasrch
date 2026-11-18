"""Table T06 -> APPENDIX: the complete L2 world registry, all 102 worlds.

WHAT THIS FIXES. T01's L2 field lists the 24 ANALYSIS FAMILIES -- "GWAS signal diagnostics · locus
analysis · TWAS variant harmonization" -- and the appendix claimed to list every L2 world. It did not:
a family is four or five worlds, one clean and the rest perturbed, and the perturbation is the entire
measurement. This table lists all 102.

GROUPED BY FAMILY, NOT BY TRACK, because at L2 the family IS the unit of method. Every world in a
family is handed the same analysis to perform and the same `expected_method` to satisfy; what differs
is what has been done to the data or what the tool will silently do to the answer. Printing the method
once per family and then only the per-world action is not compression, it is the structure of the
level.

THE FOUR CLASSES ARE THE POINT OF L2. A DATA CONFOUND corrupts the input; a TOOL / PROCEDURE TRAP does
not touch the data at all -- the software runs, returns a complete-looking result, and the result is
invalid, which is why "it executed" is never evidence here; a STATISTICAL TRAP is a defensible
procedure applied where its assumptions fail; a CLEAN CONTROL must simply be analysed correctly. 24 of
102 worlds are clean, for the same reason L1 carries controls.

Caption draft, kept here so table and caption stay in sync:

    Table A3: The complete L2 analysis registry. All 102 worlds, grouped by track and analysis family,
    with the class of each and the response the world was built to expect. Each family's `method` line
    is the analysis specification every world in that family is handed, printed once and cut to its
    first sentences; the companion CSV carries all text in full. The classes are 24 clean controls, 36
    data confounds, 34 tool- or procedure-output traps and 8 statistical traps. The tool/procedure
    class is the level's central object: the software succeeds and returns a complete-looking result
    that is invalid, so successful execution is never evidence of a valid answer. Where a field is
    marked "not recorded in the world manifest" the string is genuinely absent upstream and has been
    left empty rather than reconstructed.

Run: .venv_bench/bin/python tab06_l2_registry.py
"""
import collections
import csv
import os

import fig_common as C
import registry_common as R

BASE = os.path.dirname(os.path.abspath(__file__))
rows = [r for r in csv.DictReader(open(os.path.join(BASE, "results/world_registry.csv")))
        if r["level"] == "L2"]

by_fam = collections.OrderedDict()
for r in sorted(rows, key=lambda r: (r["track_display"], r["family"],
                                     r["class"] != "clean control", r["world"])):
    by_fam.setdefault((r["track_display"], r["family"]), []).append(r)

groups = []
for (t, f), rs in by_fam.items():
    # The method is printed once for the family, so take it from a world that HAS one -- cf_gwas and
    # scrna have worlds whose manifest cell omits fields, and an empty first row would blank the header.
    method = next((r["expected_method"] for r in rs if r["expected_method"]), "")
    groups.append((f"{t}  ·  {f}", len(rs), method,
                   [(r["world"], r["class"], r["correct_action"]) for r in rs]))

cls = collections.Counter(r["class"] for r in rows)
n_missing = sum(1 for r in rows if not r["correct_action"]) + \
            sum(1 for r in rows if not r["expected_method"])
foot = (f"{len(rows)} L2 worlds over {len(by_fam)} analysis families in "
        f"{len({t for t, _ in by_fam})} tracks: {cls['clean control']} clean controls, "
        f"{cls['data confound']} data confounds, {cls['tool / procedure trap']} tool / procedure "
        f"traps and {cls['statistical trap']} statistical traps. A tool / procedure trap leaves the "
        f"data intact: the software runs, returns a complete-looking result, and the result is "
        f"invalid. {n_missing} fields are absent in the upstream manifests and are shown as such "
        f"rather than reconstructed. Method lines are cut to their first sentences; T06.csv carries "
        f"every string in full.")

TITLE = "L2 analysis — complete world registry"
pages = R.paginate(groups, title=TITLE, foot=foot)
for i, page in enumerate(pages):
    fig = R.draw(page, i, len(pages), TITLE, foot)
    name = "T06_l2_registry" if len(pages) == 1 else f"T06{chr(ord('a') + i)}_l2_registry"
    C.save(fig, name,
           [{"track_family": g, "world": w, "class": c, "correct_action": a, "expected_method": m}
            for g, _, m, ws in page for w, c, a in ws],
           ["track_family", "world", "class", "correct_action", "expected_method"])
print(f"   {len(rows)} worlds · {dict(cls)} · {len(by_fam)} families · {len(pages)} part(s)")
