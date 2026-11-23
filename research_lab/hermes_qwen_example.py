"""Ask Hermes and Qwen to implement the VM scheduler and grade the submission."""

import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from uuid import uuid4

from hermes_qwen_runtime import BASE_URL, MODEL, local_hermes_profile

EXAMPLE = Path(__file__).resolve().with_name("coding_example")
TOOL = "read_project"
IMAGE = "python:3.12-slim@sha256:05a994d2344eb364cc186910f4fc8786a38215f39f00d0acc25bff33a08f4177"
RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "scheduler_submission",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {"source": {"type": "string"}},
            "required": ["source"],
            "additionalProperties": False,
        },
    },
}
SYSTEM_PROMPT = """Implement the Puppy50 VM test scheduler in Python.
Call read_project with part "brief" to get the requirements and any grader feedback.
Return only a JSON object with one field, "source", containing the complete Python
module as plain text. Use no imports, no decorators, and no executable code at
module scope. Keep the solution concise. If the grader provided feedback, fix it.
"""


def generate_source(brief, feedback):
    from run_agent import AIAgent
    from tools.registry import registry

    reads = []

    def read_project(args, **_):
        if args != {"part": "brief"}:
            return json.dumps({"error": 'Use part "brief"'})
        reads.append("brief")
        return json.dumps({"brief": brief, **feedback})

    def constrain_reply(_call_id, name, _args, _result):
        if name == TOOL and reads == ["brief"]:
            agent.request_overrides.update(
                tools=[], tool_choice="none", response_format=RESPONSE_FORMAT
            )

    registry.register(
        name=TOOL,
        toolset="puppy50_coding_example",
        schema={
            "name": TOOL,
            "description": "Read the VM scheduler requirements, example, and any grader feedback.",
            "parameters": {
                "type": "object",
                "properties": {"part": {"type": "string", "enum": ["brief"]}},
                "required": ["part"],
                "additionalProperties": False,
            },
        },
        handler=read_project,
    )

    agent = AIAgent(
        provider="custom",
        api_mode="chat_completions",
        base_url=BASE_URL,
        api_key="local-only",
        model=MODEL,
        enabled_toolsets=["puppy50_coding_example"],
        skip_context_files=True,
        skip_memory=True,
        skip_background_review=True,
        quiet_mode=True,
        max_iterations=3,
        max_tokens=1300,
        run_budget_seconds=255,
        request_overrides={"temperature": 0, "tool_choice": "auto", "timeout": 210},
        tool_complete_callback=constrain_reply,
    )
    if agent.valid_tool_names != {TOOL}:
        raise RuntimeError(f"Unexpected Hermes tool surface: {sorted(agent.valid_tool_names)}")
    started = time.monotonic()
    result = agent.run_conversation(
        'Read the project brief, then deliver the completed scheduler in the JSON "source" field.',
        system_message=SYSTEM_PROMPT,
    )
    evidence = {
        "tool_reads": reads,
        "qwen_calls": result.get("api_calls"),
        "elapsed_seconds": round(time.monotonic() - started, 2),
    }
    reply = result.get("final_response")
    calls = evidence["qwen_calls"]
    if result.get("completed") is not True or reads != ["brief"] or type(calls) is not int or calls < 2:
        return "", evidence, "Hermes did not complete the required project read and submission"
    try:
        source = json.loads(reply)["source"]
    except (TypeError, ValueError, KeyError):
        return "", evidence, "Return a JSON object with Python code in the source string"
    if not isinstance(source, str) or not source.strip() or len(source.encode("utf-8")) > 12_000:
        return "", evidence, "Submit a nonempty Python source string below 12,000 bytes"
    if fence := re.fullmatch(r"\s*```(?:python)?\s*\n(.*?)\n```\s*", source, re.DOTALL):
        source = fence[1]
    return source.strip() + "\n", evidence, None


def grade(source_file):
    name = f"puppy50-example-{uuid4().hex}"
    command = [
        "docker", "run", "--rm", "--name", name, "--pull", "never",
        "--network", "none", "--read-only", "--cap-drop", "ALL", "--user", "65534:65534",
        "--security-opt", "no-new-privileges=true", "--cpus", "1", "--memory", "96m",
        "--memory-swap", "96m", "--pids-limit", "16", "--ulimit", "cpu=5:5",
        "--mount", f"type=bind,src={EXAMPLE / 'grade.py'},dst=/grader.py,readonly",
        "--mount", f"type=bind,src={source_file},dst=/submission.py,readonly",
        IMAGE, "python", "-I", "-B", "/grader.py", "/submission.py",
    ]
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=16)
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=15, check=False)
        return {"passed": 0, "total": None, "failures": ["The scheduler exceeded its execution time limit"]}
    if 125 <= process.returncode <= 127:
        raise RuntimeError(f"Container could not start: {process.stderr.strip()[:500]}")
    if process.returncode != 0:
        return {"passed": 0, "total": None, "failures": ["The scheduler exceeded a resource limit or stopped early"]}
    return json.loads(process.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    brief = (EXAMPLE / "PROJECT.md").read_text(encoding="utf-8")
    subprocess.run(["docker", "pull", IMAGE], check=True, timeout=100)
    report = {"model": MODEL, "challenge": "Puppy50 VM test scheduler", "passed": False, "submissions": []}
    feedback = {}
    with local_hermes_profile() as context:
        report["context_tokens"] = context
        for number in (1, 2):
            source, evidence, error = generate_source(brief, feedback)
            if error:
                result = {"passed": 0, "total": None, "failures": [error]}
            else:
                candidate = output / f"submission-{number}.py"
                candidate.write_text(source, encoding="utf-8")
                evidence["source_file"] = candidate.name
                evidence["source_sha256"] = hashlib.sha256(candidate.read_bytes()).hexdigest()
                result = grade(candidate)
            report["submissions"].append({"number": number, **evidence, **result})
            report["passed"] = result["total"] is not None and result["passed"] == result["total"]
            (output / "coding-example.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            mark = "PASS" if report["passed"] else "FAIL"
            print(f"Submission {number}: {mark} ({result['passed']}/{result['total']} checks)", flush=True)
            if report["passed"]:
                break
            feedback = {"grader_feedback": result["failures"][:6]}
            if source:
                feedback["previous_source"] = source
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
