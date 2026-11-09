# Puppy50 v113: 2 GiB and startup follow-up

The published v113 image is an experimental local-media build. It has not reached the eight-second or 384 MiB RAM-only browser goals. Its core release evidence contains a 2 GiB Fast Start trial in which the RAM copy did not start because the available-memory reserve was not met.

## Additional 2 GiB comparisons

An A–B–B–A comparison on one QEMU/KVM host used v112 and v113 diagnostic images. Both diagnostic images retained the original memory guard; they added a serial report of its values. All four runs completed the RAM copy, reported RAM READY, and loaded a fresh local page after the virtual USB was removed. At the guard, the samples reported between 1,143,080 and 1,216,324 KiB available. The guard required a 680,220 KiB root copy plus a 393,216 KiB reserve.

Those diagnostic images differ from the published ISO. Together with the published image's one separate 2 GiB failure, the results show that 2 GiB behavior can vary; they do not prove a reliable minimum or identify the exact reason for that failure. Heavy web pages and physical computers may need more memory. Keep the USB connected until the green RAM READY indicator.

A separate A–B–B–A comparison ran v112 and a diagnostic test image with Firefox spare-process preallocation disabled at 2 GiB. All four completed RAM migration in that small sample. A separate three-sample-per-image timing repeat showed only a 0.02-second first-frame difference at 3 GiB. These tests do not establish a meaningful speed or RAM-reliability advantage, and that preference is not part of the v113 release.

## Direct graphical session experiments

Two attempts to bypass the original display manager did not reach Firefox. The first still started the original display manager through a diagnostic dependency. In the second, after the old display manager was isolated, the system journal showed that systemd tried to resolve the live user before the test's preparation step created it. These failed diagnostic images are not in the v113 release.

The evidence archive includes the raw guest serial logs, actual screenshots, test fixtures, and timing results. These are virtual measurements, not a test of the user's physical Acer or Wi-Fi adapter.
