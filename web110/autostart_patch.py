#!/usr/bin/env python3
"""Test-only reordering of the non-root browser session startup."""

import argparse
from pathlib import Path

STATUS_LINE = '''\t\tprintf '\\n/run/p50-stage/tools/p50-status >/tmp/p50-status.log 2>&1 &\\n' >> "${p50_autostart}" || panic "p50: cannot enable USB status indicator"'''
FAST_AUTOSTART = '''#!/bin/sh
# Keep the USB notice prominent and start the browser before delayed controls.
/run/p50-stage/tools/p50-status >/tmp/p50-status.log 2>&1 &
firefox-esr file:///usr/share/puppy50web/index.html >/tmp/puppy50-firefox.log 2>&1 &
(
    sleep 3
    tint2 >/tmp/puppy50-tint2.log 2>&1 &
    nm-applet >/tmp/puppy50-network-applet.log 2>&1 &
    for agent in /usr/lib/mate-polkit/polkit-mate-authentication-agent-1 /usr/lib/x86_64-linux-gnu/mate-polkit/polkit-mate-authentication-agent-1; do
        if [ -x "$agent" ]; then
            "$agent" >/tmp/puppy50-polkit.log 2>&1 &
            break
        fi
    done
) &
'''
MIGRATION_MARKER = '"$B" sleep 8\nemit P50_STAGE_START\n'
DIAGNOSTIC = r'''(
    "$B" sleep 12
    {
        if pgrep -u user -x tint2 >/dev/null 2>&1 && pgrep -u user -x nm-applet >/dev/null 2>&1 && pgrep -u user -x p50-status >/dev/null 2>&1 && pgrep -u user -f '[f]irefox' >/dev/null 2>&1; then
            printf 'P50_V110_UI_OK\n'
        else
            printf 'P50_V110_UI_MISSING\n'
        fi
    } >/dev/ttyS0 2>&1
) &
'''


def patch_main(text):
    if text.count(STATUS_LINE) != 1 or 'P50_V110_FAST_AUTOSTART' in text:
        raise ValueError('Unexpected or already patched autostart hook')
    checks = '''
\t\tgrep -Fqx 'tint2 >/tmp/puppy50-tint2.log 2>&1 &' "${p50_autostart}" || panic "p50: unexpected tint2 startup"
\t\tgrep -Fqx 'nm-applet >/tmp/puppy50-network-applet.log 2>&1 &' "${p50_autostart}" || panic "p50: unexpected network startup"
\t\tgrep -Fqx 'firefox-esr file:///usr/share/puppy50web/index.html >/tmp/puppy50-firefox.log 2>&1 &' "${p50_autostart}" || panic "p50: unexpected browser startup"
\t\tcat > "${p50_autostart}" <<'P50_V110_FAST_AUTOSTART'
'''
    hook = checks + FAST_AUTOSTART + 'P50_V110_FAST_AUTOSTART\n'
    return text.replace(STATUS_LINE, STATUS_LINE + '\n' + hook, 1)


def patch_migration(text):
    if text.count(MIGRATION_MARKER) != 1 or 'P50_V110_UI_OK' in text:
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
