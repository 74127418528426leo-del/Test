# Puppy50 v65 — Isolate actual browser website access from GitHub runner Internet restrictions

## Observed v64 result (real guest)

Completed network KVM run https://github.com/74127418528426leo-del/Test/actions/runs/41573693962:
- QEMU e1000 driver initialized; DHCP, default gateway, DNS configuration and external-domain DNS resolution passed at **384 MiB** and **1024 MiB**.
- An external `https://example.com/` curl attempt timed out at the **TCP connection stage** in both guests. Certificate verification was NOT reached; this is not evidence of bad CA certificates.
- Real Firefox JavaScript, mouse and keyboard interaction passed at 1024 MiB.
- The guest submitted QEMU HMP navigation to external URL, but the screenshots did **not** prove successful external web rendering.
- The online ISO CI was correctly stopped before public release. The diagnostic ISO was preserved in a 3-day Actions artifact but is **not** a secure production build.

## Why v65 is a sharper test

The host (GitHub Actions Linux runner) serves a real HTML page at `127.0.0.1:8000/v65`. Official QEMU user-mode networking exposes the host on `10.0.2.2` from the guest.

A QEMU VM booting **the same exact v64 ISO** is instructed, via actual keyboard input, to navigate Firefox to `http://10.0.2.2:8000/v65`. The page contains a unique magenta background (RGB 203,45,145). The host HTTP server logs a request for `/v65`. The QEMU framebuffer is sampled before and after navigation and requires a magenta-fraction transition. Both the host request and Firefox pixels are needed for success. This avoids ambiguous browser PID/HMP results.

Tests run from the v65 branch without compiling a new kernel or replacing the v64 ISO. The workflow checks SHA256 of the archived ISO, runs real KVM at 1024 MiB, and uploads serial, screenshots and host request logs.

Workflow: https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-v65-website-proof.yml

## External Internet remains a DIFFERENT requirement

The workflow also measures **whether the GitHub runner** can reach external HTTPS directly (`curl --noproxy '*'`) versus its normal proxy environment without printing the proxy URL or credentials.

If host-normal HTTPS succeeds but direct host HTTPS fails, external guest connections through QEMU NAT can fail despite perfect guest DHCP and DNS, because QEMU NAT cannot transparently inherit host HTTP proxy settings. This is a possible explanation to test, **not a predetermined result**.

A host-served HTTP page passing at 1024 MiB would demonstrate virtual Ethernet, TCP, HTTP and actual Firefox rendering work together. It would NOT establish external HTTPS, captive portal access, every physical Wi-Fi adapter, hardware sound or security updates.

Production release gates remain: verified public HTTPS with certificate validation **inside the guest and Firefox**, browser updateability, repeatable cold-boot tests, physical hardware compatibility, and a 384 MiB working browser if the Ultra target is to be claimed.
