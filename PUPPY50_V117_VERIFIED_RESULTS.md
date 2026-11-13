# Puppy50 v117 — real BIOS fast-boot breakthrough, recovery still under validation

**Research date:** 2026-11-13. This is a **test-only candidate**, not a production-ready ISO. Target: genuine Firefox first-frame <=8 seconds, with safe RAM-only transition and recovery. Measurements are from QEMU/KVM, not the user's physical Acer X3950.

## Proven in controlled A–B–B–A BIOS SATA KVM trial

- Unchanged v115 input ISO SHA-256 `d697081adf836b7c8b75fe352964764e082b0214a262c8d9895eb9388c3e825a`.
- New candidate modifies only the *BIOS* Syslinux boot menu using `menu shiftkey` while leaving the kernel, compressed root (664 MiB), both initrd versions, full-RAM fallback image, network drivers and UEFI GRUB menu byte-for-byte unchanged. ISO SHA-256 manifest updated.
- QEMU/KVM, 3 GiB guest RAM, 2 i3-540-conservative virtual CPUs, AHCI virtual CD-ROM on uncapped backing, BIOS boot, 0.2-second framebuffer polling plus screenshot overhead. Clock starts immediately before QEMU launch; **not physical power-on**.

| Run | First genuine Firefox home | Verified full RAM ready | Virtual media eject + post-eject browser |
| --- | ---: | ---: | --- |
| Original v115 #1 | 8.25 s | 15.39 s | PASS |
| v117 Shift BIOS #1 | **7.16 s** | 14.29 s | PASS |
| v117 Shift BIOS #2 | **7.15 s** | 14.28 s | PASS |
| Original v115 #2 | 8.21 s | 15.33 s | PASS |
| **Original mean** | 8.230 s | 15.360 s | PASS |
| **v117 candidate mean** | **7.155 s** | **14.285 s** | PASS |

The first-frame mean gain is **1.075 seconds** for the actual VMs. The new candidate met the **<=8-second threshold in both of its tested BIOS SATA runs**. Evidence https://github.com/74127418528426leo-del/Test/actions/runs/43433005041

This performance result does NOT apply to UEFI, to slow USB 2.0, to all host CPU combinations, or to real physical Intel i3-540 until separately measured.

## UEFI functionality

The candidate leaves the UEFI GRUB menu unchanged. A separate KVM UEFI boot passed Firefox first-frame, verified RAM copy, AHCI CD-medium ejection, a subsequent webpage request, and no recorded test errors. Its first frame was **14.69 seconds** (not an 8-second result). Evidence https://github.com/74127418528426leo-del/Test/actions/runs/43434331282

## Release blocker: recovery menu

Original Syslinux contains **Full RAM first** and **Recovery** as distinct boot entries; these remain in the ISO. Syslinux officially documents `MENU SHIFTKEY`: unless Shift/Alt or Caps Lock/Scroll Lock is held when entering the menu, launch default immediately. A manual recovery test that attempted to hold Shift through a QEMU keyboard event did **not successfully select** the Full RAM menu; it ended up booting the fast default. Therefore recovery accessibility is **not yet verified** and no v117 image should be published as the new recommended production release until independent recovery selection is demonstrated.

A safer follow-up additionally changes BIOS `timeout 10` (one second) to `timeout 0`. In Syslinux, timeout zero means **no timeout**, but `MENU SHIFTKEY` still immediately boots default when Shift is *not* held. Thus a Shift-held recovery menu should stay open indefinitely. That two-config change is undergoing an additional matched A/B speed test and boot-menu timing diagnostics. UEFI unchanged.

## Limitations and gates

- The RAM-ready marker must be produced only after copying the complete root SquashFS to tmpfs, verifying its SHA-256, switching device-mapper backing, and detaching the old medium. Never remove a physical boot USB before green RAM READY.
- The 384 MiB RAM-only Firefox goal is **not achieved**: the unchanged 664 MiB compressed root exceeds this budget on its own.
- Physical Acer POST, SATA SSD/USB throughput, Intel i915 rendering, Wi-Fi, dual monitors and 4K video were not tested here.
- No browser TLS or Firefox sandbox protections were weakened by this BIOS-only change.
- Original v115 ISO remains available as the current separately tested recovery baseline.

**Next:** show reliable Shift-held full-RAM recovery, verify repeated <=8-second candidate boots, and publish a separately labeled experimental v117 ISO and ZIP with exact checksums. Do not claim physical-hardware performance.
