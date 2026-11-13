# Puppy50 v126–v127: authentic early X11 through Linux switch-root

## What is actually proven

**No authentic Firefox cold first frame under three seconds has been achieved or certified.** The most comparable six-VM published-v122 study showed v117 7.955 s, earlier X11 with unchanged Zstandard root 7.385 s, and earlier X11 plus larger LZ4 root 6.755 s to the actual first Firefox framebuffer (the three groups ran on the same GitHub KVM host). All 6 passed the checksum-verified root migration, virtual-media ejection and a new real HTTP 200 request afterward. [Six-run benchmark](https://github.com/74127418528426leo-del/Test/actions/runs/43499812972). The two separately published v122 experimental ISOs are at [v122 release](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v122-direct-fast-codec-experimental). This is NOT a physical Acer power-on test.

### The pre-systemd X11 defect and its correction

The original v123 attempt produced either no Firefox frame or a **late LightDM fallback** frame—not a valid early display. The [v124 forensic run](https://github.com/74127418528426leo-del/Test/actions/runs/43502728439) found early Xorg `AddScreen/ScreenInit failed for driver 0` and Openbox unable to connect to the display; after switch-root a different LightDM-managed Xorg owned vt7. That invalidated any attribution of a late ~9 s Firefox window to the failed early Xorg.

A v125 attempt to force QEMU std VGA's DRM display before starting the early authenticated Xorg succeeded in making `bochs` load, preserving the early `Xorg :0 -auth /home/user/.Xauthority ... vt1` through the root switch, but still drew no browser frame. The [v125 forensic VM](https://github.com/74127418528426leo-del/Test/actions/runs/43504239144) found early Xorg and nonroot Openbox/Firefox processes alive, while **`/tmp/.X11-unix` had become empty after Linux switched root**. The systemd `tmp.mount` was obscuring the temporary early X11 UNIX socket. Merely finding Firefox processes cannot count as a visible browser.

The new v126 isolated initrd patch [v126/preserve_xsocket.py](./v126/preserve_xsocket.py) masks only the late `tmp.mount` in the volatile live root overlay, preserving the originally initialized `/tmp` (still temporary RAM, with 01777 permissions) and early Xorg socket across switch-root. It **does not** disable Xauth, Firefox sandbox, remove external network drivers, or replace the unchanged full-RAM recovery initrd.

### Complete v126 VM proof

[The actual tested v126 ISO experiment passed](https://github.com/74127418528426leo-del/Test/actions/runs/43504728219):

- A real **1280×800 Firefox home-page framebuffer** first seen at **8.70 s** on a host monotonic clock starting immediately before QEMU's process launched, including virtual BIOS/menu/kernel/userspace. This is not physical Acer time.
- The running real Xorg process after switchroot was **`Xorg :0 -auth /home/user/.Xauthority -nolisten tcp -noreset vt1`**, without LightDM. The `/tmp/.X11-unix/X0` socket was visible after switch-root. Nonroot Openbox and Firefox content/socket processes were running. Pre-systemd Xorg and session traces were independently printed.
- The original, unchanged compressed root copy was checksum-verified and green RAM READY reached at **15.88 s**. Only then did the benchmark eject the SATA/AHCI virtual optical medium.
- Firefox opened a new local page via an **HTTP 200** request from the test server after ejection, with the VM still running. The original kernel, SquashFS root and full-RAM fallback image stayed byte-identical to their v117 source.
- **8.70 s is not below 3 seconds.** No v126 ISO was released as a three-second browser, and Wi-Fi, real i915, dual monitors, physical Acer i3-540 CPU/BIOS and 4K online video were not independently tested. The 384MiB all-RAM Firefox goal remains unmet.

### v127 research experiment

The [v127/parallel_firefox.py](./v127/parallel_firefox.py) variant starts the **unchanged Firefox ESR as the same unprivileged user** as soon as the early authenticated X11 socket exists, in its own `dbus-run-session`, *concurrently with* Openbox startup, rather than from Openbox's later autostart. It edits only the volatile staged live account autostart to avoid duplicate Firefox while retaining network applets and polkit. The kernel, original root, original full-RAM fallback and Xauth/sandbox remain unchanged.

A [four matched A–B–B–A CI experiment](https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-v127-parallel-firefox-ab.yml) builds both ISOs from identical verified source and compares real frame timings on the SAME runner. It requires every boot to retain the early authenticated Xorg after switch-root, preserve X0 socket, verify full RAM migration, safely eject virtual media and make a new authenticated server HTTP 200 request. Any failure or a non-Firefox splash frame is not an accepted result.

**Release gate remains strict: no under-three-second ISO without repeated true cold Firefox frames under 3 s, all functional/safety gates, and real-hardware validation. The latest downloadable experimental media remain the published v122 release.**
## v127 completed matched four-boot results — 2026-11-13

[Completed v127 A–B–B–A authenticated Firefox test](https://github.com/74127418528426leo-del/Test/actions/runs/43505491538) succeeded. On ONE shared KVM runner, both images were rebuilt from the exact original v117 ISO with identical kernel, Zstd root SquashFS, unchanged full-RAM recovery initrd, early graphics module, authenticated Xorg, non-root Firefox and volatile X11 socket continuity. The only functional change in v127 was to launch the original Firefox ESR concurrently with Openbox and comment out its duplicate Openbox autostart command in the volatile live account.

| Matched trial | Real Firefox first frame | Verified RAM READY |
|---|---:|---:|
| v126 Openbox autostart #1 | 9.03 s | 15.74 s |
| v127 parallel Firefox #1 | **8.61 s** | 15.83 s |
| v127 parallel Firefox #2 | **8.42 s** | 15.63 s |
| v126 Openbox autostart #2 | 8.63 s | 15.30 s |
| **v126 mean** | **8.830 s** | **15.520 s** |
| **v127 mean** | **8.515 s** | **15.730 s** |

**First-frame gain: 0.315 seconds.** Complete RAM READY slowed 0.210 seconds in this same-runner experiment. All four VMs had a genuine user-visible Firefox home frame and passed checksum-verified RAM migration, media ejection after READY, a new server-received HTTP 200 from the running Firefox browser, and proof of authenticated pre-systemd Xorg still running with /tmp/.X11-unix/X0 present after switch-root. The v127 candidate had serial markers proving the normal Openbox Firefox autostart was relocated and the unprivileged direct launcher executed. No late LightDM fallback was accepted. No Firefox sandbox, Xauth, CA store, original root or recovery image was weakened.

**Neither candidate was anywhere near 3 seconds.** The two v127 first frames were 8.61 and 8.42 seconds and the 8.515s candidate mean is not directly comparable with v122's 6.755s mean measured on a different KVM host. This result shows that parallel Firefox startup alone does not close the multi-second gap. Do not publish a new v127 ISO as a 3-second OS. The best published, fully verified experimental download is still [v122](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v122-direct-fast-codec-experimental). The physical Acer i3-540, real i915, Wi-Fi and 384MiB full-RAM target remain unproven. Keep separate v115 recovery media.
