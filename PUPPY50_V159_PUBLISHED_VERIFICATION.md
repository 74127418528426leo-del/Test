# Puppy50 v159 — published & independently tested 2026-11-14

## Exact immutable release files

[GitHub prerelease](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v159-verified-browser-httpsafe-experimental)

- ISO: `Puppy50_v159_WebRender_Nice10_EXPERIMENTAL.iso`, **906,297,344 bytes**, SHA-256 `ffe1792d02b3906bbcf8b52b9a5e203916c7d1e063e159e36478805653d622cd`.
- ZIP: `Puppy50_v159_WebRender_Nice10_EXPERIMENTAL.zip`, **906,300,017 bytes**, SHA-256 `a3f38cc14de77b11541e86daf6ed8f6f7059b49bacb4a485e18f2d570e44f013`.
- [Complete successful GitHub Actions release verification](https://github.com/74127418528426leo-del/Test/actions/runs/43602011946).

The exact SHA-256 identified shipping ISO **passed four genuinely independent NEW cold-boot QEMU launches**, two BIOS and two UEFI, with a host-monotonic timer started before each QEMU process. This is **NOT** an actual physical Acer power-on measurement or a genuine 5-second system.

| Firmware trial | Actual first rendered Firefox home frame |
| :-- | --: |
| BIOS cold boot 1 | **8.89 s** |
| BIOS cold boot 2 | **8.41 s** |
| UEFI cold boot 1 | **13.32 s** |
| UEFI cold boot 2 | **13.10 s** |

Each of four VMs independently verified **complete, checksum-validated original compressed-root migration into RAM** BEFORE virtual boot media ejection and independently navigated the original Firefox ESR to the nonce-authenticated host web fixture, which recorded an actual **HTTP 200** after eject. The guest Firefox remains unprivileged with its original sandbox, same Firefox ESR and same Zstd root and full-RAM rescue image.

### What changed compared with v158?

**The shipping OS startup code is unchanged:** the v159 build uses the same v151 experimental OS code as v158 (recreated from original cryptographically pinned sources). The substantial engineering change is the **host-controlled test harness**, not a claim of newly faster Linux/Firefox. v158's release had correctly been blocked because a single QMP Ctrl+L + typed URL attempt often did not generate an actual Firefox HTTP request; its metadata `input_sent_after_eject=true` proved only that keyboard events were sent, not that the browser used the network.

The v159 auditor measures the real host web fixture's **HTTP 200 receipts, per VM**, immediately after RAM-eject, then repeats QMP keyboard navigation within the **same running guest** up to three times only if no receipt appears. It never simulates a GET from the host, never restarts/resumes a VM to fake cold startup, and fails the entire release if even one real browser HTTP 200 is missing. The initial first-frame measurements are unchanged by this later validation process.

**Release and hardware caveats:** no verified <5 second Firefox on BIOS or UEFI (including modern KVM), no real USB power-on or firmware POST timing, no physical Acer i3-540 + i915 or Wi-Fi or dual monitor certification, and no 384MiB full RAM with a compressed root > 664MiB alone. Keep a **separate original v115 recovery USB**: the accelerated BIOS Shift-key recovery menu was not independently verified. Never disconnect boot media until the verified GREEN **RAM READY** signal.

This is an experimental Debian Live Firefox OS, **not the official Puppy Linux distribution**.
