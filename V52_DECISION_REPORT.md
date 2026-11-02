# Puppy50 v52: The process-state experiment

Date: 2026-11-02. Branch: puppy50-v52-firefox-waitstate-probe.

## Why this is the next highest-value experiment
The same v50 Firefox+Xorg+Openbox bootless compressed RAM root was booted in KVM at three allocations (https://github.com/74127418528426leo-del/Test/actions/runs/41544771276).

| Guest RAM | 512 MiB | 768 MiB | 1024 MiB |
|---|---:|---:|---:|
| Boot, copied SFS, root switch, CD ejection | PASS | PASS | PASS |
| Peak monitored Firefox-related subprocesses | 1 | 4 | 9 |
| Kernel OOM kill counter increase | 0 | 0 | 0 |
| Minimum MemAvailable (MiB) | 49.312 | 42.777 | 10.617 |
| Real framebuffer browser page visible | NO | NO | YES |

The v50 main Firefox process at 512 MiB has roughly 23–33 MiB RSS during sample intervals; the full browser process tree does not appear. This is evidence of incomplete initialization, but no proof of the precise cause. No kernel OOM does NOT exclude userspace malloc/mmap failure.

## New observation channels (not optimizations)
- v52 retains v50's 3-second bounded guest serial memory monitor.
- It adds the Firefox parent process state, number of threads, VmSize, VmPeak, kernel wait channel (wchan) and up to six representative thread wait channels.
- No browser security flags or process limits are changed. No new graphics stack and no new guest file logging are needed.
- Same installed browser, hardware modules, firmware and root architecture are retained; only this diagnostic script grows slightly.
- Compare real QEMU boot at 512 and 1024 MiB. Record full serial, three framebuffer screenshots and CD ejection proof for each.

## Interpretation rules
- Multiple long-lasting futex or poll waits can be normal event loop behavior; **do not label a deadlock without corroboration**.
- A 512 MiB VmSize above physical RAM alone does not prove failure: virtual address reservations are not necessarily resident.
- 512 MiB parent alive and small RSS with no content process may indicate failed allocation or process launch, an initialization stall or a graphics IPC blockage. Investigate actual stderr, failed syscalls and mapped X11 windows before choosing a repair.
- If 512 and 1024 have the same parent state/wait profile but very different content children, focus on process creation, sandbox permissions and memory allocator return paths.
- Firefox rendering only at 1024 MiB is a functional observation for the local page. QEMU uses -nic none so secure HTTPS functionality is not proven.
- At least 384 MiB (binary) with functioning browser UI, real input and secure Internet access is required for goal acceptance; an SFS copy and blank cursor do not count.

## Architecture work in parallel
- A separate branch (puppy50-v51-qemu-firmware-experiment) is measuring removal of firmware **unused only by QEMU standard VGA**. It is never safe to distribute that image as universal hardware boot.
- Mesa v26.1 Gallium has a confirmed direct DT_NEEDED dependency from libgallium-26.1.6.so to libLLVM.so.22.1 in the existing Alpine build. Do not remove LLVM by file deletion.
- Mesa's Meson gallium-drivers option can select crocus and softpipe with LLVM disabled in an independent source-build experiment; compile and run tests before claiming the target Intel 8086:0042 functionality. See https://android.googlesource.com/platform/external/mesa3d/+/refs/tags/upstream-mesa-26.1.2/meson.options.
- WPE WebKit 2.54 WPEPlatform includes DRM/KMS and headless output without a desktop compositor (https://wpewebkit.org/about/faq.html). A real browser shell would still need URL bar, tab handling, downloads, permissions, updates, and full security controls.

The v52 workflow result must be read before any new root-cause claim; nothing here proves modern browsing at 384 MiB.
