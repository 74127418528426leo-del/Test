# Puppy50 v114 — trace-driven startup layout

**Goal:** Reduce time from QEMU launch to an actually usable, network-capable Firefox while retaining the staged RAM transition and its fallback; the 8 s target is not yet demonstrated.

**Baseline:** Published v113 local-media ISO, SHA-256 `4e6dc9b9d1f8f416b47ea046ffcfc5f1c6a7a732dc9ac0e67ff49bd53d271ea1`. Its 3 GiB BIOS/30 MiB/s virtual USB repeat averaged 15.70 s to the home frame and 19.07 s to an automated local JavaScript response; physical Acer power-on and execution speed are not measured.

**Architecture:** First observe file opens in an isolated v113 diagnostic VM, starting a short-lived fanotify monitor after the root filesystem mounts and before the desktop. Use only first-open paths from the immutable system tree to produce a squashfs sort order. Repack the exact same filesystem contents and metadata with the existing zstd and 256 KiB block settings. Keep the kernel, both initramfs archives and boot menus byte-identical. No live files, browser, security settings, firmware or drivers are removed.

**Constraints:** The filesystem trace must prove the monitor was active, detect queue overflow and include actual Firefox library/archive opens; treat any incomplete or perturbed trace as diagnostic only. Store the trace on guest tmpfs and preserve screenshots, logs and timing. Use the same host for A–B–B–A comparisons, starting the clock before QEMU; measure first real home frame, local JS response while media is still attached, verified RAM-ready, fresh page after USB removal and public HTTPS. A first frame is not proof of usability. Compare on a finer poll interval and repeat any plausible win.

**Work:**

1. Build a read-only guest file-open monitor and a trace-to-sort converter with tests for valid paths, duplicates, device and transient paths, and incomplete/overflowed logs. Instrument only a test image and verify the unmodified full-RAM fallback and media hashes.
2. Capture a real boot trace and use it to order a new SquashFS image. Verify that old and new extracted filesystem trees match in both directions, including metadata and hardlinks. Keep the default/unsorted v113 image as control; report any size and RAM-copy changes.
3. Compare the exact images in alternating order; require real JavaScript response and a new page after virtual USB removal. Repeat meaningful results on an independent host. Test other browsing content, BIOS/UEFI, offline, 2 and 3 GiB, network restoration, full-RAM fallback and independent media/root audits before distributing any candidate.
4. If the layout does not improve startup beyond sampling/noise, retain v113 and document the failed approach. A small sample does not establish physical performance, physical Wi-Fi, all network access, 384 MiB Firefox, or 8 s.
