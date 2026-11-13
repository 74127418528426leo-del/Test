#!/usr/bin/env python3
"""Experiment only: increase Firefox libxul overlap prefetch from 96MiB to 256MiB.

Never changes Firefox code, sandbox, live root, kernel or full RAM fallback.
User-relevant benefit MUST be measured by an actual cold visible Firefox frame.
"""
import argparse
from pathlib import Path

OLD='nice -n 10 dd if="$p50_lib" of=/dev/null bs=1048576 count=96 2>/dev/null'
NEW='''printf 'P50_V133_PREFETCH_256MB_STARTED %s\\n' "$(cat /proc/uptime)" >/dev/ttyS0
            nice -n 10 dd if="$p50_lib" of=/dev/null bs=1048576 count=256 2>/dev/null'''
def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Refuse host filesystem')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if not p.is_file() or p.is_symlink():raise ValueError('Expected disposable extracted initrd shell script')
    s=p.read_text()
    if 'P50_V131_LIBXUL_READAHEAD' not in s or 'P50_V127_FIREFOX_DIRECT_EXEC' not in s:
        raise ValueError('Required original secure startup path absent')
    if s.count(OLD)!=1 or 'P50_V133_PREFETCH_256MB_STARTED' in s:
        raise ValueError(f'Unexpected 96MiB prefetch script count {s.count(OLD)}')
    p.write_text(s.replace(OLD,NEW,1))
    return p
if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
