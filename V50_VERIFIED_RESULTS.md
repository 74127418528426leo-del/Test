# Puppy50 Web v50 — Verified real KVM results

2026-11-02. Completed GitHub Actions run:
https://github.com/74127418528426leo-del/Test/actions/runs/41544771276

This is a real KVM result, not proof of 384 MiB.

## Controlled experiment
- Same v49-style bootless RAM-root, Linux kernel, Firefox ESR, Xorg/Openbox, and QEMU standard VGA at 512, 768 and 1024 MiB.
- All three guests copied the compressed SquashFS into RAM-backed tmpfs, switched root, ejected the virtual CD, started Xorg and requested Firefox.
- Real guest serial monitor gathered 44, 45, 44 complete samples, respectively.
- Kernel oom_kill counter **did not increase** in any of the three observation windows.
- Manual framebuffer inspection at 145 seconds: 512 MiB black with pointer; 768 MiB black with pointer; 1024 MiB displayed Firefox and the packaged local HTML page.
- Guest memory-PSI fields were unavailable in these measurements, so no PSI claim is possible.

| Guest RAM | 512 MiB | 768 MiB | 1024 MiB |
|---|---:|---:|---:|
| Complete memory samples | 44 | 45 | 44 |
| Maximum monitored Firefox-related processes | 1 | 4 | 9 |
| Kernel OOM kills observed | 0 | 0 | 0 |
| Minimum reported MemAvailable | 49.312 MiB | 42.777 MiB | 10.617 MiB |
| Visible browser page at t=145 s | NO | NO | YES |

At 512 MiB the Firefox parent remained present but showed only about 27-33 MiB of RSS in representative samples, without the complete Firefox process tree. At 768 MiB more processes appeared but the window was still black in the tested interval. At 1024 MiB multiple content processes existed and the local page rendered.

## Interpretation and open questions
- **No kernel OOM kill is not proof of sufficient memory.** Firefox can fail allocations, stall, or decline to spawn content processes without a kernel OOM kill.
- MemAvailable is a reclaimability estimate, not reserved browser memory; the minimum value was smaller at 1024 MiB in part because more browser processes were running.
- No captured Firefox exit or meaningful stderr identifies a root cause yet. The kernel memory-pressure interface did not supply usable PSI readings.
- No proof of HTTPS (guest had no network), real browser interaction, WebGL, USB/audio, Wi-Fi, or the real Acer Intel graphics.
- Therefore, the rigorous functional threshold of the v50 Firefox image remains above 768 MiB within the observed window, with rendering demonstrated at 1024 MiB. The exact threshold is unknown.

## Next falsifiable steps
1. Observe live Firefox parent VmSize, VmRSS, VmPeak, process state, wait channel and thread count. Check X11 mapped windows and failed process spawning.
2. Binary-search the rendered-page threshold with unchanged image at 896 and potentially 960 MiB.
3. Test a separately labeled QEMU-specific image without physical-device firmware, measuring exact compressed SquashFS changes and boot success. This is NOT a real-hardware variant.
4. In a separate, ABI-verified graphics path, evaluate smaller Intel Crocus/Mesa drivers, while keeping Firefox TLS and sandbox protection.
5. Count 384 MiB success only after actual RAM-root copy, boot-media removal, visible browser interaction, secure HTTPS and stability. A root copy alone is insufficient.

The GitHub Actions artifact has seven-day retention; source and this report remain in the repository.
