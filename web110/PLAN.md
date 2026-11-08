# Puppy50 v110 boot-time research

Goal: reduce the time from QEMU launch to the first visible Firefox home frame toward eight seconds while keeping the full live system, Firefox sandbox, network stack, staged RAM migration and the v109 release available.

Baseline: published v109 ISO, SHA-256 `e6b341ae3a272bb6bfa063814b2b61a14ba9dadd5f41137a8203f651120671da`. On a two-vCPU, 3-GiB virtual machine with capped USB, the previous two-run mean was 19.46 seconds; physical Acer timing is unknown.

The previous diagnostic serial log shows roughly one second between USB mass-storage detection and disk discovery. Test exactly one change: `usb-storage.delay_use=0` on the Fast Start kernel command line. Compare the unmodified and modified images in A-B-B-A order on one host with the existing v109 test harness, retain screenshots, check a new nonce page after the verified RAM transition and virtual unplug, and measure both browser-visible and RAM-ready time. The image remains a test artifact, not a release: a shorter USB discovery delay can cause problems with some physical devices, so no universal compatibility is inferred.

Inspect v109's boot archive and capture the guest's actual systemd critical chain in a separately instrumented diagnostic build. Use those measurements to choose the next experiment. Never treat a home-page screenshot as proof of network readiness or 8-second physical-hardware performance. Preserve all unsuccessful outcomes and do not claim 8 seconds without repeated, equivalent tests.
