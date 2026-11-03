# Puppy50 v79 — Human-reviewed 1024 vs 2048 MiB actual Firefox network comparison

**Real 3-way KVM workflow:** https://github.com/74127418528426leo-del/Test/actions/runs/41682409363

**Controlled variables:** KVM, 2 virtual CPUs, standard VGA, Linux RAM-root, identical click script, same public `https://www.wikipedia.org/` target, same TLS-preserving host-only HTTPS bridge, guest NIC continuously enabled. Each condition ran on its own GitHub Actions host; runner congestion and environmental variability prevent interpreting this as a universal performance benchmark.

| Guest source | RAM | Guest CA-verified public HTTPS | First homepage color disappeared | Actual Wikipedia page visibly present by end |
|---|---:|---|---:|---|
| v76 stock APK-managed Mesa | 1024 MiB | PASS | 325 seconds from VM start | **NO**: Firefox still showed a mostly blank loading page at 405 seconds |
| v78 complete APK inventory with LLVM runtime | 1024 MiB | PASS | 325 seconds from VM start | **NO**: Firefox still showed a blank page at 405 seconds |
| v78 complete APK inventory with LLVM runtime | 2048 MiB | PASS | 185 seconds from VM start | **YES**: genuine Wikipedia language portal visible by 185s and remained visible through 405s |

The mouse click was at approximately **165 seconds from VM launch**. A page being blank after navigation is **not** successful webpage rendering, even if the homepage turquoise background disappears and the CI's color-change gate passes. Hence the automated v79 workflow completed successfully for all three conditions, but human visual review qualifies *only* the 2048 MiB result as a real Wikipedia webpage success in this run.

## Exact screenshot evidence

- v76, 1024 MiB, final 405s frame SHA-256: `e5d9bf41187f09a5d136d9cbb450b661bfd0118876005d3cdd77f743f2f24213` — blank/loading webpage
- v78, 1024 MiB, final 405s frame SHA-256: `836fc7189067915382eb16f7fca536f443b89a02665dfe740a51c8d8c5284f80` — blank webpage
- v78, 2048 MiB, first confirmed Wikipedia screenshot at 185s SHA-256: `5810ac139716b3e9f64d2d2839e0de9c00826a42b54f2d2155a89eacc5b10f01` — Wikipedia content clearly present

The genuine raw PPM frames and guest serial traces remain in the workflow's three source artifacts. The intact, trusted-CA public HTTPS serial results passed for all conditions.

## Engineering interpretation

This suggests that memory pressure may be limiting site rendering at **1024 MiB**, but this single comparison does not prove the mechanism. The earlier v76 KVM run did display Wikipedia at 1024 MiB; therefore **1 GiB is inconsistent, not categorically impossible**. External network timing, virtual CPU scheduling and cache/graphics behavior might contribute. The v78 complete package inventory is not itself evidence of good runtime responsiveness.

The 2048 MiB v78 configuration is an independently supported **functional online baseline** for this site, but it is not enough to claim the browser works well on arbitrary websites or within 384 MiB.

## What to do next

1. Run controlled repeated **same-image** cold boots at 1024 and 2048 MiB, not one run, capturing per-run time-to-visible-Wikipedia and host QEMU CPU/RSS plus any kernel OOM messages.
2. Add an explicit screenshot content check or independent visual review to the release gate. Turquoise pixel disappearance is only navigation, not a loaded website.
3. Prefer 2048 MiB for a user testing v78's public website rendering while collecting reproducible evidence. On the user's 4 GiB physical host, test whether 2 GiB QEMU allocation leaves the host responsive.
4. For the preferred 1 GiB/384 MiB goals, investigate memory instrumentation and browser process optimization **without weakening Firefox sandbox, TLS or site isolation**. Image size on disk is not peak Firefox memory consumption.
5. Keep public **v70** as the unchanged experimental baseline until a candidate satisfies browsing, package integrity, patchability and resource acceptance gates. Do not claim every network is accessible.

**Scope:** all results are in QEMU using the host's authorized network. No physical Wi-Fi roaming, hotspot changes, actual old Intel graphics compatibility, complete vulnerability maintenance, or universal web compatibility were certified.
