# Puppy50 Web — Public QEMU VM Preview v63 (EXPERIMENTAL)

This public pre-release contains the **same bootable ISO successfully tested** in GitHub Actions run [41565605787](https://github.com/74127418528426leo-del/Test/actions/runs/41565605787), packaged with a reproducible QEMU VM profile and offline launch scripts. There is no permanent QCOW2/OVA disk: the real VM boots from the live ISO and copies its operating system into physical guest RAM.

## Downloads

- **Puppy50_QEMU_VM_v63_bundle.zip** — recommended: ISO, checksum, Linux/Windows launch scripts and VM profile in a single file.
- **Puppy50_Web_QEMU_Preview_v62.iso** — standalone read-only bootable ISO.
- **SHA256SUMS** — checksums for the ISO.
- **README_PUBLIC_VM.md** — operating instructions and limitations.
- **Puppy50_QEMU_Preview_v62_manifest.json** — machine-readable ISO test provenance.

## Real KVM verification

- **384 MiB allocated guest RAM:** root copied into RAM, root switched, virtual CD ejected; **Firefox did not render**. This is **NOT** a functional 384 MiB browser.
- **1024 MiB allocated guest RAM:** Firefox displayed the bundled offline local page, ran JavaScript, and reacted visibly to a QEMU-generated mouse click and keyboard T input after boot-media removal.
- **Hardware profile:** x86_64 PC, IDE read-only optical drive, 2 vCPUs, standard VGA, **no writable hard disk, no network adapter**.
- **Security / hardware:** not certified for secure internet browsing or use on physical computers. Intel i915/Crocus, Wi-Fi, sound and security updates are not validated; the Mesa overlay is experimental.

## Boot locally (Linux / Xubuntu)

Download and extract the bundle. Run:

```bash
bash launch_linux.sh
```

The launcher checks the ISO against its SHA-256 and uses KVM if accessible, otherwise slower TCG. The VM is ephemeral and remains offline.

**This is a research prototype, not an official Puppy Linux distribution or secure production OS.** Sources, upstream provenance and public build/test evidence: [Puppy50 v63 branch](https://github.com/74127418528426leo-del/Test/tree/puppy50-v63-public-qemu-vm).

Source of original Puppy boot media: BookwormPup64 10.0.12; restaged Alpine kernel/root and scripts are independently built within the public source workflow. Upstream packages carry their own licenses.
