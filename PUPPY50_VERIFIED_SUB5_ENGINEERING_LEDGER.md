# Puppy50 / Firefox — verified cold-boot optimization ledger (2026-11-13)

**RELEASE GATE: NOT UNDER FIVE SECONDS.** Every numerical first-frame time in this file is a **real Firefox UI framebuffer frame measured from host monotonic time immediately BEFORE starting a new QEMU process**. They are **NOT** physical Acer cold-power-on measurements. All named matched tests use QEMU on the same CI host during that one workflow, 2 virtual CPUs with Westmere/i3-540-conservative feature mask, 3GiB RAM, BIOS AHCI optical media, 0.2-second visual polling. Different workflow runners are not directly comparable.

## Current known dependable downloadable artifact

[Published v122 LZ4 ISO and ZIP, or separate smaller Zstandard ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v122-direct-fast-codec-experimental). Its independent release pipeline booted exact shipping bytes under BIOS and UEFI, verified the entire SquashFS migrated into RAM by checksum, removed virtual boot media only after RAM READY, and obtained real HTTP 200 from Firefox afterwards. The matched 6-boot v122 test measured **6.755s LZ4 mean**, **7.385s Zstd mean** and **7.955s exact v117 baseline**. These are *experimental*, not certified hardware images or five-second builds.

## Measurement ledger — positive changes and non-wins

