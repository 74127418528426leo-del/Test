#!/usr/bin/env python3
"""Research-only defer Openbox (not Firefox) by 2 seconds.

Early secure Xorg and independent sandboxed nonroot Firefox remain unchanged.
The full original Openbox session, Wi-Fi UI and polkit run automatically later.
Safely applicable only to disposable initramfs with v136 prerequisites.
"""
from pathlib import Path
import argparse

OLD="/usr/bin/dbus-run-session -- /usr/bin/openbox-session"
NEW='/usr/bin/dbus-run-session -- /bin/sh -c "sleep 2; exec /usr/bin/openbox-session"'
def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir(): raise ValueError('Refusing host filesystem')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if p.is_symlink() or not p.is_file(): raise ValueError('Missing extracted boot source')
    s=p.read_text()
    required=('P50_V127_FIREFOX_DIRECT_EXEC','P50_V135_HOSTNAME_RESOLUTION','P50_V133_PREFETCH_256MB_STARTED','P50_V126_PRESERVE_XSOCKET')
    if any(x not in s for x in required):
        raise ValueError('Secure DRM/Xauth/Firefox plus hosts/256MiB prerequisites absent')
    if s.count(OLD)!=1 or 'P50_V137_OPENBOX_DEFERRED' in s:
        raise ValueError(f'Expected exactly one Openbox launcher: {s.count(OLD)}')
    patched=s.replace(OLD,NEW,1)
    marker="printf 'P50_V123_OPENBOX_START %s\\n' \"$(cat /proc/uptime)\" > /dev/ttyS0"
    if patched.count(marker)!=1:
        raise ValueError(f'Expected Openbox start marker exactly once, got {patched.count(marker)}')
    patched=patched.replace(marker,"printf 'P50_V137_OPENBOX_DEFERRED %s\\n' \"$(cat /proc/uptime)\" > /dev/ttyS0\n"+marker,1)
    p.write_text(patched)
    return p
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('extracted_root',type=Path)
    print(patch(p.parse_args().extracted_root))
