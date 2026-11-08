#!/usr/bin/env python3
"""Instrument a test-only boot to investigate the prebuilt linker cache."""

import argparse
from pathlib import Path

MAIN_MARKER = '\n\tFstab\n\tNetbase\n'
MIGRATION_MARKER = '"$B" sleep 8\nemit P50_STAGE_START\n'

MAIN_HOOK = r'''
	# P50_V110_PREBUILT_LD_CACHE: experiment only, and only with an existing cache.
	if [ -z "${TORAM:-}" ] && [ -s "${rootmnt}/etc/ld.so.cache" ]; then
		p50_ld_unit="${rootmnt}/etc/systemd/system/ldconfig.service"
		[ ! -e "${p50_ld_unit}" ] && [ ! -L "${p50_ld_unit}" ] || panic "p50: unexpected ldconfig override"
		ln -s /dev/null "${p50_ld_unit}" || panic "p50: cannot mask ldconfig"
	fi
'''

DIAGNOSTIC = r'''(
    "$B" sleep 12
    {
        printf '\nP50_V110_CACHE_DIAGNOSTIC_BEGIN\n'
        if [ "$(readlink /etc/systemd/system/ldconfig.service 2>/dev/null || true)" = /dev/null ]; then
            printf 'P50_V110_LDCONFIG_MASKED\n'
        else
            printf 'P50_V110_LDCONFIG_NOT_MASKED\n'
        fi
        if [ -s /etc/ld.so.cache ] && ldconfig -i -X -C /run/p50-stage/ldconfig-check.cache >/dev/null 2>&1 && cmp -s /etc/ld.so.cache /run/p50-stage/ldconfig-check.cache; then
            printf 'P50_V110_CACHE_IDENTICAL\n'
        else
            printf 'P50_V110_CACHE_DIFFERENT\n'
        fi
        rm -f /run/p50-stage/ldconfig-check.cache
        printf 'P50_V110_CACHE_DIAGNOSTIC_END\n'
    } >/dev/ttyS0 2>&1
) &
'''


def patch_main(text):
    if text.count(MAIN_MARKER) != 1 or 'P50_V110_PREBUILT_LD_CACHE' in text:
        raise ValueError('Unexpected or already patched initramfs boot script')
    return text.replace(MAIN_MARKER, MAIN_HOOK + MAIN_MARKER, 1)


def patch_migration(text):
    if text.count(MIGRATION_MARKER) != 1 or 'P50_V110_CACHE_DIAGNOSTIC_BEGIN' in text:
        raise ValueError('Unexpected or already patched migration script')
    return text.replace(MIGRATION_MARKER, DIAGNOSTIC + MIGRATION_MARKER, 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('initrd_root', type=Path)
    args = p.parse_args()
    root = args.initrd_root.resolve(strict=True)
    if root == Path('/'):
        raise ValueError('Refusing to modify the live root')
    a = root / 'usr/lib/live/boot/9990-main.sh'
    b = root / 'usr/lib/p50-stage/p50-migrate.sh'
    if any(p.is_symlink() or not p.is_file() for p in (a, b)):
        raise ValueError('Both boot files must be regular files')
    main_source = patch_main(a.read_text())
    migration_source = patch_migration(b.read_text())
    a.write_text(main_source)
    b.write_text(migration_source)


if __name__ == '__main__':
    main()
