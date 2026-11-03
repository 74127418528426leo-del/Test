# Puppy50 Web v86 — 1536 MiB Memory-Safe Network Launcher

This is a **launcher and host-network update for the exact original public v70 ISO**, not a replacement OS. The ISO is SHA256-verified and unchanged. Tested QEMU 1.5 GiB Firefox Wikipedia rendering with the source ISO was observed from the real v84 KVM screenshots in run [41695446129](https://github.com/74127418528426leo-del/Test/actions/runs/41695446129).

## One-time installation on Linux / Xubuntu

```bash
sudo apt-get update
sudo apt-get install qemu-system-x86 python3
```

Download **Puppy50_Web_v86_RAM_Safe_Network_Bundle.zip**, extract, open a terminal in its folder, then:

```bash
bash launch_linux_v86.sh
```

The default guest RAM is **1536 MiB**. Unlike the previous 1024 MiB default, this was independently observed displaying the complete Wikipedia homepage in a real QEMU guest from the public v70 ISO. The launcher checks Linux `MemAvailable`, refuses to overcommit the host, and leaves at least an estimated 768 MiB to other host programs.

To override guest memory:

```bash
PUPPY50_RAM_MIB=1792 bash launch_linux_v86.sh
```

To start offline:

```bash
PUPPY50_NETWORK=off bash launch_linux_v86.sh
```

To connect to another *authorized* host Wi-Fi network using NetworkManager:

```bash
bash connect_host_network_v70.sh
```

NetworkManager asks you for any required credentials. **Only the host selects the physical Wi-Fi/Ethernet/hotspot**; QEMU shares the host's outbound connection through a virtual e1000 adapter. This does not provide universal network access, captive-portal bypass, independent Wi-Fi SSID selection from within the guest, or access to blocked/private networks.

## Fault recovery

The included host-only TLS-preserving HTTPS bridge is supervised, and its owned child may be restarted after a crash. It binds to `127.0.0.1:3128` on the host; guest traffic reaches it over `10.0.2.2`. It allows CONNECT to approved public HTTPS destinations while preserving guest-side CA certificate verification. The launcher refuses to adopt an unknown existing proxy on that port.

Previous host-side restart tests passed, and a v75 real-VM test established Wikipedia could be loaded after a manual bridge interruption. **Automatic restart does not guarantee live socket continuity after a host Wi-Fi switch.** Firefox may require a reload.

## Verified and unverified

Verified: original v70 ISO SHA256 `26a9b339c6de87a1c891512742d608a910f4bbfce66fe26a96159297c98f8e2e`, actual 1536MiB Wikipedia rendering screenshot bound to SHA256 `a4d929d358e29553de48ccfc413bacccb1e67fc8fcb56bf7c9a0b0ada6e68a66`, 1 GiB baseline previously having limited memory, and original v70 network/Firefox controls.

Unverified: all other public websites, **any** physical Wi-Fi chipset or SSID handoff inside the VM, security-maintained browser, automatic package updates, browser sandbox audit, safe password entry, physical GPU drivers and functioning Firefox at 384 MiB.

### Security warning

The original ISO's Firefox ESR 140.12.0 is **outdated** as of November 2026. Mozilla published ESR 153.6 security fixes on October 27. This experimental VM is **not appropriate for confidential sites or entering sensitive credentials**, even when an HTTPS connection succeeds. Keep a current host browser for those tasks.

An independent maintained Debian Live + Wi-Fi firmware pilot is being developed in another branch. This launcher deliberately preserves your small proven QEMU ISO until that maintained system has passed actual boot and browser tests.
