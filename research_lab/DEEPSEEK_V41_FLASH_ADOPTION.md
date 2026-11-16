# DeepSeek V4.1 Flash adoption decision

**Decision:** Select DeepSeek V4.1 Flash as the preferred open-weight model to evaluate for Puppy50 research and coding-agent work. This is a model-selection decision, not evidence that the model has been deployed, run against the repository, or outperformed Qwen/Hermes.

## Verified license and access

The official `deepseek-ai/DeepSeek-V4.1-Flash` model card identifies the model as MIT-licensed and says the repository and model weights are under the MIT License. The pinned license file at revision `fb2764a5cf321eaa5070ca8f9e892818f477c16d` contains the standard MIT grant and notice requirement:

- Model card: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash
- Pinned license: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/fb2764a5cf321eaa5070ca8f9e892818f477c16d/LICENSE

MIT covers the model weights and the licensed repository. It does not make a hosted inference API free, nor does it automatically license separate runtimes, tool frameworks, datasets, or downstream components. Audit those separately before deployment.

## Deployment constraint

The official Hugging Face model listing currently reports approximately 510 GB of files. The current execution environment has no visible NVIDIA GPU and about 59 GB of free workspace storage, so local inference is not feasible here. Do not download partial shards or claim a local run. A real self-hosted evaluation needs a provisioned inference host with storage for the full checkpoint plus runtime/cache headroom and a supported multi-GPU configuration.

The official API exposes the model as `deepseek-flash` and reports it as DeepSeek-V4.1-Flash-1017. API usage is separately metered; published rates vary by peak/off-peak time. No API call should run until the project has a securely configured credential and a bounded spend limit:

- API model/version and tool-call support: https://api-docs.deepseek.com/quick_start/pricing/
- Official API pricing: https://api-docs.deepseek.com/quick_start/pricing/

## Safe evaluation plan

1. Keep the existing local Qwen 0.8B worker only as an inexpensive integration smoke test; it is not the selected architecture model.
2. Add a separately gated, manual-only DeepSeek evaluation once an authorized endpoint is available. Never call the hosted API on ordinary pushes or scheduled runs.
3. Compare both models on the exact same versioned task, prompt, read-only evidence packet, tool schema, timeout, and output-token cap.
4. Score tool-call correctness, schema validity, factual consistency, test-passing patches, retries, latency, and measured API usage. Keep raw responses and task hashes as evidence, while excluding credentials.
5. Run any accepted code proposal through offline tests, independent review, and matched BIOS/UEFI VM tests. No agent output can merge to stable or promote an ISO by itself.

## Current status

- MIT license verified from the official model repository.
- Model selected for a future controlled comparison.
- No DeepSeek inference has run: this session has no DeepSeek API credential and no suitable local GPU host.
- Latest Puppy50 agent-pilot run remains a failing Qwen/Hermes integration run; it does not test DeepSeek or launch a Puppy50 VM.
- The under-five-second Firefox target remains unverified.
