#!/usr/bin/env python3
"""Generate visible Debian Live boot menus for the public test preview."""
from pathlib import Path
import argparse


BIOS = '''label live-ram
    menu label Start Puppy50 (copy to RAM)
    menu default
    linux /live/vmlinuz
    initrd /live/initrd.img
    append boot=live components toram quiet locales=en_US.UTF-8

label live-safe-graphics
    menu label Start with basic graphics (copy to RAM)
    linux /live/vmlinuz
    initrd /live/initrd.img
    append boot=live components toram nomodeset quiet locales=en_US.UTF-8

label legacy-recovery
    menu label Legacy recovery - OFFLINE ONLY (older kernel)
    linux /live/vmlinuz-6.12.115+deb13.1-amd64
    initrd /live/initrd-full.img
    append boot=live components toram quiet locales=en_US.UTF-8
'''

GRUB = '''source /boot/grub/config.cfg

menuentry "Start Puppy50 (copy to RAM)" {
    linux /live/vmlinuz boot=live components toram quiet locales=en_US.UTF-8 findiso=${iso_path}
    initrd /live/initrd.img
}
menuentry "Start with basic graphics (copy to RAM)" {
    linux /live/vmlinuz boot=live components toram nomodeset quiet locales=en_US.UTF-8 findiso=${iso_path}
    initrd /live/initrd.img
}
menuentry "Legacy recovery - OFFLINE ONLY (older kernel)" {
    linux /live/vmlinuz-6.12.115+deb13.1-amd64 boot=live components toram quiet locales=en_US.UTF-8 findiso=${iso_path}
    initrd /live/initrd-full.img
}
if [ "${grub_platform}" = "efi" ]; then
    menuentry "UEFI firmware settings" { fwsetup }
fi
'''


def generate(original_bios, original_grub, output):
    if original_bios.count('timeout 10\n') != 1:
        raise ValueError('Unexpected BIOS timeout layout')
    if original_grub.count('set timeout=1\n') != 1:
        raise ValueError('Unexpected GRUB timeout layout')
    output.mkdir(parents=True, exist_ok=True)
    files = {
        'isolinux.cfg': original_bios.replace('timeout 10\n', 'timeout 50\n', 1),
        'live.cfg': BIOS,
        'config.cfg': original_grub.replace('set timeout=1\n', 'set timeout=5\n', 1),
        'grub.cfg': GRUB,
    }
    for name, contents in files.items():
        (output / name).write_text(contents)
    return files


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('bios', type=Path)
    p.add_argument('grub', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    generate(a.bios.read_text(), a.grub.read_text(), a.output)
