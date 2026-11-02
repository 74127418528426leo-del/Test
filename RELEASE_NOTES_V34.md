# Puppy50 v34 — low-memory experimental ISO

**Source:** official BookwormPup64 10.0.12 with SHA-256 `ae65f6e6d70a96f48bdbb291c2426f8a2fd77a73692e149e81a5eecb6fe7509f`. Original application and desktop SFS content is retained.

**Modifications:**
1. A fail-closed single conditional in initrd defaults to disk-backed SFS loading (previously proven v22), while explicit `pfix=copy` remains supported.
2. An additive `ydrv_dpupbw64_10.0.12.sfs` overlays the system with a verified prebuilt `/var/lib/plocate/plocate.db` (from main SFS, not later user files).
3. The automatic plocate update's `.desktop` entry starts a small wrapper that waits **600 seconds**, then runs the original `plocate-update-db` at idle I/O and low CPU priority. The original executable, menu and applications are not removed.
4. The release ISO intentionally has **no debug/probe rc.local that automatically launches Firefox**. Diagnostic behavior is excluded from the deliverable.

**Original search behavior caveat:** The initial index might not include programs on secondary SFS layers or files added after ISO creation. Search results are potentially stale for the first ten minutes; the later background update is intended to refresh them. This is an explicit behavior change and not yet an independently certified no-regression optimization. No permanent steady-state RAM savings are claimed from delaying indexing.

**Build & tests:** [real GitHub Actions run](https://github.com/74127418528426leo-del/Test/actions/runs/41455782272) recreates the ISO from a verified source, verifies the replacement initrd, refuses diagnostic browser auto-start scripts, and attempts two real KVM CD boots (256/512 MiB) before uploading the complete ISO artifact and matching SHA-256 checksum. **Screenshots alone do not establish complete application compatibility.** When published, the separate GitHub Actions artifact will contain the bootable .iso.

**Important:** This is not a 50 MB ISO or 50 MB physical RAM OS. It is an experimental live-boot build; do not install over working drives. Normal Xubuntu, target Intel i915, UEFI, two monitor, sound and networking compatibility still require physical smoke tests.
