#!/usr/bin/env python3
"""Collect only Firefox's application caches from a fresh offline VM."""

import argparse
from pathlib import Path
import subprocess
import tarfile
import time

from repack import replace_once


CACHES = ('startupCache.8.little', 'scriptCache.bin', 'scriptCache-child.bin')
COMPATIBILITY = 'compatibility.ini'
LOCATION = 'cache-location.txt'
PORT = 'org.puppy50.cache'
UNIT = '''[Unit]
Description=Collect application startup caches from a disposable offline Firefox session
After=systemd-udevd.service

[Service]
Type=oneshot
TimeoutStartSec=110
ExecStart=/run/p50-stage/tools/busybox sh /run/p50-stage/tools/capture-firefox-cache.sh
'''
COLLECT = r'''#!/bin/sh
set -eu
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
log() { printf 'P50_CACHE_%s\n' "$1" >/dev/ttyS0; }
if [ "$(ls -A /sys/class/net)" != lo ]; then log NOT_OFFLINE; exit 1; fi
modprobe virtio_console
port=/dev/virtio-ports/org.puppy50.cache
for attempt in $(seq 1 100); do
    [ -c "$port" ] && break
    sleep .1
done
[ -c "$port" ] || { log PORT_NOT_FOUND; exit 1; }
profile=/home/user/.mozilla/firefox/p50-default
for attempt in $(seq 1 240); do
    pgrep -u 1000 -x firefox-esr >/dev/null && break
    sleep .1
done
pgrep -u 1000 -x firefox-esr >/dev/null || { log FIREFOX_NOT_FOUND; exit 1; }
log FIREFOX_RUNNING
for attempt in $(seq 1 600); do
    pgrep -u 1000 -x firefox-esr >/dev/null || break
    sleep .1
done
if pgrep -u 1000 -x firefox-esr >/dev/null; then log FIREFOX_DID_NOT_QUIT; exit 1; fi
log FIREFOX_QUIT
stage=$(mktemp -d /run/p50-cache-export.XXXXXX)
for cache_root in "$profile" /home/user/.cache/mozilla/firefox/p50-default; do
    [ -s "$cache_root/startupCache/startupCache.8.little" ] || continue
    [ ! -e "$stage/cache-location.txt" ] || { log AMBIGUOUS_CACHE; exit 1; }
    if [ "$cache_root" = "$profile" ]; then
        printf 'profile\n' >"$stage/cache-location.txt"
    else
        printf 'xdg\n' >"$stage/cache-location.txt"
    fi
    for name in startupCache.8.little scriptCache.bin scriptCache-child.bin; do
        file="$cache_root/startupCache/$name"
        [ -f "$file" ] && [ ! -L "$file" ] && [ -s "$file" ] || { log "MISSING_$name"; exit 1; }
        [ "$(stat -c %s "$file")" -le 20971520 ] || { log CACHE_TOO_LARGE; exit 1; }
        cp "$file" "$stage/$name"
    done
done
if [ ! -s "$stage/cache-location.txt" ]; then
    find "$profile" /home/user/.cache/mozilla/firefox -maxdepth 4 -type f -name '*Cache*' -printf 'P50_CACHE_FOUND %P\n' >/dev/ttyS0 2>/dev/null || :
    log NO_STARTUP_CACHE
    exit 1
fi
[ -f "$profile/compatibility.ini" ] && [ ! -L "$profile/compatibility.ini" ] || { log NO_COMPATIBILITY; exit 1; }
cp "$profile/compatibility.ini" "$stage/compatibility.ini"
tar -C "$stage" -cf "$port" startupCache.8.little scriptCache.bin scriptCache-child.bin compatibility.ini cache-location.txt
log EXPORTED
'''


def install_capture(root):
    lib = root / 'usr/lib/p50-stage'
    (lib / 'capture-firefox-cache.sh').write_text(COLLECT)
    (lib / 'p50-capture-cache.service').write_text(UNIT)
    script = root / 'usr/lib/live/boot/9990-main.sh'
    text = script.read_text()
    marker = '\t\tp50_autostart="${rootmnt}/etc/skel/.config/openbox/autostart"'
    install = r'''        cp /usr/lib/p50-stage/p50-capture-cache.service "${rootmnt}/etc/systemd/system/" || panic "cache: cannot install collector"
        ln -s ../p50-capture-cache.service "${rootmnt}/etc/systemd/system/graphical.target.wants/p50-capture-cache.service" || panic "cache: cannot activate collector"
'''
    script.write_text(replace_once(text, marker, install + marker))


