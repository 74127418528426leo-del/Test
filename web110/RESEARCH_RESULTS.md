# Puppy50 startup research — November 8, 2026

## Measurement and limitations

The target is eight seconds from immediately before QEMU launch to a visible, real Firefox home page. The timer includes virtual firmware and the boot menu but does not include a physical computer's power-on self-test. Input, fresh-page loading and HTTPS were exercised only after the staged RAM transition and virtual media removal, not at the instant of the first frame. Tests below use a two-vCPU, 3-GiB KVM guest with a conservative old-Intel feature mask, BIOS, and a 30 MiB/s virtual USB cap. Each A–B–B–A comparison uses two samples per image and approximately 0.8-second frame sampling. Host CPU speeds vary; compare only within each row.

| Independent same-host comparison | v109 mean | Test image mean | Finding |
| --- | ---: | ---: | --- |
| Shorter USB scan delay | 19.535 s | 18.300 s | About 1.235 s earlier; verified in additional virtual boot tests. |
| Intel-focused early initramfs | 20.580 s | 19.175 s | About 1.405 s earlier; two NVIDIA GSP firmware files omitted only from Fast Start, with the original full initramfs retained for fallback. |
| Prebuilt linker cache | 20.525 s | 20.560 s | No measurable browser improvement; not adopted. |
| Browser-first desktop startup | 19.535 s | 19.480 s | Difference below the sampling interval; not adopted. |
| Combined USB and Intel changes | 19.560 s | 17.085 s | About 2.475 s earlier; RAM-ready means 38.230 s versus 35.740 s. |

The eight-second target and the earlier 384 MiB browser target remain unmet. Real Acer firmware startup, actual USB speed, physical Wi-Fi, graphics, sound and power use were not measured. Virtual CPU feature masking is not a simulation of an i3-540's execution speed.

## Evidence and source

- [USB matched benchmark](https://github.com/74127418528426leo-del/Test/actions/runs/42457412894) and [five virtual validation scenarios](https://github.com/74127418528426leo-del/Test/actions/runs/42458605379).
- [Published v110 USB experiment](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v110-usb-faststart-experimental), SHA-256 `b2f6ce26c4a794d87fd2e29d1d22b7e49a1ee175d58d89f7b72215dd54bc8a9e`.
- [Intel initramfs comparison and BIOS fallback](https://github.com/74127418528426leo-del/Test/actions/runs/42458143496).
- [Linker cache comparison](https://github.com/74127418528426leo-del/Test/actions/runs/42458325361) and [desktop startup ordering comparison](https://github.com/74127418528426leo-del/Test/actions/runs/42458540258).
- [Combined image matched benchmark](https://github.com/74127418528426leo-del/Test/actions/runs/42458887918), SHA-256 `3ead70c1876e0ae02759ffd5887ef89a7e47eb87f4756faba65958bd011101e6`.
- [Startup profile](https://github.com/74127418528426leo-del/Test/actions/runs/42457785214) and [initramfs inventory](https://github.com/74127418528426leo-del/Test/actions/runs/42457846610).

The startup profile found `ldconfig.service` in the systemd critical chain, but masking its rebuild did not improve the measured first Firefox frame; the unchanged cached data was independently compared in the two test boots. The inventory identified approximately 59 MiB of NVIDIA GSP firmware within the early image, while the user's known machine has Intel integrated graphics. This is a rationale for a *test* image, not proof of physical hardware support.

Keep boot media attached until the green RAM-ready message in Fast Start. The full-RAM fallback does not show that notice. Writing an ISO to USB erases the chosen USB drive. All releases are experimental.
