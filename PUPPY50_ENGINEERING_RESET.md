# Puppy50: engineering reset, not just another version

## User contract

- Preserve the original BookwormPup64 10.0.12 desktop and original programs.
- The operating-system filesystem files must live in RAM after the boot media has been removed.
- The aspirational physical RAM ceiling is 384 MiB, with Firefox and the desktop still genuinely responsive.
- No hidden disk/USB/network dependence, misleading GPU accounting, silent feature deletion, or merely fake screenshot/process proof.

## The actual measured obstacle

Official ISO SHA256: ae65f6e6d70a96f48bdbb291c2426f8a2fd77a73692e149e81a5eecb6fe7509f.

- Six original complete SquashFS layers: 779,874,304 bytes = 743.746 MiB.
- Original-file-preserving v43 XZ six layers: 658,075,648 bytes = 627.590 MiB.
- Actual reduction in RAM-resident compressed files: 121,798,656 bytes = 116.156 MiB = 15.618%.
- v40 vs v43 late-boot 4GiB MemTotal-MemAvailable estimate: 1,269.25 -> 1,233.71 MiB, only approximately 35.54 MiB improvement. This metric is NOT exact irreducible physical process memory.
- The main v43 OS layer alone is 395,800,576 bytes = 377.465 MiB. This leaves only 6.535 MiB for everything else within a 384MiB physical limit, even with all other app/driver layers omitted.
- Exact same-content files duplicated across layers: <=0.544 MiB uncompressed; no meaningful leverage.
- Full v43 six-layer XZ payload exceeds the entire 384 MiB physical target by 243.590 MiB before kernel and applications.
- Reserving 128 MiB for useful runtime gives a compressed payload budget <=256 MiB. We would need another 59.21% savings from the verified 627.59 MiB XZ data. A 192MiB runtime reservation requires a <=192MiB payload, an additional 69.41% savings. This arithmetic does not prove all possible encodings are impossible, but the present architecture cannot meet the constraints.

## Why this resets the project

43 version labels do not mean 43 progressively more efficient operating systems. Many were necessary diagnostics, CI corrections, packaging, screenshots, and functional tests. They should not have been called memory breakthroughs.

Linux MemTotal minus MemAvailable is a guest estimate of remaining available resources, not exact physical memory allocation. SquashFS storage in tmpfs appears as shared memory and can possibly be moved to zram under pressure. Zram then physically occupies RAM and must be measured separately, not subtracted as free storage.

## Focused experiments

1. Matched 4GiB v40 vs v43 after-media-ejection Firefox test: same guest, same temporary diagnostic overlay, actual filesystem loops, then browser offline HTML, memory/shmem/pagecache/slab/zram/PSI measurements and screenshots.
2. RAM-only memory-capacity bracket: exact v43 ISO at 1280, 1536 and 2048 MiB, with real X11 desktop, optical CD eject and post-eject browser evidence. These are objective progress toward 384MiB, not substitute goals.

## New release acceptance gate

Do not publish another supposedly improved Puppy50 ISO unless:

- It demonstrates >=10% reduced real RAM requirement or measured physical memory use with no feature regression, OR
- It proves a lower minimum RAM tier, while sustaining desktop and browser AFTER source-media removal, OR
- It solves another major verified usability blocker.

Do not call a smaller ISO a faster OS without speed measurements. Do not call a Firefox process working Firefox without actual page pixels and responsiveness. Do not disable Firefox sandboxing or security features to win benchmarks.

## Architectural decision

For a truly 384 MiB system, one would need to change the contents or representation vastly more than XZ achieved. A hardware-specific, trimmed application/firmware or compiler inventory could be a valuable alternative, but MUST be labeled as changed feature scope, not "all original programs and files."

The safe full original-feature RAM-only mode remains the 4GiB-tested v43 until stronger evidence exists. User's physical PC still needs independent hardware regression testing.


## New independently measured minimum-RAM finding (same ISO, no packaging change)

