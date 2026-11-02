# Puppy50 v51 — verified QEMU-only firmware-ablation results

2026-11-02. Real reproducible GitHub Actions/KVM experiment:
https://github.com/74127418528426leo-del/Test/actions/runs/41546583445

## Actual compressed SquashFS measurements

| Image | Bytes | MiB |
|---|---:|---:|
| Original Firefox root v48 | 387,715,072 | 369.753906 |
| v49 bootless full-hardware root (direct v51 baseline) | 336,138,240 | 320.566406 |
| v51 bootless + QEMU-only firmware profile | 212,172,800 | 202.343750 |

- Firmware removal from v49 baseline saved exactly **123,965,440 compressed bytes = 118.222656 MiB**, not merely raw bytes.
- Raw staged firmware removed: **124,283,930 bytes**.
- Aggregate reduction from v48 to QEMU-only v51: **175,542,272 bytes = 167.40625 MiB = 45.27%**.
- Retained intact: Firefox ESR browser engine, kernel modules, Mesa Gallium, LLVM and the startup code.
- External original matching kernel and initrd were assembled into the real ISO after SquashFS was compressed. ISO embedded-image byte-verification passed.
- The v51 ISO was 277,151,744 bytes (264.3125 MiB); the ISO contains other boot files and must **not** be confused with the RAM-copied SquashFS size.

## Real KVM proof at three physical memory allocations

| Observed evidence | 384 MiB | 512 MiB | 1024 MiB |
|---|---|---|---|
| RAM-copy of complete compressed root | YES | YES | YES |
| Root switch onto RAM-backed SquashFS overlay | YES | YES | YES |
| QEMU virtual boot medium ejected | YES | YES | YES |
| Xorg startup marker | YES | YES | YES |
| Firefox launch requested | YES | YES | YES |
| 145-second framebuffer visually shows browser | **NO (black + cursor)** | **NO (black + cursor)** | **YES (Firefox and local HTML)** |
| Interactive browsing confirmed | NO | NO | NO |
| Internet / HTTPS confirmed | NO (VM -nic none) | NO | NO |
| Physical computer compatibility | NOT TESTED | NOT TESTED | NOT TESTED |

Manual screenshot inspection of artifact frame_145.ppm confirms black framebuffer with cursor at 384/512 MiB. 1024 MiB screenshot shows rendered Firefox browser window, local HTML heading and normal browser toolbar.

**Milestone achieved:** the QEMU-specific system boots, copies compressed root into RAM, switches to RAM-root and ejects its CD at the long-targeted 384 MiB physical guest RAM allocation. **Milestone NOT achieved:** a visible, secure interactive browser at 384 MiB. Do not conflate the two.

## Serious limitation: not safe to boot this image on user's Acer computer

The v51 experiment removed physical Intel i915, Wi-Fi, Bluetooth and other firmware. An untested real i915 GPU or wireless card may require them. **No firmwareless ISO should be advertised as a universal Puppy replacement.** Real-hardware mode must select verified necessary firmware from boot media before fully releasing it and copy that firmware into RAM, with honest RAM accounting. This alternative remains a research proposal.

## Next highest-value engineering actions

1. Read the v52 Firefox process/wait-state diagnostic (https://github.com/74127418528426leo-del/Test/tree/puppy50-v52-firefox-waitstate-probe). v50 proved no *kernel* OOM kills at 512/768/1024 and incomplete child process creation at low RAM; it did not prove why.
2. Measure system memory consumption **at the exact point the browser first visibly renders**, including process PSS, scratch and cache, on unchanged image at 768, 896, 960, 1024 MiB.
3. Build a narrow Mesa 26.x Crocus/softpipe variant with LLVM disabled (compile and ABI/runtime test), then measure actual SquashFS delta and **WebGL on Intel 8086:0042** before promoting physical configuration. Never delete the existing LLVM shared library while libgallium requires it.
4. Evaluate WPE WebKit 2.54 WPEPlatform headless/DRM-KMS engine via a real measured browser shell, preserving current security and real web features; do not treat Cog as a modern full browser.
5. Preserve v49 full-hardware-compatible baseline and isolated experimental v51 branch. 384 MiB actual browser functionality is still unachieved.

Artifacts in GitHub Actions have seven-day retention; this text is a durable repository record.
