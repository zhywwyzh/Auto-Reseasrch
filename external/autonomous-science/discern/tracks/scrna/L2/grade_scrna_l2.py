"""scrna L2 — C grader (0-3 per world, aligned with L1 grade_generic + clinvar L2) vs the golden truth in each
world's manifest. Dispatched by manifest 'sub_task':
  annotation  : recovered the 8 true cell types AND handled the confound (flagged the doublet/batch/ambient
                artifact; did NOT invent a spurious cell type for it)
  marker_de   : recovered the canonical markers AND rejected the ambient false marker / used pseudobulk (not
                cells-as-replicates) for the condition DE
  composition : recovered the 8-type composition WITHOUT counting doublets as a type, without mis-attributing a
                batch-confounded shift to biology, and without over-integrating away a real population difference

usage: grade_scrna_l2.py <run_dir> <model_suffix>
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
    return json.load(open(p)) if os.path.exists(p) else None


# ------------------------------- composition ACCURACY vs ground truth (matches GWAS/clinvar's answer-correctness) -------------------------------
# The L2 C grade must reflect whether the agent COMPUTED THE ANALYSIS CORRECTLY (answer matches the golden truth),
# not only whether it handled the confound -- the same accuracy+confound structure GWAS (lambda/z vs gold) and
# clinvar (correct/n vs gold_bin) already use. Here: does the reported cell-type COMPOSITION match the true counts?
_GT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ground_truth", "ground_truth.json")
_GT_COMP = (json.load(open(_GT_PATH)).get("cell_type_composition", {}) if os.path.exists(_GT_PATH) else {})


def composition_props(out):
    """Reported per-canonical-type PROPORTIONS from the agent's composition (labels normalized, zero-count dropped)."""
    comp = out.get("composition") or {}; d = {}
    if isinstance(comp, dict):
        for k, v in comp.items():
            n = v.get("count") if isinstance(v, dict) else v
            try: n = float(n)
            except Exception: continue
            if n <= 0: continue
            for t in norm_types(k):
                d[t] = d.get(t, 0.0) + n
    s = sum(d.values()) or 1.0
    return {k: v / s for k, v in d.items()}


def composition_accuracy(out, gold_comp=_GT_COMP):
    """(n_close, ng): canonical types whose reported PROPORTION is within tolerance (rel err < 0.5) of the true
    proportion. The agent's POOLED composition should match the underlying 8-type totals in every world (doublet/
    batch/over-integration only move or add cells; the pooled totals are ~invariant). None if no ground truth."""
    if not gold_comp:
        return None
    tot = sum(gold_comp.values()) or 1.0
    gp = {k: v / tot for k, v in gold_comp.items()}
    rp = composition_props(out)
    n = sum(1 for t, tp in gp.items() if tp > 0 and rp.get(t, 0.0) > 0 and abs(rp[t] - tp) / tp < 0.5)
    return n, len(gp)


def _acc_cap(n_close, ng):
    """Accuracy CAPS the composition score (you cannot score high with a wrong composition). Never inflates."""
    if n_close >= ng - 2: return 3        # >=6/8 types with correct proportion
    if n_close >= ng - 4: return 2        # >=4/8
    if n_close >= 2:      return 1
    return 0


# ------------------------------- cell-type name normalization (agent label -> canonical PBMC type) -------------------------------
def norm_types(text):
    """Map free-text cell-type labels to the canonical 8. Returns the SET of canonical types mentioned."""
    # underscore is a regex WORD char, so 'NK_cells'/'B_cells'/'CD14_Monocytes' break \b boundaries -> treat _ as space
    t = str(text).lower().replace("_", " "); out = set()
    if "cd4" in t and ("t" in t or "th" in t):                 out.add("CD4 T")
    if "cd8" in t and "t" in t:                                 out.add("CD8 T")
    if re.search(r"\bnk\b|natural killer", t):                  out.add("NK")
    if re.search(r"\bcd14\b|classical mono", t):                out.add("CD14 Mono")
    if re.search(r"fcgr3a|cd16|non.?classical mono|ncmono", t): out.add("FCGR3A Mono")
    if re.search(r"\bdc\b|dendritic", t):                       out.add("DC")
    if re.search(r"platelet|megakaryo", t):                     out.add("Platelet")
    if re.search(r"\bb\b|b cell|b-cell|b lympho|plasma", t) and "t" not in re.sub(r"platelet|megakaryo", "", t):
        # 'b' as a standalone lineage word (avoid matching inside 'platelet'/'t cell')
        if re.search(r"(^|[^a-z])b($|[^a-z])|b.?cell|b.?lympho|plasma", t):
            out.add("B")
    return out


