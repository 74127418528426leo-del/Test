#!/usr/bin/env python3
"""Test-only v116: give a cold Firefox first access to the CPU before desktop helpers.

This patches only an *extracted* staging initramfs. Never edit the running root.
No changes to browser sandbox, NetworkManager service, or RAM verification.
"""
from pathlib import Path
import argparse

MARKER = "\n\tFstab\n\tNetbase\n"
HOOK = r'''
	# P50_V116_FIREFOX_PRIORITY: schedule browser before user-interface utilities.
	if [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
		p50_autostart="${rootmnt}/etc/skel/.config/openbox/autostart"
		p50_ff_line='firefox-esr file:///usr/share/puppy50web/index.html >/tmp/puppy50-firefox.log 2>&1 &'
		[ -f "${p50_autostart}" ] && [ ! -L "${p50_autostart}" ] || panic "p50: missing autostart"
		[ "$(grep -Fxc "${p50_ff_line}" "${p50_autostart}")" = 1 ] || panic "p50: unexpected Firefox launch"
		[ "$(grep -c '^tint2 ' "${p50_autostart}")" = 1 ] || panic "p50: missing panel"
		[ "$(grep -c '^nm-applet ' "${p50_autostart}")" = 1 ] || panic "p50: missing network applet"
		p50_new="${p50_autostart}.p50-v116"
		[ ! -e "${p50_new}" ] && [ ! -L "${p50_new}" ] || panic "p50: unexpected autostart temporary"
		{
			printf '#!/bin/sh\n'
			printf '%s\n' "${p50_ff_line}"
			printf 'sleep 6\n'
			sed '1d;/^firefox-esr file:/d' "${p50_autostart}"
		} > "${p50_new}" || panic "p50: cannot prepare browser-first autostart"
		chmod 0755 "${p50_new}" || panic "p50: cannot set autostart permissions"
		mv "${p50_new}" "${p50_autostart}" || panic "p50: cannot replace autostart"
		unset p50_ff_line p50_new p50_autostart
	fi
'''

def patch_main(s: str) -> str:
    if s.count(MARKER) != 1 or "P50_V116_FIREFOX_PRIORITY" in s:
        raise ValueError("Unsupported or already modified initrd live-boot hook")
    return s.replace(MARKER, HOOK + MARKER, 1)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("root",type=Path)
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    if root==Path("/"):
        raise ValueError("Refusing to modify the running root")
    path=root/"usr/lib/live/boot/9990-main.sh"
    if path.is_symlink() or not path.is_file():
        raise ValueError("Missing or symlinked live-boot main hook")
    path.write_text(patch_main(path.read_text()))

if __name__=="__main__":
    main()
