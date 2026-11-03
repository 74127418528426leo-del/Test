# Puppy50 v60 — a bounded zram-only swap experiment

Date: 2026-11-02 local. The code is isolated in this branch. **The actual v60 KVM result must be read before any claims of memory savings or working Firefox at 384MiB.**

## Why this is worth testing

The user requires every operating-system component and browser to operate in physical RAM, and the ISO/boot drive must be removable after startup. zram meets the diskless constraint: Linux compresses anonymous inactive pages into a **compressed RAM-backed swap device**, not a file on an SSD/HDD.

The previous v54/v57 QEMU-specific root is about 148.6 MiB compressed, leaving a nominal 235.4 MiB from 384 MiB before kernel, pagecache, Xorg, Firefox process memory, and writable tmpfs. Firefox's observed successful process PSS was much larger in a separate earlier 1 GiB reference. zram may help because some anonymous browser pages are compressible; it cannot create physical RAM or shrink the already XZ-compressed SquashFS.

Official Linux design: https://docs.kernel.org/admin-guide/blockdev/zram.html
Alpine guide: https://wiki.alpinelinux.org/wiki/Zram

## Actual v60 implementation

- Branch base is v59, itself combining v54's custom Softpipe-only LLVM-free Mesa with v58's validated early initrd evdev/psmouse input handoff.
- Retain `zram` kernel module and its module dependencies in the carefully selected kernel closure, loading it by direct insmod in the initrd before switching to RAM-root.
- Root's experimental launcher calls `web60/zram_setup.sh` **before launching Xorg or Firefox**, refusing to proceed if it cannot actually activate `/dev/zram0`. Zero disk-backed swap configuration is added.
- **Virtual swap capacity: 256 MiB**; **physical allocator cap: 128 MiB**. Neither adds to actual QEMU physical RAM. There is no backing filesystem/device for zram.
- Memory reclaim policy: `vm.swappiness=100`, `vm.page-cluster=0`. These are experiment parameters, not universal recommendations.
- Serial telemetry every four seconds samples real `/sys/block/zram0/mm_stat`, `io_stat` and `/proc/meminfo`. CI parses the actual occupied compressed physical bytes separately from virtual SwapTotal.
- Run real KVM 384 MiB and 1024 MiB guest allocations; verify RAM-copy, root-switch, CD-ejection, mandatory evdev event handlers, script-run indicator, click and keyboard DOM transitions. The final CI test intentionally fails closed unless **all** local offline interaction gates pass.
- If zram swap activates but `mm_stat` shows `orig_data_size=0`, report that it was **unused**, not that it saved memory.

## Acceptance and interpretive limits

- Compared to a v59 no-zram reference using the same kernel/Mesa root, note that the extra zram module/scripts slightly change SFS size. CI measures the new compressed root size rather than assuming 148.621 MiB.
- zram consumes CPU time and physical RAM for its compressed pool. With a 128 MiB cap it may exhaust its allocator and fail to help; process thrashing may make input sluggish. A passing boot does not prove acceptable interactivity.
- The guest has no configured external network. HTTPS/TLS, real websites, page navigation, WebGL and downloads are not validated by the offline DOM page test.
- The image excludes real Intel i915 firmware and uses software renderer only; physical Acer hardware and dual displays are not validated.
- The hand-overlaid Mesa packaging database is not coherent for security updates, so the build is **not production-ready**.
- If zram does not demonstrably lower the minimum working-memory threshold, the sensible next avenue is a fundamentally smaller secure browser engine in a real isolated VM with its namespace sandbox intact, such as WPEPlatform 2.54. Do not disable the sandbox merely to pass a test.

Live v60 workflow: https://github.com/74127418528426leo-del/Test/actions/runs/41561951905

No physical user computer was changed.
