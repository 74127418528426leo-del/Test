# Puppy50 v119: verified next steps toward <3-second Firefox cold startup

**Status:** Work has advanced; **NO VERIFIED UNDER-3-SECOND COLD BOOT**. The released v117 ISO remains the known published experimental reference. Never describe a firmware-suppressed warm resume, splash image, Firefox process PID, or host-injected kernel as an authentic full cold boot.

## Objective and strict proof gate

Measure host monotonic elapsed time **immediately before launching QEMU/KVM** through the first **actual framebuffer pixels of the real Firefox home page**, with no framebuffer substitution, browser warm start or VM suspension. Require full staged RAM migration **only after checksum verification**, physical-medium ejection **only after real RAM READY**, and independent *HTTP 200 receipts* for a new browser request after the boot medium is virtually removed. Preserve the complete working browser, TLS/CA store, sandbox, firmware and drivers; reject arbitrary "fast" regressions. Physical Intel i3-540/i915 and physical Wi-Fi/SSD tests are not inferred from virtual CPUID. Running 2 virtual CPUs at Westmere-compatible CPUID on modern AMD/Intel host does not emulate vintage CPU speed.

The exact reference ISO is:
[Puppy50 v117 released test ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v117-instant-bios-experimental), SHA-256
`a7fe532f501b9541c3a4fc22455e57ef79b8389eac6561720c25d7e188231b83`,
906,297,344 bytes. The original v115 test ISO remains independently available for recovery.

## Measured v119 experiment A: lossless root SquashFS Zstd -> LZ4

One same-host A–B–B–A KVM trial completed successfully on 2026-11-13, with 2 guest virtual CPUs, 3 GiB guest RAM, BIOS, uncapped AHCI virtual-CD storage, and 0.2s first-real-frame sampling. Every VM rendered Firefox, completed full checksum-verified RAM migration, ejected the virtual medium after READY, and generated a real HTTP 200 request to the matching test server. **No security check or hardware/network component was omitted.**

| Trial | First Firefox frame | RAM READY |
|---|---:|---:|
| Original v117 Zstd #1 | 7.33 s | 14.47 s |
| LZ4-compressed root #1 | **6.73 s** | 14.87 s |
| LZ4-compressed root #2 | **6.93 s** | 14.56 s |
| Original v117 Zstd #2 | 7.39 s | 14.51 s |
| **v117 Zstd mean** | **7.360 s** | **14.490 s** |
| **LZ4 candidate mean** | **6.830 s** | **14.715 s** |

Measured first-frame gain **0.530 s**, but full RAM READY on average **0.225 s slower**. Root compressed size increases from **696,545,280 bytes (664.3 MiB)** to **963,948,544 bytes (919.3 MiB)**, an increase of **267,403,264 bytes (255.0 MiB)**. That is a significant RAM and optical/USB storage penalty; do not extrapolate the result to slow USB media or low-RAM PCs. This worsens the already unmet 384MiB whole-system RAM requirement. Two actual LZ4 first frames remained **far above three seconds**. No v119 release was made as a result of this candidate alone.

