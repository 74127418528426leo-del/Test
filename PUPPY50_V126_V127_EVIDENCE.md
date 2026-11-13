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