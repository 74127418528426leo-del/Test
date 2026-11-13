#!/usr/bin/env python3
"""Research only: avoid redundant late live-config in staged fast boot.

The original v115 full-RAM recovery initrd and public v117 ISO are preserved.
Run AFTER the v118 initramfs nonroot-user patch, BEFORE v120 direct X11 patch.
"""
import argparse
from pathlib import Path

MARKER="\n\tFstab\n\tNetbase\n"
HOOK=r'''
    # P50_V119_LIVECONFIG_DISABLED: staged fast boot only, NOT physical-certified.
    if [ -z "@{TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
        p50_mask="@{rootmnt}/etc/systemd/system/live-config.service"
        [ ! -e "$p50_mask" ] && [ ! -L "$p50_mask" ] || panic "v122: unexpected live-config override"
        grep -q '^user:' "@{rootmnt}/etc/passwd" || panic "v122: unprepared user"
        ln -s /dev/null "$p50_mask" || panic "v122: cannot mask late live-config"
        printf 'P50_V119_LIVECONFIG_DISABLED %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
    fi
'''.replace('\n    ','\n\t').replace('@{',chr(36)+'{')


def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():
        raise ValueError('Only a disposable unpacked initramfs may be changed')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if p.is_symlink() or not p.is_file():
        raise ValueError('Missing expected live boot shell script')
    src=p.read_text()
    if src.count(MARKER)!=1 or 'P50_V119_LIVECONFIG_DISABLED' in src:
        raise ValueError('Unrecognized or already patched live boot')
    if 'P50_V118_EARLY_USER' not in src:
        raise ValueError('Early-user prerequisite not installed')
    p.write_text(src.replace(MARKER,HOOK+MARKER,1))
    return p

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
