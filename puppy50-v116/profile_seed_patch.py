#!/usr/bin/env python3
"""Test-only: seed a clean Firefox ESR profile before creating the live user.

No browsing data, remote certificates, sandbox bypasses, or policy changes.
Preseeded profile must be verified by real VM browser and connectivity tests.
"""
import argparse
from pathlib import Path
MARKER="\n\tFstab\n\tNetbase\n"
HOOK=r'''
	# P50_V116_PROFILE_SEED: avoid per-boot default-profile creation when possible.
	if [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
		p50_skel="${rootmnt}/etc/skel"
		p50_conf="${p50_skel}/.config/mozilla/firefox"
		[ -d "${p50_skel}" ] && [ ! -L "${p50_skel}" ] || panic "p50: unexpected skeleton"
		[ ! -e "${p50_conf}" ] && [ ! -L "${p50_conf}" ] || panic "p50: profile already exists"
		mkdir -p "${p50_conf}/Profiles/p50.default-esr" || panic "p50: unable to preseed profile"
		cat >"${p50_conf}/profiles.ini" <<'P50_PROFILE_INI'
[General]
StartWithLastProfile=1
Version=2

[Profile0]
Name=default-esr
IsRelative=1
Path=Profiles/p50.default-esr
Default=1
P50_PROFILE_INI
		: > "${p50_conf}/Profiles/p50.default-esr/prefs.js" || panic "p50: unable to seed clean prefs"
		chmod -R go-w "${p50_conf}" || panic "p50: invalid profile permissions"
		unset p50_skel p50_conf
	fi
'''
def patch_main(s):
    if s.count(MARKER)!=1 or 'P50_V116_PROFILE_SEED' in s:
        raise ValueError('Unexpected initrd script')
    return s.replace(MARKER,HOOK+MARKER,1)
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify running root')
    f=root/'usr/lib/live/boot/9990-main.sh'
    if f.is_symlink() or not f.is_file(): raise ValueError('Missing regular main hook')
    f.write_text(patch_main(f.read_text()))
if __name__=='__main__':main()
