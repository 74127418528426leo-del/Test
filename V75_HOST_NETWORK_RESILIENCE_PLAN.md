# Puppy50 v75 — Real host-side outbound HTTPS interruption and recovery

**Baseline:** exact public v70 ISO with SHA-256 `26a9b339c6de87a1c891512742d608a910f4bbfce66fe26a96159297c98f8e2e`. Reuses 1024 MiB KVM, non-root Firefox, QEMU e1000 NAT and trusted-CA public HTTPS.

A previous v74 test successfully disconnected and reconnected the **guest virtual Ethernet** adapter, then visually opened Wikipedia. This is strong but not equivalent to host Wi-Fi roaming.

## Changed dimension in v75

No OS build or kernel change. The guest NIC stays active throughout. Instead:

1. Start the host-only, public-address-restricted, TLS-preserving HTTPS CONNECT bridge on `127.0.0.1:3128`. Confirm the host can access Wikipedia with normal certificate verification.
2. Boot exact v70 in real KVM; confirm guest RAM-root and optical-media eject; wait until Firefox and certificate-verified guest HTTPS pass.
3. At 165 seconds, terminate only the known bridge process. Confirm the host-side TCP listener is actually unavailable.
4. At 185 seconds, restart the bridge and confirm public HTTPS through it, without relaxing certificate validation.
5. At 205 seconds, click the same verified Wikipedia tile inside Firefox with a real QEMU mouse event.
6. Save the actual framebuffer. The test only passes its automated gate if the homepage disappears after the click. **Human visual review must independently confirm Wikipedia content**, not an error screen.
7. No claim of direct Wi-Fi SSID selection, captive-portal bypass or an actual physical network transition is permitted.

Current workflow: https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-v75-host-https-recovery.yml

## Why this is important

It tests whether a running browser can resume external activity after an interruption in the **host-side outbound connection service**, without losing the in-RAM operating system or restarting the guest. This is closer to a useful user-facing recovery property than an additional small ISO byte reduction.

It still does not establish that all host uplinks, VPNs, firewall policies or wireless adapters are supported. Authorization and the host's network policies remain authoritative.