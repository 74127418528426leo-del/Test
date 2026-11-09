# Puppy50 v114 Fast Verification — experimental

This is a Debian Live-based browser system, not an official Puppy Linux release. The fast boot starts Firefox while it copies the compressed system into RAM. This version changes the staged-copy verifier: it first tries the system's SHA-256 implementation and falls back to the original BusyBox implementation if that command cannot run. The entire copied filesystem still has to match the ISO's SHA-256 manifest before the system signals that the USB can be removed. The memory guard, browser, Linux kernel, firmware, compressed system filesystem, boot menus, and full-RAM fallback are unchanged from v113.

**The eight-second browser goal and the 384 MiB RAM-only Firefox goal have not been achieved.** The physical Acer computer, its i915 graphics, physical Wi-Fi, and real USB drives were not tested.

## Measured startup

| Matched test | v113 | v114 | Samples |
| --- | ---: | ---: | ---: |
| First Firefox home frame | 14.95 s | 14.84 s | 2 per image |
| Local page JavaScript response | 18.11 s | 18.08 s | 2 per image |
| Verified RAM-ready signal | 35.87 s | 34.34 s | 2 per image |

The observed first-frame difference is smaller than the approximately 0.2-second polling sleep, so this test does not establish a browser-startup gain. Verified RAM readiness was about 1.53 seconds earlier on that host. A separate diagnostic study measured the original complete-image hash at approximately 2.96 seconds and the faster hash at approximately 1.43 seconds; those diagnostic images are not this release image.

Each comparison used one QEMU/KVM host, 2 virtual CPUs, 3 GiB guest RAM, BIOS, and a virtual USB with a 30 MiB/s read cap. The timer began just before QEMU launch and includes virtual firmware and menu time. It does not include physical power-on or POST. The virtual CPU feature mask does not reproduce the actual speed of an Intel i3-540. The local JavaScript response time includes automated URL entry after the home screen appears. The small sample is not a guarantee of speed on another computer.

## What was checked

- An independent audit compared all 307 extracted ISO entries. Only the two copies of the fast boot archive and the checksum manifest differed from v113. Inside the fast boot archive, the only changed file was the staged migration script, and its only modification was the hash invocation and its BusyBox fallback. All 293 ISO file checksums passed.
- Virtual BIOS with 2 GiB, UEFI with 3 GiB, and the BIOS full-RAM fallback each booted, accepted browser interaction, and loaded a fresh local page after simulated USB removal. Public HTTPS was also seen in Firefox on the 2 GiB BIOS run. These are individual VM results, not guaranteed minimum RAM requirements.
- Separate fault-injection VMs retained the USB and did not signal readiness when the expected checksum was wrong or both hash programs were unavailable. When the fast program was missing, the original BusyBox verifier checked the entire copy and the VM remained usable after simulated removal. The tests used diagnostic images with the same hash-selection and digest-comparison logic.
- In v113 tests, 1 and 1.5 GiB did not complete the staged RAM transition, and a 384 MiB VM failed while unpacking the boot archive. This version retains the same root filesystem and boot architecture, so the 384 MiB goal remains unverified and unmet. The compressed root alone is 696,545,280 bytes (about 664 MiB).

## Use and limitations

In **Fast start**, keep the USB connected until the green **RAM READY** message appears. If the status turns red, keep the USB connected; the RAM transition has not completed. The **Full RAM first (fallback)** boot-menu option loads the original recovery environment before starting the desktop and does not show the green staged indicator.

The physical Acer Aspire X3950, its dual monitors and Wi-Fi, Secure Boot, video acceleration, and real-world 4K streaming remain untested. No claim is made that all networks or websites work. This experimental live session loses unsaved changes on shutdown. Writing an ISO to a USB drive normally erases that selected drive. Retain the prior v113 image as a fallback.

## Integrity

ISO size: 906,297,344 bytes (864.31 MiB).

SHA-256: `bf19a63758fbb6ab9aad5cb3b04c9b0e97b32944ab30f304fa16a205c78096b9`

The accompanying evidence archive contains the clean build, independent byte audit, safety fault tests, virtual-machine results, screenshots, and relevant test source. This is a prerelease for testing, not a finished eight-second system.
