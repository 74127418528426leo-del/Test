# Puppy50 Firefox v99 — real compressed-RAM (zram) experiment

**Experiment:** 2026-11-03/04. **Live ISO branch:** v91 Debian 13 Live Firefox ESR 153.6 (no browser/CA/network policy changes). **Actual KVM run:** https://github.com/74127418528426leo-del/Test/actions/runs/41747335187

## Independently inspected guest screen results

| RAM allocation | Configuration | Actual website screenshot timeline |
|---|---|---|
| 2048 MiB | Original, no zram | Firefox local page at 100s, `https://example.com/` visibly rendered by **185s**, persisted through 300s |
| 2048 MiB | zram 1GiB LZ4 | Firefox local page still visible at **220s**, `https://example.com/` visible by **300s** |
| 2560 MiB | zram 1GiB LZ4 | External HTTPS website visible by **185s**, persisted through 300s |

All three real VMs reported CA-verified guest-side public HTTPS, Firefox as the unprivileged live account, and continued operation after ejecting the original boot medium. **A successful process check is not proof of visible websites; these website findings were established from independently inspected actual QEMU images.**

## Critical memory discovery

At 2048 MiB with zram:
- 17 actual serial memory samples.
- zram was **actually enabled** with LZ4; no physical disk swap was created.
- 1GiB logical zram swap became almost completely full.
- **Largest observed compressed-swap physical allocation: 1010.0 MiB.**
- **Largest observed uncompressed swap allocation: 1016.34 MiB**, indicating almost no effective compression of the sampled swapped data.
- Lowest sampled Linux MemAvailable: **198.80 MiB**; zero reported OOM kills.
- The browser was noticeably slower to reach the website than in the no-zram 2GiB run; this is one observation, not statistical proof of slowdown.

At 2560 MiB with zram: physical allocation reached **1012.65 MiB**, and lowest sampled MemAvailable was **537.48 MiB**. Merely seeing swap activity is not proof of beneficial RAM savings; used zram pages still occupy physical RAM.

## Decision

**Do not promote this 1GiB zram configuration.** It improved neither observed 2GiB navigation speed nor memory efficiency. The original maintained Firefox image is currently preferable. This evidence does **not** prove a 2GiB guaranteed minimum: previous v94 2GiB repeated trials failed to complete navigation; the v99 original 2GiB succeeded. Testing reproducibility and collecting no-zram guest memory pressure is the next step (v100).

## Evidence

- Original 2048MiB frames + logs: https://github.com/74127418528426leo-del/Test/actions/runs/41747335187/artifacts/13284742195
- zram 2048MiB frames + guest telemetry: https://github.com/74127418528426leo-del/Test/actions/runs/41747335187/artifacts/13285360523
- zram 2560MiB frames + guest telemetry: https://github.com/74127418528426leo-del/Test/actions/runs/41747335187/artifacts/13284900965
- Build security file hash equality artifact: https://github.com/74127418528426leo-del/Test/actions/runs/41747335187/artifacts/13283584357
- v99 test-only ISO artifact: https://github.com/74127418528426leo-del/Test/actions/runs/41747335187/artifacts/13284133680
- Reference: https://docs.kernel.org/admin-guide/blockdev/zram.html

No bare-metal physical Wi-Fi adapter or any-network capability has been verified. The goal of 384 MiB for modern Firefox has not been achieved.
