# Puppy50 Web v69 — Public HTTPS Online QEMU VM Preview

**Status: experimental. The first verified 1 GiB RAM-only Puppy50 QEMU system that visibly loaded a public HTTPS page in Firefox. Not safe for sensitive browsing.**

## Actual independent KVM evidence

This exact ISO was built in GitHub Actions [run 41656250129](https://github.com/74127418528426leo-del/Test/actions/runs/41656250129). That workflow reported **failure** due to its legacy DOM frame timestamps and an incorrectly escaped native Firefox exit-code parser. Its raw screenshots and serial log were subsequently inspected and independently re-evaluated; the source artifact and proof are retained.

- Linux root copies completely into 1024 MiB guest RAM; the QEMU CD is ejected.
- Firefox displays local HTML and executes JavaScript; a real virtual mouse click changes it to orange and a real keyboard T changes it to green.
- The guest obtained DHCP and DNS and connected to **https://example.com** through the host's TCP CONNECT bridge, using the guest's normal CA certificate verification.
- The same non-root Firefox instance opened **https://example.com** as a new tab, and the actual final screenshot displays the **Example Domain** website.
- Test frames: `frame_145.ppm` gold JavaScript, `frame_195.ppm` orange mouse, `frame_245.ppm` green keyboard, `frame_375.ppm` public Example Domain.

The release checker binds the inspected real screenshot and ISO to their exact SHA-256 hashes and checks the actual frame color stages, serial log and KVM RAM-root evidence. A successful HTTPS `curl` or submitted command by itself is not enough.

## Run the portable virtual machine

Connect your **Xubuntu host** to Wi-Fi, wired Ethernet, or a phone hotspot **first**. This VM has only an emulated Intel e1000 Ethernet interface, not a Wi-Fi SSID picker. It shares the host's current Internet connection through QEMU's user-mode NAT, and the included optional localhost-only HTTPS CONNECT bridge preserves end-to-end encryption when direct guest outbound TCP is blocked.

Install prerequisites on the host:

```bash
sudo apt-get install qemu-system-x86 python3
```

Download and extract `Puppy50_Online_QEMU_VM_v69_Bundle.zip` and run:

```bash
bash launch_linux_https_bridge.sh
```

The included script verifies the ISO against SHA256SUMS, starts a loopback-only outbound HTTPS bridge as needed, uses KVM when available (TCG fallback), and runs the QEMU guest with 1024 MiB RAM, standard VGA, a read-only CD, and **no writable hard drive**.

For a larger guest on a computer with sufficient physical RAM:

```bash
PUPPY50_RAM_MIB=2048 bash launch_linux_https_bridge.sh
```

To disconnect guest networking:

```bash
PUPPY50_NETWORK=off bash launch_linux_https_bridge.sh
```

**Demonstration quirk in this test ISO:** after an initial delay of approximately three minutes following browser startup, the operating system automatically opens `https://example.com` in a new tab. You can navigate to other websites with Firefox's address bar; the automatic demonstration is not intended as a permanent homepage setting.

## What it does NOT prove

- Only the public site `example.com` was visually verified. Modern interactive websites, authentication, downloads, streaming, WebGL, and other domains still need testing.
- The 384 MiB RAM-only boot is verified in earlier builds but **Firefox is not usable at 384 MiB**. This online build was tested at 1024 MiB.
- An operating system cannot guarantee access to every physical Wi-Fi network, captive portal, VPN, WPA Enterprise network, firewall, or blocked website. QEMU networking works through the host's current authorized connection. The guest does not independently control the host's Wi-Fi credentials.
- This build is **not a maintained production OS**: its custom graphics libraries lack coherent package update metadata, and the browser sandbox/security-update lifecycle has not been fully audited. Avoid banking, confidential accounts, medical portals, passwords or sensitive work in this prototype.
- No physical Acer Intel i915/GMA hardware, dual monitors, Bluetooth, sound, Wi-Fi USB adapters or direct-installation compatibility is certified. Do not overwrite your Xubuntu installation.
- The host-side bridge is unprivileged, listens only on 127.0.0.1:3128, denies private network destinations, and forwards HTTPS TLS bytes without replacing certificates. QEMU NAT itself can access host-local services in some configurations, so treat the VM as an experimental sandbox, not a hardened isolation boundary.

Source: https://github.com/74127418528426leo-del/Test/tree/puppy50-v69-actual-firefox-https-page

This is a browser-only Alpine-based research system using Puppy boot media components, not an official Puppy Linux distribution. Upstream licenses still apply.
