# Puppy50 autonomous open-weight agents — reproducible findings (2026-11-15)

## 1. Actual open-weight LLM inference verified

- A real 4-bit Qwen3.5-0.8B GGUF model was downloaded and checksum
  verified on GitHub-hosted Ubuntu CPU, run by llama.cpp, and answered
  two real messages (researcher and independent reviewer) with valid JSON.
  [Evidence run](https://github.com/74127418528426leo-del/Test/actions/runs/43772131550).

- A four-runner distributed job launched the **same model separately on
  four independent CPU runners**, 32 requests on each, for a total of
  **128 actual real model responses and 128 unique role/task IDs**.
  [Verified 128-run](https://github.com/74127418528426leo-del/Test/actions/runs/43773527093).
  Each independent shard and the independent reducer job passed.
  [Final immutable reducer artifact](https://github.com/74127418528426leo-del/Test/actions/runs/43773527093/artifacts/14184714930).

## 2. Format ≠ quality: first distributed audit was an important negative result

- **0/128 of the 0.8B outputs passed the strict JSON/allowlist test** in
  the original unstructured generation batch. The cause was demonstrated
  by raw output: spurious keys, markdown code fences and output text
  inconsistent with the expected fields, plus incomplete responses.
  None were passed into a trusted ISO build.

- The next four-request pilot used the **documented llama.cpp JSON-schema
  constrained decoder**, eliminating the format failure:
  **4/4 valid safe-schema JSON outputs** in
  [the proof run](https://github.com/74127418528426leo-del/Test/actions/runs/43774118417).
  However, the tiny model returned mostly generic/repeated hypotheses.
  JSON correctness is not evidence of OS-engineering capability.

- A larger quantized 4B model's quality pilot is separately launched:
  [Qwen3.5 4B real engineering test](https://github.com/74127418528426leo-del/Test/actions/runs/43774339319).
  Do not claim this passed until GitHub verifies the result.

## 3. Genuine Hermes framework test — not yet successful

- Official Hermes Agent Docker was actually pulled and launched
  against the local 0.8B model. Initial run failed its minimum 64K
  context requirement. Retest allocated 65536 context but Hermes
  one-shot never completed before the bounded 160-second timeout;
  it was stopped. The GitHub smoke workflow itself could still finish
  green because this stage was marked diagnostic `continue-on-error`.
  [Hermes diagnostic run](https://github.com/74127418528426leo-del/Test/actions/runs/43772563750).

- A separate `research_lab/gpu_server/run_hermes_research.sh`
  prepares a restricted one-shot Hermes worker against model-served
  Qwen3.8 with the supported named custom-provider API and environment
  secret. **It has not been executed on real GPU hardware.**

## 4. Qwen3.8 GPU plan — configured, not provisioned

- `research_lab/gpu_server/compose.yaml` describes
  vLLM `Qwen/Qwen3.8-27B-FP8` on a user's authorized CUDA GPU with
  65536-token context and no public server port.
- User must supply the GPU host, private endpoint, authentication and
  approve any cloud compute charges. Ordinary GitHub CPU runners are
  not enough to host this large model efficiently.
- All candidate OS code remains subject to independent build, security
  and BIOS/UEFI QEMU testing before promotion; generated code is never
  blindly installed, released, or merged.

## 5. Puppy50 boot target still not reached

Existing guarded VM controller reports test candidate nice=-10, Zstd=3,
four real frames: BIOS 10.31s and 8.65s, UEFI 21.03s and 12.89s
with complete functional gates; all exceeded **strict <5 seconds**.
The actual Acer i3-540 physical power-on-to-browser time and 384 MiB
full-RAM Firefox target remain unverified.

## Scope of the number '128'

The successful distributed test is **128 independent inference
requests**, **not** 128 independently provisioned intelligent
autonomous long-lived agents, GPU instances, or verified operating
system improvements.

Success in infrastructure, model output syntax and
real-world OS optimization are three different milestones.
