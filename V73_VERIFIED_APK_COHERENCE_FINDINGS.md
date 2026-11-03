# Puppy50 v73 — Exact published v70 ISO package-integrity findings

Verified GitHub Actions run: https://github.com/74127418528426leo-del/Test/actions/runs/41668355349

Audited SHA-256: `26a9b339c6de87a1c891512742d608a910f4bbfce66fe26a96159297c98f8e2e`
Public source image: https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-qemu-normal-v70

## Verified quantitative observations

- The actual Alpine APK installed database **does exist**: `lib/apk/db/installed`.
- It records **247 installed packages** including Firefox ESR **140.12.0-r0**.
- The image has **629 shared-library paths** in the scanned tree.
- Of package-owned regular shared library files, **340 legacy SHA-1 digests were checked** and **8 did not match** the APK installed-file records.
- These 8 discrepancies are *all in the custom Mesa graphics library family*:
  `usr/lib/libgbm.so.1.0.0`,
  `usr/lib/libEGL.so.1.0.0`,
  `usr/lib/libGLESv2.so.2.0.0`,
  `usr/lib/libGL.so.1.2.0`,
  `usr/lib/libgallium-26.1.6.so`,
  `usr/lib/libGLESv1_CM.so.1.1.0`,
  `usr/lib/gbm/dri_gbm.so`,
  `usr/lib/dri/libdril_dri.so`.
- **Five unowned paths** are the unversioned Mesa library aliases
  `usr/lib/libgbm.so`, `usr/lib/libEGL.so`, `usr/lib/libGLESv1_CM.so`, `usr/lib/libGL.so`, `usr/lib/libGLESv2.so`. These may be symlink aliases rather than independent ELF binaries; the audit does **not** assert otherwise.
- The CA trust bundle exists; this does not certify browser TLS policies or the operating system's security.
- The observed on-disk files differ from those recorded by the package database; `apk upgrade` or reinstalling original Mesa could overwrite optimized graphics files or yield inconsistent behavior.

## Recommended next corrective build

**Do not silently change package metadata to mark arbitrary files as official.**

1. Preserve the exact v70 ISO and reference hashes.
2. Rebuild the custom LLVM-free Mesa changes from controlled, documented source against a pinned Alpine package build environment.
3. Package the changes as consistently versioned, signed, installable `.apk` packages with explicit dependencies and conflicts; do not overlay raw libraries.
4. Install them through Alpine APK on a disposable staging root and verify `apk audit` and library ownership against the resulting database.
5. Run real KVM smoke tests: RAM-root and media eject; Firefox homepage; actual mouse/keyboard; at least two public HTTPS sites; host Wi-Fi/Ethernet NAT and CA validation.
6. Record the size/speed tradeoff against the 148.66 MiB custom root. If a supported package-based image is larger, do **not** call that a regression when it meaningfully improves maintainability and user safety.
7. Audit the Firefox sandbox, CVEs, release updates and package provenance independently before allowing confidential logins.

This audit does NOT establish that the eight mismatches are malicious or exploited. They are expected given prior manual graphics-library replacement, but still need remediation for production maintenance.

## Explicit non-achievements

No browser sandbox penetration test, complete CVE assessment, system image signature, physical Intel driver verification or all-network compatibility certification has been done. The current public v70 image remains **experimental**, even though real Firefox browsing over QEMU NAT has been demonstrated.