def collect_type_labels(out):
    """Every cell-type label the agent asserted, from the common schema fields, normalized to the canonical set."""
    got = set()
    for e in (out.get("annotations") or []):
        if isinstance(e, dict):
            got |= norm_types(e.get("cell_type", ""))
    for x in (out.get("cell_types_found") or []):
        got |= norm_types(x)
    comp = out.get("composition") or {}
    if isinstance(comp, dict):
        for k, v in comp.items():
            # a type given an explicit ZERO count in the composition is NOT a recovered population
            if isinstance(v, (int, float)) and v == 0:
                continue
            if isinstance(v, str) and v.strip() in ("0", "0.0", "0%"):
                continue
            got |= norm_types(k)
    return got


def collect_marker_genes(out):
    genes = set()
    mk = out.get("markers")
    if isinstance(mk, dict):
        for v in mk.values():
            genes |= {str(g).upper() for g in (v if isinstance(v, list) else [v])}
    elif isinstance(mk, list):
        genes |= {str(g).upper() for g in mk}
    return genes


# ------------------------------- cue regexes for confound-handling detection (mirrors clinvar FIELD_CUES + DISCREP) -------------------------------
KIND_CUE = {
    "doublet": r"doublet|multiplet|two.?cell|co.?express.*(exclus|lineage|two)|cd3.*(ms4a1|cd79)|(ms4a1|cd79).*cd3|scrublet|doubletfinder",
    "batch":   r"batch|technical (effect|artifact|variation)|sequencing run|gem well|integrat|regress.*out|harmony|confound",
    "ambient": r"ambient|soup|contaminat|background|cell.?free|soupx|cellbender|spillover|leak|bleed",
    "over_integration": r"over.?integrat|over.?correct|erase|hallucinat|preserv.*(differ|deplet|population)|deplet|reduc.*(batch|run|b.?cell)|lower in (batch|run)|absent in|only in (one )?batch|batch.?specific population|do not (over.?)?integrat",
    "pseudoreplication": r"pseudobulk|pseudo.?bulk|aggregat.*(sample|donor|replicate)|per.?donor|per.?sample|edger|deseq|sum.*counts.*donor",
}
HANDLE = r"artifact|not (a )?(real |new |novel )?cell.?type|not a new|spurious|exclude|remove|filter|flag|technical|correct|regress|integrat|decontaminat|do not|shouldn|contaminat|confound"
INVENT = r"t.?b (cell|hybrid|type|doublet)|b.?t (cell|type)|cd3.*ms4a1|hybrid cell type|novel cell type|new cell type|unknown (novel|new) (population|type)|t/b"


def text_blob(o):
    """Concatenate only the string VALUES of the agent output (NOT the schema field names) — so a field named
    'ambient_genes_flagged' / 'batch_confounded' can never falsely match a cue meant for the agent's own content."""
    parts = []
    def rec(x):
        if isinstance(x, dict):
            for v in x.values(): rec(v)
        elif isinstance(x, (list, tuple)):
            for v in x: rec(v)
        else:
            parts.append(str(x))
    rec(o)
    return " ".join(parts).lower()


def flagged(out, kind):
    blob = text_blob(out)
    struct = any(str((a or {}).get("kind", "")).lower().find(kind[:5]) >= 0
                 for a in (out.get("artifacts_flagged") or []) + (out.get("spurious_populations_flagged") or [])
                 if isinstance(a, dict))
    return struct or bool(re.search(KIND_CUE[kind], blob) and re.search(HANDLE, blob))


def invented_real_type(out, blob):
    """The agent asserted a spurious HYBRID/novel type as a REAL cell type (the fooled failure)."""
    labels = " ".join([str((e or {}).get("cell_type", "")) for e in (out.get("annotations") or [])] +
                      [str(x) for x in (out.get("cell_types_found") or [])] +
                      list((out.get("composition") or {}).keys()))
    lab = labels.lower()
    # a hybrid/novel label that is NOT qualified as a doublet/artifact -> treated as real
    return bool(re.search(INVENT, lab) and not re.search(r"doublet|multiplet|artifact", lab))


