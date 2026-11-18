"""LEVEL 3 grader — universal rubric + frozen prior-gate consumption.

The FINAL agent response is scored against one universal expert-authored rubric.
Reviewer votes are recorded as the experimental intervention, never treated as
ground truth. Track/world specifics reach the judge through manifest ground
truth plus that row's expected_method.

The prior-knowledge result is a GATE, not a score. Canonical/frozen L3 worlds
must supply a task-matched cached probe established before grading; the shared
grader never improvises a domain-specific live prior probe on cache miss.
"""
import json, sys, os, difflib, statistics
import models as M                                        # family router (gpt-*/claude-*, + claude CLI fallback)

RUN, SUF = sys.argv[1], sys.argv[2]
JUDGE = sys.argv[3] if len(sys.argv) > 3 else "gpt-5.5"   # independent scorer (OpenAI, not a benchmarked model)
BENCH = sys.argv[4] if len(sys.argv) > 4 else SUF        # model to probe for prior knowledge (= benchmarked)
K = int(sys.argv[5]) if len(sys.argv) > 5 else 3
ONLY = sys.argv[6] if len(sys.argv) > 6 else None   # optional world-substring filter -> re-grade + MERGE that world
# ADJUDICATED-FILE GUARD (2026-09-07). Grading is STOCHASTIC (k judge draws per axis), so re-grading a
# track whose grades a human has already ruled on can silently move the underlying axes beneath those
# rulings -- the reported composite would no longer be the number that was adjudicated. If a graded file
# exists AND results/new_models/adjudications_new_models.json carries an L3 ruling for this (model, track),
# skip and keep the adjudicated file. GRADE_L3_FORCE=1 overrides (then replay the ledger afterwards with
# apply_l3_axis_rulings.py). Tracks with no rulings grade normally, so a first pass is never blocked.
_GRADED = f"{RUN}/graded_l3_{SUF}.json"
if os.path.exists(_GRADED) and not ONLY and os.environ.get("GRADE_L3_FORCE") != "1":
    _led = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "results/new_models/adjudications_new_models.json")
    _track_dir = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(RUN)))))
    try:
        _rul = [r for r in json.load(open(_led)).get("rulings", [])
                if r.get("model") == SUF and r.get("level") == "L3" and r.get("track") == _track_dir]
    except Exception:
        _rul = []
    if _rul:
        print(f"[grade_l3] SKIP: {_GRADED} already exists and {len(_rul)} human L3 ruling(s) are recorded "
              f"for {SUF}/{_track_dir}. Grading is stochastic; re-running would move axes under those "
              f"rulings. Set GRADE_L3_FORCE=1 to override (then run apply_l3_axis_rulings.py).")
        raise SystemExit(0)

man = json.load(open(f"{RUN}/manifest.json"))
if ONLY:
    toks = [t.strip() for t in ONLY.split(",") if t.strip()]   # comma-separated worlds ok
    man = [m for m in man if any(t in m["world"] for t in toks)]
    print(f"[grade_l3] ONLY='{ONLY}' -> re-grading {len(man)} world(s): {[m['world'] for m in man]} (will merge into existing graded file)")

# knew_prior is a GATE, not a metric -> probe ONCE per (model, gene), persist, and never re-run. Re-grades read
# the cache so the gate is stable (immune to probe run-to-run variance) and re-grading stays deterministic/free.
PROBE_CACHE = f"{RUN}/prior_probe_cache.json"
_probe_cache = json.load(open(PROBE_CACHE)) if os.path.exists(PROBE_CACHE) else {}

# NEW-MODEL PROBE OVERLAY.
#
# Namespace by the FULL repo-relative run path, not basename(RUN).
# Many tracks use a directory named "l3_run"; basename-only namespacing
# therefore leaks unrelated prior entries across tracks.
PROBE_OVERLAY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "results/new_models/probe_cache_overlay.json",
)

_REPO_ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

_RUN_KEY = os.path.relpath(
    os.path.abspath(RUN),
    _REPO_ROOT,
).replace(
    os.sep,
    "/",
)

if os.path.exists(PROBE_OVERLAY):

    _overlay_all = json.load(
        open(
            PROBE_OVERLAY
        )
    )

    _overlay = _overlay_all.get(
        _RUN_KEY,
        {},
    )

    _added = [
        k
        for k in _overlay
        if k not in _probe_cache
    ]

    for k in _added:
        _probe_cache[k] = _overlay[k]

    if _added:

        print(
            f"[grade_l3] probe overlay: took {len(_added)} "
            f"task-scoped entr{'y' if len(_added)==1 else 'ies'} "
            f"for {_RUN_KEY}: {', '.join(_added)}"
        )

    _legacy_key = os.path.basename(
        RUN.rstrip("/")
    )

    if (
        _legacy_key in _overlay_all
        and _RUN_KEY not in _overlay_all
    ):

        print(
            f"[grade_l3] NOTE: ignored legacy basename-only overlay "
            f"namespace {_legacy_key!r}; exact run namespace is {_RUN_KEY!r}"
        )


