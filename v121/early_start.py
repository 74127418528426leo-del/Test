#!/usr/bin/env python3
"""Research only: attempt a direct non-root X11 session as soon as basic.target.

Patch the v120 guarded staged initrd ONLY. Do not alter released ISO, root,
kernel, network services, full-RAM fallback or Firefox sandbox.
"""
from pathlib import Path
import argparse

OLD='After=systemd-logind.service systemd-user-sessions.service\nWants=systemd-logind.service'
NEW='After=systemd-logind.service\nWants=systemd-logind.service'
NEEDLE="        printf 'P50_V120_DIRECT_READY %s\\n' \"$(cat /proc/uptime)\" >/dev/ttyS0"
EARLY=r'''        # P50_V121_BASIC_TARGET: register the nonroot X11 session independently of
        # graphical.target; keep the target's original display-manager Wants as well.
        p50_basic="@{rootmnt}/etc/systemd/system/basic.target.wants"
        mkdir -p "$p50_basic" || panic "v121: cannot create basic.target link directory"
        [ ! -e "$p50_basic/display-manager.service" ] && [ ! -L "$p50_basic/display-manager.service" ] || panic "v121: conflicting early session unit"
        ln -s ../display-manager.service "$p50_basic/display-manager.service" || panic "v121: early display start link failed"
        printf 'P50_V121_EARLY_SESSION_REGISTERED %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
'''.replace('@{',chr(36)+'{')


def patch(root: Path):
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():
        raise ValueError('Refusing non-disposable initramfs root')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if not p.is_file() or p.is_symlink():
        raise ValueError('Expected real initramfs live script')
    s=p.read_text()
    if 'P50_V120_DIRECT' not in s or 'P50_V118_EARLY_USER' not in s or 'P50_V119_LIVECONFIG_DISABLED' not in s:
        raise ValueError('v121 requires previous guarded staged boot changes')
    if 'P50_V121_BASIC_TARGET' in s or s.count(OLD)!=1 or s.count(NEEDLE)!=1:
        raise ValueError('Unexpected direct-session source layout or already patched')
    p.write_text(s.replace(OLD,NEW,1).replace(NEEDLE,EARLY+NEEDLE,1))
    return p


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
