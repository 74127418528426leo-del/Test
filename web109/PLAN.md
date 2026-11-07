# Staged RAM boot prototype

Goal: make the existing Firefox and networking environment available before copying the full compressed root to RAM, while retaining a safe path to USB removal after the copy completes. Eight seconds is aspirational and not claimed. The previously published v108 remains the fallback.

The separate v108 research showed a media-attached demand boot reaches the first browser frame earlier in a virtual test, and a separate tiny fixture showed that a read-only device-mapper target can be redirected to an identical RAM-backed loop. Neither result proves the combination on the operating system. This prototype joins those ideas only for testing.

Prototype: add isolated device-mapper tools to the initramfs, wrap the single live system image in a read-only linear mapping, leave all firmware and the original system SquashFS unchanged, and start Firefox without the initial `toram` copy. A nonblocking service later copies the filesystem into tmpfs, verifies its size and SHA-256 against the ISO manifest, switches the mapper, checks the new loop's RAM backing, detaches the old loop, and only then emits a readiness marker. All commands involved in a suspended-root switch must run from tmpfs; failures must not emit readiness or advise removing the USB.

Verification gates before a user-facing image:
1. Preserve the early microcode archive and the existing SquashFS; verify all ISO checksums and confirm shell and helper tests.
2. Boot the prototype in QEMU with capped USB, wait for an explicit migration-ready marker, remove virtual boot media, and verify a fresh local page and a public HTTPS page in Firefox. Inspect the screenshots and root backing diagnostics. Compare first Firefox time to v108 on a matched host with repeated trials.
3. Inject checksum mismatch, copy failure and insufficient memory; ensure no early ready marker and no unsafe ejection. Exercise concurrent I/O and recovery paths, and test BIOS and UEFI, offline startup and network restoration, and at least 2 GiB virtual memory. Never infer real Acer performance or wireless support from a virtual machine.
4. Add a clear, visible user indication that the USB must remain connected until RAM migration succeeds. Prevent confused removal on failed or incomplete migration. Verify how ephemeral browser data behaves.
5. Review the dependencies included in the initramfs, their licenses and update compatibility, and inspect potential device-mapper suspend or resume races. Preserve hardware firmware and Firefox TLS. Do not use LOOP_CHANGE_FD, which has documented kernel problems.
6. Publish a separate explicitly experimental image only after the exact image and its UI pass the tests. If the design fails any gate, retain the working v108 release and accurately report the failure.
