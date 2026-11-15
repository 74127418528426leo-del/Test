#!/usr/bin/env python3
"""Puppy50 Research Lab: 128 research task slots, bounded optional real LLM calls.

Only validated numerical parameters enter the legacy VM runner.
Ideas and model prose are NEVER executed as code.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
import ipaddress
import sys
import urllib.error
import urllib.request
from quality_gate import assess as assess_scientific_quality

ROLES = (
    "kernel-critical-path", "initramfs-and-compression", "firefox-startup",
    "graphics-and-web-rendering", "cpu-memory-scheduling", "bios-uefi",
    "security-and-recovery", "measurement-and-reproducibility"
)
NICE = (-10, -9, -11, -8, -12, -7, -13, -6, -5)
ZSTD = (3, 2, 4, 1, 5, 6, 7, 8)
VALID = {(n, z) for n in NICE for z in ZSTD}
ROOT = Path(__file__).resolve().parent
STRICT_GATES = (
    "real Firefox first visible frame under 5.000s on every cold boot",
    "two BIOS plus two UEFI boots of exact candidate ISO",
    "SHA-verified RAM migration and safe media removal",
    "real Firefox browser HTTP 200 after removal",
    "identical original kernel, SquashFS root, security sandbox, and recovery",
    "two independent complete four-boot batches before VM milestone",
)
MAX_PERSISTED = 72

def now():
    return datetime.now(timezone.utc).isoformat()

def read_json(path, fallback):
    if not path or not Path(path).is_file():
        return fallback
    return json.loads(Path(path).read_text())

def task_grid():
    """128 logical independent research assignments; not 128 live model sessions."""
    return [
        {"task_id": f"{role}-{i+1:02d}", "role": role, "slot": i+1,
         "focus": f"Investigate {role} with independent hypothesis {i+1}/16"}
        for role in ROLES for i in range(16)
    ]

def ident(nice, zstd):
    return f"nice{nice}_zstd{zstd}"

def validate(obj):
    if not isinstance(obj, dict):
        raise ValueError("proposal must be a JSON object")
    n, z = obj.get("nice"), obj.get("zstd")
    if type(n) is not int or type(z) is not int or (n,z) not in VALID:
        raise ValueError("proposal exceeds allowlisted niceness/compression constraints")
    hypothesis = obj.get("hypothesis")
    if not isinstance(hypothesis, str) or not 8 <= len(hypothesis.strip()) <= 500:
        raise ValueError("invalid hypothesis text")
    idea = obj.get("architecture_idea", "")
    if not isinstance(idea, str) or len(idea) > 700:
        raise ValueError("invalid architectural idea")
    return {"id": ident(n,z), "nice": n, "zstd": z,
            "hypothesis": hypothesis.strip(), "architecture_idea": idea.strip()}

def parse_model_json(text):
    text=text.strip()
    # Some open-weight thinking models put reasoning in a separate marked span.
    if text.startswith("<think>") and "</think>" in text:
        text=text.split("</think>",1)[1].strip()
    if text.startswith("```"):
        lines=text.splitlines()
        if len(lines)>2 and lines[-1].strip()=="```":
            text="\n".join(lines[1:-1]).strip()
    return json.loads(text)

class OpenAI:
    """A remote model session requires an explicit API key and AI-enabled flag."""
    def __init__(self, model, key):
        if not key: raise ValueError("AI enabled but P50_OPENAI_API_KEY missing")
        self.model=model
        self.key=key
    def call(self, instructions, prompt, max_tokens=500):
        data=json.dumps({
            "model":self.model, "instructions":instructions, "input":prompt,
            "max_output_tokens":max_tokens, "store":False
        }).encode()
        req=urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=data, method="POST",
            headers={"Authorization":"Bearer "+self.key,
                     "Content-Type":"application/json",
                     "User-Agent":"Puppy50-ResearchLab/1"})
        try:
            with urllib.request.urlopen(req, timeout=55) as response:
                obj=json.load(response)
        except urllib.error.HTTPError as e:
            # Don't leak a potentially sensitive response or the bearer token.
            raise RuntimeError(f"model HTTP {e.code}") from None
        output=[]
        for item in obj.get("output", []):
            for c in item.get("content", []):
                if c.get("type")=="output_text":
                    output.append(c.get("text",""))
        if not output:
            raise RuntimeError("model returned no usable output text")
        return parse_model_json("\n".join(output))

class QwenCompatibleChat:
    """Open-weight Qwen via a separately hosted HTTPS OpenAI-compatible endpoint.

    This does NOT run or install a model on GitHub CPU runners.
    Requires P50_QWEN_ENDPOINT (HTTPS base URL ending /v1).
    """
    def __init__(self, model, key, endpoint):
        if not endpoint:
            raise ValueError("Qwen enabled but P50_QWEN_ENDPOINT missing")
        parts=urlsplit(endpoint.strip())
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
            raise ValueError("Qwen endpoint must use HTTPS without embedded credentials")
        if parts.query or parts.fragment or not parts.path.rstrip("/").endswith("/v1"):
            raise ValueError("Qwen endpoint must be an HTTPS /v1 API base URL")
        host=parts.hostname.lower()
        if host in ("localhost","metadata.google.internal") or host.endswith((".localhost",".local",".internal")):
            raise ValueError("Qwen requires a remotely reachable HTTPS endpoint")
        try:
            addr=ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            if not addr.is_global:
                raise ValueError("Qwen endpoint must not point to private or loopback IP")
        if not key:
            raise ValueError("Qwen enabled but P50_QWEN_API_KEY missing")
        if not isinstance(model,str) or not model.strip():
            raise ValueError("Qwen model ID required")
        self.model=model.strip()
        self.key=key
        self.url=endpoint.rstrip("/")+"/chat/completions"

    def call(self, instructions, prompt, max_tokens=500):
        data=json.dumps({
            "model":self.model,
            "messages":[{"role":"system","content":instructions},
                        {"role":"user","content":prompt}],
            "max_tokens":max_tokens,
            "stream":False,
            "temperature":0.2,
            "response_format":{"type":"json_object"},
            "chat_template_kwargs":{"enable_thinking":False}
        }).encode()
        req=urllib.request.Request(self.url,data=data,method="POST",
            headers={"Authorization":"Bearer "+self.key,
                     "Content-Type":"application/json",
                     "User-Agent":"Puppy50-ResearchLab/1"})
        try:
            with urllib.request.urlopen(req,timeout=70) as response:
                obj=json.load(response)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Qwen model HTTP {e.code}") from None
        choices=obj.get("choices",[])
        if not choices or not isinstance(choices[0],dict):
            raise RuntimeError("Qwen model returned no choices")
        content=choices[0].get("message",{}).get("content","")
        if isinstance(content,list):
            content="\n".join(str(x.get("text","")) for x in content if isinstance(x,dict))
        if not isinstance(content,str) or not content.strip():
            raise RuntimeError("Qwen model returned no usable content")
        return parse_model_json(content)

INSTRUCTIONS = """You are a specialized Puppy50 OS research agent.
Return ONLY a JSON object with integer 'nice' (one of -10,-9,-11,-8,-12,-7,-13,-6,-5),
integer 'zstd' (one of 3,2,4,1,5,6,7,8), string 'hypothesis' (8-500 chars),
and optional string 'architecture_idea' (max 700 chars, research-only).
Never invent a verified speedup or claim actual test results.
Do not propose shell commands, weakening security or disabling recovery.
This output is untrusted hypothesis data, not executable code.
The test target is four independent cold QEMU boots (BIOS twice, UEFI twice),
real Firefox first frame STRICTLY below 5 seconds, complete RAM migration,
safe media eject, and real browser HTTP200 after eject."""

def candidate_key(d):
    return (d["nice"],d["zstd"])

def deterministic_hypotheses(taken, history, max_new):
    # Offline scheduling is rule-based; explicitly NOT AI inference.
    prior={x.get("candidate_id") for x in history}
    result=[]
    for n in NICE:
        for z in ZSTD:
            k=(n,z)
            if k in taken or (ident(n,z) in prior):
                continue
            result.append({"id":ident(n,z),"nice":n,"zstd":z,
                "hypothesis":f"Controlled {n=} and zstd={z} comparison; measure the real ISO, not a surrogate.",
                "architecture_idea":"The unchanged kernel, root, browser sandbox and recovery must be verified.",
                "source":"deterministic_scheduler", "role":"offline-planner",
                "critic":"strict allowlist validation"})
            if len(result)>=max_new: return result
    return result

def ai_hypotheses(provider,tasks,taken,history,max_new,max_calls,max_parallel):
    # Every proposal consumes one call and every independent critique consumes another.
    # max_calls is a strict hard limit before entering worker threads.
    proposals=[]
    errors=[]
    budget=min(max_calls//2, max_new, len(tasks))
    if budget<1: return [],["need at least 2 model calls for proposer+critic"]
    prior_ids={x.get("candidate_id") for x in history}
    # Ground the researchers in actual VM feedback; no invented performance.
    # Keep only bounded, non-secret evidence from previous tracked runs.
    recent=[
        {"candidate_id":str(x.get("candidate_id",""))[:64],
         "vm_passed":x.get("vm_passed") is True,
         "reason":str(x.get("reason",""))[:160],
         "first_frame_seconds":x.get("frames")}
        for x in history[-12:] if isinstance(x,dict)
    ]
    def propose(task):
        response=provider.call(INSTRUCTIONS,(
            f"Research role: {task['role']}; task {task['task_id']}. "
            f"Latest verified baseline: v159, NOT under five seconds. "
            f"Current candidates already queued: {sorted(ident(*k) for k in taken)[:50]}. "
            f"Return a detailed, falsifiable compression/niceness hypothesis of 100-500 characters, "
            f"as a complete sentence ending in a period. Specify a causal startup stage, "
            f"real first visible Firefox frame outcome, matched same-host BIOS/UEFI baseline, "
            f"and independent safety gates. Firefox niceness cannot influence earlier initramfs. "
            f"Use architecture_idea for explicit recovery and sandbox preservation plans. "
            f"Observed prior verified VM ledger (failures included): {json.dumps(recent,sort_keys=True)}. "
            f"Use the ledger as feedback and NEVER claim a result that has not passed independently. "
            f"Never assert benchmark results."))
        proposal=validate(response)
        quality=assess_scientific_quality(proposal)
        if not quality["admit"]:
            raise ValueError("Scientific quality rejected: " + "; ".join(quality["errors"]))
        return task,proposal
    # Rotate specialties across cycles; no cycle exhausts the same role repeatedly.
    offset = len(taken) % len(tasks)
    active = [tasks[(offset + i*17) % len(tasks)] for i in range(budget)]
    with ThreadPoolExecutor(max_workers=max_parallel) as pool:
        futs=[pool.submit(propose,t) for t in active]
        for fut in as_completed(futs):
            try:
                task,p=fut.result()
                if candidate_key(p) in taken or p["id"] in prior_ids:
                    errors.append(task["task_id"]+": duplicate or already tested")
                    continue
                proposals.append((task,p))
            except Exception as e:
                errors.append(str(e)[:200])
    # Review as a separate bounded parallel stage (no arbitrary code execution).
    # The maximum total calls is 2*budget <= max_calls.
    accepted=[]
    def review(pair):
        task,p=pair
        result=provider.call(
            "Act as an independent OS-experiment safety reviewer. Return only "
            "JSON with boolean 'approve' and short string 'reason'. "
            "Reject non-allowlisted parameters, unsupported speed claims, "
            "sandbox weakening, recovery removal or uncontrolled expense.",
            json.dumps({"candidate":p,"security_gates":STRICT_GATES}),max_tokens=230)
        return task,p,result
    with ThreadPoolExecutor(max_workers=max_parallel) as pool:
        futs=[pool.submit(review,pair) for pair in proposals[:budget]]
        for fut in as_completed(futs):
            try:
                task,p,critique=fut.result()
                if critique.get("approve") is not True:
                    errors.append(p["id"]+": rejected by critic: "+
                                  str(critique.get("reason",""))[:130])
                    continue
                if candidate_key(p) in {candidate_key(x) for x in accepted}:
                    continue
                p.update({"source":"openai_model","role":task["role"],
                          "critic":str(critique.get("reason","Approved"))[:180]})
                accepted.append(p)
            except Exception as e:
                errors.append("review error: "+str(e)[:150])
    return accepted[:max_new],errors

def merge_queue(previous,new):
    existing=[validate(p) | {
        "source":p.get("source","previous"),"role":p.get("role","previous"),
        "critic":p.get("critic","previous")
    } for p in previous.get("candidates",[]) if isinstance(p,dict)]
    by_id={p["id"]:p for p in existing}
    for p in new:
        if p["id"] not in by_id:by_id[p["id"]]=p
    # Order is stable and capped. The VM controller still decides what to run.
    return {"schema":1,"updated_at":now(),"candidates":list(by_id.values())[:MAX_PERSISTED]}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--queue",default="")
    a.add_argument("--history",default="")
    a.add_argument("--output",default="lab-results")
    a.add_argument("--max-new",type=int,default=8)
    a.add_argument("--max-model-calls",type=int,default=8)
    a.add_argument("--parallel",type=int,default=4)
    a.add_argument("--ai-enabled",action="store_true")
    opt=a.parse_args()
    if not 1<=opt.max_new<=64 or not 0<=opt.max_model_calls<=128 or not 1<=opt.parallel<=16:
        raise SystemExit("unsafe experiment/request limits")
    queue=read_json(opt.queue,{"schema":1,"candidates":[]})
    state=read_json(opt.history,{"history":[]})
    history=state.get("history",[])
    taken={candidate_key(validate(x)) for x in queue.get("candidates",[])}
    tasks=task_grid()
    if opt.ai_enabled:
        provider_name=os.getenv("P50_MODEL_PROVIDER","qwen_compatible").strip().lower()
        if provider_name=="qwen_compatible":
            provider=QwenCompatibleChat(
                os.getenv("P50_QWEN_MODEL","Qwen/Qwen3.8-27B"),
                os.getenv("P50_QWEN_API_KEY"),
                os.getenv("P50_QWEN_ENDPOINT"))
        elif provider_name=="openai":
            provider=OpenAI(os.getenv("P50_OPENAI_MODEL","gpt-6-luna"),
                            os.getenv("P50_OPENAI_API_KEY"))
        else:
            raise ValueError("unsupported P50_MODEL_PROVIDER")
        new,errors=ai_hypotheses(provider,tasks,taken,history,opt.max_new,
                                  opt.max_model_calls,opt.parallel)
        mode="live_ai_model_calls"
        requests_budget=min(opt.max_model_calls,2*min(opt.max_model_calls//2,opt.max_new))
    else:
        new=deterministic_hypotheses(taken,history,opt.max_new)
        errors=[]
        mode="OFFLINE_NO_AI"
        requests_budget=0
    merged=merge_queue(queue,new)
    out=Path(opt.output);out.mkdir(parents=True,exist_ok=True)
    (out/"queue.json").write_text(json.dumps(merged,indent=2,sort_keys=True)+"\n")
    report={"created_at":now(),"mode":mode,
        "task_slots_planned":len(tasks),
        "real_ai_agent_sessions_confirmed":0 if not opt.ai_enabled else None,
        "max_model_calls_this_run":requests_budget,
        "model_provider":(os.getenv("P50_MODEL_PROVIDER","qwen_compatible") if opt.ai_enabled else "none"),
        "new_safe_hypotheses":len(new),
        "queue_total":len(merged["candidates"]),
        "real_VM_boots_executed_by_this_workflow":0,
        "unexecuted_architecture_ideas":[x.get("architecture_idea","") for x in new],
        "errors":errors[:40],
        "next_step":"Puppy50 VM workflow must execute and verify queued candidates before a speed claim."}
    (out/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    with open(os.environ.get("GITHUB_STEP_SUMMARY",os.devnull),"a") as f:
        f.write("## Puppy50 AI Research Laboratory\n\n")
        f.write(f"- Research slots: **{len(tasks)}** (not 128 concurrently running models)\n")
        f.write(f"- Mode: **{mode}**\n")
        f.write(f"- New safe hypotheses: **{len(new)}**\n")
        f.write(f"- Current queued candidates: **{len(merged['candidates'])}**\n")
        f.write("- VM verification: **not performed in this workflow**\n")
    return 0

if __name__=="__main__":
    sys.exit(main())
