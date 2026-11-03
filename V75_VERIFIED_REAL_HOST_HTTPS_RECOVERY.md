# Puppy50 v75 — VERIFIED: Firefox resumed public HTTPS browsing after host bridge interruption

**Completed real KVM workflow:** https://github.com/74127418528426leo-del/Test/actions/runs/41674232157

**Unchanged ISO:** public Puppy50 Web v70, SHA-256 `26a9b339c6de87a1c891512742d608a910f4bbfce66fe26a96159297c98f8e2e`.

## Real observed result

- 1024 MiB KVM guest, two CPUs, e1000 QEMU NAT, read-only boot CD.
- RAM-only Linux boot and virtual CD ejection passed.
- Guest DHCP, DNS and CA-verified public HTTPS boot test passed.
- At 165 seconds the host HTTPS bridge's known PID was stopped; its loopback socket `127.0.0.1:3128` was independently verified unreachable.
- At 185 seconds the bridge was restarted; its local listener and a fresh **host-side CA-verified HTTPS request** to Wikipedia both succeeded.
- At 205 seconds a real QEMU virtual-mouse click opened Wikipedia in the same guest Firefox session.
- Genuine guest screenshots at 205, 245 and 285 seconds were individually inspected and showed the real Wikipedia homepage, not a browser error or blank screen.
- The automated KVM acceptance workflow concluded **success** with no logged QEMU harness errors.
- No Linux ISO was rebuilt or modified for this test.

## Scope

This verifies recovery from a deliberately interrupted **host-side TLS-preserving CONNECT service** and renewed public-site browsing. It does not demonstrate an actual change of Wi-Fi SSID, VPN/captive portal authentication, unrestricted access to every network, live streaming, encrypted session persistence, or physical GPU compatibility.

Keep the public v70 release unchanged and continue coherent graphics packaging.