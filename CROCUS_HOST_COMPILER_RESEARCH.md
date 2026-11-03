# Puppy50 Web — Physical Intel Crocus without target LLVM: research hypothesis

Date: 2026-11-02. This is a **research hypothesis**, NOT a compiled or GPU-tested result.

The current QEMU-specific v53 Softpipe build has demonstrably compiled Mesa 26.1.6 without LLVM and its installed shared libraries had no direct libLLVM dynamic links. This saves source dependencies but does NOT provide hardware acceleration for the user's older Intel PCI 8086:0042 GPU.

## Concrete upstream insight

Mesa 26.x Crocus requires a shader precompilation tool during the **build**, and the initial naive compile with -Dgallium-drivers=crocus,softpipe -Dllvm=disabled produced:
  ERROR: Feature llvm cannot be disabled: CLC requires LLVM.

This does not logically prove a Crocus **runtime** must link LLVM.

Buildroot's September 2026 upstream patches identify the distinction between host-side precompilers and target LLVM:
https://lore-kernel.gnuweeb.org/buildroot/643ab362-2687-448a-b4e8-3ab9d539bf4f%40smile.fr/T/

Mesa 26.x Meson logic sets with_clc=false for the target build if -Dmesa-clc=system and Rusticl is not enabled, and locates externally supplied native host binaries mesa_clc and vtn_bindgen2. The precomp-compiler option may also need system host tools, depending on Crocus build products:
https://sources.debian.org/src/mesa/26.1.2-1~bpo13+1/meson.build
https://android.googlesource.com/platform/external/mesa3d/+/refs/tags/upstream-mesa-26.1.2/meson.options

## Falsifiable future two-stage build

1. In a BUILD-HOST ONLY stage, compile and install the relevant Mesa host shader-generation tools using LLVM and, where necessary, Clang. This builder may be large; its LLVM files are NOT copied to the operating-system image.
2. In a fresh Alpine/musl TARGET stage, build Mesa 26.1.x with only crocus,softpipe, using -Dmesa-clc=system, -Dprecomp-compiler=system, -Dllvm=disabled, -Dgallium-rusticl=false and no Vulkan drivers, pointing PATH to the host tools. If Meson or compilation requires another LLVM target dependency, record the failure rather than bypassing it.
3. Install the target libraries into a disposable staging root. Scan all ELF DT_NEEDED edges, inspect code generation outputs, then verify running driver actually initializes PCI 8086:0042 in real hardware.
4. Measure true compressed SquashFS savings and loaded process PSS. Test WebGL and browser rendering, keyboard, mouse, dual 1080p display stability and GPU resets on the actual old Intel hardware. The QEMU standard VGA GPU cannot validate i915/Crocus.
5. Package the resulting Mesa/firmware as an updateable APK with all ABI dependencies, runtime package metadata and security updates. Do not distribute manual library overlays as production systems.

## Why this is worth testing
The build compiler can use much more RAM and LLVM without violating the 384MiB **runtime** budget. If the target runtime can omit LLVM, it could recover tens of compressed MiB while retaining accelerated graphics. This separation between compile-time and run-time dependencies is an architectural breakthrough only if the actual hardware functionality is independently verified.

Counterexample: if runtime Crocus really links LLVM or requires impossible GPU capabilities, this path is rejected; retain the original full-driver distribution as the compatibility edition.

Never compromise browser sandbox, TLS certificate checks or process isolation in order to satisfy the RAM target.
