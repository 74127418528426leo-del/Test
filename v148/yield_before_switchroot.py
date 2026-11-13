#!/usr/bin/env python3
"""Research-only yield initramfs main thread so pre-systemd Firefox can paint.

After the authenticated nonroot Xorg/Firefox launcher is backgrounded, give
the real browser 1.8 seconds while root mount and X11 stay available, then
continue the EXACT original live-boot/switch-root/systemd and migration path.
This is not a fake/warm-boot measurement. Never claim success without real
QEMU framebuffer Firefox, verified RAM copy, safe eject, fresh HTTP200.
"""
from pathlib import Path
import argparse

MARKER='chroot "$p50_root" /usr/local/sbin/p50-v123-start-x >/dev/ttyS0 2>&1 &'
HOOK=r'''
        # P50_V148_YIELD_EARLY_FIREFOX_BEFORE_SYSTEMD:
        # foreground boot work yields to existing secure X11/Firefox process.
        printf 'P50_V148_YIELD_BEGIN %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
        sleep 1.8
        printf 'P50_V148_YIELD_DONE %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
'''
def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Refusing physical root')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if p.is_symlink() or not p.is_file():raise ValueError('Expected extracted disposable live boot')
    data=p.read_text()
    prerequisites=('P50_V123_BEFORE_PID1','P50_V144_XORG_VT7_SELECTED',
        'P50_V141_PRIORITY_EXPERIMENT','P50_V139_EMPTY_PROFILE_CREATED',
        'P50_V137_OPENBOX_DEFERRED')
    if any(x not in data for x in prerequisites):
        raise ValueError('Requires authenticated v147 early Firefox with VT7')
    if data.count(MARKER)!=1 or 'P50_V148_YIELD_BEGIN' in data:
        raise ValueError('Unknown/multiple launcher or already installed')
    data=data.replace(MARKER,MARKER+HOOK,1)
    p.write_text(data)
    return p

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
