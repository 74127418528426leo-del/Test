# Puppy50 Web v62 — QEMU-only experimental ISO preview

**THIS IS AN EXPERIMENTAL VIRTUAL MACHINE IMAGE, NOT AN INSTALLABLE OR PRODUCTION OPERATING SYSTEM.**

Puppy50 Web is a personal Alpine Linux-based browser-only research prototype inspired by Puppy Linux. This build combines the independently measured LLVM-free Softpipe Mesa graphics stack and the repaired early Linux evdev/psmouse input driver loading. It reuses publicly available Puppy boot media components solely as the initial boot foundation; it is not a standard BookwormPup image.

## What has been proven in real GitHub Actions KVM

* The SAME produced ISO is tested at 384 MiB and 1024 MiB physically allocated guest RAM.
* At **384 MiB**, the complete compressed root filesystem copies into RAM, the root is switched, and the emulated boot CD is ejected. **Firefox does not visibly render** at 384 MiB. It is not a usable 384 MiB browser.
* At **1024 MiB**, Firefox renders the bundled **offline** HTML page, executes JavaScript, responds visibly to a real virtual mouse click, and then changes again after a virtual keyboard T keypress.
* The kernel evdev and psmouse drivers are loaded from the initial RAM disk before the root switch; real event-device handlers are verified.
* No persistent root filesystem is attached in the test. The browser runtime and writable root live entirely in guest RAM.
* The graphics stack uses **CPU Softpipe**, not Intel Crocus, i915, or physical GPU acceleration.

## Practical VM-only test

On a Linux host with virtualization available and the QEMU system package installed:

```bash
# Ubuntu/Xubuntu example:
sudo apt-get install qemu-system-x86

sha256sum -c SHA256SUMS

# OFFLINE QEMU STANDARD VGA test, 1 GiB guest:
qemu-system-x86_64 -enable-kvm -m 1024 -smp 2 \
  -cdrom Puppy50_Web_QEMU_Preview_v62.iso \
  -boot order=d -vga std -nic none
```

On Linux without KVM acceleration, omit `-enable-kvm`, but expect much slower operation. No disk image is needed or attached. All guest changes vanish when the VM is shut down. Do not install this ISO onto a USB stick expecting normal hardware support.

The initial page is a locally packaged test page, not proof that general websites, downloads or modern internet applications work. The 1024 MiB allocation was tested for this offline test page only, and may not be sufficient for larger websites.

## Known limitations and explicit warnings

1. **Do not boot this prototype on your real PC as a general purpose OS.** Wi-Fi/Bluetooth/i915 and other physical-hardware firmware were intentionally removed for QEMU-only experiments.
2. **Do not enable networking for sensitive browsing.** Secure HTTPS browsing, TLS behavior, browser sandbox enforcement and security-update policies have not been independently validated.
3. The custom Mesa libraries were overlaid on distro-managed packages without rebuilding the matching package metadata. Automated updates are not verified.
4. No sound, downloads, file persistence, USB storage, dual-monitor support, system recovery, or full WebGL capability has been validated.
5. The 384 MiB guest successfully boots into RAM but does not yet display a usable browser.
6. Do not publicly redistribute or market this as a certified secure OS without a licensing/source-attribution and security audit.
7. This preview is a **GitHub Actions artifact** (time-limited), not a stable GitHub Release.

## Verification

Read `Puppy50_QEMU_Preview_v62_manifest.json` and `SHA256SUMS` after downloading the artifact. The manifest contains the actual SHA-256 of the same ISO that was KVM-tested. The GitHub workflow refuses to upload a preview ISO if the 1024 MiB interaction proof or the 384 MiB RAM-root boot evidence is missing.

Source: https://github.com/74127418528426leo-del/Test/tree/puppy50-v62-qemu-preview-iso

The complete v62 workflow log and screenshot evidence are attached to the same GitHub Actions run in a separate diagnostics artifact.
