#!/usr/bin/env python3
"""Compare protected trees from two independently unpacked Live images."""

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path

PROTECTED = (
    'proc', 'dev', 'sys', 'etc/resolv.conf', 'usr/lib/firmware',
    'usr/lib/firefox-esr', 'usr/share/firefox-esr', 'etc/firefox-esr', 'etc/NetworkManager',
    'usr/lib/NetworkManager', 'etc/ssl', 'usr/share/ca-certificates',
    'usr/bin/nmcli', 'usr/sbin/NetworkManager', 'usr/local/sbin/puppy50-network-probe',
    'usr/lib/x86_64-linux-gnu/libnss3.so', 'usr/lib/x86_64-linux-gnu/libnssutil3.so',
    'usr/lib/x86_64-linux-gnu/libssl3.so', 'usr/lib/x86_64-linux-gnu/libnspr4.so',
    'usr/lib/x86_64-linux-gnu/libsoftokn3.so', 'usr/lib/x86_64-linux-gnu/libsmime3.so',
)


def snapshot(root):
    root = Path(root).resolve(strict=True)
    output = {}

    def walk(relative):
        path = root / relative
        if not os.path.lexists(path):
            output[relative.as_posix()] = {'kind': 'missing'}
            return
        info = path.lstat()
        record = {'mode': stat.S_IMODE(info.st_mode), 'uid': info.st_uid, 'gid': info.st_gid}
        if stat.S_ISLNK(info.st_mode):
            record.update(kind='symlink', target=os.readlink(path))
        elif stat.S_ISDIR(info.st_mode):
            record['kind'] = 'directory'
        elif stat.S_ISREG(info.st_mode):
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(chunk)
            record.update(kind='file', size=info.st_size, sha256=digest.hexdigest())
        else:
            record.update(kind='special', type=stat.S_IFMT(info.st_mode), device=info.st_rdev)
        try:
            record['xattrs'] = {name: os.getxattr(path, name, follow_symlinks=False).hex()
                                for name in sorted(os.listxattr(path, follow_symlinks=False))}
        except OSError as exc:
            raise RuntimeError(f'Unable to audit extended attributes on {relative}: {exc}') from exc
        output[relative.as_posix()] = record
        if record['kind'] == 'directory':
            for child in sorted(path.iterdir(), key=lambda p: p.name):
                walk(relative / child.name)

    for relative in PROTECTED:
        walk(Path(relative))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('candidate', type=Path)
    args = parser.parse_args()
    left, right = snapshot(args.baseline), snapshot(args.candidate)
    differing = [key for key in sorted(set(left) | set(right)) if left.get(key) != right.get(key)]
    print(json.dumps({'protected_entries_baseline': len(left), 'protected_entries_candidate': len(right),
                      'difference_count': len(differing), 'first_differences': differing[:50]}, indent=2))
    if differing:
        raise SystemExit('Protected trees differ')


if __name__ == '__main__':
    main()
