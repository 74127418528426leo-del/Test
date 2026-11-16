#!/usr/bin/env python3
"""Puppy50 bounded VM experiment controller; does not run AI model agents."""
import argparse, base64, json, math, os, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = "experiments/puppy50-autolab/state.json"
NICE = [-10,-9,-11,-8,-12,-7,-13,-6,-5]
ZSTD = [3,2,4,1,5,6,7,8]
# Prioritize a small *structural* experiment before sweeping many numeric knobs.
# Same Firefox priority and Zstd settings; only the libxul read-ahead depth varies.
PREFETCH_LEVELS=(0,32,64,96,128)
PREFETCH_CANDIDATES=[
    {"id":f"nice-10_zstd3_prefetch{mib}", "nice":-10, "zstd":3, "prefetch":mib}
    for mib in PREFETCH_LEVELS
]
CANDIDATES = [{"id": f"nice{n}_zstd{z}", "nice": n, "zstd": z} for n in NICE for z in ZSTD]
CANDIDATES.extend(PREFETCH_CANDIDATES)
BOOTS = {"bios1","uefi1","bios2","uefi2"}

def utc():
    return datetime.now(timezone.utc).isoformat()

def api(method, body=None, path=STATE_PATH):
    token=os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    repo=os.environ["GITHUB_REPOSITORY"]
    if not token: raise RuntimeError("GitHub token missing")
    url=f"https://api.github.com/repos/{repo}/contents/{path}"
    if method=="GET": url+="?ref=puppy50-autolab-state"
    data=None if body is None else json.dumps(body).encode()
    request=urllib.request.Request(url,method=method,data=data,headers={
        "Authorization":f"Bearer {token}","Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28","Content-Type":"application/json",
        "User-Agent":"Puppy50-AutoLab"})
    with urllib.request.urlopen(request,timeout=30) as r: return json.load(r)

def load_state():
    try: obj=api("GET")
    except urllib.error.HTTPError as e:
        if e.code!=404: raise
        return {"schema":1,"started":utc(),"vm_goal_verified":False,
                "vm_goal_candidate":None,"history":[]},None
    return json.loads(base64.b64decode(obj["content"]).decode()),obj["sha"]

def save_state(state,sha):
    content=base64.b64encode((json.dumps(state,indent=2,sort_keys=True)+"\n").encode()).decode()
    obj={"message":"autolab: record real VM experiment [skip ci]",
         "content":content,"branch":"puppy50-autolab-state"}
    if sha: obj["sha"]=sha
    api("PUT",obj)

def trials(state,id):
    return [x for x in state["history"] if x["candidate_id"]==id]

def independently_verified_iso(history, candidate):
    """Return the exact ISO with two successful distinct-run batches, if any.

    A candidate ID describes parameters, not immutable build bytes. Two
    independently executed jobs testing different ISO hashes cannot certify
    the same image. This does not itself publish or review an ISO.
    """
    runs_by_sha={}
    for item in history:
        if (not isinstance(item,dict) or item.get("candidate_id")!=candidate or
                item.get("vm_passed") is not True or item.get("benchmark_timing_schema")!=2):
            continue
        digest=item.get("iso_sha256")
        run=str(item.get("run_id") or "")
        if (not run or not isinstance(digest,str) or len(digest)!=64 or
                any(c not in "0123456789abcdef" for c in digest)):
            continue
        runs_by_sha.setdefault(digest,set()).add(run)
    return next((digest for digest,runs in runs_by_sha.items() if len(runs)>=2),None)

def valid_recorded_goal(state):
    digest=state.get("vm_goal_iso_sha256")
    candidate=state.get("vm_goal_candidate")
    matching=[x for x in state.get("history",[]) if isinstance(x,dict) and x.get("iso_sha256")==digest]
    return bool(state.get("vm_goal_verified") is True and digest and candidate and
                independently_verified_iso(matching,candidate)==digest)

