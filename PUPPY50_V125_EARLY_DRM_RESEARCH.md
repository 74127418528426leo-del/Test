# Puppy50 v124/v125 — verify the early X11 path rather than relying on fallback

**Status 2026-11-13:** Real Firefox cold boot under 3 seconds **NOT proven**. v122 is the newest independent experimental release; see [v122 release](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v122-direct-fast-codec-experimental). Keep [v115 separate recovery media](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v114-fast-verification-experimental).

## Why the apparent pre-systemd Firefox boot did NOT verify early Firefox

The first [v123 run](https://github.com/74127418528426leo-del/Test/actions/runs/43500793748) showed neither an actual Firefox frame nor RAM-ready in the benchmark result, although a later artifact audit confirmed serial `P50_STAGE_COPY_VERIFIED` and `P50_STAGE_READY` markers: the browser-first benchmark simply never advanced to the RAM-ready polling gate after failing the visual-frame test. Therefore **do not report the RAM copy itself as having failed**.

Other v123 runs rendered a Firefox window in 9.10 and 9.29 seconds, but a [read-only v124 post-root forensic run](https://github.com/74127418528426leo-del/Test/actions/runs/43502728439) established **the display was created by late LightDM**, not the new early Xorg. Its serial evidence:

- Attempted early Xorg began around **2.6 seconds guest kernel uptime**, but its own Xorg log said **`AddScreen/ScreenInit failed for driver 0`** and `Server terminated with error (1)`.
- Early Openbox reported **`Failed to open the display from the DISPLAY environment variable`**.
- After switch root, a different **LightDM** process was running with **`Xorg :0 ... -auth /var/run/lightdm/root/:0 ... vt7`**, not the early secure Xorg launched with `-auth /home/user/.Xauthority ... vt1`.
- The late LightDM/Firefox session explains the 9.29-second successful Firefox frame without proving that the early-Xorg route worked.
- The RAM migration service still reported **`P50_STAGE_COPY_VERIFIED` and `P50_STAGE_READY`**, so the principal failure was early display initialization, not the verification algorithm.

This falsifies any assertion that the previous v123 run successfully accelerated cold Firefox by running X11 pre-systemd. The original VM method was insufficient to discriminate late LightDM fallback.

## v125 experiment: explicit DRM prerequisite and no LightDM fallback

The [guarded patch](./v125/require_early_drm.py) is applied **only** to a disposable extracted staged boot initrd after early nonroot user precreation and the earlier v123 X11 hook:

1. Attempt QEMU std VGA's `bochs_drm` module and initialize `/dev/dri/card0` before asking Xorg to start. Fail closed if module/device unavailable.
2. Mask `lightdm.service` in that isolated test overlay so an apparent window rendered by the old session cannot falsely pass.
3. Retain Xauthority MIT cookie, TCP-disabled Xorg, unprivileged Firefox and original kernel/root/fallback initrd.
4. Verify the active post-root display process is **`Xorg ... -auth /home/user/.Xauthority`**, and no LightDM is running.
5. Accept only a real framebuffer Firefox page, checksum-verified whole-root RAM migration, virtual-media ejection after RAM READY, and an authenticated new browser HTTP 200 response after eject.

[Reproducible v125 real-VM workflow](https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-v125-early-drm-no-fallback.yml). This is not a release and not equivalent to a physical i915 (Acer) graphics driver test. If virtual DRM is unavailable or the early display does not function, the approach is rejected rather than silently allowing LightDM to start.

## Existing safe reference

The best *same-host matched* v122 six-VM result was a **6.755-second mean** real Firefox first frame for LZ4 plus earlier direct X11, versus **7.955 seconds** for the released v117 ISO. Zstandard early-direct averaged **7.385 seconds** and uses substantially less compressed RAM. This comparison passed six post-media-ejection authenticated HTTP 200 receipts and verified RAM checksum. The v122 published ISO later independently passed BIOS/UEFI browser and safe-RAM smoke tests (which are slower and from different runners). No tested configuration has achieved `<3.00` seconds or been tested on the actual Acer X3950 with i3-540, i915 graphics and Wi-Fi.

**Release gate:** Do not label an ISO "three-second cold Firefox" without repeated physical or matched KVM verification of the actual first Firefox frame and safe networking/RAM operation.