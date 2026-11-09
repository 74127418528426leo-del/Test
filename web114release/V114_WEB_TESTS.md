# Puppy50 v114: web and video test observations

These are observations from the exact published v114 ISO, not from physical Acer hardware. Every site was opened in Firefox in an independent QEMU/KVM VM with 3 GiB RAM and two virtual CPUs. The boot medium was virtually removed after the RAM-ready indication before the site was opened. Screenshots record what was on screen at that moment; sites and their verification requirements can change.

- The user's John 1 panorama at `3dbibleonline.github.io` rendered. The view changed in response to simulated keyboard input. The two corresponding screenshots show the initial and changed views; they do not establish performance or smoothness on the physical Acer.
- CNN's page rendered behind a consent prompt. The browser displayed a notice that DRM must be enabled for some media, and the page's video area reported unsupported DRM. Playback was not demonstrated.
- The YouTube 4K page rendered but required sign-in to verify the client was not a bot; its video did not play in this test.
- The requested Pexels page displayed a river image and a Google sign-in popup. A still image does not prove video playback or its resolution.
- A separate locally served synthetic H.264 video was 3840 × 2160 at 24 fps, muted, and looped. Over 32.094 seconds, Firefox reported 770 frames and 0 dropped frames (about 23.99 fps). The displayed VM desktop was 1280 × 800 on a fast AMD EPYC host. This tests synthetic local decoding and a scaled display, not native 4K output, audio, Internet streaming, other codecs, or Acer performance.

The exact ISO SHA-256 is `bf19a63758fbb6ab9aad5cb3b04c9b0e97b32944ab30f304fa16a205c78096b9`. The attached evidence ZIP contains the screenshots, browser and VM logs, synthetic-video metadata and timing telemetry.
