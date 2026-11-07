# Puppy50 v108 — faster RAM boot (experimental)

This is an experimental, Debian-based, browser-focused live image. It starts Firefox automatically and provides NetworkManager for supported wired and wireless networks. The default boot copies the compressed live system into RAM before opening the browser. A physical Acer and physical Wi-Fi have not been tested. This is not an official Puppy Linux release.

- Download size: 841,285,632 bytes (802.31 MiB).
- ISO SHA-256: `6bc9393a62667305bcdee18d763fc0f26a67a8abaeea001633c0c5057b47bcad`.
- The BIOS and UEFI default live entries request `toram`. The one-second menu still offers a fail-safe entry, but fail-safe was not boot-tested and does not request `toram` by default. The automatic default selection and moving the highlight to fail-safe were tested in a BIOS VM; a physical keyboard was not tested.
- Compared with v107, the automatic development network probe is disabled so Firefox does not wait for it. NetworkManager, browser certificate verification, Firefox, the kernel, firmware and network drivers are retained. The old opt-in test proxy depended on the disabled probe and is no longer available in this image.
- The early boot archive is losslessly recompressed: the early archive prefix, including microcode, is byte-identical, and the decompressed main archive matches byte for byte. Standard Debian initramfs tools successfully opened both. The BIOS and UEFI menu wait is reduced from two seconds to one.

## What the tests actually show

The same-host A-B-B-A virtual comparisons used a QEMU guest with two virtual CPUs, 3 GiB RAM, a restrictive old-CPU feature model, BIOS boot, a virtual USB read cap of 30 MiB/s, and two measurements per version in each scenario. Timings run from immediately before QEMU starts to the first detected Firefox home frame, sampled approximately every 0.8 seconds. The host CPU was AMD EPYC 9V45 for the normal comparison and AMD EPYC 7763 for the blocked-HTTPS comparison. They are separate hosts; compare versions within each row only. This CPU model does not reproduce the real i3-540's speed.

| Scenario | v107 mean | v108 mean | Observed improvement |
| --- | ---: | ---: | ---: |
| Normal virtual networking | 48.00 s | 45.17 s | 2.83 s |
| Outbound HTTPS deliberately blocked during startup | 55.26 s | 46.93 s | 8.33 s |

The eight-second goal has not been achieved or measured on physical hardware. BIOS USB and UEFI USB or optical boots were checked in virtual machines. In successful online cases, Firefox loaded a fresh local test page after the virtual boot media was removed, then loaded example.com over HTTPS. Another VM started with HTTPS blocked and loaded that website after access was restored in the same session. An independently modified diagnostic image showed the live compressed filesystem and writable overlay in RAM; that diagnostic is not a bit-for-bit copy of this release. Actual Wi-Fi association, physical hardware, device-specific drivers, sleep/resume, video acceleration, and Secure Boot remain untested.

At 1 and 1.5 GiB guest RAM, the browser did not complete the after-ejection page test. A 2 GiB BIOS online VM passed once, and a 2 GiB UEFI offline VM passed once; that is not a proven minimum for real computers or complex websites. A 384 MiB browser session is not demonstrated and is inconsistent with copying the roughly 669 MiB compressed root to RAM. Heavy sites and video require additional memory and processor capacity.

The local home page contains an old statement saying no public website had been verified. That statement predates these VM tests; example.com was subsequently verified as described above. It does not imply every site or network is supported.

## Using the image

Write the ISO to a USB drive with a suitable ISO-writing program; writing normally erases the selected drive. Start from that USB using the computer's boot menu. The default live system should open Firefox; use the network icon in the bottom panel to connect to a network you are authorized to use. Hotspots, captive portals and enterprise networks depend on the hardware and network configuration and have not been individually tested.

This is an ephemeral live system: downloads, browser data, settings, and in-session updates are lost on reboot unless separately saved. Do not assume it will automatically keep the base image updated. Save important work externally and verify the checksums. Keep a working fallback until the actual computer, network, and the websites you need have been tested.

The previous experimental image remains available: https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v107-zstd-fastboot-experimental . The accompanying test-evidence archive includes screenshots, the validation results, checksums, and build reports, including the low-memory failures.
