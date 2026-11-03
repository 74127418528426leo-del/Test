# Puppy50 v52 — Verified Firefox wait-state evidence

Date: 2026-11-02. Completed real KVM run:
https://github.com/74127418528426leo-del/Test/actions/runs/41548426953

## Actual observations

The same Firefox ESR + Xorg/Openbox RAM-root image was booted at 512 and 1024 MiB in QEMU standard VGA. Both completed the verified RAM-root copy/switch and virtual CD ejection.

| Measurement | 512 MiB | 1024 MiB |
|---|---:|---:|
| Firefox-named state observations | 41 | 59 |
| Firefox-named unique process IDs | 1 | 6 |
| Maximum threads in one monitored Firefox-named process | 17 | 82 |
| Max sampled VmSize (virtual address space) | 2834.54 MiB | 11326.76 MiB |
| Max sampled VmPeak (virtual address space) | 2834.54 MiB | 19468.53 MiB |
| Kernel OOM kills observed | 0 | 0 |
| Lowest sampled MemAvailable | 48.344 MiB | 24.547 MiB |
| Browser visibly rendered local page | NO | YES |

In the 512 MiB guest the Firefox parent was sampled running/runnable (state R with wait channel 0) 29 times out of 41, in an uninterruptible squashfs_decompress wait 6 times, and in an ordinary poll wait 4 times. The 1024 MiB guest also frequently experienced squashfs_decompress waits, page-cache folio waits and some bio waits, yet Firefox rendered successfully.

**Do not infer a deadlock or single root cause from this.** SquashFS decompression could be a contributing cost, but the same kernel path occurs in the successful 1 GiB case. No kernel OOM kill was observed; failed userspace allocations, startup IPC and graphics initialization remain possible. VmSize is not resident physical RAM. Several Firefox-named PIDs are subprocesses, not independent browser sessions.

## Next controlled experiments

1. Compare real XZ-compressed vs Zstandard-compressed copies of an otherwise identical QEMU-only root. Measure real file sizes and 384/512/1024 MiB KVM boot/screenshots; source branch puppy50-compression-ab-384. Do not claim that faster decompression solves the browser.
2. Separately build a softpipe-only LLVM-free Mesa version on Alpine/musl. Crocus with Mesa 26.1.6 cannot simply disable LLVM in a default native build: its CLC compiler stage required LLVM in the attempted configuration. Hardware acceleration on Intel 8086:0042 has not been demonstrated with a reduced Mesa build.
3. Capture early Firefox child-process spawn errors, X11 window mapping, and loader traces in the isolated guest, before treating this as an allocation failure.
4. Require a real visible, interactive and secure browser at 384 MiB, real RAM-only root, removable boot media and stable browsing before calling the goal complete.

This is a 100% offline QEMU test. HTTPS, audio, WebGL, USB and physical-machine support remain unverified. Real guest memory PSI readings were unavailable. No changes to the user's Xubuntu hardware were performed by the CI experiments.
