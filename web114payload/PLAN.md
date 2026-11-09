# v114 early-payload measurements

Baseline: exact published v113, SHA-256 `4e6dc9b9d1f8f416b47ea046ffcfc5f1c6a7a732dc9ac0e67ff49bd53d271ea1`. Measure whether moving the early udev hardware database and selected server-network firmware to the unchanged late root helps the real interactive browser start or saves memory. Test the firmware groups, the udev database, and both together separately. This is a local-media experiment, not evidence of network-root/PXE boot or physical keyboard, Wi-Fi, storage, or other hardware compatibility.

1. Validate all proposed file removals against byte-identical late-root copies before removing anything; retain symlinks, microcode, kernel, full root, boot menus, and the complete fallback initramfs. Only the selected initramfs copies may change.
2. Rebuild a test ISO with accurate media checksums and byte-check the unchanged core files and full fallback. Exercise Firefox, early local JavaScript, 3 GiB BIOS/USB, staged RAM copy, removed virtual USB, fresh HTTP, and HTTPS.
3. Compare each variant with v113 in A–B–B–A order on the same QEMU/KVM host with a 30 MiB/s virtual USB read cap, and use 0.2-second polling plus capture overhead. Reject changes whose gain is not repeatable or which risk unverified hardware behavior. An independent repeat and broader validation are needed before any release.
4. Do not claim physical Acer timing, 8 s, 384 MiB Firefox, all-network compatibility or RAM readiness without the matching evidence. Existing v113 remains untouched.
