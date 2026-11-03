# Puppy50 Web v54 — integration experiment and strict acceptance gates

## Objective
Integrate the **already successfully compiled** Mesa 26.1.6 Softpipe-only LLVM-free graphics stack into a real RAM-copied, QEMU-only browser OS. Compare actual SquashFS compressed size and KVM screenshots against the matched v51 firmwareless baseline. No physical Xubuntu machine is modified.

Preceding verified tests:
- v51 QEMU standard VGA firmware-free root: 212,172,800 bytes (202.34375 MiB), real 384MiB RAM-copy/root-switch/media-ejection PASS, 384MiB browser rendering FAIL; https://github.com/74127418528426leo-del/Test/actions/runs/41546583445
- v52 real 512/1024 MiB Firefox process-state measurements: no kernel OOM kills, main Firefox alive on 512MiB, SquashFS decompression waits also present in successful 1024MiB rendering; https://github.com/74127418528426leo-del/Test/actions/runs/41548426953
- v53 complete Mesa 26.1.6 source compilation on Alpine 3.24/musl: Softpipe-only with LLVM disabled, dynamic ELF audit success, **no GPU runtime test**; https://github.com/74127418528426leo-del/Test/actions/runs/41549441016

## v54 method
1. Rebuild identical Alpine Firefox/Xorg/Openbox+kernel closure; prune the same QEMU-only firmware, keep all browser security features intact.
2. Compress baseline root using XZ 1 MiB blocks and record exact file size.
3. Independently compile Mesa Softpipe (not Crocus, nor LLVMpipe) with LLVM disabled and verify the produced archive checksum.
4. Extract binaries ONLY into a disposable staged /output/rootfs, check all staged ELF dynamic libraries for direct libLLVM dependencies, and remove old LLVM files only if no direct consumer remains.
5. Measure matched final compressed root with exactly the same XZ options. A smaller image is a *size* result, not functional proof.
6. Rebuild ISO with separately preserved matching boot kernel and initrd; test real QEMU/KVM at 384,512,1024 MiB and inspect framebuffer evidence.

## What remains explicitly unproven
- **No real Crocus/i915 acceleration**. This experimental stack uses CPU Softpipe only.
- A zero direct DT_NEEDED link to LLVM does not exclude dlopen/plugin loading or hidden runtime assumptions.
- Custom Mesa overlays distro-installed Mesa: APK package metadata is inconsistent until a proper maintained replacement APK is built. This image must not be distributed as secure production OS.
- No modern HTTPS browsing proof, no physical dual-monitor USB, sound, Wi-Fi or WebGL acceptance evidence.
- Firefox may remain too RAM-heavy after driver reduction. 384MiB will be declared PASS only when the actual window renders and responds to input, secure browsing succeeds, RAM-root is verified, boot media is removed, and repeatability/stability is measured.

## High-value design conclusion
The compressed SFS occupies **guest RAM** even while its decompressed pages and Firefox process memory are active. That cost stacks in practice with browser PSS, graphics, kernel and working buffers. v51's 202.344MiB SFS leaves 181.656MiB nominal at 384MiB before any other required allocations. v52's successful 1GiB Firefox reference showed hundreds of MiB of process PSS across browser subprocesses. Further filesystem savings are necessary but may not be sufficient.

Once the smaller software graphics image works, the best next independent direction is WPE WebKit >=2.54 with its modern WPEPlatform headless and DRM/KMS support. Build a *complete secure minimal browser shell*, measure source closure, WebKit subprocess PSS, sandbox and SSL integrity, and validate actual page interaction. Never confuse legacy Cog with a full modern browser.

Workflow: https://github.com/74127418528426leo-del/Test/actions/runs/41551178153
