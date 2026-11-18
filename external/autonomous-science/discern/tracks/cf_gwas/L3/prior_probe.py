"""cf_gwas L3 prior probe — the task-matched gate grade_l3.py reads (materialized 2026-09-07).

    python tracks/cf_gwas/L3/prior_probe.py tracks/cf_gwas/L3/results/l3_run <model> [<model> ...]

WHY THIS FILE EXISTS. cf_gwas is the pilot track: its cache was populated in Aug 2026 by
`tracks/cf_gwas/screen_cf_genes.py`, a PANEL-SELECTION screen that probes a candidate list across the
whole roster. Every other track ships a `L3/prior_probe.py` that probes ONE model on demand; cf_gwas
never did, so adding a model left it with no cache entry. grade_l3.cached_prior_probe() refuses to
improvise (it raises rather than probe live), which is correct -- but it means cf_gwas L3 grading dies
for any new model. Found 2026-09-07 while reviewing glm-5.3, whose cf_GSTM1/cf_TGFB1 worlds had run
but could not be graded.

The probe below is BYTE-IDENTICAL in prompt and parsing to screen_cf_genes.probe(), so a new model's
gate is decided by the same question the six frozen models answered. Only the bookkeeping differs:
knew_prior = (the model's one-word verdict == this world's textbook direction), which is what the
frozen entries encode (TGFB1 -> DELETERIOUS, GSTM1 -> PROTECTIVE; a model answering UNKNOWN gets
knew_prior=None and its counterfactual cell is CONFOUNDED-EXCLUDED, exactly as kimi-k3/GSTM1 was).

Refusal-aware: a refused probe records knew_prior=None (never False) -- a refusal is not a statement
about the model's prior, and must not silently gate a world out. See [[new-model-refusal-protocol]].
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
import models as M
from probe_cache_io import load_cache, save_cache

RUN = sys.argv[1] if len(sys.argv) > 1 else f"{ROOT}/tracks/cf_gwas/L3/results/l3_run"
MODELS = sys.argv[2:] or ["glm-5.3"]
TRAIT = "cystic fibrosis lung-disease severity"

# gene -> the textbook direction the world flips (from the manifest's textbook_expectation_direction)
TEXTBOOK = {"GSTM1": "PROTECTIVE", "TGFB1": "DELETERIOUS"}


def probe(model, gene):
    """Identical prompt/parse to screen_cf_genes.probe(); returns (verdict, full answer)."""
    sys_p = "You are a human geneticist. Answer ONLY from established, published literature — not from any dataset."
    usr = (f"According to established biology and the published literature, is HIGHER genetically-predicted "
           f"{gene} expression generally PROTECTIVE (associated with LOWER {TRAIT}) or DELETERIOUS "
           f"(associated with HIGHER {TRAIT})? Give 1-2 sentences, then end with exactly one word on its own "
           f"line: PROTECTIVE, DELETERIOUS, or UNKNOWN.")
    ans = M.chat(model, sys_p, usr)
    if M.LAST_STOP_REASON.get(model) == "refusal":
        return "REFUSED", "[REFUSED_PROBE]"
    tail = ans.strip().split()[-1].upper() if ans.strip() else ""
    if "PROTECT" in tail:    d = "PROTECTIVE"
    elif "DELETERI" in tail: d = "DELETERIOUS"
    else:                    d = "UNKNOWN"
    return d, ans.strip()


def main():
    cache = load_cache(RUN)
    for model in MODELS:
        if not M.available(model):
            print(f"[probe] {model}: NO CREDENTIAL — skipping"); continue
        for gene, textbook in TEXTBOOK.items():
            key = f"{model}|{gene}"
            if key in cache:
                print(f"[probe] {model:<16} {gene:<7} knew_prior={cache[key].get('knew_prior')}  (cached)"); continue
            d, ans = probe(model, gene)
            knew = None if d in ("UNKNOWN", "REFUSED") else (d == textbook)
            cache[key] = {"answer": ans, "knew_prior": knew}
            print(f"[probe] {model:<16} {gene:<7} verdict={d:<12} textbook={textbook:<12} knew_prior={knew}")
    print(f"[probe] wrote {save_cache(RUN, cache)} ({len(cache)} entries)")
    print("[probe] ADMISSIBLE = knew_prior True (the agent HELD the textbook direction the data flips).")


if __name__ == "__main__":
    main()
