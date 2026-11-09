#!/usr/bin/env python3
"""Experimental two-layer staged migration; fail closed on partial switches."""
import argparse
from pathlib import Path

def replace_once(text,old,new):
 if text.count(old)!=1:raise ValueError('Unexpected boot script marker: '+old[:80])
 return text.replace(old,new,1)

EXTRA_MAPPING=r'''
    # P50_DUAL_EXTRA_MAPPING: retain the firmware layer from the beginning.
    if [ -z "${TORAM:-}" ] && [ "$1" = /run/live/medium/live/extras.squashfs ]; then
        p50_extra_loop="$(setup_loop "$1" '0' '1')" || panic "p50: cannot attach extra image"
        modprobe -q -b dm_mod >/dev/null 2>&1 || panic "p50: device mapper unavailable"
        p50_extra_sectors="$(blockdev --getsz "${p50_extra_loop}")" || panic "p50: cannot size extra image"
        /usr/lib/p50-stage/dm-init create p50-staged-extra --readonly --table "0 ${p50_extra_sectors} linear ${p50_extra_loop} 0" >/dev/null 2>/dev/console || panic "p50: cannot create extra mapping"
        p50_extra_mm="$(/usr/lib/p50-stage/dm-init info -c --noheadings --separator : -o major,minor p50-staged-extra | tr -d '[:space:]')" || panic "p50: cannot inspect extra mapping"
        case "${p50_extra_mm}" in *:*) ;; *) panic "p50: invalid extra device number" ;; esac
        p50_extra_major="${p50_extra_mm%:*}"; p50_extra_minor="${p50_extra_mm#*:}"
        case "${p50_extra_major}${p50_extra_minor}" in ''|*[!0-9]*) panic "p50: invalid extra device number" ;; esac
        if [ ! -b /dev/mapper/p50-staged-extra ]; then
            mknod /dev/mapper/p50-staged-extra b "${p50_extra_major}" "${p50_extra_minor}" || panic "p50: cannot create extra device"
        fi
        p50_extra_actual="$(stat -c '%t:%T' /dev/mapper/p50-staged-extra)"
        p50_extra_expected="$(printf '%x:%x' "${p50_extra_major}" "${p50_extra_minor}")"
        [ "${p50_extra_actual}" = "${p50_extra_expected}" ] || panic "p50: extra device mismatch"
        echo /dev/mapper/p50-staged-extra
        return
    fi
'''
def patch_helper(text):
 marker='p50_backing_device ()\n{\n'
 if 'P50_DUAL_EXTRA_MAPPING' in text:raise ValueError('Already patched')
 return replace_once(text,marker,marker+EXTRA_MAPPING)

