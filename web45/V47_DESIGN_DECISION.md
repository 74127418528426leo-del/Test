# Puppy50 Web v47 engineering decision (2026-11-02)

## Hard requirements retained
- Real 384 MiB QEMU allocation (and separately record 384 MB decimal interpretation).
- The entire running filesystem must be RAM-resident; virtual optical medium must be removable after copy, with no silent fallback to original disk.
- Only the browser is visible, but Linux still supplies an actual secure networking stack, a compatible keyboard/mouse/input layer, display, USB, audio, and tested peripheral support.
- Never modify the user's Xubuntu machine as part of these experiments. Run in isolated disposable virtual machines first.
- Keep Puppy50 Classic/v43 intact as the original-applications baseline. Do not mistake that build for a successful 384 MiB browser-only edition.

## Observed in the v46 1 GiB KVM guest
- Output root SquashFS: **387,715,072 bytes** (**369.753906 MiB**).
- Initrd: **14,210,283 bytes**; ISO image: **452,263,936 bytes**. These numbers describe different artifacts, not three independent simultaneous guest RAM copies.
- RAM copy completed and source virtual CD was unmounted.
- /dev/null non-root read/write preflight PASS.
- Xorg reported running.
- Firefox launch was requested. The sampled log did not prove a rendered Firefox window or a usable Internet browser; 'real_guest_proof_emitted' was false.
- The Actions job concluding 'success' means diagnostics and artifact collection succeeded; it is NOT a user-level browser PASS.
- Evidence: https://github.com/74127418528426leo-del/Test/actions/runs/41536152682

## Arithmetic boundary, independent of optimistic tweaks
- At a **384 MiB** guest size, copying the compressed SFS alone leaves **14.246094 MiB** before kernel, graphics, loaded files and browser processes. A modern full browser cannot be considered functional on that basis.
- At **384 MB decimal** (366.211 MiB), the measured SFS already exceeds total nominal RAM (387.7 MB > 384 MB), so even this file alone does not fit.
- As a PLANNING HYPOTHESIS (not a verified lower bound), assign 64 MiB to kernel+graphics, 160 MiB to web engine, and 32 MiB to burst/headroom. That leaves **128 MiB** for the compressed SFS. It requires reducing the measured SFS by **241.753906 MiB** (~65.4%). Reality may require a still smaller image or larger browser runtime.
- Passing this assumed budget is not proof of actual boot, successful HTTPS, browser compatibility, or safety. Replace hypothetical buckets with repeatable measured allocations.

## Newly audited startup defect
The previous staged root script wrote symlinks from /etc/runlevels/default to '../../../init.d/SERVICE'; those resolve to /init.d/SERVICE and are broken, not /etc/init.d/SERVICE. It also tried to enable 'eudev', whereas Alpine uses 'udev', 'udev-trigger', etc. The v47 branch fixes those paths, adds proper OpenRC boot-stage ordering, and tests a staged fake root without changing the host system.

Reference: https://wiki.alpinelinux.org/wiki/Eudev and https://docs.alpinelinux.org/user-handbook/0.1a/Working/openrc.html

## Next measured experiment (must not be reported as complete)
1. Confirm a rendered, interactive Firefox window at 1 GiB after the /dev/null repair. Test the packaged offline page, key input, and user permission, without disabling security boundaries.
2. Test a newer, security-maintained embedded WebKit/WPEPlatform build as the alternative browser engine. Its DRM/KMS output can avoid a full Wayland/Xorg compositor where supported, but a custom minimal browser shell must provide navigation, tabs, downloading, HTTPS policy, security prompts and recovery. Verify graphics support on Intel i915 and QEMU separately. Do not assume it uses less memory until measured.
3. Build the **complete runtime package closure**, audit its compressed SquashFS size using ram_budget_gate.py, and test at 384 MiB only after it reaches the assumed image-budget gate.
4. Perform repeatable offline rendering, HTTPS/DNS and interaction, random navigation, download, multimedia, keyboard, mouse, USB, graphical output, and boot-CD removal tests. Record kernel+graphics costs, browser PSS, guest MemAvailable, cgroup memory.current, memory PSI, zram real physical consumption, swap-in/out and OOM events.
5. At least five distinct cold boots of an unchanged image, using identical scenes and timeouts. A passing process ID or a CI success badge is insufficient: preserve real screenshot evidence plus successful interaction and a documented 384 MiB memory ledger.
6. Compare directly with original BookwormPup64 and v43 on the same VM hardware and workload; do not present differing workloads as an improvement factor.

## Safe engineering principle
Do not disable browser sandboxing, site isolation, TLS certificate validation or process protections simply to force a 384 MiB boot. A lightweight but unsafe Internet browser is not a successful operating system.
