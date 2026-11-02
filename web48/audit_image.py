#!/usr/bin/env python3
"""Repeatable actual-filesystem size attribution. Never certifies a browser boot.

Counts *staged* files and an *actual* compressed SquashFS, not theoretical
apk package sizes. The compressed sizes of independent groups are NOT additive.
Symbolic links are not followed. No files are modified.
"""
import argparse
import importlib.util
import json
import os
from collections import defaultdict
from pathlib import Path

GATE = Path(__file__).resolve().parents[1] / "web45/ram_budget_gate.py"
spec = importlib.util.spec_from_file_location("puppy50_ram_gate", GATE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def category(relative):
    name = relative.as_posix()
    if name.startswith(("lib/modules/", "usr/lib/modules/")):
        return "kernel-modules"
    if name.startswith(("lib/firmware/", "usr/lib/firmware/")):
        return "firmware"
    if name.startswith("boot/"):
        return "kernel-boot-files"
    if name.startswith(("usr/lib/firefox/", "usr/lib/firefox-esr/")):
        return "firefox-engine"
    if "wpe-webkit" in name or "WPEWebKit" in name or "WebKit" in name:
        return "webkit-engine"
    if name.startswith("usr/share/"):
        return "shared-resources-fonts-data"
    if name.startswith(("usr/lib/", "lib/")):
        return "shared-libraries"
    if name.startswith(("usr/bin/", "usr/sbin/", "bin/", "sbin/")):
        return "executables"
    return "other-files"

def audit(root, sfs_bytes, ram_mib=384, top=30):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root is not a directory")
    totals = defaultdict(int)
    files = []
    logical_bytes = 0
    physical_file_bytes = 0
    unique_inodes = set()
    symlinks = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Avoid following linked directories into other filesystems.
        dirnames[:] = [d for d in dirnames if not (Path(dirpath)/d).is_symlink()]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.is_symlink():
                symlinks += 1
                continue
            if not p.is_file():
                continue
            st = p.stat(follow_symlinks=False)
            relative = p.relative_to(root)
            size = st.st_size
            logical_bytes += size
            inode = (st.st_dev, st.st_ino)
            if inode not in unique_inodes:
                unique_inodes.add(inode)
                physical_file_bytes += size
            totals[category(relative)] += size
            files.append((size, relative.as_posix()))
    budget = gate.assess(sfs_bytes, guest_mib=ram_mib)
    return {
      "schema": "PUPPY50_V48_ACTUAL_IMAGE_AUDIT",
      "guest_ram_mib": ram_mib,
      "measured_sfs_bytes": sfs_bytes,
      "measured_sfs_mib": round(sfs_bytes / gate.MIB, 3),
      "staged_file_count": len(files),
      "staged_symlink_count": symlinks,
      "staged_apparent_file_bytes": logical_bytes,
      "staged_unique_inode_file_bytes": physical_file_bytes,
      "nonadditive_uncompressed_directory_categories": dict(sorted(totals.items(), key=lambda x: -x[1])),
      "largest_staged_regular_files": [{"bytes": sz, "path": p} for sz, p in sorted(files, reverse=True)[:top]],
      "ram_budget_estimate_only": budget,
      "is_complete_browser_proven": False,
      "is_secure_modern_browser_proven": False,
      "warning": "Categories show UNCOMPRESSED apparent file sizes, NOT independent compressed savings. No VM boot, networking, modern web or peripheral compatibility is certified."
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--sfs", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--ram-mib", type=int, default=384)
    args = p.parse_args()
    report = audit(args.root, args.sfs.stat().st_size, args.ram_mib)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"measured_sfs_mib": report["measured_sfs_mib"],
       "ram_gate": report["ram_budget_estimate_only"]["classification"],
       "largest_files": report["largest_staged_regular_files"][:8]}, indent=2))

if __name__ == "__main__":
    main()
