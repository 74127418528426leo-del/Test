# Puppy50 v111 — Intel Fast Start (EXPERIMENTAL)

This is an experimental Debian Live browser system, not an official Puppy Linux release. It does **not** meet the eight-second goal and has not been tested on the physical Acer Aspire X3950.

ISO SHA-256: `3ead70c1876e0ae02759ffd5887ef89a7e47eb87f4756faba65958bd011101e6`

## What changed

Fast Start is optimized for an Intel-graphics-oriented machine. It omits two NVIDIA GSP firmware files from the early initramfs and sets `usb-storage.delay_use=0`, reducing the USB mass-storage device scan delay. The system filesystem, kernel, CPU microcode and early driver archive remain the same as v109. The ISO also includes the original, complete v109 initramfs for the **Full RAM first (fallback)** and recovery menu entries. The reduced early image and shorter scan delay may not work on all graphics hardware or USB devices. The [v110 USB-only release](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v110-usb-faststart-experimental) and [v109 release](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v109-faststart-ram-experimental) remain available.

## Measured startup

An A–B–B–A comparison with two runs of each image on the same virtual host used BIOS, two virtual CPUs, 3 GiB guest RAM, a conservative virtual CPU feature mask, and a 30 MiB/s virtual USB read cap:

| Measurement | v109 | v111 combined experiment |
| --- | ---: | ---: |
| First Firefox home page visible, mean | 19.560 s | 17.085 s |
| RAM-ready marker, mean | 38.230 s | 35.740 s |

These measurements start immediately before QEMU launches, not at physical power-on. Screenshots were sampled approximately every 0.8 seconds; two runs per image are not a full statistical study. Keyboard interaction, a fresh local page and an HTTPS page were checked **after** RAM was ready and virtual media was removed; they were not timed at the first visible frame. No physical Acer boot time can be inferred from the VM.

## Virtual testing and limits

- A BIOS virtual USB guest with 2 GiB RAM reached the RAM-ready marker and opened a fresh local page and HTTPS after virtual media removal.
- UEFI virtual USB boot offline, UEFI virtual optical boot online, BIOS full-RAM fallback, and restoring an intentionally blocked virtual network were tested with 3 GiB guests.
- An independent audit compared this image with v109 and verified the original fallback initramfs, root filesystem, kernel, and early microcode/driver prefix. It checked the two omitted firmware files and retained the remaining extracted early-boot contents.
- Physical Acer hardware, real Wi-Fi, audio, graphics, Secure Boot, 4K playback, captive portals, enterprise authentication, VPNs, and all network adapters remain untested. The earlier 384 MiB RAM target remains unmet for this browser build.

## Using the image

In Fast Start mode **keep the USB connected until the green RAM READY message appears**. If it remains amber or turns red, keep the USB connected. The full-RAM fallback does not display the green notice; if uncertain, leave the USB connected. Writing the ISO to a USB drive erases the selected USB drive. Browser data and downloads are temporary unless deliberately saved elsewhere. This image does not automatically keep the browser and system current across fresh boots.
