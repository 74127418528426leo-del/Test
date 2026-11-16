#!/usr/bin/env python3
"""Fail-closed validation of a bounded Hermes report against durable Puppy50 state."""
from __future__ import annotations
import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
FOOTER = re.compile(r"(?m)^\s*Messages:\s*\d+\s*\(\s*\d+\s+user,\s*(\d+)\s+tool calls?\s*\)\s*$")
BANNER = re.compile(r"(?m)^\s*☤\s+Hermes\s*$")
SUCCESSFUL_READ = re.compile(
    r"(?m)^\s*📖\s+Read\s+.*\breview-input\.json\b", re.IGNORECASE
)
SEPARATOR = re.compile(r"(?m)^\s*[─━]{8,}\s*$")
MINIMUM_FILE_TOOL_CALLS = 1
EXPECTED_TEST_SUMMARY = "Offline regression and shell syntax checks passed."
EXPECTED_LIMITATION = "One same-host run; sampled page detection, not exact first Firefox frame; independent replication required."
FIELDS = {
    "run_id", "candidate_mean_seconds", "control_mean_seconds",
    "goal_verified", "test_summary", "limitation",
}


def latest_matched_comparison(state: dict[str, Any]) -> dict[str, Any]:
    if type(state.get("vm_goal_verified")) is not bool:
        raise ValueError("persistent state has no boolean vm_goal_verified field")
    history = state.get("history")
    if not isinstance(history, list):
        raise ValueError("persistent state has no history list")
    rows = [
        row for row in history
        if isinstance(row, dict) and isinstance(row.get("matched_prefetch_control"), dict)
    ]
    if not rows:
        raise ValueError("persistent state has no completed matched comparison")
    row = rows[-1]
    comparison = row["matched_prefetch_control"]
    run_id = row.get("run_id")
    candidate = comparison.get("mean_candidate_seconds")
    control = comparison.get("mean_control_seconds")
    if not isinstance(run_id, (str, int)) or isinstance(run_id, bool) or not str(run_id):
        raise ValueError("latest matched comparison has no valid run ID")
    for name, value in (("candidate", candidate), ("control", control)):
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"latest matched comparison has invalid {name} mean")
    return {
        "run_id": str(run_id),
        "candidate_mean_seconds": float(candidate),
        "control_mean_seconds": float(control),
        "goal_verified": state["vm_goal_verified"],
    }


def parse_hermes_transcript(transcript: str) -> tuple[dict[str, Any], int]:
    clean = ANSI.sub("", transcript)
    footers = list(FOOTER.finditer(clean))
    if not footers:
        raise ValueError("Hermes transcript has no authentic message/tool-call footer")
    calls = int(footers[-1].group(1))
    if calls < MINIMUM_FILE_TOOL_CALLS:
        raise ValueError(f"expected at least {MINIMUM_FILE_TOOL_CALLS} file-tool call; observed {calls}")
    if not SUCCESSFUL_READ.search(clean):
        raise ValueError("Hermes did not successfully read the bounded review packet")
    banners = list(BANNER.finditer(clean))
    if not banners:
        raise ValueError("Hermes transcript has no final-response banner")
    response = SEPARATOR.split(clean[banners[-1].end():], maxsplit=1)[0].strip()
    # Hermes may add a bare JSON language label before otherwise-valid JSON.
    if response[:4].lower() == "json" and response[4:].lstrip().startswith("{"):
        response = response[4:].lstrip()
    if not response:
        raise ValueError("Hermes final response is empty")
    # Qwen sometimes emits this exact escaped-object form through Hermes. Remove
    # the extra quote and unescape JSON delimiters, then apply the usual strict schema/value checks.
    if response.startswith('{"\\"run_id\\"'):
        response = response[:1] + response[2:].replace('\\"', '"')
    try:
        report = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Hermes final response is not one raw JSON object: {exc.msg}") from exc
    if not isinstance(report, dict):
        raise ValueError("Hermes final response must be a JSON object")
    return report, calls


def validate_report(report: dict[str, Any], state: dict[str, Any], tool_calls: int) -> dict[str, Any]:
    if tool_calls < MINIMUM_FILE_TOOL_CALLS:
        raise ValueError(f"expected at least {MINIMUM_FILE_TOOL_CALLS} file-tool call; observed {tool_calls}")
    if set(report) != FIELDS:
        raise ValueError(
            f"report fields mismatch (missing={sorted(FIELDS-set(report))}, "
            f"extra={sorted(set(report)-FIELDS)})"
        )
    expected = latest_matched_comparison(state)
    if str(report["run_id"]) != expected["run_id"]:
        raise ValueError("reported run ID does not match the latest completed matched comparison")
    for key in ("candidate_mean_seconds", "control_mean_seconds"):
        value = report[key]
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"reported {key} is not a finite number")
        if not math.isclose(float(value), expected[key], rel_tol=0.0, abs_tol=0.001):
            raise ValueError(f"reported {key} does not match persistent state")
    if type(report["goal_verified"]) is not bool:
        raise ValueError("reported goal_verified is not a boolean")
    if report["goal_verified"] is not expected["goal_verified"]:
        raise ValueError("reported goal flag does not match persistent state")
    if report["test_summary"] != EXPECTED_TEST_SUMMARY:
        raise ValueError("report does not match the completed offline regression checks")
    if report["limitation"] != EXPECTED_LIMITATION:
        raise ValueError("report omits or changes the required timing/replication limitation")
    if len(re.findall(r"\b[\w'-]+\b", " ".join(
        str(report[key]) for key in ("test_summary", "limitation")
    ))) > 100:
        raise ValueError("report exceeds the 100-word output limit")
    return {
        **expected,
        "agent_tool_calls": tool_calls,
        "agent_report_consistent": True,
        "test_summary": report["test_summary"],
        "limitation": report["limitation"],
        "scope": "Hermes consistency check only; it does not independently reproduce or certify a Puppy50 boot.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        transcript = Path(args.transcript).read_text(errors="replace")
        state = json.loads(Path(args.state).read_text())
        report, calls = parse_hermes_transcript(transcript)
        verified = validate_report(report, state, calls)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(1, f"REJECTED Hermes evidence report: {exc}\n")
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(verified, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verified, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
