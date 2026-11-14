#!/usr/bin/env python3
"""Research-only: install audited Firefox frontend startupCache in fresh nonroot profile.

The archive is built offline using the identical Firefox ESR version and ONLY
anonymous startupCache filesystem nodes (no cookies/history/passwords/SQLite).
Extraction happens into the original volatile RAM overlay before Firefox starts.
No browser binary, sandbox, TLS, network config or fallback root changes.
"""
from pathlib import Path
import argparse
OWN='chown -R 1000:1000 "$p50_root/home/user/.mozilla" || panic "v139: could not grant profile to nonroot user"'
HOOK=r'''        # P50_V152_SEED_ANONYMOUS_STARTUP_CACHE: offline generated, no user data.
        p50_seed=/usr/share/puppy50/p50-startupcache.tar
        [ -f "$p50_seed" ] && [ ! -L "$p50_seed" ] || panic "v152: audited seed archive absent"
        [ "$(wc -c <"$p50_seed")" -gt 1024 ] || panic "v152: empty seed cache"
        tar -xf "$p50_seed" -C "$p50_root/home/user" || panic "v152: failed to restore prebuilt startupCache"
        chown -R 1000:1000 "$p50_root/home/user/.cache" "$p50_root/home/user/.mozilla" || panic "v152: seed ownership"
        printf 'P50_V152_STARTUP_CACHE_SEEDED %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
'''
def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Physical host modification refused')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if not p.is_file() or p.is_symlink():raise ValueError('Expected disposable initrd')
    s=p.read_text()
    required=('P50_V149_WEBRENDER_USERJS_READY','P50_V139_EMPTY_PROFILE_CREATED',
              'P50_V144_XORG_VT7_SELECTED','P50_V141_PRIORITY_EXPERIMENT',
              'P50_V127_FIREFOX_DIRECT_EXEC')
    if any(x not in s for x in required):raise ValueError('Secure actual-profile v149 prerequisites absent')
    if s.count(OWN)!=1 or 'P50_V152_STARTUP_CACHE_SEEDED' in s:
        raise ValueError('Unknown or previously patched profile bootstrap')
    p.write_text(s.replace(OWN,HOOK+OWN,1))
    return p
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