# ------------------------------- per-sub-task graders -------------------------------
def _flagged_struct(out, kind):
    """STRUCTURED-only artifact flag (mirrors the composition fix): the agent must put the artifact in
    artifacts_flagged / spurious_populations_flagged. No loose cue-blob fallback -> merely DISCUSSING 'doublet'
    in the trajectory (while concluding none) no longer earns credit."""
    return any(str((a or {}).get("kind", "")).lower().find(kind[:5]) >= 0
               for a in (out.get("artifacts_flagged") or []) + (out.get("spurious_populations_flagged") or [])
               if isinstance(a, dict))


def _ambient_injected_gene_flagged(out, genes):
    """The agent flagged AMBIENT and named the INJECTED gene (LYZ/S100A8) — not just 'some ambient' (e.g. CD79B)."""
    G = [g.upper() for g in genes]
    for a in (out.get("artifacts_flagged") or []) + (out.get("spurious_populations_flagged") or []):
        if isinstance(a, dict) and str(a.get("kind", "")).lower().find("ambient") >= 0:
            if any(g in json.dumps(a).upper() for g in G):
                return True
    ag = out.get("ambient_genes_flagged")
    if isinstance(ag, list) and any(str(g).upper() in G for g in ag):
        return True
    # issues_found is a first-class structured findings field: credit an entry that ASSERTS ambient AND
    # names the injected gene in the SAME entry (both conditions together -> not an incidental cue-match).
    for it in (out.get("issues_found") or []):
        s = (it if isinstance(it, str) else json.dumps(it)).upper()
        if "AMBIENT" in s and any(g in s for g in G):
            return True
    return False


def grade_annotation(m, out):
    gold_types = set(m["gold"]["true_types"]); ng = len(gold_types)
    found = collect_type_labels(out); nrec = len(found & gold_types)
    conf = m["gold"].get("confound")
    if not conf:                                                # CLEAN: pure recovery of the 8 types
        if nrec >= 6: return 3, f"clean: recovered {nrec}/{ng} cell types"
        if nrec >= 4: return 2, f"clean: recovered {nrec}/{ng}"
        if nrec >= 2: return 1, f"clean: recovered {nrec}/{ng}"
        return 0, f"clean: recovered {nrec}/{ng} (failed)"
    kind = conf["kind"]
    if kind == "ambient":                                      # DECISIVE: must name the INJECTED ambient gene(s)
        fl = _ambient_injected_gene_flagged(out, conf.get("ambient_genes") or [conf.get("gene", "LYZ")])
        if fl and nrec >= 5: return 3, f"ambient: flagged the injected ambient gene(s) LYZ/S100A8 + recovered {nrec}/{ng}"
        if nrec >= 5:        return 2, f"ambient: recovered {nrec}/{ng} but did not flag the injected LYZ/S100A8 ambient spread"
        if nrec >= 3:        return 1, f"ambient: recovered {nrec}/{ng}"
        return 0, f"ambient: recovered {nrec}/{ng} (mis-annotated on the ambient marker)"
    fl = _flagged_struct(out, kind)                           # DECISIVE: structured artifacts_flagged of THIS kind, NOT a cue-match
    if invented_real_type(out, text_blob(out)):               # invented a spurious type for the artifact = fooled
        return 0, f"{kind}: invented a spurious cell type for the artifact (fooled)"
    if fl and nrec >= 4: return 3, f"{kind}: flagged the {kind} artifact (structured) + recovered {nrec}/{ng}"
    if fl:               return 2, f"{kind}: flagged the {kind} artifact, weak recovery {nrec}/{ng}"
    if nrec >= 4:        return 1, f"{kind}: recovered {nrec}/{ng} but did not flag the {kind} artifact"
    return 0, f"{kind}: recovered {nrec}/{ng}, artifact not handled"


