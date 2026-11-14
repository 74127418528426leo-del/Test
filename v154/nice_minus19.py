#!/usr/bin/env python3
"""Puppy50 QEMU-only Firefox cold-boot niceness experiment (-15 vs -19).

Modify only Firefox launch priority from root before dropping privileges.
Do not change Firefox binary, content sandbox, DNS, root FS, kernel, or
checksum-verified RAM migration. Fail closed when prerequisite absent.
"""
from pathlib import Path
import argparse

OLD="/usr/bin/nice -n -15 setpriv --reuid=user --regid=user --init-groups"
NEW="/usr/bin/nice -n -19 setpriv --reuid=user --regid=user --init-groups"
MARKER="printf 'P50_V153_FIREFOX_NICE15_REQUESTED %s\\n'"
HOOK="""printf 'P50_V154_FIREFOX_NICE19_REQUESTED %s\\n' "$(cat /proc/uptime)" >/dev/ttyS0
        """

def patch(root:Path) -> Path:
    root=root.resolve(strict=True)
    if root==Path("/") or not root.is_dir(): raise ValueError("Refuse physical host root")
    p=root/"usr/lib/live/boot/9990-main.sh"
    if p.is_symlink() or not p.is_file():raise ValueError("Expected extracted initrd")
    s=p.read_text()
    for req in ("P50_V153_FIREFOX_NICE15_REQUESTED","P50_V146_HIGHER_FIREFOX_PRIORITY_REQUESTED",
                "P50_V149_SOFTWARE_WEBRENDER","P50_V144_XORG_VT7_SELECTED"):
        if req not in s:raise ValueError("Missing prerequisite "+req)
    if s.count(OLD)!=1 or s.count(MARKER)!=1 or "P50_V154_FIREFOX_NICE19_REQUESTED" in s:
        raise ValueError("Unknown v153 command or patch was already applied")
    p.write_text(s.replace(OLD,NEW,1).replace(MARKER,HOOK+MARKER,1))
    return p

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("extracted_root",type=Path)
    print(patch(a.parse_args().extracted_root))
