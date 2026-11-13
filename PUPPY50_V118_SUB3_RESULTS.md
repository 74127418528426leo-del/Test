# Puppy50 v118 — genuine cold-start Firefox under 3 seconds research

**Date:** 13 November 2026. **Status:** UNDER THREE SECONDS **NOT ACHIEVED**. Do not ship a “3-second ISO” or describe a resume, an image placeholder or process spawning as Firefox visibly ready.

## Definition and immutable baseline

The clock begins **immediately before spawning QEMU/KVM**. The first frame is accepted only if the real 1280×800 Firefox desktop/home-page framebuffer matches the original multi-pixel detector. The proof additionally requires the full original browser, system network access, checksum-verified complete compressed-root copy to RAM, successful virtual medium ejection **only after verified RAM READY**, and new real HTTP browser activity **after ejection**. A physical Acer X3950 power-on timer is separate and has never been tested on real hardware.

Baseline **released v117 experimental ISO** is exactly `a7fe532f501b9541c3a4fc22455e57ef79b8389eac6561720c25d7e188231b83` (906,297,344 bytes). It remains available unchanged.

Final [v117 release A–B–B–A test](https://github.com/74127418528426leo-del/Test/actions/runs/43436287638): mean original v115 9.275 s vs released v117 candidate **8.360 s**. A separate same-host test showed 7.155 s v117, but this did not reproduce below 8 on the release runner, so even eight seconds is not guaranteed.

## Experiment 1 — bypass virtual BIOS Syslinux path by direct host kernel injection

This is intentionally a **diagnostic, NOT a bootable PC/USB image**. Both paths still used the identical v117 root image, guest virtual AHCI CD media, 2 virtual CPUs, 3 GiB RAM, BIOS firmware, 0.2s framebuffer polling, and verified all four post-eject browser connections. In the alternate path only, QEMU loads the unmodified kernel/initrd via `-kernel/-initrd/-append`, removing the guest ISO bootloader dependency.

| Four matched A–B–B–A trials | Real Firefox first frame | Verified RAM-ready |
|---|---:|---:|
| Standard v117 ISO #1 | 9.44 s | 16.16 s |
| Direct host kernel #1 | 9.02 s | 15.72 s |
| Direct host kernel #2 | 8.83 s | 16.03 s |
| Standard v117 ISO #2 | 9.21 s | 15.91 s |
| **Standard mean** | **9.325 s** | **16.035 s** |
| **Direct-kernel mean** | **8.925 s** | **15.875 s** |

**Only 0.400 seconds first-frame gain, nowhere near <3 s.** Because direct kernel loading is not a physical-media cold boot, these values are useful exclusively to isolate the bottleneck, NOT a physical-boot claim. The tested system still spent ~8.9 seconds inside the remaining kernel/live-boot/session/Firefox path.

[Full reproducible successful four-VM run](https://github.com/74127418528426leo-del/Test/actions/runs/43485170362)

## Experiment 2 — move live account setup from LightDM preflight into initramfs

A separate experimental initrd patch [v118/precreate_user.py](./v118/precreate_user.py) requires the expected staged root, validates the original preflight setup, and precreates the ordinary unprivileged live account and Openbox autostart before systemd. It removes only the redundant preflight step after success, retains the original root/Firefox/kernel and all integrity checks, and refuses unfamiliar layouts. The full RAM first and recovery initrd remain byte-identical. **Research only; not yet a passed optimization.**

[Reproducible matched benchmark workflow](https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-v118-early-user-ab.yml)

## Experiment 3 — try direct X11 session after precreating user

Previous direct-X attempts in v113 failed because systemd tried to resolve the live user before it existed. This separate research branch combines the v118 early-user hook with the older direct-session experiment after that prerequisite, while preserving browser/working-network/RAM verification gates. A candidate that fails to render the browser, signal real RAM ready, remove media safely and open a new real page is automatically rejected.

[Direct-X workflow](https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-v118-direct-x-ab.yml)

## Architectural conclusions / release gate

- The v117 one-second BIOS-menu improvement was real. Bypassing the *remaining* virtual BIOS loader made only a small additional difference.
- The bottleneck for sub-3-second cold Firefox is primarily **after kernel entry**: live-root and systemd/session preparation, X11 initialization, Firefox library startup, and real first-frame rendering. No single bootloader optimization plausibly closes a ~6-second remaining gap.
- Candidate future proof requires multiple matched runs with **every candidate first Firefox frame <3.00 s** and all browser, network, RAM and recovery checks passed. Never infer the actual Intel i3-540's CPU performance from a fast VM runner with the same CPUID flags.
- The 384 MiB fully-in-RAM Firefox goal remains unmet; the **664 MiB compressed root alone** exceeds this budget. Real i915, physical Wi-Fi, dual monitors and 4K streaming are also not verified.
- Until stronger evidence, retain [v117 experimental ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v117-instant-bios-experimental) and independently keep a [v115 recovery ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v114-fast-verification-experimental), because v117's Shift-held rescue access was not demonstrated.

**Release decision: no under-3-second ISO until measurements and functional checks justify it.**
