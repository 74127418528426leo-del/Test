# Puppy50 v81 — Verified Linux memory-pressure measurement and Firefox webpage behavior

**Completed real KVM workflow:** https://github.com/74127418528426leo-del/Test/actions/runs/41685756301

## Controlled source and instrumentation

Two KVM guests used the **same** disposable v78 complete-APK image plus one read-only 10-second memory logger added before Xorg starts. The original kernel, initrd, Firefox, TLS certificate store, and e1000 networking behavior were retained. Both guests operated entirely from RAM, ejected their boot CD, passed guest DHCP and DNS and performed a public HTTPS connection with certificate validation. Guest RAM set to **1024 MiB** or **2048 MiB**, 2 virtual CPUs, same website tile and same QEMU click sequence. Individual GitHub Actions runner hosts may differ.

Telemetry was parsed from the actual guest `/proc/meminfo`, `/proc/vmstat`, `/proc/pressure/memory` if available, and Firefox process `VmRSS` as a deliberately labeled double-counting trend statistic. No user content, usernames or credentials were captured.

## Exact 1 GiB versus 2 GiB results

| Metric | 1024 MiB | 2048 MiB |
|---|---:|---:|
| Actual guest Linux MemTotal | 987,272 KiB | 2,017,924 KiB |
| Actual 10s samples | 30 | 37 |
| Median MemAvailable | **16,912 KiB = 16.5 MiB** | **934,952 KiB = 913.0 MiB** |
| Minimum MemAvailable | **0 KiB** | **748,044 KiB = 730.5 MiB** |
| Ending MemAvailable | **0 KiB** | **922,796 KiB = 901.2 MiB** |
| Configured swap | 0 | 0 |
| Increase in kernel `oom_kill` counter | 0 | 0 |
| Maximum sum of Firefox-process VmRSS (NOT PSS or physical unique memory) | 634,652 KiB | 1,314,916 KiB |
| PSI memory pressure available from this guest kernel | No | No |
| QEMU monitor mouse click emitted | Yes | Yes |
| Firefox visually displays actual Wikipedia page | **NO**; still on Puppy50 homepage at 405s | **YES**; Wikipedia visible at 185s and throughout subsequent captures |

**Actual screenshot SHA-256 from unchanged raw QEMU PPM frames:**

- 1024 MiB at 405 seconds: `ffb3428e5c986ad2b13040fef397afbc735aa462c00f0b1071201fb7695c02da`; user-control homepage remains with Wikipedia hovered
- 2048 MiB at 185/405 seconds: `6ebcd1b10afb784736dc3c22812b2312f0c2d73217413d4954ce2f6f46791c34`; full live Wikipedia multilingual landing page visibly loaded

The KVM integration workflows and both memory-analysis jobs completed successfully. In the 1024 MiB case, the browser-level benchmark script's exit status was **nonzero because the homepage never disappeared**; this was deliberately captured rather than allowed to abort the independent serial-memory parser and raw evidence uploads. The overall v81 diagnostic job's success means the memory instrumentation worked, **not that 1 GiB web browsing succeeded**.

## Causality and limitations

Firefox startup dropped 1024 MiB Linux MemAvailable from 624,664 KiB at boot to 50,884 KiB around 61 seconds and ultimately to 0 KiB. Its *median* 16.5 MiB means the guest spent much of the test near exhaustion. The corresponding 2048 MiB guest retained at least 730.5 MiB despite displaying an actual public site. No OOM-killer events occurred in either guest; lack of OOM kills does **not** demonstrate a healthy browser or absence of memory reclaim stalls.

These observations strongly support RAM pressure as a plausible explanation for 1 GiB unreliability, but do not prove the precise causal mechanism. The kernel did not expose PSI statistics, and this experiment did not capture browser process `Pss`, per-thread scheduler delays, page-fault rates, swap, or browser performance profiles.

An earlier 1 GiB v71 experiment **did** visibly render Wikipedia, so it would be false to say modern Firefox can never work at 1 GiB. The repeated recent experiments indicate it is not *reliably usable* at that RAM setting.

## Correct next engineering decisions

1. **Use 2048 MiB** as the currently verified functional default for experimental modern Firefox browsing and keep the host's remaining RAM/CPU responsiveness in view; a 4 GiB physical host will be tight.
2. At 1024 MiB, examine actual browser memory PSS/USS where guest kernel supports `/proc/[pid]/smaps_rollup`, hard page faults, process CPU delays, and component features; do not disable TLS validation, Firefox sandbox or site isolation to reduce use.
3. Test bounded compressed zram only as a measured experiment, not as RAM creation. It consumes some CPU and real physical RAM, especially relevant on old i3 systems.
4. Keep the **384 MiB** target as a separate RAM-only boot milestone, not a functioning modern full website guarantee. Consider a limited text-only browser as an explicitly different optional fallback.
5. Replace outdated Firefox ESR 140.12.0-r0 with a current security-maintained upstream build via a tracked packaging process before production/public sensitive browsing; the v83 audit confirms the current installed image is stale.
6. Maintain current v70 public experimental release unchanged. User-ready v78 package bundle remains clearly experimental; no direct Wi-Fi network selector, host roaming/captive-portal guarantee or security certification has been demonstrated.

**Key lesson:** compressed ISO size does not equal runtime memory footprint. A user-controlled browser that reliably renders HTTPS websites with adequate memory is more valuable than a byte-smaller but unresponsive ISO.