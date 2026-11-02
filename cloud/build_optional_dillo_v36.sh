#!/bin/sh
# Puppy50 experimental optional browser. Only Debian 12 Dillo and FLTK packages added.
set -eu
[ "$#" -eq 4 ] || { echo "Usage: $0 existing-ydrv dillo.deb libfltk.deb output-ydrv" >&2;exit 2; }
base=$1;pkg=$2;fltk=$3;out=$4
[ -r "$base" ] && [ -r "$pkg" ] && [ -r "$fltk" ] && [ ! -e "$out" ] || exit 3
test "$(dpkg-deb -f "$pkg" Package)" = "dillo" || exit 4
test "$(dpkg-deb -f "$pkg" Version)" = "3.0.5-7+b1" || exit 4
test "$(dpkg-deb -f "$fltk" Package)" = "libfltk1.3" || exit 4
test "$(dpkg-deb -f "$fltk" Version)" = "1.3.8-5" || exit 4
r=$(mktemp -d)
trap 'rm -rf "$r"' EXIT HUP INT TERM
unsquashfs -d "$r" "$base" >/dev/null
dpkg-deb -x "$pkg" "$r"
dpkg-deb -x "$fltk" "$r"
test -x "$r/usr/bin/dillo" || exit 5
test -x "$r/etc/rc.d/rc.local" || exit 5
test -r "$r/var/lib/plocate/plocate.db" || exit 5
mksquashfs "$r" "$out" -noappend -no-progress >/dev/null
test -s "$out"
echo "Experimental overlay contains Dillo 3.0.5 and FLTK 1.3.8. Firefox untouched."
