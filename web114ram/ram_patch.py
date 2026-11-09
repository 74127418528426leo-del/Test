#!/usr/bin/env python3
"""Isolated experiments; retain staged-copy SHA-256 and reserve checks."""
import argparse
from pathlib import Path

HASH='actual=$("$B" sha256sum "$COPY") || fail \'copy hash failed\''
GUARD='[ "$mem_k" -ge $((need_k + 393216)) ] || fail \'insufficient available memory and reserve\''


def patch_hash(text,mode):
    if mode not in ('profile','openssl','coreutils','retry'):raise ValueError('Unknown experiment')
    if text.count(HASH)!=1:raise ValueError('Unexpected copy hash command')
    cmd={'profile':HASH,'retry':HASH,'openssl':'actual=$(/usr/bin/openssl dgst -sha256 -r "$COPY") || fail \'copy hash failed\'','coreutils':'actual=$(/usr/bin/sha256sum "$COPY") || fail \'copy hash failed\''}[mode]
    return text.replace(HASH,cmd,1)


def memory_retry_function():
    return r'''p50_wait_memory() {
    p50_attempt=0
    while :; do
        p50_attempt=$((p50_attempt + 1))
        mem_k=$("$B" awk '/^MemAvailable:/ {print $2}' /proc/meminfo) || return 2
        case "$mem_k" in ''|*[!0-9]*) return 2;; esac
        emit "P50_V114_MEM_AVAILABLE_KIB=$mem_k ATTEMPT=$p50_attempt"
        [ "$mem_k" -ge $((need_k + 393216)) ] && return 0
        [ "$p50_attempt" -ge 10 ] && return 1
        "$B" sleep 2 || return 2
    done
}
'''


def patch_source(text,mode):
    if 'P50_V114_RAM_PROFILE' in text or text.count(GUARD)!=1:raise ValueError('Unexpected or already patched guard')
    text=patch_hash(text,mode)
    commands={'profile':HASH,'retry':HASH,'openssl':'actual=$(/usr/bin/openssl dgst -sha256 -r "$COPY") || fail \'copy hash failed\'','coreutils':'actual=$(/usr/bin/sha256sum "$COPY") || fail \'copy hash failed\''}
    command=commands[mode]
    if text.count(command)!=1:raise ValueError('Unexpected selected hash command')
    text=text.replace(command,'emit "P50_V114_HASH_ENGINE='+mode+'"\n'+command,1)
    if mode=='retry':
        text=text.replace(GUARD,memory_retry_function()+'p50_wait_memory || fail \'insufficient available memory and reserve\'',1)
    markers=[('emit P50_STAGE_START\n','STAGE_START'),('emit P50_STAGE_COPYING\n','COPY_BEGIN'),('[ "$("$B" stat -c %s "$COPY")" = "$size" ] || fail \'copied size differs\'\n','COPY_END'),('actual=${actual%% *}\n','HASH_READ_END'),('emit P50_STAGE_COPY_VERIFIED\n','HASH_OK'),('SWITCH_ATTEMPTED=1\n','SWITCH_BEGIN'),('emit P50_STAGE_READY\n','READY')]
    for original,label in markers:
        if text.count(original)!=1:raise ValueError('Unexpected staging marker: '+label)
        diagnostic='emit "P50_V114_RAM_PROFILE '+label+' UPTIME=$("$B" awk \'{print $1}\' /proc/uptime)"\n'
        text=text.replace(original,original+diagnostic,1)
    return text


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('mode',choices=('profile','openssl','coreutils','retry'));a=p.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify the running system')
    path=root/'usr/lib/p50-stage/p50-migrate.sh'
    if path.is_symlink() or not path.is_file():raise ValueError('Expected regular migration script')
    path.write_text(patch_source(path.read_text(),a.mode))

if __name__=='__main__':main()
