# Puppy50 v122 — verified same-host Firefox cold-boot research

**November 13, 2026. Goal: genuine Firefox first visible page within 3 seconds. Status: NOT achieved.** These results measure genuine cold QEMU/KVM process launch, including virtual BIOS and ISO boot, not powering on the physical Acer. Firefox must render its real home-page framebuffer (not just a PID, splash image, or warm VM), copy its complete compressed root to RAM with SHA proof, eject virtual media only after RAM READY, and make a new authenticated HTTP 200 request afterward.

## Successful six-boot three-way comparison

[Verified six cold Firefox boot workflow](https://github.com/74127418528426leo-del/Test/actions/runs/43499812972). Same GitHub KVM host, 2 Westmere-compatible virtual CPUs, 3 GiB RAM, BIOS, uncapped SATA/AHCI CD, 0.2s visual polling. A-B-C-C-B-A ordering.

| Trial | Real first Firefox frame | Complete SHA-verified RAM READY | Browser HTTP200 after eject |
| --- | ---: | ---: | --- |
| Original v117 #1 | 7.82 s | 15.48 s | PASS |
| Earlier direct X11 + Zstandard #1 | 7.37 s | 15.04 s | PASS |
| Earlier direct X11 + LZ4 #1 | **6.76 s** | 15.42 s | PASS |
| Earlier direct X11 + LZ4 #2 | **6.75 s** | 15.42 s | PASS |
| Earlier direct X11 + Zstandard #2 | 7.40 s | 14.66 s | PASS |
| Original v117 #2 | 8.09 s | 15.25 s | PASS |
| **Original mean** | **7.955 s** | **15.365 s** | PASS |
| **Earlier direct Zstandard mean** | **7.385 s** | **14.850 s** | PASS |
| **Earlier direct LZ4 mean** | **6.755 s** | **15.420 s** | PASS |

LZ4 plus early direct X11 was **1.200 seconds faster** than the exact original v117 ISO on this host; changing only the root compression from Zstd to LZ4 with the **same direct-session initrd** yielded another **0.630 seconds** improvement. The compressed root grew from **696,545,280 bytes (~664.3 MiB) to 963,948,544 bytes (~919.3 MiB)**. Thus the faster option worsens full-RAM capacity and slower physical-media read requirements. The Zstd version retains the smaller compressed root and reaches complete verified RAM READY sooner.

All six virtual machines completed real Firefox rendering, full checksum-verified RAM migration, QMP CD removal after verification, and an actual new browser HTTP 200 response after removal. No tested ISO reached the three-second goal.

## Measured deeper startup bottleneck

A working [persistent guest systemd profile](https://github.com/74127418528426leo-del/Test/actions/runs/43498072829) measured **1.599 s kernel + 2.303 s userspace = 3.902 s** until graphical.target, with live-config taking 446ms and NetworkManager 251ms on that particular KVM host. A second [verified process-creation test](https://github.com/74127418528426leo-del/Test/actions/runs/43499820480) observed actual guest kernel uptimes: **Xorg 4.960s**, **Openbox 5.640s**, **Firefox ESR parent PID 5.800s**. Its actual first Firefox frame appeared after 9.43s measured on the different host-QEMU-start clock. Kernel uptime and host clock origins differ; do not subtract them.

This directly explains why minor tweaks to compression or service ordering cannot guarantee Firefox within three seconds on the same startup design. The graphical and browser process launch itself is currently late. Running KVM with limited i3-compatible CPUID is not the same as running on a real vintage i3-540 at original clock rates, and all physical Acer boot times remain unmeasured.

## Safety and discarded alternatives

- Recompressing initramfs with LZ4 instead of Zstd saved only **0.16 seconds** on a different controlled host test and increased archive size around 9 MB, so there was no compelling improvement.
- The historic offline 220MB Alpine-based Firefox image required **48.24 seconds** to display its actual interactive page in a cold QEMU test and was not internet-browsing equivalent.
- A v123 pre-systemd Xorg and nonroot Firefox architectural experiment **failed to render Firefox in 140 seconds and failed the full-RAM readiness gate**; it was rejected and is **NOT** in either v122 image.
- The embedded Shift-held BIOS recovery menu from v117 remains unproven accessible. Keep the unchanged v115 ISO on a separate rescue medium.
- The full-RAM Firefox target at 384 MiB remains unmet and cannot fit the original 664MiB compressed root alone.

## Release decision

Do not claim or guarantee a three-second startup. The v122 research branch contains reproducible source and evidence. A separate release workflow builds two clearly labeled **EXPERIMENTAL** ISOs: faster LZ4 and smaller Zstandard, and must successfully boot the **exact candidate bytes under BIOS and UEFI**, copy root to verified RAM, virtually eject boot media, and make a new HTTP 200 request from Firefox afterward **before** a download is published. User's actual Acer X3950 firmware, Intel i915, Wi-Fi, dual monitors, streaming 4K, and public HTTPS across all sites have NOT been certified. Do not remove real USB boot media before green RAM READY. Neither image is an official Puppy Linux distribution or a production OS.

[Original released v117 ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v117-instant-bios-experimental) · [Original v115 recovery](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v114-fast-verification-experimental) · [Draft research pull request](https://github.com/74127418528426leo-del/Test/pull/3)
