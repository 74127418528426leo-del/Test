#!/usr/bin/env python3
"""Remove three explicitly scoped non-Intel graphics firmware collections."""

import argparse
import json
import os
import shutil
from pathlib import Path

GRAPHICS_FIRMWARE = ('amdgpu', 'radeon', 'nvidia')


def trim_gpu_firmware(root: Path) -> dict:
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Root must be an existing non-symlink directory')
    current = root
    for name in ('usr', 'lib', 'firmware'):
        current = current / name
        if current.is_symlink() or not current.is_dir():
            raise ValueError(f'Firmware ancestor must be a directory: {current}')
    firmware = current
    paths = {name: firmware / name for name in GRAPHICS_FIRMWARE}
    for path in paths.values():
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError(f'Graphics firmware target is not a real directory: {path}')
    report = {}
    for name, path in paths.items():
        files, size = 0, 0
        if path.exists():
            for parent, _, filenames in os.walk(path, followlinks=False):
                for filename in filenames:
                    item = Path(parent) / filename
                    if not item.is_symlink() and item.is_file():
                        files += 1
                        size += item.stat().st_size
            shutil.rmtree(path)
        report[name] = {'files': files, 'bytes': size}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = trim_gpu_firmware(args.root)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
