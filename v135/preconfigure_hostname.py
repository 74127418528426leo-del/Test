#!/usr/bin/env python3
"""Hypothesis only: create local hostname mapping before Firefox starts.

Tests whether the first Firefox launch waits for host name resolution while
systemd has not initialized the live network stack. External DNS, Firefox TLS,
browser sandbox, complete RAM verification and original fallback are unchanged.
"""
import argparse
from pathlib import Path

MARKER='        # P50_V131_LIBXUL_READAHEAD: prefill up to 96MiB of libxul pages'
HOOK=r'''        # P50_V135_HOSTNAME_RESOLUTION: only temporary staged root /etc/hosts.
        p50_hosts="$p50_root/etc/hosts"
        [ -f "$p50_hosts" ] && [ ! -L "$p50_hosts" ] || panic "v135: unsafe hosts file"
        if grep -Eq '(^|[[:space:]])localhost.localdomain([[:space:]]|$)' "$p50_hosts"; then
            printf 'P50_V135_HOST_ALREADY_MAPPED %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
        else
            printf '127.0.1.1 localhost.localdomain\n' >> "$p50_hosts" || panic "v135: hosts update failed"
            printf 'P50_V135_HOST_MAPPING_ADDED %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
        fi
'''
def patch(root:Path):
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Refuse to mutate real host')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if not p.is_file() or p.is_symlink():raise ValueError('Invalid extracted live root')
    s=p.read_text()
    if 'P50_V127_FIREFOX_DIRECT_EXEC' not in s or 'P50_V131_LIBXUL_READAHEAD' not in s:
        raise ValueError('Missing secure Firefox and pagecache prefetch')
    if s.count(MARKER)!=1 or 'P50_V135_HOSTNAME_RESOLUTION' in s:
        raise ValueError(f'Unexpected live-boot hook, marker count={s.count(MARKER)}')
    p.write_text(s.replace(MARKER,HOOK+MARKER,1))
    return p
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
