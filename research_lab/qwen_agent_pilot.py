#!/usr/bin/env python3
"""One-file, read-only Qwen-Agent integration pilot for Puppy50 evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
from urllib.parse import urlsplit

TOOL_NAME = "p50_read_review_input"
PACKET_NAME = "review-input.json"
MAX_PACKET_BYTES = 4096
MAX_TOOL_CALLS = 1
MAX_LLM_CALLS = 3
MAX_OUTPUT_TOKENS = 512
MODEL_ID = "p50-qwen35-review"
EXPECTED_TEST_SUMMARY = "Offline regression and shell syntax checks passed."
EXPECTED_LIMITATION = (
    "One same-host run; sampled page detection, not exact first Firefox frame; "
    "independent replication required."
)
SYSTEM_MESSAGE = (
    "You are a read-only evidence reviewer. Call p50_read_review_input exactly "
    "once with path review-input.json; this call is required. After the tool "
    "returns, copy all six values exactly into one minified raw JSON object with "
    "keys run_id, candidate_mean_seconds, control_mean_seconds, goal_verified, "
    "test_summary, limitation. Output no explanation, markdown, or invented "
    "facts. Do not call another tool. The packet does not certify a Puppy50 boot."
)


def _parse_tool_args(params: str | dict) -> dict:
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError as exc:
            raise ValueError("tool arguments must be JSON") from exc
    if not isinstance(params, dict):
        raise ValueError("tool arguments must be an object")
    if set(params) != {"path"} or params.get("path") != PACKET_NAME:
        raise ValueError("tool may read only review-input.json")
    return params


def safe_read_review_packet(root: str | Path, params: str | dict,
                            audit: list[dict], max_calls: int = MAX_TOOL_CALLS) -> str:
    """Read one fixed regular file, recording allowed and denied tool attempts."""
    if isinstance(params, dict):
        shown_path = params.get("path", "<missing>")
    elif isinstance(params, str):
        shown_path = params[:120]
    else:
        shown_path = f"<{type(params).__name__}>"
    event = {
        "call": len(audit) + 1,
        "tool": TOOL_NAME,
        "path": shown_path,
        "status": "denied",
    }
    audit.append(event)
    if event["call"] > max_calls:
        raise ValueError("tool call limit exceeded")
    _parse_tool_args(params)

    base = Path(root).resolve(strict=True)
    target = base / PACKET_NAME
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(target, flags)
    except OSError as exc:
        raise ValueError("review packet is unavailable or is a symlink") from exc
    with os.fdopen(fd, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("review packet must be a regular file")
        raw = stream.read(MAX_PACKET_BYTES + 1)
    if len(raw) > MAX_PACKET_BYTES:
        raise ValueError("review packet exceeds the byte limit")
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("review packet is not UTF-8") from exc
    event.update({
        "status": "read",
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    })
    return content


def parse_model_report(response: str) -> dict:
    """Accept a raw JSON object with optional Qwen think/JSON labels only."""
    if not isinstance(response, str):
        raise ValueError("Qwen final response must be text")
    text = response.strip()
    if text.startswith("<think>"):
        end = text.find("</think>")
        if end < 0:
            raise ValueError("unterminated Qwen think block")
        text = text[end + len("</think>"):].strip()
    if text[:4].lower() == "json" and text[4:].lstrip().startswith("{"):
        text = text[4:].lstrip()
    try:
        report = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Qwen final response is not one raw JSON object") from exc
    if not isinstance(report, dict):
        raise ValueError("Qwen final response must be a JSON object")
    return report


def validate_agent_run(report: dict, audit: list[dict], state: dict) -> dict:
    """Require one successful real tool read and exact consistency with state."""
    if len(audit) != 1:
        raise ValueError(f"expected exactly one tool execution; observed {len(audit)}")
    event = audit[0]
    if (event.get("tool") != TOOL_NAME or event.get("path") != PACKET_NAME
            or event.get("status") != "read"):
        raise ValueError("Qwen-Agent did not read the fixed review packet successfully")
    # Reuse the repository's deterministic, fail-closed evidence validator.
    from hermes_review_gate import validate_report

    verified = validate_report(report, state, tool_calls=1)
    verified["scope"] = (
        "Qwen-Agent consistency check only; it does not independently reproduce "
        "or certify a Puppy50 boot."
    )
    return verified


def _content_text(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            item.get("text", "") for item in content
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        )
    raise ValueError("final assistant message has no text content")


def _require_loopback_endpoint(base_url: str) -> None:
    parsed = urlsplit(base_url)
    if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
            or parsed.path != "/v1" or parsed.username or parsed.password
            or parsed.query or parsed.fragment):
        raise ValueError("Qwen-Agent endpoint must be plain HTTP on 127.0.0.1/v1")


def resolve_packet_root(packet: str | Path) -> Path:
    """Reject a packet symlink before deriving the only readable directory."""
    path = Path(packet)
    if path.name != PACKET_NAME or path.is_symlink():
        raise ValueError("packet must be a regular review-input.json, not a symlink")
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("review packet must be a regular file")
    root = path.parent.resolve(strict=True)
    if path.resolve(strict=True) != root / PACKET_NAME:
        raise ValueError("review packet resolved outside its fixed parent")
    return root


def summarize_agent_messages(messages: list) -> dict:
    """Keep only bounded diagnostics needed to explain a failed model turn."""
    roles = []
    tool_names = []
    assistant_preview = ""
    for message in messages:
        if not isinstance(message, dict):
            continue
        roles.append(str(message.get("role", ""))[:32])
        calls = message.get("tool_calls")
        if isinstance(calls, list):
            for call in calls:
                function = call.get("function") if isinstance(call, dict) else None
                name = function.get("name") if isinstance(function, dict) else None
                if isinstance(name, str):
                    tool_names.append(name[:80])
        legacy = message.get("function_call")
        if isinstance(legacy, dict) and isinstance(legacy.get("name"), str):
            tool_names.append(legacy["name"][:80])
        if message.get("role") == "assistant":
            try:
                assistant_preview = _content_text(message)[:512]
            except ValueError:
                pass
    return {
        "message_roles": roles[:12],
        "model_tool_call_names": tool_names[:4],
        "assistant_final_preview": assistant_preview,
        "assistant_preview_truncated": len(assistant_preview) == 512,
    }


def run_agent(base_url: str, packet: Path, state: dict, diagnostics: dict | None = None) -> dict:
    """Run pinned Qwen-Agent against local Qwen with one credential-free tool."""
    _require_loopback_endpoint(base_url)
    packet_root = resolve_packet_root(packet)
    from qwen_agent.agents import Assistant
    from qwen_agent.agents import fncall_agent as fncall_module
    from qwen_agent.tools.base import BaseTool

    # The pinned Qwen-Agent framework defaults to many model/tool turns. Limit
    # this experimental worker to three local completions and one tool call.
    fncall_module.MAX_LLM_CALL_PER_RUN = MAX_LLM_CALLS
    audit: list[dict] = []
    if diagnostics is not None:
        diagnostics["tool_events"] = audit

    class ReviewInputTool(BaseTool):
        name = TOOL_NAME
        description = "Read the fixed, read-only Puppy50 review packet once."
        parameters = [{
            "name": "path",
            "type": "string",
            "description": "Must be exactly review-input.json.",
            "required": True,
        }]

        def call(self, params, **kwargs):
            return safe_read_review_packet(packet_root, params, audit)

    llm_cfg = {
        "model": MODEL_ID,
        "model_type": "oai",
        "model_server": base_url,
        "api_key": "local-cpu-only",
        "generate_cfg": {
            "temperature": 0,
            "top_p": 0.1,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "max_input_tokens": 8192,
            "reasoning_effort": "none",
            "use_raw_api": False,
        },
    }
    bot = Assistant(
        llm=llm_cfg,
        function_list=[ReviewInputTool()],
        system_message=SYSTEM_MESSAGE,
        name="Puppy50 bounded evidence reviewer",
    )
    chunks = list(bot.run(messages=[{
        "role": "user",
        "content": "Read the review packet with your tool and return the required JSON.",
    }], seed=42, lang="en"))
    if not chunks or not isinstance(chunks[-1], list):
        raise ValueError("Qwen-Agent returned no final message list")
    messages = chunks[-1]
    if diagnostics is not None:
        diagnostics.update(summarize_agent_messages(messages))
    calls = [m for m in messages if isinstance(m, dict) and m.get("role") == "function"]
    if len(calls) != len(audit):
        raise ValueError("Qwen-Agent function messages do not match executed tool calls")
    assistant_messages = [
        m for m in messages if isinstance(m, dict) and m.get("role") == "assistant"
    ]
    if not assistant_messages:
        raise ValueError("Qwen-Agent returned no assistant response")
    final_text = _content_text(assistant_messages[-1])
    if diagnostics is not None:
        diagnostics["assistant_final_preview"] = final_text[:512]
        diagnostics["assistant_preview_truncated"] = len(final_text) > 512
    report = parse_model_report(final_text)
    verified = validate_agent_run(report, audit, state)
    return {
        "passed": True,
        "framework": "Qwen-Agent",
        "model": MODEL_ID,
        "endpoint": base_url,
        "max_tool_calls": MAX_TOOL_CALLS,
        "max_llm_calls": MAX_LLM_CALLS,
        "assistant_messages": len(assistant_messages),
        "tool_events": audit,
        "report": report,
        "validation": verified,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    diagnostics = {}
    try:
        state = json.loads(args.state.read_text(encoding="utf-8"))
        evidence = run_agent(args.base_url, args.packet, state, diagnostics)
        code = 0
    except Exception as exc:
        evidence = {
            "passed": False,
            "framework": "Qwen-Agent",
            "model": MODEL_ID,
            "error_type": type(exc).__name__,
            "error": str(exc)[:360],
            "diagnostics": diagnostics,
        }
        code = 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(evidence, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
