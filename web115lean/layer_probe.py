#!/usr/bin/env python3
"""Add test-only reporting of loop backings without changing the RAM safety gate."""
import argparse
from pathlib import Path
MARKER='"$B" sleep 8\nemit P50_STAGE_START\n'
PROBE=r'''(
 "$B" sleep 3
 {
  printf '\nP50_V114_LAYER_PROBE_BEGIN\n'
  for p in /sys/block/loop*/loop/backing_file; do
   [ -r "$p" ] || continue
   printf 'P50_V114_LOOP %s ' "$p"
   "$B" cat "$p" || true
  done
  printf 'P50_V114_LAYER_PROBE_END\n'
 } >/dev/ttyS0 2>&1
) &
'''
def patch_migrate(text):
 if text.count(MARKER)!=1 or 'P50_V114_LAYER_PROBE_BEGIN' in text:raise ValueError('Unexpected or previously patched migration script')
 return text.replace(MARKER,PROBE+MARKER,1)
def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root.resolve(strict=True)
 if root==Path('/'):raise ValueError('Refusing to modify the running system')
 path=root/'usr/lib/p50-stage/p50-migrate.sh'
 if path.is_symlink() or not path.is_file():raise ValueError('Expected a regular migration script')
 path.write_text(patch_migrate(path.read_text()))
if __name__=='__main__':main()
