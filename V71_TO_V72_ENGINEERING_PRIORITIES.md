# Puppy50 — Engineering decision after real v70 + v71 Internet tests

## Verified baseline (do not regress)

- Public v70 ISO is a real 1024 MiB RAM-only QEMU browser system; root copy, CD eject, DHCP, DNS, guest CA-verified HTTPS and the user-controlled Firefox homepage passed in real KVM.
- The exact public v70 ISO has now opened a **second public HTTPS website, Wikipedia**, through a real QEMU pointer click on the user homepage. This was independently inspected from actual `frame_245.ppm` and `frame_275.ppm` screenshots, and recorded with SHA-256 in `vm/V71_WIKIPEDIA_VISUAL_REVIEW.json`.
- The previous public v69 ISO independently displayed `https://example.com/`.
- Wi-Fi/Ethernet/hotspot support currently means **authorized networking through the host via QEMU user-mode NAT**, not that this guest contains every physical wireless driver.

## Strategic priority: reliability and maintainability before smaller RAM

1. **Browser security maintenance**. Rebuild the custom Mesa replacement as tracked Alpine packages rather than unmanaged shared-library overlays. Pin and attest the kernel, browser and CA trust bundle; integrate timely CVE/security updates and reproducible signatures. Require a real browser sandbox assessment. Do not recommend account logins until this work is audited.
2. **Real public-site compatibility matrix**. Test actual Firefox rendering and interaction for at least 10 independent HTTPS websites with a diverse mix of static, script-heavy, interactive and media pages. Preserve actual KVM screens, serial logs, network transcripts without private user data, and guest memory PSS. A curl success does not substitute for browser frames.
3. **Network portability**. Use host-managed Wi-Fi/Ethernet/hotspot by default. Include explicit offline setting, read-only host network diagnosis, guest local DHCP/DNS/TLS status, and a normal Firefox proxy configuration. Test host network switching/reconnection, IPv4, optional IPv6, VPN and captive portals on authorized networks. Never bypass credentials, certificates or firewall policies.
4. **Physical ISO (separate hardware product)**. Start with an actual inventory of the target Intel GPU, Ethernet and Wi-Fi chipsets, BIOS/UEFI boot profile, USB controller, monitor layout and required firmware. Build a hardware-specific kernel module and firmware closure and test on physical devices. Broad physical Wi-Fi support cannot be certified through QEMU e1000.
5. **Memory targets**. Preserve the working 1024 MiB QEMU baseline, consider 2048 MiB guest allocations for heavier modern websites where host RAM permits, and continue 384 MiB only as a distinct research subproject. ZRAM alone has already failed to make Firefox render at 384 MiB with a measured full allocator cap.

## Acceptance tests before any claim of "works on any network"

A network is usable only if an authorized host/physical network link exists and the guest obtains a valid route, DNS, real CA-verified public HTTPS and actual Firefox page rendering. Test each of these separately. VPNs, corporate WPA/802.1X, captive portals and blocked sites depend on network policy and credentials; no operating system can make access universal.

## Distinctive product direction

Rather than advertising a smallest-ever ISO, build a **verifiable, adaptive, entirely RAM-only browser workspace**. Each boot emits a machine-readable signed evidence report: measured RAM, boot-media independence, network mode, kernel/firmware/profile compatibility, browser sandbox and update status, and actual website input/render checks. Offer safe fallback to offline mode on failure. This is a proposed engineering system, not yet a demonstrated industry first.

Public release: https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-qemu-normal-v70

Second real public site test: https://github.com/74127418528426leo-del/Test/actions/runs/41662860725
