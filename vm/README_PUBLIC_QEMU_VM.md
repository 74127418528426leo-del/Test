# Puppy50 Public QEMU Test Virtual Machine (experimental)

This is the **actual kind of virtual machine used in the Puppy50 KVM tests**: QEMU x86_64 with a read-only live boot ISO, standard VGA, 2 virtual CPUs, and 1024 MiB of allocated guest RAM. The VM has **no attached writable disk and no network adapter**. The entire operating system is copied from the boot ISO into guest RAM; the virtual optical medium can then be ejected.

There is **no persistent QCOW2/OVA image or continuously running hosted VM**. The portable VM is the tested live ISO plus reproducible launch scripts/configuration. It is not a webpage that can run QEMU in your browser.

## Public release download

The signed-off public asset is published **only after automated real KVM tests pass**:

https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-qemu-v63

If this URL does not yet show downloadable assets, the new ISO build has not finished its acceptance tests or a release-publication step failed. Do not mistake this page for a confirmed binary download.

## What's in the release bundle

- `Puppy50_Web_QEMU_Preview_v62.iso` — a real bootable experimental CD image.
- `Puppy50_QEMU_VM_v63_bundle.zip` — the ISO together with the Linux and Windows launch scripts, VM profile, checksums, and source commit manifest.
- `SHA256SUMS` and the machine-readable release manifest.
- `launch_linux.sh`, `launch_windows.ps1`, and `QEMU_VM_PROFILE.json`.

## Launch on Linux (tested QEMU hardware profile)

Install QEMU (`sudo apt-get install qemu-system-x86` on Ubuntu/Xubuntu). Extract the **VM bundle ZIP**, then run:

```bash
bash launch_linux.sh
```

The script verifies the downloaded ISO checksum and launches a read-only optical boot in QEMU with `-m 1024 -smp 2 -vga std -nic none`. If `/dev/kvm` isn't accessible, it falls back to much slower TCG emulation. This VM can be shut down without modifying a host disk.

To reproduce the low-memory RAM-only boot (but **not a working web browser**) use:

```bash
PUPPY50_RAM_MIB=384 bash launch_linux.sh
```

## What the tests really prove

**1 GiB guest:** actual offline Firefox local-page rendering, JavaScript execution and two real input-device events (mouse-click → orange page and keyboard T → green page), after RAM-root switch and boot-media eject.

**384 MiB guest:** the compressed root copies into RAM, switches root, and the boot medium can be ejected. Firefox still does **not** render the page and this is NOT a usable 384 MiB browser.

**Not proven:** secure public internet HTTPS browsing, DNS, updates, network attachment, sound, webcams, USB passthrough, real Intel i915/Crocus drivers or full physical PC compatibility. This is a narrowly targeted VM research preview, **not a secure production OS**. Network is intentionally disconnected.

## Source and provenance

The code and full build workflow are public:
https://github.com/74127418528426leo-del/Test/tree/puppy50-v63-public-qemu-vm

The ISO builder uses a verified download of the official Puppy BookwormPup 10.0.12 media for its bootloader assets, replaces the root filesystem with an Alpine Linux Firefox stack, and uses an independently matched Alpine Linux kernel and initrd. The source project is inspired by Puppy Linux but is **not** an official Puppy release.

The binary is not cryptographically signed by a recognized distribution authority. SHA-256 confirms file integrity against the published manifest, not publisher identity. Upstream packages retain their own licenses; do not claim security certification or official Puppy sponsorship.

No part of this public VM package has been installed onto the user's physical Xubuntu system.
