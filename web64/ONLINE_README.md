# Puppy50 Web v64 — ONLINE QEMU experimental browser ISO

This ISO is a **new experimental network-enabled variant** of the previously published offline-only Puppy50 QEMU v63 preview. It is NOT certified as a secure general-purpose operating system or for use on actual laptops/desktops.

## Connect to the Internet through the host's network

The VM exposes an **emulated Intel e1000 Ethernet card** to its Linux guest. QEMU's unprivileged **user-mode NAT networking** provides a DHCP server, gateway and DNS, forwarding outbound traffic through the host computer's current network connection.

This means the VM can generally use the host's existing Wi-Fi, Ethernet, or phone-hotspot Internet connection **without learning the Wi-Fi password inside the VM**. The host must first be connected to the network. The guest does **not** directly manage Wi-Fi SSIDs, enterprise 802.1X, Bluetooth tethering or captive portal authentication. QEMU NAT cannot promise access to *every* network: restrictive firewalls, VPN policies, offline networks and captive portals may prevent Internet access.

Official documentation: https://www.qemu.org/docs/master/system/devices/net.html

## Actual security-preserving tests

The build refuses to publish if the real 1024MiB guest does not establish a DHCP lease, default route, working DNS and external HTTPS fetch with normal certificate verification (`curl`, *no insecure flags*). It also checks that the local Firefox page displays JavaScript readiness and reacts to physical QEMU mouse and keyboard events, and that the 384MiB guest copies its root to RAM and ejects the virtual boot medium.

The KVM automation separately opens `https://example.com/` through Firefox's address bar and captures a **real framebuffer screenshot** after attempting the navigation. A keyboard command or screenshot alone does not prove the remote page loaded, so that particular visual result must be manually inspected. HTTPS validation by curl is independent of Firefox's own certificate database and is not a comprehensive security assessment.

## VM instructions (after artifact publication)

1. Download and extract the online VM bundle (or the ISO and launch scripts separately).
2. On Linux install QEMU: `sudo apt-get install qemu-system-x86`.
3. Make sure your **host** is connected to the Internet.
4. Run `bash launch_linux_online.sh` with the ISO and SHA256SUMS alongside it.
5. In Firefox, use the address bar to type `https://example.com`, `https://www.mozilla.org`, or other addresses. Normal web compatibility is not assured until a broader website suite passes.

By default the online launcher uses QEMU NAT. Switch back to an offline VM with `PUPPY50_NETWORK=off bash launch_linux_online.sh`. The VM has no writable hard drive. Browsing history, downloads and other guest state disappear after power off unless an explicit, audited export facility is added later.

## What is still missing

- At **384 MiB**, the Linux root reliably boots fully in RAM, but Firefox still does not visibly render. **1 GiB is the positive-control allocation for browser functionality.**
- No current ISO has been verified to support arbitrary **physical Wi-Fi adapters** on the user's actual Acer computer, dual displays, audio, Bluetooth, full WebGL, browser sandbox hardening or secure automated updates.
- Restrictive enterprise networks, WPA3 Enterprise and Wi-Fi captive portals require additional work or configuration on the **host** for this QEMU NAT VM.
- This prototype contains an overlaid custom Mesa Softpipe library set with outdated package tracking. It is not a security-maintained distribution. Avoid sensitive accounts and confidential browsing until a security audit and automated patching work.
- Sandbox and TLS validation are not intentionally disabled, but this fact alone does not certify browser security.

All source code and QEMU testing jobs are in https://github.com/74127418528426leo-del/Test/tree/puppy50-v64-online-qemu

The previous offline v63 release is preserved unmodified: https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-qemu-v63
