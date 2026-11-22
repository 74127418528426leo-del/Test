#!/usr/bin/env python3
"""Build the fast BIOS VM trial from the verified public ISO."""

import argparse
import hashlib
from pathlib import Path
import re
import subprocess


EARLY_PREFIX_BYTES = 45_302_784
BASELINE_SHA = 'b035187b2c6ad8e1686b10889d7d67144d16be22b5ed734cc9da613b5a14db32'
NEWC_HEADER = 110


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f'Unexpected match count for {old[:120]!r}')
    return text.replace(old, new, 1)


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def cpio_archives(data):
    """Split the concatenated newc archives and inventory each payload."""
    offset = 0
    archive_start = None
    files = {}
    while offset < len(data):
        if data[offset] == 0:
            offset += 1
            continue
        header = data[offset:offset + NEWC_HEADER]
        if len(header) != NEWC_HEADER or header[:6] != b'070701':
            raise ValueError(f'Unexpected CPIO header at offset {offset}')
        if archive_start is None:
            archive_start = offset
        size = int(header[54:62], 16)
        name_size = int(header[94:102], 16)
        start = offset + NEWC_HEADER
        name = data[start:start + name_size]
        if not name.endswith(b'\0'):
            raise ValueError('Invalid CPIO filename')
        data_start = (start + name_size + 3) & ~3
        offset = (data_start + size + 3) & ~3
        if offset > len(data):
            raise ValueError('Invalid CPIO file size')
        if name == b'TRAILER!!!\0':
            yield data[archive_start:offset], files
            files = {}
            archive_start = None
        elif size:
            files[name[:-1].decode().removeprefix('./')] = size
    if archive_start is not None:
        raise ValueError('Unterminated CPIO archive')


def split_initrd(image, work):
    data = image.read_bytes()
    early = data[:EARLY_PREFIX_BYTES]
    main = data[EARLY_PREFIX_BYTES:]
    if main[:4] != b'\x28\xb5\x2f\xfd':
        raise ValueError('Unexpected main archive codec')
    expected = {'kernel/x86/microcode/AuthenticAMD.bin', 'kernel/x86/microcode/GenuineIntel.bin'}
    microcode = {}
    for index, (archive, files) in enumerate(cpio_archives(early)):
        if files and set(files) <= expected:
            microcode.update(files)
        else:
            if set(files) & expected:
                raise ValueError('Refusing to omit an archive mixing microcode and other files')
            (work / f'extra-{index}.cpio').write_bytes(archive)
            print(f'Keep early CPIO {index} ({len(files)} payloads, {len(archive)} bytes)')
    if set(microcode) != expected:
        raise ValueError(f'Unexpected microcode payloads: {microcode}')
    print('Microcode retained in the generic boot entry:', microcode)
    (work / 'main.zst').write_bytes(main)
    (work / 'early.cpio').write_bytes(early)


MARK = r'''p50_mark() {
    read -r stamp idle </proc/uptime
    printf 'P50_FIVE_%s %s\n' "$1" "$stamp" >/dev/ttyS0
}
p50_mark LAUNCHER
'''
OLD_PREFETCH = r'''            nice -n 10 dd if="$p50_lib" of=/dev/null bs=1048576 count=256 2>/dev/null
            printf 'P50_V131_READAHEAD_COMPLETE %s\n' "$(cat /proc/uptime)" >/dev/ttyS0'''


def modify_boot_script(initrd, prefetch_mib):
    script = initrd / 'usr/lib/live/boot/9990-main.sh'
    text = script.read_text()
    start = 'set -eu\numask 077\np50_cookie="$(mcookie)"'
    text = replace_once(text, start, 'set -eu\numask 077\n' + MARK + 'p50_cookie="$(mcookie)"\np50_mark COOKIE')
    for command, marker in [
        ('mkdir -p /home/user /tmp/.X11-unix /run/user/1000', 'RUNTIME_DIRS'),
        ('chmod 0700 /run/user/1000', 'RUNTIME_PERMISSIONS'),
        ('xauth -f /home/user/.Xauthority add :0 . "$p50_cookie"', 'XAUTH'),
        ('chmod 0600 /home/user/.Xauthority', 'XAUTH_PERMISSIONS'),
    ]:
        text = replace_once(text, command + '\n', command + f'\np50_mark {marker}\n')
    if prefetch_mib:
        prefetch = OLD_PREFETCH.splitlines()[0].replace(
            'nice -n 10 dd if="$p50_lib"',
            'chroot "$p50_root" /usr/bin/nice -n 5 /usr/bin/dd if=/usr/lib/firefox-esr/libxul.so',
        ).replace('count=256', f'count={prefetch_mib}')
    else:
        prefetch = OLD_PREFETCH.splitlines()[0]
    replacement = f'''            if {prefetch.strip()}; then
                printf 'P50_FIVE_PREFETCH_OK %s\\n' "$(cat /proc/uptime)" >/dev/ttyS0
            else
                printf 'P50_FIVE_PREFETCH_FAILED %s\\n' "$(cat /proc/uptime)" >/dev/ttyS0
            fi'''
    text = replace_once(text, OLD_PREFETCH, replacement)
    script.write_text(text)


