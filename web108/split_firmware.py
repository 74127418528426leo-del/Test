#!/usr/bin/env python3
"""Move an intact firmware tree into a separate image-layer staging root."""

import argparse
import os
import shutil
from pathlib import Path


def split_firmware(root: Path, layer: Path) -> None:
    root, layer = Path(root), Path(layer)
    if root.is_symlink() or layer.is_symlink() or not root.is_dir() or not layer.is_dir():
        raise ValueError('Both staging roots must be real directories')
    root_real, layer_real = root.resolve(), layer.resolve()
    if root_real == layer_real or root_real in layer_real.parents or layer_real in root_real.parents:
        raise ValueError('Staging roots must be separate trees')
    current = root
    for part in ('usr', 'lib', 'firmware'):
        current = current / part
        if current.is_symlink() or not current.is_dir():
            raise ValueError(f'Unexpected firmware staging path: {current}')
    if any(layer.iterdir()):
        raise ValueError('Firmware layer staging root must start empty')
    source = current
    root_usr, root_lib = root / 'usr', root / 'usr/lib'
    lib_stat = root_lib.stat()
    layer_usr, layer_lib = layer / 'usr', layer / 'usr/lib'
    layer_usr.mkdir()
    layer_lib.mkdir()
    os.replace(source, layer_lib / 'firmware')
    os.utime(root_lib, ns=(lib_stat.st_atime_ns, lib_stat.st_mtime_ns))
    for original, copied in ((root_lib, layer_lib), (root_usr, layer_usr), (root, layer)):
        stat = original.stat()
        os.chown(copied, stat.st_uid, stat.st_gid)
        shutil.copystat(original, copied, follow_symlinks=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--layer', type=Path, required=True)
    args = parser.parse_args()
    split_firmware(args.root, args.layer)
    print('Complete firmware tree staged in a separate layer.')
