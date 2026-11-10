# Puppy50: font-cache and page-prefetch research

Both are diagnostic experiments against the exact published v114 image. Their VM results do not establish startup speed on the physical Acer, and neither diagnostic ISO is the general-use release.

## Prebuilt system font cache

A test image seeded the system fontconfig cache using the v114 image's own fonts and fontconfig. The cache data was 194,000 bytes; the fast boot archive increased by 70,688 bytes. The compressed root and original full-RAM fallback were unchanged. Guest-side fontconfig reported the caches valid, and the font list matched the build-time list.

In an initial matched comparison with two boots per image, first Firefox home averaged 15.62 seconds for v114 and 15.03 seconds with the cache; local JavaScript response averaged 19.19 and 18.45 seconds. In a separate four-boots-per-image repeat, the means were 15.76 and 15.32 seconds for first home and 19.25 and 18.82 seconds for local JavaScript response. The repeat also completed individual 2 GiB BIOS, 3 GiB UEFI, and full-RAM fallback VM checks, with a fresh page loaded after virtual USB removal. These are modest, test-host-specific results, not an eight-second result. A clean optional-cache implementation requires its own safety and performance tests before distribution.

## Targeted Firefox page prefetch

A separate read-only probe sampled Firefox file-page cache residency near the first home screen. It found 164,093,952 bytes, about 156.49 MiB, resident across three Firefox files. Residency can include kernel read-ahead and is not a list of pages Firefox necessarily demanded.

In two matched boots per image, proactively reading those ranges made the first home-screen mean **slower**, from 14.89 to 15.61 seconds; local JavaScript response rose from 18.15 to 18.76 seconds, and RAM-ready from 34.67 to 36.52 seconds. The prefetch variant was not adopted.

Each comparison used one QEMU/KVM host, two virtual CPUs, 3 GiB guest RAM, virtual BIOS, a 30 MiB/s virtual USB cap, and a timer from before QEMU launch. Local JavaScript response includes automated URL entry after the home screen appears. Sample counts are small and the polling interval was about 0.2 seconds plus screenshot overhead.

The evidence ZIP contains the VM result files, media checks, screenshots, cache and font-list reports, and page-residency measurements. The eight-second browser goal and 384 MiB RAM-only Firefox goal remain unmet.
