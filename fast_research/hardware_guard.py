#!/usr/bin/env python3
"""Restrict the pre-PID1 QEMU graphics shortcut; use standard desktop elsewhere."""
from pathlib import Path
import sys

MARKER = '\t# P50_V123_BEFORE_PID1: isolated QEMU-only research, unsafe for physical release.\n'
OLD = '\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then\n'
GUARD = '''\t# P50_FAST_GPU_GUARD: unverified GPUs must retain normal LightDM.
\tp50_fast_gpu=0
\tif grep -qw hypervisor /proc/cpuinfo; then
\t    for p50_pci in /sys/bus/pci/devices/*; do
\t        [ -r "$p50_pci/vendor" ] && [ -r "$p50_pci/device" ] || continue
\t        p50_id="$(cat "$p50_pci/vendor"):$(cat "$p50_pci/device")"
\t        if [ "$p50_id" = '0x1234:0x1111' ]; then p50_fast_gpu=1; break; fi
\t    done
\tfi
\tif [ "$p50_fast_gpu" != 1 ]; then
\t    printf 'P50_FAST_GPU_GUARD_STANDARD_DESKTOP\\n' >/dev/ttyS0
\tfi
'''


def patch_file(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file():raise ValueError('Expected extracted boot script')
    s=p.read_text()
    if s.count(MARKER)!=1 or 'P50_FAST_GPU_GUARD' in s:
        raise ValueError('Unexpected source or already patched')
    prefix,tail=s.split(MARKER,1)
    if not tail.startswith(OLD):raise ValueError('Unexpected early display condition')
    guarded=OLD.replace(' ]; then',' ] && [ "$p50_fast_gpu" = 1 ]; then')
    p.write_text(prefix+GUARD+MARKER+guarded+tail[len(OLD):])


if __name__=='__main__':
    root=Path(sys.argv[1]).resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Refuse host filesystem')
    patch_file(root/'usr/lib/live/boot/9990-main.sh')
