# Puppy50 Web v102 — Intel-targeted Firefox RAM-only Live ISO (experimental)

**Real bootable Debian Live ISO.** This is a separate experimental Intel-graphics edition, not a replacement for the [v93 full-hardware edition](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-debian-live-v93-maintained-https).

## Measured improvements

The v102 ISO is **760,545,280 bytes = 725.31 MiB**, compared with 990,183,424 bytes = 944.31 MiB originally. **Actual saving: 219 MiB / 23.19%.** Inside the squashfs, unrelated NVIDIA/AMDGPU GPU firmware and duplicate kernel/initrd copies were removed. Firefox ESR 153.6, NetworkManager, wireless firmware, Intel i915 firmware, CA bundle, sandbox, and original ISO bootloader were preserved.

Three **real QEMU KVM** guests successfully booted the ISO, launched non-root Firefox, established certificate-verified HTTPS, and continued after the boot CD was ejected, without physical disk swap or OOM kills. The observed minimum available RAM was **85.39 MiB** at 2048 MiB trial A, **127.95 MiB** at 2048 MiB trial B, and **762.00 MiB** at the 2560 MiB control. Independent visual inspection of final screenshots found:

- **2048 A:** a public Google search page loaded, but the automated virtual keyboard dropped URL characters. This does **not** count as correct navigation to the requested example.com URL.
- **2048 B:** the exact external `https://example.com/` site was displayed.
- **2560 control:** the exact external `https://example.com/` site was displayed by 185 seconds.

This is promising but does **not** establish reliable 2 GiB operation. 2.5 GiB retains a much larger measured safety margin.

## Network and hardware boundaries

NetworkManager/nm-applet offer graphical selection of **authorized** wired and supported wireless networks, with normal password and captive portal authentication. QEMU's **emulated wired network** worked; physical Wi-Fi hardware, enterprise networks, WPA3, IPv6-only, USB tethering and VPN have **not** been certified. The original broad wireless firmware collection remains included. No OS can guarantee access to every network.

This variant removes **AMD and NVIDIA GPU firmware** and therefore may fail on hardware needing those files. It is aimed at Intel integrated graphics; use the separate v93 full-hardware edition for other computers.

This is a TEST-only research prerelease, not security certified or recommended for sensitive banking/accounts. Use a spare USB if testing bare-metal Live mode; writing an ISO to USB erases that USB. Keep your current installed operating system intact. RAM-only Live operation has been tested in QEMU, not universally on physical computers.

## Independent reproducibility

- [v102 real ISO build, size audits, and three KVM guest tests](https://github.com/74127418528426leo-del/Test/actions/runs/41751806750)
- [v100 original Firefox 2 GiB comparison](https://github.com/74127418528426leo-del/Test/actions/runs/41748934221)
- [v101 read-only ISO component inventory](https://github.com/74127418528426leo-del/Test/actions/runs/41750712402)
- [v102 audited source](https://github.com/74127418528426leo-del/Test/tree/puppy50-v102-intel-firefox-trim-real-kvm)

Full frame SHA256s pinned in `V102_MANUAL_SCREENSHOT_PROOF.json`. **The 384 MiB goal and all-network compatibility have not been achieved.**
