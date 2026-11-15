#!/usr/bin/env python3
"""Smoke-test real, LOCAL Qwen text inference on one bounded GitHub CPU runner.

No secrets, no paid model requests, no repo writes, no code execution from model.
This is a *connectivity/JSON* test of a tiny 0.8B model, not OS engineering.
"""
import argparse
import json
from pathlib import Path
import time
import urllib.request
from datetime import datetime, timezone

from lab import parse_model_json, validate

BASE="http://127.0.0.1:8080"
MODEL="Qwen3.5-0.8B-Q4_K_M.gguf"

def request(path, payload=None, timeout=65):
    url=BASE+path
    data=None if payload is None else json.dumps(payload).encode("utf-8")
    req=urllib.request.Request(
        url, data=data, method=("POST" if data else "GET"),
        headers={"Content-Type":"application/json","User-Agent":"Puppy50-Qwen-Local-Smoke/1"})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        return json.load(response)

def run():
    started=time.monotonic()
    deadline=started+120
    while True:
        try:
            health=request("/health",timeout=4)
            if health.get("status")=="ok": break
        except Exception:
            pass
        if time.monotonic()>deadline:
            raise RuntimeError("Local Qwen inference did not become healthy in 120s")
        time.sleep(2)
    calls=[]
    for role, instruction in [
        ("researcher","You are an OS boot optimization researcher. Return a short JSON object "
           "with exactly these fields: nice=-10, zstd=3, "
           'hypothesis="Preserve Firefox networking and test real firmware boot times." '
           "No markdown, no other text."),
        ("safety-reviewer","You independently check an untrusted OS optimization hypothesis. "
           'Return ONLY JSON with approve=true and reason="Retain boot recovery and verify evidence." '
           "Do not claim anything was tested.")
    ]:
        payload={"model":MODEL,"stream":False,"temperature":0.0,
                 "max_tokens":180,
                 "messages":[
                     {"role":"system","content":"Provide concise plain JSON only. No hidden reasoning in final."},
                     {"role":"user","content":instruction}],
                 "chat_template_kwargs":{"enable_thinking":False}}
        tick=time.monotonic()
        result=request("/v1/chat/completions",payload,timeout=100)
        content=result.get("choices",[{}])[0].get("message",{}).get("content","")
        if not isinstance(content,str) or len(content.strip())<2:
            raise RuntimeError("Real Qwen returned no nonempty answer")
        record={"role":role,"seconds":round(time.monotonic()-tick,2),
                "model_response":content[:1800],
                "reply_received":True,"parsed_json":False,
                "strict_validation":False}
        try:
            obj=parse_model_json(content)
            record["parsed_json"]=True
            if role=="researcher":
                p=validate(obj)
                record["strict_validation"]=(p["nice"],p["zstd"])==(-10,3)
                record["proposal"]=p
            else:
                record["strict_validation"]=obj.get("approve") is True and isinstance(obj.get("reason"),str)
        except (ValueError,TypeError,KeyError):
            pass
        calls.append(record)
    return {"timestamp":datetime.now(timezone.utc).isoformat(),
            "backend":"real local llama.cpp inference, CPU-only",
            "model_source":"axteam/Qwen3.5-0.8B-GGUF",
            "model_id":MODEL,
            "independent_model_requests":len(calls),
            "real_text_inference_confirmed":all(x["reply_received"] for x in calls),
            "strict_agent_json_confirmed":all(x["strict_validation"] for x in calls),
            "actual_iso_boots":0,
            "not_a_27B_model":True,
            "not_128_parallel_agents":True,
            "call_results":calls,
            "wall_seconds":round(time.monotonic()-started,2)}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="cpu-smoke-results/smoke.json")
    args=p.parse_args()
    result=run()
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="call_results"},indent=2))
    print("Saved:",out)
