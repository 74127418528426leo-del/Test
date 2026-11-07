# v107 boot-speed investigation

Goal: reduce cold start to visible, responsive Firefox while keeping the normal live root fully RAM-loaded, preserving the existing browser security and network capabilities. Eight seconds is a target, not an assumed result.

1. Pin the published v106 ISO and inspect its boot media, compressed root, initramfs and largest installed components. Capture the live guest's boot critical path and actual overlay mounts in a temporary diagnostic-only image.
2. Compare xz with an x86 executable filter and zstd against v106. Repack the same complete root with no packages, firmware, browser security, boot options or network behavior removed. Verify byte content and filesystem metadata before testing.
3. Run v106 and each variant on the same KVM host, including virtual USB with a documented bandwidth cap, browser responsiveness, HTTPS, and access after removing the virtual medium. Keep raw screenshots and timing data; report only what they establish.
4. Investigate a targeted cache-startup optimization only if guest mount evidence supports a safe fail-closed design. Never globally mark other system services as already updated.
5. Publish a separate experimental image only after a meaningful improvement and independent review; otherwise report the result and retain v106 as the download.

Known limits: v106's 594.83 MiB root alone requires at least 10.4 seconds to copy at USB 2.0's theoretical 480 Mbit/s signalling rate. VM times do not establish the physical Acer's cold-start time; real hardware and Wi-Fi are not tested. A changed design must not secretly defer disk-backed executable loading while claiming a complete RAM-only boot.
