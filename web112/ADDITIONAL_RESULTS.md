# Puppy50 v112 — additional 4K and panorama tests

These additional tests used the exact released v112 ISO, SHA-256 `317999f51e47698d90889b129e9f74bbbefaa382b4d481f4da32016861d8ddc7`, in QEMU/KVM with two virtual CPUs and 3 GiB RAM. In both tests the system reported the RAM migration ready and the virtual boot USB was removed before the browser visited the test page.

## Synthetic local 4K video

Firefox played a locally served, synthetic H.264 test clip with a 3840 × 2160 source at 24 frames per second. The 12-second clip looped. Across 32.08 seconds, browser playback telemetry reported 770 total frames and zero dropped frames, an observed average of 24.0 frames per second. The evidence package contains the original telemetry, clip metadata, virtual machine logs, a browser screenshot, and the exact command used to synthesize the clip.

This was a low-complexity synthetic clip, viewed in a 1280 × 800 virtual screen, not a 4K physical display. It does not establish 4K streaming, 60 fps, audio, any particular web service, or performance on the user's physical Acer. The YouTube page separately requested sign-in verification, and the Pexels page requested human verification, so those two video streams were not tested.

## Bible panorama keyboard movement

Firefox loaded the user's John 1:1 panorama after virtual USB removal. The test clicked the panorama and sent twelve right-arrow key events. The view visibly turned between the saved before and after screenshots; approximately 91% of the selected panorama region changed according to the pixel comparison. This demonstrates the movement in this VM and scene, not smoothness or physical Acer performance.

[4K test run](https://github.com/74127418528426leo-del/Test/actions/runs/42481962218) · [Panorama movement run](https://github.com/74127418528426leo-del/Test/actions/runs/42482106330)
