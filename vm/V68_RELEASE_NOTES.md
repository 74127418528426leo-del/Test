# Puppy50 Web v68 — Internet-enabled QEMU VM Preview (experimental)

This is an **experimental** browser-only Linux virtual machine that runs from a RAM-loaded live ISO. It does not install to the host disk. It uses QEMU's e1000 virtual Ethernet card, DHCP and DNS, and shares the host's existing Wi-Fi, Ethernet or hotspot connection through QEMU NAT.

**HTTPS fallback:** If direct guest TCP connections fail while the host has outbound access, the bundled optional loopback HTTPS CONNECT bridge can forward TLS-encrypted bytes from the guest to public hosts on ports 443/8443. The guest's Firefox and curl validate real public certificates. The bridge never terminates TLS or imports a new certificate authority. It blocks private/internal target addresses.

## Downloads

The recommended asset is `Puppy50_v68_Online_QEMU_VM_Bundle.zip` which includes the ISO, checksum, secure host-only bridge source, Linux launcher, machine-readable manifest and instructions.

Separate ISO-only and SHA256 assets may also be available.

## Launch from Linux/Xubuntu

```bash
sudo apt-get install qemu-system-x86 python3
# Extract Puppy50_v68_Online_QEMU_VM_Bundle.zip
bash launch_linux_https_bridge.sh
```

Your host must already have Internet connectivity. The guest starts with 1024MiB of RAM; a larger value such as `PUPPY50_RAM_MIB=2048` may improve modern-site performance on a machine with sufficient RAM.

To switch off all VM networking:

```bash
PUPPY50_NETWORK=off bash launch_linux_https_bridge.sh
```

## Honest limitations

This is **not** a secure or maintained production distribution; the custom graphics libraries lack coherent system package-update metadata. Do not use sensitive accounts until browser patching and stronger sandbox/network auditing are completed.

The 384MiB RAM-only boot is verified but Firefox is **not functional at 384MiB**. No physical Intel GPU compatibility, Wi-Fi SSID selector, WPA Enterprise, VPN, captive portal or all-network guarantee is proven. Networking is configured on the **host**, not by picking Wi-Fi networks from inside the guest.

Official Puppy Linux does not sponsor this prototype. Source is published, and original upstream software keeps its own licenses. No writable hard drive is attached, and session changes disappear when the VM shuts down.

## Verification references

- Working host-to-guest real HTTP website and Firefox screenshots: https://github.com/74127418528426leo-del/Test/actions/runs/41621113605
- TLS-preserving host bridge / IPv4 egress test: https://github.com/74127418528426leo-del/Test/actions/runs/41622338556
- Actual guest end-to-end CA-verified external HTTPS test: https://github.com/74127418528426leo-del/Test/actions/runs/41622969689

**This prerelease must not be published until the real guest's public HTTPS test and Firefox screenshot review pass.**
