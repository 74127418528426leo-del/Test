#!/usr/bin/env python3
"""Adjust extracted v104/v105 boot-menu configs, keeping recovery choices."""
import argparse
from pathlib import Path


def patch_syslinux(text):
    if text.count('timeout 0\n') != 1 or 'default vesamenu.c32\n' not in text:
        raise ValueError('Unexpected original Syslinux menu')
    # Syslinux uses tenths of a second. Existing live.cfg marks the live menu
    # entry as default; selecting other entries before timeout remains possible.
    return text.replace('timeout 0\n', 'timeout 20\n', 1)


def patch_grub(text):
    if text.count('set default=0\n') != 1 or 'set timeout=' in text:
        raise ValueError('Unexpected original GRUB menu')
    return text.replace('set default=0\n',
                        'set default=0\nset timeout_style=menu\nset timeout=2\n', 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('syslinux', type=Path)
    parser.add_argument('grub', type=Path)
    args = parser.parse_args()
    # Validate both files before changing either.
    syslinux_new = patch_syslinux(args.syslinux.read_text())
    grub_new = patch_grub(args.grub.read_text())
    args.syslinux.write_text(syslinux_new)
    args.grub.write_text(grub_new)
