"""Run a read-only Hermes review of recorded Puppy50 VM boot measurements."""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from hermes_qwen_runtime import BASE_URL, MODEL, local_hermes_profile

sys.path.insert(0, str(Path(__file__).parent / "hermes_skills/puppy50-progress/scripts"))
from status import REPOSITORY, snapshot

TOOL = "read_boot_batch"
VIEWS = {"latest": "the latest VM trial", "best": "the fastest complete VM batch"}
SYSTEM_PROMPT = """You report recorded Puppy50 QEMU Firefox boot tests.
Call read_boot_batch with the requested view to retrieve the results.
Return only JSON with the tool's candidate, worst_seconds, and next_step.
Copy the three values exactly, including null for missing measurements.
"""
RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "puppy50_boot_review",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "candidate": {"type": ["string", "null"]},
                "worst_seconds": {"type": ["number", "null"]},
                "next_step": {"enum": ["measure", "optimize", "diagnose", "verified", "replicate"]},
            },
            "required": ["candidate", "worst_seconds", "next_step"],
            "additionalProperties": False,
        },
    },
}


def boot_batches(state):
    if not isinstance(state, dict) or not isinstance(state.get("history"), list):
        raise ValueError("AutoLab state is missing its experiment history")
    observations = snapshot(state, {}, {})
    best = observations["best_complete_4boot_candidate"] or {}
    batches = {}
    for view, candidate, frames, passed in (
        ("latest", observations["latest_candidate"], observations["latest_observed_frames"],
         observations["latest_vm_passed"]),
        ("best", best.get("candidate"), best.get("frames", {}), best.get("strict_vm_goal_passed")),
    ):
        if not isinstance(candidate, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,65}", candidate):
            candidate = None
        if candidate == "unknown":
            candidate = None
        batches[view] = {
            "candidate": candidate,
            "frames_recorded": len(frames),
            "worst_seconds": max(frames.values(), default=None),
            "vm_gate_passed": passed is True,
            "independently_verified": (
                candidate is not None
                and observations["vm_goal_verified"]
                and candidate == observations["vm_goal_candidate"]
            ),
        }
    return batches


def expected_review(batch):
    if batch["frames_recorded"] < 4:
        next_step = "measure"
    elif batch["worst_seconds"] >= 5.0:
        next_step = "optimize"
    elif not batch["vm_gate_passed"]:
        next_step = "diagnose"
    elif batch["independently_verified"]:
        next_step = "verified"
    else:
        next_step = "replicate"
    return {
        "candidate": batch["candidate"],
        "worst_seconds": batch["worst_seconds"],
        "next_step": next_step,
    }


def review_passed(result, tool_reads, view, expected):
    calls = result.get("api_calls")
    if result.get("completed") is not True or tool_reads != [view]:
        return False
    if type(calls) is not int or calls < 2:
        return False
    try:
        answer = json.loads(result.get("final_response"))
    except (TypeError, ValueError):
        return False
    return answer == expected and type(answer["worst_seconds"]) is not bool


def review_batches(batches):
    # Hermes and its tool registry are needed only for the live inference run.
    from run_agent import AIAgent
    from tools.registry import registry

    expected = {view: expected_review(batch) for view, batch in batches.items()}
    reads = []

    def read_batch(args, **_):
        view = args.get("view")
        if not isinstance(view, str) or view not in VIEWS:
            return json.dumps({"error": "Select latest or best"})
        reads.append(view)
        return json.dumps(expected[view])

    registry.register(
        name=TOOL,
        toolset="puppy50_review",
        schema={
            "name": TOOL,
            "description": "Read the latest Puppy50 VM trial or the fastest complete four-boot batch and its recommended next step.",
            "parameters": {
                "type": "object",
                "properties": {"view": {"type": "string", "enum": list(VIEWS)}},
                "required": ["view"],
                "additionalProperties": False,
            },
        },
        handler=read_batch,
    )

    reviews = {}
    for view, description in VIEWS.items():
        reads.clear()

        def constrain_reply(_call_id, name, _args, _result):
            if name == TOOL and reads == [view]:
                # Tool selection remains automatic. Once the data arrives, request a typed answer.
                agent.request_overrides.update(
                    tools=[], tool_choice="none", response_format=RESPONSE_FORMAT
                )

        agent = AIAgent(
            provider="custom",
            api_mode="chat_completions",
            base_url=BASE_URL,
            api_key="local-only",
            model=MODEL,
            enabled_toolsets=["puppy50_review"],
            skip_context_files=True,
            skip_memory=True,
            skip_background_review=True,
            quiet_mode=True,
            max_iterations=4,
            max_tokens=192,
            run_budget_seconds=150,
            request_overrides={"temperature": 0, "tool_choice": "auto", "timeout": 105},
            tool_complete_callback=constrain_reply,
        )
        if agent.valid_tool_names != {TOOL}:
            raise RuntimeError(f"Unexpected Hermes tool surface: {sorted(agent.valid_tool_names)}")
        started = time.monotonic()
        result = agent.run_conversation(
            f"Report {description} (view: {view}). Return only the JSON object.",
            system_message=SYSTEM_PROMPT,
        )
        reply = result.get("final_response") or ""
        reviews[view] = {
            "passed": review_passed(result, reads, view, expected[view]),
            "tool_reads": list(reads),
            "model_api_calls": result.get("api_calls"),
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "observed_batch": batches[view],
            "expected_review": expected[view],
            "model_reply": reply[:1200] if isinstance(reply, str) else None,
        }
    return reviews


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--state-revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.state_revision):
        parser.error("--state-revision must be a Git commit SHA")

    batches = boot_batches(json.loads(args.state.read_text(encoding="utf-8")))
    with local_hermes_profile() as context:
        reviews = review_batches(batches)
    passed = all(review["passed"] for review in reviews.values())
    report = {
        "source_repository": REPOSITORY,
        "state_revision": args.state_revision,
        "model": MODEL,
        "context_tokens": context,
        "passed": passed,
        "reviews": reviews,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for view, review in reviews.items():
        verdict = "PASS" if review["passed"] else "FAIL"
        print(f"{view} review: {verdict} ({review['model_api_calls']} Qwen calls)")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
