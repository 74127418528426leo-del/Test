# Puppy50 Web v65 — Experimental Internet-enabled QEMU VM

This is a **public experimental online virtual-machine edition**, built from the independent, KVM-tested Puppy50 Web v64 network-enabled live ISO (once its checks pass).

## Downloads (when publicly released)

* **Puppy50_Online_QEMU_VM_v65_bundle.zip** — ISO, SHA256, Linux and Windows launchers, networking profile and documentation.
* **Puppy50_Web_v64_Online_QEMU.iso** — just the real bootable experimental CD-ROM ISO.
* **SHA256SUMS** — ISO file integrity manifest.
* **Puppy50_v64_Online_manifest.json** — guest acceptance-test evidence and limits.

## What the VM actually supports

- Offline or **outbound QEMU user-mode NAT** virtual networking with an emulated Intel e1000 NIC.
- DHCP, DNS and HTTPS through the **host computer's currently connected Wi-Fi, wired Ethernet or hotspot**; the guest does not directly choose physical Wi-Fi networks.
- Guest **curl** validates a real HTTPS response from `https://example.com/` with CA certificate verification. A real Firefox test then attempts URL navigation and captures a framebuffer for manual inspection.
- 1,024 MiB allocated RAM reference with real Firefox JavaScript, mouse and keyboard activity, plus entire Linux system resident in RAM; removable virtual CD.
- 384 MiB still supports RAM-only system boot, **not a functional modern browser**.

## Security and network limitations

* A passing curl HTTPS test is **not a certificate, network, or browsing security certification** for Firefox or every website. The browser's separate remote-site frame must be inspected.
* Network access depends on host connectivity and policy; not all enterprise Wi-Fi/captive portals/VPNs are compatible. Physical Wi-Fi chipsets, 802.1X, driver installation and an SSID password chooser are outside this experimental QEMU-only edition.
* No writable virtual disk; downloaded files and browsing session are wiped when the VM powers off. The custom CPU Softpipe Mesa overlay lacks coherent OS update tracking, so avoid sensitive accounts and do not use this as a production Internet workstation.
* The browser sandbox and TLS verification were **not deliberately disabled** to satisfy the tests, but that alone does not prove full security.

## Linux host

Extract the bundle, connect the HOST computer to a network, then run:

```bash
sudo apt-get install qemu-system-x86
bash launch_linux_online.sh
```

To switch the same VM to offline mode:

```bash
PUPPY50_NETWORK=off bash launch_linux_online.sh
```

On Windows the included `launch_windows_online.ps1` is a **convenience script, not independently host-tested**.

The preview is a Linux/QEMU research system, not an official Puppy Linux version.

Source: https://github.com/74127418528426leo-del/Test/tree/puppy50-v65-public-online-vm

Earlier offline-only, already published release: https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-qemu-v63
