#!/usr/bin/env python3
"""Read-only Puppy50 progress for Hermes gateway / WhatsApp.

No GitHub token, mutation endpoint, arbitrary URL, subprocess, or remote exec.
Data is fetched from the user's public GitHub repo. The status is not a VM
success claim unless the independent state records a verified result.
"""
import argparse
import base64
import json
import math
import os
from collections import Counter
from datetime import datetime, timezone
from urllib import error, request
from pathlib import Path

REPOSITORY = "74127418528426leo-del/Test"
BASE = "https://api.github.com/repos/" + REPOSITORY
STATE = "experiments/puppy50-autolab/state.json"
QUEUE = "research_lab/queue.json"
BRANCH = "puppy50-autolab-state"
ALLOWED_COMMANDS = ("progress","latest","fastest","failures","comparison","tasks","help")
WORKFLOWS = (
    "Puppy50 autonomous guarded VM experimentation",
    "Puppy50 AI Research Laboratory",
    "Puppy50 Qwen 128 Tasks Across Four Servers",
    "Puppy50 Qwen 4B Engineering Quality Pilot",
    "Puppy50 isolated measurement and prefetch replication",
    "Puppy50 parallel secure X11 cookie experiment",
    "Puppy50 zero-prefetch independent replication",
    "Puppy50 Qwen Coder bounded CPU smoke",
)

def fetch_json(path):
    if not isinstance(path,str) or not path.startswith("/"):
        raise ValueError("invalid GitHub API path")
    if "://" in path or ".." in path or path.startswith("//"):
        raise ValueError("unsafe API path")
    url=BASE+path
    headers={
        "Accept":"application/vnd.github+json",
        "User-Agent":"Puppy50-Hermes-ReadOnly/1",
        "X-GitHub-Api-Version":"2022-11-28"
    }
    # Optional, scoped READ-ONLY credential for a private/rate-limited repo.
    # Never print or include it in GitHub logs or phone replies.
    token=os.environ.get("P50_GH_READONLY_TOKEN","").strip()
    if token:headers["Authorization"]="Bearer "+token
    req=request.Request(url,headers=headers)
    with request.urlopen(req,timeout=12) as response:
        return json.load(response)

def read_branch_file(path):
    obj=fetch_json("/contents/"+path+"?ref="+BRANCH)
    if not isinstance(obj,dict) or obj.get("encoding")!="base64":
        raise ValueError("unexpected GitHub state response")
    raw=base64.b64decode(obj["content"],validate=False)
    if len(raw)>1024*1024:
        raise ValueError("state file unexpectedly large")
    result=json.loads(raw)
    if not isinstance(result,dict):
        raise ValueError("state must be object")
    return result

def numeric_frames(item):
    f=item.get("frames")
    if not isinstance(f,dict): return []
    found=[]
    for key in ("bios1","uefi1","bios2","uefi2"):
        v=f.get(key)
        if type(v) in (int,float) and math.isfinite(v) and 0<v<600:
            found.append((key,round(float(v),3)))
    return found

def read_workflow_runs():
    # Core workflows are looked up individually so Pages activity cannot hide
    # them. One shared recent-runs query covers experimental branch workflows
    # without consuming one rate-limited GitHub request per experiment.
    files=("puppy50-autonomous-research.yml", "puppy50-ai-research-lab.yml",
           "puppy50-qwen-distributed-128.yml", "puppy50-qwen-4b-pilot.yml")
    combined=[]
    for wf in files:
        items=fetch_json("/actions/workflows/"+wf+"/runs?per_page=1").get("workflow_runs",[])
        if isinstance(items,list):combined.extend(items[:1])
    recent=fetch_json("/actions/runs?per_page=100").get("workflow_runs",[])
    if isinstance(recent,list):combined.extend(recent)
    return {"workflow_runs":combined}

def snapshot(state,queue,runs):
    history=[x for x in state.get("history",[]) if isinstance(x,dict)]
    candidate=state.get("vm_goal_candidate")
    digest=state.get("vm_goal_iso_sha256")
    matching_runs={str(x.get("run_id")) for x in history
                   if x.get("candidate_id")==candidate and x.get("iso_sha256")==digest
                   and x.get("vm_passed") is True and x.get("benchmark_timing_schema")==2
                   and x.get("run_id")}
    verified=(state.get("vm_goal_verified") is True and isinstance(digest,str) and
              len(digest)==64 and all(c in "0123456789abcdef" for c in digest) and
              bool(candidate) and len(matching_runs)>=2)
    latest_runs={}
    for r in runs.get("workflow_runs",[]):
        if not isinstance(r,dict): continue
        name=r.get("name")
        if name in WORKFLOWS and name not in latest_runs:
            latest_runs[name]={
                "status":r.get("status"),"conclusion":r.get("conclusion"),
                "html_url":r.get("html_url"),"created_at":r.get("created_at")}
    all_four=[]
    any_frames=[]
    for x in history:
        vals=numeric_frames(x)
        if vals:
            any_frames.append((x,vals))
            if len(vals)==4:all_four.append((x,vals))
    # "Best" is fastest worst-case of a full four-boot batch,
    # never cherry-pick a single BIOS result.
    best=min(all_four,key=lambda p:max(v for _,v in p[1])) if all_four else None
    latest=history[-1] if history else {}
    matched_reports=[x.get("matched_prefetch_control") for x in history
                     if isinstance(x.get("matched_prefetch_control"),dict)]
    latest_matched=matched_reports[-1] if matched_reports else None
    candidate_count=len(queue.get("candidates",[])) if isinstance(queue.get("candidates"),list) else 0
    return {
      "checked_utc":datetime.now(timezone.utc).isoformat(),
      "source_repository":REPOSITORY,
      "vm_goal_verified":verified,
      "vm_goal_candidate":candidate if verified else None,
      "vm_experiments_recorded":len(history),
      "model_hypotheses_queued":candidate_count,
      "latest_candidate":str(latest.get("candidate_id","unknown"))[:65],
      "latest_result_reason":str(latest.get("reason","no VM results"))[:240],
      "latest_observed_frames":dict(numeric_frames(latest)),
      "latest_vm_passed":latest.get("vm_passed") is True,
      "latest_same_host_comparison":latest_matched,
      "best_complete_4boot_candidate":(
         {"candidate":best[0].get("candidate_id"),
          "frames":dict(best[1]),
          "worst_seconds":max(t for _,t in best[1]),
          "mean_seconds":round(sum(t for _,t in best[1])/4,3),
          "strict_vm_goal_passed":best[0].get("vm_passed") is True}
         if best else None),
      "latest_workflow_runs":latest_runs,
      "physical_acer_power_on_to_browser_tested":False,
      "notes":"Model responses and successful CI are NOT proof of faster or usable OS. "
              "Only real QEMU validation with Firefox, RAM and network gates counts."
    }

