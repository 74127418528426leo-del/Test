# Puppy50 — Network portability engineering matrix

This project must not treat **a network adapter, an Internet connection, DNS, or verified HTTPS** as interchangeable things. Each is a separate testable requirement.

## Actual v64 QEMU network design

The emulator presents an Intel e1000 virtual Ethernet NIC and uses unprivileged QEMU user-mode NAT to forward outbound traffic through the host's Internet connection. Inside the Alpine Linux guest:
1. `e1000` driver and dependency chain are loaded **in the initial RAM disk before switch_root**. This is essential because the compact target root does not expose its kernel module tree to late modprobe.
2. `dhcpcd` configures the emulated NIC by DHCP; record a real IPv4 address and default route.
3. Use QEMU's DHCP-provided DNS configuration; guest curl must resolve `example.com`.
4. Retrieve a real external HTTPS page with `curl` and **normal certificate verification**. Never use an insecure or certificate-ignore switch to pass CI.
5. Independently run the real GUI Firefox browser, offline interaction checkpoints, then navigate through the actual address bar to `https://example.com/` and retain the final framebuffer. Visual site-content proof requires inspecting the resulting capture. Curl alone does NOT prove the browser loaded the URL.

QEMU official docs: https://www.qemu.org/docs/master/system/devices/net.html

## Network classes: do not misrepresent results

| Connection | Online QEMU (host connected) | Direct physical boot |
|---|---|---|
| Home Ethernet | Uses host's existing Ethernet via NAT | Needs actual hardware NIC driver, DHCP and verification |
| Home Wi-Fi WPA2/WPA3 | Uses host's existing Wi-Fi via NAT; guest does NOT see SSID | Needs detected WLAN hardware/firmware, wpa_supplicant/iwd, secure user UI |
| Mobile phone hotspot | Works through host networking when host already online, subject to policy | Needs direct WLAN/USB tether driver/profile |
| Coffee shop captive portal | Host may need to sign in; guest access not guaranteed | Requires captive portal discovery and login; privacy checks |
| University/corporate 802.1X | Only via host when host can authenticate; VPN policies may block guest | Needs 802.1X/EAP credentials, certificates, identity UI and enterprise validation |
| VPN/proxy-restricted network | May be blocked by host policy; NAT isn't a bypass | Needs admin-approved routing/proxy setup |
| IPv6-only network | Not validated: v64 pins QEMU NAT to IPv4 | Requires real IPv6 RA/DHCPv6/DNS64 and corresponding tests |
| Offline / airplane mode | `PUPPY50_NETWORK=off`; local page remains available | Hardware-specific radio state controls are unbuilt |

**No OS can promise successful connection to every possible network**: access credentials, security controls and site availability are external conditions. The correct goal is automatic discovery, secure user-approved authentication, transparent failure reports and safe offline behavior.

## Native-hardware requirement, separate build

A physical-hardware edition should retain network drivers and firmware for the target user's actual PCI/USB Wi-Fi and Ethernet hardware and verify them under Linux on the actual PC. It should implement network selection from a secure desktop or local privileged service with authorization; do not expose a root-authenticated network API to arbitrary browser webpages. Add useful diagnostics: no adapter, no carrier, no DHCP, DNS failed, captive portal, TLS failed, Internet reachable.

Support at least Wi-Fi, wired LAN, USB Ethernet/phone tether with tested hardware before describing it as universal, and provide a fallback offline browser. Any firmware needed by the target machine must be bundled/verified before download because the network could be unavailable during first boot.

## Acceptance priorities

1. **Now:** v64 QEMU guest obtains DHCP + DNS + CA-verified HTTPS in real RAM-only KVM and Firefox still responds to input.
2. **Next:** manually review screenshot after Firefox HTTPS navigation, automate an independent real HTTPS page-render proof, and test multiple websites and downloads.
3. **Then:** verified security updates, browser sandbox, DNS proxy/CSP/cert error handling, network toggles, session export, and traffic restrictions.
4. **Finally:** physical adapter/firmware support for real Acer X3950 (and selected other machines), selectable WLAN, IPv6 and captive portal tests. Do not infer physical support from QEMU-only tests.

The 384MiB requirement remains a separate research gate: RAM-only boot works, but active Firefox browsing at 384MiB is still not achieved.
