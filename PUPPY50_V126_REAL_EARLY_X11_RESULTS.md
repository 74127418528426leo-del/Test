# Puppy50 v126 — genuine pre-systemd authenticated Firefox first frame achieved (NOT three seconds)

**Status: experimental QEMU-only research; browser visible in 8.70 seconds from immediately before QEMU spawn. The under-3-second user goal remains unmet. No v126 public ISO release or real-Acer test.**

## Direct evidence

A complete [v126 QEMU KVM run](https://github.com/74127418528426leo-del/Test/actions/runs/43504728219) booted the authenticated early-Xorg startup path. Verified guest log and browser measurements:

- Xorg was requested at **3.23 seconds of guest kernel uptime** and Openbox at **3.34 seconds**; kernel uptime is *not* the same origin as the timer from before host VM launch.
- A persistent post-switch-root reporter showed **Xorg PID running as root on display :0 using `-auth /home/user/.Xauthority -nolisten tcp -noreset vt1`**, nonroot Openbox running, and nonroot Firefox ESR PID running. It also confirmed the original late LightDM executable **was absent**, preventing a false-positive fallback.
- The X11 socket `/tmp/.X11-unix/X0` survived the switch root. v125 had failed because systemd's later `tmp.mount` hid the socket even though Openbox, Xorg and Firefox processes appeared present.
- Actual Firefox home page framebuffer first detected at **8.70 seconds from QEMU launch**, based on real screenshot pixels rather than a splash image or browser PID.
- Full root checksum-verified RAM backing at **15.88 seconds**, subsequent virtual-media ejection and an authenticated new browser **HTTP 200** after ejection, browser still running, and zero benchmark-reported errors.

The exact released v117 kernel and the original full-RAM recovery initrd remain unchanged in the experimental candidate. The main Zstd SquashFS root remains original and byte-identical. This test used 2 virtual CPUs and 3 GiB RAM on a modern KVM host; it **does not** emulate Intel i3-540 physical performance, nor verify Intel i915, actual Wi-Fi, dual monitor or 4K performance.

## Engineering implications

v126 is a meaningful *architecture validation*: a user-authenticated nonroot Firefox session is now compatible with an Xorg server started before systemd PID1, as long as the virtual DRM module is initialized and the UNIX socket survives /tmp continuity. The previous v123 window observed at ~9 seconds was created by late LightDM; the v126 reporter explicitly ruled that out.

The benchmark still takes far more than three seconds. Speed attribution cannot be made by comparing v126's 8.70 seconds against other GitHub runners; an exact same-host A–B–B–A comparison is needed. One such follow-up v127 test moves Firefox from the Openbox autostart script to a concurrent nonroot launch immediately after the X socket appears, while retaining actual framebuffer, verified RAM, safe-media and HTTP 200 checks.

## Release restriction

Do **not** claim under-three-second power-on, production OS support or the 384MiB RAM-only goal from these results. Keep the currently published [v122 experimental Zstandard and LZ4 ISO downloads](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v122-direct-fast-codec-experimental) and the independent [v115 recovery ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v114-fast-verification-experimental). The original Shift-held BIOS rescue menu is not independently proven accessible. A more radical physical boot and native graphics/Firefox startup redesign is still needed for <3 seconds.
