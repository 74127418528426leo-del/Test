#!/usr/bin/env python3
"""Research-only allow nonroot Firefox moderate -5 nice priority at first startup.

Root launches coreutils nice which immediately calls setpriv and drops to
unprivileged user with original Firefox sandbox. No capabilities are retained.
All original root/firmware, network, rescue, and RAM-copy code unchanged.
"""
from pathlib import Path
import argparse
ORIG="setpriv --reuid=user --regid=user --init-groups"
MARKER="        # P50_V131_LIBXUL_READAHEAD: prefill up to 96MiB of libxul pages"
HOOK=r'''        # P50_V141_PRIORITY_EXPERIMENT: only Firefox process and children,
        # not the network manager, Xorg or system migration thread.
        [ -x "$p50_root/usr/bin/nice" ] || panic "v141: coreutils nice unavailable"
        printf 'P50_V141_FIREFOX_EARLY_PRIORITY_CONFIGURED %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
'''
PSMARK="printf '\\n-- display and session processes --\\n'"
PSHOOK=r'''printf 'P50_V141_ACTUAL_NICE_VALUES\n'
    ps -eo pid,ni,user,comm | grep -E '[f]irefox-esr|[o]penbox|[X]org' | head -15 || true
    '''
def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Refuse host filesystem')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if not p.is_file() or p.is_symlink():raise ValueError('Expected extracted boot script')
    s=p.read_text()
    required=('P50_V133_PREFETCH_256MB_STARTED','P50_V135_HOSTNAME_RESOLUTION','P50_V127_FIREFOX_DIRECT_EXEC','P50_V124_POSTROOT_X11_FORENSIC')
    if any(x not in s for x in required):raise ValueError('Original secure boot prerequisites absent')
    if s.count(ORIG)!=2 or s.count(MARKER)!=1 or s.count(PSMARK)!=1 or 'P50_V141_PRIORITY_EXPERIMENT' in s:
        raise ValueError(f'Unexpected source: orig={s.count(ORIG)} marker={s.count(MARKER)} psmarker={s.count(PSMARK)}')
    s=s.replace(ORIG,"/usr/bin/nice -n -5 "+ORIG,1)
    s=s.replace(MARKER,HOOK+MARKER,1)
    s=s.replace(PSMARK,PSHOOK+PSMARK,1)
    p.write_text(s)
    return p
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
