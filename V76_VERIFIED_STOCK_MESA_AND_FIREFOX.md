# Puppy50 v76 — VERIFIED: stock APK-managed Mesa and real 1 GiB Firefox browsing

**Completed real KVM workflow:** https://github.com/74127418528426leo-del/Test/actions/runs/41674705325

The source experiment extracts the **exact existing public v70 ISO**, verified SHA-256 `26a9b339c6de87a1c891512742d608a910f4bbfce66fe26a96159297c98f8e2e`, and rebuilds only a disposable new RAM-root. Neither the host OS nor public v70 is modified.

## Actual package coherency result

In v70: 247 installed APK package records, eight owned Mesa ELF digest mismatches, five unowned shared-library aliases.

In the v76 disposable stock-Mesa control, after running Alpine `apk fix --reinstall` for mesa/mesa-dri-gallium/mesa-egl/mesa-gbm/mesa-gl/mesa-gles and removing only five known unowned development aliases:

- **0 scanned owned shared-library digest mismatches**.
- **0 scanned unowned shared-library aliases**.
- **247 installed APK package records remain**.
- Firefox ESR registered version remains `140.12.0-r0`.
- The original kernel and initrd are byte-for-byte identical.
- New control ISO SHA-256 `1bfa7344a7130180acaeaee9405b08b49cf7ba97a11d143eb3b0a5bcf177d058`.

## ISO size comparison

| Image | Bytes | MiB |
|---|---:|---:|
| Original v70 public | 221,577,216 | 211.3125 |
| v76 stock-Mesa experimental | 226,820,096 | 216.3125 |
| Additional size | 5,242,880 | 5.0 |

The stock-Mesa image is **2.366% larger** than v70.

## Actual 1 GiB guest result

The v76 KVM workflow succeeded: the new stock-Mesa ISO copied to RAM, switched root, ejected the virtual CD, started the non-root Firefox homepage, obtained DHCP/DNS, verified the public HTTPS certificate, and responded to a real mouse click. The genuine QEMU frames at 205, 245 and 285 seconds were inspected and **visibly show the real Wikipedia webpage**.

This means a stock distribution-managed Mesa image can support the current 1 GiB QEMU/browser baseline with only a small file-size increase. It is a useful alternative to manually overlaid graphics.

## Crucial remaining conditions

- **Do not call this a fully consistent/updatable OS yet.** The v73 audit only checks shared libraries that still exist, not all files recorded as installed by APK. The next **v77 full manifest audit** will quantify missing package-owned files and critical ELF libraries.
- No full CVE, browser sandbox, firmware, secure update, physical Wi-Fi, hardware i915 or sensitive-login audit has been completed.
- Firefox at 384 MiB remains nonfunctional in the earlier tested profile; v76 was verified at 1 GiB.
- This control ISO is a time-limited GitHub Actions artifact and is **not** an official public release; preserve the existing known-good v70 download.
