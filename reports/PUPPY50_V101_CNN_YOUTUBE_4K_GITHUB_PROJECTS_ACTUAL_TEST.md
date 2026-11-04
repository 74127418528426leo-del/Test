# Puppy50 Firefox v101 — Real CNN, YouTube 4K, and GitHub Pages test

**Date:** November 3, 2026 (tests crossed into November 4 UTC). **Live test workflow:** https://github.com/74127418528426leo-del/Test/actions/runs/41751945239

**Method:** actual QEMU/KVM virtual machines with the previously verified v100 diagnostic-only Debian Live Firefox ESR 153.6 ISO, true nonroot Firefox GUI, valid CA-verified guest public HTTPS, virtual e1000 NAT, and 1280×800 virtual graphics. Browser navigated to the real sites through virtual keyboard events. Actual QEMU framebuffer screenshots and guest memory telemetry were examined independently. No swap or zram was enabled.

| Requested page | Guest RAM | Observed result | Lowest MemAvailable | Guest media ejection |
|---|---:|---|---:|---|
| https://www.cnn.com/ | 3072 MiB | News homepage and video previews rendered, consent/privacy modal blocked full reading | 816.00 MiB | Proven |
| https://www.youtube.com/watch?v=TlLmve5I67o | 4096 MiB | YouTube watch page and sidebar loaded, but player required sign-in to confirm not a bot; playback **did not start** | 1612.86 MiB | Not checked due test-harness omission |
| https://3dbibleonline.github.io/john/ | 3072 MiB | John 3D Bible front page, 21 chapter choices and panorama counters appeared | 1007.21 MiB | Proven |
| https://74127418528426leo-del.github.io/BIBLE-3D/ | 4096 MiB | Genesis 1, Scripture City controls, real 3D landscape/landmarks rendered | 1501.36 MiB | Proven |

Each VM reported nonroot Firefox and guest CA-verified public HTTPS. All four tests ended with actual QEMU screenshots and 19 guest memory-pressure samples; reported OOM counter was 0 in all four samples series.

## What was NOT verified
- **YouTube 4K 2160p playback: FAILED TO TEST** due site-enforced anti-bot sign-in screen. Firefox console produced videoHeight=0, currentTime=0 and droppedVideoFrames=0; these are NOT proof of decoded playback.
- YouTube QEMU media-ejection gate FAILED because original v101 test schedule omitted the 310s event. This was a test-harness bug, not a guest OS crash. Script corrected in a subsequent code commit, but YouTube was NOT rerun after correction. Other three VMs did prove surviving boot-media removal.
- CNN privacy terms were **not accepted**; no premium CNN stream was tested.
- John panorama, BIBLE-3D walking or interactive camera actions were not exercised in this smoke test. The scene itself clearly rendered.
- No actual physical Intel graphics acceleration, 4K monitor, physical Wi-Fi, or user Acer hardware tested. QEMU only has emulated graphics and was limited to 1280×800, so a 4K smoothly decoded playback claim would be invalid even if a video player had appeared.

## Artifacts and evidence

- [Real KVM CNN screenshot, serial, report](https://github.com/74127418528426leo-del/Test/actions/runs/41751945239/artifacts/13287261522)
- [Real KVM YouTube denied video screen and actual DevTools console](https://github.com/74127418528426leo-del/Test/actions/runs/41751945239/artifacts/13286967630)
- [Real KVM John Gospel homepage](https://github.com/74127418528426leo-del/Test/actions/runs/41751945239/artifacts/13286967321)
- [Real KVM Scripture City Genesis 3D scene](https://github.com/74127418528426leo-del/Test/actions/runs/41751945239/artifacts/13286317336)
- [v101 repeatable test code](https://github.com/74127418528426leo-del/Test/tree/puppy50-v101-real-sites-cnn-youtube-bible/web101)

## Decision

**Accept real browsing results for CNN, John and BIBLE-3D on assigned RAM only, not general production compatibility.** Do not promote an ISO or claim 4K video capability based on the YouTube sample, because YouTube's anti-bot challenge prevented playback. Test these destinations directly on the intended Acer hardware for real-world CPU/GPU responsiveness and network reliability. A dedicated 4K test should be conducted on legitimate logged-in/authorized access, with YouTube Stats for Nerds showing current 3840×2160 resolution, active increasing playback time, and measured dropped frames.

Existing [v93 experimental Firefox ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-debian-live-v93-maintained-https) remains the public browser-focused Live OS download; v100/v101 are diagnostics/tests, not release promotions.
