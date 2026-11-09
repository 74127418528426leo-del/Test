# Early non-root Firefox session experiment

Goal: compare the published v113 ISO against a diagnostic image that starts the real non-root Firefox desktop earlier, targeting the same eight-second goal. The experiment does not disable Firefox sandbox features, remove browser files, weaken the RAM-copy reserve, modify the root SquashFS, or change the original full-RAM fallback.

The v113 direct-session experiment was neutral because it waited for `live-config.service` and `systemd-user-sessions.service`. This variant prepares the live user after local filesystem setup and starts D-Bus, logind, udev trigger and the direct X11 session before the normal `sysinit.target` completes. It retains PAM login, the network applet, rootless Firefox and the late RAM transition. It removes logind's explicit wait for `modprobe@drm.service` while still requesting that module; real hardware effects are unknown.

Use identical QEMU/KVM host settings, 2 vCPUs, 3 GiB, BIOS, virtual USB capped at 30 MiB/s and a host-clock timer starting before QEMU, in A–B–B–A order. Verify runtime systemd dependencies, non-root Firefox/network controls, actual early local-page JavaScript response, green verified RAM readiness, fresh local-page input after virtual USB removal and public HTTPS screenshots. A separate early journal reporter preserves diagnostics if the graphical session never reaches `graphical.target`. An 8-second physical Acer boot is not established by this experiment.

Only a material, repeated improvement with preserved functionality could justify further validation of the exact image. If the change causes service cycles, graphical failure, lost networking or no measured gain, preserve the evidence and do not adopt it.