def grade_marker_de(m, out):
    canon = m["gold"]["canonical_markers"]
    canon_genes = {g.upper() for gs in canon.values() for g in gs}
    got = collect_marker_genes(out); nrec = len(got & canon_genes); ncan = len(canon_genes)
    conf = m["gold"].get("confound"); blob = text_blob(out)
    if not conf:                                                # CLEAN: canonical-marker recovery
        if nrec >= 0.5 * ncan: return 3, f"clean: recovered {nrec}/{ncan} canonical markers"
        if nrec >= 0.3 * ncan: return 2, f"clean: recovered {nrec}/{ncan}"
        if nrec > 0:           return 1, f"clean: recovered {nrec}/{ncan}"
        return 0, f"clean: recovered {nrec}/{ncan}"
    if conf["kind"] == "ambient":
        g = conf["gene"].upper()
        listed = g in got                                      # reported the ambient gene AS a real marker
        agf = [str(x).upper() for x in (out.get("ambient_genes_flagged") or [])]
        in_list = any(g in x for x in agf)
        carpet = len(agf) > 12                                 # >12 genes dumped as 'ambient' = indiscriminate, not a diagnosis
        # SPECIFIC = named the injected gene in a REASONED ambient statement (issues_found / flag reason pairing the gene
        # with ambient/soup/contamination language), OR listed it in a FOCUSED (non-carpet-bomb) ambient set.
        reasoned = False
        for it in (out.get("issues_found") or []) + (out.get("artifacts_flagged") or []) + (out.get("spurious_populations_flagged") or []):
            s = it if isinstance(it, str) else json.dumps(it)
            if g in s.upper() and re.search(KIND_CUE["ambient"], s.lower()):
                reasoned = True; break
        specific = reasoned or (in_list and not carpet)
        if specific and nrec >= 0.3 * ncan: return 3, f"ambient: specifically flagged {g} as ambient + recovered {nrec}/{ncan} markers"
        if specific:                        return 2, f"ambient: specifically flagged {g} as ambient, weak recovery"
        if in_list and carpet:              return 2, f"ambient: flagged {g} only within an indiscriminate {len(agf)}-gene ambient dump (non-specific, no diagnosis)"
        if listed:                          return 0, f"ambient: reported {g} as a real marker (fooled by the soup)"
        return 1, f"ambient: did not flag {g} but did not feature it as a marker"
    # pseudoreplication
    method = str(out.get("de_method", "")).lower()
    used_pb = bool(re.search(KIND_CUE["pseudoreplication"], blob)) or "pseudobulk" in method
    named = bool(re.search(r"pseudorep|cells? as (biological )?replicate|inflat|false.?positive|squair|non.?independen|not independent", blob))
    if used_pb and named: return 3, "pseudorep: used pseudobulk AND named the pseudoreplication pitfall"
    if used_pb:           return 2, "pseudorep: used pseudobulk"
    if named:             return 1, "pseudorep: flagged inflation but used single-cell DE"
    return 0, "pseudorep: cells-as-replicates, no awareness (fooled by inflated DE)"


def grade_composition(m, out):
    """Composition C grade = confound-handling (core) CAPPED by answer-accuracy vs ground truth (matches the
    GWAS/clinvar accuracy+confound structure). The cap only LOWERS a score: a model that handles the confound but
    computes a wrong composition (e.g. collapses cells into 'unassigned') cannot score high."""
    conf = m["gold"].get("confound")
    if conf and conf.get("kind") == "resolution":            # resolution_trap is a composition world (2nd tool trap)
        return grade_resolution_trap(m, out)
    score, note = _grade_composition_core(m, out)
    acc = composition_accuracy(out)
    if acc is not None:
        n_close, nng = acc
        cap = _acc_cap(n_close, nng)
        if cap < score:
            return cap, note + f" | ACCURACY-CAP {n_close}/{nng} types within tol -> {score}->{cap}"
        note += f" | acc {n_close}/{nng}"
    return score, note


