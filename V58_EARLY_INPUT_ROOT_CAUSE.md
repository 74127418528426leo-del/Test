# Puppy50 — early-initrd evdev driver handoff

**Status: code change committed, real v58 KVM input proof pending.** This document distinguishes the verified v56 failure from the v58 hypothesis.

## Verified failure from real v56 guest

Completed run: https://github.com/74127418528426leo-del/Test/actions/runs/41556636182

The v56 build's retained module/initial RAM disk inventories both listed `evdev`, `psmouse`, `mousedev` in the 107-driver closure for Alpine kernel `6.18.60-0-lts`.

Yet real guest `serial.log` at **both 384 MiB and 1024 MiB** contained:
```
modprobe: FATAL: Module evdev not found in directory /lib/modules/6.18.60-0-lts
PUPPY50_V56_INPUT_MODULE_FAILED=evdev
PUPPY50_V56_INPUT_MODULE_FAILED=psmouse
PUPPY50_V56_INPUT_MODULE_FAILED=mousedev
H: Handlers=sysrq kbd
```

The guest copied its compressed root into RAM, switched root and ejected the virtual boot CD at both RAM sizes. At 1024 MiB, real framebuffer snapshots proved the bundled local webpage rendered and its JavaScript executed (gold script-ready bar). At 384 MiB the screen was black except the pointer. Neither memory allocation showed the prescribed orange mouse-click or green keyboard-response state.

This means **the original input 'fix' did not actually load input-event drivers into the running kernel**. It is not evidence that Firefox could not receive input for another reason after evdev is corrected.

## Root cause in source code

`web45/minimal_initrd_modules.py` copied the complete retained 107-driver closure into the initial RAM disk. But `web45/direct_insmod_loader.py` generated an early `/busybox insmod` script with only storage/network-storage filesystem seeds. It did **not** load `evdev`, `psmouse`, or `mousedev` before `switch_root`. Once the initial RAM disk was discarded, the final root's modprobe lookup did not locate those drivers. The resulting guest lacked `eventX` input handlers needed by Xorg/libinput.

## Implemented v58 repair

- Add `evdev`, `psmouse`, `mousedev` as **mandatory early-initrd direct insmod seeds**, in dependency order.
- Require these drivers to exist in the generated module dependency graph and to be explicitly represented in the generated `load_early_modules.sh`; refuse to build an ISO otherwise.
- Record the real `/proc/modules` state and `/proc/bus/input/devices` event handlers **before** switch_root. Record persistent `/sys/module` state and actual event handlers in the final RAM root.
- Do not interpret a failed `modprobe` after switch_root as proof a previously loaded kernel module is absent. Check kernel state instead.
- Retain the v56 independently visible DOM readiness, mouse, and keyboard tests, and test at 384/1024 MiB using real QEMU HMP input and PPM captures.

Run: https://github.com/74127418528426leo-del/Test/actions/runs/41559290419

## Unchanged acceptance standards

A successful load of evdev alone is **not** a 384 MiB browser success. The combined goal still requires visible rendering, real user input, URL navigation, HTTPS/TLS and sandbox behavior, repeatable RAM-root boot without removable boot medium, stable memory pressure and a coherent updateable package set. This is a QEMU std-VGA test only; not evidence of Intel GMA 8086:0042 hardware compatibility.

Only GitHub experimental source and CI images were changed. The user's Xubuntu computer was not touched.
