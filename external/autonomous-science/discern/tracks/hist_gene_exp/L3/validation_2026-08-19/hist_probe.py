"""hist L3 bivalency prior-probe (double-check). PREDICTION-eliciting phrasing (not principle-validation) —
the enhancer flip died because its probe asked to VALIDATE a principle. knew_prior=True iff the model predicts
EXPRESSED given strong H3K4me3 AND does NOT volunteer this gene's K562 bivalency/Polycomb repression.
Captures full answer for fabrication-adjudication."""
import json, os, sys
sys.path.insert(0,"/workspace/discern-benchmark")
import models as M
MODELS=["gpt-5.6-sol","claude-opus-5","glm-5.2","kimi-k3","gpt-4.1","deepseek-v4-pro"]
GENES=["DUSP4","NR4A3","DEPTOR","PBX3"]
SYS=("You are a gene-regulation expert. Answer ONLY from established knowledge, not from any dataset in front of you.")
def q(g): return (f"In K562 cells, the promoter of {g} carries strong H3K4me3. Based on established knowledge, would you "
    f"expect {g} to be highly expressed in K562? Give a one-sentence expectation, then end with exactly one word on its "
    f"own line: 'expressed', 'silent', or 'uncertain'.")
BIV=("bivalen","polycomb","h3k27me3","k27me3","prc2","ezh2","poised","repress")
RES="/tmp/claude-1082/-data-anonymous-genomic-discovery-gym/d698a956-138f-426d-97a7-f8131f970f0d/scratchpad/hist_probe_result.json"
out=json.load(open(RES)) if os.path.exists(RES) else {}
for m in MODELS:
    for g in GENES:
        k=f"{m}|{g}"
        if k in out and out[k].get("tail"): continue
        try:
            a=(M.chat(m,SYS,q(g)) or "").strip()
            tail=a.split()[-1].lower().strip(".'\"") if a else ""
            volun=[c for c in BIV if c in a.lower()]
            knew = (tail=="expressed") and not volun
            out[k]={"model":m,"gene":g,"tail":tail,"volunteered_bivalency":volun,"knew_prior":knew,"answer":a[:500]}
        except Exception as e:
            out[k]={"model":m,"gene":g,"error":str(e)[:150]}
        json.dump(out,open(RES,"w"),indent=1)
    print(f"done {m}",flush=True)
print("ALL DONE",flush=True)
