#!/usr/bin/env bash
# Actual official Hermes Agent CLI one-shot against the local Qwen CPU server.
# This is a non-destructive CI integration check, not unattended code execution.
set -euo pipefail
mkdir -p hermes-smoke-home hermes-smoke-results
chmod 700 hermes-smoke-home
cat >hermes-smoke-home/config.yaml <<'YAML'
model:
  default: Qwen3.5-0.8B-Q4_K_M.gguf
  provider: custom
  base_url: http://127.0.0.1:8080/v1
  api_key: local-only-demo
YAML
chmod 600 hermes-smoke-home/config.yaml

echo "PUPPY50_HERMES_OFFICIAL_DOCKER_CHECK"
docker pull nousresearch/hermes-agent:stable
set +e
timeout 160 docker run --rm --network host \
  -e PUID="$(id -u)" -e PGID="$(id -g)" \
  -v "$PWD/hermes-smoke-home:/opt/data" \
  --memory 4g --cpus 2 \
  nousresearch/hermes-agent:stable \
  -z 'You are a Puppy50 research critic. Reply with one sentence saying that real QEMU and Firefox verification is mandatory. Do not execute tools, shell commands or change any files.' \
  >hermes-smoke-results/reply.txt 2>hermes-smoke-results/stderr.txt
status=$?
set -e
python3 - "$status" <<'PY'
import json,sys
from pathlib import Path
code=int(sys.argv[1])
reply=Path("hermes-smoke-results/reply.txt").read_text(errors="replace")
error=Path("hermes-smoke-results/stderr.txt").read_text(errors="replace")
report={
 "framework":"NousResearch Hermes Agent stable image",
 "model":"local Qwen3.5-0.8B Q4_K_M",
 "hermes_cli_exit_code":code,
 "nonempty_response":bool(reply.strip()),
 "hermes_one_shot_completed":code==0 and bool(reply.strip()),
 "output_excerpt":reply.strip()[:700],
 "stderr_excerpt":error.strip()[-1200:],
 "real_vm_tests":0,
 "no_automatic_code_writes":True
}
Path("hermes-smoke-results/report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k not in ("stderr_excerpt","output_excerpt")},indent=2))
PY
# Do not erase the separately verified direct-Qwen result if Hermes needs
# configuration changes; report the independent result via artifact and summary.
exit 0
