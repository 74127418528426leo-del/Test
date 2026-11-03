# Puppy50 Web v64 — Experimental ONLINE QEMU live ISO

This is a network-enabled experimental update to [Puppy50 v63 Offline](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-qemu-v63). It is **not official Puppy Linux, a security-certified distribution, or a physical-computer installer**.

## New components

- QEMU's outbound-only unprivileged user-mode networking, **e1000** virtual Ethernet, and matching kernel module loaded before the entire operating system switches into RAM.
- Alpine `dhcpcd` for DHCP, DNS routing through host NAT, and real `curl` to test **CA-verified HTTPS access to https://example.com/**.
- Normal Firefox address bar and browser input at the 1024 MiB guest reference, now with an online network.
- Launch scripts for Linux and a convenience Windows PowerShell host wrapper, with SHA-256 verification and `PUPPY50_NETWORK=off` option.
- Real GitHub Actions KVM tests for actual root-in-RAM and boot-medium ejection at 384 and 1024 MiB, keyboard/mouse DOM interaction at 1024 MiB, outbound DHCP/DNS/CA-verified HTTPS from inside the guest and a screenshot after Firefox address-bar navigation.

## Host networks

Because the VM uses a virtual Ethernet connection behind QEMU NAT, it can use the **host's existing Wi-Fi, Ethernet, USB tether, or mobile hotspot Internet connection**, subject to the host network's firewall/VPN/proxy policies. The *host*, not the VM, selects Wi-Fi SSIDs and enters credentials. It is **not true that the VM is verified to join every possible physical wireless network**.

This build is virtual-machine-only: no physical Wi-Fi adapter pass-through, corporate 802.1X, WPA Enterprise, captive portal configuration, real GPU drivers, sound or wired NIC driver matrix has been demonstrated.

## Functional and security limits

- Current modern Firefox UI and local-page input are only verified at **1024 MiB**. RAM-only boot at **384 MiB** works but Firefox is still not usable at that memory allocation.
- Positive curl HTTPS is only proof of guest DHCP/DNS/TLS for one endpoint, not universal website compatibility. Firefox navigation is separately exercised, screenshots require manual review before claiming remote page contents.
- Firefox sandbox controls and TLS trust verification are not intentionally disabled; still the custom Mesa package overlay and security update process have not passed production hardening checks. Avoid using sensitive accounts or confidential information.
- No disk is attached. The OS lives entirely in RAM, and session data disappears when the guest powers off unless a separate export design is implemented.
- Public release assets are uploaded **only after** the real VM acceptance gates pass. If no release is visible, the tests have not justified one.

Live CI: https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-v64-online-qemu.yml

Source: https://github.com/74127418528426leo-del/Test/tree/puppy50-v64-online-qemu
