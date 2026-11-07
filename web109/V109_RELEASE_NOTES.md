# Puppy50 v109 — Fast Start and RAM (EXPERIMENTAL)

**Experimental Debian Live browser system**, not an official Puppy Linux release. This release contains Firefox ESR and a NetworkManager connection menu. The ISO is 845,479,936 bytes (806.31 MiB); it is not a 50 MiB system and the original 384 MiB RAM target has not been met.

ISO SHA-256: `e6b341ae3a272bb6bfa063814b2b61a14ba9dadd5f41137a8203f651120671da`

## What changed

The default **Fast start** mode opens Firefox while the system continues preparing a verified copy in RAM. Keep the USB connected while the amber notice is visible. Only remove it after the green **RAM READY — USB may be removed** notice appears; you may click the notice to close it. If the red notice appears, keep the USB connected. The copy is checked against the ISO manifest before the switch; a deliberately wrong checksum was rejected in a virtual test, and the browser remained usable with the media attached.

The alternate **Full RAM first (fallback)** menu entry follows the earlier v108 approach. A BIOS virtual test selected it and continued browsing after virtual media removal. This fallback does **not** show the new green readiness notice; keep the USB connected if in doubt. Its home page retains an outdated statement that no public website has been verified; example.com has since opened in a virtual machine. UEFI fallback selection and the recovery menu entry have not been tested. The boot menu has a short timeout: use an arrow key promptly to select a nondefault option.

## Measured startup

In a matched A–B–B–A virtual test, with two runs of each image on the same AMD EPYC 9V45 host, a 2-vCPU, 3-GiB guest, BIOS, a conservative virtual CPU feature mask, and a virtual USB read cap of 30 MiB/s:

| Measurement | v108 | v109 |
| --- | ---: | ---: |
| Firefox home page visible, mean of two runs | 45.34 seconds | 19.46 seconds |
| RAM ready, mean of two runs | Full RAM copied before Firefox | 38.13 seconds |

The v109 first-browser result was 25.88 seconds, or about 57%, lower (about 2.33 times as fast). These measurements use the host clock beginning immediately before QEMU launch and sampled screenshots. They do not measure the physical Acer Aspire X3950, firmware power-on time, a real USB drive, or another computer. **The eight-second goal has not been achieved or verified.**

## What was tested

- BIOS virtual USB, UEFI virtual USB offline, and UEFI virtual optical media: Firefox and the RAM-ready transition were exercised, followed by a fresh page after virtual media removal. The online cases also opened example.com over HTTPS.
- A 2 GiB virtual machine completed the RAM transition and browsing after virtual USB removal. A 1.5 GiB virtual machine refused to make the RAM copy because it could not preserve its memory reserve and kept the media connected. This is not a tested minimum for real hardware. Start with 4 GiB or more for an initial trial; actual requirements depend on the hardware and websites.
- Virtual network access was restored in the same session after it was deliberately blocked. No physical Wi-Fi adapter, Wi-Fi authentication, captive portal, enterprise network, VPN, or Secure Boot has been tested. The original system image and firmware were retained, but no claim is made that every network or device works.
- After virtual USB removal, CNN's home page rendered behind its terms prompt, and your John Bible project's home page rendered. CNN indicated that some protected media required DRM. The YouTube test displayed a bot-verification sign-in request; Pexels displayed a security-verification screen. Neither video playback nor 4K resolution was verified, and Bible verse/3D interactions were not exercised.
- An independent image audit confirmed that the compressed system image and early microcode prefix match v108 byte for byte; the remaining initramfs contents and selected metadata matched except the documented boot changes and staged tools.

## Before using

Use a USB image writer to write the ISO; **writing the image erases the selected USB drive**. Choose the device carefully and keep a backup of important files. The live session is temporary: browser data, downloaded files and settings in RAM are lost on shutdown unless you deliberately save them to separate persistent storage. This experimental image is not a tested updater; its browser and system will not automatically remain current between fresh boots.

The ISO has not been tested on the Acer or other physical hardware. Real startup time, Wi-Fi support, stability, media playback, and security depend on the device and network. If it does not boot or the red notice appears, leave the USB attached and try the fallback or the earlier v108 experimental image.

The attached evidence archive includes the tested screenshots, logs, benchmarks, review hashes, package copyright notices, and source/test files. The image was built from commit `b0ec8274f84b58a78209a92f81400b272583a193`; validation scripts and release packaging are available on branch `puppy50-v108-architecture`.
