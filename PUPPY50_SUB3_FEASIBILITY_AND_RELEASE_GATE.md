# Puppy50: authentic sub-3-second cold Firefox feasibility and release contract

**Goal:** physical power-on (including firmware) through the first **real interactive Firefox window**, no warmed browser, VM state replay, screenshot placeholder, fake first frame, insecure Firefox mode or permanently attached source media. The fully safe OS must then copy its root into RAM with checksums before removable media can be ejected, preserve networking/TLS/sandbox, recovery and physical display support. This is more demanding than a fast kernel-only boot, a process-PID marker or waking an already-running session.

## What is actually measured

The existing evidence begins its reference clock **immediately before the virtual QEMU/KVM process starts** (includes virtual BIOS and bootloader but excludes a real Acer's firmware power-on delay). Browser first-frame pixels are sampled approximately every 0.2 seconds. Match images in alternating A–B–B–A order on the **same host** because KVM runner CPU speed varies.

| Proven condition, experiment | First real Firefox home frame | Important caveat |
| --- | ---: | --- |
| Published v117 BIOS/SATA release proof | mean **8.360s** | [4 matched release pipeline boots](https://github.com/74127418528426leo-del/Test/actions/runs/43436287638) |
| v122 newer early-X11/LZ4 root, same-host control | mean **6.755s**, against 7.955s original | [6 matched BIOS KVM runs, full RAM+post-eject HTTP200](https://github.com/74127418528426leo-del/Test/actions/runs/43499812972), ~255MiB larger compressed root |
| v126 **genuine X11 before PID1** | **8.70s** | [One QEMU-only first-frame proof](https://github.com/74127418528426leo-del/Test/actions/runs/43504728219), actual Xorg survived switch-root without LightDM; do **not** compare absolute timing to v122 different runner |
| v127 Firefox parallel to Openbox | mean **8.515s** vs v126 **8.830s** | [Four matched boots](https://github.com/74127418528426leo-del/Test/actions/runs/43505491538), 0.315-second same-host gain |
| v128 precreated account in compressed root | mean **8.540s** vs v126 **8.615s** | [Four matched boots](https://github.com/74127418528426leo-del/Test/actions/runs/43506349966), only 0.075 seconds, rejected |

**No tested release or prototype reaches 3.00 seconds even once.** These are KVM host timings, not old Intel i3-540 throughput. The real Acer Aspire X3950 with Intel i915 GPU, physical BIOS POST and USB/SSD storage has **not** been booted with these test images. A virtual CPUID flag mask does not emulate actual 2010 CPU performance. A true 384 MiB RAM-only Firefox + networking OS is **not** possible with the currently unchanged 664 MiB compressed SquashFS root alone, without a fundamental reduction or entirely different memory architecture.

## New Firefox-specific bottleneck under test

[Mozilla Bug 2084921](https://bugzilla.mozilla.org/show_bug.cgi?id=2084921) reports an ~1.5-second first-window-paint stall on GPU-less Linux CI due to Mesa llvmpipe shader compilation, and suggests testing software WebRender. **This issue is not proof the Puppy50 KVM guests have the same exact bottleneck.** v129 tests `gfx.webrender.software=true` as **one isolated Firefox preference only**, verifying its effective profile state and comparing four actual first frames, untouched sandbox, full RAM checksums and post-eject HTTP 200. Its results must be read before any claim that shader rendering can help.

## Important firmware and hardware limitation

Current official [coreboot supported mainboard documentation](https://doc.coreboot.org/mainboard/) does **not list the Acer Aspire X3950**, although it lists some other Acer boards. This means **no safe coreboot BIOS-flashing path for this specific board has been established**. Do not recommend experimenting with unsupported firmware flashing just to shave off seconds. This lack of a support listing is not definitive proof the board can never be ported; it is a strong reason to avoid an unvalidated firmware replacement.

Mozilla's [official Firefox build benchmarking documentation](https://firefox-source-docs.mozilla.org/performance/Benchmarking.html) suggests profile-guided optimization may improve performance, but does not guarantee any specific cold-start reduction and would require rebuilding, testing browser security and reproducing old CPU compatibility. It is not a quick kernel flag fix.

## Strict release gate

A legitimate "under three seconds" image needs: (a) **at least four authentic cold starts** of the exact immutable released ISO, first-frame before **3.00s in each** not just mean, (b) BIOS and UEFI boot paths confirmed, (c) real Firefox browser interacting with fresh HTTPS pages and the network after the full root SHA verification and media ejection, (d) working unprivileged account, sandbox, CA store and recovery media, and (e) an **independent physical Acer hardware test** before advertising the old machine as supported.

A fast **resume** from RAM, hibernation restore or VM snapshot may meet a three-second display goal on some systems, but it is a *different metric from power-off cold boot* and must always be labeled as such. Do not alter the clock's start or present it as a compliant result.

**Status:** experiment pipeline active; current known production-ready under-3-second OS: **none**. Keep released [v122 experimental ISO/ZIP](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v122-direct-fast-codec-experimental) and independent [v115 recovery](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v114-fast-verification-experimental), both with appropriate safety warnings.

## Completed v129 renderer policy experiment

The [four VM results](https://github.com/74127418528426leo-del/Test/actions/runs/43508019175) showed **6.880s** mean first Firefox frame for v127 baseline versus **6.790s** for v129 with a Firefox software-WebRender policy file installed before startup (difference **0.090s**). All four actual browser frames, RAM checksums, safe ejects and post-eject HTTP200 checks passed. However [the independent saved-artifact audit](https://github.com/74127418528426leo-del/Test/actions/runs/43509153482) found that the benchmark's asynchronous guest reporter never confirmed the preference in Firefox's actual user profile. The primary workflow correctly failed its policy-proof check. Therefore **do not claim the renderer setting was effectively applied or that a meaningful speedup was verified**. The sub-three-second goal remains unmet; the experiment is not eligible for release. Its result does not invalidate Mozilla's separate GPU-less CI bug report.
