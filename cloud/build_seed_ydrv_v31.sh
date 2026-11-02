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
mksquashfs "$root" "$output" -noappend -no-progress >/dev/null
[ -s "$output" ] || exit 4
unsquashfs -cat "$output" var/lib/plocate/plocate.db | sha256sum | grep "^$expected" >/dev/null
# Preserve the plocate group; -all-root would incorrectly make the index root:root.
verify=$(mktemp -d)
unsquashfs -d "$verify" "$output" var/lib/plocate/plocate.db >/dev/null
[ "$(stat -c '%u:%g' "$verify/var/lib/plocate/plocate.db")" = "0:114" ] || {
  echo "Refusing release: plocate database ownership is not root:114" >&2; exit 7;
}
rm -rf "$verify"
echo "Prebuilt search DB embedded with verified root:plocate group ownership"
