# Puppy50 v72 — Second independent public-site interaction test

## Already demonstrated and protected baseline

- **Published v70 QEMU-only ISO**: https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-qemu-normal-v70
- Root fully copies into **1024 MiB guest RAM**, boot CD ejects, non-root Firefox renders a user-controlled homepage.
- DHCP, DNS, trusted guest TLS against example.com and optional TLS-preserving public-host CONNECT bridge demonstrated.
- **v71 Wikipedia**: a real QEMU mouse click from the normal user home screen visually displayed `https://www.wikipedia.org/`. Human-reviewed image hashes: `vm/V71_WIKIPEDIA_VISUAL_REVIEW.json`.
- Earlier **v69 Example Domain**: real public HTTPS page visually observed.

## New v72 test: Mozilla, without changing the OS

**Use the exact same byte-for-byte v70 ISO**, downloaded from Actions run 41660921113 and verified against its SHA256 manifest, not a source-based rebuild.

Using KVM's actual PS/2 virtual mouse:
1. Boot `-m 1024`, 2 CPUs, standard VGA, QEMU e1000 user NAT, and host-only TLS-preserving bridge.
2. At 145s, eject the boot CD after RAM-root boot and save a before-click homepage frame.
3. Move relative pointer right 220 units toward the Mozilla homepage tile. **Capture 165s pre-click hover** and inspect status bar/hover to identify the actual target.
4. At 185s, physically inject a left-click; capture 205, 245 and 275s webpage frames.
5. Require actual RAM-root, CD eject, guest CA HTTPS, Firefox home page and HMP input injection. Require the homepage cyan accent to disappear as a *transition*, not as proof of Mozilla content.
6. Inspect the screenshots manually. A Firefox blank page, error page, captive portal, or a different website **cannot** be counted as successfully displayed Mozilla.
7. If Mozilla loads, record the accurate test site, frame hashes, observed content and UI behavior. If not, investigate pointer placement, HTTP status, browser memory, TLS errors or blocked resources before altering the OS.

## Why this is the correct next engineering step

A Linux ISO being small and its browser receiving a PID are poor success criteria. The user needs real websites, inputs and device portability. Each independent site should produce measurable, reviewable evidence before the project claims it works widely.

Next test classes after Mozilla include a JS-heavy search site, a text/article page, file download over HTTPS, login with a **synthetic non-sensitive test account**, video playback, WebGL fallback, and mid-session host-network changes. Maintain a per-site result matrix with RAM/CPU, time-to-first-render, uptime, blocked resource categories and verified screenshots.

## Non-negotiable limits

- "Any network" is **not** literally possible: the host must have authorized connectivity, acceptable firewall/VPN policies and any required credentials. This QEMU edition only knows an emulated e1000 NIC and inherits authorized host Wi-Fi/Ethernet/hotspot.
- Do not disable TLS CA validation or browser sandbox. Do not test personal passwords.
- A real downloadable physical Acer-compatible ISO, security updates, and functional Firefox at 384 MiB have **not** been demonstrated.
- Keep v70 as the current downloadable preview. Do not publish new "working" ISO merely because a test script changed.
