# Puppy50 Firefox v100 — repeated QEMU test findings

**Actual run:** https://github.com/74127418528426leo-del/Test/actions/runs/41748934221

## Three real-guest tests, identical maintained Firefox, no zram

| Guest RAM | Browser's external example.com page actually visible? | First screenshot with public page | Lowest sampled MemAvailable | OOM kills |
|---|---|---|---:|---:|
| 2,048 MiB trial A | No: local Puppy50 homepage still visible at 300s | Not seen in 300s | 14.23 MiB | 0 |
| 2,048 MiB trial B | Yes | At 260s | 146.29 MiB | 0 |
| 2,560 MiB control | Yes | At 185s | 545.11 MiB | 0 |

All guests completed CA-validated HTTPS in Linux, launched Firefox as non-root, and survived the original Live CD ejection without a VM hard drive. That is independent of external browser page rendering and is NOT proof of physical Wi-Fi connectivity.

The failing 2048 MiB trial's `/proc/pressure/memory` some 10-second average reached 59.51% in eight sampled windows, and reported no OOM kill. Firefox remained onscreen but could not finish navigating externally. The successful 2048 MiB trial retained more available memory and eventually loaded the page. These are small-sample observations: **2 GiB is experimentally possible, not reliably proven.**

## Why next investigate the ISO itself

The real v101 audit measured:
- compressed SquashFS **844,705,792 bytes (805.57 MiB)**
- total ISO **990,183,424 bytes (944.31 MiB)**
- regular files inside SquashFS **2,159,657,540 uncompressed bytes (2059.61 MiB)**
- `usr/lib/firmware` **841.62 uncompressed MiB**, including AMD/NVIDIA GPU firmware unneeded on Intel graphics
- Firefox runtime **294.21 uncompressed MiB**
- duplicate boot initramfs inside root **113.04 uncompressed MiB**

These are uncompressed subdirectory sizes. Compressed savings MUST be measured by building an ISO, not inferred directly. Do NOT strip Intel graphics or Wi-Fi firmware and do NOT disable HTTPS checks or Firefox sandbox.

Read-only v101 inventory: https://github.com/74127418528426leo-del/Test/actions/runs/41750712402

## Next v102

Make a separate Intel-graphics-only experimental Live ISO removing only AMDGPU/NVIDIA GPU firmware and redundant kernel/initramfs files INSIDE the read-only root, while preserving actual external Live boot files, Firefox, TLS and every Wi-Fi firmware candidate. Compare exact compressed ISO bytes, then repeat 2GiB/2.5GiB KVM Firefox external-site tests. Users on AMD/NVIDIA-only graphics must use the existing full-hardware v93 release.

**No guarantee of any-network compatibility, real physical Wi-Fi or 384 MiB Firefox.**
