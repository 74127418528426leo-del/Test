# Puppy50 v82 — Actual original v70 ISO, 1 vs 2 GiB browser comparison

**Unmodified public v70 ISO SHA-256:** `26a9b339c6de87a1c891512742d608a910f4bbfce66fe26a96159297c98f8e2e`.

**Real KVM test workflow:** https://github.com/74127418528426leo-del/Test/actions/runs/41685499554

The same original lean-Mesa v70 ISO was tested in two independent KVM runners with the identical host-only HTTPS bridge, physical mouse-button injection into the actual guest, read-only CD, and stable QEMU Ethernet. Both received DHCP/DNS and passed guest-side public HTTPS certificate verification.

## Human inspection of genuine QEMU screenshots

| RAM | 185-second screenshot | 405-second screenshot | Automated CI |
|---|---|---|---|
| **1024 MiB** | Puppy50 homepage still visible with Wikipedia card highlighted | Still the SAME homepage; click did not cause navigation | **FAIL**, correctly reports no page transition |
| **2048 MiB** | Firefox visibly displays real `https://www.wikipedia.org/` landing page with language links | Wikipedia still visibly open and stable | **PASS** |

Exact raw PPM SHA-256 checks:

- Public v70, 1024 MiB, 405 seconds: `50e6b6cd488d5fbb2cbcc0c2b07b740fe0501abf212f9210a5596105f79889db`
- Public v70, 2048 MiB, 185 seconds: `6ebcd1b10afb784736dc3c22812b2312f0c2d73217413d4954ce2f6f46791c34`

The 1024 MiB condition had no kernel/user-space error markers, did not crash, and still reported the injected mouse-button monitor commands. **Successful injection does not prove that Firefox acted on the click.** The 2048 MiB condition visibly renders Wikipedia, beyond mere loading status.

## Interpretation

This result is consistent with the previous v79 experiment: both original lean Mesa and stock/full-package Mesa showed unreliable public browsing at 1024 MiB in these runs, while 2048 MiB succeeded. Thus the issue is **not uniquely attributable to stock Mesa or its LLVM dependency**.

Do not infer that all 1 GiB boots fail: an earlier real v71 1 GiB KVM run visually loaded Wikipedia. This is variable behavior, possibly memory pressure, event-loop starvation, network scheduling or other resource contention. Instrumented guest MemAvailable/PSI/OOM tests in v81 are designed to narrow the cause.

## Practical decision

- Set 2048 MiB as the **currently better-supported experimental browsing configuration**, subject to remaining host RAM and old-hardware performance. 
- Keep 1024 MiB as an engineering target rather than asserting fully reliable web browsing.
- Keep 384 MiB as a verified **RAM-only boot**, not modern Firefox usability.
- Do not recommend sensitive logins: the prototype contains Firefox ESR 140.12.0-r0, older than later upstream security fixes. Update provenance/sandbox must be addressed before production.
- Neither 2048 MiB KVM test nor host-level NAT/bridge recovery proves direct guest Wi-Fi SSID control or access to *every* physical network.
