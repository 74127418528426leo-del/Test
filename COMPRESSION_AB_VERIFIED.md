# Puppy50 RAM-root compression A/B — verified real KVM result

Run: https://github.com/74127418528426leo-del/Test/actions/runs/41549643172

A matched QEMU standard VGA firmwareless Firefox root was compressed twice from the same staged files, preserving the same installed browser, kernel, dynamic libraries and Xorg/Openbox dependencies.

| Matched image | Compressed bytes | MiB |
|---|---:|---:|
| XZ, 1MiB blocks | 212,172,800 | 202.34375 |
| Zstandard level 10, 256KiB blocks | 259,674,112 | 247.64453125 |

Zstandard produced **47,501,312 more compressed bytes, 45.30078125 MiB**, than XZ.

## Actual KVM results for Zstandard image
- 384 MiB: the early RAM-copy process was killed; guest serial ended with the lines "Killed" and "PUPPY50_WEB_V45_FAIL_RAM_COPY". RAM-copy and root switch flags were false. Not a RAM-root boot success and not a Firefox success.
- 512 MiB: compressed root copied into guest RAM, root switch succeeded, virtual optical media was ejected, Xorg started and Firefox launch was requested. Do not infer visible or interactive browser success.
- 1024 MiB: compressed root copied, root switch and CD ejection succeeded, Xorg started and Firefox was requested. Browser visibility requires manual screenshot inspection.

The matched XZ baseline previously passed the guest RAM-copy and root-switch gate at **384 MiB** (https://github.com/74127418528426leo-del/Test/actions/runs/41546583445). At that level, its Firefox browser remained black except the mouse cursor. A root copy is not a browser-functionality test.

## Conclusion
For the 384 MiB RAM-only target and this selected compression configuration, XZ is the better choice. Do NOT claim Zstandard is inherently slower or cannot work in other designs: this experiment did not directly measure startup time under equal available memory, CPU utilization, or alternative Zstandard compression levels.

At 384 MiB, the Zstandard image alone left at most 136.355 MiB nominal available; the XZ image left 181.656 MiB. Other kernel, graphics and browser memory costs remain. Favor genuine package elimination and browser working-set reduction rather than increasing the compressed SFS to save speculative decompression time.

The guest had no network, so HTTPS, online browsing, downloads and WebGL were not demonstrated. The firmwareless image is QEMU-specific, not intended for real Intel hardware.
