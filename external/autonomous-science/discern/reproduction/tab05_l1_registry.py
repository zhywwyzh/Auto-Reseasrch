"""Table T05 -> APPENDIX: the complete L1 world registry, all 79 worlds.

WHAT THIS ADDS THAT T01 CANNOT. T01 lists each track's L1 worlds as a run-on line of names --
"clean · duplicate rows · beta outlier · EAF-scale mismatch · ..." -- which tells a reader that a world
exists and nothing about what it does. A name is not a description: `eaf_scale` names a condition
without saying what was altered, why it threatens validity, or what a proportionate response would be.
This table gives every world its answer key.

NOT AUTHORED. Every method and action string is extracted verbatim from the world's own run manifest
by extract_world_registry.py -- written by the builder that made the world, not by a later reader of
it. See that file for the join and for the 18 fields that are genuinely absent upstream.

THE THREE CLASSES ARE NOT THREE SEVERITIES, and the class comes from the manifest's `issue_present`
flag, not from the world's name. A clean control carries no issue and must be accepted; a BOUNDARY
world also carries none but looks like it does -- real biology whose correct handling is to keep the
data -- and a CONTROLLED INTEGRITY CHALLENGE must be recognised and handled. "Challenge" rather than
"defect" because several are not damage: protein's `missing_hydrogens` is a heavy-atom X-ray
structure, which is ordinary preparation. A benchmark of broken worlds alone would score reflexive
suspicion as competence, which is why 15 of the 79 carry no issue.

Caption draft, kept here so table and caption stay in sync:

    Table A2: The complete L1 integrity registry. All 79 worlds, grouped by track, with the class of
    each and the response the world was built to expect. Each track's `method` line is the QC protocol
    that track's task demands, printed once because every world in the track shares it; it is cut to
    its first sentences, and the companion CSV carries all text in full. 8 worlds are clean controls,
    7 are BOUNDARY cases carrying no issue at all -- real biology that resembles one, where the
    correct action is to retain the data -- and 64 are controlled integrity challenges spanning 58
    distinct types. Class is read from each world's `issue_present` flag, not inferred from its name.
    The three classes are a design requirement rather than a difficulty gradient: a benchmark built
    only from broken worlds would reward reflexive suspicion.

Run: .venv_bench/bin/python tab05_l1_registry.py
"""
import collections
import csv
import os

import registry_common as R

BASE = os.path.dirname(os.path.abspath(__file__))
rows = [r for r in csv.DictReader(open(os.path.join(BASE, "results/world_registry.csv")))
        if r["level"] == "L1"]

by_track = collections.OrderedDict()
for r in sorted(rows, key=lambda r: (r["track_display"], r["class"] != "clean control", r["world"])):
    by_track.setdefault(r["track_display"], []).append(r)

groups = [(t, len(rs), rs[0]["expected_method"],
           [(r["world"], r["class"], r["correct_action"]) for r in rs])
          for t, rs in by_track.items()]
# The method line is printed once per track, so it must BE one per track. If a track's worlds carry
# different method strings the group header would silently show one of them as if it covered all.
for t, rs in by_track.items():
    assert len({r["expected_method"] for r in rs}) == 1, f"{t}: L1 method is not per-track"

cls = collections.Counter(r["class"] for r in rows)
n_types = len({r["world"] for r in rows if r["class"] == "controlled integrity challenge"})
foot = (f"{len(rows)} L1 worlds over {len(by_track)} tracks: {cls['clean control']} clean controls, "
        f"{cls['boundary case']} boundary cases carrying no defect at all, and "
        f"{cls['controlled integrity challenge']} controlled integrity challenges spanning "
        f"{n_types} distinct types. "
        f"Method lines are cut to their first sentences; T05.csv carries every string in full.")

TITLE = "L1 integrity — complete world registry"
pages = R.paginate(groups, title=TITLE, foot=foot)
for i, page in enumerate(pages):
    fig = R.draw(page, i, len(pages), TITLE, foot)
    name = "T05_l1_registry" if len(pages) == 1 else f"T05{chr(ord('a') + i)}_l1_registry"
    C_rows = [{"track": t, "world": w, "class": c, "correct_action": a,
               "expected_method": m}
              for t, _, m, ws in page for w, c, a in ws]
    import fig_common as C
    C.save(fig, name, C_rows, ["track", "world", "class", "correct_action", "expected_method"])
print(f"   {len(rows)} worlds · {dict(cls)} · {len(pages)} part(s)")
