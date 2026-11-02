# Puppy50 Web — architecture decision record (2026-11-02)

## What has actually been demonstrated

- Full original BookwormPup64 v43: six RAM-backed SFS at 4 GiB allocated, root SFS total 627.59 MiB, Xorg/JWM/ROX after eject.
- Browser-only Alpine: compressed SFS ~369.7–369.8 MiB after hardware-focused pruning, complete RAM copy and /dev/sr0 removal in a 1,024-MiB QEMU guest.
- v46 boot success: direct dependency-ordered insmod, full RAM copy, CD unmount, OpenRC and Xorg.
- v46 browser failure: Firefox exited code 11 after a GLib `do_posix_spawn` assertion on `read_null != -1`. This assertion corresponds to failure opening `/dev/null` (read-only access) in the GLib subprocess launcher. A new change explicitly verifies and repairs non-root read/write access to `/dev/null`; whether the repair works remains an open KVM question until the new guest evidence is checked.
- One late-boot example (before working Firefox) had `MemTotal=988284 kB`, `MemAvailable=400056 kB`, `Shmem=379320 kB`, and `SwapTotal=0`. Thus the *nonavailable-memory proxy* was about 574.4 MiB and Shmem about 370.4 MiB. This is not full physical process accounting or a browser benchmark.
- No working Firefox render at 384, 512, 768, or 1,024 MiB has been certified for the browser-only build.

## Technical pivot, prioritized for meaningful savings

1. **Repair graphics/browser correctness.** Do not disable Firefox security features. Require the actual page visible in a KVM screenshot and a stable non-root process after CD eject. Validate input/navigation, then one network page.
2. **Measure entire runtime** after a controlled Firefox launch: `MemTotal`, `MemAvailable`, `Shmem`, `Slab`, `SReclaimable`, `SwapTotal`, kernel OOM/PSI pressure, and Firefox process RSS/PSS. Repeat at 1,024, 768, 512, and 384 MiB until the true minimum is measured.
3. **Remove boot-only duplication from resident root.** The Alpine root still includes `/boot`, even though the ISO has a separately loaded kernel and initramfs. Keep firmware and runtime modules needed by real peripherals.
4. **Hardware-adaptive RAM copy:** keep a universal installation ISO, but prepare machine-specific RAM payloads based on actual PCI/USB device IDs discovered at early boot, retaining a common USB keyboard/mouse/storage/network baseline. This can improve resident-size without inventing a universally tiny firmware set. Must ensure future hot-plugging remains usable for declared supported devices; selected modules and firmware should be measured in QA.
5. **Benchmark a second browser engine** under identical security, HTML/JS/WebGL compatibility requirements and actual rendering tests. Compare *full package dependency closure*, working RAM memory and latency, not front-end download size.
6. **Working hardware 384 MiB goal:** maintain no disk swap, all active OS layers RAM-backed, boot medium safely ejectable, Firefox or equivalent browser responsive, network and WebGL tested. If unsupported, report limits plainly.

## Design alternatives & tradeoffs

- A 384 MiB live system with a disk-backed filesystem **does not** meet the strict all-in-RAM requirement.
- Copying a 369.75 MiB SFS into 384 MiB leaves ~14.25 MiB for the entire kernel, framebuffer and process allocations; this build cannot meet the target as-is.
- Cloud browser offloading might reduce local memory but would change the requirement that web code runs locally, and requires internet; it is not a replacement for on-device browsers.
- Aggressively removing Firefox security sandboxing, TLS verification, driver safety checks or web isolation is **not** an acceptable RAM saving.

## Precise acceptance gate

Only call an ISO working when the actual QEMU guest proves (a) kernel and initrd load, (b) SFS copied to tmpfs, (c) source media unmounted/ejected, (d) Xorg and non-root browser remain alive, (e) a real HTML page is visibly rendered and keyboard/mouse controls respond, (f) memory statistics recorded after rendering, (g) basic HTTPS networking works without removing TLS checks. All requirements apply independently for each tested RAM size.

Latest experiment: https://github.com/74127418528426leo-del/Test/actions/runs/41536152682
