#!/usr/bin/env python3
"""Instrument, without changing, the staged-RAM available-memory guard."""
import argparse
from pathlib import Path

GUARD='[ "$mem_k" -ge $((need_k + 393216)) ] || fail \'insufficient available memory and reserve\''

def instrument(text):
    if text.count(GUARD)!=1 or 'P50_V113_GUARD_AVAILABLE_KIB' in text:
        raise ValueError('Unexpected or already instrumented memory guard')
    report='emit "P50_V113_GUARD_AVAILABLE_KIB=$mem_k NEED_KIB=$need_k RESERVE_KIB=393216"\n'
    return text.replace(GUARD,report+GUARD,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify the running system')
    path=root/'usr/lib/p50-stage/p50-migrate.sh'
    if path.is_symlink() or not path.is_file():raise ValueError('Expected regular migration script')
    path.write_text(instrument(path.read_text()))

if __name__=='__main__':main()