[Independent GitHub Actions run, raw frames and receipts](https://github.com/74127418528426leo-del/Test/actions/runs/43491646882)

## Measured v119 experiment B: lossless initramfs Zstd -> LZ4

Only the Zstd-compressed main initrd cpio archive changed to Linux-compatible legacy LZ4 framing; the early microcode/module archive, root SquashFS, kernel, original full-RAM fallback, Firefox and drivers remained byte-identical. Original initrd **65,934,888 bytes** vs LZ4 **74,935,562 bytes**, a 9,000,674-byte increase. All four QEMU VMs actually booted Firefox, migrated the original root fully into RAM, ejected virtual media and received successful real HTTP 200 responses. The first aggregation attempt crashed *after* all VM boots with a report dictionary-key typo; an independent follow-up successfully reanalyzed the immutable saved trial JSON files and fixture logs, proving that this was an analytics-only failure.

| Trial | First Firefox frame |
|---|---:|
| Zstd original #1 | 10.73 s |
| LZ4 initrd candidate #1 | 9.87 s |
| LZ4 initrd candidate #2 | 10.45 s |
| Zstd original #2 | 9.91 s |
| **Zstd mean** | **10.32 s** |
| **LZ4 initrd mean** | **10.16 s** |

Mean gain **0.16 s**, within small-run host and framebuffer noise; cannot claim a reliable optimization. **Reject** main-initrd LZ4 as a useful change due added size and negligible gain. Different absolute host times across the v119 root and initrd experiments do *not* establish a ranking of the compression codecs.

[Original test VM evidence](https://github.com/74127418528426leo-del/Test/actions/runs/43491950347) · [Successful independent artifact audit](https://github.com/74127418528426leo-del/Test/actions/runs/43493234298)

## Measured critical-path observations and limitation

An instrumented v117 startup reached the live-root hook at ~**1.65s guest kernel uptime** and LightDM's user preflight at ~**3.96s guest uptime** in a functional test VM. A second instrumented test measured root ~**1.87s** and preflight ~**4.56s**. These are **guest kernel-uptime measurements, not host clock-from-QEMU-launch measurements**, and should never be combined numerically as if their origins were identical. The later Firefox-exec serial marker was absent in both instrumented runs, even after a reporter modification; the real Firefox frames/verified RAM and browser use passed. Therefore do NOT invent a Firefox-exec timestamp. The late reporter did not reliably finish, which is a *profiling test* limitation rather than a boot failure. The established login preparation timing alone reveals that the unchanged systemd/live-session startup path is not capable of reaching a real Firefox frame in three seconds.

[Instrumented v117 evidence (functioning browser, reporter incomplete)](https://github.com/74127418528426leo-del/Test/actions/runs/43492468608) · [Follow-up marker attempt](https://github.com/74127418528426leo-del/Test/actions/runs/43493044242)

## Architecture hypotheses under test

- Independently verified v118 early-user precreation gained **0.42s** in a matched A–B–B–A trial, with real post-ejection HTTP 200 subsequently proven on BIOS and UEFI. Can early-user be combined safely with the LZ4 root for an additional gain? A **combined ISO benchmark** has been defined under .github/workflows/puppy50-v119-integrated-early-user-lz4.yml, and must pass all manifest, browser and RAM tests before being treated as a usable candidate.
- A much smaller historical **220.5MB Alpine Firefox offline test ISO** uses a different live-root boot architecture; it is not secure-online/network equivalent to v117. Measure the original exact historical ISO's actual first JS-rendered page under 1GiB in a fresh KVM boot before spending effort on adapting its networking or fonts. Do not conflate an offline visual frame with a functional secure network browser. Defined in .github/workflows/puppy50-v119-alpine-cold-frame.yml.
- Reaching <3s with fully working modern Firefox on the physical old Acer may be impossible with the current Linux+X11+Firefox architecture, USB I/O and CPU. High-level strategies like kiosk auto-resume and preloaded VM snapshots would change the metric; label them warm resume, **not** genuine cold boot. A genuinely redesigned root/session/browser startup path would need independent hard evidence and full physical-hardware validation.

## Safety/status

**No newly published v119 ISO is certified <3 seconds.** Do not publish or claim a working v119 production OS simply because an experimental QEMU benchmark has a speed gain. Do not remove a physical USB until the green VERIFIED RAM READY notice. Keep the original v115 recovery medium separately available because the released v117 experimental BIOS Shift recovery menu remains unverified.

Tests are performed on isolated GitHub Actions KVM runners; the private physical Acer has not been booted. Browser networking and HTTPS evidence varies by experiment; the v119 root and initrd comparisons have verified four real authenticated local HTTP 200 responses after ejection, but that is not a real-world guarantee of every website, Wi-Fi SSID, 4K video or hardware configuration.
