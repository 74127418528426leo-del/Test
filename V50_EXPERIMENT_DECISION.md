# Puppy50 Web v50 — memory bottleneck experiment and evidence rules

**2026-11-02; experimental branch, no physical Xubuntu changes.**

## Frozen baseline / measured facts

- The v49 Firefox+Xorg+Openbox RAM-root SquashFS is **336,138,240 bytes = 320.56640625 MiB**, down 51,576,832 bytes (49.1875 MiB) compared with its matched pre-optimization reference.
- At **512 MiB**, the real v49 KVM guest copied the full compressed SFS to tmpfs, switched to an overlay rooted in the RAM-copied SFS, ejected virtual boot CD, launched Xorg and requested Firefox. Real 512 MiB QEMU snapshots at 95/145/155 seconds showed a black desktop except for mouse pointer. Browser UI not proven.
- At **1024 MiB**, the *same v49 image* visibly rendered a local Firefox test page in real framebuffer screenshots. Network was disabled; this does not prove DNS, HTTPS, media, WebGL, or keyboard interactivity.
- The old guest serial logs were truncated at the launch-request marker because the foreground Firefox launcher had not returned; **absence of a Firefox exit code is not proof the process succeeded, failed or was OOM-killed.**
- Original v49 evidence: https://github.com/74127418528426leo-del/Test/actions/runs/41541381474

## v50 intervention — instrumentation only

- Add bounded read-only guest serial telemetry, launched just before Xorg. Collect per-sample MemAvailable, Shmem, swap utilization, /proc/vmstat oom_kill/page faults, /proc/pressure/memory, individual process RSS/PSS and limited Xorg/Firefox log excerpts.
- Keep the browser sandbox, site isolation, SSL trust validation, app binaries, codecs and graphics libraries unchanged. No extra disk, no disk swap. Use the same v49 bootless-root concept.
- Test three real KVM memory allocations: **512, 768 and 1024 MiB**. Preserve actual screenshots, ISO integrity checks, guest serial logs and explicit QEMU CD-eject evidence.
- Analyze with `web50/analyze_guest_memory.py` and require three valid sample series. A CI job passing is NOT evidence of successful rendering.

Workflow: https://github.com/74127418528426leo-del/Test/actions/runs/41544771276

## Falsifiable next decisions (not predetermined outcomes)

| Observation | Next technical experiment |
|---|---|
| 512 MiB OOM counter increases | profile exact killed processes; reduce compressed root and runtime memory; then compare RAM-backed zram with no external swap. No guarantee of success |
| 512 MiB memory PSI full sustained/high, but no OOM | identify compression/page-reclaim thrashing, RAM-root tmpfs image size, Firefox multiprocess PSS and tmpfs profile/cache; compare limited RAM-backed swap only as explicit A/B test |
| 512 MiB no OOM, low PSI, Firefox processes alive | investigate X11 window mapping, Firefox profile startup, library loading, font cache, GLib, user permissions and Xorg logs rather than deleting more features |
| 512 MiB Firefox process absent or repeatedly exits | capture exit status and stderr; repair actual process-startup defect, no unverified RAM assertion |
| 768 MiB visibly renders | binary-search practical threshold (e.g., 640 MiB) with identical image and cold-boot protocol |
| 768 MiB also blank but 1024 MiB renders | measure 896 MiB and investigate larger startup headroom |
| Memory watch missing or malformed | fix telemetry before claiming diagnosis |
| Any image only shows a pointer/black framebuffer | treat browser UI as unverified despite successful RAM-root copy |

## 384 MiB design constraint

- **384 MiB binary:** subtracting the 320.566 MiB compressed root leaves at most 63.434 MiB nominal before guest kernel, graphics, initrd, browser, writable tmpfs/overlay and runtime. That is not a feasible complete browsing budget.
- **384 MB decimal:** 366.211 MiB total leaves at most 45.645 MiB before those costs.
- Pursue separate modular designs rather than claiming minor optimizations can bridge this gap. Potential serious paths: independently verified target-specific Crocus driver build, reduced firmware closure grounded in actual PCI/USB inventory, embedded WPE direct-display shell with HTTPS/navigation/permissions, and careful zram-only memory compression. All require actual functional and security verification.
- The QEMU standard-VGA virtual GPU does **not** establish compatibility on an old physical Intel 8086:0042 i915 machine. Test WebGL and dual 1080p physical outputs on the real target after isolated VM validation.

## Definitive acceptance gate

At fixed 384 MiB physical guest RAM: boot, copy verified compressed root into RAM, eject CD, prove all running system storage RAM-backed; render real modern browser UI; navigate offline and HTTPS pages; respond to keyboard/mouse, restore tabs/download files as designed; show no uncontrolled memory pressure/OOM across >=5 cold boots; retain sandbox and TLS; test representative real web apps and graphics. Never infer user-visible success from a process PID, Xorg marker, GitHub Actions success status or screenshot of a blank pointer screen.
