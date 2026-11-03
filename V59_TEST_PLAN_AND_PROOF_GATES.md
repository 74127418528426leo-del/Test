# Puppy50 v59 — 148 MiB graphics reference plus early input-driver handoff

**Experimental / real-KVM only. Not a distributable Puppy Linux replacement.**

## Verified foundations

- v54 real compressed XZ SquashFS was 155,840,512 bytes = **148.621 MiB** after replacing the installed Mesa Gallium/LLVM stack with a custom Softpipe-only Mesa build. This is a **QEMU std-VGA, physical-firmware-free** image, not an Intel Crocus build. Real 384 MiB RAM-root boot with CD ejection passed, but Firefox showed a black framebuffer at 384 MiB; at 1024 MiB its UI and local HTML rendered. https://github.com/74127418528426leo-del/Test/actions/runs/41554290703
- v56 real KVM logs showed input handler `Handlers=sysrq kbd` but no `eventX`; after switch_root, `modprobe` could not find evdev, psmouse or mousedev. All three were present in the 107-driver initial RAM disk but omitted from the generated **early direct-insmod seed list**. This demonstrates why simply adding them to the retained-driver allowlist did not fix input.
- v58 independently tests early-initrd insmod of evdev/psmouse/mousedev, and records kernel module state after root switch. https://github.com/74127418528426leo-del/Test/actions/runs/41559290419

## v59 integrated experiment

- Base all other code on v57's compact LLVM-free graphics integration.
- Bring over v58's mandatory dependency-ordered early insmod and initrd fail-closed checks.
- Before Xorg launch, verify persistent loaded modules, `/proc/bus/input/devices` eventX handlers and device nodes.
- Use an actual framebuffer-based 3-stage DOM indicator: JavaScript gold, mouse click orange, keyboard T green.
- KVM tests at 384 MiB and 1024 MiB, both after RAM-only root switching and removal of virtual CD.
- Source and build test: https://github.com/74127418528426leo-del/Test/actions/runs/41560016480

## Acceptance criteria — explicitly separate gates

A. **Boot:** true after verified SFS copy into RAM, new root switch and virtual media eject. Not proof of browser viability.

B. **Graphics:** true after visible local browser UI and JavaScript gold stage. A Firefox PID alone does not pass.

C. **Interaction:** true after the clicked orange transition and keyboard green transition in the real VM screenshot, with command submission logged.

D. **384 MiB:** all A–C in the physically allocated 384 MiB guest. Not satisfied by passing at 1024 MiB.

E. **Production readiness:** DNS, verified HTTPS/TLS, browser sandbox, multiple real websites, downloads/uploads, stable memory pressure and no OOM across repeated cold boots, package/update integrity and target physical Intel GMA/i915 hardware with peripherals must also pass.

The v59 CI workflow explicitly fails rather than reporting success if its offline 384 MiB interaction gates do not pass. That does NOT erase valid build-size or boot-only achievements.

The 148.621 MiB root is an earlier measured reference; v59 adds input modules and its own exact compressed byte count remains to be measured. A secure full browser at 384 MiB is not yet proven.

**No changes were applied to the user's existing Xubuntu installation.**
