#!/usr/bin/env python3
"""Force safer, test-only RAM guard and checksum failures in isolated images."""
import argparse
from pathlib import Path

MEM_CASE='        case "$mem_k" in \'\'|*[!0-9]*) return 2;; esac\n'
HASH_CHECK='[ "${#expected}" -eq 64 ] || fail \'source checksum missing or ambiguous\'\n'

def inject_retry_fault(text,mode):
    if mode not in ('recover','exhaust') or text.count(MEM_CASE)!=1 or 'P50_V114_INJECT_LOW_MEMORY' in text:
        raise ValueError('Unexpected memory-fault target')
    limit=2 if mode=='recover' else 10
    line='        # P50_V114_INJECT_LOW_MEMORY: only reduce the measured availability.\n'
    line+=f'        if [ "$p50_attempt" -le {limit} ]; then mem_k=0; fi\n'
    return text.replace(MEM_CASE,MEM_CASE+line,1)

def inject_bad_checksum(text):
    if text.count(HASH_CHECK)!=1 or 'P50_V114_INJECT_BAD_HASH' in text:raise ValueError('Unexpected checksum-fault target')
    line="expected=0000000000000000000000000000000000000000000000000000000000000000 # P50_V114_INJECT_BAD_HASH\n"
    return text.replace(HASH_CHECK,HASH_CHECK+line,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('mode',choices=('recover','exhaust','bad_checksum'));a=p.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify the running system')
    path=root/'usr/lib/p50-stage/p50-migrate.sh'
    if path.is_symlink() or not path.is_file():raise ValueError('Expected regular migration script')
    source=path.read_text();modified=inject_bad_checksum(source) if a.mode=='bad_checksum' else inject_retry_fault(source,a.mode)
    path.write_text(modified)

if __name__=='__main__':main()
