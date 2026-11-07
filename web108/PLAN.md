# Fast boot architecture experiment

Goal: reduce the time to the Firefox home page on a RAM-booted, browser-focused image while preserving ordinary web access and network firmware. The eight-second cold-boot target is aspirational, not a claim.

Baseline: published v107 ISO SHA-256 cbdf605f87d345ca60d1a0a3cebb20312864c81c2a286c8eacb5acb85769c0c2. Its read-only root and initramfs contain extensive hardware firmware; root is copied fully to RAM before browser startup.

Experiment: derive an explicitly Acer/Intel graphics oriented image. Remove only the amdgpu, radeon and nvidia firmware directories from the post-boot root, keeping Intel graphics, all other firmware, microcode, browser, network packages, security policies and default toram behavior. Explore a second candidate that additionally removes the same graphics-firmware directories from the early initramfs; compare its early-boot and GPU compatibility risk separately. The general-purpose v107 ISO remains available unchanged.

Run an independent lossless experiment on the initramfs: preserve the first three cpio segments byte-for-byte, including AMD and Intel early microcode and early kernel modules, and recompress the final gzip-compressed cpio stream with Zstandard. Verify the uncompressed bytes match exactly and test the real boot path; retain all firmware in this comparison. This is separate from the graphics-profile experiment so performance and compatibility can be attributed correctly.

Verification gates:
1. Pin the v107 image hash; prove targeted paths and ensure all other firmware entries, browser and other root content are preserved, including comparisons after repacking. Do not delete outside the extracted scratch tree or follow symlinks out of it.
2. Preserve boot mode, browser sandbox, certificates, network manager and optional proxy safeguards; do not weaken TLS or bypass network authorization. Check the internal media checksum manifest for every listed file.
3. Build bootable test-only ISO(s), then run matched A-B-B-A v107-versus-candidate QEMU boots on the same machine using the restrictive CPU feature model, 3 GiB RAM and a 30 MiB/s virtual USB cap; retain screenshots, timing, serial and network evidence. Verify a fresh nonce page and public HTTPS after removing the virtual boot device. Report every failure.
4. Test BIOS and UEFI boots plus a 2 GiB configuration on the final candidate; inspect frames, capture hardware-compatibility limitations and verify the published bytes match the tested ISO. Do not claim real Acer performance, physical Wi-Fi, universal graphics compatibility, 384 MiB RAM, or eight-second startup without those actual tests.
5. Only publish an experimental image if the new architecture provides a reproducible improvement and the evidence supports the claims. Clearly disclose removed graphics firmware and keep the general v107 fallback linked.
