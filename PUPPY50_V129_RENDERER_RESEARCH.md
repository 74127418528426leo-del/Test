# Puppy50 v129 — Firefox first paint vs Mesa llvmpipe software shader compilation

**Research only; under-three-second Firefox cold boot NOT demonstrated. No release allowed by this experiment alone.**

## Why this is a higher-value experiment

Current Mozilla Bugzilla issue [2084921](https://bugzilla.mozilla.org/show_bug.cgi?id=2084921) reports that Linux Firefox CI systems **without a GPU** can block the first visible browser paint for approximately **1.5 seconds** when Mesa llvmpipe first compiles software shader code. The issue explicitly discusses using the **`gfx.webrender.software=true`** setting as a possible way to avoid unnecessary GL software rendering. This is a hypothesis specific to that test class, **not proof** that the Puppy50 guest has exactly the same cause, nor that old physical Intel i915 hardware will benefit.

Previous [v126](https://github.com/74127418528426leo-del/Test/actions/runs/43504728219) proved nonroot Firefox working on authenticated, before-systemd Xorg after reliable virtual DRM and X11 socket handoff. A subsequent [v127 matched four-boot run](https://github.com/74127418528426leo-del/Test/actions/runs/43505491538) moved Firefox to launch in parallel with Openbox and measured 8.515s vs 8.830s same-host first Firefox frame, a modest 0.315s gain. The [v128 user-precreation test](https://github.com/74127418528426leo-del/Test/actions/runs/43506349966) measured only 0.075s difference, below the 0.2s sampling interval, so prebuilding the user was rejected.

## Exact v129 controlled test

The [v129 test-only initrd patch](./v129/software_webrender.py) writes a single Firefox ESR enterprise Preferences setting, `gfx.webrender.software=true`, **before starting Firefox**. It leaves Firefox binary, Gecko content isolation, TLS, sandbox, networking, original kernel/root squashfs, original full-RAM fallback, Xorg authentication and early GPU initialization intact. The patched migration diagnostics check that the setting actually appeared in Firefox's profile; an absent profile observation must fail the workflow rather than be treated as proof of an effective setting.

The [four-boot A–B–B–A workflow](https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-v129-software-webrender-ab.yml) compares exact v127 early-Firefox boot against the identical image with only the enterprise policy. All VMs must render real Firefox home pixels, retain authenticated X11 without LightDM fallback, checksum-copy the complete root into RAM, eject virtual media **after** RAM READY, and register a new nonce-authenticated **HTTP 200** response from Firefox afterward. The host timer begins immediately before QEMU launch and uses 0.2-second framebuffer polling.

**Release hold:** even if the policy shortens the first frame, it needs independent 4K video, HTTPS, GPU/i915, physical Acer and UEFI validation before production use. It is not valid to infer <3 seconds on a physical 2010 Acer from fast VM runner samples. All current versions still fail the 384MiB full-RAM Firefox target because the compressed system root alone is ~664MiB.

Keep [v122 experimental release](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v122-direct-fast-codec-experimental) and separate [v115 recovery ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v114-fast-verification-experimental).