def format_text(data,command):
    if command=="help":
        return ("Puppy50 status commands: progress, latest, fastest, failures, comparison, tasks, help. "
            "Read-only reports: no builds are started or stopped.")
    vm="VERIFIED" if data["vm_goal_verified"] else "NOT VERIFIED"
    if command=="tasks":
        runs=data.get("latest_workflow_runs",{})
        details=[]
        for title,name in (("VM experiment",WORKFLOWS[0]),("AI research",WORKFLOWS[1]),
                           ("Isolated measurement",WORKFLOWS[4]),
                           ("X11 cookie experiment",WORKFLOWS[5]),
                           ("Zero-prefetch replication",WORKFLOWS[6]),
                           ("Qwen Coder smoke",WORKFLOWS[7])):
            run=runs.get(name,{})
            details.append(f"{title}: {run.get('conclusion') or run.get('status') or 'unknown'}")
        return ("Latest workflow tasks: "+"; ".join(details)+". "
                "Workflow state is not evidence of persistent independent agents or a running Hermes supervisor.")
    if command=="comparison":
        matched=data.get("latest_same_host_comparison")
        if not isinstance(matched,dict):
            return "No independently documented same-host prefetch comparison yet."
        return (
            f"Latest same-host QEMU prefetch comparison: "
            f"control {matched.get('reference_prefetch_mib')} MiB mean "
            f"{matched.get('mean_control_seconds')}s vs candidate "
            f"{matched.get('candidate_prefetch_mib')} MiB mean "
            f"{matched.get('mean_candidate_seconds')}s. "
            f"Control minus candidate: {matched.get('mean_control_minus_candidate_seconds')}s. "
            f"Sampled home-page detections; independent replication is needed. "
            f"5s and physical Acer goals NOT certified."
        )
    if command=="latest":
        f=data["latest_observed_frames"]
        frames=", ".join(f"{k} {v:.2f}s" for k,v in f.items()) or "not recorded"
        return (f"Puppy50 latest: {data['latest_candidate']}. "
            f"Firefox frames: {frames}. "
            f"VM passed: {data['latest_vm_passed']}. "
            f"Reason: {data['latest_result_reason']}.")
    if command=="fastest":
        b=data["best_complete_4boot_candidate"]
        if not b:return "No complete four-boot QEMU measurements have been recorded yet."
        return (f"Best observed complete four-boot batch: {b['candidate']}, "
                f"mean {b['mean_seconds']:.2f}s, slowest {b['worst_seconds']:.2f}s. "
                f"Under-five-second VM goal: {vm}. Physical Acer remains untested.")
    if command=="failures":
        bad=data["latest_result_reason"]
        w=data["latest_workflow_runs"].get(WORKFLOWS[0],{})
        return f"Latest VM result: {bad}. GitHub VM workflow: {w.get('conclusion') or w.get('status') or 'unknown'}. "               f"Run: {w.get('html_url') or 'not found'}"
    w=data["latest_workflow_runs"].get(WORKFLOWS[0],{})
    return (f"Puppy50 progress: under-5s VM target {vm}. "
        f"{data['vm_experiments_recorded']} VM attempts recorded; "
        f"{data['model_hypotheses_queued']} queued hypotheses. "
        f"Last VM workflow: {w.get('conclusion') or w.get('status') or 'unknown'}. "
        f"Actual Acer timing still unverified. "
        f"{w.get('html_url') or ''}")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",nargs="?",choices=ALLOWED_COMMANDS,default="progress")
    p.add_argument("--json",action="store_true")
    args=p.parse_args()
    if args.command=="help" and not args.json:
        print(format_text({},args.command));return 0
    try:
        state=read_branch_file(STATE)
        queue=read_branch_file(QUEUE)
        runs=read_workflow_runs()
        result=snapshot(state,queue,runs)
        print(json.dumps(result,indent=2) if args.json else format_text(result,args.command))
        return 0
    except (error.HTTPError,error.URLError,TimeoutError,OSError,ValueError,KeyError) as exc:
        # Never turn a failed live read into a fictional success or leak credentials.
        detail=("HTTP "+str(exc.code) if isinstance(exc,error.HTTPError)
                else type(exc).__name__)
        print("Puppy50 live status unavailable; inspect "+
              "https://github.com/"+REPOSITORY+"/actions . Reason: "+detail)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
