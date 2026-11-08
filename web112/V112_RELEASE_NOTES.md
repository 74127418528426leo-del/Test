# Puppy50 v112 Fast Read — experimental

This image improves the previous v111 experimental browser system by storing the same live filesystem in smaller SquashFS blocks for on-demand reads. The independent audit compared the unpacked filesystem contents and checked metadata. The kernel, Fast Start initramfs, full-RAM fallback initramfs, and BIOS and UEFI menu configuration are byte-identical to v111. Firefox's first-run notice remains present. This is a Debian Live-based experimental browser system, not an original Puppy Linux release.

**The eight-second target has not been reached.** The current results are virtual-machine measurements, not a measurement of a physical Acer computer.

| Measurement | v111 | v112 |
| --- | ---: | ---: |
| First Firefox home frame, matched layout test | 17.16 s | 15.47 s |
| RAM-ready, same matched layout test | 35.83 s | 36.63 s |
| Automated local page and JavaScript response, separate matched interaction test | 20.88 s | 19.66 s |
| ISO size | 877.31 MiB | 872.31 MiB |

Each matched comparison ran in alternating v111–v112–v112–v111 order on one QEMU/KVM host, with two virtual CPUs, 3 GiB RAM, BIOS and a 30 MiB/s virtual USB read cap. Timings start immediately before QEMU launch, include the virtual firmware and boot menu, and exclude physical power-on and POST. The home-frame detector sampled approximately every 0.8 seconds. These are two samples per image, not a reliable estimate for all computers. The interaction test starts automated typing only after it detects the home screen; its response time is not the earliest possible human interaction. Its USB stayed attached throughout the early interaction.

## What has been tested

- BIOS USB at 2 GiB RAM; UEFI USB while offline; UEFI optical media online; BIOS full-RAM-first fallback; and reconnection after a deliberate HTTPS outage. Each case was run in a virtual machine.
- In Fast Start cases, the guest reported a verified RAM copy, the virtual boot media was removed, and Firefox responded afterward. A new local page was fetched after removal when the guest was online. Public HTTPS was visually checked in the online restoration case.
- A separate audit compared every unpacked root filesystem file and checked metadata against v111, checked boot files for equality, and verified all 293 included ISO checksums.

## Limitations and use

- The physical Acer Aspire X3950, its USB stick, Wi-Fi hardware, graphics, audio, and other computers have not been tested. The virtual CPU feature mask does not reproduce an i3-540's actual speed.
- The earlier goal of a full Firefox browser system at 384 MiB RAM is not met; the smallest passing v112 browser VM used 2 GiB. There is no proof of smooth 4K playback or support for every network.
- In **Fast start**, keep the USB connected until the green **RAM READY** message appears. The desktop can be used before then, but removing the media early can interrupt it. **Full RAM first (fallback)** is available in the boot menu and does not show the green indicator.
- Writing this image to a USB drive erases the selected drive. Check the drive carefully before writing. Keep a copy of important data.
- This ISO is experimental. Its behavior with real hardware, time to boot, network connections, and media playback may differ substantially from the virtual tests.

## Integrity

The ISO is 914,685,952 bytes (872.31 MiB). SHA-256:

`317999f51e47698d90889b129e9f74bbbefaa382b4d481f4da32016861d8ddc7`

Source, exact test workflows, logs, and screenshots are available in this repository. Earlier v111 remains available separately.