EXTRA_META=r'''
EXTRA_SRC=/run/live/medium/live/extras.squashfs
EXTRA_COPY=$STORE/extras.squashfs
EXTRA_NEW_LOOP=''
EXTRA_TABLE_LOADED=0
'''
EXTRA_PREP=r'''
[ -f "$EXTRA_SRC" ] && [ ! -L "$EXTRA_SRC" ] || fail 'extra source image absent or symlink'
[ ! -e "$EXTRA_COPY" ] || fail 'extra RAM destination already exists'
extra_expected=$("$B" awk '$2=="./live/extras.squashfs" { print $1 }' "$MANIFEST")
[ "${#extra_expected}" -eq 64 ] || fail 'extra checksum missing or ambiguous'
case "$extra_expected" in *[!0-9a-f]*) fail 'invalid extra checksum';; esac
extra_size=$("$B" stat -c %s "$EXTRA_SRC")
case "$extra_size" in ''|*[!0-9]*) fail 'invalid extra source size';; esac
'''
EXTRA_OLD=r'''
extra_old_table=$("$DM" table p50-staged-extra) || fail 'cannot inspect original extra table'
set -- $extra_old_table
[ "$#" -eq 5 ] && [ "$1" = 0 ] && [ "$3" = linear ] && [ "$5" = 0 ] || fail 'unexpected original extra table'
extra_old_sectors=$2
extra_old_target=$4
case "$extra_old_target" in ''|*[!0-9:]*) fail 'unexpected original extra target';; esac
extra_old_name=$("$B" readlink "/sys/dev/block/$extra_old_target") || fail 'cannot resolve original extra device'
extra_old_name=${extra_old_name##*/}
case "$extra_old_name" in loop[0-9]*) ;; *) fail 'original extra target is not a loop device';; esac
extra_old_backing=$("$B" cat "/sys/block/$extra_old_name/loop/backing_file") || fail 'cannot inspect original extra backing'
case "$extra_old_backing" in "$EXTRA_SRC"|"${EXTRA_SRC#/}") ;; *) fail 'extra loop does not point to boot image';; esac
EXTRA_OLD_LOOP="/dev/$extra_old_name"
'''
EXTRA_COPY_VERIFY=r'''
emit P50_DUAL_EXTRA_COPYING
"$B" cp "$EXTRA_SRC" "$EXTRA_COPY" || fail 'extra copy failed'
[ "$("$B" stat -c %s "$EXTRA_COPY")" = "$extra_size" ] || fail 'extra copied size differs'
extra_actual=$("$B" sha256sum "$EXTRA_COPY") || fail 'extra copy hash failed'
extra_actual=${extra_actual%% *}
[ "$extra_actual" = "$extra_expected" ] || fail 'extra hash differs from ISO manifest'
EXTRA_NEW_LOOP=$("$B" losetup -f) || fail 'no free extra loop device'
"$B" losetup -r "$EXTRA_NEW_LOOP" "$EXTRA_COPY" || fail 'cannot attach extra RAM copy'
extra_new_name=${EXTRA_NEW_LOOP##*/}
extra_new_sectors=$("$B" cat "/sys/block/$extra_new_name/size") || fail 'cannot size extra RAM loop'
[ "$extra_new_sectors" = "$extra_old_sectors" ] || fail 'extra loop sizes differ'
"$DM" reload p50-staged-extra --readonly --table "0 $extra_new_sectors linear $EXTRA_NEW_LOOP 0" || fail 'cannot load extra table'
EXTRA_TABLE_LOADED=1
emit P50_DUAL_EXTRA_COPY_VERIFIED
'''
EXTRA_SWITCH_VERIFY=r'''
emit P50_DUAL_ROOT_SWITCHED
/run/p50-stage/tools/p50-switch-extra || fail 'cannot complete extra mapper switch'
extra_new_table=$("$DM" table p50-staged-extra) || fail 'cannot inspect new extra table'
set -- $extra_new_table
[ "$#" -eq 5 ] && [ "$1" = 0 ] && [ "$2" = "$extra_new_sectors" ] && [ "$3" = linear ] && [ "$5" = 0 ] || fail 'unexpected new extra table'
extra_new_target_name=$("$B" readlink "/sys/dev/block/$4") || fail 'cannot resolve new extra target'
[ "${extra_new_target_name##*/}" = "$extra_new_name" ] || fail 'extra mapping is not using RAM loop'
extra_new_backing=$("$B" cat "/sys/block/$extra_new_name/loop/backing_file") || fail 'cannot inspect extra RAM backing'
case "$extra_new_backing" in "$EXTRA_COPY"|"${EXTRA_COPY#/}") ;; *) fail 'new extra backing is not RAM copy';; esac
emit "P50_DUAL_EXTRA_RAM_BACKING=$extra_new_backing"
"$B" losetup -d "$EXTRA_OLD_LOOP" || fail 'old extra loop is still in use'
'''
def patch_migration(text):
 if 'P50_DUAL_EXTRA_COPY_VERIFIED' in text:raise ValueError('Already patched')
 text=replace_once(text,"NEW_LOOP=''\n",EXTRA_META+"NEW_LOOP=''\n")
 text=replace_once(text,'        if [ "$TABLE_LOADED" = 1 ]; then', '        if [ "$EXTRA_TABLE_LOADED" = 1 ]; then "$DM" clear p50-staged-extra || true; fi\n        if [ -n "$EXTRA_NEW_LOOP" ]; then "$B" losetup -d "$EXTRA_NEW_LOOP" || true; fi\n        "$B" rm -f "$EXTRA_COPY" || true\n        if [ "$TABLE_LOADED" = 1 ]; then')
 text=replace_once(text,'need_k=$(( (size + 1023) / 1024 ))',EXTRA_PREP+'need_k=$(( (size + extra_size + 1023) / 1024 ))')
 text=replace_once(text,'emit P50_STAGE_COPYING\n',EXTRA_OLD+'emit P50_STAGE_COPYING\n')
 text=replace_once(text,'emit P50_STAGE_COPY_VERIFIED\n',EXTRA_COPY_VERIFY+'emit P50_STAGE_COPY_VERIFIED\n')
 text=replace_once(text,'"$B" losetup -d "$OLD_LOOP" || fail \'old loop is still in use\'\n',EXTRA_SWITCH_VERIFY+'"$B" losetup -d "$OLD_LOOP" || fail \'old loop is still in use\'\n')
 text=replace_once(text,'printf \'%s\\n\' "$new_table" > /run/p50-stage/READY','printf \'%s\\n%s\\n\' "$new_table" "$extra_new_table" > /run/p50-stage/READY')
 return text

def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root.resolve(strict=True)
 if root==Path('/'):raise ValueError('Refusing to change running system')
 targets=[(root/'usr/lib/live/boot/9990-misc-helpers.sh',patch_helper),(root/'usr/lib/p50-stage/p50-migrate.sh',patch_migration)]
 changed=[]
 for path,func in targets:
  if path.is_symlink() or not path.is_file():raise ValueError('Expected isolated regular script')
  changed.append((path,func(path.read_text())))
 for path,data in changed:path.write_text(data)
if __name__=='__main__':main()
