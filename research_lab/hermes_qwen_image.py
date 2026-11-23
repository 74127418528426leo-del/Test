#!/usr/bin/env python3
"""Plan a Qwen image prompt and verify the renderer's PNG."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageStat

from hermes_qwen_runtime import BASE_URL, MODEL, local_hermes_profile


TOOL = "read_image_brief"
IMAGE_MODEL = "Qwen/Qwen-Image-2.1-Turbo"
SEED = 5067
SIZE = 384
BRIEF = {
    "subject": "A small friendly puppy next to a compact retro desktop computer with a glowing sapphire screen.",
    "composition": "Square editorial 3D illustration, centered subject, three-quarter view.",
    "art_direction": "Ivory computer case, midnight-blue studio backdrop, warm amber rim light, a few realistic details.",
    "constraints": "One puppy and one computer. Clear silhouette, clean background, no lettering or logos.",
}
RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "image_prompt",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {"prompt": {"type": "string"}},
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
}


def plan_image():
    from run_agent import AIAgent
    from tools.registry import registry

    reads = []

    def read_brief(args, **_):
        if args != {"part": "brief"}:
            return json.dumps({"error": 'Use part "brief"'})
        reads.append("brief")
        return json.dumps(BRIEF, ensure_ascii=False)

    def constrain_reply(_call_id, name, _args, _result):
        if name == TOOL and reads == ["brief"]:
            agent.request_overrides.update(
                tools=[], tool_choice="none", response_format=RESPONSE_FORMAT
            )

    registry.register(
        name=TOOL,
        toolset="puppy50_image_example",
        schema={
            "name": TOOL,
            "description": "Read the subject, composition, and constraints for the Puppy50 image.",
            "parameters": {
                "type": "object",
                "properties": {"part": {"type": "string", "enum": ["brief"]}},
                "required": ["part"],
                "additionalProperties": False,
            },
        },
        handler=read_brief,
    )
    agent = AIAgent(
        provider="custom",
        api_mode="chat_completions",
        base_url=BASE_URL,
        api_key="local-only",
        model=MODEL,
        enabled_toolsets=["puppy50_image_example"],
        skip_context_files=True,
        skip_memory=True,
        skip_background_review=True,
        quiet_mode=True,
        max_iterations=3,
        max_tokens=230,
        run_budget_seconds=150,
        request_overrides={"temperature": 0, "tool_choice": "auto", "timeout": 105},
        tool_complete_callback=constrain_reply,
    )
    if agent.valid_tool_names != {TOOL}:
        raise RuntimeError("Unexpected Hermes tool availability")
    result = agent.run_conversation(
        'Read the image brief and return one Qwen-Image prompt as JSON with the key "prompt".',
        system_message=(
            'Call read_image_brief with part "brief" before answering. Follow its visual constraints. '
            "Write a concise English image-generation prompt."
        ),
    )
    calls = result.get("api_calls")
    if result.get("completed") is not True or reads != ["brief"] or type(calls) is not int or calls < 2:
        raise RuntimeError("Hermes did not finish the required tool call and model reply")
    prompt = json.loads(result["final_response"])["prompt"]
    if not isinstance(prompt, str) or not 40 <= len(prompt.strip()) <= 1100:
        raise ValueError("The image prompt must contain 40–1100 characters")
    return {"prompt": prompt.strip(), "tool_reads": reads, "qwen_calls": calls}


def verified_sha256(output):
    with Image.open(output) as image:
        if image.format != "PNG" or image.size != (SIZE, SIZE):
            raise ValueError(f"Expected a {SIZE}x{SIZE} PNG")
        if max(ImageStat.Stat(image.convert("RGB")).stddev) < 8:
            raise ValueError("Image output appears blank")
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("plan", "verify"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    receipt = out / "image-example.json"
    if args.stage == "plan":
        report = {
            "passed": False, "planning_model": MODEL, "image_model": IMAGE_MODEL,
            "backend": "stable-diffusion.cpp CPU", "seed": SEED, "width": SIZE, "height": SIZE,
        }
        with local_hermes_profile():
            report.update(plan_image())
        print(f"Image prompt ready after {report['qwen_calls']} Qwen calls", flush=True)
    else:
        report = json.loads(receipt.read_text(encoding="utf-8"))
        if report.get("tool_reads") != ["brief"] or report.get("qwen_calls", 0) < 2:
            raise ValueError("Missing verified prompt-planning evidence")
        report["sha256"] = verified_sha256(out / "puppy50-qwen-image.png")
        report["passed"] = True
        print(f"Verified Qwen image {SIZE}x{SIZE} on CPU", flush=True)
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