def generate(iso, out):
    from web103.site_test import send_key
    from web85.qemu_debian_live_smoke import qmp
    from web109.boot_bench_ahci import capture

    out = out.resolve()
    iso = iso.resolve(strict=True)
    out.mkdir(parents=True)
    monitor = out / 'qmp.sock'
    serial = out / 'serial.log'
    tar = out / 'startup-cache.tar'
    argv = [
        'qemu-system-x86_64', '-machine', 'pc,accel=kvm',
        '-cpu', 'Westmere,-aes,-pclmulqdq,-x2apic,-3dnowprefetch',
        '-m', '3072', '-smp', '2', '-nic', 'none', '-display', 'none', '-vga', 'std',
        '-serial', f'file:{serial}', '-qmp', f'unix:{monitor},server=on,wait=off',
        '-boot', 'order=c', '-no-reboot',
        '-smbios', 'type=1,manufacturer=Acer,product=Aspire-X3950-EMULATED',
        '-drive', f'file={iso},if=none,id=livecd,format=raw,readonly=on',
        '-device', 'ich9-ahci,id=ahci', '-device', 'ide-cd,drive=livecd,bus=ahci.0,id=bootusb,bootindex=1',
        '-device', 'virtio-serial-pci', '-chardev', f'file,id=seed,path={tar}',
        '-device', f'virtserialport,chardev=seed,name={PORT}',
    ]
    with (out / 'qemu.log').open('wb') as log:
        vm = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 35
            while time.monotonic() < deadline and vm.poll() is None:
                if monitor.exists() and capture(monitor, out, None):
                    capture(monitor, out, 'fresh-firefox.png')
                    break
                time.sleep(.2)
            else:
                raise RuntimeError('The cache-generation VM did not display Firefox')
            time.sleep(24)
            qmp(monitor, 'human-monitor-command', {'command-line': 'mouse_button 1'})
            time.sleep(.1)
            qmp(monitor, 'human-monitor-command', {'command-line': 'mouse_button 0'})
            send_key(monitor, ['ctrl', 'q'], 110)
            time.sleep(.8)
            send_key(monitor, ['ret'], 100)
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline and vm.poll() is None:
                marks = serial.read_text(errors='replace')
                if 'P50_CACHE_EXPORTED' in marks.splitlines():
                    break
                time.sleep(.2)
            else:
                capture(monitor, out, 'cache-export-timeout.png')
                raise RuntimeError('Firefox did not export all native application caches')
        finally:
            if vm.poll() is None:
                vm.terminate()
                try:
                    vm.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    vm.kill()
                    vm.wait()
    return tar


def extract_cache(tar_path, dest):
    allowed = set(CACHES) | {COMPATIBILITY, LOCATION}
    dest.mkdir(parents=True)
    with tarfile.open(tar_path, 'r:') as archive:
        members = archive.getmembers()
        if len(members) != len(allowed) or {m.name for m in members} != allowed:
            raise ValueError('Unexpected Firefox cache archive entries')
        for member in members:
            max_size = 20 * 1024 * 1024 if member.name in CACHES else 2048
            if not member.isfile() or not 0 < member.size <= max_size:
                raise ValueError(f'Invalid Firefox cache member {member.name}')
            with archive.extractfile(member) as source:
                (dest / member.name).write_bytes(source.read())
    if not (dest / COMPATIBILITY).read_text().startswith('[Compatibility]\n'):
        raise ValueError('Invalid Firefox compatibility record')
    if (dest / LOCATION).read_text().strip() not in ('profile', 'xdg'):
        raise ValueError('Invalid Firefox cache path selection')
    print({name: (dest / name).stat().st_size for name in sorted(allowed)})


def install_seed(root, seed):
    import shutil

    shutil.copytree(seed, root / 'usr/lib/p50-firefox-seed')
    script = root / 'usr/lib/live/boot/9990-main.sh'
    text = script.read_text()
    marker = 'chown -R 1000:1000 "$p50_root/home/user/.mozilla" || panic "v139: could not grant profile to nonroot user"'
    init = r'''        p50_seed=/usr/lib/p50-firefox-seed
        case "$(cat "$p50_seed/cache-location.txt")" in
            profile) p50_cache="$p50_profile/startupCache" ;;
            xdg) p50_cache="$p50_root/home/user/.cache/mozilla/firefox/p50-default/startupCache" ;;
            *) panic "p50: unexpected application cache location" ;;
        esac
        mkdir -pm 0700 "$p50_cache" || panic "p50: cannot create application cache directory"
        cp "$p50_seed/compatibility.ini" "$p50_profile/compatibility.ini" || panic "p50: cannot copy Firefox compatibility record"
        for p50_item in startupCache.8.little scriptCache.bin scriptCache-child.bin; do
            cp "$p50_seed/$p50_item" "$p50_cache/$p50_item" || panic "p50: cannot seed Firefox application cache"
        done
        chown -R 1000:1000 "$p50_cache" || panic "p50: cannot set Firefox cache owner"
        if [ "$p50_cache" != "$p50_profile/startupCache" ]; then
            chown -R 1000:1000 "$p50_root/home/user/.cache/mozilla" || panic "p50: cannot set parent cache owner"
        fi
        printf 'P50_FIVE_CACHE_SEEDED %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
'''
    script.write_text(replace_once(text, marker, init + marker))


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_subparsers(dest='mode', required=True)
    capture = modes.add_parser('capture')
    capture.add_argument('root', type=Path)
    boot = modes.add_parser('generate')
    boot.add_argument('iso', type=Path)
    boot.add_argument('output', type=Path)
    seed = modes.add_parser('seed')
    seed.add_argument('root', type=Path)
    seed.add_argument('cache', type=Path)
    args = parser.parse_args()
    if args.mode == 'capture':
        install_capture(args.root)
    elif args.mode == 'generate':
        extract_cache(generate(args.iso, args.output), args.output / 'cache-files')
    else:
        install_seed(args.root, args.cache)


if __name__ == '__main__':
    main()
