# Puppy50 v35 — Experimental bootable ISO

**Status:** Actual QEMU CD-boot completed successfully. This is not a certified 50MB OS.

## Download and verify
- GitHub Actions run: https://github.com/74127418528426leo-del/Test/actions/runs/41448683211
- Full ISO + SHA-256: https://github.com/74127418528426leo-del/Test/actions/runs/41448683211/artifacts/13142929607
- ISO filename: `Puppy50_v35_EXPERIMENTAL_PRESEEDED.iso`
- ISO SHA-256: `1550c322179ed8fd30e29b2386d12559f6c0a51280a359ee22acf6d489bdac5d`
- Original BookwormPup64 10.0.12 SHA-256: `ae65f6e6d70a96f48bdbb291c2426f8a2fd77a73692e149e81a5eecb6fe7509f`

## Original programs preserved
The ISO retains the original BookwormPup64 main/adrv/bdrv/fdrv/zdrv/kbuild application SquashFS files and the original bootloader. It does not remove Firefox, Synaptic or other upstream applications. The initrd changes only the copy-to-RAM default while keeping explicit pfix=copy available.

The ISO adds a small ydrv measurement layer:
1. Correctly permissioned prebuilt plocate database for the immutable main SquashFS. Observed as root:plocate (mode 640) in guest.
2. Delayed automatic plocate database rebuild (it is postponed, NOT removed; first-boot delay does not make index updates cheaper).
3. Boot diagnostics to capture actual guest process and search status. These diagnostics are experimental and not suitable as permanent user-facing features.

## Independently verified actual guest results
Cloud test: original ISO SHA verified, modified ISO built and booted via QEMU CD boot, no -kernel override. 512MiB VM: Xorg/JWM/ROX-Filer/X11 socket pass; plocate search returns ROX-Filer paths; original Firefox ESR process starts. Human review of final framebuffer confirms Firefox GUI, title bar, tabs, address bar, original taskbar.

The 512MiB guest at the post-launch test point reported ~251648 kB MemAvailable and almost no used swap; this is a *point sample*, not stabilized memory, and user/browser input was not automated.

## Not proven
- No complete interactive browsing workflow or JavaScript test.
- No verified 50 MB physical RAM footprint.
- No verified 5× reduction in stabilized RAM use.
- No guarantee of full app suite, save-file and UEFI/dual-monitor compatibility.
- Search index covers the original main SFS, not every optional application SFS, and needs updating when files change.
- Old hardware (Acer i3-540, integrated graphics, dual monitors) has not been directly tested.

## Safe use
Use a virtual machine or a non-destructive live USB first. Verify SHA-256 before boot. Keep backups. This is experimental software, not a drop-in replacement for a working desktop system.

The GitHub Actions artifact may require GitHub authentication and has a limited retention window. It is a full ISO, not a small source ZIP.
