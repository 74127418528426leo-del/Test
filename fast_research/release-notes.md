# Puppy50 Browser Live — staged-start experimental preview

This experimental 64-bit Debian Live image combines staged startup with the Firefox ESR 153.7.0 and Debian 6.12.117 kernel packages included in the November 14 public preview. It is not an official Puppy Linux distribution or a production-certified OS. Packages reflect that build date and may need newer security updates. No persistent update mechanism is verified.

## Test results and limits

In a same-runner BIOS VM comparison with a two-second boot menu, two control Firefox first frames averaged 11.52 seconds; two candidate frames averaged 10.52 seconds. The candidate's JavaScript responses were 13.71–13.75 seconds and verified RAM readiness was 19.72–19.76 seconds. One UEFI VM reached its first frame in 14.09 seconds and RAM readiness at 23.28 seconds. A separate Cirrus VM used the standard desktop fallback, reached its first frame in 14.02 seconds and RAM readiness at 23.40 seconds.

Those VM tests used 3 GiB RAM and a virtual AHCI device. Their timer starts at QEMU launch, not physical power-on. The tested guest browsed a local server after the virtual boot media was removed, and screenshots show a public HTTPS page. Two trials per BIOS condition are too few to guarantee a speed improvement on every boot. Five- or seven-second complete boot is not demonstrated.

Physical computers, the Acer X3950, Wi-Fi adapters, dual monitors, Secure Boot and 4K video have not been verified. The early display shortcut is restricted to a recognized virtual graphics device; other devices take the normal desktop path. Keep the boot USB connected throughout the session: the indicator and media removal have only been tested with virtual devices. Use the separately published full-RAM preview as a recovery option.

## Booting and integrity

Use a 64-bit x86 computer with 4 GiB RAM recommended. Write the ISO to a separate USB drive with a trusted image writer; **this erases the selected drive**. Pick the USB drive from your firmware boot menu. The session is temporary, so save important files elsewhere before shutdown.

On Linux, download the ISO and `SHA256SUMS` into one directory and run `sha256sum -c SHA256SUMS`. On Windows use `Get-FileHash` in PowerShell and compare the SHA-256. These checks detect mismatches; they are not a digital signature.

The original public preview and its Debian source files are at https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-browser-live-public-preview-20261114. The scripts and exact changes used for this experiment are included in `PROJECT_SOURCES.zip`; the comparison, serial logs and screenshots are in `TEST_EVIDENCE.zip`. The build starts from the earlier preview and does not claim complete reconstruction of that earlier image from source. Firefox is a Mozilla trademark; this project is not affiliated with Mozilla or Debian.
