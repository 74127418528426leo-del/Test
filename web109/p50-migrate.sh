#!/run/p50-stage/tools/busybox sh
# Experimental only. Never signals ready until the complete root copy is
# verified and the original read-only loop has been detached.
set -eu
B=/run/p50-stage/tools/busybox
DM=/run/p50-stage/tools/dm-run
SRC=/run/live/medium/live/filesystem.squashfs
MANIFEST=/run/live/medium/sha256sum.txt
COPY=/run/p50-stage/root.squashfs
NEW_LOOP=''
TABLE_LOADED=0
SWITCH_ATTEMPTED=0
SWITCHED=0
READY=0
if [ -c /dev/ttyS0 ]; then exec >/dev/ttyS0 2>&1; fi
fail() { echo "P50_STAGE_FAILED: $*"; exit 1; }
cleanup() {
    if [ "$READY" = 1 ]; then return; fi
    if [ "$SWITCH_ATTEMPTED" = 0 ]; then
        if [ "$TABLE_LOADED" = 1 ]; then "$DM" clear p50-staged-root || true; fi
        if [ -n "$NEW_LOOP" ]; then "$B" losetup -d "$NEW_LOOP" || true; fi
        "$B" rm -f "$COPY" || true
    else
        # A failed or interrupted switch has uncertain active backing.
        # Keep both devices and the RAM copy until reboot; never claim ready.
        echo P50_STAGE_SWITCH_UNCERTAIN_KEEP_BOTH
    fi
    printf 'not ready\n' > /run/p50-stage/FAILED || true
    echo P50_STAGE_NOT_READY
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM
"$B" sleep 8
echo P50_STAGE_START
[ -f "$SRC" ] && [ ! -L "$SRC" ] || fail 'source image absent or symlink'
[ -r "$MANIFEST" ] || fail 'media checksum manifest absent'
[ ! -e "$COPY" ] || fail 'RAM destination already exists'
[ "$("$B" stat -f -c %T /run/p50-stage)" = tmpfs ] || fail 'destination is not tmpfs'
expected=$("$B" awk '$2=="./live/filesystem.squashfs" { print $1 }' "$MANIFEST")
[ "${#expected}" -eq 64 ] || fail 'source checksum missing or ambiguous'
case "$expected" in *[!0-9a-f]*) fail 'invalid source checksum';; esac
size=$("$B" stat -c %s "$SRC")
case "$size" in ''|*[!0-9]*) fail 'invalid source size';; esac
need_k=$(( (size + 1023) / 1024 ))
mem_k=$("$B" awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
free_k=$("$B" df -Pk /run/p50-stage | "$B" awk 'NR==2 {print $4}')
case "$mem_k:$free_k" in *[!0-9:]*) fail 'cannot measure free space';; esac
[ "$mem_k" -ge $((need_k + 393216)) ] || fail 'insufficient available memory and reserve'
[ "$free_k" -ge $((need_k + 32768)) ] || fail 'insufficient tmpfs space'
set -f
old_table=$("$DM" table p50-staged-root) || fail 'cannot inspect original table'
set -- $old_table
[ "$#" -eq 5 ] && [ "$1" = 0 ] && [ "$3" = linear ] && [ "$5" = 0 ] || fail 'unexpected original table'
old_sectors=$2
old_target=$4
case "$old_target" in ''|*[!0-9:]*) fail 'unexpected original target';; esac
old_name=$("$B" readlink "/sys/dev/block/$old_target") || fail 'cannot resolve original device'
old_name=${old_name##*/}
case "$old_name" in loop[0-9]*) ;; *) fail 'original target is not a loop device';; esac
old_backing=$("$B" cat "/sys/block/$old_name/loop/backing_file") || fail 'cannot inspect original loop backing'
case "$old_backing" in "$SRC"|"${SRC#/}") ;; *) fail 'original loop does not point to boot image';; esac
OLD_LOOP="/dev/$old_name"
echo P50_STAGE_COPYING
"$B" cp "$SRC" "$COPY" || fail 'copy failed'
[ "$("$B" stat -c %s "$COPY")" = "$size" ] || fail 'copied size differs'
actual=$("$B" sha256sum "$COPY") || fail 'copy hash failed'
actual=${actual%% *}
[ "$actual" = "$expected" ] || fail 'copied hash differs from ISO manifest'
echo P50_STAGE_COPY_VERIFIED
NEW_LOOP=$("$B" losetup -f) || fail 'no free loop device'
"$B" losetup -r "$NEW_LOOP" "$COPY" || fail 'cannot attach RAM copy'
new_name=${NEW_LOOP##*/}
new_sectors=$("$B" cat "/sys/block/$new_name/size") || fail 'cannot size RAM loop'
[ "$new_sectors" = "$old_sectors" ] || fail 'loop sizes differ'
"$DM" reload p50-staged-root --readonly --table "0 $new_sectors linear $NEW_LOOP 0" || fail 'cannot load new table'
TABLE_LOADED=1
# This static helper performs suspend and resume in the same process. It and
# its executable pages are in tmpfs, so it does not start a dynamic loader from
# the root filesystem while that filesystem is suspended.
SWITCH_ATTEMPTED=1
/run/p50-stage/tools/p50-switch || fail 'cannot complete mapper switch'
SWITCHED=1
new_table=$("$DM" table p50-staged-root) || fail 'cannot inspect new table'
set -- $new_table
[ "$#" -eq 5 ] && [ "$1" = 0 ] && [ "$2" = "$new_sectors" ] && [ "$3" = linear ] && [ "$5" = 0 ] || fail 'unexpected new table'
new_target_name=$("$B" readlink "/sys/dev/block/$4") || fail 'cannot resolve new target'
[ "${new_target_name##*/}" = "$new_name" ] || fail 'mapping is not using the RAM loop'
new_backing=$("$B" cat "/sys/block/$new_name/loop/backing_file") || fail 'cannot inspect RAM loop backing'
case "$new_backing" in "$COPY"|"${COPY#/}") ;; *) fail 'new loop backing is not the RAM copy';; esac
"$B" losetup -d "$OLD_LOOP" || fail 'old loop is still in use'
printf '%s\n' "$new_table" > /run/p50-stage/READY
echo "P50_STAGE_RAM_BACKING=$new_backing"
echo "P50_STAGE_RAM_TABLE=$new_table"
READY=1
echo P50_STAGE_READY
