# Puppy50 v61 — verified real WPE headless guest failure

Completed real KVM workflow (conclusion: FAIL on sandboxed page-load gate):
https://github.com/74127418528426leo-del/Test/actions/runs/41563320388

- Debian sid WPEPlatform 2.54 headless runtime built successfully and compressed using XZ into **158.852 MiB** of SquashFS.
- The independently verified optical ISO booted successfully with 384MiB and 1024MiB physical guest allocations. Both copied the compressed runtime to RAM, switched root, and ejected the original CD.
- Both guests ran the WPE launcher as an unprivileged user and attempted to create a WebKit headless view with sandbox disabling flags **absent**.
- In both guests the WPE launcher exited **139 (SIGSEGV/segmentation fault)** before the `PUPPY50_WPE_HEADLESS_BEGIN` print in the C program. No local page load completed.
- The **1024MiB** guest still had a **minimum measured MemAvailable of 611.324MiB**. That makes a simple physical memory shortage an implausible explanation for this particular failure. At 384MiB the minimum measured MemAvailable was **130.219MiB**. No claim of a working 384MiB WPE browser is supported.
- The serialized logs did not contain a `bwrap:` error in the real KVM guest, unlike the earlier Docker namespace failure. This is a **different observed failure**; without a native backtrace we cannot identify a specific crashing instruction or library.
- The 384MiB sample captured an early WPE launcher process PSS of about **42.416MiB** before it exited. That is not a functional browser working-set measurement.

**Decision:** First debug the native WPE startup crash in a 1024MiB sandbox-compatible guest using a bounded core/backtrace or native debugger, and do not disable WebKit sandbox to mask the failure. Only after a successful 1024MiB local page load does a 384MiB memory comparison become scientifically meaningful.

Sources: current code https://github.com/74127418528426leo-del/Test/tree/puppy50-v61-wpe-real-kvm
