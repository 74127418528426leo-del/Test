#!/usr/bin/env python3
"""v51 disposable VM-only profile. NEVER suitable for general hardware ISO.

Removes runtime firmware assets from a staged Alpine guest only after full
dependency installation. QEMU std-vga + virtual IDE do not need Intel Wi-Fi,
Bluetooth or physical i915 firmware, but a real PC often DOES. This is a
MEASUREMENT branch, not a production OS. Does not remove any kernel modules
or browser packages; verify future KVM tests.
"""
import argparse
import json
import os
from pathlib import Path

def trim(root: Path):
    root=root.resolve(strict=True)
    # Restrict to throwaway image-tree convention; never permit live /.
    if root.name != "rootfs" or root.parent.name != "output":
        raise ValueError("Refusing any directory other than */output/rootfs")
    if not (root/"etc/apk/repositories").is_file():
        raise ValueError("Not the expected staged Alpine build")
    if not (root/"usr/share/puppy50web/index.html").is_file():
        raise ValueError("Missing expected test browser page")
    firmware_dirs=[]
    for p in (root/"lib/firmware",root/"usr/lib/firmware"):
        if p.is_symlink():
            # Resolve aliases only if they remain within the staged root.
            try: p=p.resolve(strict=True)
            except OSError: continue
        if not p.is_dir(): continue
        try: p.relative_to(root)
        except ValueError: raise ValueError("Firmware points outside stage")
        if p not in firmware_dirs: firmware_dirs.append(p)
    if not firmware_dirs:
        raise ValueError("No staged firmware directories; refusing to claim improvement")
    records=[]
    for directory in firmware_dirs:
        for current,dirnames,filenames in os.walk(directory,followlinks=False):
            for name in filenames:
                p=Path(current)/name
                if p.is_symlink():
                    records.append((p,0,"symlink"))
                elif p.is_file():
                    records.append((p,p.stat().st_size,"regular"))
            # File links are not traversed and are therefore out-of-scope.
    actual_files=[(p,n,k) for p,n,k in records if k=="regular"]
    if not actual_files:
        raise ValueError("No actual firmware files to measure")
    for p,_,_ in records:
        p.unlink()
    return {
        "schema":"PUPPY50_V51_QEMU_STD_VGA_FIRMWARE_ONLY",
        "valid_real_hardware_variant":False,
        "qemu_only":True,
        "browser_packages_preserved":True,
        "kernel_modules_preserved":True,
        "removed_file_count":len(actual_files),
        "uncompressed_regular_file_bytes_removed":sum(n for _,n,_ in actual_files),
        "symlinks_removed":sum(k=="symlink" for _,_,k in records),
        "all_firmware_file_entries_remaining":sum(1 for d in firmware_dirs for _ in d.rglob("*") if _.is_file()),
        "warning":"No physical WiFi/Bluetooth/i915 firmware included. QEMU std-vga only. Not a universal OS, not production-ready, and no proof of working Firefox or 384 MiB performance."
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    result=trim(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
