#!/usr/bin/env python3
"""QEMU-only experiment: Firefox priority -12 versus already verified -10.

The only edited source in the disposable extracted initrd is the Firefox
niceness value and a serial diagnostic marker; no sandbox, binary, root,
full-RAM fallback, network, or external ISO files are changed.
"""
from pathlib import Path
import argparse
OLD="/usr/bin/nice -n -10 setpriv --reuid=user --regid=user --init-groups"
NEW="/usr/bin/nice -n -12 setpriv --reuid=user --regid=user --init-groups"
MARKER="printf 'P50_V146_HIGHER_FIREFOX_PRIORITY_REQUESTED %s\\n'"
ADD="""printf 'P50_V160_FIREFOX_NICE12_REQUESTED %s\\n' "$(cat /proc/uptime)" >/dev/ttyS0
        """
def patch(root:Path) -> Path:
    root=root.resolve(strict=True)
    if root==Path("/") or not root.is_dir():raise ValueError("Physical root modification refused")
    p=root/"usr/lib/live/boot/9990-main.sh"
    if p.is_symlink() or not p.is_file():raise ValueError("Expected disposable unpacked initrd")
    s=p.read_text()
    for req in ("P50_V149_SOFTWARE_WEBRENDER","P50_V146_HIGHER_FIREFOX_PRIORITY_REQUESTED",
                "P50_V144_XORG_VT7_SELECTED","P50_V127_FIREFOX_DIRECT_EXEC"):
        if req not in s:raise ValueError("Required secure v151 Firefox prerequisite missing: "+req)
    if s.count(OLD)!=1 or s.count(MARKER)!=1 or "P50_V160_FIREFOX_NICE12_REQUESTED" in s:
        raise ValueError("Unexpected/inconsistent v151 source")
    p.write_text(s.replace(OLD,NEW,1).replace(MARKER,ADD+MARKER,1))
    return p
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("extracted_root",type=Path)
    print(patch(a.parse_args().extracted_root))