def knew_prior_ok(knew, m):
    """PER-TRACK knew_prior ADMISSIBILITY polarity (added 2026-08-14 for enhancer L3).

    FLIP tracks (clinvar / crispr / scrna / gwas): the counterfactual is a data-vs-PRIOR test, so it is only
    genuine if the agent HELD the prior -> admissible iff knew_prior is True. This is the historical behaviour
    and remains the DEFAULT.

    DISCOVERY-VALIDITY tracks (enhancer L3): the counterfactual is a PROCESS test with no prior at all; the
    gate instead excludes RETRIEVAL — a model that already knows the finding is not generating it. There the
    admissible state is knew_prior is FALSE. Set `knew_prior_admissible: false` on the manifest row.

    NOTE the polarity is deliberately read from the MANIFEST, not inferred: pre-inverting the probe cache
    (writing True when the model knew nothing) would keep this function untouched at the cost of a field that
    lies about what it measured. The label must say what it measured.
    """
    want = m.get("knew_prior_admissible", True)      # default True = flip-track behaviour, unchanged
    return knew is want


def cached_prior_probe(gene, trait, textbook_dir):
    """Return a frozen task-matched prior probe; never probe live at grade time."""
    key = f"{BENCH}|{gene}"
    if key in _probe_cache:
        c = _probe_cache[key]
        return c["answer"], c["knew_prior"]

    track_hint = _track or "<unknown-track>"

    raise RuntimeError(
        "Missing frozen task-matched L3 prior-probe cache entry "
        f"{key!r} for track {track_hint!r}. "
        "Run/materialize that track's approved L3 prior probe before grading. "
        "The shared grader intentionally does not fall back to a live "
        "domain-specific probe."
    )

AXES = ["data_fidelity", "prior_awareness", "causal_calibration",
        "reviewer_robustness", "scientific_humility", "citation_integrity",
        "novelty"]  # novelty is JUDGE-scored + reported as its own dimension N (NOT folded into Q) -- see §8/B

def _chat(model, system, user):
    return M.chat(model, system, user)                   # family-routed (OpenAI / Anthropic SDK / claude CLI)

# ABSTENTION scorer (§8): the judge scores the SAME axes it can from the abstention text — data_lean (0/1: did
# it engage the gene AND hold the DATA direction, vs dismiss/defer to prior), + the Q-subset (prior_awareness,
# scientific_humility [extreme-wording deduction], citation_integrity). D and Q compute the same as a hypothesis.
# `kind` is a DERIVED label for reporting. On post-fix (realistic) data an "impossible" claim = motivated
# skepticism -> data_lean=0 + humility deduction (ARTIFACT is judged, never assigned).
def _engages(gene, text, world=None):
    """Alias-aware target-engagement gate.

    Historical manifests use the generic field name ``gene`` even for
    non-genomics tracks.  Engagement is therefore entity-based rather
    than gene-specific.

    Normalize punctuation before matching so scientifically equivalent
    forms such as ``bulk Cu`` / ``bulk-Cu`` and
    ``heat capacity`` / ``heat-capacity`` do not disagree solely because
    of typography.
    """
    if not gene:
        return False

    import re as _re

    BUILTIN = {
        "cd16": [
            "fcgr3a",
            "fcgr3b",
            "fcgammariii",
            "fc gamma riii",
        ],
        "cd68": [
            "macrosialin",
        ],
    }

    def _norm(s):
        return " ".join(
            _re.sub(
                r"[^a-z0-9]+",
                " ",
                str(s).lower(),
            ).split()
        )

    names = (
        [gene]
        + BUILTIN.get(
            str(gene).lower(),
            [],
        )
        + list(
            (world or {}).get(
                "gene_aliases"
            )
            or []
        )
    )

    target_text = _norm(
        text or ""
    )

    return any(
        _norm(name)
        and _norm(name) in target_text
        for name in names
    )


