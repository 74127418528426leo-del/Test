#!/usr/bin/env python3
"""Change only the delay before staging starts, in a disposable extracted initramfs."""
import argparse
from pathlib import Path
MARKER='"$B" sleep 8\nemit P50_STAGE_START\n'

def patch(text,seconds):
    if seconds not in (0,2,4,6) or text.count(MARKER)!=1:
        raise ValueError('Unexpected script or selected delay')
    return text.replace(MARKER,f'"$B" sleep {seconds}\nemit P50_STAGE_START\n',1)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('seconds',type=int,choices=(0,2,4,6));a=p.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify the live system')
    path=root/'usr/lib/p50-stage/p50-migrate.sh'
    if path.is_symlink() or not path.is_file():raise ValueError('Expected regular script')
    path.write_text(patch(path.read_text(),a.seconds))
if __name__=='__main__':main()
