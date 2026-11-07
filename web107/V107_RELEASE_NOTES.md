# Puppy50 v107 Fast Boot — EXPERIMENTAL

This is a bootable, browser-focused Debian Live experiment derived from the previously published v106 image. The normal boot menu starts automatically, copies the live system to RAM using `toram`, and launches Firefox ESR. Wi-Fi and Ethernet are managed with the inherited NetworkManager setup. The image retains the same browser, root filesystem contents, drivers and firmware as v106, but compresses the read-only root with Zstandard rather than XZ. It also repairs and checks all 292 entries in the inherited media-integrity list.

**The eight-second target has not been reached or verified. No physical Acer, actual Wi-Fi adapter, or Secure Boot system was tested.** The ISO is an experiment, not a finished or broadly supported operating system. Use only networks you are authorized to join; hardware, drivers, authentication and captive portals determine which connections work.

## Download and integrity

* `Puppy50_v107_FastBoot_EXPERIMENTAL.iso`: 846,528,512 bytes (807.31 MiB)
* SHA-256: `cbdf605f87d345ca60d1a0a3cebb20312864c81c2a286c8eacb5acb85769c0c2`
* `SHA256SUMS` verifies the downloaded ISO file. This is a checksum, not an authenticated digital signature.
* The ISO contains a refreshed `sha256sum.txt` for the live-media integrity check; all 292 listed entries were verified by extracting the exact finished image.

## What was tested

The original compression experiment used a Xeon Platinum 8573C KVM host, two virtual CPUs, 3,072 MiB of guest memory, and a virtual USB storage read cap of 30 MiB/s. It booted v106 and the new-compression prototype twice each, in baseline–candidate–candidate–baseline order. Time from just before virtual-machine launch to the local Firefox home page averaged **60.585 seconds** for v106 and **48.44 seconds** for the prototype. Each result came from only two boots; screenshot checks were sampled approximately every 0.8 seconds. The prototype was subsequently rebuilt to repair its media-checksum file. These results cannot predict real Acer boot time.

The exact final ISO was then tested in QEMU/KVM under these separate configurations:

| Virtual boot | Guest memory | Network | Result |
|---|---:|---|---|
| BIOS, USB, 30 MiB/s cap | 2,048 MiB | Virtual Ethernet | Firefox home, fresh local test page after USB removal, and example.com |
| BIOS, USB, 30 MiB/s cap | 2,560 MiB | Virtual Ethernet | Firefox home, fresh local test page after USB removal, and example.com |
| UEFI, USB | 2,560 MiB | Offline | Firefox home and `about:about` after USB removal |
| UEFI, optical | 2,560 MiB | Offline | Firefox home and `about:about` after optical eject |

Screenshots and guest logs are included in the test evidence. The 2,048 MiB result is a limited VM test, not a universal minimum for modern websites. The UEFI tests did not use Secure Boot. A separate diagnostic-only derivative recorded a tmpfs-backed live medium, a SquashFS loop file under it, and a tmpfs overlay; the diagnostics were not added to the shipped image. The ordinary failsafe boot entries do not request `toram` and were not demonstrated to be RAM-only.

The read-only compressed root grew from 623,726,592 to 701,440,000 bytes, about 74.1 MiB more in RAM when copied. Comparing the extracted roots in both directions and checking hard-link groups found no differences in the compared content and metadata; the default boot configuration was unchanged. This is not a claim that every filesystem metadata class is identical.

## Using it

1. Verify the downloaded ISO against `SHA256SUMS`.
2. Write the ISO to a spare USB flash drive using an ISO-writing tool. **Writing an image erases that USB drive.**
3. Boot the computer from the USB drive and use the default live option. The system opens Firefox automatically. If the machine supports its wireless device, use the network icon to join an authorized network.
4. Save anything you want to keep to separate storage or a cloud service. This live RAM session is temporary and can lose changes when shut down.

On the Aspire X3950's built-in USB 2.0 ports, the 701,440,000-byte compressed root alone would take at least 11.69 seconds to transfer at the 480 Mbit/s USB 2.0 signaling maximum, even before protocol overhead, firmware startup or browser loading. This calculation applies to this image and full pre-copy architecture, not every conceivable OS design. Sources: [Acer Aspire X3950 service guide](https://www.mrmemory.co.uk/downloads/memory-configurations/65057.pdf), [USB-IF high-speed rate](https://www.usb.org/node/214), [Debian live-boot `toram`](https://manpages.debian.org/testing/live-boot-doc/live-boot.7.en.html).

## Reproducibility

* [Compression experiment](https://github.com/74127418528426leo-del/Test/actions/runs/42371438964)
* [Checked media-image build](https://github.com/74127418528426leo-del/Test/actions/runs/42372921677)
* [Exact-image tests](https://github.com/74127418528426leo-del/Test/actions/runs/42372995731)
* [Diagnostic derivative](https://github.com/74127418528426leo-del/Test/actions/runs/42373073284)
