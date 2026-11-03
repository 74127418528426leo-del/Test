# Puppy50 v85 — Maintained Debian Live browser with physical network selection (EXPERIMENTAL)

## Why this is a new track rather than "v70 replaced"

The original v70 RAM-only QEMU ISO has an Alpine Firefox ESR 140.12.0 package. As of 2026-11-03, Mozilla has fixed important security issues in Firefox ESR 153.6.0 (October 27, 2026). Repacking v70 or reinstalling the same outdated APK cannot fix this. Debian 13 (trixie) has a signed `firefox-esr` 153.6.0 security package for x86_64.

**v85 builds a separate Debian 13 Live USB/DVD experimental ISO**, with a browser-focused desktop and normal NetworkManager connection menu. It must not be represented as a small Puppy Linux replacement: it is a deliberately less-minimal but maintainable proof of concept.

## Actual intended features

- A current **distribution-packaged Firefox ESR**, no manual glibc APK mixing
- Non-root graphical user session (LightDM, Openbox, Firefox)
- A small tint2 tray with NetworkManager for selecting **authorized** physical Wi-Fi networks, wired links and available VPN connections configured by the operator
- Kernel-supported Wi-Fi drivers and Debian firmware packages for several Intel, Realtek and Qualcomm/Atheros adapters
- `toram` live boot to copy the compressed read-only filesystem into RAM, with a RAM overlay
- User chooses websites from the normal Firefox URL bar; no forced demo page
- CA-verified HTTPS via the real host network; **QEMU-only** fallback through the existing public-destination-restricted host bridge if direct VM TCP is blocked
- No permanent host disk installation, no persistence of passwords after shutdown unless the user separately configures one later
- Rebuildable ISO from signed Debian repositories and explicit package manifests

## Known costs and hardware boundaries

A maintained modern Firefox and physical Wi-Fi drivers take more space than the optimized Alpine-only VM. This prototype may need **4 GiB RAM for full toram + Firefox**; that is a proposed test allocation, not yet a verified hardware minimum. A target of a modern browser at 384 MiB remains a different research goal.

Actual Wi-Fi access still depends on physical adapter driver, firmware, regional restrictions, the user's authorization/credentials, and any captive portal. No OS can promise joining every network or bypass network controls. The QEMU guest still sees only an emulated Ethernet adapter; the physical SSID picker will be verifiable **only on real hardware**, not in virtual Ethernet tests.

Security remains experimental until real updated-browser version, vendor signatures, sandbox settings, kernel update process, firmware provenance, and physical networking receive separate verification.

## Reproducible cloud build

Source: `web85/`. Workflow: `puppy50-v85-debian-managed-live.yml`.

The workflow uses a **native Debian 13 container** for current `live-build`, not an Ubuntu runner's legacy `trixie/updates` layout. It builds from Debian's signed archives, checks the actual `/var/lib/dpkg/status` from the newly built `filesystem.squashfs`, and boots the exact ISO in KVM with 4096 MiB to check RAM-root operation, visual frames, guest-side public HTTPS and removal of the boot CD.

The ISO is **test-only** and must not be publicly released until actual KVM screenshots demonstrate the non-root Firefox and network tray, and an independent reviewer confirms external browsing and acceptable real hardware support.
