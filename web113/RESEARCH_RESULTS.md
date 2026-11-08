# Puppy50 v113 startup research

The public v112 ISO is the baseline: SHA-256 `317999f51e47698d90889b129e9f74bbbefaa382b4d481f4da32016861d8ddc7`. The eight-second target has not yet been demonstrated. These are experimental comparisons, not a new published system image.

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

## Boot timing profile

A separate, lightly instrumented v112 fast boot measured the device-mapper `udevadm settle` at 0.03 s in each of two VM runs (guest uptime 1.99→2.02 s and 1.95→1.98 s). In one run the live root hook occurred at guest uptime 2.08 s, LightDM preflight at 5.38–5.41 s, and the Firefox launch command at 7.50 s. The first Firefox home frame was seen at 15.46 s on the host clock. Guest uptime and host launch time have different origins and must not be subtracted directly; the gap before the kernel clock includes virtual firmware, boot menu, and image loading.

The profile's candidate and baseline home means differed by only 0.05 s, below the polling interval, so the diagnostics did not show a meaningful startup change in this small sample. The diagnostics show Firefox running as the unprivileged `user` account with content processes. They are not a substitute for a full Firefox sandbox audit.

## Test boundaries and discarded approaches

- The first attempt at early LightDM scheduling did not actually remove an original unit dependency. Its timing is not evidence for the intended change. A corrected unit-copy experiment verified the runtime dependency was absent and confirmed the non-root Firefox, network applet, panel, and RAM status processes; the corrected results are in the table.
- Early background reads initiated from the initramfs were not instrumented well enough to prove that all files remained accessible across root switching. Their results are not used to justify a speed claim. The later systemd-prefetch experiments logged successful reads and are the ones reported above.
- Firefox spare-process preference experiments reached and interacted with the browser but failed their preference-observation check. Their timings are invalid for evaluating the setting until the policy and live preference are independently verified.
- Higher Zstd compression was applied to an identical uncompressed main initramfs archive. The early CPU microcode prefix, root filesystem, full recovery initramfs, and all 293 media checksums were verified. The compressed module archive experiment also round-tripped its module archive byte-for-byte. Virtual boot does not prove every physical machine's decompressor or firmware compatibility.
- Smaller-block candidates were checked by extracting the filesystems and comparing contents and metadata in both directions. No measured speed improvement justifies replacing v112 with these larger images.
- These results do not prove 384 MiB Firefox operation, actual Acer startup time, physical Wi-Fi compatibility, PXE/network-root boot, or real-world 4K streaming. Keep the USB attached until the green RAM-ready message in Fast Start; the full-RAM-first fallback has no green indicator.

[Detailed timing and udev experiments](https://github.com/74127418528426leo-del/Test/actions/runs/42532374463) · [Verified prefetch comparisons](https://github.com/74127418528426leo-del/Test/actions/runs/42532660203) · [Corrected display ordering](https://github.com/74127418528426leo-del/Test/actions/runs/42533723169) · [Initramfs compression](https://github.com/74127418528426leo-del/Test/actions/runs/42533207205) · [Smaller filesystem blocks](https://github.com/74127418528426leo-del/Test/actions/runs/42533808494) · [Current v112 release and durable evidence](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v112-fast-read-experimental)