| Version / actual run | Matched baseline | Candidate | Difference | Interpretation |
|---|---:|---:|---:|---|
| [v120 bypass LightDM](https://github.com/74127418528426leo-del/Test/actions/runs/43497790398) | 7.290 | 6.965 | +0.325 | Candidate 2/2 correct Firefox/RAM/HTTP |
| [v121 start direct X11 at basic.target](https://github.com/74127418528426leo-del/Test/actions/runs/43498990765) | 8.095 | 7.280 | +0.815 | 4 matched functional boots |
| [v122 LZ4+early X11](https://github.com/74127418528426leo-del/Test/actions/runs/43499812972) | 7.955 | 6.755 | +1.200 | LZ4 ~919MiB compressed; Zstd ~664MiB |
| [v127 early Firefox parallel with WM](https://github.com/74127418528426leo-del/Test/actions/runs/43505491538) | 8.830 | 8.515 | +0.315 | Full RAM and HTTP passed |
| [v128 pre-create Live user](https://github.com/74127418528426leo-del/Test/actions/runs/43506349966) | 8.615 | 8.540 | +0.075 | Negligible |
| [v130 skip global udev settle](https://github.com/74127418528426leo-del/Test/actions/runs/43510839117) | 7.720 | 7.705 | +0.015 | Negligible; do not prioritize |
| [v131 96MiB libxul readahead](https://github.com/74127418528426leo-del/Test/actions/runs/43511500652) | 6.915 | 6.465 | +0.450 | 4/4 functional boots; keep |
| [v132 unchanged v122 ISO, 2 vs 4 vCPUs](https://github.com/74127418528426leo-del/Test/actions/runs/43511809794) | 8.125 | 8.275 | **−0.150** | Four vCPUs slower on this runner |
| [v133 96 vs 256MiB libxul](https://github.com/74127418528426leo-del/Test/actions/runs/43513699520) | 8.860 | 8.615 | +0.245 | 4/4 functional after correcting reporter |
| [v134 Zstd vs LZ4 with same libxul prefetch](https://github.com/74127418528426leo-del/Test/actions/runs/43513127128) | 6.300 | 6.235 | +0.065 | LZ4 speed gain minor vs +255MiB RAM |
| [v135 early localhost mapping](https://github.com/74127418528426leo-del/Test/actions/runs/43513747035) | 7.225 | 6.815 | +0.410 | 4/4 functional; retain if reproducible |
| [v136 256MiB plus hostname](https://github.com/74127418528426leo-del/Test/actions/runs/43519084792) | 7.330 | 6.995 | +0.335 | 4/4 matched local VM success, but see independent failure below |
| [v137 defer Openbox 2s behind Firefox](https://github.com/74127418528426leo-del/Test/actions/runs/43519373003) | 8.025 | 7.820 | +0.205 | 4/4 functional; utility must remain available |
| [v139 explicit empty Firefox profile](https://github.com/74127418528426leo-del/Test/actions/runs/43519754016) | 7.910 | 7.700 | +0.210 | Nonroot fresh profile; no credentials imported |
| [v141 -5 Firefox nice first attempt](https://github.com/74127418528426leo-del/Test/actions/runs/43520672529) | 7.625 raw | 7.130 raw | +0.495 raw | Actual Firefox -5 verified; reporter failed because of misplaced word boundary, corrected repeat not yet certified |

All "difference" values above are from **within** that experiment; DO NOT sum or compare their raw means across different GitHub hosts. Even the fastest single measured 6.11s v134 run is **not** a verified five-second OS.

## Failed, unproven, or unsafe assumptions

- [v123 pre-systemd Xorg initially failed](https://github.com/74127418528426leo-del/Test/actions/runs/43500793748). Later early-frame successes were initially false: LightDM had actually started and displayed Firefox. Followup v125 DRM `bochs` initialization and v126 preserving the X11 socket across switch-root fixed that particular problem.
- [v129 software WebRender experiment](https://github.com/74127418528426leo-del/Test/actions/runs/43509153482): browser preference not verified applied, so do **not** claim it accelerated compositor startup.
- [v138 Firefox omni.ja read ahead](https://github.com/74127418528426leo-del/Test/actions/runs/43519545373): candidate's `P50_V138_OMNI_READAHEAD_DONE` marker absent. Even with displayed candidate frames, the intended optimization did not complete and is **rejected**.
- [v140 alternate LZ4 initrd compression](https://github.com/74127418528426leo-del/Test/actions/runs/43520090627): candidate failed actual visible Firefox / safe media ejection. **Do not release.**
- [v142 tty1 getty mask A-B-B-A](https://github.com/74127418528426leo-del/Test/actions/runs/43521536538): two candidate Firefox frames 7.82 and 7.99s, but second baseline became visually unresponsive, invalidating a complete paired timing comparison. The candidate itself requires independent BIOS/UEFI reliability checks.
- [Independent v136 release smoke](https://github.com/74127418528426leo-del/Test/actions/runs/43520338227) failed: neither Firefox's visible frame nor the benchmark's RAM-ready gate was observed despite guest serial indicating **`P50_STAGE_COPY_VERIFIED`, `P50_STAGE_READY`, early secure Xorg and actual nonroot Firefox processes**. [Captured original screenshots audit](https://github.com/74127418528426leo-del/Test/actions/runs/43521213508) shows an almost-black 1280×800 framebuffer with sparse gray console text even after 70 seconds. Suspect a Linux tty1 getty vs early Xorg VT ownership conflict, **unconfirmed until candidate-only repetitions pass**. The v136 publication workflow correctly stopped; **NO v136 release exists**.
- The original v115 independent recovery ISO is still required on **separate** storage; the fast BIOS Shift-key rescue menu is not independently proven on actual hardware.
- Virtual QEMU network/HTTP does not certify actual Wi-Fi, Acer graphics/firmware, 4K video, dual monitors or every site.
- 384MiB **cannot** hold the current compressed 664MiB Zstd root and modern Firefox with its working memory.

## Active reliability/optimization decision

The pending [v141 corrected nice test](https://github.com/74127418528426leo-del/Test/actions/runs/43521736672), [v143 combined build](https://github.com/74127418528426leo-del/Test/actions/runs/43521942541), [v144 Xorg VT7 test](https://github.com/74127418528426leo-del/Test/actions/runs/43522338499), and [v145 independent VT1 candidate-only BIOS/UEFI](https://github.com/74127418528426leo-del/Test/actions/runs/43522510925) must be judged by **actual post-QEMU cold Firefox frames, verified RAM copy, no late LightDM, and real post-ejection HTTP200**. A V143 independent candidate-only BIOS/UEFI test was also launched at https://github.com/74127418528426leo-del/Test/actions/runs/43522612660 . Do not endorse any unfinished run.

**Release threshold:** repeated candidate boots **strictly below 5.00s**, genuine full Firefox GUI, functional TLS/networking, checksum-verified RAM migration before ejection, and successful independent BIOS/UEFI exact-byte smoke. For claims specific to the user's Acer, physically verify its power-on and all device drivers as a separate step. Never hide the still-much-later RAM READY time behind an early-browser-frame score.
