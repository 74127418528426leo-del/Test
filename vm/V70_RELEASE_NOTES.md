# Puppy50 Web v70 — Normal browsing with verified guest HTTPS

**Experimental online QEMU-only live ISO. Not a secure or maintained production OS.**

This version converts the earlier v69 real-public-HTTPS browser demonstration into a normal RAM-only user workspace. Firefox opens a home page with multiple website shortcuts and a link to the guest's network status. No external website is automatically opened after a timer.

## Download and run

Download `Puppy50_Online_QEMU_VM_v70_Bundle.zip` from this release. The ZIP contains:

- `Puppy50_Web_v70_Normal_Browser_Online.iso` — tested experimental live Linux ISO.
- `launch_linux_v70.sh` — checksum-verified QEMU launcher with NAT and optional localhost HTTPS bridge.
- `host_https_bridge.py` — TLS-preserving, local-only bridge with private target blocking.
- `host_network_preflight_v70.py` — read-only host DNS and HTTPS test.
- `connect_host_network_v70.sh` — optional explicit host Wi-Fi chooser with NetworkManager's own credential prompts.
- `SHA256SUMS`, test manifests, and the user README.

On Linux/Xubuntu, connect your **host** to Wi-Fi, Ethernet, or a phone hotspot and run:

```bash
sudo apt-get install qemu-system-x86 python3
# Extract the ZIP into one folder and from that folder:
bash launch_linux_v70.sh
```

For more demanding websites on computers with enough RAM:

```bash
PUPPY50_RAM_MIB=2048 bash launch_linux_v70.sh
```

For an offline session:

```bash
PUPPY50_NETWORK=off bash launch_linux_v70.sh
```

This QEMU VM has no writable hard disk. The compressed root is copied fully into guest RAM and the virtual optical boot media can be ejected. Browser/session changes disappear after shutdown.

## What is independently demonstrated

The public v69 release has real 1 GiB guest Firefox screenshots of a valid public `https://example.com` tab and CA-verified guest HTTPS. The v70 acceptance suite tests the **new user home page** in real KVM, guest DHCP/DNS and CA-verified HTTPS, RAM-only operation, and no forced navigation. A manual review is linked to the exact ISO and screenshot hashes.

Website shortcuts to Wikipedia, Mozilla and Google are present but **their page rendering is not independently certified** by these tests. Network restrictions, captive portals, proxy policies and website-specific requirements can still interfere.

## Physical networking and security limitations

QEMU user-mode NAT uses the host's authorized active network. This is not the same as providing every possible Wi-Fi driver, a guest SSID selector or guaranteed access through every firewall, VPN, corporate authentication system or captive portal. NetworkManager may save host Wi-Fi profiles when the user explicitly runs the optional chooser.

The 384 MiB RAM-only Linux boot is an earlier result; Firefox still is **not usable at 384 MiB**. v70 uses a 1 GiB positive-control VM. A 2 GiB guest may improve heavy websites but is not a new performance certification.

Custom graphics libraries, sandbox/update policies, package integrity and real-hardware driver coverage are not fully audited. Do not use this prototype for sensitive logins or replace your current Xubuntu installation with it.

Earlier public online VM: https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-qemu-online-v69

Source branch: https://github.com/74127418528426leo-del/Test/tree/puppy50-v70-normal-browsing
