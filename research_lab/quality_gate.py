#!/usr/bin/env python3
"""Conservative pre-VM scientific-quality filter for model-authored hypotheses.

This is NOT an expert peer review or proof of better performance.
Prevents wasteful VM builds from truncated, nonfalsifiable or impossible ideas.
"""
import re

MEASUREMENT=("first frame","first visible firefox","firefox first",
             "firefox frame","first rendered","first visible",
             "first screen","time to first")
CONTROL=("baseline","matched","same-host","same host","control",
         "compared","versus"," vs ","a/b")
SPECIFIC=("zstd","initramfs","libxul","prefetch","i/o",
          "firefox","render","scheduler","priority","cpu","xorg")

def assess(proposal):
    if not isinstance(proposal,dict):
        return {"admit":False,"errors":["proposal is not an object"]}
    h=proposal.get("hypothesis","")
    if not isinstance(h,str):h=""
    norm=" ".join(h.lower().split())
    errors=[]
    if not 100<=len(h)<=500:
        errors.append("hypothesis must contain 100-500 characters")
    if not re.search(r"[.!?]\s*$",h):
        errors.append("incomplete or truncated sentence")
    if not any(w in norm for w in MEASUREMENT):
        errors.append("missing explicitly measurable real Firefox first-frame outcome")
    if not any(w in norm for w in CONTROL):
        errors.append("missing matched control or baseline comparison")
    if not any(w in norm for w in SPECIFIC):
        errors.append("no concrete Linux/Firefox mechanism")
    if ("nice" in norm or "priority" in norm) and ("during initramfs" in norm
        or "before the kernel" in norm or "before firefox starts" in norm):
        errors.append("chronology error: Firefox niceness cannot affect an earlier initramfs stage")
    # Select traceable and reversible risk controls for code-review pipeline.
    # No LLM-generated code is executed by this filter.
    plan=proposal.get("architecture_idea","")
    if not isinstance(plan,str):plan=""
    lower=plan.lower()
    if not any(w in lower for w in ("sandbox","recovery","rollback","security","preserve","unchanged")):
        errors.append("missing explicit recovery/security protection plan")
    return {"admit":not errors,"errors":errors}

if __name__=="__main__":
    import json,sys
    proposal=json.load(sys.stdin)
    report=assess(proposal)
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report["admit"] else 1)
