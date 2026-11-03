# Puppy50 v73 — Verified APK package-coherency audit of the public v70 ISO

**Actual independent source:** https://github.com/74127418528426leo-del/Test/actions/runs/41668355349

**Binary audited:** public Puppy50 Web v70 ISO, SHA-256 `26a9b339c6de87a1c891512742d608a910f4bbfce66fe26a96159297c98f8e2e`. No change to this ISO or user's host.

## Exact observed results

| Inventory | Result |
|---|---:|
| Alpine APK package records in real root | 247 |
| Firefox package version registered | `140.12.0-r0` |
| Mesa package version registered | `26.1.6-r0` |
| Shared-library files scanned | 629 |
| Shared libraries without APK file ownership | **5** |
| Owned shared-library SHA-1 digests checked | 340 |
| Digest mismatches against APK installed records | **8** |
| Valid CA bundle present | Yes (178,791 bytes) |
| Production update security validated | **No** |

The 8 mismatches occur in the deliberately overlaid custom Mesa implementation: `libgbm.so.1.0.0`, `libEGL.so.1.0.0`, `libGLESv2.so.2.0.0`, `libGL.so.1.2.0`, `libgallium-26.1.6.so`, `libGLESv1_CM.so.1.1.0`, `dri_gbm.so`, and `libdril_dri.so`. Five shared-library symlinks named `libgbm.so`, `libEGL.so`, `libGLESv1_CM.so`, `libGL.so`, and `libGLESv2.so` lack an APK owner.

**Interpretation:** the updated libraries may be functional, and the working Firefox/KVM tests confirm an offline and limited public-site baseline. But the APK database still records the original upstream package payload checksums. The system's file inventory therefore no longer accurately represents all installed bytes. **Do not respond by silently editing the APK installed database or bypassing integrity checks.** A real fix rebuilds the changed graphics components as coherent reproducible APK packages (with source, patches, local package versioning, manifests, signatures and reproducible tests), or uses an entirely stock package-managed graphics stack after performance comparison.

## Safest next engineering experiment

1. Build a reproducible stock-Mesa control image and a tracked custom-Softpipe variant from the same exact Alpine package snapshot. Preserve the working v70 ISO separately.
2. Compare actual guest boot, Firefox rendering, page interaction, memory PSS, WebGL compatibility, ISO bytes, and package records, with matching KVM hardware and cold boots.
3. Require ZERO owned-package digest mismatches and a documented source-to-binary provenance for any new release, plus consistent browser/package security patch tracking.
4. Add a browser sandbox and network boundary audit; zero APK digest mismatches alone do not certify a secure OS.

**Scope warning:** APK installed-file Q1/SHA-1 entries are only legacy package-coherency metadata. These checks do NOT establish cryptographic publisher identity, timely CVE patching, browser process isolation, or firmware safety. The system remains an experimental VM and is not suitable for sensitive account logins.

Raw result is available in the workflow's `Puppy50_v73_real_v70_ISO_package_coherence_audit` artifact.
