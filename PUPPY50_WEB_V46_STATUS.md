# Puppy50 Web v46 — RAM-only browser-system engineering (2026-11-02)

## Proven, using original KVM guest serial evidence

1. Alpine x86-64 kernel **6.18.60-0-lts** and custom RAM-only initrd booted.
2. The previous v45 boot failure was not caused by the browser: the 103 selected kernel modules were present but their .ko.gz filenames could not be resolved in BusyBox's early-boot modules.dep.
3. Converting the selected early-boot modules into regular .ko files and regenerating modules.dep fixed that failure: **all 14 monitored kernel module loads returned 0**.
4. The guest discovered the QEMU optical CD at `/dev/sr0`, copied **387,690,496 bytes (369.730 MiB)** of XZ-compressed browser OS into RAM, unmounted the boot CD and switched to a RAM-backed SquashFS+OverlayFS root.
5. Alpine OpenRC successfully started on this RAM-backed root at **1,024 MiB allocated RAM**. The virtual CD was subsequently ejected in QEMU.
6. **Xorg failed** to start; Firefox rendering, keyboard/mouse interactivity and 384 MiB operation are **not** verified. A subsequent isolated graphics experiment adds VESA/fbdev fallbacks and QEMU DRM devices and collects the Xorg error log.

## Compression and feasibility

- Original complete BookwormPup64 SFS data: 743.746 MiB, v43 XZ version: 627.590 MiB.
- v44 full browser-only Alpine compressed root: 480.414 MiB.
- v45/v46 hardware-focused browser-only root: **369.730 MiB** (actual SquashFS size), which is still **too big for 384 MiB total** once kernel, graphics and Firefox allocations are included.
- 384 − 369.730 = **14.270 MiB available** before runtime. Reserving a merely illustrative 128 MiB for runtime would require a compressed root of at most 256 MiB. The real browser's working-set requirement still needs measurement.
- Pruning drivers means universal hardware coverage has **not** been demonstrated. Testing on Intel i915 graphics, networking, input and dual monitors remains required.
- Do not disable Firefox security protections to game memory numbers.

## Evidence and next gates

- Source branch: [puppy50-v46-boot-media-diagnostics](https://github.com/74127418528426leo-del/Test/tree/puppy50-v46-boot-media-diagnostics).
- Verified RAM-copy early-boot KVM evidence: [Actions run 41531831667](https://github.com/74127418528426leo-del/Test/actions/runs/41531831667) / its evidence artifact.
- Graphics correction work: [Actions run 41533089646](https://github.com/74127418528426leo-del/Test/actions/runs/41533089646). **Don't call it successful until its real guest logs and screenshots are reviewed.**
- Real boot acceptance: RAM copy; switch_root; CD unmount/ejection; Xorg and browser actually running; offline HTML rendered; keyboard/mouse response; networking, Wi-Fi, audio, USB, dual displays; repeated cold-boot memory/PSI trials.
- **Never publish the experimental v46 ISO as a finished browser OS until the complete tests pass.**
