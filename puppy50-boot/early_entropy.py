"""Enable real paravirtual entropy during the compact BIOS entry when present."""
import argparse
from pathlib import Path

from early_graphics import add_early_module
from repack import replace_once


def enable_entropy(root, modules):
    add_early_module(root, modules, 'virtio_rng')
    init = root / 'init'
    code = init.read_text()
    code = replace_once(code, 'p50_display=0\n', 'p50_display=0\np50_rng_pci=0\n')
    code = replace_once(code, '0x1234:0x1111) p50_display=1 ;;',
                        '0x1234:0x1111) p50_display=1 ;;\n'
                        '            0x1af4:0x1005|0x1af4:0x1044) p50_rng_pci=1 ;;')
    # Full kernel CSPRNG initialization and the ordinary fallback are preserved.
    probe = r'''
if [ "$P50_OPTICAL_PATH" = 1 ] && [ "$p50_rng_pci" = 1 ]; then
    (
        if modprobe -q -b virtio_pci && modprobe -q -b virtio_rng; then
            n=0
            while [ "$n" -lt 25 ]; do
                for endpoint in /sys/bus/virtio/drivers/virtio_rng/virtio*; do
                    [ -L "$endpoint" ] || continue
                    read -r stamp idle <&3 || stamp=unknown
                    printf 'P50_ENTROPY_DEVICE_BOUND %s\n' "$stamp" >&4
                    exit 0
                done
                n=$((n+1))
                sleep .02
            done
        fi
        printf 'P50_ENTROPY_DEVICE_UNAVAILABLE\n' >&4
    ) 3</proc/uptime 4>/dev/ttyS0 </dev/null >/dev/null 2>&1 &
fi
'''
    anchor = 'export P50_OPTICAL_PATH\n'
    init.write_text(replace_once(code, anchor, anchor + probe))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('modules', type=Path)
    args = parser.parse_args()
    enable_entropy(args.root, args.modules)
