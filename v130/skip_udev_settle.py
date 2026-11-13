#!/usr/bin/env python3
"""Research-only remove global udev settle from fast QEMU DRM startup.

Prerequisites: authenticated v127 Firefox, v125 bochs DRM, v126 socket continuity.
The v125 /dev/dri/card0 char-device wait and fail-closed panic remain unchanged.
This tests one hypothesis: global udev settle unnecessarily blocks early Xorg.
No kernel, secure browser config, recovery initrd or root is changed.
"""
from pathlib import Path
import argparse

OLD='udevadm settle >/dev/null 2>&1 || panic "v125: cannot settle DRM"'
NEW='printf \'P50_V130_SKIP_GLOBAL_UDEV_SETTLE %s\\n\' "$(cat /proc/uptime)" >/dev/ttyS0'
PREREQS=('P50_V125_DRM_PREREQ','P50_V126_PRESERVE_XSOCKET','P50_V127_FIREFOX_DIRECT_EXEC')
def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():
        raise ValueError('Refusing to patch physical host filesystem')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if not p.is_file() or p.is_symlink():raise ValueError('Expected disposable extracted initrd script')
    src=p.read_text()
    if any(x not in src for x in PREREQS):
        raise ValueError('Missing previous RAM-safe secure X11/Firefox launch prerequisite')
    if src.count(OLD)!=1 or 'P50_V130_SKIP_GLOBAL_UDEV_SETTLE' in src:
        raise ValueError(f'Unexpected udev settle source count {src.count(OLD)}')
    if 'while [ "$p50_drm_attempt" -lt 30 ] && [ ! -c "$p50_root/dev/dri/card0" ]' not in src:
        raise ValueError('Missing fail-closed DRM card0 device wait')
    p.write_text(src.replace(OLD,NEW,1))
    return p

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
