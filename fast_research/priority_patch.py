#!/usr/bin/env python3
"""Change only the Firefox nice value inside a disposable extracted initrd."""
from pathlib import Path
import sys

OLD = '/usr/bin/nice -n -10 setpriv --reuid=user --regid=user --init-groups'
NEW = '/usr/bin/nice -n -19 setpriv --reuid=user --regid=user --init-groups'


def patch_file(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Expected ordinary extracted boot script')
    s = path.read_text()
    if ('P50_V149_SOFTWARE_WEBRENDER' not in s or
            'P50_V127_FIREFOX_DIRECT_EXEC' not in s or s.count(OLD) != 1 or NEW in s):
        raise ValueError('Unexpected baseline or already patched boot script')
    path.write_text(s.replace(OLD, NEW, 1))


if __name__ == '__main__':
    root = Path(sys.argv[1]).resolve(strict=True)
    if root == Path('/') or not root.is_dir():
        raise ValueError('Refuse host filesystem')
    patch_file(root / 'usr/lib/live/boot/9990-main.sh')
