# Puppy50 v110 — USB Fast Start (EXPERIMENTAL)

This is an experimental Debian Live browser system, not an official Puppy Linux release. It does **not** meet the eight-second goal, and it is not verified on the Acer Aspire X3950 or on a physical USB drive.

ISO SHA-256: `b2f6ce26c4a794d87fd2e29d1d22b7e49a1ee175d58d89f7b72215dd54bc8a9e`

## What changed

The Fast Start entry sets `usb-storage.delay_use=0`, reducing the Linux USB mass-storage device scan delay. The full-RAM fallback uses the original delay. The root filesystem, kernel and initramfs match the published v109 image. Some real USB devices may require more time to initialize, so this is a hardware-compatibility experiment; the earlier [v109 experimental ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v109-faststart-ram-experimental) remains available.

## Measurements

With two runs of each image in A–B–B–A order on the same virtual host, BIOS, two virtual CPUs, 3 GiB guest RAM, a conservative virtual CPU feature mask, and a 30 MiB/s virtual USB read cap:

| Measurement | v109 | v110 USB experiment |
| --- | ---: | ---: |
| First Firefox home page visible, mean | 19.535 s | 18.300 s |
| RAM-ready marker, mean | 38.310 s | 36.975 s |

Times start immediately before the QEMU process launches, not at physical power-on. Browser visibility was sampled approximately every 0.8 seconds; two runs per image are not a full statistical study. Keyboard interaction, a fresh local page and an HTTPS page were checked **after** the RAM-ready marker and virtual media removal; they were not timed at the first visible frame. No estimate is made for the physical Acer.

## What the virtual tests covered

- A 2 GiB BIOS virtual USB guest reached RAM ready, had its virtual USB removed, and opened a fresh local page and an HTTPS page.
- UEFI virtual USB boot in an offline 3 GiB guest, UEFI virtual optical boot in an online 3 GiB guest, and the BIOS full-RAM fallback were exercised after virtual media removal.
- A virtual network intentionally blocked at startup was restored in the same session. This does not prove physical Wi-Fi, captive portals, enterprise authentication, VPNs, or all network devices.
- The exact boot image's internal checksum list was verified. The included evidence contains logs and screenshots from the matched comparison and the additional virtual tests.

## Using the image

In Fast Start mode **keep the USB connected until the green RAM READY message appears**. If it remains amber or turns red, keep the USB connected. The full-RAM fallback does not display the green notice; if uncertain, leave the USB connected.

Writing an ISO to a USB drive erases the selected USB drive. Live-session browser data and downloads are temporary unless deliberately saved elsewhere. This release does not automatically keep the browser or system current across fresh boots. Physical Acer graphics, audio, Wi-Fi, Secure Boot, video playback, and 4K performance have not been verified. The earlier 384 MiB RAM target remains unmet for this browser build.
