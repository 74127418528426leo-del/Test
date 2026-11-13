# Puppy50 v120: real Linux critical-path optimization toward under 3 seconds

**2026-11-13. Status: genuine Firefox <3 seconds NOT achieved.** v117 experimental release and v115 recovery media remain unchanged and separately available. The candidate is test-only, not a production OS and not a physical Acer boot claim.

## Critical-path measurement — persistent guest systemd reporter

[Successful complete profiler run](https://github.com/74127418528426leo-del/Test/actions/runs/43498072829): the **actual** guest persistent systemd service wrote its report to QEMU serial **after switch-root**, avoiding the older failed initramfs background reporter. The VM visibly rendered Firefox, passed checksum-verified complete root-to-RAM migration, performed verified virtual CD eject and received a new real HTTP 200 browser response.

The guest's **systemd-analyze time** reported **1.599 s kernel + 2.303 s userspace = 3.902 s to graphical.target**. This is the guest kernel-origin clock, **not** the independent host monotonic from before QEMU launch; do not add or subtract as if origins matched. Systemd dependency chain:

- `live-config.service` started at 1.485 s of systemd userspace, took **446 ms**, and precedes `basic.target`.
- `basic.target` reached after **1.932s** in userspace.
- `NetworkManager.service` began at 1.993 s, took **251 ms** before `network.target` and `systemd-user-sessions.service`.
- `lightdm.service` became active around 2.272 s in userspace (the unit itself took only **21 ms**, which does NOT cover Xorg/PAM and Firefox graphical readiness).
- `graphical.target` reached after 2.301 s of userspace, 3.902 s total from guest kernel entry.

The journal included Xorg and nonroot Firefox process activity, and normal Firefox child content/socket processes (Firefox sandbox was **not disabled**). The largest `systemd-analyze blame` item (the p50-staged-root DM device) measures long residency and is **not** an actual blocking path to lightdm; do not misattribute 11.96 s to critical boot.

**Consequence:** in this VM the ordinary userspace graphical target alone exceeds the new three-second target, before the actual Firefox frame. A true sub-3-second design needs Firefox launched earlier in parallel with essential services or a fundamentally different OS/display/browser startup. Disabling one tiny network or GUI helper cannot close this gap.

## Verified v120 no-LightDM direct unprivileged X11 candidate

Another [independent four-VM A–B–B–A benchmark](https://github.com/74127418528426leo-del/Test/actions/runs/43497790398) tested a **disposable initrd variant**, implemented by [v120/rapid_direct.py](./v120/rapid_direct.py). Its staged-only boot precreates the nonroot user, masks the redundant `live-config.service`, and runs Firefox through `startx`, `dbus-run-session` and `openbox-session` without LightDM. The kernel, root SquashFS, physical network stack, Firefox binary and full-RAM fallback initrd are unchanged.

| Matched cold QEMU BIOS/SATA trial | First real Firefox frame | SHA-verified RAM READY |
| --- | ---: | ---: |
| Original v117 #1 | 7.83 s | 14.96 s |
| v120 direct X11 #1 | **6.96 s** | 14.09 s |
| v120 direct X11 #2 | **6.97 s** | 14.11 s |
| Original v117 #2 | 6.75 s | 14.38 s |
| **Original mean** | **7.290 s** | **14.670 s** |
| **v120 candidate mean** | **6.965 s** | **14.100 s** |

**Measured same-runner first-frame gain: 0.325 s.** Full RAM READY was 0.570 s faster. Every VM displayed the **actual 1280×800 Firefox page**, reached verified RAM-ready, safely removed virtual boot media, and generated a fresh server-observed **HTTP 200** afterward. This is working VM functionality, but not proof of real Wi-Fi, i915 drivers on the user's Acer, or a consistent time below three seconds.

The first v121 direct-start-at-basic.target iteration had a **static source-pattern failure** before VM boots, so it provides **no performance measurement**. The exact-match fix and a new workflow are under testing on its own research branch; do not report gains until its run passes.

## Unresolved hard limits

- No single tested candidate reached under 3.00 s. The current positive v120 first-frame samples are 6.96/6.97 s.
- The published v117 ISO's 664.3MiB compressed root alone already exceeds a 384MiB RAM budget, and modern Firefox needs additional memory. No true 384MiB Firefox claim is valid.
- Physical Acer X3950 i3-540 power-on firmware, Intel i915, Wi-Fi, dual-monitor support, 4K streaming and low-speed USB are unverified.
- The v117 original SHIFT-key rescue menu was not independently proven accessible; preserve the v115 recovery ISO on a separate medium.
- No network TLS/sandbox protections were removed in these v120 experiments. Retain all verification gates on any new release.

**Decision: keep v120 as an auditable research branch, NOT a 3-second ISO.**

## Independent second guest profile: process start times from actual /proc

[Completed v120 process-uptime profile](https://github.com/74127418528426leo-del/Test/actions/runs/43499820480) measured actual kernel process-creation times by reading process stat field 22 from within the real booted guest (rather than guessing from PID existence).

- **Xorg:** guest kernel uptime **4.960 seconds** at process creation.
- **Openbox:** guest kernel uptime **5.640 seconds**.
- **Firefox ESR parent process:** guest kernel uptime **5.800 seconds**.
- **Real first Firefox frame:** **9.43 seconds** from host monotonic immediately **before QEMU launch**; the kernel-uptime clock and host clock have different origins and must not be subtracted directly.
- **systemd graphical target:** this separate runner reported **2.236s kernel + 2.745s userspace = 4.981s**. The first runner reported 3.902s; absolute timings are not universal.
- This VM again completed SHA-verifiable RAM migration, safe virtual medium removal, and a successful new HTTP 200 browser request after ejection.

The normal Firefox launch path on this guest is **already >3 seconds since guest kernel clock start before Firefox exists**, let alone renders. Getting a true sub-3-second *cold* browser frame would require bypassing the existing start dependencies, or redesigning the OS/browser, not merely masking a small service. The trial does not prove that every imaginable radically different architecture is incapable of three seconds, nor does it test a physical Acer CPU/firmware.
