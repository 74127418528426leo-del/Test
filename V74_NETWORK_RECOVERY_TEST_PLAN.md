# Puppy50 v74 — Guest Ethernet link resilience test (controlled QEMU experiment)

## Why this test comes before a universal-network claim

The public v70 ISO already boots fully into RAM at 1024 MiB, retains Firefox after ejecting its boot CD, and has visually opened Example Domain and Wikipedia through the host-side QEMU NAT/HTTPS path. This proves basic network browsing, not the ability to roam between different physical Wi-Fi networks.

**Question:** When the virtual Ethernet carrier disappears briefly and returns, does Firefox recover far enough to open an external page without rebooting?

## Experimental control

- Reuse the exact public v70 ISO with SHA-256 `26a9b339c6de87a1c891512742d608a910f4bbfce66fe26a96159297c98f8e2e`. No new operating-system image or package modification.
- QEMU KVM, 1024 MiB RAM, two virtual CPUs, standard VGA, floppy/HD absent, read-only boot CD; e1000 NIC explicitly named `puppynic` with user-mode backend `puppynet`.
- The host's HTTPS CONNECT bridge runs on localhost, forwarding only public HTTPS destinations without terminating TLS.
- At 145 seconds: eject the boot CD, confirm RAM-root.
- At 165 seconds: issue real QEMU HMP `set_link puppynic off`; capture monitor evidence and screenshot.
- At 185 seconds: issue `set_link puppynic on`; capture monitor evidence and screenshot.
- At 205 seconds: click the previously proven Wikipedia tile using real HMP PS/2 mouse button events.
- At 245 and 285 seconds: capture the real Firefox framebuffer; independently check whether Wikipedia content is visible.
- The automation must fail if the virtual NIC, actual RAM-root, ejection, guest DHCP/DNS/TLS baseline, mouse command or homepage color transition are absent. Page content still requires visual review.

Official QEMU documentation for `set_link`: https://www.qemu.org/docs/master/system/monitor

## Claims this test can and cannot make

A passing result would mean **recovery after a simulated guest virtual-Ethernet link outage** while the host remains connected. It does not demonstrate host switching Wi-Fi SSIDs, moving between enterprise networks, new captive-portal credentials, physical NIC firmware, continuous DNS updates, or universal network compatibility.

An external page failing to load afterward is a valid and useful result. Investigate DHCP address/route/ARP, Firefox proxy startup mode, QEMU virtual link events, or browser connection caching, rather than simply increasing RAM or overriding certificate errors.

## Broader engineering roadmap

1. Direct QEMU NAT and host-only TLS bridge across authorized Wi-Fi, Ethernet and phone hotspot, with host egress and guest CA checks.
2. Mid-session link loss, host network change (when test runner/host safely supports it), DNS server update, QEMU TCP connection reset and reconnection.
3. Captive portals and enterprise Wi-Fi **only after user-managed authorization on the host**. Never bypass authentication or firewalls.
4. Package-coherent graphics and signed, security-maintained updates. The v73 audit found 8 Mesa digest mismatches and 5 unowned symlinks; fix via real tracked packages, not by hiding the audit.
5. Separate physical Acer-compatible Linux ISO with real GPU/network firmware, USB and dual-screen testing; do not publish as working hardware installation before tests.

Existing stable download: https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-qemu-normal-v70
