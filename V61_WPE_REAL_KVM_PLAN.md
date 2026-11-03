# Puppy50 v61 — WPEPlatform 2.54 real isolated KVM RAM-root feasibility

**Experimental, not a functional graphical browser and not production Linux.**

Live real KVM source-built job:
https://github.com/74127418528426leo-del/Test/actions/runs/41562887116

## Why this experiment exists

The prior WPE WebKit 2.54 Docker experiment exported a Debian runtime root measuring **187.531 MiB compressed XZ**, but failed to load its local page because Docker denied the Bubblewrap user namespace. The parent exited with status 139 without Docker reporting OOM. This is an invalid negative memory benchmark.

A separate compact Firefox/Mesa system **v59 at 148.660 MiB** has proven full RAM-root boot and actual DOM click/keypress at 1024MiB but fails browser rendering at 384MiB:
https://github.com/74127418528426leo-del/Test/actions/runs/41560016480

The rational next milestone is a *smaller secure browser working set*, not further cosmetic OS savings. WPE WebKit 2.54 ships a supported headless output mode via WPEPlatform and has an embedded multprocess architecture; actual memory consumption remains to be measured. Official API: https://wpewebkit.org/about/faq.html

## Actual v61 build and test boundaries

1. Compile and stage the current Debian-sid WPEPlatform 2.54 runtime in a **two-stage Docker image**: GCC and header packages remain out of the runtime layer.
2. Include a tiny standalone guest init, a legitimate nonroot user (uid 1000), `setpriv`, Linux Bubblewrap sandbox dependencies and the CA trust package.
3. Separately install the matching Alpine 3.24 linux-lts kernel+module closure; prune unneeded hardware modules, and produce the verified minimal optical boot/initrd used by the earlier real RAM-root KVM experiments. The user’s physical machine is not changed.
4. Physically exclude `/boot/vmlinuz-lts` and the installed kernel module tree from the compressed Debian runtime SFS while constructing the ISO, then preserve the matching boot kernel/early modules in initrd. The entire final browser root is copied to tmpfs, the root is switched and QEMU virtual CD ejected before the outcome is assessed.
5. Boot two independent QEMU guests with exactly **384MiB and 1024MiB allocated physical RAM**, `-nic none` and no disk backing.
6. The guest invokes WPE using `WPE_PLATFORM=headless`, under uid 1000 and with its WebKit/Bubblewrap sandbox **not disabled**. Log local HTML load completion and any sandbox failures; record MemAvailable and WebKit-related process RSS/PSS while active.
7. Fail the CI *functional WPE engine* gate if either guest cannot complete the local page load after RAM-root switch and virtual media removal.

## Important limits

- Headless page load is not a graphical/browser-shell success: it proves no actual pixels, mouse, keyboard, URL navigation, HTTPS, WebGL or downloads.
- A 384MiB QEMU physical guest is a stronger memory test than the prior Docker 384MiB cgroup because the whole compressed root stored in RAM counts toward physical memory usage.
- `WPE_PLATFORM=headless` may still need graphical software driver dependencies or a functional sandbox user namespace; failure is not proof of an inherent WebKit memory floor until guest logs are examined.
- Debian sid is a moving distribution. The exact package closure should be pinned and security-updated before any ISO distribution. This is not Puppy Linux binary compatibility, nor an Alpine Firefox package variant.
- WPE WebKit modern renderer is an embedded engine. A polished general browser requires a user interface, tabs, downloads, permission prompts, security indicators and an update mechanism.
- The old Intel i915 GMA and dual monitors are not tested here. Even a QEMU headless success would not certify physical Crocus DRM/KMS support.

## Interpretation policy

- Engine starts but page does not load: read userns/Bubblewrap and WebKit process exit code.
- Page loads at 1024 but not 384: measure real memory pressure and process PSS; consider zram reclaim and a smaller runtime closure.
- Page loads at both: next milestone is DRM/KMS pixels and real key/mouse interaction with sandbox retained, then HTTPS.
- If Debian compressed WPE runtime is still too large, investigate building a narrow, maintained Alpine/musl WPE package closure rather than deleting shared libraries blindly.

Nothing in this experiment modifies the user's physical Xubuntu machine.
