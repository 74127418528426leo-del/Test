#!/usr/bin/env python3
"""Bounded local Qwen-Coder code-generation smoke test; never execute output."""
import argparse
import ast
import json
import re
import time
import urllib.request
from pathlib import Path


TASKS = [
    {"id":"strict_time", "prompt":
     "Write exactly one Python function below_five(seconds). For an ordinary "
     "finite numeric input, return whether seconds is strictly greater than 0 "
     "and strictly less than 5. Output only the function.",
     "expected":"def below_five(seconds):\n    return 0 < seconds < 5\n"},
    {"id":"hash_identity", "prompt":
     "Write exactly one Python function same_iso(first, second). The inputs are "
     "already validated SHA-256 strings. Return whether they are equal. "
     "Output only the function.",
     "expected":"def same_iso(first, second):\n    return first == second\n"},
    {"id":"paired_difference", "prompt":
     "Write exactly one Python function improvement(control, candidate). "
     "Return control minus candidate; both are same-clock numeric timings. "
     "Output only the function.",
     "expected":"def improvement(control, candidate):\n    return control - candidate\n"},
]


def inspect_response(text, expected):
    result = {"valid_python":False,"exact_ast_match":False,"model_code_executed":False}
    if not isinstance(text,str) or len(text)>8192:
        return result
    text = text.strip()
    fenced = re.fullmatch(r"```(?:python)?\s*\n(.*?)\n```", text, re.S | re.I)
    if fenced:
        text = fenced.group(1)
    try:
        parsed = ast.parse(text)
        wanted = ast.parse(expected)
    except (SyntaxError,ValueError,MemoryError,RecursionError):
        return result
    result["valid_python"] = True
    # This deliberately recognizes only one exact safe syntax tree. Correct
    # alternatives are unrecognized, not proof of a wrong implementation.
    result["exact_ast_match"] = ast.dump(parsed,include_attributes=False)==ast.dump(wanted,include_attributes=False)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    records=[]
    for task in TASKS:
        payload={"model":"p50-coder", "stream":False,"temperature":0,
                 "max_tokens":160,"messages":[
                   {"role":"system","content":"Return only the requested Python function."},
                   {"role":"user","content":task["prompt"]}]}
        request=urllib.request.Request("http://127.0.0.1:8088/v1/chat/completions",
             data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
        start=time.monotonic()
        record={"task":task["id"],"reply_received":False,"model_code_executed":False}
        try:
            with urllib.request.urlopen(request,timeout=120) as response:
                data=json.load(response)
            text=data["choices"][0]["message"]["content"]
            record.update(inspect_response(text,task["expected"]))
            record["reply_received"]=isinstance(text,str) and bool(text.strip())
            record["response"]=text[:8192] if isinstance(text,str) else None
        except (OSError,ValueError,KeyError,IndexError,TypeError) as exc:
            record["error_type"]=type(exc).__name__
        record["seconds"]=round(time.monotonic()-start,3)
        records.append(record)
    summary={"model":"Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF Q4_K_M",
             "model_sha256":"cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046",
             "inference":"actual local CPU inference via llama.cpp",
             "tasks":records,"model_code_executed":False,
             "limitation":"Three tiny exact-AST probes; unrecognized alternatives may be correct. "
                          "Not an OS engineering capability benchmark or autonomous agent proof."}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({"responses":sum(r["reply_received"] for r in records),
                      "exact_ast_matches":sum(r.get("exact_ast_match",False) for r in records),
                      "model_code_executed":False},indent=2))
    if not all(r["reply_received"] for r in records):
        raise SystemExit("one or more local model requests failed")


if __name__=="__main__":
    main()
