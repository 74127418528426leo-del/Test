# Puppy50 — five-second Firefox engineering status (2026-11-14)

**Goal:** From a real cold start, full Firefox ESR first visible frame strictly below **5.000 seconds**, with authentic networking, original browser sandbox, checksum-verified migration of the entire immutable operating-system root to RAM before safe boot-media removal, and an HTTP 200 request made after eject. The correct performance clock starts **before QEMU launches**, not when Firefox launches; never count a splash screen, paused/resumed VM, fake screenshot, or process PID alone.

## Published, SHA-audited functional experimental ISO

[Public Puppy50 v150 VT7 Firefox release](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v150-vt7-early-firefox-experimental)

- ISO: `Puppy50_v150_VT7_Firefox_EXPERIMENTAL.iso` 906,297,344 bytes; SHA-256 `0787715ea0825993256c2a6cd1f6e8fddf69219294aca2ba99a1b44b033c4d08`.
- ZIP: `Puppy50_v150_VT7_Firefox_EXPERIMENTAL.zip` 906,299,953 bytes; SHA-256 `3572d38ccd78d506fd4bb3c1113186e5f64139c6c2cbd11f9dcf71204bc04be5`.
- Release was conditioned on **four independently repeated BIOS/UEFI exact-shipping-ISO VMs** with real Firefox, verified RAM migration, medium eject, and post-eject HTTP 200. It is **NOT** under five seconds; it has not been certified on the original physical Acer i3-540, Intel i915, Wi-Fi or dual monitors.

## Next proven independent experiment

[v151 software WebRender plus Firefox nice=-10](https://github.com/74127418528426leo-del/Test/actions/runs/43541098999): A–B–B–A matched BIOS tests mean genuine Firefox first frame **8.03 s** candidate versus **9.15 s** software WebRender/Firefox nice=-5 reference. Candidate samples **8.04 and 8.02 s**. Independent candidate BIOS **7.84 s**, UEFI **12.69 s**. All six full-RAM media-eject/HTTP 200 tests passed. **Not under five.** Same runner pairing is essential: 9.15 s baseline includes a 10.46 s outlier; do not extrapolate 1.12 s as guaranteed on physical hardware.

## Rejected startup cache generation

[v152 original Xvfb Firefox cache build](https://github.com/74127418528426leo-del/Test/actions/runs/43543365213) opened Firefox but never created a genuine anonymous startupCache. Its Xvfb graceful shutdown timed out; there was no cache to validate. Do not construct fake startupCache data or publish any warm-resume build as cold.

## Newly launched experiments — results pending until independently checked

- **v153:** Firefox nice=-10 versus nice=-15 on same matched runner, same secure VT7 WebRender profile, copied root, RAM and browser. [Live evidence](https://github.com/74127418528426leo-del/Test/actions/runs/43599588303).
- **v154:** nice=-15 versus nice=-19, preserving nonroot Firefox and system migration, test must retain working post-eject network. [Live evidence](https://github.com/74127418528426leo-del/Test/actions/runs/43599878629).
- **v155:** tried graceful WM_DELETE_WINDOW before harvesting anonymous Firefox cache; Firefox returned status **139 (crashed)** with no startupCache, reject.
- **v156:** corrects the offline Firefox cache-generation profile argument to match the known working single-hyphen `-profile` launch; only actual generated anonymous cache is accepted. [Live evidence](https://github.com/74127418528426leo-del/Test/actions/runs/43600322572).
- **v157:** same Firefox nice=-10, WebRender, VT7 and profile but Openbox starts at 4s instead of 2s; requires usable desktop and full network after eject. [Live evidence](https://github.com/74127418528426leo-del/Test/actions/runs/43600224993).

Nothing above authorizes a five-second or universal-hardware claim until output exists. At 3GiB QEMU guest RAM, the Zstd root is approximately **664 MiB compressed**; it cannot be resident entirely inside 384MiB RAM, and no newer experiment changes that. The real Acer has four logical hardware threads but does **not** run with the performance of today's cloud Xeon KVM host simply because the QEMU CPU feature mask is `i3-540-conservative`.

**Recovery warning:** The fast BIOS boot menu's Shift shortcut has not been independently certified, so retain the original working v115 ISO on another recovery USB. Never unplug boot media before a green, checksum-verified RAM READY indication.