def clear_stale_goal(state):
    """Invalidate old claims without deleting the experiment history."""
    if state.get("vm_goal_verified") is True and not valid_recorded_goal(state):
        state["invalidated_legacy_goal"]={
            "candidate":state.get("vm_goal_candidate"),
            "iso_sha256":state.get("vm_goal_iso_sha256"),
            "reason":"missing two distinct same-ISO runs with timing schema 2"}
        state["vm_goal_verified"]=False
        state["vm_goal_candidate"]=None
        state.pop("vm_goal_iso_sha256",None)
        state.pop("vm_goal_verified_at",None)

def queued_candidates():
    """Only load allowlisted numeric AI hypotheses. Never execute agent code."""
    try:
        obj=api("GET",path="research_lab/queue.json")
        data=json.loads(base64.b64decode(obj["content"]).decode())
    except urllib.error.HTTPError as e:
        if e.code==404: return []
        raise
    found=[]
    allowed={(c["nice"],c["zstd"]):c for c in CANDIDATES
             if "prefetch" not in c}
    for candidate in data.get("candidates",[]):
        if not isinstance(candidate,dict):continue
        n,z=candidate.get("nice"),candidate.get("zstd")
        if type(n) is not int or type(z) is not int:continue
        selected=allowed.get((n,z))
        if selected and selected not in found:found.append(selected)
    return found

def choose(state):
    if valid_recorded_goal(state):
        return None,"VM verification complete; physical verification still required"
    for c in CANDIDATES:
        t=trials(state,c["id"])
        if len(t)==1 and t[0]["vm_passed"]: return c,"repeat promising result on independent run"
    # Test one-variable prefetch hypotheses once each before broad numeric sweeps.
    # Failed hypotheses are not automatically repeated unless they passed once.
    for c in PREFETCH_CANDIDATES:
        if len(trials(state,c["id"]))<2:
            return c,"independent structural prefetch replication and same-host matched control"
    # AI-proposed numeric parameters receive priority, but still obey all VM gates.
    for c in queued_candidates():
        if len(trials(state,c["id"]))<2:
            return c,"research-lab proposed, allowlisted VM candidate"
    pending=[c for c in CANDIDATES if len(trials(state,c["id"]))<2]
    if not pending: return None,"candidate catalog exhausted; new hypotheses required"
    pending.sort(key=lambda c:len(trials(state,c["id"])))
    return pending[0],"next candidate"

