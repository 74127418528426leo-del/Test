# Puppy50 v43 — Original Puppy, RAM-resident, lossless XZ compression

Base: official **BookwormPup64 10.0.12**, ISO SHA-256 **ae65f6e6d70a96f48bdbb291c2426f8a2fd77a73692e149e81a5eecb6fe7509f**.

## Completed research, separately verified

- Original **six** SquashFS images: **779,874,304 bytes**, **743.746 MiB**.
- XZ (1 MiB blocks, x86 filter) lossless repacks: **658,075,648 bytes**, **627.590 MiB**.
- Verified storage reduction: **121,798,656 bytes**, **116.156 MiB**, **15.618%**.
- The v41 audit extracted and individually SHA-256 compared every file and recorded path metadata in all six repacks. None of the original user-visible applications was deliberately removed.
- v42 exact-byte cross-layer duplicates yield an upper bound of only 0.544 MiB of uncompressed repeated content; not an effective compression strategy.
- v40 previously proved the original six SquashFS layers were resident in tmpfs with no disk swap after ejection of the virtual CD at 4 GiB allocated, but had not applied the XZ improvement.

## New v43 release candidate and strict test gate

The GitHub Actions workflow for v43 recompresses **all six** original SquashFS files afresh from the verified upstream ISO, verifies the file contents and metadata by full round-trip extraction, replaces the six ISO SFS payloads while retaining the original bootloaders and RAM-only initrd policy, and verifies the exact embedded compressed bytes. A separate instrumented **QA ISO** boots under a 4 GiB KVM guest, ejects the virtual boot CD, and checks all six actual SquashFS loop backings and original JWM/Xorg/ROX processes after ejection.

The distributable ISO is uploaded **only if** every test passes. If a kernel cannot mount the XZ files or any copied SFS is missing, the Actions job must fail; do not publish or recommend a failed ISO.

The original Puppy filesystem content is not deleted, but binary-level SquashFS bytes and compression performance change. The boot test is not a complete network/audio/USB, graphics, multi-display, or Firefox compatibility regression audit.

[Actual v43 Actions run](https://github.com/74127418528426leo-del/Test/actions/runs/41485045293)

## Why 384 MiB is not yet feasible

**The six XZ files alone occupy 627.59 MiB**, exceeding a 384 MiB system by **243.59 MiB** before allowing any RAM for kernel, RAM disk metadata, Xorg, ROX-Filer, JWM, Firefox, and other applications. This is a measured obstacle **for the original six files and tested compression layout**, not a theorem about every possible alternate distribution.

To keep the original entire ISO data resident, our current complete version must run at a higher RAM allocation. An alternative 384 MiB configuration that loads system files from another device on demand does not satisfy the user's explicit completely RAM-resident requirement.

## Important operating notes

- Unsaved documents and session changes in a RAM-only live boot disappear on power-off; consciously persist work to an external writable device.
- RAM-only boot can be more responsive after loading, but XZ decompression is CPU intensive, and slower older CPUs may experience slower first page accesses. Measure before claiming a speedup.
- Retain the verified v40 image as the fallback until v43 real ISO and hardware tests pass.
