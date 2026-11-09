#!/usr/bin/env python3
"""Install a targeted, read-only prefetch service on the staged test path."""
import argparse
from pathlib import Path

MARK='\n\tFstab\n\tNetbase\n'
HOOK=r'''
\t# P50_TARGETED_PREFETCH: isolated diagnostic; unchanged full-RAM fallback.
\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
\t\tp50_unit="${rootmnt}/etc/systemd/system/p50-hot-prefetch.service"
\t\tp50_wants="${rootmnt}/etc/systemd/system/sysinit.target.wants"
\t\t[ ! -e "${p50_unit}" ] && [ ! -L "${p50_unit}" ] && [ ! -L "${p50_wants}" ] || panic "p50: unexpected page prefetch service"
\t\tmkdir -p "${p50_wants}" || panic "p50: cannot create prefetch directory"
\t\t[ ! -e "${p50_wants}/p50-hot-prefetch.service" ] && [ ! -L "${p50_wants}/p50-hot-prefetch.service" ] || panic "p50: prefetch already enabled"
\t\tcat > "${p50_unit}" <<'P50_TARGET_UNIT'
[Unit]
Description=Experimental Firefox targeted page-cache prefetch
DefaultDependencies=no
Requires=local-fs.target
After=local-fs.target
Before=sysinit.target
[Service]
Type=simple
ExecStart=/run/p50-stage/tools/p50-prefetch.sh
Nice=10
TimeoutStartSec=35
[Install]
WantedBy=sysinit.target
P50_TARGET_UNIT
\t\tln -s ../p50-hot-prefetch.service "${p50_wants}/p50-hot-prefetch.service" || panic "p50: cannot enable page prefetch"
\tfi
'''.replace('\\t','\t')

def patch_main(text):
    if text.count(MARK)!=1 or 'P50_TARGETED_PREFETCH' in text:raise ValueError('Unexpected or already patched boot script')
    return text.replace(MARK,HOOK+MARK,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify live root')
    path=root/'usr/lib/live/boot/9990-main.sh'
    if path.is_symlink() or not path.is_file():raise ValueError('Expected regular boot script')
    path.write_text(patch_main(path.read_text()))

if __name__=='__main__':main()
