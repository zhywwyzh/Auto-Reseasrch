"""clinvar_acmg L3 prior-knowledge probe (task-matched to the diagnosis-flip).

Asks each benchmarked model, in a clean isolated context, what gene is the CLASSIC cause of each phenotype.
knew_prior=True iff it names the ANCHOR (textbook) gene -> the flip is a genuine prior-vs-data test for that model;
False/None -> CONFOUNDED (grade_l3 excludes the cell). Writes {run_dir}/prior_probe_cache.json in the exact format
grade_l3.cached_prior_probe expects (key = f"{model}|{flipped_gene}", where flipped_gene = the PARTNER gene).

usage: prior_probe.py <run_dir> <model> [<model> ...]
"""
import json, os, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
import models as M
from probe_cache_io import load_cache, save_cache   # frozen-safe cache I/O (2026-09-05)

RUN = sys.argv[1]
MODELS = sys.argv[2:] or ["deepseek-v4-pro", "kimi-k3"]

# anchor (textbook classic gene) + partner (data-supported answer = the manifest flipped_gene) per world.
# NOTE: probe the SURFACE phenotype (elicits the anchor prior); the dossier's fuller phenotype carries the
# signature that points to the partner. e.g. probe "hereditary breast cancer" -> BRCA1 (anchor); the cf_LFS
# dossier adds the Li-Fraumeni family history -> TP53 (partner).
PAIRS = {"cf_FH":  ("familial hypercholesterolemia", "LDLR",  "APOB"),
         "cf_LFS": ("hereditary breast cancer",       "BRCA1", "TP53")}
# (dropped cf_LFS_crc MLH1->TP53: models anchor on APC not MLH1 for early CRC -> confounded; also collided with
#  cf_LFS on the shared flipped_gene=TP53 prior-cache key. See dossier.py.)

SYS = "You are a clinical geneticist. Answer ONLY from established medical literature — not from any dataset."


def probe(model, pheno, anchor):
    usr = (f"According to established clinical genetics, what single gene is the CLASSIC / most commonly cited cause "
           f"of {pheno}? Give 1-2 sentences, then end with exactly one word on its own line: the gene symbol.")
    ans = M.chat(model, SYS, usr) or ""
    # REFUSAL guard (2026-09-03): a provider-level refusal (claude-fable-5 dual-use layer) is NOT
    # evidence about the model's prior. Returning it as a normal empty/short answer let the
    # gene-symbol regex score knew_prior=False off a truncated fragment, which would silently
    # mis-gate L3 admissibility. Refused -> REFUSED_PROBE, and the caller records knew_prior=None.
    if M.LAST_STOP_REASON.get(model) == "refusal":
        return ("[REFUSED_PROBE]", None)

    tail = ans.strip().split()[-1].upper() if ans.strip() else ""
    up = ans.upper()
    knew = True if anchor.upper() in tail or re.search(rf"\b{anchor.upper()}\b", up) else \
           (False if re.search(r"[A-Z0-9]{2,}", tail) else None)   # named a (different) gene -> False; nothing -> None
    return ans.strip()[:600], knew


cache = load_cache(RUN)
for model in MODELS:
    if not M.available(model):
        print(f"[probe] {model}: NO CREDENTIAL — skipping"); continue
    for world, (pheno, anchor, partner) in PAIRS.items():
        ans, knew = probe(model, pheno, anchor)
        cache[f"{model}|{partner}"] = {"answer": ans, "knew_prior": knew}
        print(f"[probe] {model:<16} {world:<9} anchor={anchor:<6} knew_prior={knew}  :: ...{ans[-90:]!r}")
_wrote = save_cache(RUN, cache)
print(f"[probe] wrote {_wrote} ({len(cache)} entries)")
