# Puppy50 v58 — VERIFIED real kernel-input breakthrough

Real completed GitHub Actions/KVM run:
https://github.com/74127418528426leo-del/Test/actions/runs/41559290419

## The bug and the repair

The v56/v57 guests retained `evdev`, `psmouse` and `mousedev` files in the temporary initramfs, but the generated early boot direct-insmod script omitted them. After `switch_root`, the final `modprobe` lookup failed, and the guest only showed keyboard `Handlers=sysrq kbd`, with no `eventX` device.

v58 made these drivers **mandatory early initrd insmod seeds** (with their module dependency closure), validated the generated startup loader at ISO build time, and checked kernel state before and after switching roots. This keeps modules resident in the running kernel even when their initramfs files are no longer present.

## Actual guest evidence

At BOTH 384 MiB and 1024 MiB physical QEMU guest allocation, the real `serial.log` contained:

```
PUPPY50_V46_DIRECT_INSMOD module=evdev status=0
PUPPY50_V46_DIRECT_INSMOD module=psmouse status=0
PUPPY50_V46_DIRECT_INSMOD module=mousedev status=0
PUPPY50_V58_INPUT_EARLY_LOADED=evdev
PUPPY50_V58_INPUT_EARLY_LOADED=psmouse
PUPPY50_V58_INPUT_EARLY_LOADED=mousedev
PUPPY50_V58_EARLY_EVENT_HANDLER=PASS
H: Handlers=sysrq kbd event0
H: Handlers=event1 mouse0
H: Handlers=event2 mouse1
```

The root copy, switch to RAM-root and virtual-CD ejection passed in both guests.

| Verifiable browser criterion | 384 MiB | 1024 MiB |
|---|---|---|
| Actual eventX input device handlers | PASS | PASS |
| Offline Firefox JavaScript gold stage | NO (black framebuffer) | PASS |
| Mouse event orange stage | NO | **PASS** |
| Keyboard T event green stage | NO | **PASS** |
| Full offline input sequence | NO | **PASS** |

In the 1024 MiB test, **three different real QEMU screenshots** showed JavaScript ready, CLICK CONFIRMED and KEYBOARD CONFIRMED, in that order. The independent P6 pixel verifier passed all three tests. This is the first actual positive keyboard+mouse user interaction proof for the browser-only system.

## What this does NOT establish

- The 384 MiB guest still did not visually render Firefox, despite successful RAM-root boot and input modules. It is NOT a functional browser at the target RAM limit.
- The measured 212,209,664-byte = 202.37890625 MiB QEMU-only v58 compressed root is NOT equivalent to the separately measured LLVM-free v54 148.621 MiB root. Do not mix those numbers.
- The test is QEMU std-VGA with no virtual network adapter; it does not prove HTTPS, DNS, URL navigation, downloads, real WebGL, graphics acceleration, diskless system package updates, or peripheral support on the physical Intel 8086:0042 Acer computer.
- This is a local offline page exercise. Browser sandbox/TLS flags were not explicitly disabled, but security isolation and full TLS behavior were not independently audited.

## Next experiment already underway

v59 integrates v58's early input loading into the smaller custom Softpipe Mesa configuration and applies **fail-closed 384 MiB offline input acceptance**:
https://github.com/74127418528426leo-del/Test/actions/runs/41560016480

No change was made to the user's Xubuntu operating system. Source and actions logs are durable; GitHub artifacts have limited retention.
