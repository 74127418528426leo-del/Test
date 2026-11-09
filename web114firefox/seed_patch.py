#!/usr/bin/env python3
"""Install a version-pinned UI startup cache in an isolated test initramfs."""
import argparse
import hashlib
from pathlib import Path

MAIN_MARKER = '\n\tFstab\n\tNetbase\n'
WRAPPER = r'''#!/bin/sh
# This cache contains only Firefox's compiled internal UI resources.
# A fresh per-session copy remains writable and Firefox can invalidate it.
if [ -r /run/p50-stage/tools/p50-v114-ui-cache ]; then
    p50_cache_dir="$(mktemp -d "${TMPDIR:-/tmp}/p50-ffcache.XXXXXXXX")" || p50_cache_dir=
    if [ -n "$p50_cache_dir" ] && cp /run/p50-stage/tools/p50-v114-ui-cache "$p50_cache_dir/startupCache.8.little"; then
        MOZ_STARTUP_CACHE="$p50_cache_dir/startupCache.8.little"
        export MOZ_STARTUP_CACHE
    fi
fi
exec firefox-esr "$@"
'''
HOOK = r'''
\t# P50_V114_UI_CACHE: only the staged test boot receives a pinned UI cache.
\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
\t\tp50_autostart="${rootmnt}/etc/skel/.config/openbox/autostart"
\t\t[ -f "${p50_autostart}" ] && [ ! -L "${p50_autostart}" ] || panic "p50: missing expected desktop autostart"
\t\tgrep -Fqx 'firefox-esr file:///usr/share/puppy50web/index.html >/tmp/puppy50-firefox.log 2>&1 &' "${p50_autostart}" || panic "p50: unexpected browser autostart"
\t\tsed -i 's|^firefox-esr file:|/run/p50-stage/tools/p50-v114-firefox file:|' "${p50_autostart}" || panic "p50: cannot install test wrapper"
\t\tgrep -Fqx '/run/p50-stage/tools/p50-v114-firefox file:///usr/share/puppy50web/index.html >/tmp/puppy50-firefox.log 2>&1 &' "${p50_autostart}" || panic "p50: cannot verify test wrapper"
\tfi
'''.replace('\\t', '\t')


def patch_main(text):
    if text.count(MAIN_MARKER) != 1 or 'P50_V114_UI_CACHE' in text:
        raise ValueError('Unexpected or already patched boot main')
    return text.replace(MAIN_MARKER, HOOK + MAIN_MARKER, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('seed', type=Path)
    parser.add_argument('sha256')
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    if root == Path('/'):
        raise ValueError('Refusing to modify the running system')
    if args.seed.is_symlink() or not args.seed.is_file():
        raise ValueError('Expected a regular UI cache seed')
    data = args.seed.read_bytes()
    if not 4096 <= len(data) <= 16_000_000 or hashlib.sha256(data).hexdigest() != args.sha256:
        raise ValueError('Unexpected UI cache seed size or hash')
    main_file = root / 'usr/lib/live/boot/9990-main.sh'
    stage = root / 'usr/lib/p50-stage'
    cache_file = stage / 'p50-v114-ui-cache'
    wrapper_file = stage / 'p50-v114-firefox'
    if main_file.is_symlink() or not main_file.is_file() or stage.is_symlink() or not stage.is_dir():
        raise ValueError('Expected extracted initramfs files')
    if cache_file.exists() or cache_file.is_symlink() or wrapper_file.exists() or wrapper_file.is_symlink():
        raise ValueError('Refusing to overwrite existing stage tools')
    main_text = patch_main(main_file.read_text())
    cache_file.write_bytes(data)
    cache_file.chmod(0o644)
    wrapper_file.write_text(WRAPPER)
    wrapper_file.chmod(0o755)
    main_file.write_text(main_text)


if __name__ == '__main__':
    main()
