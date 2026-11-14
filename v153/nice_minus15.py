#!/usr/bin/env python3
"""Research-only: test Firefox nice=-15 against verified nice=-10 cold boot.

Only changes niceness of the sandboxed nonroot Firefox process and children
inside the disposable extracted initrd. The kernel, root, original full-RAM
rescue, session security and networking are byte-identical to v151.
"""
from pathlib import Path
import argparse

OLD="/usr/bin/nice -n -10 setpriv --reuid=user --regid=user --init-groups"
NEW="/usr/bin/nice -n -15 setpriv --reuid=user --regid=user --init-groups"
MARKER="printf 'P50_V146_HIGHER_FIREFOX_PRIORITY_REQUESTED %s\\n'"
ADD="""printf 'P50_V153_FIREFOX_NICE15_REQUESTED %s\\n' "$(cat /proc/uptime)" >/dev/ttyS0
        """
def patch(root: Path) -> Path:
    root=root.resolve(strict=True)
    if root==Path("/") or not root.is_dir():raise ValueError("Refuse physical root")
    p=root/"usr/lib/live/boot/9990-main.sh"
    if not p.is_file() or p.is_symlink(): raise ValueError("Expected extracted initrd only")
    s=p.read_text()
    req=("P50_V149_SOFTWARE_WEBRENDER","P50_V146_HIGHER_FIREFOX_PRIORITY_REQUESTED",
         "P50_V144_XORG_VT7_SELECTED","P50_V127_FIREFOX_DIRECT_EXEC")
    if any(marker not in s for marker in req):raise ValueError("Expected v151 authenticated Xorg Firefox prerequisites absent")
    if s.count(OLD)!=1 or s.count(MARKER)!=1 or "P50_V153_FIREFOX_NICE15_REQUESTED" in s:
        raise ValueError(f"Unexpected / already patched v151 launch ({s.count(OLD)} matches)")
    p.write_text(s.replace(OLD,NEW,1).replace(MARKER,ADD+MARKER,1))
    return p
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("extracted_root",type=Path)
    print(patch(a.parse_args().extracted_root))
