#!/usr/bin/env python3
"""Puppy50 Web 384 MiB planning gate, NOT a memory-use certification.

Use actual measured SFS bytes. The browser, kernel+graphics and safety figures
are explicit ASSUMPTIONS until a real QEMU guest supplies measurements.
An image exceeding the entire guest is unconditionally impossible to copy in.
Passing the planning gate NEVER proves bootability or website usability.
"""
import argparse
import json
from pathlib import Path

MIB = 1024 * 1024

def assess(image_bytes, guest_mib=384, kernel_mib=64, browser_mib=160, safety_mib=32):
    if image_bytes < 0 or min(guest_mib, kernel_mib, browser_mib, safety_mib) < 0:
        raise ValueError("negative sizes are not valid")
    image_mib = image_bytes / MIB
    estimated_other = kernel_mib + browser_mib + safety_mib
    available_image_mib = guest_mib - estimated_other
    remaining_mib = guest_mib - image_mib
    if image_mib >= guest_mib:
        classification = "FAIL_HARD_SFS_ALONE_GE_GUEST_RAM"
    elif image_mib > available_image_mib:
        classification = "FAIL_ASSUMED_RUNTIME_BUDGET"
    else:
        classification = "PASS_ESTIMATE_ONLY_NOT_REAL_VM_PROOF"
    return {
        "classification": classification,
        "image_bytes_measured": image_bytes,
        "image_mib_measured": round(image_mib, 3),
        "guest_mib_allocated": guest_mib,
        "spare_after_image_mib_upper_bound": round(remaining_mib, 3),
        "assumed_kernel_graphics_mib": kernel_mib,
        "assumed_browser_mib": browser_mib,
        "assumed_safety_mib": safety_mib,
        "target_max_image_mib_assumed": available_image_mib,
        "required_image_shrink_mib_assumed": round(max(0, image_mib - max(0, available_image_mib)), 3),
        "real_browser_proven_at_guest_ram": False,
        "note": "Upper-bound accounting only: RAM-copy overhead, kernel reservations and caches make actual usable headroom smaller. All runtime assumptions must be replaced by measurements."
    }

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image", type=Path, help="Path to built SquashFS image")
    ap.add_argument("--ram-mib", type=int, default=384)
    ap.add_argument("--kernel-mib", type=int, default=64)
    ap.add_argument("--browser-mib", type=int, default=160)
    ap.add_argument("--safety-mib", type=int, default=32)
    a = ap.parse_args()
    result = assess(a.image.stat().st_size, a.ram_mib, a.kernel_mib,
                    a.browser_mib, a.safety_mib)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["classification"].startswith("PASS_ESTIMATE") else 2

if __name__ == "__main__":
    raise SystemExit(main())
