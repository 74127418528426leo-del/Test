#!/usr/bin/env python3
"""Use a Hermes-planned Qwen prompt to generate a verified image."""

import argparse
import hashlib
import io
import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from PIL import Image, ImageStat

from hermes_qwen_runtime import BASE_URL, MODEL, local_hermes_profile


TOOL = "read_image_brief"
IMAGE_MODEL = "Qwen/Qwen-Image"
SPACE = "https://qwen-qwen-image.hf.space"
SEED = 5067
MAX_IMAGE_BYTES = 12 * 1024 * 1024
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


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def render(prompt, record):
    client = build_opener(NoRedirect())
    endpoint = SPACE + "/gradio_api/call/infer"
    args = [prompt, SEED, False, "1:1", 4, 24, False]
    request = Request(endpoint, json.dumps({"data": args}).encode(), {"Content-Type": "application/json"})
    with client.open(request, timeout=35) as response:
        event_id = json.load(response)["event_id"]
    if not re.fullmatch(r"[a-f0-9]{32}", event_id):
        raise RuntimeError("Unexpected Qwen demo event ID")
    record["event_id"] = event_id
    deadline = time.monotonic() + 210
    event = ""
    with client.open(endpoint + "/" + event_id, timeout=45) as response:
        for raw in response:
            if time.monotonic() > deadline:
                raise TimeoutError("Qwen image queue exceeded the example's deadline")
            line = raw.decode("utf-8").strip()
            if line.startswith("event: "):
                event = line[7:]
            if line.startswith("data: ") and event == "error":
                raise RuntimeError("Qwen demo returned an error: " + line[6:300])
            if line.startswith("data: ") and event == "complete":
                image, seed = json.loads(line[6:])
                break
        else:
            raise RuntimeError("Qwen demo closed its queue before returning an image")
    url = urlsplit(image["url"])
    if url.scheme != "https" or url.netloc != urlsplit(SPACE).netloc or not url.path.startswith("/gradio_api/file="):
        raise RuntimeError("Qwen demo returned a file URL outside its image endpoint")
    if seed != SEED:
        raise RuntimeError("Qwen demo returned a different seed")
    with client.open(url.geturl(), timeout=35) as response:
        data = response.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise RuntimeError("Qwen demo returned an oversized image")
    return data


def checked_image(raw, output):
    with Image.open(io.BytesIO(raw)) as image:
        if not (256 <= image.width <= 3072 and image.width == image.height):
            raise ValueError("Unexpected image dimensions for the square example")
        picture = image.convert("RGB")
    deviations = ImageStat.Stat(picture).stddev
    if max(deviations) < 8:
        raise ValueError("Image output appears blank")
    picture.save(output, format="PNG")
    return {
        "width": picture.width,
        "height": picture.height,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    report = {"passed": False, "planning_model": MODEL, "image_model": IMAGE_MODEL, "backend": SPACE, "seed": SEED}
    started = time.monotonic()
    try:
        with local_hermes_profile():
            report.update(plan_image())
        print(f"Image prompt ready after {report['qwen_calls']} Qwen calls", flush=True)
        report.update(checked_image(render(report["prompt"], report), out / "puppy50-qwen-image.png"))
        report["passed"] = True
        print(f"Verified Qwen image {report['width']}x{report['height']}", flush=True)
    except HTTPError as error:
        report["error"] = f"Image backend HTTP {error.code}"
    except (KeyError, OSError, TypeError, ValueError, RuntimeError) as error:
        report["error"] = str(error)[:350]
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 2)
        (out / "image-example.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["passed"]:
        print(f"Image example failed: {report['error']}", flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
