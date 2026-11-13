#!/usr/bin/env python3
"""Research-only prefetch of immutable Firefox ELF pages during DRM setup.

The compressed SquashFS, Firefox binary, kernel and full-RAM recovery
initrd are unchanged. Does not turn off any Firefox security feature.
This is an explicitly unverified performance hypothesis until cold
Firefox first-frame and post-ejection network checks succeed.
"""
from pathlib import Path
import argparse

MARKER='        # P50_V125_DRM_PREREQ: test only.'
HOOK=r'''        # P50_V131_LIBXUL_READAHEAD: prefill up to 96MiB of libxul pages
        # concurrently with graphics initialization, using low-priority CPU.
        # Files stay on the original, authenticated read-only SquashFS.
        p50_lib="$p50_root/usr/lib/firefox-esr/libxul.so"
        [ -f "$p50_lib" ] && [ ! -L "$p50_lib" ] || panic "v131: expected immutable libxul missing"
        printf 'P50_V131_READAHEAD_STARTED %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
        (
            nice -n 10 dd if="$p50_lib" of=/dev/null bs=1048576 count=96 2>/dev/null
            printf 'P50_V131_READAHEAD_COMPLETE %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
        ) &
'''
def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():
        raise ValueError('Only disposable extracted initramfs data can be modified')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if not p.is_file() or p.is_symlink():
        raise ValueError('Missing real extracted initrd shell script')
    src=p.read_text()
    required=('P50_V127_FIREFOX_DIRECT_EXEC','P50_V126_PRESERVE_XSOCKET','P50_V125_DRM_PREREQ')
    if any(x not in src for x in required):
        raise ValueError('Requires stable v127 authenticated X11 + unprivileged Firefox')
    if src.count(MARKER)!=1 or 'P50_V131_LIBXUL_READAHEAD' in src:
        raise ValueError(f'Unexpected source layout or patched twice (matches={src.count(MARKER)})')
    p.write_text(src.replace(MARKER,HOOK+MARKER,1))
    return p
if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
