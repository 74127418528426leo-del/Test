#!/usr/bin/env python3
"""Prune translations outside English and Spanish in an extracted live root."""

import argparse
import json
import os
import re
import shutil
import stat
from pathlib import Path


def regular_bytes(path: Path) -> int:
    if path.is_symlink():
        return 0
    total = 0
    for parent, _dirs, files in os.walk(path, followlinks=False):
        for name in files:
            info = (Path(parent) / name).lstat()
            if stat.S_ISREG(info.st_mode):
                total += info.st_size
    return total


def prune(root: Path) -> dict:
    root = root.resolve(strict=True)
    if root == Path('/') or not root.is_dir():
        raise ValueError('refusing unsafe filesystem root')
    locale_dir = root
    for part in ('usr', 'share', 'locale'):
        locale_dir = locale_dir / part
        if locale_dir.is_symlink() or not locale_dir.is_dir():
            raise ValueError(f'expected a non-symlink directory: {locale_dir}')
    removed = []
    removed_bytes = 0
    for item in sorted(locale_dir.iterdir()):
        if re.match(r'^(en|es)($|[_@.])', item.name):
            continue
        if item.is_symlink():
            item.unlink()
        elif item.is_dir():
            removed_bytes += regular_bytes(item)
            shutil.rmtree(item)
        else:
            continue
        removed.append(item.name)
    return {'removed': removed, 'removed_regular_bytes': removed_bytes,
            'preserved_languages': ['English', 'Spanish'],
            'scope': 'usr/share/locale directory entries only'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    print(json.dumps(prune(args.root), indent=2))


if __name__ == '__main__':
    main()
