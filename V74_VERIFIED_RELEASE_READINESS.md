# Puppy50 — v74 Evidence-Based Readiness Dashboard (November 3, 2026)

## Stable, public user download

**Puppy50 Web v70**: https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-qemu-normal-v70

This is a complete **experimental** QEMU live-ISO VM with an offline-capable Firefox homepage, read-only CD boot and RAM-only Linux root. The newer v71–v74 runs are **tests of the exact existing v70 ISO**; they do not require publishing another ISO.

## Evidence matrix

| Claim | State | Independent proof |
|---|---|---|
| Real 1024MiB KVM guest loads Linux root into RAM and ejects optical media | PASS | v70 run 41660921113 |
| Non-root Firefox displays interactive homepage with JavaScript and mouse/keyboard | PASS | v70 and earlier test runs |
| Guest's DHCP/DNS + public HTTPS with CA validation | PASS for example.com | v70 run 41660921113 |
| Actual `https://example.com/` webpage visibly opened in Firefox | PASS | v69 run 41656250129 / independently reviewed image |
| User clicks actual Wikipedia homepage tile and Wikipedia renders | PASS | v71 run 41662860725 |
| Virtual e1000 link off/on, followed by working Wikipedia without guest reboot | **PASS** | v74 run 41670823827, `vm/V74_ETHERNET_RECOVERY_REAL_VISUAL_REVIEW.json` |
| Real Mozilla webpage displayed | **UNVERIFIED** | v72 focus/mouse harness has failed to navigate; no Firefox-side site error established |
| Direct physical Wi-Fi SSID selection from guest | NOT SUPPORTED | QEMU guest sees virtual e1000, host manages Wi-Fi |
| Automatic host SSID roaming/captive portal/VPN/enterprise-auth across physical networks | NOT CERTIFIED | Virtual carrier-bounce is not host-network switch |
| Functional offline Firefox within 384 MiB | **FAIL** | earlier v59–v61 memory experiments |
| APK package file integrity and coherent graphics updates | **FAIL** | v73 run 41668355349: 8 Mesa shared-library digest mismatches and 5 unowned library symlinks |
| Current full browser sandbox, security patch lifecycle, physical computer compatibility | NOT CERTIFIED | no full audit or physical KVM-to-hardware equivalence |

## Correct engineering decision

1. **Preserve v70** as the known-good user-download baseline. Do not release another ISO purely to raise the version number.
2. **Fix the package-coherency problem first**: build proper signed, source-tracked, rebuildable Mesa packages; never hide digest discrepancies by manually altering the APK database.
3. **Expand the real browser test matrix** to static text, JS-heavy forms/search, downloads, audio/video and multiple domains. A QEMU command or `curl` result alone does not prove Firefox rendering. Use a per-site exact screenshot hash and real guest memory/time measurements.
4. **Improve network resilience** with follow-up tests for DNS changes, lost outbound TCP sockets, recovery under host Wi-Fi/Ethernet/hotspot transitions, and authorized captive portal login on the host. Virtual e1000 carrier success is an important limited milestone, not a universal network guarantee.
5. **Separate physical-hardware OS** for actual GPUs, USB/NICs/firmware, Wi-Fi selection and dual monitors. Validate with real hardware before offering an installer.
6. **Keep the 384 MiB experiment separate** from the working v70 1024 MiB image; zram allocations from the same physical RAM do not create additional capacity.

## User launch

From the extracted v70 bundle on an authorized connected Xubuntu/Linux host:

```bash
sudo apt install qemu-system-x86 python3
bash launch_linux_v70.sh
```

The host can be connected via Wi-Fi, Ethernet, or a phone hotspot. Guest Internet routing goes through user-mode QEMU NAT and its host-only TLS-preserving fallback. This does not circumvent network policies or give guest direct control of Wi-Fi credentials.

**Never use this experimental browser for sensitive logins, medical portals, financial transactions or confidential data until browser and package security maintenance is independently reviewed.**
