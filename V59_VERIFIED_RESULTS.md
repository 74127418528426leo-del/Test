# Puppy50 v59 — VERIFIED compact LLVM-free, early-input KVM result

Completed KVM run: https://github.com/74127418528426leo-del/Test/actions/runs/41560016480

## Quantitative root image

The actual XZ-compressed root with both the LLVM-free Softpipe Mesa replacement and early-initrd evdev/psmouse input handling was **155,881,472 bytes = 148.66015625 MiB**, measured in the completed CI. Its matched pre-Mesa replacement root was 212,209,664 bytes, so a full **56,328,192 bytes = 53.71875 MiB** were saved in this direct comparison.

The complete QEMU ISO assembled, and the real guest verified its full compressed-root copy into RAM, root switch and virtual boot media ejection with physical guest allocations of both 384MiB and 1024MiB.

## Real framebuffer acceptance table

| Evidence gate | 384MiB | 1024MiB |
|---|---|---|
| Actual RAM-root copy/switch/CD eject | YES | YES |
| Kernel evdev/psmouse loaded early | YES | YES |
| Kernel eventX input interface exists | YES | YES |
| Firefox renders the local offline page | NO (black except cursor) | YES |
| JavaScript gold script-ready marker | NO | YES |
| Real mouse click orange state change | NO | YES |
| Real keyboard T green state change | NO | YES |

The 1024MiB guest's actual screenshots show the scripted gold → orange → green change in response to QEMU input. The 384MiB guest did not reach even the gold stage. The explicit CI final gate failed on 384MiB as designed, rather than passing on size/boot alone.

## Engineering implications

**The compact graphics stack and early input fix are now compatible with each other.** The full Chromium-like browser working-set barrier remains: Firefox does not render in the tested interval at 384MiB even though the system and kernel input are functioning.

A likely explanation is insufficient browser runtime memory/long-lived allocations, but its root cause and minimum working RAM are NOT yet proven by this comparison alone. Actual browser process PSS in older 1GiB tests was significantly higher than the remaining nominal RAM at 384MiB.

The next independent test is v60, which configures bounded zram swap on a real 384MiB guest while preserving the full diskless requirement:
https://github.com/74127418528426leo-del/Test/actions/runs/41561951905

It uses 256MiB **virtual** zram swap with a 128MiB cap on actual physical compressed-allocator allocations, measures real `mm_stat`, and refuses to claim memory expansion from swap size. If zram is insufficient, prioritize a smaller secure browser runtime (e.g. WPEPlatform 2.54 inside real sandbox-compatible KVM), not disabling Firefox security features.

## Explicit limitations

This image remains experimental. Its QEMU firmwareless profile does not contain all physical Intel i915/adapter firmware; Softpipe is CPU-only, not Crocus hardware acceleration. Its hand-overlaid Mesa libraries also lack coherent Alpine apk package metadata. No HTTPS/DNS/network browsing, WebGL, real hardware input/audio/dual 1080p monitors or security-update system was verified. The user’s existing Xubuntu installation was not modified.
