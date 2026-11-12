# Puppy50 v116 — second research round (12 Nov 2026)

**Release decision: retain v115.** The 8-second Firefox-first-frame goal remains unachieved. These are isolated A/B research images, **not approved OS releases**.

## Verified original input

- Exact source ISO: `Puppy50_v115_Font_Cache_EXPERIMENTAL.iso`
- SHA-256: `d697081adf836b7c8b75fe352964764e082b0214a262c8d9895eb9388c3e825a`
- Full ISO: 906,297,344 bytes (864.3 MiB); compressed root 696,542,497 bytes (664.3 MiB).
- Root SquashFS: **zstd, 256 KiB blocks**; Firefox `libxul.so` 183,820,912 bytes uncompressed.
- The original root and full-RAM fallback were byte-compared unchanged in the rebuilt experimental ISO runs.

## Same-host controlled tests

All comparisons ran in A–B–B–A order, BIOS/KVM, 2 vCPUs, 3 GiB virtual RAM, virtual USB capped at 30 MiB/s. The first-screen clock starts immediately before launching QEMU (includes virtual firmware and boot menu, not physical POST). Firefox's first-home-frame detection is polling-based, and each candidate has only two measurements; differences measured in hundredths are not reliable improvements. Do **not** compare absolute timings between different host runs.

| Candidate | Baseline first-frame mean | Candidate first-frame mean | Verified RAM-ready mean (baseline → candidate) | Outcome |
| --- | ---: | ---: | ---: | --- |
| Browser-first autostart, defer auxiliary GUI processes 6 s | 15.950 s | 16.370 s | 35.915 → 36.090 s | **Reject**, no gain; all four simulated media removals passed |
| Seed pristine Firefox profile before creating user | 15.540 s | 15.525 s | 35.765 → 35.735 s | **Reject**, 0.015-second difference below measurement resolution; four media removals passed |
| Unlink nonessential memory/GUI diagnostic services | 15.52 s (first baseline) | **No Firefox frame** (first candidate) | 35.23 → **not reached** | **Reject**, safety gate correctly failed; do not ship or interpret timing |
| Defer background RAM copy from 8 to 20 s (previous round) | 14.695 s | 14.645 s | 34.870 → 46.685 s | **Reject**, no meaningful frame gain, 11.815 s worse RAM readiness |

### Evidence links

- Browser-first four-VM comparison: https://github.com/74127418528426leo-del/Test/actions/runs/43233833077
- Firefox profile four-VM comparison: https://github.com/74127418528426leo-del/Test/actions/runs/43234891341
- Optional diagnostic-service removal failed VM: https://github.com/74127418528426leo-del/Test/actions/runs/43234721306
- Exact original SquashFS compressor audit: https://github.com/74127418528426leo-del/Test/actions/runs/43235214326
- Previous delayed RAM-copy failure as optimization: https://github.com/74127418528426leo-del/Test/actions/runs/43126365660

**Safety policy:** Maintain the checksum-verified RAM transfer, keep the USB attached until green RAM READY, keep NetworkManager and its UI available, and retain the full-RAM recovery option. Never claim physical Intel i3-540, Wi-Fi, dual displays or 4K decoding were tested.

## Current research

A matched same-ISO storage-bandwidth A/B has been scheduled separately to test whether the virtual USB cap is a material part of the first-frame time:
https://github.com/74127418528426leo-del/Test/actions/runs/43235887141

This document is not evidence of an 8-second release, and no replacement ISO should be published without a reproducible win and functional tests.
