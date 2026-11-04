# Puppy50 Firefox v100 — controlled 2GiB browser reliability investigation

**Actual date:** November 3–4, 2026.
**Run:** https://github.com/74127418528426leo-del/Test/actions/runs/41748934221
**Source:** diagnostic-only addition to previously working v91 Debian 13 Live Firefox ESR 153.6.0; *no zram, no swap, no modifications to Firefox, NetworkManager, or CA bundle*. Build checked cryptographic hashes of browser and network security files and preserved bootloader.

## Genuine QEMU-KVM guest evidence

| Test | 100s | 185s | 300s | Min MemAvailable | Guest HTTPS | OOM indicator |
|---|---|---|---|---:|---|---|
| 2048 MiB trial A | Local Puppy50 homepage | Local homepage | **Local homepage; navigation failed** | **14.23 MiB** | CA-verified direct PASS | no OOM reported in 8 samples; telemetry stopped early |
| 2048 MiB trial B | Local Puppy50 homepage | Address bar example.com, local page still visible | **Public example.com webpage rendered** | **146.29 MiB** | CA-verified direct PASS | 0 over 17 samples |
| 2560 MiB control | Local Puppy50 homepage | **Public example.com webpage rendered** | Public example.com remained visible | **545.11 MiB** | CA-verified direct PASS | 0 over 18 samples |

Both 2GiB trials had real Firefox process and full toram media-ejection survival. **One of two succeeded**, demonstrating intermittency, not a reliable 2GiB minimum. The visual outcomes were checked from actual guest screenshots, not inferred from QMP key events or curl. The difference in minimum available RAM strongly suggests pressure, but only 8 samples were retained in the unsuccessful trial, and causality is not proven.

The 2560 MiB control had substantially more headroom. Prior v93 and v94 successful real-browser tests at 2560 MiB reinforce that configuration, but no formal statistical reliability target or independent physical Acer hardware test has been achieved.

## Rejected v99 zram hypothesis

The separate preceding v99 test [41747335187](https://github.com/74127418528426leo-del/Test/actions/runs/41747335187) enabled actual 1 GiB logical zram LZ4 swap entirely within RAM. At 2GiB physical, it held ~1016 MiB original pages using ~1010 MiB physical. This near-incompressible swap was not memory-efficient. It eventually displayed example.com by 300s but was markedly slower than the unmodified 2GiB VM in that one comparison. **Do not promote zram v99.**

## Next engineering priority

Measure and reduce the baseline RAM footprint of Debian Live + Firefox on startup; prioritize right-sizing the RAM-resident squashfs, user services, fonts/firmware and Firefox process lifecycle **without weakening TLS verification, sandboxing or cutting essential Wi-Fi support**. Test three or more 2048-MiB real-website trials with QEMU, preserve originals, monitor memory pressure and require actual page screenshots. Only upgrade the user-facing ISO after repeated success and physical hardware checks.

The previously published [v93 Firefox experimental prerelease](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-debian-live-v93-maintained-https) is unchanged. No physical Wi-Fi or all-network compatibility has been proved. The 384MiB modern Firefox target is unmet.

## Immutable archived evidence

- 2048 A (failure): https://github.com/74127418528426leo-del/Test/actions/runs/41748934221/artifacts/13285044013
- 2048 B (success): https://github.com/74127418528426leo-del/Test/actions/runs/41748934221/artifacts/13284813494
- 2560 control (success): https://github.com/74127418528426leo-del/Test/actions/runs/41748934221/artifacts/13285408791
- v100 build hash audit: https://github.com/74127418528426leo-del/Test/actions/runs/41748934221/artifacts/13285186292

**Research build only; not recommended for banking, confidential logins, or production deployment.**