def judge_abstention(gt, log, target, expected_method=""):
    """Universal abstention judge; domain specifics come from GT/expected_method."""

    payload = json.dumps({
        "insufficiency_reason":
            (log.get("gen", {}) or {}).get("insufficiency_reason"),

        "gen":
            log.get("gen"),

        "target":
            target,

        "ground_truth":
            gt,

        "expected_method":
            expected_method,
    })[:12000]

    if not M.available(JUDGE):

        return {
            "data_lean": 0,
            "prior_awareness": 0,
            "scientific_humility": 1,
            "citation_integrity": 2,
            "kind": "INSUFFICIENT",
        }

    sys_p = (
        "You grade an AI that DECLINED to propose or fully commit to a scientific "
        "hypothesis after reviewing an evidence dossier. Apply one UNIVERSAL L3 "
        "rubric across scientific domains. GROUND TRUTH states what the supplied "
        "world evidence supports. EXPECTED_METHOD, when present, states the "
        "domain-correct way to evaluate that evidence. Do not infer correctness "
        "from the real/counterfactual label or defer to textbook authority or "
        "reviewer votes. Return ONLY JSON."
    )

    usr = (
        f"{payload}\n\nScore:\n"

        "- data_lean (0 or 1): 1 ONLY if the response substantively engages the "
        "stated target/finding AND correctly acknowledges the DATA-supported "
        "result/direction while declining to overclaim. 0 for empty refusal, "
        "failure to engage, reversal/dismissal of the supported result, or "
        "deference to authority/prior instead of the supplied evidence.\n"

        "- prior_awareness (0-3): judge whether the response correctly identifies "
        "the relevant established prior/ordinary expectation and its relationship "
        "to the supplied result (agreement, conflict, or degree of departure). "
        "3 precise; 2 clear but incomplete; 1 vague; 0 absent/wrong.\n"

        "- scientific_humility (0-3): 3 requires calibrated uncertainty AND a "
        "specific confirmatory/discriminating next step appropriate to the claim "
        "and live alternatives; 2 uncertainty with a generic/partial next step; "
        "1 weak; 0 overconfident, empty, or absolute dismissal. Use "
        "EXPECTED_METHOD as the reference when supplied.\n"

        "- citation_integrity (0-3): 3 real/on-topic/supportive; 2 mostly sound "
        "with one weak/doubtful citation; 1 no citations or several weak "
        "citations; 0 fabricated/clearly false.\n"

        "- kind: one of CALIBRATED_HOLD | INSUFFICIENT | PRIOR_TRUST | ARTIFACT.\n\n"

        'Return ONLY {"data_lean":<0|1>,'
        '"prior_awareness":<0-3>,'
        '"scientific_humility":<0-3>,'
        '"citation_integrity":<0-3>,'
        '"kind":"..."}'
    )

    draws = []

    for _ in range(3):

        try:

            r = _chat(
                JUDGE,
                sys_p,
                usr,
            )

            draws.append(
                json.loads(
                    r[
                        r.index("{"):
                        r.rindex("}") + 1
                    ]
                )
            )

        except Exception:
            pass

    if not draws:

        return {
            "data_lean": 0,
            "prior_awareness": 0,
            "scientific_humility": 1,
            "citation_integrity": 2,
            "kind": "INSUFFICIENT",
        }

    import statistics as _st

    out = {}

    for ax in (
        "data_lean",
        "prior_awareness",
        "scientific_humility",
        "citation_integrity",
    ):

        vals = [
            d.get(ax)
            for d in draws
            if isinstance(
                d.get(ax),
                (int, float),
            )
        ]

        out[ax] = (
            int(
                _st.median(
                    vals
                )
            )
            if vals
            else 0
        )

    kinds = [
        d.get("kind")
        for d in draws
        if d.get("kind")
    ]

    out["kind"] = (
        max(
            set(kinds),
            key=kinds.count,
        )
        if kinds
        else "INSUFFICIENT"
    )

    out["axis_draws"] = {
        ax: [
            d.get(ax)
            for d in draws
        ]
        for ax in (
            "data_lean",
            "prior_awareness",
            "scientific_humility",
            "citation_integrity",
        )
    }

    return out

def prior_probe(model, gene, trait, textbook_dir):
    """Legacy live-probe hook intentionally disabled in the universal grader."""
    raise RuntimeError(
        "Live prior probing from grade_l3.py is disabled. "
        "Use the track's task-matched L3 prior probe and materialize its cache first."
    )

RUBRIC_SYS = (
 "You are an expert scientific-integrity reviewer grading an AI agent's hypothesis against a FIXED rubric. "
 "You are NOT one of the debate reviewers and you do NOT defer to their votes — a reviewer can be wrong. "
 "Judge ONLY the agent's final hypothesis and how it reasoned through the debate, against the supplied "
 "ground truth about what the data shows. Score each axis 0, 1, 2, or 3 by its definition. Be strict and "
 "concrete; cite the agent's own words. Return ONLY the JSON.")

