#!/usr/bin/env python3
"""Use a narrower device readiness check for the QEMU AHCI boot path."""

import argparse
from pathlib import Path

from repack import replace_once


GUARD = r'''# Only the compact BIOS path with the expected QEMU display and AHCI controller.
p50_ahci=0
p50_display=0
if grep -qw p50-vm-entry /proc/cmdline && grep -qw hypervisor /proc/cpuinfo; then
    for device in /sys/bus/pci/devices/*; do
        [ -r "$device/vendor" ] && [ -r "$device/device" ] || continue
        read -r vendor <"$device/vendor"
        read -r product <"$device/device"
        case "$vendor:$product" in
            0x8086:0x2922) p50_ahci=1 ;;
            0x1234:0x1111) p50_display=1 ;;
        esac
    done
fi
P50_OPTICAL_PATH=0
if [ "$p50_ahci" = 1 ] && [ "$p50_display" = 1 ]; then P50_OPTICAL_PATH=1; fi
export P50_OPTICAL_PATH
'''
WAIT = r'''if [ "${P50_OPTICAL_PATH:-0}" = 1 ]; then
    p50_attempt=0
    while [ ! -b /dev/sr0 ] && [ "$p50_attempt" -lt 40 ]; do
        sleep .02
        p50_attempt=$((p50_attempt + 1))
    done
    if [ -b /dev/sr0 ]; then
        printf 'P50_FIVE_OPTICAL_DEVICE_READY %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
    else
        udevadm settle || true
    fi
else
    udevadm settle || true
fi'''


def patch(root):
    init = root / 'init'
    step = '\nrun_scripts /scripts/init-top\n'
    init.write_text(replace_once(init.read_text(), step, '\n' + GUARD + step))
    udev = root / 'scripts/init-top/udev'
    udev.write_text(replace_once(udev.read_text(), 'udevadm settle || true\n', WAIT + '\n'))
    script = root / 'usr/lib/live/boot/9990-misc-helpers.sh'
    mark = '\t# or do the scan of block devices\n'
    fast_search = r'''    # check_dev still applies the original Live image identity check.
    if [ "${P50_OPTICAL_PATH:-0}" = 1 ] && [ -z "${LIVE_MEDIA:-}" ] && [ -b /dev/sr0 ]; then
        if check_dev "null" /dev/sr0; then return 0; fi
    fi

'''
    script.write_text(replace_once(script.read_text(), mark, fast_search + mark))


def reduce_display_waits(root):
    script = root / 'usr/lib/live/boot/9990-main.sh'
    text = script.read_text()
    old = '        udevadm settle >/dev/null 2>&1 || panic "v125: cannot settle DRM"'
    new = '''        if [ "${P50_OPTICAL_PATH:-0}" != 1 ]; then
            udevadm settle >/dev/null 2>&1 || panic "v125: cannot settle DRM"
        fi'''
    text = replace_once(text, old, new)
    text = replace_once(text, 'while [ "$p50_i" -lt 35 ]; do', 'while [ "$p50_i" -lt 175 ]; do')
    text = replace_once(text, '\tsleep 0.10\n', '\tsleep 0.02\n')
    script.write_text(text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('--reduce-display-waits', action='store_true')
    args = parser.parse_args()
    patch(args.root)
    if args.reduce_display_waits:
        reduce_display_waits(args.root)
