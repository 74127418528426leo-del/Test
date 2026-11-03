# Puppy50 v72 — Real Firefox input device audit and Mozilla compatibility test

## Baseline evidence

The public, user-controlled v70 ISO **has not changed** and SHA256 is `26a9b339c6de87a1c891512742d608a910f4bbfce66fe26a96159297c98f8e2e`. v71 confirmed a Wikipedia click using the pointer's **original** position.

The first v72 Mozilla test used `mouse_move 220 0` and `mouse_button 1/0` to try moving right to the adjacent homepage card. The real guest at 1024 MiB booted from RAM, ejected the CD, rendered its homepage, got DHCP/DNS, and passed the host HTTPS bridge preflight. **Its homepage remained unchanged at every captured frame**, and its CI acceptance gate correctly failed.

## Root cause supported by emulator evidence

The actual `info mice` output showed:

```
  Mouse #2: QEMU PS/2 Mouse
* Mouse #4: vmmouse (absolute)
```

The `*` indicates QEMU's active pointer. The test tried relative movement using the active **absolute** vmmouse. No movement to the Mozilla card was observed; the pointer still hovered Wikipedia in the 165, 185 and later frames. This does **not** show Mozilla failing. It is a test harness selection error.

QEMU's documented monitor interface provides `mouse_set index` to choose the active pointer device, followed by `mouse_move dx dy` and `mouse_button`. This is an explicit, supported way to request relative mouse input without relying on guest automation tools.

Docs: https://www.qemu.org/docs/master/system/monitor

## v72 correction under real KVM retest

At 165 seconds:
1. Query `info mice`.
2. Issue `mouse_set 2`.
3. Query again; require `* Mouse #2: QEMU PS/2 Mouse` rather than assuming success.
4. Issue `mouse_move 220 0`.
5. Capture a **before-click** screenshot for exact hover review.

At 185 seconds, send the real left-click, with after-click frames at 205, 245, and 275 seconds.

**The gate refuses to mark Mozilla as displayed merely because the homepage cyan color disappears or HMP commands return a prompt.** A reviewer must verify Mozilla content/title/location in the actual frame, since an error page or different link can also change the screen.

The first failed v72 test is retained here:
https://github.com/74127418528426leo-del/Test/actions/runs/41665965512

The verified v70 ISO and current public release remain unchanged:
https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-qemu-normal-v70

## Second observed attempt: PS/2 selection was not enough

The **real** second run https://github.com/74127418528426leo-del/Test/actions/runs/41667361961 demonstrated that `mouse_set 2` correctly changed the active monitor pointer from absolute vmmouse #4 to PS/2 #2, but subsequent `mouse_move 220 0` and click **still did not change the Firefox homepage**. All actual 1920x1080 screenshot stages had the same cyan accent fraction (`0.03874`). QEMU command acceptance and active device selection are therefore **not** equivalent to a guest Firefox pointer movement. Do not claim Mozilla webpage access from either mouse attempt.

## Third test: accessible keyboard navigation instead of more pointer guessing

The next test now issues three real `sendkey tab` events through QEMU (home links are ordered Example Domain, Wikipedia, Mozilla), captures focus screenshots at 155/165/175/185 seconds, then sends `sendkey ret` at 205 seconds to activate the focused link. It keeps the **same public v70 ISO**, actual 1 GiB RAM allocation, QEMU NAT with host TLS-preserving bridge, and strict browser-frame evidence gate. It will not claim a third public webpage until the actual site is visually reviewed.

This is superior to arbitrary mouse movement hacks because keyboard accessibility is useful to actual people as well as automated tests, while the present guest/VM exposes conflicting mouse paths.

## Larger product lessons

- The VM's **authorized host network** can be Wi-Fi, Ethernet, or hotspot because the guest uses e1000/QEMU NAT; it does not contain a physical Wi-Fi SSID picker. No honest design can promise Internet across every secured or restricted network.
- First prove real site-by-site browser behavior before claiming generalized compatibility.
- Package coherency, browser security patching and physical Intel GPU firmware remain more important production blockers than further small ISO byte savings.
- 384 MiB still provides a RAM-only boot, **not** a working Firefox browser.
