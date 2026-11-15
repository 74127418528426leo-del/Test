# Self-hosted Qwen3.8 GPU inference for Puppy50

**Prepared, not deployed:** These files run on an independently provisioned
NVIDIA GPU server with Docker Compose and NVIDIA Container Toolkit.
No GPU account, GPU machine or private token is provisioned by ChatGPT or
GitHub. **Starting/renting GPU hardware can incur charges.**

## Requirements

- Supported NVIDIA GPU, drivers and `docker compose` with NVIDIA GPU runtime;
  for the FP8 model use a compatible GPU with enough available VRAM.
  Start with 1× H100 80GB if available; verify memory headroom empirically.
- At least 80 GB free disk for model/cache and ample CPU RAM.
- A GitHub runner (or approved private proxy) able to connect to this endpoint.
  Public GitHub runners cannot access a private localhost socket remotely.
- No secrets in Git commits or published logs.

## Start only after owner provisions GPU and controls cost

```bash
cd research_lab/gpu_server
cp example.env .env
chmod 600 .env
# Change the example token to a strong private value.
docker compose config -q        # validates compose config
nvidia-smi
docker compose up -d
curl -fsS -H "Authorization: Bearer YOUR_PRIVATE_TOKEN" http://127.0.0.1:8000/v1/models
```

`compose.yaml` pins official vLLM v0.28.0 and official
`Qwen/Qwen3.8-27B-FP8`. First launch downloads large weights and can take
substantial time. Service binds **127.0.0.1:8000 on the GPU host only**.
The vLLM API token does not secure every endpoint: never forward port 8000
directly to the internet.

## Connect the existing GitHub research controller

Supply an **authenticated HTTPS** ingress reachable from the authorized
runner, secured by a firewall/mTLS and private networking/tunnel. On a
private-network self-hosted runner you may instead use a private proxy URL
with valid TLS. The endpoint variable is the HTTPS *base* URL including /v1,
for example `https://qwen.example.com/v1` (only a placeholder).

In GitHub Settings → Secrets and variables → Actions, configure:
- Secret `P50_QWEN_API_KEY` equal to the private token.
- Variable `P50_QWEN_ENDPOINT` = trusted HTTPS URL ending `/v1`.
- Variable `P50_QWEN_MODEL` = `Qwen/Qwen3.8-27B-FP8`.
- Variable `P50_MODEL_PROVIDER` = `qwen_compatible`.

Use manual `Puppy50 AI Research Laboratory` workflow dispatch with
`enable_ai=true` and small model-call limit (8) to start. The scheduled AI
calls stay disabled until explicitly enabled. Models are research
assistants; unreviewed generated shell/Python is never run automatically.

## Stop compute usage

```bash
docker compose down
```

Do not claim a five-second ISO or physical Acer verification from model
text alone. The separate QEMU workflow must independently test all
functional and startup gates.

References:
https://docs.vllm.ai/en/v0.27.0/deployment/docker/
https://docs.vllm.ai/en/latest/usage/security/
https://recipes.vllm.ai/Qwen/Qwen3.8-27B
