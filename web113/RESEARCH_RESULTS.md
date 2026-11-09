# Puppy50 v113 startup research

The public v112 ISO is the baseline: SHA-256 `317999f51e47698d90889b129e9f74bbbefaa382b4d481f4da32016861d8ddc7`. The eight-second target has not yet been demonstrated. These are experimental comparisons; none demonstrates an eight-second system.

Each row below compares v112 and one candidate in A–B–B–A order on the same QEMU/KVM host, using two virtual CPUs, 3 GiB RAM, BIOS and virtual USB limited to 30 MiB/s. Timings begin immediately before QEMU launch; they do not include physical power-on. Two samples per image and approximately 0.8-second home-frame polling limit precision. Guest CPU feature restrictions do not reproduce the speed of a physical Intel i3-540. JavaScript response includes automated URL entry, performed only after the home frame is detected.

| Experiment | Baseline home | Candidate home | Baseline JS response | Candidate JS response | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Remove global early udev settle | 15.42 s | 15.01 s | 18.40 s | 18.02 s | Below frame-sampling resolution; retain the wait. |
| Prefetch only Firefox's main library | 15.47 s | 15.91 s | 18.77 s | 18.99 s | No improvement; RAM-ready was 1.48 s later. |
| Prefetch Firefox archive files | 15.48 s | 15.47 s | 18.70 s | 18.68 s | No measurable improvement. |
| Prefetch library and archives | 15.52 s | 17.08 s | 18.83 s | 20.27 s | Slower; not adopted. |
| Start LightDM without waiting for user-sessions | 16.27 s | 16.27 s | 19.60 s | 19.38 s | Corrected runtime ordering was verified; no meaningful first-frame improvement. |
| Start LightDM and D-Bus earlier | 15.52 s | 15.46 s | 18.82 s | 18.56 s | Corrected runtime ordering was verified; no meaningful first-frame improvement. |
| Recompress the main initramfs archive at Zstd 19 | 16.36 s | 15.93 s | 19.67 s | 19.25 s | Boot archive 6.23 MiB smaller; timing difference is less than one polling interval. |
| Also compress early module archive | 15.50 s | 15.47 s | 18.84 s | 18.87 s | Driver archive shrank by only 0.19 MiB; no measurable gain. |
| SquashFS 64 KiB blocks | 15.48 s | 16.35 s | 18.94 s | 19.57 s | Slower, ISO increased to 912.31 MiB. |
| SquashFS 32 KiB blocks | 15.85 s | 16.26 s | 19.06 s | 19.38 s | No improvement, ISO increased to 932.31 MiB. |
| SquashFS 16 KiB blocks | 16.34 s | 17.17 s | 19.89 s | 20.60 s | Slower, ISO increased to 956.31 MiB. |

## Deferred network-driver prototype

The local-media prototype removes 199 network driver files only from the early initramfs; each was independently checked byte-for-byte against its copy in the unchanged live root. CPU microcode, kernel, root filesystem, boot menus and full-RAM fallback initramfs were unchanged. In the fast path, network drivers then load after the root mounts. The prototype also added a serial diagnostic; that diagnostic produced an unsupported BusyBox `ip` usage message. A cleaner candidate retains the exact original compressed main archive and contains no added serial diagnostic.

In the initial A–B–B–A comparison, first home averaged 15.50 s for v112 versus 14.62 s for the prototype, with 0.8 s frame polling. A separate A–B–B–A–A–B repeat with 0.2 s between frame polls (plus capture overhead) recorded 15.82 s versus 15.18 s, and local JavaScript response averaged 19.08 s versus 18.44 s. These are only two and three samples per image, respectively. Both tests used the same virtual configuration stated above. Physical power-on and actual i3-540 performance were not measured.

The instrumented prototype also passed five VM scenarios: BIOS USB at 2 GiB; UEFI USB offline; UEFI optical media online; BIOS full-RAM-first fallback; and restored HTTPS after a simulated outage. In the Fast Start cases it signaled a verified RAM copy and allowed browser interaction after virtual media removal. The emulated e1000 driver was observed after root mounting, but physical Wi-Fi and other real adapters were not tested. Network-root/PXE boot may need the deferred drivers before the root is available, so use the original full-RAM fallback for such experiments. The root filesystem is 696,545,280 bytes (about 664 MiB) and therefore cannot itself fit entirely into 384 MiB RAM in this design.