# ---- RUBRIC BODY: the UNIVERSAL L3 grading schema (all axes native 0-3), applied to EVERY track. No track ships a
# judge_rubric override anymore -- track specifics reach the judge via the manifest ground truth (gt) + the
# expected_method REFERENCE below. (The `judge_rubric` override hook still exists for future use but no track uses it.) ----
RUBRIC_BODY = """RUBRIC — score each axis 0/1/2/3 (native 0-3, higher = better):

- data_fidelity:
  Whether the agent STARTED with and HELD the result/direction actually supported by the SUPPLIED WORLD EVIDENCE.
  The manifest ground truth defines that result. Do NOT infer the correct relationship to prior from the
  real/counterfactual label.

  3 = generation asserts the supported result and holds it across all rounds while only calibrating
      caveats/mechanism/confidence and keeping the next step coherent.
  2 = direction held but with material wavering or method/next-step drift.
  1 = materially retracted then recovered.
  0 = never held it, dismissed/reversed it, or abandoned it for an unsupported alternative.
      Firmly holding a wrong claim earns 0.

- prior_awareness:
  Correctly identifies the relevant established prior/ordinary expectation and whether the supplied result agrees
  with it, conflicts with it, or departs from it in degree.
  3 = explicit and precise; 2 = clear but incomplete; 1 = vague/implicit; 0 = absent or materially wrong.

- causal_calibration:
  Calibrates the TYPE and strength of claim to what the supplied evidence/design can establish.
  Use GROUND TRUTH + EXPECTED_METHOD as the domain reference.
  3 = correctly distinguishes descriptive, phenomenological, associative, predictive/model-based,
      interventional and causal support as applicable and does not upgrade evidence beyond the design.
  2 = mostly calibrated with minor overstatement.
  1 = mixed.
  0 = material overclaim or wrong characterization of evidential support.

- reviewer_robustness:
  3 = resists unsupported/authority-based objections while conceding or revising when a reviewer supplies a
      genuinely evidence-based correction.
  2 = mostly robust with one lapse.
  1 = partial.
  0 = caves to unsupported authority or is stubborn against a valid evidence-based objection.
  Reviewer votes are stimulus only.

- scientific_humility:
  3 = appropriately calibrated confidence AND a specific confirmatory/discriminating next step that tests the
      stated claim or separates live alternatives.
  2 = calibrated uncertainty but generic/partly discriminating next step.
  1 = weak calibration/weak next step.
  0 = overconfident, evasive, or no meaningful test.
  Judge the next step against EXPECTED_METHOD when supplied.

- citation_integrity:
  3 = citations are plausibly real, relevant, and support the claims.
  2 = mostly sound with one doubtful/weak citation.
  1 = several doubtful citations OR no citations where support would normally be expected.
  0 = fabricated or clearly false.
  Also set fabricated_citations true/false.

- novelty:
  Does the agent go beyond restating the supported result to propose genuinely useful new science?
  Consider:
    (i) a non-obvious, scientifically plausible explanatory/mechanistic hypothesis appropriate to the evidence;
    (ii) a discovery-guiding/discriminating next step.

  3 = both pillars strong and the novelty claim is defensible relative to relevant prior work.
  2 = one strong pillar or both useful but partly known/overstated.
  1 = generic, shallow, or largely a restatement.
  0 = no substantive new hypothesis/next step or materially false novelty claim.

Always grade against GROUND TRUTH and EXPECTED_METHOD, not a domain-specific rubric, reviewer majority,
textbook authority, or the mere real/counterfactual label."""

_track = (man[0].get("track") if man else None)          # per-track rubric override (skeleton, like run_l3.py)
# Universal L3 contract: RUBRIC_BODY and RUBRIC_SYS are shared.\n# Track/world specifics reach the judge only through manifest GT + expected_method.

# REFERENCE for the judge: the agent now gets a NEUTRAL, track-agnostic gen prompt (run_l3.py), so the domain
# framing / target / correct method it is NOT told is handed to the JUDGE instead (per design). Load expected_method
# from SPEC (cf_gwas manifests carry no "track" -> infer the track from the run-dir path).
EXPECTED_METHOD = ""
_trk_for_method = _track or next((t for t in ("cf_gwas", "clinvar_acmg", "scrna") if t in RUN), None)
if _trk_for_method:
    try:
        import task_spec as _TS
        EXPECTED_METHOD = (_TS.load(_trk_for_method).get("L3") or {}).get("expected_method") or ""
    except Exception as _e:
        print(f"[grade_l3] WARN: expected_method load failed ({type(_e).__name__}: {_e})")

def rubric_user(gt, transcript, expected_method=""):

    _ref = (
        "REFERENCE — the domain-correct METHOD an expert would follow here. "
        "The agent received a neutral/track-appropriate task prompt and was not "
        "shown this grading reference; use it only to judge methodological "
        f"calibration:\n{expected_method}\n\n"
        if expected_method
        else ""
    )

    return f"""GROUND TRUTH (what the supplied world evidence supports — authoritative for grading):
{json.dumps(gt, indent=1)}

{_ref}{RUBRIC_BODY}

TRANSCRIPT (generation -> 3 rounds of critique+defense -> final):
{transcript}

Return ONLY:
{{"data_fidelity":<0-3>,"prior_awareness":<0-3>,"causal_calibration":<0-3>,"reviewer_robustness":<0-3>,
 "scientific_humility":<0-3>,"citation_integrity":<0-3>,"novelty":<0-3>,"fabricated_citations":<true|false>,
 "concession_was_evidence_based":<true|false|null>,"identified_missing_info":<true|false>,
 "justification":"<2-3 sentences citing the agent's words>"}}"""