def _grade_composition_core(m, out):
    gold_types = set(m["gold"]["true_types"]); ng = len(gold_types)
    found = collect_type_labels(out); nrec = len(found & gold_types)
    conf = m["gold"].get("confound"); blob = text_blob(out)
    if not conf:                                                # CLEAN: recover the 8-type composition
        if nrec >= 6: return 3, f"clean: composition over {nrec}/{ng} types"
        if nrec >= 4: return 2, f"clean: {nrec}/{ng}"
        if nrec >= 2: return 1, f"clean: {nrec}/{ng}"
        return 0, f"clean: {nrec}/{ng}"
    kind = conf["kind"]
    if kind == "doublet":
        # DECISIVE: the coherent ~140-cell doublet cluster looks like a novel/transitional type. Reward recognizing it
        # as doublets; penalize annotating it as a real/novel/transitional type (the tempting failure).
        fl = flagged(out, "doublet"); inv, lbl = _spurious_type_as_real(out)
        if inv and not fl:   return 0, f"doublet: annotated the doublet cluster as a real/novel type ('{lbl}') — fooled"
        if fl and nrec >= 6: return 3, f"doublet: recognized/excluded the doublet cluster + composition over {nrec}/{ng} real types"
        if fl and nrec >= 4: return 2, f"doublet: flagged doublets, weak composition {nrec}/{ng}"
        if nrec >= 6:        return 1, f"doublet: composition {nrec}/{ng} but did not flag the doublet cluster"
        return 0, f"doublet: {nrec}/{ng}, doublet cluster not handled"
    if kind == "batch":
        # DECISIVE: no signpost — the model must DISCOVER the two runs (suffix -1/-2) AND judge the composition
        # difference unattributable. Penalize discovering the per-run difference but reporting it as real biology.
        pg = out.get("per_batch_composition") or out.get("per_group_composition") or {}
        n_groups = len(pg) if isinstance(pg, dict) else 0
        discovered = n_groups >= 2 or bool(re.search(     # affirmative discovery of a two-run structure (avoid "no batches")
            r"two (10x )?(batch|run|group)|two sequencing runs|second (batch|run)|"
            r"barcode suffix.*(two|-2|second)|-1 (and|vs|/) *-2|both (runs|batches)", blob))
        confd = out.get("batch_confounded") is True or bool(
            re.search(r"confound|unattributab|not (interpretable|attributable)|cannot (attribut|separat|distinguish)|"
                      r"perfectly (aligned|correlated|confounded)|inseparab|uninterpretab", blob)
            and re.search(r"batch|run|group|condition", blob))
        if confd and nrec >= 4:      return 3, f"batch: discovered the runs + flagged the composition difference as unattributable/confounded ({nrec}/{ng})"
        if confd:                    return 2, f"batch: flagged the confound, weak composition {nrec}/{ng}"
        if discovered and nrec >= 4: return 0, f"batch: reported the per-run composition difference as real biology, did not flag the confound (fooled)"
        if nrec >= 4:                return 1, f"batch: reported a pooled composition {nrec}/{ng} but never discovered the two-run structure"
        return 0, f"batch: {nrec}/{ng}, confound not handled"
    if kind == "over_integration":
        # DECISIVE: batch-2 genuinely lacks the population; reward preserving it, penalize integrating it away
        # (hallucinating the missing type back into batch-2, or batch-correcting without preserving the absence).
        mt = conf.get("missing_type", "B")
        pg = out.get("per_batch_composition") or out.get("per_group_composition") or {}
        b2 = _batch2_count(pg, mt)                              # missing-type count the agent reports in batch-2 (or None)
        # REDESIGN: batch-2 has a REAL sharp DEPLETION (small nonzero true_b2), not a categorical absence. Over-
        # integration RESTORES b2 toward the batch-1 proportion (full ~= batch-1 rate x batch-2 size, ~tens-hundreds).
        # PRESERVED = reported count stays near the real depletion (well below the restored level). ERASED = inflated
        # toward the full proportion. Band separates "kept the ~15x depletion" (order of magnitude) from "restored".
        true_b2 = conf.get("n_b_batch2", 0) or 0
        n_b1 = conf.get("n_b_batch1"); n1 = conf.get("n_batch1"); n2 = conf.get("n_batch2")
        full = (n_b1 / n1) * n2 if (n_b1 and n1 and n2) else (n_b1 or 0)   # what over-integration would restore
        band = max(3.0 * true_b2, 0.25 * full, 5.0)            # tolerance around the real depleted count
        struct_preserved = (b2 is not None and b2 <= band)
        struct_erased = (b2 is not None and b2 > band)
        text_preserve = bool(re.search(KIND_CUE["over_integration"], blob))
        text_integrated = bool(re.search(r"harmony|bbknn|scvi|batch.?correct|integrated the (batch|run)|ran integrat|regress.*batch", blob))
        if struct_erased:                                      return 0, f"over_int: reported ~{b2:.0f} {mt} in batch-2 vs real depleted ~{true_b2:.0f} (restored toward the ~{full:.0f} full proportion, band {band:.0f}) — over-integrated (fooled)"
        if (struct_preserved or text_preserve) and nrec >= 4:  return 3, f"over_int: preserved the real batch-2 {mt}-cell depletion (~{true_b2:.0f}, reported ~{b2:.0f}) + composition {nrec}/{ng}" if b2 is not None else f"over_int: preserved the real batch-2 {mt}-cell depletion (text) + composition {nrec}/{ng}"
        if struct_preserved or text_preserve:                  return 2, f"over_int: preserved the real depletion, weak composition {nrec}/{ng}"
        if text_integrated:                                    return 0, f"over_int: batch-corrected without preserving the real {mt}-cell depletion (fooled — restored the population)"
        if nrec >= 4:                                          return 1, f"over_int: composition {nrec}/{ng} but did not surface/guard the batch-2 {mt}-cell depletion"
        return 0, f"over_int: {nrec}/{ng}, over-integration risk not handled"
    return 0, "unknown confound"


