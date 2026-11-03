# Puppy50 Web v93 — Maintained Firefox, real internet browsing (experimental prerelease)

**Experimental Debian Live browser-only RAM system.** This release contains the **exact previously tested v91 ISO** (repackaged without changing its bytes), not a redesigned or smaller ISO.

## Actual verified results (November 3, 2026)

- The Live system boots in real QEMU/KVM, copies the Live root into RAM, and survives ejecting its read-only boot CD.
- Firefox ESR **153.6.0esr-1~deb13u1** was verified in the signed Debian package inventory (from the earlier successful build).
- Firefox starts as an unprivileged non-root user under LightDM/Openbox.
- The guest verified a real public HTTPS connection without disabling certificate checks.
- A human-inspected QEMU framebuffer shows **https://example.com/** actually rendered in Firefox at **2560 MiB allocated RAM** and at **3072 MiB**.
- At 2048 MiB, the local Firefox homepage appeared but the automated URL input did not complete in the first trial. This is *not* a hard RAM minimum finding; a slower-input retest is under investigation.
- At 1536 MiB, the graphical desktop was black with cursor and panel; no Firefox window appeared during the 300-second trial.

The total compressed Live ISO is approximately 1 GB. This is **not** a 50 MB Puppy Linux ISO. The updated Debian browser and firmware trade compressed size for maintainability and broader potential device support.

## Network capabilities and boundaries

In a VM, QEMU user-mode NAT normally shares **the host's authorized** Wi-Fi, Ethernet or mobile-hotspot connection; the guest need not know the host Wi-Fi password. The included NetworkManager applet and Intel/Realtek/Atheros firmware enable network selection on compatible **physical** hardware; no physical Wi-Fi adapter, WPA-Enterprise, captive portal, 802.1X, IPv6-only network, Bluetooth tethering, or actual Acer machine has been certified. VPN/firewall restrictions and login requirements must be respected. **No OS can promise to join every network.**

## Security and installation

This is a *test-only prerelease*, not a production- or security-certified desktop. Avoid sensitive accounts, banking, medical portals, personal credentials and confidential workloads until sandbox, update and physical driver behavior are audited. Keep your existing Xubuntu installation; do not overwrite its storage.

To run virtually, install QEMU on Xubuntu. Download this ISO and SHA256SUMS and use the accompanying v93 launcher package and guide. The launcher verifies the ISO checksum, checks host available RAM, and uses no writable virtual disk. **On a 4 GiB Xubuntu host, a 2560 MiB guest may fail the memory guard**; this is intentional to prevent host memory exhaustion. A bare-metal Live USB test would use the host's RAM directly, but that hardware path has not yet been verified.

## Independent evidence

- v92 normal Firefox address-bar navigation: https://github.com/74127418528426leo-del/Test/actions/runs/41718614432
- v93 unchanged ISO RAM-threshold tests: https://github.com/74127418528426leo-del/Test/actions/runs/41720896581
- Full source and launcher kit: https://github.com/74127418528426leo-del/Test/tree/puppy50-v93-debian-live-lowram-real-web
- Real screenshot hash bound by V93_HUMAN_VISUAL_REVIEW.json.

**No guarantee of any network, arbitrary websites, or physical Wi-Fi.**