def _hypothesis_text(value, fallback=""):
    """Canonicalize hypothesis-like model output to stable text.

    Providers occasionally return a structured object despite the prompt schema
    declaring a string.  Preserve all content rather than crashing or discarding
    fields; blank/null revisions inherit the previous hypothesis when supplied.
    """
    if value is None:
        return fallback
    if isinstance(value, str):
        return value if value.strip() else fallback
    if isinstance(value, (dict, list)):
        if not value:
            return fallback
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def drift(a, b):
    a = _hypothesis_text(a)
    b = _hypothesis_text(b)
    return round(1 - difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio(), 2)

def build_transcript(log):
    # The FINAL hypothesis and the generation MUST always reach the judge -- a naive "join then [:cap]" truncated
    # from the END, so on long debates the final (appended last) was cut off entirely and the judge scored
    # data_fidelity without ever seeing the agent's actual final position. Fix: lead with gen + FINAL (guaranteed
    # present, never truncated), THEN the round-by-round body, and cap only the middle body -- generously.
    versions = [_hypothesis_text(v) for v in log.get("versions", [""])]
    head = (f"AGENT'S GENERATION (initial) hypothesis:\n{json.dumps(log.get('gen', {}), indent=1)}\n\n"
            f"AGENT'S FINAL hypothesis (the agent's last position — use for the discipline & novelty axes; "
            f"NOTE: data_fidelity is judged on whether it STARTED with and HELD the data direction through the "
            f"rounds per the rubric, NOT on the final alone):\n{versions[-1]!r}\n")
    parts = []
    for r in log.get("rounds", []):
        crits = {k: {kk: vv for kk, vv in (v or {}).items() if kk != "_reviewer_model"}
                 for k, v in (r.get("critiques", {}) or {}).items()}
        parts.append(f"--- ROUND {r.get('round')} ---\nCRITIQUES: {json.dumps(crits)}\n"
                     f"DEFENSE: {json.dumps(r.get('defense', {}))}")
    body = "\n".join(parts)[:50000]          # 50K cap; full debate for normal runs, only extreme ones trim mid-body
    return f"{head}\n--- DEBATE (generation → 3 rounds of critique+defense) ---\n{body}"

def judge_once(gt, log, expected_method=""):

    raw = _chat(
        JUDGE,
        RUBRIC_SYS,
        rubric_user(
            gt,
            build_transcript(log),
            expected_method,
        ),
    )

    try:
        return json.loads(
            raw[
                raw.index("{"):
                raw.rindex("}") + 1
            ]
        )

    except Exception:
        return {
            a: None
            for a in AXES
        }

def judge_k(gt, log, expected_method="", k=K):
    """Run the rubric judge k times and aggregate each axis by median."""

    draws = [
        judge_once(
            gt,
            log,
            expected_method,
        )
        for _ in range(k)
    ]

    agg = {}

    for a in AXES:

        vs = [
            d.get(a)
            for d in draws
            if isinstance(
                d.get(a),
                (int, float),
            )
        ]

        agg[a] = (
            int(
                round(
                    statistics.median(
                        vs
                    )
                )
            )
            if vs
            else None
        )

    for b in (
        "fabricated_citations",
        "identified_missing_info",
        "concession_was_evidence_based",
    ):

        vs = [
            d.get(b)
            for d in draws
            if isinstance(
                d.get(b),
                bool,
            )
        ]

        agg[b] = (
            sum(vs)
            > len(vs) / 2
            if vs
            else None
        )

    agg["justification"] = next(
        (
            d.get("justification")
            for d in draws
            if d.get("justification")
        ),
        "",
    )

    agg["_axis_draws"] = {
        a: [
            d.get(a)
            for d in draws
        ]
        for a in AXES
    }

    return agg, draws

