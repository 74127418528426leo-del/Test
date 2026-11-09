#!/usr/bin/env python3
"""Instrument an isolated test boot to export only its Firefox UI startup cache."""
import argparse
from pathlib import Path
MARKER='"$B" sleep 8\nemit P50_STAGE_START\n'
REPORT=r'''(
    # Firefox writes the cache on an idle timer (historically about 60 s), so
    # wait for its completed file instead of assuming it exists at startup.
    "$B" sleep 25
    {
        printf '\nP50_V114_FIREFOX_CACHE_PROBE_BEGIN\n'
        p50_wait=0
        while [ "$p50_wait" -lt 140 ]; do
            p50_count="$(find /home/user/.cache/mozilla/firefox /home/user/.config/mozilla/firefox -type f -name 'startupCache.8.little' -print 2>/dev/null | wc -l)"
            if [ "$p50_count" = 1 ]; then
                p50_cache="$(find /home/user/.cache/mozilla/firefox /home/user/.config/mozilla/firefox -type f -name 'startupCache.8.little' -print 2>/dev/null)"
                if [ -s "$p50_cache" ]; then "$B" sleep 3; break; fi
            fi
            "$B" sleep 5
            p50_wait=$((p50_wait + 5))
        done
        printf '%s\n' 'Firefox local profile cache candidates:'
        find /home/user/.cache/mozilla/firefox /home/user/.config/mozilla/firefox -type f -name 'startupCache.8.little' -print 2>/dev/null || true
        p50_count="$(find /home/user/.cache/mozilla/firefox /home/user/.config/mozilla/firefox -type f -name 'startupCache.8.little' -print 2>/dev/null | wc -l)"
        if [ "$p50_count" = 1 ]; then
            p50_cache="$(find /home/user/.cache/mozilla/firefox /home/user/.config/mozilla/firefox -type f -name 'startupCache.8.little' -print 2>/dev/null)"
            if cp "$p50_cache" /run/p50-stage/v114-startupcache.bin && [ -s /run/p50-stage/v114-startupcache.bin ]; then
                stat -c 'P50_V114_CACHE_BYTES=%s' /run/p50-stage/v114-startupcache.bin
                sha256sum /run/p50-stage/v114-startupcache.bin | sed 's/^/P50_V114_CACHE_SHA256=/'
                if /usr/bin/curl --fail --silent --show-error --connect-timeout 4 --max-time 20 --noproxy '*' --data-binary @/run/p50-stage/v114-startupcache.bin http://10.0.2.2:8767/cache -o /dev/null; then
                    printf 'P50_V114_CACHE_EXPORT_OK\n'
                else
                    printf 'P50_V114_CACHE_EXPORT_FAILED\n'
                fi
            else
                printf 'P50_V114_CACHE_COPY_FAILED\n'
            fi
        else
            printf 'P50_V114_CACHE_PATH_COUNT=%s\n' "$p50_count"
        fi
        printf 'P50_V114_FIREFOX_CACHE_PROBE_END\n'
    } >/dev/ttyS0 2>&1
) &
'''
def instrument(text):
    if text.count(MARKER)!=1 or 'P50_V114_FIREFOX_CACHE_PROBE_BEGIN' in text:raise ValueError('Unexpected or already instrumented migration script')
    return text.replace(MARKER,REPORT+MARKER,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify the running system')
    path=root/'usr/lib/p50-stage/p50-migrate.sh'
    if not path.is_file() or path.is_symlink():raise ValueError('Expected a regular migration script')
    path.write_text(instrument(path.read_text()))
if __name__=='__main__':main()
