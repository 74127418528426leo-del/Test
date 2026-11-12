#!/usr/bin/env python3
"""Test-only: omit obsolete telemetry services from the staged fast-boot path.

Does not disable NetworkManager, the live-system RAM verifier, or p50-status.
The complete full-RAM recovery image remains untouched.
"""
import argparse
from pathlib import Path

MARKER="\n\tFstab\n\tNetbase\n"
HOOK=r'''
	# P50_V116_DROP_BOOT_TELEMETRY: no nonessential memory/process sampling
	# during nonroot Firefox's first frame. Keep all real networking services.
	if [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
		for p50_diag in puppy50-memory-diagnostics puppy50-gui-diagnostics; do
			p50_link="${rootmnt}/etc/systemd/system/multi-user.target.wants/${p50_diag}.service"
			if [ -L "${p50_link}" ]; then
				[ "$(readlink "${p50_link}")" = "../${p50_diag}.service" ] || panic "p50: unexpected telemetry unit link"
				rm "${p50_link}" || panic "p50: cannot disable test telemetry"
			fi
		done
		unset p50_diag p50_link
	fi
'''
def patch_main(s):
    if s.count(MARKER)!=1 or 'P50_V116_DROP_BOOT_TELEMETRY' in s:
        raise ValueError('Unsupported initrd main hook')
    return s.replace(MARKER,HOOK+MARKER,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);args=p.parse_args()
    root=args.root.resolve(strict=True)
    if root==Path('/'):raise ValueError("Refusing to modify running system")
    file=root/'usr/lib/live/boot/9990-main.sh'
    if file.is_symlink() or not file.is_file():raise ValueError('Expected extracted main file')
    file.write_text(patch_main(file.read_text()))

if __name__=='__main__': main()
