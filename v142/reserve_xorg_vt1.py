#!/usr/bin/env python3
"""Reserve Xorg vt1 while preserving serial and alternate systemd gettys.

Research only: early v136 Xorg attaches tty1 before systemd starts. The
default getty@tty1/autovt@tty1 may repaint that same VT and leave a BLACK
QEMU framebuffer even though secure Firefox and Xorg remain healthy.
The change masks only tty1 in the disposable live overlay, not network,
Firefox sandbox, other virtual terminals, serial getty, kernel or recovery.
"""
from pathlib import Path
import argparse
MARKER='        # P50_V125_DRM_PREREQ: test only.'
HOOK=r'''        # P50_V142_TTY1_FOR_EARLY_XORG: preserve screen ownership.
        for p50_name in getty@tty1.service autovt@tty1.service; do
            p50_unit="$p50_root/etc/systemd/system/$p50_name"
            [ ! -e "$p50_unit" ] && [ ! -L "$p50_unit" ] || panic "v142: existing tty1 unit override"
            ln -s /dev/null "$p50_unit" || panic "v142: cannot mask conflicting tty1 console"
        done
        printf 'P50_V142_TTY1_GETTY_DISABLED %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
'''
def patch(root:Path):
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Refuse physical host')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if not p.is_file() or p.is_symlink():raise ValueError('Expected unpacked initramfs live-boot')
    s=p.read_text()
    required=('P50_V123_BEFORE_PID1','P50_V125_DRM_PREREQ',
              'P50_V126_PRESERVE_XSOCKET','P50_V127_FIREFOX_DIRECT_EXEC')
    if any(x not in s for x in required):raise ValueError('Needs secured early Xorg/Firefox v136')
    if s.count(MARKER)!=1 or 'P50_V142_TTY1_FOR_EARLY_XORG' in s:
        raise ValueError('Unknown or already patched root')
    p.write_text(s.replace(MARKER,HOOK+MARKER,1))
    return p
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
