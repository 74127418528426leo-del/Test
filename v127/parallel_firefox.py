#!/usr/bin/env python3
"""Experimental startup patch: start real Firefox in parallel with Openbox.

Runs Firefox unprivileged in the same authenticated X11, DBus session
and original content-sandbox configuration. Doesn't fake screenshots,
disable networking, or change physical recovery. Run ONLY against a
disposable extracted staged initramfs already patched through v126.
"""
from pathlib import Path
import argparse

ORIGINAL = '''\t/usr/bin/dbus-run-session -- /usr/bin/openbox-session \\
\t>/run/p50-v123-openbox.log 2>&1 &'''
REPLACEMENT = '''\t/usr/bin/dbus-run-session -- /bin/sh -c '
        printf "P50_V127_FIREFOX_DIRECT_EXEC %s\\\\n" "$(cat /proc/uptime)" >/dev/ttyS0
        firefox-esr file:///usr/share/puppy50web/index.html >/tmp/puppy50-firefox.log 2>&1 &
        exec /usr/bin/openbox-session
    ' \\
    >/run/p50-v123-openbox.log 2>&1 &'''

def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():
        raise ValueError("Refuse to touch physical OS, extracted initramfs only")
    p=root/'usr/lib/live/boot/9990-main.sh'
    if p.is_symlink() or not p.is_file():
        raise ValueError('Expected a regular live-boot source')
    src=p.read_text()
    prereqs=('P50_V123_BEFORE_PID1','P50_V125_DRM_PREREQ',
             'P50_V126_PRESERVE_XSOCKET','P50_V118_EARLY_USER')
    if any(t not in src for t in prereqs):
        raise ValueError('Prerequisite early-authenticated X11 and RAM-safe hooks missing')
    if src.count(ORIGINAL)!=1 or 'P50_V127_FIREFOX_DIRECT_EXEC' in src:
        raise ValueError(f'Unexpected early Openbox launcher layout; matches={src.count(ORIGINAL)}')
    p.write_text(src.replace(ORIGINAL,REPLACEMENT,1))
    return p

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
