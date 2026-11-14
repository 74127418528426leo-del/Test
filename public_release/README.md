# Puppy50 Browser Live — public test preview

Puppy50 Browser Live is an experimental, browser-focused Debian Live image for 64-bit x86 computers. It starts a temporary desktop with Firefox ESR. This is not the official Puppy Linux distribution and is not a certified, production-ready operating system.

## Before starting

- Use a separate USB drive with at least 2 GB of capacity. Writing the ISO **erases the selected drive**. Double-check the target before writing.
- Use a 64-bit x86 computer with at least 4 GiB RAM recommended. This build copies the live filesystem into RAM; the earlier 384 MiB goal is not met.
- This is a temporary live session: save files elsewhere before shutdown. Installed programs, settings, and security updates generally disappear on reboot.
- Keep the boot media connected during the session. No physical-media removal indicator has been verified.
- This preview has only been tested in virtual machines. Physical computers, individual graphics and wireless adapters, dual monitors, audio, Secure Boot, and streaming services remain unverified. Keep your usual OS and separate recovery media available.

## Download and verify

The release provides an ISO and an optional ZIP containing that same ISO. To verify the ISO on Linux, put it in the same folder as `SHA256SUMS` and run `sha256sum -c SHA256SUMS`. On macOS compare `shasum -a 256 Puppy50_Browser_Live_Public_Preview.iso` with the checksum. On Windows PowerShell compare `(Get-FileHash 'Puppy50_Browser_Live_Public_Preview.iso' -Algorithm SHA256).Hash` with the checksum.

A checksum helps detect corruption relative to the published value. This preview does not provide an independently verifiable signing key or a signed update system.

## Boot

1. Write the ISO to the USB drive using a trusted image-writing tool, confirming the selected drive. This erases that drive.
2. Restart the computer and select the USB drive from its firmware boot menu. BIOS and UEFI were tested in VMs; Secure Boot has not been verified.
3. Choose **Start Puppy50 (copy to RAM)**. If graphics fail, try the menu's **basic graphics** choice. Neither option is guaranteed to work on every computer.
4. Use the network icon to select a connection. Wireless support and captive portals depend on the hardware and network.

The menu's legacy recovery option uses an older kernel and is for **offline troubleshooting only**. It shares the same USB drive and is no substitute for separate recovery media.

## Security and maintenance

The image was built from signed Debian repositories and contains Firefox ESR 153.7.0 and Debian kernel 6.12.117. These versions will eventually become outdated. The image does not have a verified persistent update mechanism: get a newly rebuilt image for later security updates rather than assuming a temporary update survives reboot. Do not use the preview as if it were security-certified.

VM testing covered boot, Firefox interaction, JavaScript, local network requests after virtual-media removal, a valid public HTTPS site, and the browser warning on an expired certificate. It did not establish a guarantee for every site or machine. Tests measured startup from the virtual machine process start, not physical power-on, and do not establish a sub-seven-second boot.

In additional VM checks, GitHub, CNN and YouTube pages loaded. CNN's live stream requested DRM, which was not verified, and YouTube requested a sign-in/bot check before the selected test video would play. Video playback and 4K performance are therefore unverified; website prompts can vary by network and account.

## Source and notices

The release includes build and test evidence, the project's scripts, an installed package inventory and a source-package index. Four source ZIPs mirror the Debian Snapshot files listed in that index; their contents are identified by hashes. On Linux, download the four ZIPs, `SOURCE_INDEX.json`, `SOURCE_FILE_DETAILS.json` and `PROJECT_SOURCES.zip` into one directory, extract the project scripts, and run `python3 restore_sources.py <release-directory> <output-directory>` to reconstruct the Debian source-package files. Original Debian copyright notices are available in the running system at `/usr/share/doc/<package>/copyright`.

The build starts from the earlier v115 image and applies the project's documented changes and Debian upgrades; the scripts do not claim to recreate every part of that earlier image from source. Firefox is a Mozilla trademark; this project is not affiliated with Mozilla or Debian.