def menu_text(base):
    standard = 'label live-ram\n    menu label Experimental staged startup (keep USB connected)\n    menu default\n'
    fast = '''label live-auto
    menu label Start Puppy50 (keep boot media connected)
    menu default
    com32 ifcpu.c32
    append hypervisor -- live-vm -- live-ram

label live-vm
    menu hide
    linux /live/vmlinuz
    initrd /live/initrd-vm.img
    append boot=live components quiet locales=en_US.UTF-8 p50-vm-entry

label live-ram
    menu label Standard startup with CPU microcode
'''
    return replace_once(base, standard, fast)


def repack(base, work, trial, image, selector, direct=False):
    menu = work / 'candidate-live.cfg'
    menu.write_text(menu_text((work / 'live.cfg').read_text()))
    mapped = {
        './isolinux/live.cfg': menu,
        './isolinux/ifcpu.c32': selector,
        './live/initrd-vm.img': image,
    }
    if direct:
        config = work / 'candidate-isolinux.cfg'
        config.write_text('''default live-auto
prompt 0
timeout 0
include live.cfg

label recovery-menu
    com32 vesamenu.c32
    append menu.cfg
''')
        mapped['./isolinux/isolinux.cfg'] = config
    lines = []
    for line in (work / 'original.sha256sum.txt').read_text().splitlines():
        match = re.fullmatch(r'([a-f0-9]{64})( [ *])(.*)', line)
        if not match:
            raise ValueError(f'Invalid manifest entry: {line!r}')
        checksum, separator, path = match.groups()
        if path in mapped:
            checksum = digest(mapped[path])
        lines.append(checksum + separator + path)
    for name in ('./isolinux/ifcpu.c32', './live/initrd-vm.img'):
        if any(line[66:] == name for line in lines):
            raise ValueError(f'Unexpected existing file {name}')
        lines.append(f'{digest(mapped[name])}  {name}')
    manifest = work / 'candidate.sha256sum.txt'
    manifest.write_text('\n'.join(lines) + '\n')
    mapped['./sha256sum.txt'] = manifest
    iso = work / f'{trial}.iso'
    command = ['xorriso', '-indev', str(base), '-outdev', str(iso)]
    for name, path in mapped.items():
        command.extend(['-map', str(path), name[1:]])
    command.extend(['-boot_image', 'any', 'replay', '-commit', '-end'])
    subprocess.run(command, check=True)
    print(f'{digest(iso)}  {iso}')


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_subparsers(dest='action', required=True)
    split = modes.add_parser('split')
    split.add_argument('image', type=Path)
    split.add_argument('work', type=Path)
    patch = modes.add_parser('patch')
    patch.add_argument('initrd', type=Path)
    patch.add_argument('--prefetch-mib', type=int, choices=(0, 64, 128, 256), default=0)
    build = modes.add_parser('repack')
    build.add_argument('base', type=Path)
    build.add_argument('work', type=Path)
    build.add_argument('trial')
    build.add_argument('image', type=Path)
    build.add_argument('selector', type=Path)
    build.add_argument('--direct', action='store_true')
    args = parser.parse_args()
    if args.action == 'split':
        split_initrd(args.image, args.work)
    elif args.action == 'patch':
        modify_boot_script(args.initrd, args.prefetch_mib)
    else:
        if digest(args.base) != BASELINE_SHA:
            raise ValueError('Input ISO is not the published baseline')
        repack(args.base, args.work, args.trial, args.image, args.selector, args.direct)


if __name__ == '__main__':
    main()
