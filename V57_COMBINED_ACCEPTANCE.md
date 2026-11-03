# Puppy50 v57 — combined low-RAM graphics plus real input acceptance

**Date: 2026-11-02 local. This is an experimental KVM-only branch.**

## Proven prior milestones, not confused with current results

- Real v54 custom Mesa 26.1.6 Softpipe-only XZ-compressed root measured **155,840,512 bytes = 148.621094 MiB**. Compared with the matched QEMU-only firmware profile at 202.343750 MiB, 53.722656 MiB was saved. Real KVM at 384, 512, 1024 MiB copied the image to RAM, switched root, and ejected virtual media, but Firefox was only visibly rendered at 1024 MiB. Evidence: https://github.com/74127418528426leo-del/Test/actions/runs/41554290703
- Real v55 KVM input tests accepted QEMU HMP keyboard/mouse commands but did not show the expected webpage color change. Guest input diagnostics showed AT keyboard with only "Handlers=sysrq kbd", no eventX input handler. The hardware-pruning seeds omitted the Linux evdev kernel module, a plausible cause; this is a hypothesis until independently retested. Evidence: https://github.com/74127418528426leo-del/Test/actions/runs/41554754088
- Real v56 restores evdev plus pointer input modules and performs independent JS/click/keyboard framebuffer stage tests. Its outcome must be read before any v56 input success claim.

## v57 combines the two independent branches

- Base: the v54 real LLVM-free Softpipe build, with its successful full ELF DT_NEEDED audit, matching ISO kernel, and XZ root. Retains original Firefox security/TLS controls.
- Changes: retain evdev/mousedev/serio_raw modules and load evdev/psmouse before Xorg. Collect serial input handler listings and Xorg/libinput logs.
- Use a local HTML probe: visible gold indicator on JS, orange background on click, green background on keyboard T.
- Issue actual QEMU HMP pointer click and keyboard events separately, taking distinct P6 framebuffer captures and analyzing transitions. The scripting harness explicitly refuses to infer success from a submitted QEMU command or a browser process ID.
- Real KVM guest RAM allocations are 384 MiB and 1024 MiB. All compressed root bytes, actual boot medium ejection, ISO integrity and frame measurements are recorded.
- The new CI final step **fails closed** if either 1024 MiB positive control or 384 MiB guest lacks RAM-copy/root-switch/CD eject/JS readiness/visible click/visible key response. Artifacts are uploaded with if:always() so failed experiments still preserve evidence.

Workflow: https://github.com/74127418528426leo-del/Test/actions/runs/41557809792

## Explicitly unproven: the real end goal

Even a local offline DOM input pass is NOT proof of real HTTPS, URL navigation, TLS, uploads/downloads, web compatibility, WebGL, audio, system updating or physical Intel i915/dual-monitor performance. This is a QEMU std-VGA firmwareless profile; its CPU-Softpipe graphics stack is not a universal PC replacement. The custom Mesa overlay has mismatched APK packaging metadata and needs proper maintained packages before any distribution.

## Budget and next rational choice

A 384 MiB physical guest has **235.379 MiB nominal** after holding the 148.621 MiB compressed v54 root, *before* the kernel, page cache, Xorg, writable overlay, and browser. In a successful 1 GiB earlier Firefox session, monitored browser PSS reached roughly 240 MiB in one sample and 359 MiB at a measured peak; those process measurements are from a different system configuration and must not be added as a precise v57 prediction. This is strong reason not to assume that trimming Mesa alone will make Firefox work at 384 MiB.

Next after this input test:
1. Collect Firefox and Xorg PSS and logs on the **same combined v57 image** at 384/512/768/1024 MiB; measure actual allocation stalls, kernel userns sandbox and child process health.
2. Build a fully sandboxed WPE WebKit 2.54 system inside a **real KVM RAM-only guest**. The Debian runtime compressed to 187.531 MiB, but its Docker container could not create the bubblewrap user namespace and never loaded the page. The container test was NOT a browser/RAM success. Source: https://github.com/74127418528426leo-del/Test/actions/runs/41553275341
3. For physical Intel 8086:0042, develop an independent Crocus host-compiler/target-runtime build and preserve exact firmware support. Do not deploy this QEMU-only image to the user's PC.

Puppy50 Web is an Alpine-based browser-only research OS inspired by Puppy Linux; it is not a fully compatible implementation of classic Puppy Linux. Changes are only in GitHub Actions and branches, never the user's running Xubuntu.
