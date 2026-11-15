#!/usr/bin/env bash
# Operator-invoked Hermes research-only agent against the LOCAL vLLM GPU host.
# Requires Docker and a separately provisioned Qwen3.8-27B-FP8 server.
# No daemon, background bills, automated code execution or exposed network ports.
set -euo pipefail
: "${P50_QWEN_API_KEY:?Set the private vLLM API key in your environment}"
command -v docker >/dev/null
HERMES_DIR="${HERMES_DIR:-$HOME/.puppy50-hermes}"
mkdir -p "$HERMES_DIR"
chmod 700 "$HERMES_DIR"

cat > "$HERMES_DIR/config.yaml" <<'YAML'
model:
  default: Qwen/Qwen3.8-27B-FP8
  provider: custom:puppy50
providers:
  puppy50:
    api: http://127.0.0.1:8000/v1
    key_env: P50_QWEN_API_KEY
    transport: chat_completions
    context_length: 65536
toolsets:
  - safe
agent:
  tool_use_enforcement: false
  disabled_toolsets:
    - terminal
    - file
    - browser
    - code_execution
    - delegation
    - cronjob
YAML
chmod 600 "$HERMES_DIR/config.yaml"

echo "Puppy50 Hermes research-only one-shot (actual Qwen GPU must be serving)."
docker run --rm --network host --cpus 4 --memory 8g \
  --security-opt no-new-privileges:true \
  -e PUID="$(id -u)" -e PGID="$(id -g)" \
  -e P50_QWEN_API_KEY="$P50_QWEN_API_KEY" \
  -v "$HERMES_DIR:/opt/data" \
  nousresearch/hermes-agent:stable \
  -z 'Read-only research task: analyze why a browser-first Linux could fail post-eject HTTP checks. Propose TWO specific falsifiable hypotheses and validation steps. Do not execute tools, code, or edit files. Never claim unobserved benchmark results.'