[Prototype benchmark](https://github.com/74127418528426leo-del/Test/actions/runs/42534368869) · [Finer repeat](https://github.com/74127418528426leo-del/Test/actions/runs/42535159700) · [Five VM scenarios](https://github.com/74127418528426leo-del/Test/actions/runs/42535186177) · [Independent image audit](https://github.com/74127418528426leo-del/Test/actions/runs/42535323256) · [Corrected Firefox preference tests](https://github.com/74127418528426leo-del/Test/actions/runs/42535424434)

## Exact clean candidate results

The clean local-media image is SHA-256 `4e6dc9b9d1f8f416b47ea046ffcfc5f1c6a7a732dc9ac0e67ff49bd53d271ea1`, 906,297,344 bytes (864.31 MiB). Its independent audit confirmed the same compressed main archive, kernel, CPU microcode, root filesystem, boot menus, and full-RAM fallback as v112, 199 byte-verified late-root driver copies, and all 293 media checksums.

A first A–B–B–A comparison with 0.2 s polling plus capture overhead measured 14.90 s versus 14.82 s for the first frame and 18.07 s versus 17.97 s for the JavaScript response. A separate A–B–B–A–A–B repeat measured 16.26 s versus 15.70 s for the frame, 19.70 s versus 19.07 s for the JavaScript response, and 37.71 s versus 37.08 s for RAM readiness. The first gain is below the sampling resolution; the repeat suggests a modest gain in that VM. Each row compares images only within the same host. The small sample and host differences do not establish physical Acer performance.

At 3 GiB, separate UEFI offline USB, UEFI online optical, BIOS full-RAM fallback, and BIOS connectivity-restoration VMs passed and exercised Firefox after virtual media removal. One BIOS USB 2 GiB VM opened Firefox but declined RAM migration due to insufficient available memory plus reserve; the USB stayed attached. At 1 and 1.5 GiB, a local page responded in Firefox before USB removal but RAM migration failed. At 384 MiB, the screenshot showed initramfs unpacking failure and a kernel panic; no browser was reached in 120 seconds. These are observed test outcomes, not universal memory minima.

[Clean initial comparison](https://github.com/74127418528426leo-del/Test/actions/runs/42535754369) · [Clean repeat](https://github.com/74127418528426leo-del/Test/actions/runs/42536479145) · [3 GiB passes and 2 GiB failure](https://github.com/74127418528426leo-del/Test/actions/runs/42536475888) · [Low-memory observations](https://github.com/74127418528426leo-del/Test/actions/runs/42536910497) · [Clean independent audit](https://github.com/74127418528426leo-del/Test/actions/runs/42536473883) · [Firefox preference repeat](https://github.com/74127418528426leo-del/Test/actions/runs/42536105814)

## Follow-up: 2 GiB and a direct desktop experiment

The exact clean image's separate 2 GiB validation failed its memory-reserve check once. A later same-host A–B–B–A test used diagnostic copies of v112 and the clean layout, adding only a report of the existing guard values; both samples of each diagnostic image completed the RAM copy and worked after virtual USB removal. At the guard, available memory ranged from 1,143,080 to 1,216,324 KiB, above the required 680,220 KiB root copy plus the unchanged 393,216 KiB reserve. These diagnostic copies are not identical to the release ISO. Together with the earlier failure, this demonstrates variability rather than a reliable 2 GiB minimum or a proven regression.

A separate A–B–B–A 2 GiB comparison of v112 against the Firefox preallocation-disabled test image also passed RAM migration in all four samples. This small test does not establish a memory improvement, and the 3 GiB finer timing repeat found no meaningful speed benefit. The setting is not included in the clean candidate.

The first direct X11-session experiment failed to show Firefox. The audit revealed that the original display manager was still being started by a diagnostic service. After isolating the old display manager, the second attempt also failed: its journal showed that systemd tried to resolve the live user before the preflight had created that user. A third test moved user preparation into a separate root service and produced a functioning non-root Firefox session with the network applet, local JavaScript response, and browser input after RAM migration and virtual USB removal. In its A–B–B–A comparison at 0.2 s frame-poll sleep, v112 averaged 15.08 s to the home frame and the direct session averaged 15.07 s; JavaScript response averaged 18.28 s versus 18.27 s. The differences are below the test resolution, so the direct-session architecture is not included in the clean candidate.

[2 GiB guard investigation](https://github.com/74127418528426leo-del/Test/actions/runs/42536785403) · [2 GiB Firefox preallocation comparison](https://github.com/74127418528426leo-del/Test/actions/runs/42536862696) · [Initial direct-session attempt](https://github.com/74127418528426leo-del/Test/actions/runs/42536424516) · [Isolated direct-session diagnostic](https://github.com/74127418528426leo-del/Test/actions/runs/42537043469) · [Prepared direct-session comparison](https://github.com/74127418528426leo-del/Test/actions/runs/42537708256)

## Boot timing profile

A separate, lightly instrumented v112 fast boot measured the device-mapper `udevadm settle` at 0.03 s in each of two VM runs (guest uptime 1.99→2.02 s and 1.95→1.98 s). In one run the live root hook occurred at guest uptime 2.08 s, LightDM preflight at 5.38–5.41 s, and the Firefox launch command at 7.50 s. The first Firefox home frame was seen at 15.46 s on the host clock. Guest uptime and host launch time have different origins and must not be subtracted directly; the gap before the kernel clock includes virtual firmware, boot menu, and image loading.

The profile's candidate and baseline home means differed by only 0.05 s, below the polling interval, so the diagnostics did not show a meaningful startup change in this small sample. The diagnostics show Firefox running as the unprivileged `user` account with content processes. They are not a substitute for a full Firefox sandbox audit.

## Test boundaries and discarded approaches

- The first attempt at early LightDM scheduling did not actually remove an original unit dependency. Its timing is not evidence for the intended change. A corrected unit-copy experiment verified the runtime dependency was absent and confirmed the non-root Firefox, network applet, panel, and RAM status processes; the corrected results are in the table.
- Early background reads initiated from the initramfs were not instrumented well enough to prove that all files remained accessible across root switching. Their results are not used to justify a speed claim. The later systemd-prefetch experiments logged successful reads and are the ones reported above.
- The initial Firefox spare-process preference experiments failed their observation check because it searched the wrong Firefox profile location. Their timings remain invalid. Corrected experiments confirmed the actual setting in the XDG profile; disabling preallocation showed a 0.87 s home-frame gain in two samples per image at 0.8 s polling, while delaying it by 8 s showed no useful gain. A finer A–B–B–A–A–B repeat measured 15.78 s versus 15.75 s for the first frame and 18.96 s versus 18.94 s for JavaScript response; the change is not a demonstrated speedup.
- Higher Zstd compression was applied to an identical uncompressed main initramfs archive. The early CPU microcode prefix, root filesystem, full recovery initramfs, and all 293 media checksums were verified. The compressed module archive experiment also round-tripped its module archive byte-for-byte. Virtual boot does not prove every physical machine's decompressor or firmware compatibility.
- Smaller-block candidates were checked by extracting the filesystems and comparing contents and metadata in both directions. No measured speed improvement justifies replacing v112 with these larger images.
- These results do not prove 384 MiB Firefox operation, actual Acer startup time, physical Wi-Fi compatibility, PXE/network-root boot, or real-world 4K streaming. Keep the USB attached until the green RAM-ready message in Fast Start; the full-RAM-first fallback has no green indicator.

[Detailed timing and udev experiments](https://github.com/74127418528426leo-del/Test/actions/runs/42532374463) · [Verified prefetch comparisons](https://github.com/74127418528426leo-del/Test/actions/runs/42532660203) · [Corrected display ordering](https://github.com/74127418528426leo-del/Test/actions/runs/42533723169) · [Initramfs compression](https://github.com/74127418528426leo-del/Test/actions/runs/42533207205) · [Smaller filesystem blocks](https://github.com/74127418528426leo-del/Test/actions/runs/42533808494) · [Current v112 release and durable evidence](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v112-fast-read-experimental)
