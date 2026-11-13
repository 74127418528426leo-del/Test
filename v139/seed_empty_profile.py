#!/usr/bin/env python3
"""Research-only explicit empty Firefox profile before nonroot startup.

Avoid default-profile discovery/migration overhead. The profile is newly
created in the volatile live overlay each cold boot; no cache, credentials,
browser source, TLS rules or sandbox settings are copied or modified.
"""
from pathlib import Path
import argparse
MARKER='        # P50_V131_LIBXUL_READAHEAD: prefill up to 96MiB of libxul pages'
OLD="/usr/bin/dbus-run-session -- /usr/bin/firefox-esr file:///usr/share/puppy50web/index.html"
NEW="/usr/bin/dbus-run-session -- /usr/bin/firefox-esr -profile /home/user/.mozilla/firefox/p50-default file:///usr/share/puppy50web/index.html"
HOOK=r'''        # P50_V139_EXPLICIT_EMPTY_FIREFOX_PROFILE: no shared startup cache.
        p50_profile="$p50_root/home/user/.mozilla/firefox/p50-default"
        [ ! -e "$p50_profile" ] && [ ! -L "$p50_profile" ] || panic "v139: existing profile prevents clean test"
        mkdir -p "$p50_profile" || panic "v139: could not create live empty profile"
        chmod 0700 "$p50_profile" || panic "v139: cannot set profile permissions"
        chown -R 1000:1000 "$p50_root/home/user/.mozilla" || panic "v139: could not grant profile to nonroot user"
        printf 'P50_V139_EMPTY_PROFILE_CREATED %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
'''
def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Refuse host filesystem mutation')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if not p.is_file() or p.is_symlink():raise ValueError('Expected extracted temporary initrd source')
    s=p.read_text()
    required=('P50_V127_FIREFOX_DIRECT_EXEC','P50_V133_PREFETCH_256MB_STARTED','P50_V135_HOSTNAME_RESOLUTION')
    if any(x not in s for x in required):raise ValueError('Safe v136 prerequisites missing')
    if s.count(MARKER)!=1 or s.count(OLD)!=1 or 'P50_V139_EMPTY_PROFILE_CREATED' in s:
        raise ValueError(f'Unexpected v136 source: marker={s.count(MARKER)} firefox={s.count(OLD)}')
    p.write_text(s.replace(MARKER,HOOK+MARKER,1).replace(OLD,NEW,1))
    return p
if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
