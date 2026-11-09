#!/usr/bin/env python3
"""Install a temporary page-cache residency probe in the staged fast path."""
import argparse
from pathlib import Path

MARK='\n\tFstab\n\tNetbase\n'
HOOK=r'''
\t# P50_HOT_PROBE_SERVICE: temporary diagnostic; no mutation of recovery.
\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
\t\tp50_unit="${rootmnt}/etc/systemd/system/p50-hotpages.service"
\t\tp50_wants="${rootmnt}/etc/systemd/system/sysinit.target.wants"
\t\t[ ! -e "${p50_unit}" ] && [ ! -L "${p50_unit}" ] && [ ! -L "${p50_wants}" ] || panic "p50: unexpected page diagnostic"
\t\tmkdir -p "${p50_wants}" || panic "p50: cannot create page diagnostic directory"
\t\t[ ! -e "${p50_wants}/p50-hotpages.service" ] && [ ! -L "${p50_wants}/p50-hotpages.service" ] || panic "p50: page diagnostic already enabled"
\t\tcat > "${p50_unit}" <<'P50_HOT_UNIT'
[Unit]
Description=Temporary Firefox page-residency diagnostic
DefaultDependencies=no
Requires=local-fs.target
After=local-fs.target
Before=sysinit.target
[Service]
Type=simple
ExecStart=/run/p50-stage/tools/p50-hot-probe.sh
TimeoutStartSec=35
[Install]
WantedBy=sysinit.target
P50_HOT_UNIT
\t\tln -s ../p50-hotpages.service "${p50_wants}/p50-hotpages.service" || panic "p50: cannot enable page diagnostic"
\tfi
'''.replace('\\t','\t')

def patch_main(text):
    if text.count(MARK)!=1 or 'P50_HOT_PROBE_SERVICE' in text:raise ValueError('Unexpected or already patched main')
    return text.replace(MARK,HOOK+MARK,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify live root')
    path=root/'usr/lib/live/boot/9990-main.sh'
    if path.is_symlink() or not path.is_file():raise ValueError('Expected regular boot script')
    path.write_text(patch_main(path.read_text()))

if __name__=='__main__':main()
