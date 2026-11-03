# Puppy50 Web v69 — First visually verified public HTTPS browser VM

**Experimental QEMU-only prerelease.** The real 1024 MiB Linux virtual machine booted entirely from RAM, ejected its boot CD, responded to JavaScript/mouse/keyboard events in Firefox, and then displayed the **public Example Domain webpage** from `https://example.com` in a Firefox tab. The guest's own HTTPS request independently verified the site's CA certificate over a host-only TLS-preserving connection.

The exact ISO and captured public-webpage screenshot are bound by SHA-256 to an independent raw-evidence audit. The original KVM workflow ended in failure because its legacy input-stage screenshot timings and regex were wrong; the raw logs and screenshot were examined and re-verified rather than silently relabeled as a successful workflow.

## Download

**Recommended:** `Puppy50_Online_QEMU_VM_v69_Bundle.zip` contains the bootable ISO, verified checksums, Linux QEMU launcher, minimal loopback HTTPS bridge source, review/provenance manifest, network profile, and README.

**Standalone:** `Puppy50_Web_v69_Native_Browser_Experimental.iso` plus `SHA256SUMS`.

After connecting the host Linux computer to its Internet network:

```bash
sudo apt-get install qemu-system-x86 python3
# Extract ZIP then:
bash launch_linux_https_bridge.sh
```

There is **no writable virtual disk**. Boot medium can be removed after the system loads entirely into RAM. VM memory is 1024 MiB by default; 384 MiB browser functionality is *not* demonstrated.

In this proof-of-concept ISO, an automated verification task opens `https://example.com` in a new Firefox tab after a delayed startup interval. Firefox's normal address bar remains available for other websites.

## Boundaries

The VM shares the **host's** Wi-Fi/Ethernet/hotspot via QEMU NAT; it does not discover and select physical Wi-Fi SSIDs or guarantee operation on every restricted network. The guest has not been validated for VPNs, captive portals, WPA Enterprise, every public website, video, sound or WebGL. The security-update/package integrity process is not complete; do not use for sensitive or confidential accounts.

This is **not** an official Puppy Linux release, not ready for physical installation, and not certified for the older Intel GMA graphics controller. See `README_ONLINE_V69.md` inside the bundle for limitations.

## Provenance

- KVM raw screenshots/logs: [v69 experimental run](https://github.com/74127418528426leo-del/Test/actions/runs/41656250129)
- Source/review/manifest: [v69 public branch](https://github.com/74127418528426leo-del/Test/tree/puppy50-v69-actual-firefox-https-page)
- Existing offline-only baseline, unchanged: [v63 release](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-qemu-v63)
