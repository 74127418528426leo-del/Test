# Puppy50 v56 — Restore missing Linux event input, then separate browser stages

Real v55 KVM run (actual keyboard+mouse commands and guest serial):
https://github.com/74127418528426leo-del/Test/actions/runs/41554754088

## Diagnosed omission in previous hardware-pruning policy
The guest at both 384 and 1024 MiB reported an AT translated Set 2 keyboard in /proc/bus/input/devices, but its handler line was only:
  H: Handlers=sysrq kbd

No `event0`, `event1` or other Linux evdev input handler appeared in that device report. The Xorg input log excerpts also lacked normal libinput device attachment, even though Firefox visibly rendered at 1024 MiB.

Inspection of `web45/prune_hardware_v45.py` confirmed its DRIVER_SEEDS list originally included `i8042`, `atkbd` and `psmouse` but omitted `evdev`, which is the kernel input-event character driver normally used by Xorg/libinput. This is an actionable and highly plausible input-layer failure, not yet a demonstrated complete cause.

## Actual implemented v56 corrections
1. Add `evdev`, `mousedev` and `serio_raw` to retained module seeds, including automatically discovered dependencies.
2. Explicitly request `modprobe evdev` and `modprobe psmouse` before starting Xorg. Log each command's real result and the guest's input handler records and event nodes to serial.
3. Use the same Firefox sandbox/TLS settings; do not disable any browser security feature.
4. Build a three-stage offline DOM test page:
   - Script-load stage draws an 80px gold bar and changes the title to SCRIPT READY.
   - Real QEMU mouse click turns the background orange and prints CLICK CONFIRMED.
   - Real QEMU keyboard T turns the background green and prints KEYBOARD CONFIRMED.
5. Capture real P6 QEMU framebuffer images before input, after clicking and after typing. Measure independent palette fractions with no OCR. Green or orange in a single arbitrary screenshot cannot pass unless the preceding state was different.
6. Use the actual physical 384MiB guest RAM and a matching 1024MiB positive control; complete RAM copy/root switch/virtual CD ejection must pass.

## Strict interpretation
- QEMU HMP commands being accepted prove only that commands were submitted to QEMU, not that the guest OS, Xorg or webpage received them.
- The screenshot must prove each stage in order. No script readiness -> first investigate JavaScript/script delivery; readiness but no mouse -> Xorg input pointer/focus; click but no key -> keyboard evdev mapping/focus.
- The existing standard VGA Firefox profile may still fail to render at 384 MiB; input fixes do not establish browser memory sufficiency.
- Do not call 384MiB complete until real pages visibly render, input works, stable memory usage is measured, and secure networking is verified in a separate Internet-enabled guest.
- Only the QEMU-only firmware profile is used here. The result is not a physical Intel desktop compatibility certificate.

Latest v56 real KVM workflow:
https://github.com/74127418528426leo-del/Test/actions/runs/41556636182

All changes are on an isolated GitHub branch. This test never edits the user's running Xubuntu system.
