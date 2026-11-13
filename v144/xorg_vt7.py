#!/usr/bin/env python3
"""Research-only run early authenticated Xorg on VT7, not getty's VT1.

Retains tty1 serial/recovery, Firefox TLS/network and unprivileged sandbox.
No physical support is implied. This tests avoiding the post-switch-root
console repaint that can obscure a healthy browser X server.
"""
from pathlib import Path
import argparse

ORIG="/usr/lib/xorg/Xorg :0 -auth /home/user/.Xauthority -nolisten tcp -noreset vt1"
REPLACE="""printf 'P50_V144_XORG_VT7_SELECTED %s\\n' "$(cat /proc/uptime)" >/dev/ttyS0
/usr/lib/xorg/Xorg :0 -auth /home/user/.Xauthority -nolisten tcp -noreset vt7"""
def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir(): raise ValueError('Refuse host root')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if p.is_symlink() or not p.is_file(): raise ValueError('Expected extracted temporary initramfs file')
    s=p.read_text()
    prereqs=('P50_V123_BEFORE_PID1','P50_V125_DRM_PREREQ','P50_V126_PRESERVE_XSOCKET','P50_V127_FIREFOX_DIRECT_EXEC')
    if any(x not in s for x in prereqs):raise ValueError('Secure early-Xorg prerequisites absent')
    if s.count(ORIG)!=1 or 'P50_V144_XORG_VT7_SELECTED' in s:
        raise ValueError(f'Unexpected Xorg command, occurrences={s.count(ORIG)}')
    p.write_text(s.replace(ORIG,REPLACE,1))
    return p
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
