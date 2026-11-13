# Puppy50: authentic Firefox cold startup under five seconds — verification log

**Date:** 2026-11-13. **Status:** Target **NOT MET** by any completed test. No new ISO is authorized as a verified five-second cold-boot image.

## Unchanged measurement contract

Measure from the monotonic clock **before launching QEMU** (not from a boot menu, suspended machine or ready kernel) until a **real rendered Firefox page** appears in a QEMU framebuffer. Confirm the whole root was copied into RAM and **verified by checksum before virtual CD ejection**; the browser must subsequently make an authenticated new **HTTP 200** request. No fake framebuffer, process-launch-only result or warmed VM. These are modern KVM hosts with a restricted Westmere-compatible *feature mask*, not an emulation of a real 2010 Acer i3-540's clock, cache or disk speed. Physical Acer X3950, i915, Wi-Fi, real USB boot and 4K video are untested; do not promise these.

## Proven, published reference

- [Puppy50 v122 experimental LZ4 / Zstd release](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v122-direct-fast-codec-experimental). This is the latest independently tested downloadable experimental ISO, **not** a guaranteed under-five-second build.
- [Six-boot, three-way same-host benchmark](https://github.com/74127418528426leo-del/Test/actions/runs/43499812972): genuine Firefox first-frame means **7.955 s** original v117, **7.385 s** early X11 Zstd, **6.755 s** early X11 LZ4. Six of six SHA-verified RAM copies, safe ejections and browser HTTP200 passed. LZ4 compressed root about **919 MiB**, Zstd about **664 MiB**. The smaller Zstd version reaches RAM READY faster and is generally safer for constrained RAM.
- [Separate original v115 recovery ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v114-fast-verification-experimental) must remain available on distinct recovery media; published v117/v122 fast BIOS Shift-key menu recovery was not hardware certified.

## Latest architecture experiments (same-host comparisons only)

| Controlled test | Reference mean | Candidate mean | Result |
| --- | ---: | ---: | --- |
| [v126 early-Xorg with direct parallel nonroot Firefox](https://github.com/74127418528426leo-del/Test/actions/runs/43505491538) | 8.830 s | **8.515 s** | 0.315 s gain, working 4/4 HTTP and SHA RAM |
| [Direct Firefox inside shared Openbox DBus session, separately audited](https://github.com/74127418528426leo-del/Test/actions/runs/43512098514) | 7.610 s | 7.690 s | 0.080 s slower, reject; all four HTTP200 and SHA RAM confirmed in independent log audit |
| [Skip global udev settle after QEMU DRM driver initialized](https://github.com/74127418528426leo-del/Test/actions/runs/43510839117) | 7.720 s | 7.705 s | 0.015 s gain, below meaningful test resolution; reject; four valid HTTP200 |

The new DRM initialization optimization **did not** improve Firefox meaningfully. The shared Openbox DBus version also failed its original reporting script because a serial timestamp was malformed, **but independent analysis of the real saved guest data, 4 screenshots and HTTP server receipts passed**; timing was genuinely slower.

## Open experimental verifications in separate CI

- v131: early libxul.so page-cache read-ahead **concurrent with DRM startup**, with root/kernel/firefox binary and full-RAM fallback unchanged. Separate 2×2 A–B–B–A cold test. The test must **not** be counted as working until the complete result/HTTP gate is reported.
- v132: **identical published v122 LZ4 ISO** with two versus four QEMU vCPUs, to investigate CPU contention; **hardware configuration test, not an OS improvement**. The physical Acer has two cores and four logical threads but a much older core/memory hierarchy, so the modern KVM host results are not a physical Acer prediction.

### Release gate

A five-second cold-boot claim requires **every tested candidate boot at <5.000 seconds**, multiple matched repetitions, real Firefox rendered UI, original sandbox and networking retained, safe checksum-verified full-RAM transition, and a new HTTP200 after eject. For the user's physical Acer, real cold power-on timing and hardware functional checks would also be required. Under these constraints, **no v130–v132 build can be published as a five-second OS without further evidence**.

The old 384-MiB whole-system-in-RAM Firefox target is impossible with the currently retained 664-MiB compressed Zstd SquashFS alone. Do not disable browser security, disable site isolation, or substitute a warm snapshot/suspend for a cold boot to obtain an attractive timing.
