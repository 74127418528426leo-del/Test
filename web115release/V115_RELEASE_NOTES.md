# Puppy50 v115 Font Cache — experimental

This is an experimental Debian Live-based browser system, not an official Puppy Linux release. It adds an optional prebuilt system fontconfig cache to the v114 fast boot. If the cache cannot be installed, boot continues with normal font discovery. Firefox, all fonts, firmware, the compressed system root, and the complete full-RAM fallback are unchanged. v114's faster SHA-256 verification and its original BusyBox fallback remain in place.

**The eight-second browser goal and 384 MiB RAM-only Firefox goal have not been reached.** The physical Acer, its Wi-Fi and dual displays have not been tested.

## Matched virtual-machine results

| Measurement | v114 | v115 | Samples |
| --- | ---: | ---: | ---: |
| First Firefox home frame | 14.97 s | 14.23 s | 2 per image |
| Local JavaScript response | 18.33 s | 17.38 s | 2 per image |
| Verified RAM-ready signal | 34.59 s | 34.39 s | 2 per image |

The comparison used one QEMU/KVM host, two virtual CPUs, 3 GiB RAM, virtual BIOS and a virtual USB capped at 30 MiB/s. The timer began before QEMU launch, including virtual firmware and boot menu, but it does not measure physical power-on or POST. Local JavaScript response includes automated URL entry after Firefox's home screen appeared. The roughly 0.2-second frame-poll sleep and small sample limit precision. A separate four-per-image repeat of the earlier instrumented font-cache prototype also showed a modest improvement, but it is not this clean ISO and its absolute times should not be compared across hosts.

## Verification and limits

- A separate diagnostic VM confirmed all 20 seeded cache files matched their source hashes and were accepted before the desktop started; it observed non-root Firefox opening cache files before the first home frame. An open event does not establish cache parsing or prove the cause of a timing difference.
- An independent audit checked 307 ISO entries, the exact boot-script change and all 20 cache hashes. The root SquashFS, kernel, boot menus and full-RAM fallback matched v114; all 293 included ISO checksums passed.
- Separate virtual tests passed with BIOS and 2 GiB, UEFI and 3 GiB, and the full-RAM BIOS fallback. Each loaded a fresh page after simulated USB removal. These individual runs do not establish a guaranteed minimum memory requirement or real-hardware compatibility.
- The complete ISO is approximately 864 MiB, and its compressed root alone is about 664 MiB. A previous 384 MiB VM failed during initramfs unpacking. This is not a 50 MiB ISO or a demonstrated 384 MiB RAM-only browser.
- On v114, the user's John 1 panorama rendered and responded to input after simulated USB removal. YouTube required bot-verification sign-in, and Pexels playback remained unverified. A local synthetic 4K H.264 clip ran in a fast VM; that does not establish 4K streaming or Acer playback. These website tests were not separately repeated on v115.

## Use

In **Fast start**, keep the USB connected until the green **RAM READY** message appears. If the status turns red, keep the USB connected. The **Full RAM first (fallback)** option is unchanged and does not show the staged green indicator. The live session loses unsaved changes on shutdown. Writing an ISO to a USB drive normally erases that selected drive.

The actual Acer Aspire X3950, physical USB drives, physical Wi-Fi, Secure Boot, Intel graphics/dual monitors, and real 4K streaming remain untested. No claim is made that every network or website works. Retain the prior v114 image as a fallback.

## Integrity

SHA-256: `d697081adf836b7c8b75fe352964764e082b0214a262c8d9895eb9388c3e825a`

The accompanying evidence archive includes clean-image comparisons, separate guest cache proof, independent ISO audit, UEFI/BIOS/recovery test logs, screenshots, and relevant sources. This is an experimental prerelease, not a completed eight-second system.
