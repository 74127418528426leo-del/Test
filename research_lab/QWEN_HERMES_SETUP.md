# Qwen + Hermes / OpenClaude / OpenCode integration

**Status (updated November 16, 2026):** Run 43906628085 passed the
credential-free Hermes review gate. Hermes made two tool calls, read only the
prepared packet, and returned values matching persistent state; the report
explicitly says this does not certify a boot. Earlier runs failed at tool
selection or report formatting, so this is not a reliable always-on supervisor.
The direct Qwen function-call canary still forces the call and executes no
tool. This branch adds a separately gated Qwen-Agent trial against the same
local Qwen3.5-0.8B CPU endpoint. Run 439121 exposed two separate problems:
Hermes again made zero tool calls, and Qwen-Agent could not import because its
package metadata omitted the NumPy dependency. Qwen-Agent did not reach model
inference in that run. The dependency is now explicit and the bounded worker
is being retried. Neither Qwen3.8 GPU inference nor a persistent Hermes service
is provisioned. OpenClaude has not been exercised.

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


## Qwen-Agent worker trial

The experimental workflow installs Qwen-Agent from immutable source commit
`31a4d36d123688581a9e9744427272b33ce940e0` (package version 0.0.34) and runs
its Assistant/function-calling loop against the loopback llama.cpp endpoint.
The worker is limited to one tool that reads exactly `review-input.json`, one
successful tool execution, three local model calls, and a 180-second wall-clock
limit. The process receives no GitHub token, uses the loopback model endpoint,
and has no shell or write tool. It is not network-namespace isolated. The
deterministic gate rejects a missing or extra tool call, invalid report, or
disagreement with durable state.
Run 439121 installed the pinned source but failed at import because NumPy was
not declared by Qwen-Agent's package metadata; no Qwen-Agent model request was
made. The next run installs explicit NumPy 2.5.4, captures the resolved
package freeze, and retries the worker. The framework source is commit-pinned,
but its transitive Python dependencies are not yet locked; this pilot is not
ready for persistent deployment.

See [AI agent and provider research](AI_AGENT_AND_PROVIDER_RESEARCH.md) for
provider costs, open-source integration boundaries, and the recommended worker
architecture. No hosted provider is enabled by this experiment.
