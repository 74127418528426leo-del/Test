#!/usr/bin/env python3
"""Puppy50 research only: test -10 vs -5 niceness of nonroot sandboxed Firefox.

No root, browser security, network, kernel, rootFS, fallback or RAM logic
is changed. This tests whether more browser CPU priority accelerates its
actual visible frame without starving the final media ejection network test.
"""
from pathlib import Path
import argparse

OLD="/usr/bin/nice -n -5 setpriv --reuid=user --regid=user --init-groups"
NEW="/usr/bin/nice -n -10 setpriv --reuid=user --regid=user --init-groups"
MARKER="printf 'P50_V141_FIREFOX_EARLY_PRIORITY_CONFIGURED %s\\n'"
HOOK="printf 'P50_V146_HIGHER_FIREFOX_PRIORITY_REQUESTED %s\\n' \"$(cat /proc/uptime)\" >/dev/ttyS0\n        "
def patch(root:Path):
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Refuse host OS')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if p.is_symlink() or not p.is_file():raise ValueError('Expected extracted disposable boot')
    s=p.read_text()
    if 'P50_V141_PRIORITY_EXPERIMENT' not in s or 'P50_V127_FIREFOX_DIRECT_EXEC' not in s:
        raise ValueError('Requires earlier working nice=-5 secure Firefox')
    if s.count(OLD)!=1 or s.count(MARKER)!=1 or 'P50_V146_HIGHER_FIREFOX_PRIORITY_REQUESTED' in s:
        raise ValueError('Unexpected v141 launcher or already applied')
    p.write_text(s.replace(OLD,NEW,1).replace(MARKER,HOOK+MARKER,1))
    return p
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
