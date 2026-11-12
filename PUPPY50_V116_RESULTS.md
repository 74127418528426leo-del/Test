# Puppy50 v116: controlled optimization results

Status: **diagnostic branch, not a release**. Keep the published v115 ISO as the current usable experimental baseline. The 8-second first Firefox frame and the 384 MiB RAM-only Firefox goals have **not** been achieved.

## Experiment: background RAM-copy contention hypothesis

The verified v115 ISO (SHA-256 `d697081adf836b7c8b75fe352964764e082b0214a262c8d9895eb9388c3e825a`) served as the control. Candidate changed only the staged migration helper from `"$B" sleep 8` to `"$B" sleep 20`. The boot archive was repacked and release-file SHA-256 manifest entries updated. Byte-compare checks confirmed the original root SquashFS and full-RAM fallback image were unchanged.

All four alternating BIOS/QEMU/KVM trials (baseline, candidate, candidate, baseline) completed, saw the Firefox home, reported verified RAM readiness, safely simulated virtual USB removal, and continued browser operation without reported errors. Environment: two virtual CPUs, 3 GiB RAM, USB read cap 30 MiB/s, matched host. Timer began immediately before launching QEMU, not at physical power-on. VM CPU feature mask is not proof of physical Intel i3-540 performance.

| Trial | First Firefox frame | Verified RAM ready | Virtual media safely ejected |
| --- | ---: | ---: | :---: |
| v115 baseline 1 | 14.71 s | 34.89 s | yes |
| v116 candidate 1 | 14.64 s | 46.82 s | yes |
| v116 candidate 2 | 14.65 s | 46.55 s | yes |
| v115 baseline 2 | 14.68 s | 34.85 s | yes |
| Baseline mean | **14.695 s** | **34.870 s** | yes |
| Candidate mean | **14.645 s** | **46.685 s** | yes |

**Decision: REJECT.** The observed mean first-frame difference, 0.05 s, is smaller than the sampling and host variability. RAM verification becomes about 11.82 s later. Deferring background copying is not a justified startup optimization. Revert to the original 8-second migration schedule; do not offer the test ISO as a faster upgrade.

Evidence: https://github.com/74127418528426leo-del/Test/actions/runs/43126365660

## Other verified facts and previously explored approaches

- A checksum-matched v115 ISO inspection found 1-second boot-menu timers on both BIOS (Syslinux `timeout 10` tenths) and UEFI (GRUB `timeout=1`); removing the menu cannot supply six seconds.
- Historical v115 hot-pages prefetch A/B work **slowed** the first frame 14.89 → 15.61 s (same-host matched means), and v115 small prefetch gained only 0.06 s. Do not repeat them as presumed breakthroughs. Evidence: https://github.com/74127418528426leo-del/Test/actions/runs/42696016668 and https://github.com/74127418528426leo-del/Test/actions/runs/42747710853 .
- Earlier v113 work found no meaningful first-frame gains in generic libxul/omni.ja prefetch, early display-manager starts, X11 direct-session replacement, aggressive smaller SquashFS block compression, or removal of a 0.03-s udev wait.
- The compressed live root remains about 664 MiB; this design cannot provide a verified entire-root RAM-only boot in 384 MiB.

## Next falsifiable research step

Instrument correlated timestamps and resource utilization **without changing functional services** for kernel/initramfs completion, root mount, graphical preflight, Xorg/LightDM, non-root Firefox exec, first browser frame, and first local-JavaScript response. Keep host and guest timestamps on distinct clocks unless synchronized with a common event. Compare the per-stage budget to identify the true browser-critical-path delay. Try one reversible optimization at a time with repeated A/B controls and prove browser/network/USB-removal behavior before shipping. Do not replace the published v115 ISO on speculation.
