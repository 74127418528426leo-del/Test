# Puppy50: additional architecture research

These diagnostic images are separate from the published v114 ISO. They were tested on virtual machines, not the physical Acer. None demonstrated an eight-second Firefox startup.

## Firmware-free upper bound

One prototype moved all firmware and documentation to a separate optional layer. Its fast core was 399,679,488 bytes (381.16 MiB), and the omitted layer was 296,886,272 bytes (283.13 MiB). In two matched BIOS VM boots per image, v113 versus the prototype averaged 15.97 versus 15.60 seconds to the Firefox home screen. RAM ready averaged 37.43 versus 26.15 seconds, but the latter copied only the firmware-free core. It does **not** preserve the full firmware after USB removal and must not be treated as a general-use image. Its full-RAM fallback was separately selected in a BIOS VM, loaded a page after virtual USB removal, and showed the restored firmware directory. Both layers reconstructed the original root in bidirectional checks.

## Dual-layer staged prototype

A separate prototype mounted both layers, copied and SHA-256-verified each before switching their device mappings, checked both RAM backings, and detached the old loops before displaying RAM ready. A two-run-per-image BIOS comparison against v113 averaged 15.23 versus 14.84 seconds to Firefox home, and 36.45 versus 36.22 seconds to RAM ready. The sample is small; those are not physical-Acer times and must not be directly compared with a measurement from a different host. The diagnostic prototype does not include v114's faster verifier.

An intentionally incorrect expected second-layer hash produced a not-ready failure while leaving the media attached. A separate fault injected after the core mapping switched retained both copies and media and produced not-ready. In that test the failure happened before the second helper began its real suspend/resume operation; it did not prove recovery from all failures inside a device-mapper switch. UEFI, low-memory and physical-device behavior remain unvalidated for this exact prototype.

## Acer-specific microcode prototype

Another prototype retained early Intel microcode records for the two documented i3-540 processor signatures while retaining the original complete recovery image. Its fast boot archive shrank by 14.08 MiB. In an independent four-runs-per-image matched BIOS comparison against v113, Firefox home averaged 14.78 versus 14.34 seconds and local JavaScript response averaged 17.98 versus 17.46 seconds. Separate VM UEFI, 2 GiB BIOS and full-RAM fallback tests passed. Other Intel processor models would lose matching early microcode if they used that prototype's fast path. The VM host was AMD and could not verify Intel microcode application on the actual Acer. The diagnostic ISO's menu did not adequately label the CPU restriction, and it is not the published general-use image.

## Pexels retry

The requested Pexels page showed a river image in one VM snapshot. Two separate inspection attempts encountered human-verification pages, and the browser exposed no video element in those attempts. Playback and its resolution therefore remain unverified.

The evidence ZIP contains machine-readable summaries, VM screenshots, serial logs, media checks, and fault-test output for the experiments above. Timing includes virtual firmware/menu time from before QEMU launch and does not measure physical power-on or POST.
