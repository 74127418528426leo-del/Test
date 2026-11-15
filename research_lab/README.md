# Puppy50 — Future AI Research Laboratory

An operational, **bounded** GitHub Actions research scheduler that connects the existing Puppy50 guarded QEMU/Firefox optimization workflow to a persistent queue of peer-reviewed hypotheses.

## Qwen / Hermes / OpenClaude (new open-weight backend)

The default **optional** model backend is now `qwen_compatible`,
using Qwen3.8-27B through an independently hosted **HTTPS**
OpenAI-compatible inference server (for example vLLM). Model use is
**disabled by default** and requires an accessible endpoint, an API
secret and explicit opt-in. Qwen model weights are not downloaded onto
GitHub's ordinary CPU runners.

See [Qwen + Hermes setup](QWEN_HERMES_SETUP.md) and
[shared agent instructions](AGENTS.md). Hermes Agent and OpenClaude
are **documented external worker integrations**, not installed cloud
services. Real GPU hosting and model invocation have not been proven
by the offline CI tests.

## Live architecture

```
128 logical research task slots (8 specialties × 16 tasks)
      │
      ├── Default/offline scheduler — zero LLM/API calls, selects 8 allowlisted ideas
      │
      └── Opt-in AI mode — at most 8 model requests per scheduled run (manually scalable to 128):
             up to 4 specialist research proposals (manual maximum 64 proposals, parallel limit 16)
             up to 4 separate independent AI safety critiques (manual maximum 64 critiques)
      │
      ↓ Strict numeric validator: Firefox nice / final-initramfs zstd
      ↓ Durable candidate queue (branch puppy50-autolab-state)
      ↓ Existing Puppy50 autonomous VM experimenter (separate workflow)
      ↓ QEMU/KVM cold BIOS ×2 + UEFI ×2
      ↓ Real Firefox first-frame measurement + SHA verified RAM + eject + guest HTTP200
      ↓ Independent repeat of accepted candidates; never auto-release unverified ISO
```

## Proof of deployment

- The model-free workflow starts on lab-code changes and on a four-times-per-day GitHub Actions schedule (UTC 03:43, 09:43, 15:43, 21:43).
- `research_lab/test_lab.py` verifies 128 distinct task identifiers, numeric allowlists, no-AI cost separation, queue deduplication, and per-run model-call budget.
- The actual QEMU workflow is `.github/workflows/puppy50-autonomous-research.yml`. This lab itself runs **zero** QEMU boots. No code supplied by an AI model is executed on a runner.
- Queue: branch `puppy50-autolab-state`, file `research_lab/queue.json`. The QEMU controller prioritizes valid queued parameters, independently tests them, and records results.
- This project has **128 research slots**, not 128 simultaneously provisioned AI instances, GPU cards, or independent servers.

## Enable real AI research (optional, may incur API charges)

The model interface uses **OpenAI Responses API**. GitHub Models was discontinued in 2026 and is not used.

1. On your repository: **Settings → Secrets and variables → Actions**.
2. Add repository **secret** `P50_OPENAI_API_KEY` from your own API project (do not put the key in source files or chat).
3. Add repository **variable** `P50_OPENAI_MODEL` with a model ID your API project can access. Current default code value: `gpt-6-luna`; override if unavailable.
4. For **one manually approved run**, choose Actions → Puppy50 AI Research Laboratory → Run workflow → check `enable_ai`. The default is **false**.
5. Only if you explicitly want *recurring paid model requests*, add repository **variable** `P50_ENABLE_AI` set to `true`. Set it to `false` to stop recurring model requests.

**Model-call limit:** 8 total Responses requests per scheduled workflow, maximum 4 concurrent. A manually initiated, explicitly AI-enabled run can request up to **128 model calls**, at most **16 concurrent**, and up to **64 new hypotheses**. The API provider may bill for input/output tokens. The eight-call limit **is not a monetary cap**; configure spending ceilings and alerts with your API provider before enabling recurring model use.

## Supported science / guardrails

AI can propose new research-only architectural ideas in text, but currently only two allowlisted parameters can enter an automatic VM build:

- Nonroot Firefox process nice: `-10,-9,-11,-8,-12,-7,-13,-6,-5`.
- Final boot initramfs Zstd compression level: `3,2,4,1,5,6,7,8`.

This bounded bridge cannot alter security, browser sandbox, root, kernel, verified recovery image, USB content, or any arbitrary shell script. **Textual architectural ideas require human code review before deployment.**

Full VM gate: two BIOS and two UEFI cold boots of the exact candidate ISO, framebuffer-confirmed real Firefox frame *strictly below 5.000 seconds for every boot*, SHA-verified whole-root-in-RAM, media eject only after RAM verification, 4 in-browser HTTP200 receipts after eject, original kernel/root/recovery retained. Repeat the complete four-boot suite on a second run. A passing VM score does **not** certify the real physical Acer i3-540 machine, where firmware power-on time must also be measured. The original 384 MiB full-system RAM goal is also **not verified** by this pipeline.

## Operations and limitations

- Inspect runs: [Research Lab Actions](https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-ai-research-lab.yml)
- Inspect VM runs: [Puppy50 guarded VM Actions](https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-autonomous-research.yml)
- Pause: GitHub Actions → select workflow → ... → Disable workflow.
- State data, findings, and logs should be treated as **hypotheses until a VM test passes**. Never label offline proposals as independent LLM agents.
- To add new **kinds of OS architecture** beyond these safe knobs, extend the allowlist, patch builder, matching validator, security proofs, and regression tests on a reviewed branch first.
- This is recurring GitHub-hosted automation, not continuous 24×7 provisioned servers, 128 GPU nodes, or a cloud model contract.
