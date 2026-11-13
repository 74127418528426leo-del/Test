# Puppy50 v118 — genuine cold-start Firefox under 3 seconds research

**Date:** 13 November 2026. **Status:** UNDER THREE SECONDS **NOT ACHIEVED**. Do not ship a “3-second ISO” or describe a resume, an image placeholder or process spawning as Firefox visibly ready.

## Definition and immutable baseline

The clock begins **immediately before spawning QEMU/KVM**. The first frame is accepted only if the real 1280×800 Firefox desktop/home-page framebuffer matches the original multi-pixel detector. The proof additionally requires the full original browser, system network access, checksum-verified complete compressed-root copy to RAM, successful virtual medium ejection **only after verified RAM READY**, and new real HTTP browser activity **after ejection**. A physical Acer X3950 power-on timer is separate and has never been tested on real hardware.

Baseline **released v117 experimental ISO** is exactly `a7fe532f501b9541c3a4fc22455e57ef79b8389eac6561720c25d7e188231b83` (906,297,344 bytes). It remains available unchanged.

Final [v117 release A–B–B–A test](https://github.com/74127418528426leo-del/Test/actions/runs/43436287638): mean original v115 9.275 s vs released v117 candidate **8.360 s**. A separate same-host test showed 7.155 s v117, but this did not reproduce below 8 on the release runner, so even eight seconds is not guaranteed.

## Experiment 1 — bypass virtual BIOS Syslinux path by direct host kernel injection

This is intentionally a **diagnostic, NOT a bootable PC/USB image**. Both paths still used the identical v117 root image, guest virtual AHCI CD media, 2 virtual CPUs, 3 GiB RAM, BIOS firmware, 0.2s framebuffer polling, and verified all four post-eject browser connections. In the alternate path only, QEMU loads the unmodified kernel/initrd via `-kernel/-initrd/-append`, removing the guest ISO bootloader dependency.

| Four matched A–B–B–A trials | Real Firefox first frame | Verified RAM-ready |
|---|---:|---:|
| Standard v117 ISO #1 | 9.44 s | 16.16 s |
| Direct host kernel #1 | 9.02 s | 15.72 s |
| Direct host kernel #2 | 8.83 s | 16.03 s |
| Standard v117 ISO #2 | 9.21 s | 15.91 s |
| **Standard mean** | **9.325 s** | **16.035 s** |
| **Direct-kernel mean** | **8.925 s** | **15.875 s** |

**Only 0.400 seconds first-frame gain, nowhere near <3 s.** Because direct kernel loading is not a physical-media cold boot, these values are useful exclusively to isolate the bottleneck, NOT a physical-boot claim. The tested system still spent ~8.9 seconds inside the remaining kernel/live-boot/session/Firefox path.

[Full reproducible successful four-VM run](https://github.com/74127418528426leo-del/Test/actions/runs/43485170362)

## Experiment 2 — move live account setup from LightDM preflight into initramfs

A separate experimental initrd patch [v118/precreate_user.py](./v118/precreate_user.py) requires the expected staged root, validates the original preflight setup, and precreates the ordinary unprivileged live account and Openbox autostart before systemd. It removes only the redundant preflight step after success, retains the original root/Firefox/kernel and all integrity checks, and refuses unfamiliar layouts. The full RAM first and recovery initrd remain byte-identical. **Passed four-VM controlled test; research only, not a released ISO.**

[Reproducible matched benchmark workflow](https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-v118-early-user-ab.yml)

## Experiment 3 — try direct X11 session after precreating user

Previous direct-X attempts in v113 failed because systemd tried to resolve the live user before it existed. This separate research branch combines the v118 early-user hook with the older direct-session experiment after that prerequisite, while preserving browser/working-network/RAM verification gates. A candidate that fails to render the browser, signal real RAM ready, remove media safely and open a new real page is automatically rejected.

[Direct-X workflow](https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-v118-direct-x-ab.yml)

## Architectural conclusions / release gate

- The v117 one-second BIOS-menu improvement was real. Bypassing the *remaining* virtual BIOS loader made only a small additional difference.
- The bottleneck for sub-3-second cold Firefox is primarily **after kernel entry**: live-root and systemd/session preparation, X11 initialization, Firefox library startup, and real first-frame rendering. No single bootloader optimization plausibly closes a ~6-second remaining gap.
- Candidate future proof requires multiple matched runs with **every candidate first Firefox frame <3.00 s** and all browser, network, RAM and recovery checks passed. Never infer the actual Intel i3-540's CPU performance from a fast VM runner with the same CPUID flags.
- The 384 MiB fully-in-RAM Firefox goal remains unmet; the **664 MiB compressed root alone** exceeds this budget. Real i915, physical Wi-Fi, dual monitors and 4K streaming are also not verified.
- Until stronger evidence, retain [v117 experimental ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v117-instant-bios-experimental) and independently keep a [v115 recovery ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-v114-fast-verification-experimental), because v117's Shift-held rescue access was not demonstrated.

**Release decision: no under-3-second ISO until measurements and functional checks justify it.**

## Completed experiments 2 and 3 — all four VMs booted, no three-second result

### V118 early live-user precreation alone — successful controlled improvement

On a matched A–B–B–A BIOS AHCI virtual-CD test with the **exact v117 ISO** as baseline, 2 vCPU, 3 GiB guest RAM, uncapped storage and 0.2s polling, two v118 experimental initrd candidates started real Firefox in **6.97** and **7.18 seconds** (mean **7.075 s**) vs two released-v117 trials of **7.59** and **7.40 seconds** (mean **7.495 s**). The 0.420-second mean gain is real in this limited test but not a physical Acer result, nor a three-second result. Baseline RAM readiness averaged **14.635 s**, candidate **14.205 s**. Every VM reported a Firefox home frame, checksum-verified RAM-ready, safe virtual-medium ejection, post-ejection keyboard input and no benchmark errors. [Successful v118 early-user benchmark](https://github.com/74127418528426leo-del/Test/actions/runs/43486023722).

### V118 precreated live-user plus direct X11 instead of LightDM — functional, no large speedup

A separate matched A–B–B–A test combined the same guarded early-user initrd patch with the existing direct-session X11 prototype. **All four VMs booted and passed the benchmark's original RAM-safety/media-ejection/browser-input checks.** Candidate Firefox frames were **7.60** and **7.43 seconds** (mean **7.515 s**), compared to baseline **7.74** and **8.05 seconds** (mean **7.895 s**): a same-host mean gain of **0.380 s**. RAM-ready means: **15.30 s baseline** vs **15.18 s candidate**. This successfully fixes the old v113 direct-session prerequisite that had previously prevented launching Firefox, but **it does not achieve <3 seconds and does not show a material advantage over the simpler early-user modification**. Do not directly compare its absolute times to a different runner's early-user-only test. [Successful direct-X benchmark](https://github.com/74127418528426leo-del/Test/actions/runs/43486306890).

An additional independent artifact-only CI audit checks the HTTP fixture server logs for four successful post-ejection page requests **per run**. Do not report independently verified HTTP response counts until that follow-up CI completes. The original A–B–B–A workflows did require the browser to remain running, RAM READY to be verified, QMP to report the medium removed and post-ejection browser input sent.

## v118 final interpretation

All three experimentally measured optimizations in this research round are **well above three seconds**. The first direct-kernel diagnostic returned 8.925 s mean, early-user precreation reached 7.075 s mean on a separate runner, and early user plus direct X11 returned 7.515 s mean on yet another runner. Those absolute means are *not* cross-runner rankings. Within each independent same-host A–B–B–A test, the candidate improved its own release baseline by 0.400 s, 0.420 s, and 0.380 s respectively.

The small measured wins cannot add up to a reliable sub-3-second cold Firefox boot on this unchanged large Debian Live system. The next architectural direction—if pursued—must involve much more radical but separately safety-verified reductions to live root preparation, kernel/userspace startup and Firefox cold initialization, not just changes to the boot menu or QEMU launcher. The physical old i3-540 is still not benchmarked, and no claim that it can meet <3 s is supported.

**Release decision: no new v118 under-3-second ISO or ZIP. Retain v117 as the latest released experimental image.**

## Independent network retest — same v118 early-user candidate

The additional [artifact audit](https://github.com/74127418528426leo-del/Test/actions/runs/43487619493) found that **all eight VMs in the early-user and direct-X A–B–B–A runs reached the fixture server after virtual-media ejection**, but the server returned HTTP **403** because the original benchmark defaulted to the literal nonce P50-TEST while the test server expected P50-<GitHub run ID>. This was a **test-harness token mismatch**, not a broken guest NIC; it also meant the original comparisons did not independently prove a successful HTTP 200 page load.

A new independent [corrected BIOS-and-UEFI validation](https://github.com/74127418528426leo-del/Test/actions/runs/43487831058) rebuilt the same early-user-only experimental patch, set a shared per-run nonce, and required a **real HTTP 200 recorded by the fixture server AFTER verified RAM-ready and virtual medium ejection**.

**Result: PASS, two actual successful HTTP 200 responses**, one each from BIOS and UEFI. Both configurations reached a real Firefox first frame, passed the full root copy checksum verification and the QMP media-eject checks, and recorded zero benchmark errors.

| Independent v118 early-user validation | First visible Firefox frame | Verified RAM READY | Server HTTP 200 after eject |
| --- | ---: | ---: | :---: |
| BIOS/QEMU SATA | 9.07 s | 16.27 s | PASS |
| UEFI/QEMU SATA | 11.61 s | 19.28 s | PASS |

**Do not compare absolute startup times from different GitHub runners as proof of progress or regression.** This retest's BIOS time of 9.07 seconds does not invalidate the earlier same-host v118 7.075-second candidate mean vs its 7.495-second v117 baseline. It further demonstrates host variability, while establishing working post-ejection browser HTTP and intact UEFI boot.

### Final v118 research disposition

- All three matched architecture experiments improved their respective same-host v117 baseline by **0.400 s**, **0.420 s** and **0.380 s**, respectively. Not one came close to an authentic under-3-second cold Firefox first frame.
- The early-user patch is the simpler positive performance candidate; direct-X did not demonstrate a clearly superior benefit and added session complexity.
- A repaired independent functional test established that the early-user build has real browser/network connectivity on **both BIOS and UEFI**, and remains safe to eject virtual media **only after full checksum-verified RAM READY**.
- The old Acer i3-540 has **not** been physically booted or measured; Wi-Fi, i915, dual displays and 4K are not certified by a VM.
- **No v118 ISO or ZIP is being released or labeled under three seconds.** Retain the separately verified v117 experimental release and the original v115 recovery boot medium. A true three-second cold Firefox requires a much more radical OS/browser startup architecture and independent repeatable tests, not a bootloader shortcut or a warm-resume timing substitution.
