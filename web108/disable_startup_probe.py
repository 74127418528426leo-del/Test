#!/usr/bin/env python3
"""Disable the development-only network probe in an extracted live image."""

import argparse
import os
from pathlib import Path


def disable_startup_probe(root: Path) -> None:
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Image root must be an existing real directory')
    unit_dir = root
    for part in ('etc', 'systemd', 'system'):
        unit_dir = unit_dir / part
        if unit_dir.is_symlink() or not unit_dir.is_dir():
            raise ValueError(f'Unexpected unit ancestor: {unit_dir}')
    wants = unit_dir / 'multi-user.target.wants'
    if wants.is_symlink() or not wants.is_dir():
        raise ValueError('Unexpected multi-user wants directory')
    name = 'puppy50-network-probe.service'
    unit, enabled = unit_dir / name, wants / name
    if unit.is_symlink() or not unit.is_file():
        raise ValueError('Expected regular probe unit')
    content = unit.read_text()
    if ('Before=display-manager.service' not in content or
            'ExecStart=/usr/local/sbin/puppy50-network-probe' not in content):
        raise ValueError('Probe unit contents do not match expected baseline')
    if not enabled.is_symlink() or str(enabled.readlink()) != '/etc/systemd/system/' + name:
        raise ValueError('Unexpected probe enable link')
    replacement = unit_dir / (name + '.mask-new')
    if replacement.exists() or replacement.is_symlink():
        raise ValueError('Mask staging path already exists')
    replacement.symlink_to('/dev/null')
    os.replace(replacement, unit)
    enabled.unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    disable_startup_probe(args.root)
    print('Development network probe masked; NetworkManager remains unchanged.')
