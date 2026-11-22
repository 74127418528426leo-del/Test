#!/usr/bin/env python3
"""Keep the boot drivers needed by the QEMU VM initramfs entry."""

import argparse
from pathlib import Path
import shutil
import subprocess


REQUIRED = (
    'ahci', 'ata_piix', 'sr_mod', 'sd_mod', 'isofs', 'loop', 'squashfs', 'overlay',
    'dm_mod', 'e1000', 'virtio_blk', 'virtio_scsi', 'virtio_pci', 'xhci_pci',
    'ehci_pci', 'uhci_hcd', 'usb_storage', 'usbhid',
)
OPTIONAL = (
    'ohci_pci', 'uas', 'nvme', 'e1000e', 'virtio_net', 'virtio_console',
    'virtio_rng', 'drm', 'drm_kms_helper', 'psmouse', 'i8042', 'atarikbd',
    'fat', 'vfat', 'nls_cp437', 'nls_ascii', 'nls_utf8',
)


def trim(root):
    root = root.resolve(strict=True)
    if root == Path('/'):
        raise ValueError('Refusing to modify the host module tree')
    trees = list((root / 'usr/lib/modules').glob('*/kernel'))
    if len(trees) != 1:
        raise ValueError('Unexpected kernel module directory structure')
    modules = trees[0]
    version = modules.parent.name
    keep = set()
    for name in REQUIRED + OPTIONAL:
        res = subprocess.run(
            ['modprobe', '-d', str(root), '-S', version, '--ignore-install', '--show-depends', name],
            text=True, capture_output=True,
        )
        if res.returncode != 0:
            if name in REQUIRED:
                raise ValueError(f'Required module {name} unavailable: {res.stderr.strip()}')
            continue
        for line in res.stdout.splitlines():
            if line.startswith('insmod '):
                path = Path(line.split()[1]).resolve(strict=True)
                if not path.is_relative_to(modules):
                    raise ValueError(f'Module escapes extracted kernel tree: {path}')
                keep.add(path)
    for path in modules.rglob('*.ko*'):
        if path not in keep:
            path.unlink()
    subprocess.run(['depmod', '-b', str(root), '-a', version], check=True)
    print(f'VM initramfs keeps {len(keep)} kernel modules including dependencies')
    firmware = root / 'usr/lib/firmware'
    if firmware.is_symlink() or not firmware.is_dir():
        raise ValueError('Expected a disposable initramfs firmware directory')
    shutil.rmtree(firmware)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    trim(parser.parse_args().root)
