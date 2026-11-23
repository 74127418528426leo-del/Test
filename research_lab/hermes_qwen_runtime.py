"""Shared profile and loopback checks for the Hermes workflows."""

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.request import urlopen

BASE_URL = "http://127.0.0.1:18080/v1"
CONTEXT_TOKENS = 65_536
MODEL = "Qwen3.5-4B"


@contextmanager
def local_hermes_profile():
    with urlopen(BASE_URL + "/models", timeout=5) as response:
        models = json.load(response)["data"]
    if [model["id"] for model in models] != [MODEL]:
        raise RuntimeError("The local backend is serving a different model")
    with urlopen(BASE_URL.removesuffix("/v1") + "/props", timeout=5) as response:
        context = json.load(response)["default_generation_settings"]["n_ctx"]
    if context != CONTEXT_TOKENS:
        raise RuntimeError(f"The local backend is serving a {context}-token context")

    with tempfile.TemporaryDirectory(prefix="puppy50-hermes-") as profile:
        os.environ["HERMES_HOME"] = profile
        os.environ["HERMES_SINGLE_QUERY_SESSION"] = "1"
        # Expose the task's tools directly and keep inference on the local provider.
        config = {
            "model": {
                "default": MODEL,
                "provider": "custom",
                "base_url": BASE_URL,
                "context_length": context,
            },
            "agent": {
                "coding_context": "off",
                "execution_guidance": False,
                "task_completion_guidance": False,
                "parallel_tool_call_guidance": False,
                "environment_probe": False,
                "api_max_retries": 1,
            },
            "tools": {"tool_search": {"enabled": "off"}},
        }
        (Path(profile) / "config.yaml").write_text(json.dumps(config), encoding="utf-8")
        yield context
