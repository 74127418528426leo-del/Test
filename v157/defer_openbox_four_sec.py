#!/usr/bin/env python3
"""Research-only compare 4s vs proven 2s Openbox startup delay.

Firefox starts immediately under same nonroot authenticated VT7 X11 and
DBus; only desktop window manager launch waits two EXTRA seconds.
If Firefox is not genuinely visible and interactive after safe RAM migration,
reject. Root, kernel, full-RAM rescue, Firefox sandbox unchanged.
"""
from pathlib import Path
import argparse
OLD='/usr/bin/dbus-run-session -- /bin/sh -c "sleep 2; exec /usr/bin/openbox-session"'
NEW='/usr/bin/dbus-run-session -- /bin/sh -c "sleep 4; exec /usr/bin/openbox-session"'
MARKER="printf 'P50_V137_OPENBOX_DEFERRED %s\\n'"
ADD="""printf 'P50_V157_OPENBOX_FOUR_SECONDS %s\\n' "$(cat /proc/uptime)" >/dev/ttyS0
        """
def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path("/") or not root.is_dir():raise ValueError('Do not touch physical host')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if not p.is_file() or p.is_symlink():raise ValueError('Expected extracted initrd script')
    s=p.read_text()
    for req in ('P50_V137_OPENBOX_DEFERRED','P50_V127_FIREFOX_DIRECT_EXEC','P50_V144_XORG_VT7_SELECTED',
                'P50_V146_HIGHER_FIREFOX_PRIORITY_REQUESTED','P50_V149_WEBRENDER_USERJS_READY'):
        if req not in s:raise ValueError('Missing v151 source prerequisite: '+req)
    if s.count(OLD)!=1 or s.count(MARKER)!=1 or 'P50_V157_OPENBOX_FOUR_SECONDS' in s:
        raise ValueError(f'Unknown v151 Openbox shell (matches={s.count(OLD)})')
    p.write_text(s.replace(OLD,NEW,1).replace(MARKER,ADD+MARKER,1))
    return p

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
