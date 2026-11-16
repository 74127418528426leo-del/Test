#!/usr/bin/env python3
"""Bounded, non-executing Qwen tool-call compatibility probe."""
import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

TOOL = "p50_read_probe_file"
PATH = "probe.txt"
LIMIT = 128


def payload():
    return {
        "model": "p50-qwen35-review",
        "messages": [
            {"role": "system", "content":
             "Tool compatibility test: call the provided function exactly once "
             "with path probe.txt. It is fictional and must not be executed."},
            {"role": "user", "content": "Request the probe fixture. Return no prose."},
        ],
        "tools": [{
            "type": "function",
            "function": {
                "name": TOOL,
                "description": "Request a harmless test fixture.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string", "enum": [PATH]}},
                    "required": ["path"],
                    "additionalProperties": False,
                },
            },
        }],
        "tool_choice": {"type": "function", "function": {"name": TOOL}},
        "parallel_tool_calls": False,
        "temperature": 0,
        "max_tokens": LIMIT,
        "reasoning_effort": "none",
    }


def parse_response(data):
    choices = data.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("expected exactly one model choice")
    msg = choices[0].get("message")
    calls = msg.get("tool_calls") if isinstance(msg, dict) else None
    if not isinstance(calls, list) or len(calls) != 1:
        raise ValueError("no single OpenAI-style tool call returned")
    fn = calls[0].get("function")
    if not isinstance(fn, dict) or fn.get("name") != TOOL:
        raise ValueError("wrong tool name")
    args = fn.get("arguments")
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError as exc:
            raise ValueError("tool arguments are invalid JSON") from exc
    if args != {"path": PATH}:
        raise ValueError("tool arguments differ from the bounded probe")
    return {"name": TOOL, "arguments": args}


def get_json(url, data=None, timeout=60):
    request = Request(
        url,
        data=None if data is None else json.dumps(data).encode(),
        headers={} if data is None else {"Content-Type": "application/json"},
        method="GET" if data is None else "POST",
    )
    with urlopen(request, timeout=timeout) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError("server returned non-object JSON")
    return value


def template_capabilities(props):
    if not isinstance(props, dict):
        props = {}
    return {
        "chat_template_available": bool(props.get("chat_template")),
        "tool_template_available": bool(props.get("chat_template_tool_use")),
    }


def probe(base_url):
    base = base_url.rstrip("/")
    info = {"chat_template_available": False, "tool_template_available": False}
    try:
        props = get_json(base + "/props", timeout=10)
        info.update(template_capabilities(props))
    except Exception as exc:
        info["props_error"] = type(exc).__name__
    call = parse_response(get_json(base + "/v1/chat/completions", payload()))
    return {
        "passed": True, **info,
        "returned_tool": call["name"], "returned_arguments": call["arguments"],
        "tool_executed": False, "max_tokens": LIMIT,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    try:
        result, code = probe(a.base_url), 0
    except Exception as exc:
        result = {"passed": False, "error_type": type(exc).__name__,
                  "error": str(exc)[:240], "tool_executed": False, "max_tokens": LIMIT}
        code = 1
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
