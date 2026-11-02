# Puppy50 Web v51: QEMU-only firmware ablation, safely isolated

2026-11-02. This branch intentionally studies only QEMU standard-VGA hardware. It is NOT a universal or real-Acer boot image.

## Why this experiment exists
The measured v49 root SquashFS with secure Firefox ESR, Xorg and Openbox was 336,138,240 bytes (320.5664 MiB). The real v50 identical-image tests at 512, 768 and 1024 MiB all booted from RAM after ejecting the virtual CD. The 512 and 768 MiB screenshots remained black except the pointer; Firefox rendered at 1024 MiB. The number of observed Firefox-related processes grew from 1 to 4 to 9. No kernel OOM kills were recorded, but failed userspace allocations were not ruled out.

Source: https://github.com/74127418528426leo-del/Test/actions/runs/41544771276

## Falsifiable hypothesis
QEMU standard VGA, virtual IDE and mouse/keyboard do not require the retained physical Intel/i915/Wi-Fi/Bluetooth firmware. The v49 image carried roughly 123 MB uncompressed retained physical firmware. Deleting only these staged image firmware files *after* install, while preserving Firefox/Mesa/kernel modules, should reduce the compressed root and help establish whether 384 MiB can COPY and SWITCH to the RAM root.

A claimed 384 MiB functional browser still requires independently verified visual rendering and interaction; copy alone does not count.

## Controls
1. Build the exact same Firefox+Openbox+Xorg dependency closure as v49.
2. Stage duplicate /boot files externally while preserving the verified matching kernel.
3. Compress the complete unmodified bootless root with the exact v49 XZ options.
4. Remove only staged firmware regular files/symlinks using a path-restricted program, with a QEMU-only capability declaration.
5. Recompress using identical XZ options and measure byte difference from the actual baseline. Do not infer compressed savings from raw firmware bytes.
6. Confirm Firefox libxul, Mesa Gallium and LLVM binary files remain present.
7. Build verified bootable ISO; run real KVM at 384, 512, 1024 MiB; retain screenshots and QEMU optical eject proof.

## Non-goals and risks
- Does NOT claim compatibility with user physical Intel 8086:0042 machine, physical USB devices, Wi-Fi, Bluetooth or GPU acceleration.
- This image is inappropriate for a general-purpose hardware boot; firmware often IS needed on real PCs.
- QEMU VGA uses a different graphics path from Intel Crocus. Its success or failure cannot stand in for WebGL compatibility on real hardware.
- No disk-based swap or security bypass has been added; browser isolation/TLS must be retained.
- v50's absence of an OOM kill does NOT conclusively identify why 512/768 MiB Firefox windows did not appear.

## Future priority after measurement
- The high-value diagnostic remains Firefox initialization: determine stuck main-process wait channel, resource allocation failure, content-process spawning, and actual X11 mapped windows.
- If the compressed root plus kernel leaves no margin for Firefox at 384 MiB, build a hardware-targeted Mesa variant and/or a smaller secure web runtime; never claim this as completed before functional tests.
- Preserve v49 universal-capability baseline and v50 completed evidence.

Workflow: https://github.com/74127418528426leo-del/Test/actions/runs/41546583445
