#!/usr/bin/env python3
"""Build helpers for a test-only Intel-oriented early-boot experiment."""

import argparse
import hashlib
import json
from pathlib import Path

TARGETS = {
    'usr/lib/firmware/nvidia/ga102/gsp/gsp-535.113.01.bin': 38061600,
    'usr/lib/firmware/nvidia/tu102/gsp/gsp-535.113.01.bin': 23750944,
}


def _entry(text, marker, end_marker):
    if text.count(marker) != 1:
        raise ValueError('Missing or ambiguous menu entry: ' + marker)
    start = text.index(marker)
    end = text.find(end_marker, start + len(marker))
    return start, len(text) if end == -1 else end + 1


def _replace_entry(text, marker, end_marker, old, new):
    start, end = _entry(text, marker, end_marker)
    entry = text[start:end]
    if entry.count(old) != 1:
        raise ValueError('Unexpected initrd in menu entry: ' + marker)
    return text[:start] + entry.replace(old, new, 1) + text[end:]


def patch_menus(bios, grub):
    bios_old = '\tinitrd /live/initrd.img\n'
    bios_new = '\tinitrd /live/initrd-full.img\n'
    grub_old = '\tinitrd\t/live/initrd.img-6.12.115+deb13.1-amd64\n'
    grub_new = '\tinitrd\t/live/initrd-full.img\n'
    start, end = _entry(bios, 'label live-amd64\n', '\nlabel ')
    if bios[start:end].count(bios_old) != 1:
        raise ValueError('Unexpected BIOS fast-start initrd')
    start, end = _entry(grub, 'menuentry "Fast start (wait for RAM READY)"', '\n}')
    if grub[start:end].count(grub_old) != 1:
        raise ValueError('Unexpected UEFI fast-start initrd')
    for marker in ('label live-amd64-fullram\n', 'label live-amd64-failsafe\n'):
        bios = _replace_entry(bios, marker, '\nlabel ', bios_old, bios_new)
    for marker in ('menuentry "Full RAM first (fallback)"', 'menuentry "Recovery (full RAM, safe mode)"'):
        grub = _replace_entry(grub, marker, '\n}', grub_old, grub_new)
    return bios, grub


def remove_early_firmware(root, entries):
    root = Path(root).resolve(strict=True)
    if root == Path('/') or not root.is_dir():
        raise ValueError('Expected a temporary extracted initramfs directory')
    validated = []
    for name, size in entries.items():
        rel = Path(name)
        if rel.is_absolute() or not rel.parts or any(x in ('.', '..') for x in rel.parts):
            raise ValueError('Invalid firmware path: ' + name)
        p = root
        for part in rel.parts:
            p = p / part
            if p.is_symlink():
                raise ValueError('Symlink in firmware path: ' + name)
        if not p.is_file() or p.stat().st_size != size:
            raise ValueError('Missing or unexpected firmware file: ' + name)
        p.resolve(strict=True).relative_to(root)
        h = hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda: f.read(1048576), b''):
                h.update(chunk)
        validated.append((p, {'path': name, 'size': size, 'sha256': h.hexdigest()}))
    for path, _ in validated:
        path.unlink()
    return [entry for _, entry in validated]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('root', type=Path)
    p.add_argument('bios', type=Path)
    p.add_argument('grub', type=Path)
    p.add_argument('report', type=Path)
    args = p.parse_args()
    for menu in (args.bios, args.grub):
        if menu.is_symlink() or not menu.is_file():
            raise ValueError('Menu must be a regular file')
    bios, grub = patch_menus(args.bios.read_text(), args.grub.read_text())
    removed = remove_early_firmware(args.root, TARGETS)
    args.bios.write_text(bios)
    args.grub.write_text(grub)
    args.report.write_text(json.dumps({'removed_from_fast_initramfs_only': removed}, indent=2) + '\n')


if __name__ == '__main__':
    main()
