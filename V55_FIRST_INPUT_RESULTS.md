# Puppy50 v55 — first real QEMU keyboard test, verified result

Run: https://github.com/74127418528426leo-del/Test/actions/runs/41552914467

## What was actually tested

A complete QEMU standard-VGA browser-only Alpine/Puppy-inspired system was booted with 384MiB and 1024MiB guest memory. Both copied the compressed SquashFS to RAM, switched onto the RAM root and ejected the virtual optical medium.

The local HTML page contained inline JavaScript that changes the whole body background to green (#2bcc71) and changes the main heading when the T keydown event reaches the document.

At 175 seconds, the QEMU HMP virtual-key command "sendkey t" was submitted. Real QEMU framebuffer PPM images at 145 and 175 seconds were compared using an independently tested PPM color-counting tool (no OCR).

| Result | 384MiB | 1024MiB |
|---|---|---|
| RAM-copy/root switch/CD ejection | PASS | PASS |
| QEMU virtual keypress submitted | YES | YES |
| Local browser visible | NO (black/pointer) | YES (actual rendered Firefox HTML) |
| Green page visible after keypress | NO | NO |
| Keyboard visually proved to reach page | **NO** | **NO** |
| Network/HTTPS tested | NO | NO |

The CI job successfully collected evidence, but **the keyboard interaction criterion failed at both memory sizes**.

This does not prove the physical or virtual keyboard device itself is broken. Possible causes include missing or uninitialized PS/2/evdev input devices, Xorg/libinput mapping, page focus, Firefox key handling, or test timing.

## Corrected follow-up test

- Log real guest /proc/bus/input/devices, /dev/input node listings, and Xorg input-driver setup lines to the VM serial device.
- Issue an HMP mouse click followed by the keyboard T keypress, recording QEMU command replies and resulting screenshot.
- Require visible green pixel fraction >30% after the keypress and <4% before. Keep false positive checks for black screens and unchanged frames.
- Avoid interpreting successful HMP command submission as proof that X11 or WebKit/Firefox received a keyboard event.
- Do not weaken Firefox sandbox, SSL trust checks or site isolation.

The corrected branch is https://github.com/74127418528426leo-del/Test/tree/puppy50-v55-real-keyboard-proof
The original screenshot evidence is in a 7-day GitHub Actions artifact for the above run.

This test concerns a QEMU-only Linux guest. No real old Intel PC input compatibility or 384MiB modern browser usability is established.
