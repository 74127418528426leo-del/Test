# Puppy50 v152 — startupCache preseed experiment: DO NOT SHIP (2026-11-13)

**Verdict: no verified speed improvement and no usable startupCache binary generated.** Never label this an under-five-second OS.

In all attempts the build used the identical immutable Debian Firefox ESR SquashFS root and a newly created temporary user profile. Only an offline `startupCache` directory could have been transferred into a proposed boot image; no browsing history, cookies, credentials, or profile database were eligible. Cache generation was gated on genuine Firefox-created cache files with size limit 32 MiB, no symlinks and no user data. No candidate ISO was published because that gate never passed.

Audit of successive failures:

1. [Headless attempt 43541435133](https://github.com/74127418528426leo-del/Test/actions/runs/43541435133): headless Firefox rendered no usable SWGL framebuffer, timed out after 60s and created no startupCache. Unprivileged namespace and font-cache warnings.
2. [Xvfb attempt 43542114524](https://github.com/74127418528426leo-del/Test/actions/runs/43542114524): Xvfb start plus writable font directories; browser stayed alive until timeout and generated no startupCache. Missing or invalid DBus machine identity.
3. [Xvfb root creation fix 43542141514](https://github.com/74127418528426leo-del/Test/actions/runs/43542141514): disposable Xvfb environment still produced no cache.
4. [DBus machine-id attempt 43542499420](https://github.com/74127418528426leo-del/Test/actions/runs/43542499420): session daemon could not resolve UID 1000; first Firefox window absent, exit 127. See [read-only diagnostics](https://github.com/74127418528426leo-del/Test/actions/runs/43542894138).
5. [Disposable UID1000 fix 43542950865](https://github.com/74127418528426leo-del/Test/actions/runs/43542950865): real Firefox Xvfb window observed, but no `startupCache` after timed window run. The UID was created **only in build-only root**, never the shipped base image.
6. [Final Xvfb + Openbox + Ctrl-Q attempt 43543365213](https://github.com/74127418528426leo-del/Test/actions/runs/43543365213): real Firefox window reported, but the process did not exit cleanly before the 48-second timeout (124), and no startupCache was generated. Nothing included in release.

The safe fallback is the **independently released v150 VT7 early Firefox ISO**:
https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v150-vt7-early-firefox-experimental

The v150 exact-shipping image passed **four separate BIOS/UEFI cold Firefox frame + full RAM checksum + virtual-media ejection + new authenticated HTTP200** tests:
https://github.com/74127418528426leo-del/Test/actions/runs/43540928354
BIOS frames: 8.35s, 7.72s; UEFI frames: 11.06s, 11.06s.
These are QEMU KVM timings, **NOT** physical Acer i3-540 timings; **NOT** five seconds; full-RAM READY happens later.

Further trusted experimental improvements can be retested:
- [v141 actual Firefox process nice=-5](https://github.com/74127418528426leo-del/Test/actions/runs/43521736672): same-host baseline 7.245s vs 6.695s
- [v146 nice=-10 vs -5](https://github.com/74127418528426leo-del/Test/actions/runs/43523205534): 7.55s vs 6.90s
- [v151 WebRender configuration + nice=-10](https://github.com/74127418528426leo-del/Test/actions/runs/43541098999): matched 9.15s vs 8.03s, independent BIOS 7.84s and UEFI 12.69s. Host-runner variance is substantial and the sampled gain MUST NOT be summed with other workflow results.

Remaining constraint: a genuine full Firefox first window below **5.00 seconds on repeated cold boots**, followed by independently verified network/TLS and full RAM before media removal. A physical Acer test is still required to make any hardware-specific claim. No 384 MiB RAM-only support.
