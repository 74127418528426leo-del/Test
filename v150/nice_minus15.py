#!/usr/bin/env python3
"""Experimental change to Firefox-only nice=-15, from proven nice=-10 path.

No browser root privileges, network/security bypass, kernel, compressed root,
migration or fallback changes. Accept only full functional cold Firefox runs.
"""
from pathlib import Path
import argparse

OLD="/usr/bin/nice -n -10 setpriv --reuid=user --regid=user --init-groups"
NEW="/usr/bin/nice -n -15 setpriv --reuid=user --regid=user --init-groups"
MARKER="printf 'P50_V146_HIGHER_FIREFOX_PRIORITY_REQUESTED %s\\n'"
INSERT="printf 'P50_V150_MINUS15_FIREFOX_PRIORITY %s\\n' \"$(cat /proc/uptime)\" >/dev/ttyS0\n        "
def patch(root):
    root=Path(root).resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Refusing physical OS')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if not p.is_file() or p.is_symlink():raise ValueError('Expected extracted initrd')
    s=p.read_text()
    if 'P50_V146_HIGHER_FIREFOX_PRIORITY_REQUESTED' not in s or 'P50_V141_PRIORITY_EXPERIMENT' not in s:
        raise ValueError('Missing unchanged -10 secure Firefox prerequisites')
    if s.count(OLD)!=1 or s.count(MARKER)!=1 or 'P50_V150_MINUS15_FIREFOX_PRIORITY' in s:
        raise ValueError('Unexpected source or previously patched')
    p.write_text(s.replace(OLD,NEW,1).replace(MARKER,INSERT+MARKER,1))
    return p
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
