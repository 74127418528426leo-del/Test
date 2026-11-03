# Puppy50 v76 — Restore an update-coherent STOCK Mesa control from the exact v70 ISO

## Original evidence

Source: https://github.com/74127418528426leo-del/Test/actions/runs/41668355349

The exact public v70 compressed RAM-root has 247 Alpine APK records, 8 Mesa ELF digest mismatches and 5 unowned .so aliases. Custom software-rendering libraries were previously overlaid **outside** the package manager. This does not establish malicious behavior, but invalidates claims that binary package updates are coherent.

## Actual controlled experiment

1. Download and verify original v70 ISO SHA-256 `26a9b339c6de87a1c891512742d608a910f4bbfce66fe26a96159297c98f8e2e`.
2. Extract the compressed root into a disposable `output/rootfs` on GitHub Actions. Never alter the user's Xubuntu or public v70 download.
3. Run Alpine `apk fix --reinstall` on Mesa's actual installed packages inside an Alpine 3.24 container targeting that staged root. This is a **stock distribution control**, NOT a claim that the original optimized Mesa was packaged or signed.
4. Clean only the five known unowned development symlink aliases, fail closed on unexpected files or attempts to leave the staging root.
5. Independently audit actual installed shared library digests and ownership. Require zero recorded mismatches and zero unowned aliases. Do **not** edit `lib/apk/db/installed` directly to hide differences.
6. Recompress into a **separate** ISO. Require kernel and initial RAM disk to be byte-for-byte identical to v70.
7. Compare actual compressed ISO bytes, then run real KVM at 1024 MiB with Firefox, guest DHCP/DNS, trusted HTTPS and Wikipedia interaction.
8. Archive all build and KVM evidence. **Do not publicly release the control ISO as safe until browser rendering and security follow-up checks pass.**

Workflow: https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-v76-stock-mesa-control.yml

## Decision rule

If stock Mesa passes browsing but grows noticeably, retain it as the maintainable baseline and pursue performance from pinned source-built APK packages using documented Alpine `APKBUILD` and `abuild`, with verifiable provenance. If it fails, preserve both complete logs and the original working v70, then isolate which package or dependency caused the failure.

Even a zero-mismatch package audit does not certify up-to-date browser CVEs, secure sandboxing, all-network compatibility, physical GPU support, or a functional browser at 384 MiB.