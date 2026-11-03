# Puppy50 v54 — Real LLVM-free Mesa integration: verified final results

Experiment completed 2026-11-02 local (2026-11-03 UTC).
Successful GitHub Actions/KVM run:
https://github.com/74127418528426leo-del/Test/actions/runs/41554290703

## Matched compressed filesystem measurements

All baseline and optimized v54 image files were compressed with XZ, identical 1 MiB block settings, on an identical staged QEMU-only Alpine 3.24 Firefox ESR system.

| Experiment | Actual SquashFS bytes | MiB |
|---|---:|---:|
| Earlier full-hardware v48 root | 387,715,072 | 369.753906 |
| Earlier QEMU-only firmware profile v51 | 212,172,800 | 202.343750 |
| **v54: custom LLVM-free Softpipe Mesa + v51 firmware profile** | **155,840,512** | **148.621094** |

**Additional saving in v54 compared with the matched v51 image:** 56,332,288 bytes = **53.722656 MiB**, or 26.55% of the v51 root.

**Total reduction compared with v48:** 231,874,560 bytes = **221.132813 MiB (59.8054%)**.

The 384 MiB guest nominally has 235.379 MiB left after storing the 148.621 MiB compressed root alone; this is NOT a real measure of free RAM. Kernel, initrd, memory-backed writable filesystem, pagecache, Xorg and Firefox all require additional RAM.

## Actual integration evidence

- Source Mesa 26.1.6 Softpipe-only libraries built on Alpine/musl with LLVM disabled. The build's package archive passed SHA-256 verification.
- The replacement Gallium and related shared libraries were extracted into the disposable staged root; the staged ELF DT_NEEDED scan found zero *direct* remaining LLVM users, then the old libLLVM shared library was removed.
- This dynamic-loader scan does **not** prove that no plugins use dlopen or other indirect runtime dependencies.
- Original matching kernel and custom initrd assembled into ISO and embedded ISO assets passed byte-for-byte verification.
- Real QEMU/KVM guest tests using 384, 512 and 1024 MiB physical guest allocation all reached copied compressed root, root switch, virtual CD ejection, Xorg startup marker and Firefox launch request.

## Independently inspected real QEMU framebuffer screenshots

At 145 seconds:
- 384 MiB — black screen with cursor; **Firefox rendering NOT demonstrated**.
- 512 MiB — black screen with cursor; **Firefox rendering NOT demonstrated**.
- 1024 MiB — actual Firefox UI and packaged local HTML visible; the LLVM-free Softpipe build did not prevent basic 1 GiB browser rendering.

Thus, the primary **compressed-root size reduction and 384MiB RAM-root boot goals passed**, while the full **interactive 384MiB browser goal FAILED**. Do not label CI success as a 384MiB usable browser.

## Severe physical-hardware and distribution limitations

This v54 build removes physical-device firmware not needed in QEMU std-VGA and replaces Mesa with CPU Softpipe ONLY. It does not provide Intel Crocus or i915 hardware acceleration. It has not been tested on the Acer integrated graphics, dual displays, Wi-Fi, sound, USB hardware, or modern online websites.

The custom Mesa installation was overlaid on top of distro-managed packages, so Alpine apk metadata does not match the installed libraries. Updates, redistribution, and long-term secure production use require building a proper versioned APK and auditing the full dependency graph. DO NOT deploy this image on the user's physical PC.

No network adapter was configured in QEMU (-nic none), so HTTPS, TLS functionality, downloads, modern webpages and WebGL performance are untested. Input responsiveness was not proven by this v54 run.

## What to do next

1. Restore the kernel evdev handler pruned from the earlier allowlist. v55 serial evidence showed the QEMU keyboard only as "Handlers=sysrq kbd", without the eventX interface Xorg/libinput needs. The isolated v56 input test retains evdev, loads evdev/psmouse before Xorg, and distinguishes script readiness, mouse click, and keyboard DOM events.
2. Keep the v54 148.621MiB filesystem as **QEMU-only measured size reference**, and retest with corrected input event drivers (will enlarge it slightly).
3. Pursue smaller secure browser **working sets**, not merely filesystem bytes: in the previously functional Firefox reference, browser-process PSS reached hundreds of MiB. WPE WebKit headless Debian runtime measured 187.531MiB compressed, but failed nested Docker user-namespace sandbox; it still needs a true KVM guest, actual page load and memory proof.
4. Build real hardware Mesa Crocus + required i915 firmware as an independently validated profile, with no weakened browser sandbox, TLS or site isolation.

**No functional modern browser at 384 MiB was achieved.** The huge measured compressed-root reduction is an independent milestone.
