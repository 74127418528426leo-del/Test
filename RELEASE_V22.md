# Puppy50 v22 — Experimental bootable ISO release notes

Based on checksum-verified BookwormPup64 10.0.12.

- Download full ISO and checksum through GitHub Actions artifact: https://github.com/74127418528426leo-del/Test/actions/runs/41435476630/artifacts/13135199743
- ISO file: Puppy50_v22_EXPERIMENTAL_BookwormPup64.iso
- SHA-256: f23b53067ce002841eb95f80c38a911244b489c81cb745abb352107f57d78bc4
- Source ISO SHA-256: ae65f6e6d70a96f48bdbb291c2426f8a2fd77a73692e149e81a5eecb6fe7509f

## What changed
Only the initrd's SquashFS copy-to-RAM selection conditional was changed. By default, compressed SFS layers remain disk-backed. Explicit pfix=copy can still request copying; nocopy overrides copy. The original desktop/application SFS layers and bootloader were preserved.

## Actual boot evidence
Cloud run https://github.com/74127418528426leo-del/Test/actions/runs/41435476630 completed. QEMU booted through its virtual CD, with no direct kernel/initrd override. Screenshots at 90/240/420 host seconds were captured. Human inspection of the 240- and 420-second images confirms the original BookwormPup64 JWM desktop and Quick Setup window.

xorriso confirms the ISO retains BIOS (/isolinux.bin) and UEFI (/boot/efi.img) El Torito entries. Only the legacy SeaBIOS path was actually tested; UEFI is not confirmed.

The automatic result.json deliberately says desktop_verified=false, since the automated script only captures images. Visual inspection was done separately.

## Not yet validated
The ISO does NOT meet 50 MB RAM. Fivefold steady-state reduction is unproven. Full application regression tests, networking, audio, 3D graphics, persistence, UEFI, and the actual user's dual-monitor desktop are still untested. The ISO is about 791 MiB on disk.

## Safe usage
Verify the SHA-256 in the downloadable artifact. Use a disposable VM or non-destructive live USB first. Do not overwrite the working system disk. This is experimental, not a general-purpose supported release.

GitHub download artifact expires November 9, 2026; GitHub sign-in may be necessary.
