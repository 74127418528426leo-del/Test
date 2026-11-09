# Puppy50: complete firmware layer feasibility

## Measured on the exact v113 root filesystem

The v113 ISO was pinned to SHA-256 `4e6dc9b9d1f8f416b47ea046ffcfc5f1c6a7a732dc9ac0e67ff49bd53d271ea1`. The later v114 fast-verification candidate retains that identical compressed root. The experiment split `usr/lib/firmware` into a separate SquashFS, rebuilt the remaining root with the same Zstandard level 15 and 256 KiB blocks, then extracted and recombined both. Bidirectional `rsync -aHAXnci --delete --numeric-ids` reported no differences.

| Image | Compressed bytes | MiB |
|---|---:|---:|
| Original root | 696,545,280 | 664.277 |
| Root with all firmware removed | 426,160,128 | 406.418 |
| Separate complete firmware tree | 270,393,344 | 257.867 |
| Combined layers | 696,553,472 | 664.285 |

The size experiment moved 2,554 regular firmware files comprising 665,827,704 uncompressed bytes; no file was deleted from the reconstructed result. See [the completed measurement and audit](https://github.com/74127418528426leo-del/Test/actions/runs/42645762384).

At a cold read cap of 30 MiB/s, reading those complete layers takes at least 22.14 seconds in total, ignoring boot firmware, seeks, decompression and hash verification. The firmware-free core alone takes at least 13.55 seconds to read completely. Previous boot reads can populate the page cache, so the *later migration copy* can be shorter than this cold, aggregate data-transfer bound. Firefox can still open sooner than complete RAM readiness because SquashFS reads files on demand. Different hardware and storage produce different times.

The experiment measured file sizes and reconstructibility. **It did not create or boot a split ISO, test physical Wi-Fi, or establish an eight-second browser start.**

## Why a simple hardware-only firmware list is not sufficient

The exact image's kernel configuration contains `CONFIG_FW_LOADER=y`, `CONFIG_FW_LOADER_USER_HELPER=y`, and `# CONFIG_FW_LOADER_USER_HELPER_FALLBACK is not set`; both compressed XZ and Zstandard firmware support are enabled. The sample module metadata reports 67 Intel iwlwifi firmware names and 14 rtl8xxxu names; the zero-name results for other sampled modules are *not* proof that a hardware family never needs firmware. See the [exact-image config probe](https://github.com/74127418528426leo-del/Test/actions/runs/42646145840).

Firmware may be requested after a device is attached or on another driver operation. The [Linux 6.12 firmware documentation](https://docs.kernel.org/6.12/driver-api/firmware/fw_search_path.html) describes direct filesystem searches, and the [fallback documentation](https://docs.kernel.org/6.12/driver-api/firmware/fallback-mechanisms.html) explains when uevent fallback is disabled or unavailable. The [Linux 6.12 ath10k driver](https://github.com/torvalds/linux/blob/v6.12/drivers/net/wireless/ath/ath10k/core.c) constructs calibration and board filenames from bus and device identifiers at runtime. Therefore, gathering only names reported by the currently loaded modules is not an exhaustive general-purpose firmware manifest. A kernel firmware fallback event is not a dependable substitute for mounting the complete directory on the current configuration.

## Safe design conditions for a real two-layer experiment

1. Keep early storage and hardware firmware available and mount the complete split firmware layer before the drivers that need it probe. Preserve the original complete full-RAM boot option.
2. Keep both layers accessible while boot media is attached. SHA-256-verify the complete RAM copies against a pinned manifest; never mark readiness after copying only the currently detected adapter's firmware.
3. Switch every read-only layer's live backing to the verified RAM copy, check all relevant active mounts and loop/device-mapper backing paths, and only then emit the USB-removal signal. Any failure must retain the medium and report that removal is unsafe.
4. Test failure injection for each layer, USB removal, Wi-Fi re-probe, unplug/replug and attach of a second adapter after USB removal, resume, BIOS/UEFI and the full recovery path. QEMU wired Ethernet alone does not establish physical Wi-Fi or Acer graphics support.

A separate compatibility-limited experiment could retain only selected firmware in RAM, but its user-facing status would need to state that new or different adapters may require the original media and it would not be equivalent to the full-compatibility ready state.
