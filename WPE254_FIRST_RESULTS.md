# Puppy50 WPE WebKit 2.54 — first measured Debian runtime, with a sandbox constraint

**2026-11-02 New York / 2026-11-03 UTC.** Real GitHub Actions Docker result:
https://github.com/74127418528426leo-del/Test/actions/runs/41553275341

## What was actually built
- Debian sid packaged modern WPE WebKit 2.54-family WebKit, including WPEPlatform headless runtime. The C application compiled against the current WPE API.
- The image was built in two stages, so GCC, headers and other development packages were not included in the measured runtime.
- The complete Debian sid container runtime filesystem was exported and compressed with the same XZ 1 MiB block settings used in Puppy50 experiments.
- **Compressed WPE Debian runtime root: 196,640,768 bytes = 187.53125 MiB**.
- **At 384 MiB, only 196.469 MiB nominal memory remains after copying that root image to RAM**, before the kernel, decompressed pages, browser processes, graphics, and tmpfs working set.
- This Debian runtime root is NOT the same Linux distribution or hardware package closure as the v51 Alpine 202.344 MiB root. Their sizes alone cannot establish that WPE is faster or less memory-hungry than Firefox.

## Actual restricted 384 MiB cgroup result
- Image launched under Docker with --memory=384m, --memory-swap=384m, --network none, non-root user, --cap-drop ALL and --security-opt no-new-privileges.
- WPE printed the start marker but the WebKit sandbox helper (bubblewrap) failed:
  "bwrap: No permissions to create a new namespace, likely because the kernel does not allow non-privileged user namespaces."
- WPE parent process exited with **139**. Docker reported **OOMKilled=false**.
- The expected local HTML load-complete marker was **absent**.
- At twelve seconds the container had already exited; no valid process memory-current/peak was available.
- Therefore, NO WPE page load was demonstrated and NO browser working set was measured. This is a **nested Docker/browser namespace-conflict**, not proof that WPE cannot run under 384 MiB. Nor is it evidence that WPE is already suitable.

## Correct next experiment
Run WPE in an **isolated real QEMU guest**, which gives WebKit's bubblewrap sandbox access to normal guest user namespaces and kernel isolation. Do not disable WebKit sandbox, TLS or process protections merely to force a passing measurement. If user namespaces are unavailable inside the guest, record this and supply a browser-sandbox-compatible kernel configuration instead.

The guest must also load its compressed root into a RAM-backed filesystem, remove the virtual CD, and prove headless local page loading. Then add DRM/KMS visual rendering and keyboard input, followed by networking/HTTPS tests and process PSS/PSI under real 384 MiB physical RAM.

WPEPlatform's direct DRM and headless APIs are documented at https://wpewebkit.org/about/architecture.html and https://wpewebkit.org/about/faq.html.

Do not extrapolate a cgroup/container test into a successful RAM-only operating system. The real guest memory cost of storing the compressed image is not charged to this container's memory cgroup.
