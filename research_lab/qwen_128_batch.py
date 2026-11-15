#!/usr/bin/env python3
"""128 real small-Qwen requests, safely bounded. NOT 128 GPU agents or VM boots."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,statistics,time,urllib.request,urllib.error
from lab import task_grid,parse_model_json,validate

URL="http://127.0.0.1:8080/v1/chat/completions"
MODEL="Qwen3.5-0.8B-Q4_K_M.gguf"
SYSTEM=("You are one of 128 independent Puppy50 research task workers. "
        "Return ONLY one JSON object with integer nice from [-10,-9,-11,-8,-12,-7,-13,-6,-5], "
        "integer zstd from [3,2,4,1,5,6,7,8], and hypothesis of 8-150 characters. "
        "Do not claim any completed OS boot or validated speedup. Do not output commands or markdown.")
def send(task):
    start=time.monotonic()
    payload={
        "model":MODEL,"temperature":0,"max_tokens":130,"stream":False,
        "chat_template_kwargs":{"enable_thinking":False},
        "messages":[{"role":"system","content":SYSTEM},
                    {"role":"user","content":
                        f"Task {task['task_id']} (role {task['role']}, independent hypothesis "
                        f"{task['slot']}/16). Suggest safe actual-VM comparative experiment "
                        "using only the allowed numeric settings."}]
    }
    try:
        req=urllib.request.Request(URL,data=json.dumps(payload).encode(),method="POST",
                                   headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=70) as response:
            result=json.load(response)
        message=result["choices"][0]["message"]["content"]
        if not isinstance(message,str) or not message.strip():
            raise ValueError("model output empty")
        record={"task_id":task["task_id"],"role":task["role"],
            "model_response_received":True,"valid_safe_json":False,
            "latency_seconds":round(time.monotonic()-start,3)}
        try:
            proposal=validate(parse_model_json(message))
            record["proposal"]=proposal
            record["valid_safe_json"]=True
        except (ValueError,TypeError,KeyError) as e:
            record["validation_error"]=str(e)[:160]
            record["excerpt"]=message[:260]
        return record
    except (OSError,ValueError,TypeError,KeyError,IndexError) as e:
        return {"task_id":task["task_id"],"role":task["role"],
                "model_response_received":False,"valid_safe_json":False,
                "latency_seconds":round(time.monotonic()-start,3),
                "error":type(e).__name__+": "+str(e)[:200]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--parallel",type=int,default=4)
    p.add_argument("--shard-index",type=int,default=0)
    p.add_argument("--shard-count",type=int,default=1)
    p.add_argument("--output",default="cpu-smoke-results/batch128.json")
    a=p.parse_args()
    if not 1<=a.parallel<=4:raise SystemExit("parallel capped at four CPU request slots")
    all_tasks=task_grid()
    if len(all_tasks)!=128 or len({x["task_id"] for x in all_tasks})!=128:raise AssertionError("bad grid")
    if not 1<=a.shard_count<=8 or not 0<=a.shard_index<a.shard_count:
        raise SystemExit("invalid bounded worker shard")
    tasks=all_tasks[a.shard_index::a.shard_count]
    started=time.monotonic()
    with ThreadPoolExecutor(max_workers=a.parallel) as pool:
        records=list(pool.map(send,tasks))
    received=sum(x["model_response_received"] for x in records)
    valid=sum(x["valid_safe_json"] for x in records)
    roles=dict(Counter(x["role"] for x in records if x["valid_safe_json"]))
    stats={
        "utc":datetime.now(timezone.utc).isoformat(),
        "model":MODEL,
        "real_cpu_model_requests_attempted":len(records),
        "shard_index":a.shard_index,"shard_count":a.shard_count,
        "total_logical_research_slots":len(all_tasks),
        "model_responses_received":received,
        "safe_strict_json_responses":valid,
        "attempted_parallel_slots":a.parallel,
        "roles":roles,
        "wall_seconds":round(time.monotonic()-started,2),
        "tasks_per_second":round(len(records)/max(.001,time.monotonic()-started),3),
        "latency_p50_seconds":round(statistics.median(x["latency_seconds"] for x in records),3),
        "actual_gpu_instances":0,"actual_puppy50_iso_boots":0,
        "not_128_independent_model_instances":True,
        "results":records}
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(stats,indent=2)+"\n")
    print(json.dumps({k:v for k,v in stats.items() if k!="results"},indent=2))
    if received!=len(tasks):
        raise SystemExit(f"Only {received}/{len(tasks)} actual model responses; investigation required")
    print(f"ALL {len(tasks)} REAL QWEN MODEL REQUESTS ANSWERED (shard {a.shard_index}/{a.shard_count}); strict JSON:",valid)
if __name__=="__main__":main()
