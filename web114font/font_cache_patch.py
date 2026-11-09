#!/usr/bin/env python3
"""Diagnostic fast-start fontconfig cache seeding; leave full-RAM fallback alone."""
import argparse
from pathlib import Path

MARKER='\n\tFstab\n\tNetbase\n'
MIGRATE='"$B" sleep 8\nemit P50_STAGE_START\n'
HOOK=r'''
\t# P50_V114_FONTCACHE: test-only cache files built from the unchanged fonts.
\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
\t\tp50_cache_source=/usr/lib/p50-fontcache
\t\tp50_cache_dest="${rootmnt}/var/cache/fontconfig"
\t\t[ -d "${p50_cache_source}" ] && [ ! -L "${p50_cache_source}" ] || panic "p50: no fontconfig cache source"
\t\t[ -d "${p50_cache_dest}" ] && [ ! -L "${p50_cache_dest}" ] || panic "p50: unexpected fontconfig cache destination"
\t\tcp -a "${p50_cache_source}/." "${p50_cache_dest}/" || panic "p50: could not install fontconfig caches"
\tfi
'''.replace('\\t','\t')
DIAGNOSTIC=r'''(
 "$B" sleep 20
 {
  printf '\nP50_FONTCACHE_DIAG_BEGIN\n'
  printf '%s\n' '--- system fontconfig cache files ---'
  ls -l /var/cache/fontconfig/ || :
  printf '%s\n' '--- system fontconfig cache validation ---'
  /usr/bin/fc-cache -s -v 2>&1 || :
  printf '%s\n' '--- application font list ---'
  LC_ALL=C /usr/bin/fc-list --format '%{file}|%{family}|%{style}\n' | LC_ALL=C sort | sha256sum || :
  printf 'P50_FONTCACHE_DIAG_END\n'
 } >/dev/ttyS0 2>&1
) &
'''

def patch_main(text):
 if text.count(MARKER)!=1 or 'P50_V114_FONTCACHE' in text:raise ValueError('Unexpected boot main')
 return text.replace(MARKER,HOOK+MARKER,1)

def patch_migration(text):
 if text.count(MIGRATE)!=1 or 'P50_FONTCACHE_DIAG_BEGIN' in text:raise ValueError('Unexpected migration script')
 return text.replace(MIGRATE,DIAGNOSTIC+MIGRATE,1)

def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root.resolve(strict=True)
 if root==Path('/'):raise ValueError('Refusing to modify running system')
 paths=[(root/'usr/lib/live/boot/9990-main.sh',patch_main),(root/'usr/lib/p50-stage/p50-migrate.sh',patch_migration)]
 updates=[]
 for path,fn in paths:
  if path.is_symlink() or not path.is_file():raise ValueError('Expected isolated regular file')
  updates.append((path,fn(path.read_text())))
 for path,data in updates:path.write_text(data)
if __name__=='__main__':main()
