# Puppy50 v113 Local Media — experimental

This is a Debian Live-based browser system, not an official Puppy Linux release. It starts Firefox while it copies the live system into RAM. Compared with v112, its Fast Start image defers 199 network drivers until after the local root filesystem is mounted. An independent audit verified every removed early driver has a byte-identical copy in the unchanged root filesystem. CPU microcode, kernel, compressed root filesystem, main boot archive, boot menus, and the original full-RAM-first fallback are byte-identical to v112. The Fast Start change is intended for local USB or optical media; network-root/PXE boot was not verified.

**The eight-second goal has not been achieved. The 384 MiB RAM-only Firefox goal has not been achieved.** No physical Acer computer or Wi-Fi adapter was tested.

## Measured startup

Each comparison used one QEMU/KVM host, 2 virtual CPUs, 3 GiB guest RAM, BIOS, and a virtual USB with a 30 MiB/s read cap. The timer began just before QEMU launch and includes virtual firmware and menu time. It does not include physical power-on or POST. The virtual CPU feature mask does not reproduce the actual speed of an Intel i3-540. Browser response includes automated URL typing started after detecting the home screen.

| Matched comparison | v112 | v113 | Samples |
| --- | ---: | ---: | ---: |
| First Firefox home frame, initial comparison | 14.90 s | 14.82 s | 2 per image |
| First Firefox home frame, independent repeat | 16.26 s | 15.70 s | 3 per image |
| Local page JavaScript response, repeat | 19.70 s | 19.07 s | 3 per image |
| Verified RAM-ready signal, repeat | 37.71 s | 37.08 s | 3 per image |

The two comparisons ran on different hosts; compare versions within the same row. The first improvement is smaller than the approximately 0.2-second frame-poll sleep plus capture overhead. The independent repeat suggests a modest improvement under those VM conditions, not a guaranteed improvement on all computers or a physical eight-second boot.

## What was checked

- At 3 GiB guest RAM, UEFI USB offline, UEFI optical online, BIOS full-RAM fallback, and a BIOS network-restoration case all passed separate VM tests. The Fast Start cases signaled a verified RAM copy and Firefox accepted input after simulated boot-media removal. The fallback VM used the original full-RAM-first path. Public HTTPS was checked by viewing the resulting browser frame.
- In the initial and repeated 3 GiB comparisons, Firefox responded to a local JavaScript page before the staged RAM copy finished, and it continued browsing after the virtual USB was removed.
- A separate audit checked the two initramfs archives, all removed driver copies, unchanged core files and recovery image, and all 293 included ISO checksums.
- One BIOS USB 2 GiB test showed Firefox but refused RAM migration because its available-memory reserve was not met. Do not assume this image will run RAM-only at 2 GiB. Tests at 1 and 1.5 GiB showed a local JavaScript response with the USB attached but did not complete RAM migration. A 384 MiB VM failed during early initramfs unpacking and did not reach the browser. The compressed root filesystem alone is 696,545,280 bytes (about 664 MiB), larger than 384 MiB.

## Use and limitations

In **Fast start**, keep the USB connected until the green **RAM READY** message appears. If the status turns red, keep the USB connected; the system has not completed the RAM transition. The **Full RAM first (fallback)** boot-menu option retains v112's complete original initramfs and was tested in a 3 GiB BIOS VM. The fallback does not show the green indicator.

The user's physical Acer Aspire X3950, physical USB drives, Wi-Fi association, video acceleration, Secure Boot, and real-world 4K streaming were not tested. Some adapters may depend on early network drivers, so retain the previous v112 image and use the fallback if Fast Start fails. No claim is made that all networks or websites work. This experimental live session loses unsaved changes on shutdown. Writing an ISO to USB normally erases the selected USB drive; select it carefully.

Previous image: https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v112-fast-read-experimental

## Integrity

ISO size: 906,297,344 bytes (864.31 MiB).

SHA-256: `4e6dc9b9d1f8f416b47ea046ffcfc5f1c6a7a732dc9ac0e67ff49bd53d271ea1`

The release evidence archive contains the benchmark, validation, low-memory, and independent-audit logs and screenshots, together with the relevant test sources. This is a prerelease for testing, not a completed eight-second system.
