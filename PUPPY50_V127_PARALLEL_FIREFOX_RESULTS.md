# Puppy50 v127 — launch original Firefox concurrently with Openbox after early X11

**Result: PASS in four matched KVM cold-boot trials, but true Firefox under three seconds is still NOT achieved.** v127 is a research candidate only, not a published ISO for physical hardware.

## Actual A–B–B–A result

[Original successful comparison with all four independent VM results](https://github.com/74127418528426leo-del/Test/actions/runs/43505491538). The first-frame clock began immediately before QEMU launch and stopped at actual browser-home framebuffer detection, not PID existence or a generated placeholder.

| Trial | First real Firefox frame | Full verified RAM READY |
|---|---:|---:|
| v126 X11 early, Firefox via Openbox #1 | 9.03 s | 15.74 s |
| v127 Firefox parallel to Openbox #1 | **8.61 s** | 15.83 s |
| v127 Firefox parallel to Openbox #2 | **8.42 s** | 15.63 s |
| v126 X11 early, Firefox via Openbox #2 | 8.63 s | 15.30 s |
| **v126 mean** | **8.830 s** | **15.520 s** |
| **v127 mean** | **8.515 s** | **15.730 s** |

Measured v127 first-frame gain **0.315 seconds**; mean RAM completion **0.210 seconds slower** in this small test. All four VMs retained authenticated, no-TCP early Xorg started before PID1 and alive across root switching, no fallback LightDM, and unprivileged Firefox. All four completed checksum-verifiable RAM copy, safe QMP media removal, and nonce-authenticated post-ejection HTTP 200 requests to a new browser page. No benchmark errors.

## Architecture and limitations

The [guarded patch](./v127/parallel_firefox.py) removes the duplicate Firefox command from the volatile nonroot Openbox autostart and launches the unchanged Firefox ESR process immediately after the early authenticated Xorg display is ready, concurrently with Openbox. The offline-release kernel, existing Zstd SquashFS root, full-RAM initrd, network stack and Firefox sandbox are unchanged; this is test-only and not a replacement of the physical Acer operating system.

The gains are much less than the **more than five seconds** still missing from the real under-3-second cold Firefox target. The earlier v122 released experiment provided a faster isolated **6.755-second mean** from a *different* GitHub runner, but it must not be directly ranked against these v126/v127 absolute times; same-host A–B–B–A difference is the valid comparison.

**No release.** Do not claim under three seconds on BIOS, UEFI, a real i3-540, USB2, Wi-Fi, i915, dual displays or browser 4K. Keep [v122 experimental ISO/ZIP](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v122-direct-fast-codec-experimental) and separately the [v115 recovery ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v114-fast-verification-experimental). Full RAM-only boot at 384MiB remains impossible for the existing ~664MiB compressed root alone.
