#!/usr/bin/env python3
"""Exercise safe hashing without changing reserve, copy, or switch checks."""
import argparse
from pathlib import Path

PRIMARY='actual=$(/usr/bin/sha256sum "$COPY") || fail \'copy hash failed\''
VERIFY='[ "${#expected}" -eq 64 ] || fail \'source checksum missing or ambiguous\'\n'
FALLBACK='actual=$("$B" sha256sum "$COPY") || fail \'copy hash failed\''
ROBUST='''if actual=$(/usr/bin/sha256sum "$COPY"); then
    emit P50_V114_HASH_PRIMARY_OK
else
    emit P50_V114_HASH_FALLBACK
    actual=$("$B" sha256sum "$COPY") || fail 'copy hash failed'
fi'''

def patch_source(text):
    if text.count(PRIMARY)!=1 or 'P50_V114_HASH_PRIMARY_OK' in text:
        raise ValueError('Unexpected or already patched hash step')
    return text.replace(PRIMARY,ROBUST,1)

def inject_fault(text,mode):
    if mode not in ('bad_checksum','missing_primary','all_hash_unavailable'):
        raise ValueError('Unknown test fault')
    if mode=='bad_checksum':
        if text.count(VERIFY)!=1 or 'P50_V114_INJECT_WRONG_HASH' in text:raise ValueError('Unexpected checksum validation')
        return text.replace(VERIFY,VERIFY+'expected=0000000000000000000000000000000000000000000000000000000000000000 # P50_V114_INJECT_WRONG_HASH\n',1)
    if text.count(ROBUST)!=1 or 'P50_V114_INJECT_PRIMARY_ABSENT' in text:raise ValueError('Unexpected hash step')
    # Test-only guest overlay mutation. BusyBox remains untouched for cleanup.
    missing='emit P50_V114_INJECT_PRIMARY_ABSENT\n"$B" rm -f /usr/bin/sha256sum || fail \'cannot inject test fault\'\n'
    text=text.replace(ROBUST,missing+ROBUST,1)
    if mode=='all_hash_unavailable':
        if text.count(FALLBACK)!=1:raise ValueError('Unexpected fallback')
        text=text.replace(FALLBACK,'actual=$(/run/p50-stage/intentionally-missing-sha256 "$COPY") || fail \'copy hash failed\'',1)
    return text

def main():
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path)
    parser.add_argument('mode',choices=('normal','bad_checksum','missing_primary','all_hash_unavailable'));a=parser.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing live system')
    path=root/'usr/lib/p50-stage/p50-migrate.sh'
    if path.is_symlink() or not path.is_file():raise ValueError('Expected isolated migration script')
    text=patch_source(path.read_text())
    if a.mode!='normal':text=inject_fault(text,a.mode)
    path.write_text(text)

if __name__=='__main__':main()
