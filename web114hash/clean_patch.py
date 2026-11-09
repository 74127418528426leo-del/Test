#!/usr/bin/env python3
"""Prefer the root's faster SHA-256; retain BusyBox as a safe fallback."""
import argparse
from pathlib import Path

OLD='''actual=$("$B" sha256sum "$COPY") || fail 'copy hash failed' '''.rstrip()
NEW='''if actual=$(/usr/bin/sha256sum "$COPY"); then
    :
else
    actual=$("$B" sha256sum "$COPY") || fail 'copy hash failed'
fi'''

def patch_source(text):
    if text.count(OLD)!=1 or 'if actual=$(/usr/bin/sha256sum "$COPY"); then' in text:
        raise ValueError('Unexpected or already modified hash step')
    return text.replace(OLD,NEW,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify the running system')
    path=root/'usr/lib/p50-stage/p50-migrate.sh'
    if path.is_symlink() or not path.is_file():raise ValueError('Expected isolated regular script')
    path.write_text(patch_source(path.read_text()))

if __name__=='__main__':main()
