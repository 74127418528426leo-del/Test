# Puppy50 Web v68 — portable online QEMU VM package (experimental)

**Publication status: conditional.** The v67 ISO must first pass real 1 GiB QEMU guest HTTPS using its own CA bundle and then have its Firefox external-page screenshots independently inspected. Building a bundle does NOT mean it already passes that test.

## What this package will contain

- `Puppy50_Web_v67_HTTPS_Bridge_Experimental.iso` — experimental bootable browser-only Linux image, loaded into RAM and tested as a QEMU guest.
- `SHA256SUMS` — verify the ISO before running.
- `launch_linux_https_bridge.sh` — automatic KVM or TCG, e1000 NAT, optional host-only HTTPS fallback, cleanup on exit.
- `host_https_bridge.py` — tiny HTTPS CONNECT forwarder that binds **only** to 127.0.0.1:3128 and rejects private destinations. It forwards encrypted TLS bytes without terminating TLS, accessing browsing contents or importing a private CA.
- A verification manifest, VM hardware/network profile and screenshots.

## Linux / Xubuntu use

First connect your **host computer** to the Wi-Fi, Ethernet, phone hotspot or other available Internet connection. Install requirements:

```bash
sudo apt-get install qemu-system-x86 python3
```

Extract the complete bundle and run:

```bash
bash launch_linux_https_bridge.sh
```

The launcher uses 1 GiB guest memory by default. You may choose 2 GiB for larger websites:

```bash
PUPPY50_RAM_MIB=2048 bash launch_linux_https_bridge.sh
```

To remain completely offline:

```bash
PUPPY50_NETWORK=off bash launch_linux_https_bridge.sh
```

It does **not** install Linux on the host, attach a writable disk, or store browser history persistently. It does not expose an inbound network port to the LAN.

## How connecting to different networks actually works

The virtual machine sees one emulated e1000 Ethernet adapter and receives its IP address from QEMU's DHCP, regardless of whether the **host** is connected through Wi-Fi, wired Ethernet, or a phone hotspot. Switching physical networks happens on the host, not inside the VM. Many ordinary public websites should be reachable through QEMU NAT when the host can access them; the host-only HTTPS bridge provides an optional fallback in environments where guest outbound TCP is blocked but the host can connect.

This is **not** direct access to every wireless network or physical adapter. It does not discover Wi-Fi SSIDs, enter Wi-Fi passwords, authenticate WPA2/3 Enterprise, configure VPNs or guarantee captive portal compatibility. Those belong to a separate physical-hardware networking edition.

## Security boundaries

- The guest must validate real HTTPS certificates. The fallback bridge preserves end-to-end TLS and does not change Firefox's sandbox settings.
- Only publicly routable destinations and HTTPS ports 443/8443 are allowed through the bridge; other HTTP and host-private services are not provided by the bridge. QEMU NAT itself may still permit access to host services at 10.0.2.2.
- This is **not** a certified production OS. Its custom Mesa overlay lacks coherent package-update metadata; do not use it for sensitive accounts or confidential information until package updates, browser policies and network isolation receive separate auditing.
- The old 384 MiB target boots fully in RAM, but Firefox is still **not usable** at 384 MiB. A 1 GiB minimum is the verified offline-interaction baseline.
- No guarantee of operation on actual physical Intel 8086:0042 hardware, USB peripherals or every network topology.

## Validation and source

- v65 confirmed a real Firefox page loaded over the virtual Ethernet from the host, with matching host HTTP logs and real framebuffer pixels: https://github.com/74127418528426leo-del/Test/actions/runs/41621113605
- v66 established the host-only HTTPS CONNECT bridge can retrieve external HTTPS without bypassing certificate validation: https://github.com/74127418528426leo-del/Test/actions/runs/41622338556
- v67 is the **actual guest** HTTPS test: https://github.com/74127418528426leo-del/Test/actions/runs/41622969689

This is a forked experimental browser-only Alpine Linux environment using Puppy bootloader assets, not an official Puppy Linux release.
