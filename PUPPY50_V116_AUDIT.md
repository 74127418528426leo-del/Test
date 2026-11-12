# Puppy50 v116: evidence-first optimization work

This branch **does not claim a new ISO, a faster boot, or a finished 8-second browser**. It preserves the existing v115 GitHub release and adds a read-only audit for its test evidence.

## Published input

- ISO: `Puppy50_v115_Font_Cache_EXPERIMENTAL.iso` (906,297,344 bytes), SHA-256 `d697081adf836b7c8b75fe352964764e082b0214a262c8d9895eb9388c3e825a`.
- ZIP: `Puppy50_v115_Test_Evidence.zip` (3,516,606 bytes), SHA-256 `7825360436f14213ae8415e1505a11868f48826a9f4d48f8eb02f1354842ad6b`.
- Recorded VM medians from the previous v115 work: Firefox first visible frame 14.23 s, local JavaScript response 17.38 s, full-RAM readiness 34.39 s. These are not freshly repeated here.

## What the workflow does

The `.github/workflows/puppy50-v116-audit.yml` workflow fetches the **ZIP only** from the exact release link, verifies its GitHub-published SHA-256 and ZIP CRCs, inventories evidence files, and surfaces timing-related text into a report artifact. It **does not execute ZIP contents**, unpack the ISO, change your boot code, or install software on your computer.

## Next measurements and decision gates

1. Compare matched BIOS/UEFI runs at identical CPU/RAM/virtual-USB limits. Record time spent in firmware/menu, kernel/initramfs, root discovery, graphical login, Firefox process start, first rendered frame, and local JS interaction.
2. Use these traces to identify and remove only demonstrably redundant serial waits. Preserve browser functionality, networking, firmware support, the RAM-copy checksum verifier, full-RAM fallback and the green removable-media safety gate.
3. Run at least five repeated controls/variants. Record median and slow-tail first-frame and interactive timings; require unchanged correctness.
4. Test actual Acer Aspire X3950 graphics, dual displays, physical Wi-Fi, and real USB before making hardware claims. Full Firefox at 384 MiB remains a separate unachieved goal.

**Goal: first Firefox frame <=8 seconds, measured reproducibly.** No performance optimization should be released as successful merely because it boots once.

## Reproducibility

The current branch is diagnostic-only. Existing v115 remains the baseline. Any future v116 ISO requires an inspectable build recipe, published checksums, real comparison evidence, and safe USB-removal regression results.
