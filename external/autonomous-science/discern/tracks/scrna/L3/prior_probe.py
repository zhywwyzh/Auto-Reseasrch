"""scRNA L3 prior-knowledge probe (task-matched to the CD68 out-of-context-marker flip).

The flip only tests "trust the data over the prior" if the model HOLDS the textbook prior that CD68 is a
classical-monocyte/macrophage marker (i.e. higher in classical CD14+ monocytes than non-classical CD16+ ones).
Probe, in a clean isolated context, which monocyte subset the model thinks has higher CD68 mRNA.
  knew_prior=True  iff it says CLASSICAL   -> holds the textbook CD68->classical/macrophage prior -> genuine test.
  knew_prior=False iff it says NON-CLASSICAL -> already knows non-classical is higher -> no prior to override ->
                    CONFOUNDED (grade_l3 excludes the cell). None -> unclear.
Writes {run_dir}/prior_probe_cache.json in the format grade_l3.cached_prior_probe expects
(key = f"{model}|{flipped_gene}", flipped_gene = "CD68").

usage: prior_probe.py <run_dir> <model> [<model> ...]
"""
import json, os, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
import models as M
from probe_cache_io import load_cache, save_cache   # frozen-safe cache I/O (2026-09-05)

RUN = sys.argv[1]
MODELS = sys.argv[2:] or ["deepseek-v4-pro"]

SYS = ("You are an immunologist. Answer ONLY from established cell-biology knowledge — not from any dataset in "
       "front of you.")

# each flip: (flipped_gene cache key, question, naive_keyword=textbook that the DATA contradicts -> knew_prior=True)
FLIPS = {
    "CD68": ("Consider human PBMCs. At the mRNA level, which monocyte subset has HIGHER expression of CD68: classical "
             "CD14+ monocytes, or non-classical CD16+ (FCGR3A+) monocytes? Answer in 1-2 sentences, then end with "
             "exactly one word on its own line: either 'classical' or 'nonclassical'.", "classical"),
    "CD16": ("Consider human PBMCs. CD16 (FCGR3A) is MOST classically a marker of which cell type: NK cells, or "
             "monocytes? Answer in 1-2 sentences, then end with exactly one word on its own line: either 'NK' or "
             "'monocytes'.", "nk"),
}


def probe(model, question, naive_kw):
    ans = (M.chat(model, SYS, question) or "").strip()
    # REFUSAL guard (2026-09-03): a provider-level refusal (claude-fable-5 dual-use layer) is NOT
    # evidence about the model's prior. Returning it as a normal empty/short answer let the
    # gene-symbol regex score knew_prior=False off a truncated fragment, which would silently
    # mis-gate L3 admissibility. Refused -> REFUSED_PROBE, and the caller records knew_prior=None.
    if M.LAST_STOP_REASON.get(model) == "refusal":
        return ("[REFUSED_PROBE]", None)

    tail = ans.split()[-1].lower().strip(".") if ans else ""
    knew = (naive_kw in tail) if tail else None              # holds the textbook prior the data contradicts -> valid test
    if tail and not knew and naive_kw not in tail:
        # if the model gave the non-naive answer clearly, knew_prior=False (CONFOUNDED); ambiguous tail -> None
        knew = False if any(c.isalpha() for c in tail) else None
    return ans[:600], knew


cache = load_cache(RUN)
for model in MODELS:
    if not M.available(model):
        print(f"[probe] {model}: NO CREDENTIAL — skipping"); continue
    for gene, (q, naive) in FLIPS.items():
        ans, knew = probe(model, q, naive)
        cache[f"{model}|{gene}"] = {"answer": ans, "knew_prior": knew}
        print(f"[probe] {model:<16} {gene:<5} knew_prior={knew}  :: ...{ans[-90:]!r}")
_wrote = save_cache(RUN, cache)   # frozen (-r--r--r--) cache -> new entries go to the overlay grade_l3 reads
print(f"[probe] wrote {_wrote} ({len(cache)} entries)")
