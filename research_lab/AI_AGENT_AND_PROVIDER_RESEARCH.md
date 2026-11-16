# Puppy50 AI-agent and model-provider research

**Reviewed November 16, 2026.** This compares reusable agent software with the
inference service it connects to. The distinction matters: a free adapter does
not make a hosted model or its API free.

## What “copying an AI integration” does

An agent framework is software that plans work, calls tools, and passes results
between steps. A provider integration translates that framework's requests to
a model endpoint and handles authentication and tool-call formats. OpenClaw's
official provider list, for example, includes routes for Grok, Qwen Cloud, and
MiniMax plan/API access. Qwen-Agent can instead connect to a local
OpenAI-compatible inference server and apply Qwen's tool-call parsing itself.
Those are reusable integration patterns; they do not copy proprietary model
weights, transfer another service's free quota, or confer access to its API.

An OpenAI-compatible `base_url` is useful, but compatibility must be tested for
each model: chat format, tool-call syntax, context limits, and usage/billing can
differ. Qwen's own docs recommend its function-call templates for Qwen models
and caution against treating a reasoning model's free-form ReAct text as a
reliable tool protocol.

## What is free, and what is not

| Route | What the official material currently says | Puppy50 decision |
| --- | --- | --- |
| **Local Qwen weights + Qwen-Agent** | Qwen-Agent supports local OpenAI-compatible model servers. Local inference avoids a vendor API token bill, but still uses a computer, power, storage, and setup time. | Preferred path for CI experiments. The current 0.8B CPU model is a tool-use smoke-test model, not the engineering lead model. |
| **Grok / xAI** | The OpenClaw adapter can authenticate with an API key or OAuth; its current OAuth route requires an eligible SuperGrok or X Premium subscription. Direct API use is separately token-metered, with prepaid credits or invoicing. Adapter code is free to reuse, but the hosted service is not thereby free. | Do not call from the lab without explicit approval and a spending limit. |
| **DeepSeek API** | The official API page publishes per-token prices and supports tool calls. Charges are deducted from topped-up or granted balance. A grant may temporarily cover usage; it is not evidence of a permanent free API. | Do not call from the lab without explicit approval. |
| **MiniMax** | MiniMax Code/app access, subscription quotas, and the API key for third-party coding agents are distinct, plan-specific routes. The current official plan page advertises API keys for AI tools on paid tiers; any free app allowance is not automatically a free unattended API credential. | No use in this project. Recheck the exact plan before connecting any service. |
| **Mistral** | Mistral's current usage-limit documentation says Free mode covers a monthly Vibe/Studio budget and does not include API access; API use requires billing activation and pay-as-you-go. | Not a no-cost unattended API path. |
| **Hugging Face Inference Providers** | The published pricing page lists $0.10 monthly inference credits for free accounts, subject to change; additional usage is pay-as-you-go. | Too small and changeable for a continuous research worker; not enabled. |
| **GitHub Models** | GitHub retired the playground, catalog, inference API, and BYOK service on July 30, 2026. | Not an available free-model backend. |

Always re-check provider terms before enabling an external route. Do not put
provider keys in Qwen/Hermes prompts, pull requests, artifacts, or public GitHub
Actions. A provider adapter may send the full prompt and source snippets to the
provider, so data handling must be reviewed as well as price.

## Recommended Puppy50 orchestration

1. **Hermes is the future supervisor, not yet an always-on service.** Its job
   is to accept requests, read status, schedule bounded jobs, and hand work to
   specialists. Current Hermes CI runs end with the workflow; there is no
   persistent gateway in this repository deployment.
2. **Qwen-Agent is a candidate worker framework.** Use it for explicit research,
   coding, and debugging tasks against a local Qwen endpoint. Workers should
   receive the smallest necessary file/tool allowlist, a disposable branch or
   worktree, and a fixed compute/time budget.
3. **Independent Python checks remain authoritative.** They verify schemas,
   source hashes, test results, boot timing, BIOS/UEFI behavior, RAM checksums,
   safe media removal, and post-removal browser networking. An agent report is
   not independent evidence of its own work.
4. **A security/review worker may reject or request changes, but cannot merge,
   publish an ISO, or alter the stable branch.** Those actions remain outside
   the automated worker permissions.
5. **Use a larger local model only when hardware is available.** Qwen3.8-27B or
   a Qwen coding specialist needs a suitably provisioned GPU host or other
   explicitly approved inference service. The current repository has no such
   GPU endpoint. GitHub Actions CPU runners can test bounded control logic and
   small-model tool use, not substantiate performance claims for a larger
   model.

The Qwen-Agent pilot uses one read-only packet tool, at most one
successful tool execution, three local model calls, a 512-token output cap, and
a 180-second wall-clock limit. The process receives no GitHub token, shell
tool, or write tool. Its endpoint is loopback, but its process is not
network-namespace isolated. Failed runs preserve tool events and a bounded
assistant-response preview so a rejected report can be diagnosed.

Hermes passed its credential-free review gate in runs 43906628085,
43913391779, and 43914318295. Runs 43912198706 and 43917314867 made zero file
tool calls. In 439173, Hermes said it could not find `review-input.json`;
the cleaned process environment had dropped `TERMINAL_CWD`, which the pinned
file tools use to anchor paths. The next run supplies the isolated workspace
explicitly. This is not an always-on service or boot verification.

Qwen-Agent imports and reached the local model in run 43917314867, but its
final response failed JSON parsing. The server log shows the last generation
hit 256 tokens; truncation is likely, not confirmed because the old artifact
omitted the response preview and tool audit. The next run raises the cap to
512, disables reasoning text, and records bounded diagnostics.

The direct Qwen canary previously sent object-form `tool_choice`; pinned
llama.cpp logged a type mismatch and fell back to its default. The canary now
uses its supported string form `"required"`; it tests serialization only and
does not execute a tool. Qwen-Agent, Hermes, and OS results remain separate.

## Official sources

- [Qwen-Agent configuration: local OpenAI-compatible model servers](https://github.com/QwenLM/Qwen-Agent/blob/31a4d36d123688581a9e9744427272b33ce940e0/qwen-agent-docs/website/content/en/guide/get_started/configuration.md)
- [Qwen3 function calling and Qwen-Agent](https://github.com/QwenLM/Qwen3/blob/main/docs/source/framework/function_call.md)
- [OpenClaw official model-provider integrations](https://docs.openclaw.ai/concepts/model-providers/official-provider-plugins) and [xAI/Grok provider setup](https://docs.openclaw.ai/providers/xai)
- [xAI API pricing](https://docs.x.ai/developers/pricing), [billing and credits](https://docs.x.ai/console/billing), and [tools](https://docs.x.ai/developers/tools/overview)
- [DeepSeek API pricing and tool-call support](https://api-docs.deepseek.com/quick_start/pricing/)
- [MiniMax plan and API-key options](https://platform.minimax.io/subscribe/coding-plan) and [API pricing](https://platform.minimax.io/subscribe/token-plan)
- [Mistral usage and limits](https://docs.mistral.ai/admin/billing-usage/usage-limits)
- [Hugging Face Inference Providers pricing](https://huggingface.co/docs/inference-providers/pricing)
- [GitHub Models retirement](https://github.blog/changelog/2026-07-30-github-models-is-now-retired/)
