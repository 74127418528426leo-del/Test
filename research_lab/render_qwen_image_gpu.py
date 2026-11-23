#!/usr/bin/env python3
"""Render a Hermes image plan with the public, quota-limited Turbo GPU demo."""

import argparse
import hashlib
import io
import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4

from PIL import Image, ImageStat


SPACE = "hugging-apps/qwen-qwen-image-2-1-turbo"
SPACE_REVISION = "75660854b565a39386dfa9d30d7e08680eb2fc4a"
HOST = "https://hugging-apps-qwen-qwen-image-2-1-turbo.hf.space"
MODEL = "Qwen/Qwen-Image-2.1-Turbo"
SIZE = (1216, 896)
MAX_IMAGE_BYTES = 16 * 1024 * 1024


def call_gpu(prompt, seed):
    metadata_url = f"https://huggingface.co/api/spaces/{SPACE}"
    with urlopen(metadata_url, timeout=20) as response:
        metadata = json.load(response)
    runtime = metadata.get("runtime", {})
    hardware = runtime.get("hardware", {}).get("current", "")
    if runtime.get("sha") != SPACE_REVISION or metadata.get("host") != HOST:
        raise RuntimeError("The public GPU demo has changed. Review its model and API before rendering.")
    if runtime.get("stage") != "RUNNING" or not hardware or not hardware.startswith("zero-"):
        raise RuntimeError("The public ZeroGPU demo is unavailable")

    endpoint = f"{HOST}/gradio_api/call/generate"
    payload = {"data": [prompt, [], seed, 1024, "4:3"], "session_hash": uuid4().hex}
    request = Request(endpoint, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    started = time.monotonic()
    with urlopen(request, timeout=25) as response:
        event_id = json.load(response)["event_id"]
    if not re.fullmatch(r"[0-9a-f]{32}", event_id):
        raise RuntimeError("The public demo returned an invalid request identifier")

    event = None
    with urlopen(f"{endpoint}/{event_id}", timeout=30) as response:
        for raw_line in response:
            line = raw_line.decode().strip()
            if line.startswith("event:"):
                event = line.removeprefix("event:").strip()
            if not line.startswith("data:"):
                continue
            data = line.removeprefix("data:").strip()
            if event == "error":
                raise RuntimeError(f"Public ZeroGPU request ended with an error ({data[:400]})")
            if event == "complete":
                file_data = json.loads(data)[0]
                return file_data["url"], round(time.monotonic() - started, 3), hardware
    raise RuntimeError("The public GPU demo closed the request before returning an image")


def render(out):
    receipt = out / "image-example.json"
    plan = json.loads(receipt.read_text(encoding="utf-8"))
    prompt, seed = plan["prompt"], plan["seed"]
    if (
        plan.get("image_model") != MODEL or plan.get("tool_reads") != ["brief"]
        or type(plan.get("qwen_calls")) is not int or plan["qwen_calls"] < 2
        or not isinstance(prompt, str) or not 40 <= len(prompt.strip()) <= 1100
        or type(seed) is not int or not 0 <= seed < 2**31
    ):
        raise ValueError("Expected a validated Hermes and Qwen Turbo image plan")

    started = time.monotonic()
    url, request_seconds, hardware = call_gpu(prompt, seed)
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https" or parsed.netloc != urlsplit(HOST).netloc
        or not parsed.path.startswith("/gradio_api/file=")
    ):
        raise RuntimeError("The public demo returned an unexpected image URL")
    with urlopen(url, timeout=25) as response:
        raw = response.read(MAX_IMAGE_BYTES + 1)
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("The public demo returned an oversized image")

    output = out / "puppy50-qwen-image.png"
    with Image.open(io.BytesIO(raw)) as image:
        if image.size != SIZE or max(ImageStat.Stat(image.convert("RGB")).stddev) < 8:
            raise ValueError(f"Expected a nonblank {SIZE[0]}x{SIZE[1]} image")
        if image.format == "PNG":
            output.write_bytes(raw)
        else:
            image.save(output, format="PNG")
    with Image.open(output) as image:
        image.verify()
    plan.update(
        backend="Hugging Face public ZeroGPU Space",
        space=SPACE,
        space_revision=SPACE_REVISION,
        space_hardware=hardware,
        steps=8,
        width=SIZE[0],
        height=SIZE[1],
        gpu_request_seconds=request_seconds,
        render_stage_seconds=round(time.monotonic() - started, 3),
        sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        passed=True,
    )
    receipt.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {SIZE[0]}x{SIZE[1]} Qwen Turbo image. GPU request took {request_seconds:.2f}s.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        render(args.output)
    except HTTPError as error:
        parser.exit(1, f"Free GPU request failed with HTTP {error.code}. See the public Space quota.\n")
    except (RuntimeError, ValueError, OSError, KeyError) as error:
        parser.exit(1, f"Free GPU render failed: {error}\n")


if __name__ == "__main__":
    main()
