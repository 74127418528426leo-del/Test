#!/usr/bin/env python3
"""Aggregate exact 4×32 REAL model-call receipts; reject missing/duplicate shards."""
import argparse,hashlib,json
from pathlib import Path
from collections import Counter
from lab import task_grid

def aggregate(root):
    paths=sorted(Path(root).rglob("batch128.json"))
    if len(paths)!=4:
        raise ValueError("expected four independent 32-task evidence bundles, got "+str(len(paths)))
    reports=[json.loads(p.read_text()) for p in paths]
    if {r.get("shard_index") for r in reports}!={0,1,2,3}:
        raise ValueError("wrong or repeated shard indices")
    if any(r.get("shard_count")!=4 for r in reports):
        raise ValueError("not 4-server distributed experiment")
    all_results=[]
    for r in reports:
        records=r.get("results",[])
        if len(records)!=32 or r.get("real_cpu_model_requests_attempted")!=32:
            raise ValueError("a worker did not attempt 32 requests")
        if sum(x.get("model_response_received") is True for x in records)!=32:
            raise ValueError("model request missing or empty on worker")
        all_results.extend(records)
    got=[x.get("task_id") for x in all_results]
    expected={x["task_id"] for x in task_grid()}
    if len(got)!=128 or len(set(got))!=128 or set(got)!=expected:
        raise ValueError("missing/duplicate/relabelled task IDs")
    strict=sum(x.get("valid_safe_json") is True for x in all_results)
    summary={
        "actual_independent_gitHub_runner_jobs":4,
        "real_open_weight_qwen_model_requests":128,
        "distinct_research_task_identifiers":128,
        "strict_allowlisted_json_proposals":strict,
        "gpu_servers":0,
        "model":"Qwen3.5-0.8B-Q4_K_M.gguf",
        "not_independent_persistent_agents":True,
        "no_real_iso_boot_in_this_batch":True,
        "all_four_shards_checked":True,
        "roles":dict(Counter(x["role"] for x in all_results)),
        "evidence":[{"shard":r["shard_index"],
                     "sha256":hashlib.sha256(paths[i].read_bytes()).hexdigest(),
                     "model_answers":r["model_responses_received"]}
                     for i,r in enumerate(reports)]
    }
    return summary
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",default="evidence")
    p.add_argument("--output",default="aggregate-results/verified128.json")
    a=p.parse_args()
    report=aggregate(a.root)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
