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

## Significant new result — virtual boot-media bandwidth (unchanged v115 ISO)

A four-boot A–B–B–A comparison used the **identical verified v115 ISO** and switched only the QEMU virtual USB read cap from 30 MiB/s to uncapped. Both conditions used 2 virtual CPUs, 3 GiB RAM, BIOS, and the same host. All four trials saw the actual Firefox home frame, completed RAM-copy verification, removed virtual boot media and interacted with the browser afterward.

| Virtual media condition | First Firefox frame mean | Verified RAM-ready mean |
| --- | ---: | ---: |
| 30 MiB/s capped USB | 14.57 s | 35.205 s |
| Uncapped USB | **10.65 s** | **19.28 s** |

**Observed first-frame difference: 3.92 seconds.** This is a genuine same-host experiment, but **uncapped virtual USB is not a measured SSD or physical USB device**. The result does not prove eight seconds or predict exact Acer X3950 performance. Source: https://github.com/74127418528426leo-del/Test/actions/runs/43235887141

## Instrumented v115 startup milestones

An independently booted diagnostic v115 copy emitted guest uptime markers: initial live-root hook at **1.99 s**, LightDM login preflight at **5.09 s**, and Firefox execution command at **6.88 s**. Its first visible frame occurred at **14.69 s on the separate host/QEMU launch clock**. These numbers must not be naively subtracted because the clock origins differ; the record places a substantial portion of startup after kernel/live-root setup and during browser initialization. The diagnostic VM safely removed its boot media after verified RAM readiness. Evidence: https://github.com/74127418528426leo-del/Test/actions/runs/43236803856

Next separate comparisons: 2 versus 4 virtual logical CPUs and uncapped XHCI versus emulated SATA/AHCI. Both are deployment/runtime tests of the unchanged ISO and will not be represented as improved ISO bytes.

## Follow-up CPU scaling (unchanged v115 ISO, uncapped virtual USB)

Four A–B–B–A boot-and-ejection runs with identical v115 bytes and 3 GiB guest RAM tested two versus four virtual logical CPUs. First Firefox screen averaged **11.420 s at 2 vCPUs** and **11.425 s at 4 vCPUs**. Both completed RAM verification and virtual-media removal, but the **0.005 s** difference is entirely uninformative as an improvement. Reject adding virtual CPUs purely to improve this startup metric. Evidence: https://github.com/74127418528426leo-del/Test/actions/runs/43237354016

## SATA/CD-ROM correctness

The initial test treating the read-only ISO as an `ide-hd` failed QEMU launch (`Block node is read-only`). Reattaching it as `ide-cd` enabled a Firefox frame at **8.14 s** in one diagnostic run and completed its RAM-copy checksum at **15.26 s**, but the old USB `device_del` harness failed (`Bus 'ahci.0' does not support hotplugging`). **That result is incomplete and not a passing boot-and-ejection trial.** The test was corrected to use QMP/HMP CD *medium eject* instead of removing the AHCI device, and separate A–B–B–A runs are needed before any SATA benefit claim. Sources: https://github.com/74127418528426leo-del/Test/actions/runs/43238758836 and https://github.com/74127418528426leo-del/Test/actions/runs/43239297667

## Verified virtual SATA/CD-ROM media ejection and post-ejection browser use

The SATA benchmark harness now sends QMP/HMP `eject -f livecd` and verifies the **medium is no longer inserted**, rather than attempting unsupported AHCI device hotplug. All four comparable VMs booted, rendered Firefox, signaled verified RAM migration, ejected their boot medium, and exercised the browser afterward.

| Separate same-host experiment | Baseline mean first Firefox frame | Candidate mean first Firefox frame | RAM ready baseline → candidate |
| --- | ---: | ---: | ---: |
| **2 vCPU**: uncapped XHCI USB vs uncapped SATA/AHCI CD | 11.445 s | **10.255 s SATA** | 19.375 → 17.680 s |
| **2 vCPU USB vs 4 vCPU SATA** (two simultaneous variables) | 9.745 s | **8.970 s combined** | 17.380 → 15.615 s |

These mean values come from **two trials per variant**, each in A–B–B–A order on one GitHub Actions host. The two experiments used different hosts and therefore their absolute times must not be compared as proof of a CPU gain; the independent 2-vs-4-vCPU test showed no speedup. These are 0.8-s polling measurements with capture overhead, not physical Acer power-on timings. The separate fine-polling study is needed for an exact <=8s threshold.

Evidence: https://github.com/74127418528426leo-del/Test/actions/runs/43239297667 and https://github.com/74127418528426leo-del/Test/actions/runs/43239306226

**Important:** There is no code-level ISO optimization here. The same exact v115 ISO (SHA-256 `d697081adf836b7c8b75fe352964764e082b0214a262c8d9895eb9388c3e825a`) booted from different emulated controllers. These VM results neither certify real SATA SSD speeds nor confirm safe physical-media removal on the user's Acer. 
