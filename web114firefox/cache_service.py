#!/usr/bin/env python3
"""Install a bounded cache collector in a separate diagnostic unit."""
import argparse
from pathlib import Path
from cache_probe import REPORT

MARKER = '\n\tFstab\n\tNetbase\n'
if not REPORT.startswith('(\n') or not REPORT.endswith(') &\n'):
    raise ValueError('Unexpected capture report shape')
CAPTURE = '#!/bin/sh\nB=/run/p50-stage/tools/busybox\n' + REPORT[2:-4]
HOOK = r'''
\t# P50_V114_CACHE_SERVICE: diagnostic image only.
\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
\t\tp50_unit="${rootmnt}/etc/systemd/system/p50-cache-capture.service"
\t\tp50_wants="${rootmnt}/etc/systemd/system/graphical.target.wants"
\t\t[ ! -e "${p50_unit}" ] && [ ! -L "${p50_unit}" ] && [ ! -L "${p50_wants}" ] || panic "p50: unexpected cache service"
\t\tmkdir -p "${p50_wants}" || panic "p50: cannot create cache service directory"
\t\t[ ! -e "${p50_wants}/p50-cache-capture.service" ] && [ ! -L "${p50_wants}/p50-cache-capture.service" ] || panic "p50: cache service already enabled"
\t\tcat > "${p50_unit}" <<'P50_V114_CACHE_UNIT'
[Unit]
Description=Experimental isolated Firefox startup cache capture
After=network.target
[Service]
Type=simple
ExecStart=/bin/sh /run/p50-stage/tools/p50-cache-capture
[Install]
WantedBy=graphical.target
P50_V114_CACHE_UNIT
\t\tln -s ../p50-cache-capture.service "${p50_wants}/p50-cache-capture.service" || panic "p50: cannot enable cache service"
\tfi
'''.replace('\\t','\t')


def patch_main(text):
    if text.count(MARKER) != 1 or 'P50_V114_CACHE_SERVICE' in text:
        raise ValueError('Unexpected or already patched live boot main')
    return text.replace(MARKER, HOOK + MARKER, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    if root == Path('/'):
        raise ValueError('Refusing to modify the running system')
    main_file = root/'usr/lib/live/boot/9990-main.sh'
    tool = root/'usr/lib/p50-stage/p50-cache-capture'
    if main_file.is_symlink() or not main_file.is_file() or tool.exists() or tool.is_symlink():
        raise ValueError('Unexpected initramfs files')
    updated = patch_main(main_file.read_text())
    tool.write_text(CAPTURE)
    tool.chmod(0o755)
    main_file.write_text(updated)


if __name__ == '__main__':
    main()