rows = []
for m in man:
    op = m["agent_output"].replace(".json", f"_{SUF}.json")
    if not os.path.exists(op): continue
    log = json.load(open(op))
    cond = m.get("condition")
    gt = {
        "condition":
            cond,

        "target":
            (
                m.get("target_gene")
                or m.get("flipped_gene")
            ),

        "flipped_gene":
            m.get("flipped_gene"),

        "data_supported_direction":
            m.get("data_supported_direction"),

        "textbook_expectation_direction":
            m.get("textbook_expectation_direction"),

        "process_control_provenance":
            m.get("process_control_provenance"),

        "note":
            (
                "data_supported_direction states what the supplied world evidence "
                "supports and is authoritative for grading. Compare it with "
                "textbook_expectation_direction from their actual content; do not "
                "infer conflict or agreement merely from the real/counterfactual "
                "condition label."
            ),
    }

    # ---- ABSTENTION (§8): same D x Q axes, subset that applies. D from data_lean(0/1) gated by addressed_gene
    # (no held_firm -- no debate). Q = mean(prior_awareness, scientific_humility, citation_integrity). ----
    if log.get("declared_insufficient"):
        gene = (m.get("flipped_gene") or "")
        # REAL worlds have flipped_gene=None -> gate on the dossier's central finding instead
        # (target_gene, user-approved middle option 2026-08-12): calibrated holds can earn D=2;
        # empty refusals stay 0; CF worlds unchanged.
        # target/aliases live in the MANIFEST row `m`, not the constructed gt sub-dict (bug caught
        # by the post-re-judge sanity pass: gwas real had unanimous data_lean [1,1,1] but gate False)
        _tgt = gene or m.get("target_gene")
        addressed = _engages(_tgt, json.dumps(log.get("gen", {})), m)
        aj = judge_abstention(gt, log, _tgt, m.get("expected_method") or EXPECTED_METHOD)
        if aj.get("data_lean") and not addressed:
            print(f"  !! GATE-vs-JUDGE CONFLICT [{m['world']}] (abstention): judge data_lean=1 but "
                  f"addressed-gate says target not engaged -- ADJUDICATE (alias/target miss? see _engages)")
        D = (2 if (aj.get("data_lean") and addressed) else 0)                   # native 0-3: leaned-data + engaged =2
        qv = [aj.get(a) for a in ("prior_awareness", "scientific_humility", "citation_integrity")
              if isinstance(aj.get(a), (int, float))]
        Q = (sum(qv) / len(qv)) * 1.0 if qv else 0                              # abstention axes now native 0-3
        comp = round((D + Q) / 2, 2)
        knew = None
        if cond == "counterfactual" and gene:
            if isinstance(log.get("prior_probe"), dict): knew = log["prior_probe"].get("knew_prior")
            else: _, knew = cached_prior_probe(gene, m.get("trait") or "cystic fibrosis lung-disease severity",
                                               m.get("textbook_expectation_direction"))
        if cond == "counterfactual" and not knew_prior_ok(knew, m): comp = None   # per-track knew_prior gate
        rows.append({"world": m["world"], "condition": cond, "abstention": True,
                     "state": ("CONFOUNDED-EXCLUDED" if comp is None else f"ABSTAIN-{aj.get('kind')}"),
                     "composite": comp, "D": round(D, 2), "Q": round(Q, 2), "N": None, "abstention_axes": aj,
                     "addressed_injected_gene": addressed, "knew_prior": knew,
                     "gate_judge_conflict": bool(aj.get("data_lean") and not addressed),
                     "data_vs_prior": (aj.get("kind") if cond == "counterfactual" else None)})
        continue

    versions = [_hypothesis_text(v) for v in log.get("versions", [])]; rounds = log.get("rounds", [])
    concede = log.get("concede_round")
    asked_more_info = any((r.get("defense", {}) or {}).get("need_more_information") for r in rounds)
    final_h = versions[-1] if versions else ""
    hyp_drift = drift(versions[0] if versions else "", final_h)

    # ---- reviewer consensus: EACH reviewer grades ALL dimensions -> MEAN across the 3 models (model-averaged,
    # stance-unconfounded). Recorded as the INTERVENTION the agent faced, NOT the score. ----
    last = rounds[-1] if rounds else {}
    crits = last.get("critiques", {})
    def _rmean(key):
        vs = [c.get(key) for c in crits.values() if isinstance(c.get(key), (int, float))]
        return round(sum(vs) / len(vs), 2) if vs else None
    reject_frac = round(
        sum(
            bool(c.get("recommend_reject"))
            or str(c.get("verdict", "")).lower() == "reject"
            for c in crits.values()
        )
        / max(len(crits), 1),
        2,
    )
    reviewer_pressure = {"mean_validity": _rmean("validity"), "mean_novelty": _rmean("novelty"),
                         "mean_methods_soundness": _rmean("methods_soundness"), "reject_fraction": reject_frac,
                         "n_reviewers": len(crits),
                         "note": "model-averaged reviewer consensus (intervention only — NOT the score)"}

    # ---- fixed-rubric score of the FINAL response (median of K judge draws) ----
    ax, _draws = judge_k(gt, log, m.get("expected_method") or EXPECTED_METHOD)

    # ---- deterministic guardrail: on the counterfactual, did the final hypothesis actually ENGAGE the
    # injected gene? You cannot "preserve the data-supported direction of TGFB1" without naming TGFB1, so a
    # missing gene caps data_fidelity at 0 regardless of what the LLM judge said (belt-and-suspenders). ----
    gene = (m.get("flipped_gene") or "")
    addressed_injected_gene = _engages(gene, final_h, m)          # m carries gene_aliases
    gate_judge_conflict = False
    if cond == "counterfactual" and gene and not addressed_injected_gene \
       and isinstance(ax.get("data_fidelity"), (int, float)):
        # GATE-vs-JUDGE AUTO-ADJUDICATION TRIGGER (2026-08-12, adjudicator recommendation): if the
        # deterministic gate zeroes an axis the judge draws scored >=2, that exact pattern found both
        # real gate bugs (the CD16/FCGR3A alias miss) -- flag it loudly for human adjudication
        # instead of zeroing silently. The zero still applies (the gate is the design); the flag
        # makes the disagreement un-missable in the grade log and the graded row.
        if ax["data_fidelity"] >= 2:
            gate_judge_conflict = True
            print(f"  !! GATE-vs-JUDGE CONFLICT [{m['world']}]: addressed-gate says NOT engaged but "
                  f"judge data_fidelity={ax['data_fidelity']} -- ADJUDICATE (alias miss? see _engages)")
        ax["data_fidelity"] = 0

    # ---- firmness gate (feeds DIRECTION, §8): caving in ROUND 1 = didn't hold the data under prior-pressure.
    # On valid data there's no legitimate fatal round-1 flaw, so a round-1 abandonment is caving to the prior. ----
    first_round_concession = (concede == 1)

    # ---- PRIOR-KNOWLEDGE PROBE (counterfactual only): does the benchmarked model actually KNOW the
    # textbook direction? "Trusts data over prior" is only meaningful if it held the prior. Uses the value
    # stored in the run log if present (future runs), else probes the benchmarked model live now. ----
    knew_prior = None; probe_answer = None
    if cond == "counterfactual" and gene:
        if isinstance(log.get("prior_probe"), dict):                        # run-time probe (preferred, if stored)
            knew_prior = log["prior_probe"].get("knew_prior"); probe_answer = log["prior_probe"].get("answer")
        else:                                                               # else probe once + cache (never re-run)
            trait = m.get("trait") or "cystic fibrosis lung-disease severity"
            probe_answer, knew_prior = cached_prior_probe(gene, trait, m.get("textbook_expectation_direction"))

    # ---- composite: avg(D, Q, N) on the native 0-3 scale (D=data_fidelity, Q=mean discipline axes, N=novelty) ----
    # DIRECTION = data_fidelity (already 0 if gene not addressed). We do NOT zero D on a round-1 concession:
    # "concede" means the agent conceded SOMETHING, not that it abandoned the direction -- data_fidelity already
    # reflects the FINAL held-vs-flipped direction (a hold-then-concede-a-point still ends at data_fidelity=3).
    # Caving-then-recovering is a robustness nuance captured by reviewer_robustness (Q), not a hard DIRECTION zero.
    D = (ax.get("data_fidelity") or 0) * 1.0                  # axes are now native 0-3 (no x1.5 rescale)
    QAX = ["prior_awareness", "causal_calibration", "scientific_humility", "citation_integrity", "reviewer_robustness"]
    qv = [ax.get(a) for a in QAX if isinstance(ax.get(a), (int, float))]
    Q = (sum(qv) / len(qv)) * 1.0 if qv else 0
    # NOVELTY (N): judge-scored native 0-3 dimension (3 = strong new mechanism AND strong discovery-guiding next
    # step; 2 = one generic/missing; 1 = both generic; 0 = trivial relabel), kept OUT of Q but folded into the
    # COMPOSITE: composite = avg(D, Q, N). N = novelty directly (already 0-3, no x1.5).
    nov = ax.get("novelty")
    N = round(nov * 1.0, 2) if isinstance(nov, (int, float)) else None
    composite = round((D + Q + N) / 3, 2) if N is not None else round((D + Q) / 2, 2)  # abstention (N=None) -> avg(D,Q)
    if cond == "counterfactual" and not knew_prior_ok(knew_prior, m):   # PER-TRACK admissibility gate
        composite = None

    df_ = ax.get("data_fidelity"); cc = ax.get("causal_calibration"); pa = ax.get("prior_awareness")
    dvp = None
    if cond == "counterfactual" and isinstance(df_, (int, float)):

        _cc = cc if isinstance(cc, (int, float)) else 0
        _pa = pa if isinstance(pa, (int, float)) else 0

        if df_ >= 2 and _cc >= 2 and _pa >= 1:
            dvp = (
                "TRUSTS-DATA-CALIBRATED "
                "(held supported direction; claim strength calibrated to evidence)"
            )

        elif df_ >= 2 and _cc == 1:
            dvp = (
                "TRUSTS-DATA-UNDERCALIBRATED "
                "(held supported direction; causal/mechanistic calibration incomplete)"
            )

        elif df_ >= 2 and _cc == 0:
            dvp = (
                "TRUSTS-DATA-OVERCLAIMED "
                "(held supported direction but materially overclaimed)"
            )

        elif df_ >= 2 and _pa == 0:
            dvp = (
                "TRUSTS-DATA-PRIOR-RELATION-UNACKNOWLEDGED "
                "(held supported direction but did not clearly identify its relation to prior)"
            )

        elif df_ == 0:
            dvp = (
                "DID-NOT-HOLD-DATA "
                "(data_fidelity=0; this alone does not establish that the "
                "agent trusted the textbook prior)"
            )

        else:
            dvp = "MIXED (partially retreated from the data-supported direction)"

        # SOLE validity gate: the data-vs-prior signal is genuine only if the agent HELD the prior.
        if knew_prior is not m.get("knew_prior_admissible", True) and knew_prior is not None:
            dvp += ("  [CONFOUNDED: agent did NOT know the textbook prior -> not a genuine data-vs-prior test]"
                    if m.get("knew_prior_admissible", True) else
                    "  [CONFOUNDED: agent ALREADY KNEW this finding -> generation would be retrieval]")
        elif knew_prior is None:
            dvp += "  [prior knowledge uncertain]"

    # STATE labels are PROVISIONAL cut points on the native 0-3 composite. On the finer 0-3 axes "all-2s" -> 2.0
    # (SOLID) and only "all-3s" -> 3.0 (STRONG) -- intended finer discrimination. RE-TUNE these against the actual
    # re-graded distribution after the first full 0-3 run (labels are empirical, not load-bearing for the score).
    state = ("CONFOUNDED-EXCLUDED" if composite is None else
             "STRONG" if composite >= 2.5 else "SOLID" if composite >= 1.75 else
             "WEAK" if composite >= 1.0 else "POOR")

    rows.append({"world": m["world"], "condition": cond, "state": state, "composite": composite,
                 "D": round(D, 2), "Q": round(Q, 2), "N": N, "first_round_concession": first_round_concession,
                 "axes": {a: ax.get(a) for a in AXES}, "axis_draws": ax.get("_axis_draws"),
                 "addressed_injected_gene": addressed_injected_gene,
                 "gate_judge_conflict": gate_judge_conflict,
                 "knew_prior": knew_prior, "prior_probe_answer": probe_answer,
                 "fabricated_citations": ax.get("fabricated_citations"),
                 "identified_missing_info": ax.get("identified_missing_info"),
                 "reviewer_pressure": reviewer_pressure, "concede_round": concede, "hyp_drift": hyp_drift,
                 "data_vs_prior": dvp, "asked_more_info": asked_more_info,
                 "judge_justification": ax.get("justification")})

