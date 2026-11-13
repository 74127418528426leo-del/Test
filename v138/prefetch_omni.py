#!/usr/bin/env python3
"""Puppy50 research-only: prime immutable Firefox omni.ja front-end cache.

Firefox's Gre/XUL front-end JS lives in omni.ja. This tests whether reading
both shipped archives during early DRM saves cold first Firefox frame time.
No browser code/prefs, TLS, sandbox, network, root or recovery is modified.
"""
from pathlib import Path
import argparse

MARKER='        # P50_V131_LIBXUL_READAHEAD: prefill up to 96MiB of libxul pages'
HOOK=r'''        # P50_V138_OMNI_PREFETCH: read both signed immutable Firefox
        # packaged JS/resource archives, in parallel with early Xorg.
        p50_omni="$p50_root/usr/lib/firefox-esr/omni.ja"
        p50_app_omni="$p50_root/usr/lib/firefox-esr/browser/omni.ja"
        [ -f "$p50_omni" ] && [ ! -L "$p50_omni" ] || panic "v138: missing Firefox omni archive"
        [ -f "$p50_app_omni" ] && [ ! -L "$p50_app_omni" ] || panic "v138: missing Firefox app omni archive"
        (
            printf 'P50_V138_OMNI_READAHEAD_START %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
            nice -n 10 dd if="$p50_omni" of=/dev/null bs=1048576 2>/dev/null || exit 1
            nice -n 10 dd if="$p50_app_omni" of=/dev/null bs=1048576 2>/dev/null || exit 1
            printf 'P50_V138_OMNI_READAHEAD_DONE %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
        ) &
'''
def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Only disposable root allowed')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if not p.is_file() or p.is_symlink():raise ValueError('Invalid initrd script')
    s=p.read_text()
    must=('P50_V135_HOSTNAME_RESOLUTION','P50_V133_PREFETCH_256MB_STARTED','P50_V127_FIREFOX_DIRECT_EXEC','P50_V126_PRESERVE_XSOCKET')
    if any(x not in s for x in must):raise ValueError('Secure v136 prerequisites absent')
    if s.count(MARKER)!=1 or 'P50_V138_OMNI_PREFETCH' in s:raise ValueError(f'Unexpected source count {s.count(MARKER)}')
    p.write_text(s.replace(MARKER,HOOK+MARKER,1))
    return p
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
