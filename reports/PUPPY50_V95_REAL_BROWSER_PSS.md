# Puppy50 v95 — verified low-memory browser investigation

**Date:** 2026-11-03. **Evidence:** [real GitHub Actions browser comparison](https://github.com/74127418528426leo-del/Test/actions/runs/41728811943). **Source:** [web95](https://github.com/74127418528426leo-del/Test/tree/puppy50-v95-lowram-browser-audit/web95).

## Actual measured memory — Wikipedia

Measured in real Debian 13 graphical test containers. Peak observed **proportional set size** (PSS) across each browser's nonroot user session, including its DBus helpers; excludes the X server, kernel, RAM-only operating system image, and other host processes.

| Browser | Peak Wikipedia-session PSS | Real Wikipedia screenshot |
|---|---:|---|
| Dillo | **14.42 MiB** | YES |
| Links2 graphical | **30.15 MiB** | YES |
| NetSurf GTK | **122.35 MiB** | YES |
| surf/WebKitGTK | **423.56 MiB** | YES |
| Luakit/WebKitGTK | **436.04 MiB** | YES |
| Falkon/QtWebEngine | **445.57 MiB** | YES |
| Firefox ESR | **687.38 MiB** | YES |
| Cog/WPE WebKit | no valid measurement | Failed to load required X11 platform module in this minimal Debian image |
| Epiphany/GNOME Web | no valid measurement | GUI startup failed in minimal Xvfb/DBus environment |

**Important:** These are one-run container session measurements, not tested 384 MiB full-OS footprints or statistically repeated minimum requirements. Cog and Epiphany failures are setup/environment limitations, NOT evidence that their browsers use no memory or cannot run on a real desktop. Site rendering was inspected independently; the automated job's status alone is not proof of website content.

## Outcome

- **Strongest 384 MiB RAM-only Puppy50 Lite candidate: Dillo**, with Links2 as a basic-browser alternative. Dillo lacks JavaScript; do not suggest universal modern web compatibility.
- **NetSurf** is a graphical compromise, but JavaScript support is primitive/incomplete.
- **Modern JavaScript engine comparison:** surf/Luakit/Falkon offer relatively thin UI yet still require a substantial rendering engine. Cog/WPE deserves a separate working-platform test, not a memory claim.
- **Firefox** remains the maintained general-purpose fallback for JavaScript-heavy websites at larger memory allocations.
- **Pale Moon official 64-bit** requires AVX and >= 2 GiB free RAM, a poor fit for old first-generation Intel Core hardware.

## Experiment integrity

The first CI run lacked cross-UID access to `smaps_rollup` and its numeric PSS values were invalid. That was fixed by a same-UID unprivileged `owner_probe.py`, excluding sampler and zombie processes. **All numeric figures above are from the corrected run**. Each candidate opened blank, example.com, and wikipedia.org for timed tests, capturing process samples, logs, and PNG screenshots. Dillo, Links2, NetSurf, surf, Luakit, Falkon and Firefox completed measurements. Cog and Epiphany failed the start gate, so the overall matrix is marked failure: this is expected fail-closed behavior.

## Next test

Build a genuinely small **Dillo-based RAM-only Live ISO**, with kernel, authorized network setup, and Wi-Fi driver support. Measure **actual 384 MiB guest** startup, guest HTTP/HTTPS browsing and memory margins; don't promote the image without independent proof. The existing maintained Firefox ISO remains separate. Do not reduce sandbox or TLS verification for memory savings.

## Primary sources

- https://dillo-browser.org/user_help.html
- https://dillo-browser.org/release/
- https://www.netsurf-browser.org/documentation/info
- https://webkit.org/wpe/
- https://www.palemoon.org/systemrequirements.shtml
- https://www.kernel.org/doc/html/latest/filesystems/proc.html
