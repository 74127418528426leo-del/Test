# Puppy50 v108: continued fast-boot research

The exact published v108 image is SHA-256 `6bc9393a62667305bcdee18d763fc0f26a67a8abaeea001633c0c5057b47bcad`. It remains the release candidate for RAM-only boot. Its release notes contain its exact test limits; physical hardware, real wireless association, and an eight-second startup have not been verified.

## Initial demand-boot experiment: substantial opportunity, different behavior

A test-only derivative removed `toram` from the BIOS and UEFI kernel command lines, kept the system filesystem byte-identical, and regenerated and verified the 292-entry ISO checksum list. It reads the live system from the boot media and **requires that media to remain connected**. It is not the released RAM-only image and was not offered for download.

On the same AMD EPYC 9V45 virtual host, using BIOS, two vCPUs, 3 GiB guest RAM, a restrictive old-CPU feature model, and a 30 MiB/s capped virtual USB, the full-copy reference and media-attached derivative were compared in A-B-B-A order. Each figure is the first detected local Firefox home frame from just before QEMU launch; sampling interval was approximately 0.8 s. Two samples per case:

| Image | Samples | Mean |
| --- | --- | ---: |
| v108 full initial RAM copy | 45.47, 45.15 s | 45.31 s |
| Test-only demand boot | 19.48, 19.44 s | 19.46 s |

Firefox reached the home page, a nonce page explicitly labeled **MEDIA RETAINED**, and example.com over HTTPS in all four runs. The test harness reports the media was retained and never claims it was removed. Frame hashes are in `V108_DEMAND_REVIEW.json`; source workflow `.github/workflows/puppy50-v108-demand-study.yml`, Actions run 42398459428. This experiment does not show 19.46 s on the Acer, an 8-second boot, or a working later migration to RAM.

## Device-mapper migration feasibility: isolated proof only

A separate disposable host test created a small read-only SquashFS file, a byte-identical copy in tmpfs, and two read-only loop devices. A read-only device-mapper linear target was switched from the first loop to the second using an inactive table, suspension, and resumption. A concurrent reader completed 269 checksum passes without an observed error; the old loop and original file were removed and the mounted test fixture remained readable. Different contents were rejected before switching. The compressed fixture was only 104 sectors (53,248 bytes), though its expanded file was 8 MiB.

Actions run 42398618123, workflow `.github/workflows/puppy50-v108-dm-migration-proof.yml`. This does **not** test a live boot, the system's root filesystem, any physical machine, or safe USB removal from an OS. It is not a production implementation.

Avoid building the design on `LOOP_CHANGE_FD` or assuming the legacy `live-toram` script is safe: the [Linux kernel patch discussion](https://lists.openwall.net/linux-kernel/2026/10/12/1378) reports structural deadlock and filesystem issues in that interface and proposes removal. A device-mapper swap follows a different mechanism, but its use for a live root here still needs independent validation. The [kernel documentation](https://docs.kernel.org/6.0/admin-guide/device-mapper/writecache.html) describes device-mapper table replacement in another context; it is not a validation of this proposed OS.

The inspected v108 early boot includes the `dm-mod` kernel module and its live boot helper has `get_backing_device` and `setup_loop` entry points, but the inspection did not find a device-mapper userspace tool in the image. Source workflow `.github/workflows/puppy50-v108-inspect-migration-hooks.yml`, run 42398927528. Any implementation must add and verify a compatible userspace tool and dependencies without disrupting the rest of the initramfs or reducing hardware support.

A candidate design would start from the medium using a read-only device-mapper target, show Firefox, copy the image to RAM in the background, verify the complete copy, and switch the target before indicating that the USB may be removed. It must continue using the original medium if copying or verification fails; it must never tell the user removal is safe before all backing dependencies have moved. The switch procedure must itself run from memory so it cannot fault executable or library pages from the temporarily suspended root. It requires explicit tests for low memory, absent or corrupted media, mismatch and interrupted copy, suspend or resume failure, concurrent I/O, BIOS and UEFI, real website access, and post-switch unplug on the actual machine. Background copying may also slow browser startup through I/O contention. No timing or safety claim for this combined design is made yet.

## Firmware packing study

Splitting full firmware into an XZ SquashFS while keeping the rest Zstandard reduced the ISO from 841,285,632 to 814,022,656 bytes (26 MiB), without dropping firmware; reconstruction matched file content and checked metadata. In a two-sample matched VM comparison the means were 44.505 s for v108 and 43.97 s for the split-layer experiment, a 0.535 s difference below the approximately 0.8 s image-sampling interval. The more complex layout was not released. Actions run 42397422574, workflow `.github/workflows/puppy50-v108-layered-experiment.yml`.

## Physical constraint for the current all-before-Firefox strategy

The compressed v108 root alone is 701,440,000 bytes. At the USB 2.0 high-speed signaling ceiling of 480 Mb/s, an ideal transfer of that amount would take at least 11.69 s, without protocol overhead, firmware startup, the kernel, or Firefox. See the [USB-IF rate](https://www.usb.org/node/214). Real transfers are slower. This is a lower bound for copying this entire root over such a link before Firefox, not a prediction of any measured Acer boot time.
