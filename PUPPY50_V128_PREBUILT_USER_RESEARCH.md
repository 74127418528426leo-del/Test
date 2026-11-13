# Puppy50 v128 — offline precreated nonroot Live user before Firefox

**Research-only. Under-three-second cold Firefox is NOT demonstrated; no v128 release is authorized.**

## Isolated experiment

The [controlled v128 GitHub workflow](https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-v128-prebuilt-user-ab.yml) builds two BIOS/UEFI-bootable disposable test ISOs:

- Baseline: the **same validated v126 early Xorg initrd with its live user created during the guest's early boot**, identical released v117 kernel/root and full-RAM rescue initrd.
- Candidate: **identical early authenticated Xorg initrd, identical kernel, identical full-RAM rescue initrd**; only the unchanged Debian Live SquashFS root is extracted and repacked with its ordinary unprivileged `user` account and home skeleton created in advance. The original v126 initrd checks still run but detect the user already present, skipping its costly runtime `chroot useradd` call.

Both exact image checksums and all 293 media manifest entries are checked, with byte-exact recovery and early-X11 initrd comparisons. The four matched QEMU/KVM cold boots measure **real Firefox framebuffer first page from immediately before VM process launch**, then require verified complete compressed root copy to RAM, safe virtual boot-media eject and real HTTP 200 requests after removal. A failed browser, absent RAM READY or no network response must disqualify the candidate.

This is a controlled *hypothesis*, not a proven speed gain until the four-run result is collected. It changes only live-account provisioning; it does not attempt to weaken Firefox sandbox, alter GPU drivers, mask nonessential security services, pre-resume a VM or replace a browser with a static screenshot.

Prior matched v127 evidence: [v127 run](https://github.com/74127418528426leo-del/Test/actions/runs/43505491538) showed 8.830s v126 baseline versus 8.515s parallel Firefox, both far above three seconds. [v126 run](https://github.com/74127418528426leo-del/Test/actions/runs/43504728219) first proved the authenticated early Xorg survived switch-root and rendered Firefox with safe post-eject network requests.

**Physical Acer i3-540, i915, USB2, real Wi-Fi, actual power-on POST, and entire Firefox system at 384MiB RAM remain untested or unmet.** Keep released [v122 experimental ISO/ZIP](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v122-direct-fast-codec-experimental) and separately [v115 recovery ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v114-fast-verification-experimental).