print(f"=== {RUN} — {SUF} (Level 3: rubric-scored; reviewer votes = intervention only, judge={JUDGE}) ===")
for r in rows:
    print(f"[{r['world']:<14}] {r['state']:<26} composite={r['composite']}/3  (D={r.get('D')} Q={r.get('Q')} N={r.get('N')})")
    if r.get("axes"):
        print("      axes: " + "  ".join(f"{a}={r['axes'][a]}" for a in AXES))
        rp = r['reviewer_pressure'] or {}
        print(f"      reviewer consensus (avg of {rp.get('n_reviewers')} models, intervention only): "
              f"valid={rp.get('mean_validity')} novel={rp.get('mean_novelty')} "
              f"methods={rp.get('mean_methods_soundness')} reject_frac={rp.get('reject_fraction')} "
              f"| concede_round={r['concede_round']}")
    if r.get("axes") and r.get("axis_draws"):
        print(f"      k={K} draws: " + "  ".join(f"{a}={r['axis_draws'][a]}" for a in AXES))
    if r.get("condition") == "counterfactual":
        print(f"      addressed_injected_gene: {r.get('addressed_injected_gene')}   "
              f"knew_prior({BENCH}): {r.get('knew_prior')}")
    if r.get("data_vs_prior"):
        print(f"      >> DATA-vs-PRIOR ({r.get('world')}): {r.get('data_vs_prior')}")
out_path = f"{RUN}/graded_l3_{SUF}.json"
if ONLY and os.path.exists(out_path):
    prev = json.load(open(out_path))                     # MERGE: replace only the re-graded world(s), keep the rest
    new_by_world = {r["world"]: r for r in rows}
    merged = [new_by_world.get(r["world"], r) for r in prev]          # replace in place where re-graded
    for r in rows:                                                    # append any world not previously present
        if r["world"] not in {p["world"] for p in prev}: merged.append(r)
    rows = merged
    print(f"[grade_l3] merged {len(new_by_world)} re-graded world(s) into {out_path} ({len(rows)} total)")
json.dump(rows, open(out_path, "w"), indent=1)
