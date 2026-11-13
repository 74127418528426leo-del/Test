#!/usr/bin/env python3
"""Research: launch the original sandboxed Firefox ESR directly alongside Openbox.

The early Xorg is authenticated and preserved through switch-root by v126.
Firefox remains non-root and unchanged. Remove only duplicate Openbox-started
Firefox command in the volatile live account; keep all network applets/polkit.
"""
from pathlib import Path
import argparse

AUTO_MARKER='chmod 0700 "$p50_start" || panic "v123: cannot secure launcher"'
OPENBOX_MARKER="printf 'P50_V123_OPENBOX_START %s\\n' \"$(cat /proc/uptime)\" > /dev/ttyS0"
AUTO_HOOK=r'''
        # P50_V127_DIRECT_BROWSER: avoid starting two Firefox instances.
        p50_auto="$p50_root/home/user/.config/openbox/autostart"
        [ -f "$p50_auto" ] && [ ! -L "$p50_auto" ] || panic "v127: missing nonroot autostart"
        grep -Fq 'firefox-esr file:///usr/share/puppy50web/index.html' "$p50_auto" || panic "v127: unexpected autostart"
        sed -i 's|^firefox-esr file:|# v127 early nonroot Firefox moved to launcher: firefox-esr file:|' "$p50_auto" || panic "v127: cannot remove duplicate Firefox"
        grep -Fq '# v127 early nonroot Firefox moved' "$p50_auto" || panic "v127: duplicate Firefox removal unverified"
        printf 'P50_V127_BROWSER_START_RELOCATED %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
'''
FF_HOOK=r'''printf 'P50_V127_FIREFOX_DIRECT_EXEC %s\n' "$(cat /proc/uptime)" > /dev/ttyS0
setpriv --reuid=user --regid=user --init-groups \
    env HOME=/home/user USER=user LOGNAME=user DISPLAY=:0 \
    XDG_SESSION_TYPE=x11 XAUTHORITY=/home/user/.Xauthority XDG_RUNTIME_DIR=/run/user/1000 \
    /usr/bin/dbus-run-session -- /usr/bin/firefox-esr file:///usr/share/puppy50web/index.html \
    >/run/p50-v127-firefox.log 2>&1 &
'''


def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Do not patch host filesystem')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if p.is_symlink() or not p.is_file():raise ValueError('Unexpected boot script')
    src=p.read_text()
    if 'P50_V126_PRESERVE_XSOCKET' not in src or 'P50_V125_DRM_PREREQ' not in src:
        raise ValueError('Requires DRM-ready and persistent authenticated early X11')
    if 'P50_V127_DIRECT_BROWSER' in src or src.count(AUTO_MARKER)!=1 or src.count(OPENBOX_MARKER)!=1:
        raise ValueError('Unknown or already modified launcher layout')
    src=src.replace(AUTO_MARKER,AUTO_HOOK+AUTO_MARKER,1)
    src=src.replace(OPENBOX_MARKER,FF_HOOK+OPENBOX_MARKER,1)
    p.write_text(src)
    return p

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