- Exact v43 RAM-only ISO, guest allocated 1,280 MiB: only FIVE of seven (including the tiny disposable measurement layer) SFS files were RAM-backed; firmware and kernel-build SquashFS were still backed by the virtual CD. The CD was successfully ejected but the test fails full offline RAM residency, and final Firefox page content was blank with severe memory stalls. Do not count this capacity as successful RAM-only.
- Exact same ISO with 1,536 MiB allocated: ALL seven SquashFS layers were RAM-backed, the virtual CD was ejected, and original Firefox ESR rendered the actual offline test HTML afterward. Memory pressure was severe at various stages, so long-term smoothness is NOT established.
- Exact same ISO with 2,048 MiB allocated: ALL seven SquashFS layers RAM-backed and original Firefox ESR rendered the post-ejection HTML page. Late memory-pressure stall samples were near zero, and available memory was substantially larger. Sustained real-world use still requires additional tests.
- This confirms a new functional RAM-allocation tier. It does **not** reduce the intrinsic RAM footprint by 62.5%; reducing 4,096 MiB test allocation to 1,536 MiB is a test-limit reduction only.
- Reversed-order 384MiB Firefox HTTP-cache A/B at 300s showed BOTH original and 8MiB-capped configurations rendering HTML, both with severe PSI stalls. Earlier cache-survival advantage did NOT reliably replicate; do not adopt it as an optimization by default.

Source CI runs: capacity https://github.com/74127418528426leo-del/Test/actions/runs/41507942758 ; reversed A/B https://github.com/74127418528426leo-del/Test/actions/runs/41465968462

Further comparison at 1,664 and 1,792 MiB: https://github.com/74127418528426leo-del/Test/actions/runs/41509402161


## New matched after-ejection full-browser results

Same 4,096 MiB guest RAM, same QA scripts, same offline Firefox workload, each virtual CD ejected before browser request:

- Original compression v40: final MemTotal-MemAvailable **1,619.242 MiB**.
- Full lossless XZ original-data v43: final MemTotal-MemAvailable **1,560.707 MiB**.
- Difference: **58.535 MiB lower estimate** with browser opened, more meaningful than only measuring idle OS. Physical zram allocator ~0 in both; last PSI full avg10 0% in both. Both final actual screenshot frames showed the complete offline page.
- Single matched run only; avoid claiming statistically proven general speed or 58.535 MiB of lower irreducible process allocations.
- Source run https://github.com/74127418528426leo-del/Test/actions/runs/41507547871

## New capacity bracket, real original Firefox after boot-medium ejection

All use **the identical unmodified v43 release** (except a small temporary diagnostic layer), QEMU/KVM 2 vCPUs, networking disabled and the same HTML test:

| Guest RAM limit | Every original SquashFS RAM-backed? | Firefox after optical eject | Memory pressure | Verdict |
|---|---|---|---|---|
| 1,280 MiB | NO: fdrv and kbuild remain backed by source CD | Final blank page | Very severe, PSI full avg10 ~80% | FAIL |
| 1,536 MiB | YES | Real HTML pixels | Significant stalls in several samples, last 12.45% | Boots; not reliably usable |
| 1,664 MiB | YES | Real HTML pixels | Mostly low, last 0.13%, one 4.39% spike | Promising userland capacity |
| 1,792 MiB | YES | Real HTML pixels | Essentially zero near end | More headroom |
| 2,048 MiB | YES | Real HTML pixels | Zero final memory stalls | Healthier baseline |

Evidence and actual screenshots: https://github.com/74127418528426leo-del/Test/actions/runs/41507942758 and https://github.com/74127418528426leo-del/Test/actions/runs/41509402161

The 1,664 MiB finding is a **62.5%?** NO: allocate 1,664/4,096=40.625% of the original 4GiB test RAM, thus 59.375% reduction in configured guest RAM. The OS code was not reoptimized during these capacity tests, and one run does not prove a minimum stable target or the true physical resident set. Do not claim 384MiB accomplished.

The 1,280 MiB failure discovered an upstream boot behavior: on memory shortage some Puppy SFS files stay backed by the optical/USB source even with the RAM-only policy. A separate fail-closed boot-policy fix is now under independent KVM validation, with artifacts published only after passing positive and negative boot tests:
https://github.com/74127418528426leo-del/Test/actions/runs/41510359870
