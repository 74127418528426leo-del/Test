# Puppy50 v112 startup research

All times below use an identical within-row QEMU/KVM environment, with virtual BIOS, two vCPUs, 3 GiB RAM, and a 30 MiB/s USB read cap. Timers begin just before QEMU launch, not at physical power-on. Each image ran twice in alternating A–B–B–A order. First-frame measurements are sampled about every 0.8 seconds. Virtual CPU feature restrictions do not model an old i3 CPU's speed.

| Root layout | v111 mean home | Candidate mean home | v111 RAM ready | Candidate RAM ready | Finding |
| --- | ---: | ---: | ---: | ---: | --- |
| Repacked 1 MiB blocks (control) | 17.12 s | 17.08 s | 35.27 s | 35.21 s | No meaningful change |
| 128 KiB blocks | 16.66 s | 15.43 s | 35.80 s | 37.58 s | Faster first frame, larger ISO and later RAM ready |
| 256 KiB blocks | 17.16 s | 15.47 s | 35.83 s | 36.63 s | Faster first frame, 5 MiB smaller ISO; selected |

The 256 KiB candidate contains the same unpacked filesystem contents and checked metadata as v111. Its kernel, boot menus, fast initramfs, and full-RAM fallback initramfs are byte-identical to v111. The exact tested ISO SHA-256 is `317999f51e47698d90889b129e9f74bbbefaa382b4d481f4da32016861d8ddc7`.

A separate 256 KiB versus v111 A–B–B–A interaction comparison detected the home frame at 17.32 versus 16.34 seconds, then typed a local URL and activated a JavaScript button. The visible response averaged 20.88 versus 19.66 seconds from QEMU launch. The test starts typing after detecting the home frame, so this is a repeatable scripted task, not a direct measurement of the earliest possible response. USB remained attached and RAM copying was not yet complete during the interaction. RAM-ready means in this separate test were 37.39 versus 37.93 seconds.

Virtual validation covered BIOS USB at 2 GiB, UEFI offline USB, UEFI online optical, full-RAM fallback, and HTTPS restoration after a deliberate outage. The boot media was removed only after RAM migration and the browser was exercised afterward. A byte- and metadata-level audit independently compared the two unpacked root filesystems and checked all 293 ISO checksum entries.

The first attempt to suppress Firefox's first-run page failed safely in a test-only image: Debian's Firefox distribution directory is a relative symlink. The root cause was identified by inspecting the real filesystem. That patch is not present in the selected v112 image.

An early-payload audit found 865 early kernel module files identical to late-root copies, but byte identity alone does not prove safe removal: devices may require drivers or firmware before the root is available and may not reprobe later. Some graphics firmware was not present at the same late-root paths. No broad early-module or firmware removal was adopted on this evidence.

[Block size experiment](https://github.com/74127418528426leo-del/Test/actions/runs/42479601193) · [Interactive comparison](https://github.com/74127418528426leo-del/Test/actions/runs/42480553607) · [Five validation scenarios](https://github.com/74127418528426leo-del/Test/actions/runs/42480523148) · [Independent audit](https://github.com/74127418528426leo-del/Test/actions/runs/42480757160) · [Early payload audit](https://github.com/74127418528426leo-del/Test/actions/runs/42480267230)

The eight-second goal, 384 MiB Firefox goal, physical Acer and physical Wi-Fi verification, and smooth 4K playback remain unverified or unmet. Results must not be presented as physical-hardware timings.