# labels that read as a NOVEL/transitional cell type (the tempting doublet-as-type failure), when NOT qualified as doublet
_NOVEL_LABEL = re.compile(r"transition|intermediate|double.?positive|dual.?(positive|lineage)|hybrid|novel|"
                          r"\bb.?t\b|\bt.?b\b|co.?express|mixed.?lineage|unknown (type|population)")


def _spurious_type_as_real(out):
    """The agent asserted the doublet cluster as a REAL/novel cell type (a label that maps to no canonical PBMC type
    and is NOT qualified as a doublet/artifact) — the fooled failure. Returns (bool, offending_label)."""
    labels = list((out.get("composition") or {}).keys())
    labels += [str((e or {}).get("cell_type", "")) for e in (out.get("annotations") or [])]
    labels += [str(x) for x in (out.get("cell_types_found") or [])]
    for lab in labels:
        low = str(lab).lower()
        if norm_types(lab):                                                 # maps to a canonical PBMC type -> fine
            continue
        if re.search(r"doublet|multiplet|artifact|spurious|debris|low.?quality|filter|exclud|remov", low):
            continue                                                        # qualified as an artifact -> handled, not fooled
        if _NOVEL_LABEL.search(low):
            return True, lab
    return False, None


def _batch2_count(pg, mt):
    """The count of the missing type the agent reports in its batch-2/group-2 per-batch composition (or None)."""
    if not isinstance(pg, dict):
        return None
    for k, v in pg.items():
        if "2" in str(k) and isinstance(v, dict):
            for tk, tv in v.items():
                if mt in norm_types(tk) or mt.lower() == str(tk).strip().lower():
                    try:
                        return float(tv)
                    except Exception:
                        return None
    return None


def grade_resolution_trap(m, out):
    """TOOL TRAP — SAME accuracy+handling structure as grade_composition (tool-handling core CAPPED by answer-accuracy).
    'Handling' here = did the agent VERIFY/TUNE the clustering output (the M signal) instead of accepting the
    under-clustered default; 'accuracy' = does the reported composition match the true proportions (composition_accuracy
    cap). A model that 'tuned' but computed a wrong composition cannot score high; a model that got the right answer
    without shown tuning caps at 2 (accurate-but-silent), mirroring the composition tiers."""
    score, note = _grade_resolution_trap_core(m, out)
    acc = composition_accuracy(out)
    if acc is not None:
        n_close, nng = acc
        cap = _acc_cap(n_close, nng)
        if cap < score:
            return cap, note + f" | ACCURACY-CAP {n_close}/{nng} types within tol -> {score}->{cap}"
        note += f" | acc {n_close}/{nng}"
    return score, note


def _grade_resolution_trap_core(m, out):
    gold_types = set(m["gold"]["true_types"]); ng = len(gold_types)
    nrec = len(collect_type_labels(out) & gold_types)
    blob = text_blob(out)
    tuned = bool(re.search(r"resolution\s*[=:]?\s*[0-9]|multiple resolution|higher resolution|increas\w*.*resolution|"
                           r"sub.?cluster|leiden.*(1\.[2-9]|[2-9]\b)|re.?cluster|tune\w*.*(resolution|cluster)", blob))
    verified = bool(re.search(r"cd14.{0,30}fcgr3a|fcgr3a.{0,30}cd14|\bnk\b.{0,30}cd8|cd8.{0,30}\bnk\b|"
                              r"marker.{0,20}(separat|distinguish|resolv)|gnly|nkg7", blob))
    handled = tuned or verified                                   # the TOOL-HANDLING signal (verified/tuned the output)
    if nrec >= ng and handled:  return 3, f"resolution_trap: recovered {nrec}/{ng} AND verified/tuned the clustering (tool output verified)"
    if nrec >= ng:              return 2, f"resolution_trap: recovered {nrec}/{ng} but no explicit tuning/verification (silently right)"
    if handled or nrec >= ng-1: return 1, f"resolution_trap: under-clustered {nrec}/{ng} but flagged/attempted the resolution issue"
    return 0, f"resolution_trap: reported the under-clustered default ({nrec}/{ng}, merged types) as final (fooled by the tool default)"


GRADERS = {"annotation": grade_annotation, "marker_de": grade_marker_de, "composition": grade_composition}


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
