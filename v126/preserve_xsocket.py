#!/usr/bin/env python3
"""Research-only QEMU pre-PID1 X11 socket continuity experiment.

This prevents systemd's late tmp.mount from hiding the X11 UNIX socket
created in the volatile live overlay before switch-root. No Xauth, sandbox,
kernel, root image or post-ejection safety checks are weakened.
"""
from pathlib import Path
import argparse

MARKER="cat > \"$p50_start\" <<'P50_V123_START_X'"
HOOK=r'''
        # P50_V126_PRESERVE_XSOCKET: staged fast boot only.
        # The original live root overlay's /tmp is already volatile RAM, so
        # masking late tmp.mount preserves the early Xorg socket across PID1.
        p50_tmp="$p50_root/etc/systemd/system/tmp.mount"
        [ ! -e "$p50_tmp" ] && [ ! -L "$p50_tmp" ] || panic "v126: unexpected tmp.mount override"
        [ -d "$p50_root/tmp" ] && [ ! -L "$p50_root/tmp" ] || panic "v126: unsafe live /tmp"
        chmod 1777 "$p50_root/tmp" || panic "v126: cannot secure tmp permissions"
        ln -s /dev/null "$p50_tmp" || panic "v126: could not mask duplicate systemd tmp mount"
        printf 'P50_V126_EARLY_SOCKET_PRESERVED %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
'''

def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Refusing host filesystem')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if p.is_symlink() or not p.is_file():raise ValueError('Missing extracted boot script')
    s=p.read_text()
    if s.count(MARKER)!=1 or 'P50_V126_PRESERVE_XSOCKET' in s:
        raise ValueError('Unexpected boot initrd or previously patched')
    if 'P50_V125_DRM_PREREQ' not in s or 'P50_V123_BEFORE_PID1' not in s:
        raise ValueError('DRM and early-Xorg safety prerequisites absent')
    p.write_text(s.replace(MARKER,HOOK+MARKER,1))
    return p

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