def verify(report):
    if not isinstance(report,dict): return False,"no valid VM report"
    if report.get("benchmark_timing_schema")!=2:
        return False,"high-precision frame observation evidence missing"
    f=report.get("first_visible_Firefox_frame_seconds")
    if not isinstance(f,dict) or set(f)!=BOOTS: return False,"missing genuine BIOS/UEFI frame timestamps"
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in f.values()):
        return False,"invalid displayed Firefox frame timestamp"
    upper=report.get("home_frame_observation_upper_seconds")
    if not isinstance(upper,dict) or set(upper)!=BOOTS:
        return False,"missing host-monotonic frame-observation upper bounds"
    if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<v<5 for v in upper.values()):
        return False,"not all frame observation upper bounds strictly below five seconds"
    if any(abs(f[k]-upper[k])>0.02 for k in BOOTS):
        return False,"frame timestamps disagree with observation evidence"
    for key in ("checksum_verified_whole_root_in_RAM_all_four",
                "virtual_CD_removed_after_RAM_all_four",
                "original_Zstd_root_and_full_RAM_recovery_preserved",
                "all_four_real_Firefox_under_five_seconds"):
        if report.get(key) is not True: return False,key+" not verified"
    if report.get("real_browser_HTTP200_receipts_after_CD_removal")!=4:
        return False,"four real browser post-eject HTTP200 receipts missing"
    h=report.get("sha256","")
    if not isinstance(h,str) or len(h)!=64 or any(x not in "0123456789abcdef" for x in h):
        return False,"candidate ISO SHA256 missing"
    return True,"passed four cold BIOS/UEFI boots, all functional gates"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("plan","record"))
    p.add_argument("--candidate",default="")
    p.add_argument("--run-id",default=os.getenv("GITHUB_RUN_ID",""))
    p.add_argument("--success",default="false",choices=("true","false"))
    p.add_argument("--report",default="")
    p.add_argument("--partial",default="")
    a=p.parse_args()
    state,sha=load_state()
    if a.mode=="plan":
        c,reason=choose(state)
        info={"should_run":bool(c),"candidate":c,"reason":reason,
              "prior_experiments":len(state["history"])}
        output={"should_run":str(bool(c)).lower(),
                "candidate_id":c["id"] if c else "none",
                "nice":c["nice"] if c else -10,"zstd":c["zstd"] if c else 3,
                "prefetch":c.get("prefetch",256) if c else 256}
        with open(os.environ["GITHUB_OUTPUT"],"a") as out:
            for k,v in output.items(): print(f"{k}={v}",file=out)
    else:
        clear_stale_goal(state)
        if a.candidate not in {c["id"] for c in CANDIDATES}:
            raise ValueError("unknown candidate")
        if not a.run_id: raise ValueError("missing GitHub run id")
        if any(str(x["run_id"])==str(a.run_id) for x in state["history"]):
            info={"recorded":False,"reason":"already recorded"}
        else:
            try: report=json.loads(Path(a.report).read_text())
            except (OSError,ValueError): report=None
            try: partial=json.loads(Path(a.partial).read_text())
            except (OSError,ValueError): partial=None
            passed,reason=verify(report) if a.success=="true" else (False,"build/VM tests failed")
            # Partial results provide useful failure feedback; they NEVER confer pass.
            if not passed and isinstance(partial,dict):
                obs=partial.get("observed_frames",{})
                if isinstance(obs,dict) and obs:
                    vals=[float(v) for v in obs.values()
                          if type(v) in (int,float) and 0<float(v)<600]
                    if vals:
                        reason=(reason+"; observed "+str(len(vals))+"/4 frames, "+
                                "worst "+str(round(max(vals),3))+"s; "+
                                str(len(partial.get("vm_failures",{})))+
                                " functional diagnostics; NOT a passing VM experiment")
            entry={"at":utc(),"run_id":str(a.run_id),"candidate_id":a.candidate,
                   "vm_passed":passed,"reason":reason,
                   "frames":(report.get("first_visible_Firefox_frame_seconds")
                             if isinstance(report,dict) else
                             (partial.get("observed_frames") if isinstance(partial,dict) else None)),
                   "vm_diagnostics":(partial.get("vm_failures") if isinstance(partial,dict) else None),
                   "ram_ready_seconds":(partial.get("ram_ready_seconds") if isinstance(partial,dict) else None),
                   "post_eject_http200_by_boot":(partial.get("post_eject_http200_by_boot") if isinstance(partial,dict) else None),
                   "iso_sha256":report.get("sha256") if isinstance(report,dict) else None,
                   "benchmark_timing_schema":report.get("benchmark_timing_schema") if isinstance(report,dict) else None,
                   "home_frame_observation_upper_seconds":report.get("home_frame_observation_upper_seconds") if isinstance(report,dict) else None,
                   "matched_prefetch_control":(report.get("matched_prefetch_control")
                      if isinstance(report,dict) else None)}
            state["history"].append(entry)
            verified_sha=independently_verified_iso(state["history"],a.candidate)
            if verified_sha:
                state["vm_goal_verified"]=True
                state["vm_goal_candidate"]=a.candidate
                state["vm_goal_iso_sha256"]=verified_sha
                state["vm_goal_verified_at"]=utc()
            save_state(state,sha)
            info={"recorded":True,"passed":passed,
                  "vm_goal_verified":state["vm_goal_verified"],
                  "experiments_recorded":len(state["history"]),"reason":reason}
    print(json.dumps(info,indent=2))
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as out:
            print("## Puppy50 AutoLab "+a.mode+"\n\n```json\n"+json.dumps(info,indent=2)+"\n```",file=out)

if __name__=="__main__": main()
