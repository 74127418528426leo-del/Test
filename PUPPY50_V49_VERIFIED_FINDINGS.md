# Puppy50 Web v49: Verified findings and next decision

Date: 2026-11-02. Evidence from a real QEMU/KVM GitHub Actions run:
https://github.com/74127418528426leo-del/Test/actions/runs/41541381474

## What was measured, not guessed

- Original, identical-package Firefox root SquashFS (XZ): **387,715,072 bytes = 369.75390625 MiB**.
- After moving the redundant /boot tree out of the SquashFS staging directory, preserving the matching kernel externally, and rebuilding with exactly the same options: **336,138,240 bytes = 320.56640625 MiB**.
- Savings: **51,576,832 bytes = 49.1875 MiB = 13.3028%** of the original compressed root.
- Preserved /boot tree had around 58.58 million uncompressed bytes.
- Verified no vmlinuz, initramfs or System.map files remained inside the bootless compressed SquashFS.
- Restored kernel from external copy, verified original Puppy ISO SHA-256 and extracted kernel/initrd/SFS byte equality from the experimental v49 ISO.

## Real KVM testing at fixed 1920×1080 framebuffer

| Evidence | 1,024 MiB | 512 MiB |
|---|---|---|
| RAM copy complete in guest serial | yes | yes |
| RAM-root switch marker | yes | yes |
| QEMU virtual CD ejection confirmed | yes | yes |
| Xorg startup marker | yes | yes |
| Firefox launch requested | yes | yes |
| Manual inspection of frame_145 and frame_155: visible Firefox window | **yes** | **no (black except cursor)** |
| HTTPS / DNS tested | no (-nic none) | no (-nic none) |
| Browser interactivity proven | no | no |
| Browser WebGL tested | no | no |
| USB / sound / target Acer hardware tested | no | no |

The 1,024 MiB frame_145 screenshot shows Firefox rendering local `file:///usr/share/puppy50web/index.html` after virtual optical-medium ejection. The 512 MiB screenshots at 145 and 155 seconds are black except the mouse cursor: **do not call this a 512 MiB functional browser**.

A separate older run at 768 MiB used the *larger pre-v49 root* and also displayed a black frame at 145 seconds. This does not establish a v49 768 MiB threshold.

## Measurement warning: legacy summary fields

The v49 Actions source initially wrote `boot_1g_pass=false` and `boot_512_pass=false` as hardcoded placeholders in `V49_RESULTS.json`, despite the more precise `boot_1024_ram_copy_completed`, `boot_512_ram_copy_completed`, `boot_512_root_switched` and `boot_512_source_media_ejected` fields being true. Do not use the hardcoded placeholders to override the actual serial proof and manual screenshots. The copy/root-switch gate is a different claim from visible browser functionality.

## Memory feasibility checkpoint

At 384 MiB, the compressed SFS alone would consume **320.566 MiB nominal**, leaving only **63.434 MiB** for all other non-overlapping demands before considering the kernel, initrd, graphics, browser process and workloads. At 384 MB decimal (366.211 MiB), the nominal remainder is only 45.645 MiB. This is not realistic for a secure modern browser without a deeper architecture reduction.

The important goal is a rendered/interactive browser with no OOM at **384 MiB** or the even stricter **384 MB decimal** target, *not* merely an SFS that fits and reaches a launcher.

## Priority order

1. Add a minimal guest-side asynchronous memory logger sampling `/proc/meminfo`, `/proc/pressure/memory`, `/proc/vmstat` (especially `oom_kill`), guest swap and Firefox/Xorg process RSS/PSS while the browser starts. The current launcher blocks on Firefox, so logs must be streamed before it exits.
2. Run the **same v49 image** at 640 / 768 / 896 / 1,024 MiB, preserving real screenshots and guest logs, to find the visible-browser threshold rather than assuming 512 MiB works because the root copied.
3. Investigate Mesa/Crocus and LLVM only via verified package/ELF dependency graph and custom builds, never by deleting `libLLVM.so.22.1` from installed Gallium. A separate ABI audit confirms `libgallium-26.1.6.so` directly requires `libLLVM.so.22.1`: https://github.com/74127418528426leo-del/Test/actions/runs/41541594792
4. Plan hardware-specific firmware modules with exact PCI/USB IDs and an opt-in broader compatible variant. Do not silently remove Wi-Fi, keyboard, sound or 3D driver support.
5. Keep WPE WebKit 2.54 DRM/KMS as an experimental alternative for direct-display browser launch, but prove full browser compatibility and measure RAM before selecting it.
6. Preserve unmodified Puppy Classic and the verified v49 build. Never imply the Alpine-based browser-only project is a full original Puppy Linux compatibility release.

No physical Xubuntu machine was modified by these CI experiments. Artifacts expire after seven days; preserve run ID, GitHub source and permanent measurements here.
