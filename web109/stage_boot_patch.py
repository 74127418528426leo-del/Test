#!/usr/bin/env python3
"""Prepare an isolated research initramfs for an optional staged-RAM boot."""
from pathlib import Path
import argparse

ORIGINAL='echo $(setup_loop "${1}" \'0\' "${2}")'
HOOK='''p50_backing_device ()
{
    if [ -n "${TORAM:-}" ]; then
        setup_loop "${1}" '0' "${2}"
        return
    fi
    case "${1}" in
        /run/live/medium/live/filesystem.squashfs)
            p50_loop="$(setup_loop "${1}" '0' '1')" || panic "p50: cannot attach original root"
            modprobe -q -b dm_mod >/dev/null 2>&1 || panic "p50: device mapper unavailable"
            p50_sectors="$(blockdev --getsz "${p50_loop}")" || panic "p50: cannot size root image"
            /usr/lib/p50-stage/dm-init create p50-staged-root --readonly --table "0 ${p50_sectors} linear ${p50_loop} 0" >/dev/null 2>/dev/console || panic "p50: cannot create root mapping"
            udevadm settle
            p50_mm="$(/usr/lib/p50-stage/dm-init info -c --noheadings --separator : -o major,minor p50-staged-root | tr -d '[:space:]')" || panic "p50: cannot inspect root mapping"
            case "${p50_mm}" in *:*) ;; *) panic "p50: invalid mapping device number" ;; esac
            p50_major="${p50_mm%:*}"; p50_minor="${p50_mm#*:}"
            case "${p50_major}${p50_minor}" in ''|*[!0-9]*) panic "p50: invalid mapping device number" ;; esac
            if [ ! -b /dev/mapper/p50-staged-root ]; then
                mknod /dev/mapper/p50-staged-root b "${p50_major}" "${p50_minor}" || panic "p50: cannot create mapping node"
            fi
            p50_actual="$(stat -c '%t:%T' /dev/mapper/p50-staged-root)"
            p50_expected="$(printf '%x:%x' "${p50_major}" "${p50_minor}")"
            [ "${p50_actual}" = "${p50_expected}" ] || panic "p50: root mapping device number mismatch"
            echo /dev/mapper/p50-staged-root
            ;;
        *) setup_loop "${1}" '0' "${2}" ;;
    esac
}

'''
INSTALL='''
	# Experimental staged boot: these tools and the service live in RAM.
	if [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
		mkdir -p /run/p50-stage/tools "${rootmnt}/etc/systemd/system/graphical.target.wants" || panic "p50: cannot prepare migration tools"
		cp -a /usr/lib/p50-stage/. /run/p50-stage/tools/ || panic "p50: cannot stage migration tools"
		cp /usr/lib/p50-stage/p50-staged-migration.service "${rootmnt}/etc/systemd/system/" || panic "p50: cannot install migration service"
		ln -s ../p50-staged-migration.service "${rootmnt}/etc/systemd/system/graphical.target.wants/p50-staged-migration.service" || panic "p50: cannot enable migration service"
	fi
'''

def patch_helpers(text):
    if text.count(ORIGINAL)!=1 or text.count('get_backing_device ()')!=1 or 'p50_backing_device ()' in text:
        raise ValueError('Unexpected or already patched live helper')
    return text.replace('get_backing_device ()',HOOK+'get_backing_device ()',1).replace(ORIGINAL,'p50_backing_device "${1}" "${2}"',1)

def patch_main(text):
    marker='\n\tFstab\n\tNetbase\n'
    if text.count(marker)!=1 or text.count('\n\tFstab\n')!=1 or 'p50-staged-migration.service' in text:
        raise ValueError('Unexpected or already patched main boot script')
    return text.replace(marker,INSTALL+marker,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('initrd_root',type=Path);args=p.parse_args()
    base=args.initrd_root/'usr/lib/live/boot'; helper=base/'9990-misc-helpers.sh'; mainfile=base/'9990-main.sh'
    if helper.is_symlink() or mainfile.is_symlink() or not helper.is_file() or not mainfile.is_file():
        raise ValueError('Boot files must be regular files')
    old_h=helper.read_text();old_m=mainfile.read_text()
    new_h=patch_helpers(old_h);new_m=patch_main(old_m)
    helper.write_text(new_h);mainfile.write_text(new_m)

if __name__=='__main__':main()
