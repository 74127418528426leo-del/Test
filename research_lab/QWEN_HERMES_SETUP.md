# Qwen + Hermes / OpenClaude / OpenCode integration

**Status (updated November 16, 2026):** A pinned Qwen3.5-0.8B Q4 CPU
model behind llama.cpp and the Hermes CLI have been exercised in bounded,
credential-free GitHub Actions jobs. The Hermes tool-use pilot is inconsistent;
this is not an always-on supervisor. No Qwen3.8 GPU host or endpoint is
provisioned, and OpenClaude has not been exercised. A separate GPU deployment
still requires operator-owned, appropriately sized infrastructure.

## Model selection (verified November 15, 2026)
- **Qwen/Qwen3.8-27B** — current open-weight general-purpose agentic/reasoning
  model, Apache 2.0. Recommended first for reproducible Linux and Firefox work.
- **Qwen/Qwen3-Coder-Next** — agentic coding model; 80B total / 3B active,
  Apache 2.0, a separate specialist choice. Total weight memory matters:
  3B active does NOT mean the checkpoint fits in 3B's VRAM.
- **Qwen/Qwen3.8-2.4T-A95B** — highly capable research model; too large for
  ordinary runners. Custom license and datacenter-scale acceleration required.
  A hosted API is more practical than self-hosting this checkpoint.

References:
https://github.com/QwenLM/Qwen3.8
https://huggingface.co/Qwen/Qwen3.8-27B
https://huggingface.co/Qwen/Qwen3-Coder-Next
https://github.com/NousResearch/hermes-agent
https://github.com/xda6/OpenClaude

## Manual deployment (operator runs on **their own GPU server**)

Example assuming a GPU server that supports the desired checkpoint and
recent vLLM (version/support requirements vary by Qwen model):

```bash
# ON GPU SERVER (not GitHub Actions), after installing vLLM following its docs:
export P50_QWEN_API_KEY='<server-generated-private-secret>'
vllm serve Qwen/Qwen3.8-27B --host 127.0.0.1 --port 8000 --api-key "$P50_QWEN_API_KEY"
```

Do NOT publish port 8000. Place a secured, authenticated HTTPS reverse proxy
in front of the local endpoint, with TLS certificate and access controls.
GitHub's Ubuntu runner must reach that address. Prefer an isolated private
runner on the GPU host/network rather than exposing inference publicly. The
workflow rejects insecure HTTP and loopback URLs.

GitHub repository -> Settings -> Secrets and variables -> Actions:

```text
Repository secret:
  P50_QWEN_API_KEY    = authenticated HTTPS inference token
Repository variables:
  P50_MODEL_PROVIDER  = qwen_compatible
  P50_QWEN_ENDPOINT   = https://YOUR-SECURE-QWEN-HOST/v1
  P50_QWEN_MODEL      = Qwen/Qwen3.8-27B
```

Now go to GitHub Actions -> Puppy50 AI Research Laboratory -> Run workflow.
Select `enable_ai=true` and begin with `max_model_calls=8`, `parallel=4`
and `max_new=8`. Confirm that returned proposals pass JSON validation and
independent reviewer checks. Manually scale up to 128 calls and 16 concurrent
requests only when cost, endpoint throughput and model stability justify it.
128 calls do not mean 128 continuously running AI instances.

Recurring paid inference is **OFF** unless you set repository variable
`P50_ENABLE_AI=true` yourself. Set usage and spend limits at provider level.
Open-weight models can eliminate per-token vendor bills when self-hosted but
GPU rental, electricity and maintenance are not free.

## External agent frameworks

Use Hermes Agent for persistent researcher skills, memory, task delegation
and scheduled analysis. Use OpenClaude/OpenCode for independent coding/review
tasks in isolated cloned repositories and draft PRs. Both may connect to
compatible Qwen inference providers. Their models/tools must be configured
independently; the GitHub lab does not launch either framework automatically.

Agents should load `research_lab/AGENTS.md` as project guardrails. Restrict
their runner permissions, avoid repository secrets in model context and
do not allow model-written code into a real ISO release without manual review.

**Architecture:**
```
Hermes supervisor / OpenClaude coding workers  [external GPU/VPS]
          |
          v  proposals/draft PRs
Qwen3.8, Qwen3-Coder-Next via vLLM HTTPS GPU endpoint
          |
          v  numerical allowlist, independent LLM critique
Existing GitHub research_lab/queue.json -> guarded VM controller
          |
          v  actual QEMU BIOS/UEFI boot, real Firefox + RAM + HTTP proofs
          |
          v  evidence and failure feedback; **no unverified release**
```

The GPU model may propose creative architecture designs, but the current
automated VM bridge only directly tests bounded Firefox nice and initramfs
Zstd levels. Arbitrary kernel/compiler/Xorg patches need a separate reviewed
build workflow and approval gates; this is intentional.
