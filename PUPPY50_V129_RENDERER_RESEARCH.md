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

## Completed four-boot graphics-pref result and independent artifact audit

The first full [v129 A–B–B–A cold-boot test](https://github.com/74127418528426leo-del/Test/actions/runs/43508019175) executed **all four QEMU VMs**. Every VM produced a genuine Firefox home frame, checksum-verifiable RAM-ready, safe boot-media eject and new authenticated HTTP 200 after eject, with zero benchmark errors. **The workflow itself correctly FAILED the stricter release check** because it could not establish that Firefox wrote/retained the requested preference inside its live profile. A separate [independent audit of saved VM serial and results](https://github.com/74127418528426leo-del/Test/actions/runs/43509153482) confirmed that the candidate's `P50_V129_POLICY_BEFORE_BROWSER` marker was present in both candidate boots, but the asynchronous preference reporter never emitted either the observed or missing-preference marker. This is a test-instrumentation gap, not proof that Firefox applied the preference.

| Alternating same-host trial | Genuine first Firefox frame | RAM READY |
| --- | ---: | ---: |
| v127 original graphics pref #1 | 6.97 s | 14.13 s |
| v129 policy written before Firefox #1 | 6.80 s | 13.96 s |
| v129 policy written before Firefox #2 | 6.78 s | 13.92 s |
| v127 original graphics pref #2 | 6.79 s | 13.93 s |
| **v127 mean** | **6.880 s** | **14.030 s** |
| **v129 candidate mean** | **6.790 s** | **13.940 s** |

First-frame mean difference **0.090 seconds** and RAM mean difference **0.090 seconds** are **below the ~0.2s framebuffer polling interval** and not meaningful evidence of a repeatable speedup. One baseline boot (6.79s) was virtually identical to both candidates. The hypothesis that software WebRender would remove a >1-second first-paint stall in this particular QEMU guest was **not supported by this small timing experiment**. The Mozilla issue is valid for its particular Linux CI configuration and cannot automatically be extrapolated to this VM or physical Acer.

**Disposition: do not adopt or release v129**, do not claim that `gfx.webrender.software` was positively verified, and do not claim <3s. The original v127 and released v122 remain available; the public v122 release was not modified. Further browser-pref studies should use a persistent after-switchroot reporter or an explicit about:policies / about:config UI inspection rather than treating an asynchronous migration-service report as reliable.
