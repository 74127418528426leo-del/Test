#!/bin/sh
# Puppy50 v31: additive, reversible preseeded search database in the existing ydrv.
set -eu
[ "$#" -eq 3 ] || { echo "Usage: $0 existing_probe_ydrv.sfs verified_plocate.db new_ydrv.sfs" >&2; exit 2; }
source=$1; db=$2; output=$3
[ -r "$source" ] && [ -r "$db" ] && [ ! -e "$output" ] || { echo "Missing input or destination exists" >&2; exit 2; }
expected=164edf21846c05c22d212a0c144b90a97b54e8b997306e7976f29270b59b8c50
printf '%s  %s\n' "$expected" "$db" | sha256sum -c -
root=$(mktemp -d)
trap 'rm -rf "$root"' EXIT HUP INT TERM
unsquashfs -d "$root" "$source" >/dev/null
mkdir -p "$root/var/lib/plocate"
cp "$db" "$root/var/lib/plocate/plocate.db"
chmod 640 "$root/var/lib/plocate/plocate.db"
chown 0:114 "$root/var/lib/plocate/plocate.db"
mksquashfs "$root" "$output" -noappend -no-progress -all-root >/dev/null
[ -s "$output" ] || exit 4
unsquashfs -cat "$output" var/lib/plocate/plocate.db | sha256sum | grep "^$expected" >/dev/null
echo "Prebuilt search DB embedded without changing Puppy packages or desktop"
