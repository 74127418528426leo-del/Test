# Puppy50 / Firefox sub-5-second goal — Nov 14, 2026 experiments

**Threshold not met.** Do not turn any of the measurements below into a product promise. The clock measures a genuine Firefox ESR home-window framebuffer from **before the QEMU process launches**, not from after Linux boots. OS RAM migration is validated **later**, before simulated boot-media ejection. Each matched comparison controls the host within the same experiment; results from different GitHub Actions hosts must not be added together.

## Proven, published fallback

- [v150 experimental ISO / ZIP release](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v150-vt7-early-firefox-experimental) with four independent exact-image BIOS/UEFI checks; retains v115 rescue on a separate recovery USB.
- [v151 verified Firefox software WebRender and nice −10](https://github.com/74127418528426leo-del/Test/actions/runs/43541098999): matched mean **8.03s** versus **9.15s** nice −5, two candidate boots 8.04/8.02s. Independent candidate BIOS 7.84s, UEFI 12.69s; all six RAM/eject/browser-HTTP200 checks succeeded. Not sub-five.

## Negative findings (do NOT publish these as faster systems)

| Test | Same-host control (mean Firefox frame) | Candidate (mean) | Exact result and failure |
|---|---:|---:|---|
| [v153, nice −10 → −15](https://github.com/74127418528426leo-del/Test/actions/runs/43599588303) | 7.57s | **8.815s** | 1.245s slower; all 4 matched RAM/HTTP succeeded; independent firmware stage only 5/6 HTTP receipts (failed) |
| [v154, nice −15 → −19](https://github.com/74127418528426leo-del/Test/actions/runs/43599878629) | 7.16s (raw) | **6.76s** (raw) | Candidate real Firefox window 6.76s twice, but server logged only 1/4 post-eject HTTP responses; complete safety gate failed |
| [v157, Openbox delayed 2 → 4s](https://github.com/74127418528426leo-del/Test/actions/runs/43600224993) | 8.525s (raw) | **8.965s** (raw) | 0.44s slower; only 2/4 post-eject HTTP receipts, complete gate failed |

**Do not add fractional gains from separate CI hosts** or claim these unaccepted candidates beat v151.

## Firefox anonymous startup cache: not yet successfully generated

- [v152](https://github.com/74127418528426leo-del/Test/actions/runs/43543365213): a real Xvfb Firefox window existed, but the sandboxed builder did not produce a genuine `startupCache`; exit timeout 124.
- [v155](https://github.com/74127418528426leo-del/Test/actions/runs/43599947995): WM_DELETE_WINDOW led to exit status 139 (segfault), profile directory remained empty, no `startupCache`.
- [v156](https://github.com/74127418528426leo-del/Test/actions/runs/43600322572): corrected the offline generator to use the same single-dash `-profile` syntax as the working live ISO. The generator still exited 139 and no profile cache existed. Reject; never fabricate a cache or include histories, secrets or other user data in an image.

## Audited newer ISO in release gate

[v158 audited software WebRender + Firefox nice −10 release CI](https://github.com/74127418528426leo-del/Test/actions/runs/43600823610) rebuilds the exact known-good v151 experimental ISO, verifies binary-equal kernel/root/full-RAM recovery, and requires **two BIOS and two UEFI real cold Firefox boots**, each with a post-eject HTTP 200 receipt. Only if all four pass will the workflow publish v158 ISO and ZIP plus cryptographic checksums. Label it **experimental, NOT verified five seconds**. If it fails, retain the immutable v150 ISO and ZIP.

## Hardware and release constraints

Physical Acer X3950 i3‑540, firmware POST, USB controller/flash latency, Intel i915 graphics, real Wi-Fi, dual displays, and 4K sites are **NOT** tested by 2-vCPU KVM feature-mask emulation. The 664+MiB compressed root and real Firefox RAM usage rule out the original 384MiB entire-system-in-RAM target under the unchanged design. Never unplug actual boot media before a **checksum-verified RAM READY** message, and keep v115 external recovery media because the fast BIOS Shift-key menu rescue path has not been physically certified.

A verified strict **5.000 seconds** first Firefox frame on the actual target machine requires direct power-on to browser timing on that hardware. Even a fast single VM sample does not certify a sub-five-second physical OS.
