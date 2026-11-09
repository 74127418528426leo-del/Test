#!/usr/bin/env python3
"""Inspect the seeded Firefox mapping only inside an isolated test boot."""
import argparse
from pathlib import Path

MARKER = '"$B" sleep 8\nemit P50_STAGE_START\n'
REPORT = r'''(
  "$B" sleep 18
  {
    printf '\nP50_V114_SEED_PROFILE_BEGIN\n'
    p50_seed_seen=0
    for p50_pid in $(pgrep -u user -x firefox-esr || true); do
      if grep -F 'p50-ffcache.' "/proc/$p50_pid/maps" 2>/dev/null; then
        p50_seed_seen=1
      fi
    done
    if [ "$p50_seed_seen" = 1 ]; then
      printf 'P50_V114_SEED_MAPPING_OK\n'
    else
      printf 'P50_V114_SEED_MAPPING_MISSING\n'
      find /tmp -maxdepth 2 -name startupCache.8.little -ls 2>/dev/null || true
    fi
    printf 'P50_V114_SEED_PROFILE_END\n'
  } >/dev/ttyS0 2>&1
) &
'''


def instrument(text):
    if text.count(MARKER) != 1 or 'P50_V114_SEED_PROFILE_BEGIN' in text:
        raise ValueError('Unexpected or already instrumented migration script')
    return text.replace(MARKER, REPORT + MARKER, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    if root == Path('/'):
        raise ValueError('Refusing to modify the running system')
    path = root / 'usr/lib/p50-stage/p50-migrate.sh'
    if path.is_symlink() or not path.is_file():
        raise ValueError('Expected a regular migration script')
    path.write_text(instrument(path.read_text()))


if __name__ == '__main__':
    main()
