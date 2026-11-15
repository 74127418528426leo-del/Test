# Puppy50 AutoLab — guarded recurring VM optimization

## What is running
A scheduled GitHub Actions workflow in this repository's **default branch**:
`.github/workflows/puppy50-autonomous-research.yml`.

- Schedule: 01:17, 07:17, 13:17, 19:17 **UTC** daily. GitHub may delay or skip a schedule.
- Concurrency: at most **one full VM experiment** at a time, with a 65-minute timeout.
- Candidate catalog: Firefox nice `-10,-9,-11,-8,-12,-13` crossed with final-initramfs Zstd compression `1,2,3,4,5,6` = 36 distinct hypotheses; max two recorded trials each. No endless repeat of exhausted hypotheses.
- Engine: existing exact v159 research ISO construction based on verified pinned source and v115 image checksums; modifications are limited to known nonroot Firefox niceness and final-initramfs compression level.
- Verification per candidate: **two BIOS and two UEFI** independent QEMU cold boots from before VM process startup, real Firefox rendered window, real guest-browser HTTP200 *after* checksum-verified RAM migration and optical media eject, plus kernel/root/fallback checks.
- Success criterion: all four first-frame measurements strictly **below 5.000 seconds** and **every functional gate passed**, confirmed on **two separately triggered runs** of the same candidate. This is a **VM-only research milestone**: real Acer power-on-to-browser startup is not certified without physical measurement.
- Rejected candidates are *not* published. This workflow does not create ISO releases or alter existing recovery ISOs.

## Persistent state, controls and evidence
- History is written only to branch `puppy50-autolab-state`, file `experiments/puppy50-autolab/state.json`. No main-branch website rebuild on each measurement.
- GitHub Actions logs and short-lived evidence artifacts are produced for every attempt. Evidence artifact retention: 7 days.
- Once the VM goal passes independent confirmation, the controller skips new compute automatically.
- If the candidate catalog is exhausted, the controller also skips further expensive VM runs rather than repeat ineffective work. New engineering hypotheses must be vetted and added before restarting.
- Stop/pause: Repository → **Actions** → **Puppy50 autonomous guarded VM experimentation** → **...** → **Disable workflow**.
- Resume: enable that workflow from GitHub Actions. Never edit the success state to claim unperformed tests.

## What this is NOT
- This is **not 128 AI agents or GPU servers**. It is automated workflow orchestration using standard GitHub-hosted CPU runners and QEMU/KVM. The earlier 128-worker experiment covered independent CPU compression tasks, not LLM instances.
- It does not guarantee round-the-clock uninterrupted compute; GitHub scheduling and resource limits apply.
- It does not imply 384 MiB full-RAM Firefox, physical i915/Wi-Fi compatibility, or an under-five-second physical Acer boot.
- There is no automatically provisioned paid compute or API model bill.

## Existing proven baseline
Puppy50 v159 experimental release: https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v159-verified-browser-httpsafe-experimental

The v159 evidence reports four cold BIOS/UEFI functional boots but explicitly does **not** certify an under-five-second machine.
