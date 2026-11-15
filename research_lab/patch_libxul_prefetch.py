#!/usr/bin/env python3
"""One-variable Puppy50 research: immutable Firefox libxul prefetch depth.

Changes only the exact allowlisted dd read-ahead byte count in a disposable,
already extracted initramfs boot hook. Never touches the host OS/root image.
"""
import argparse
from pathlib import Path
import os

ALLOWED=(0,32,64,96,128,256)
OLD='nice -n 10 dd if="$p50_lib" of=/dev/null bs=1048576 count=256 2>/dev/null'
OLD_MARK='P50_V133_PREFETCH_256MB_STARTED'

def patch(root, mib):
    if type(mib) is not int or mib not in ALLOWED:
        raise ValueError("unsupported libxul prefetch depth")
    root=Path(root).resolve(strict=True)
    if root==Path("/") or not root.is_dir():
        raise ValueError("refuse host filesystem")
    target=root/"usr/lib/live/boot/9990-main.sh"
    if target.is_symlink() or not target.is_file():
        raise ValueError("expected disposable extracted hook file")
    text=target.read_text()
    for required in ("P50_V131_LIBXUL_READAHEAD",
                     "P50_V127_FIREFOX_DIRECT_EXEC",
                     "P50_V149_WEBRENDER_USERJS_READY"):
        if required not in text:raise ValueError("missing trusted earlier boot stage "+required)
    if text.count(OLD)!=1 or text.count(OLD_MARK)!=1:
        raise ValueError("unexpected prefetch code, refuse ambiguous patch")
    if "P50_AUTOLAB_PREFETCH_CONFIG" in text:
        raise ValueError("prefetch patch already applied")
    if mib:
        new=OLD.replace("count=256",f"count={mib}")
    else:
        new=': # research-only: disable prefetch, keep actual libxul path checks'
    text=text.replace(OLD,new,1)
    text=text.replace(OLD_MARK,f"P50_V133_PREFETCH_{mib}MB_STARTED",1)
    # This boot report is an accurate control rather than the old 256 label.
    # No shell execution from models is introduced.
    text=text.replace(new,
        f'# P50_AUTOLAB_PREFETCH_CONFIG={mib}\n            '+new,1)
    target.write_text(text)
    return target

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("root",type=Path)
    p.add_argument("--mib",type=int,default=None)
    a=p.parse_args()
    value=int(os.environ["P50_PREFETCH_MIB"]) if a.mib is None else a.mib
    print("P50_PREFETCH_EXPERIMENT",value,patch(a.root,value))
