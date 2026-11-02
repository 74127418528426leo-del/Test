#!/bin/sh
# Puppy50 v36: two identical instrumented ydrv layers; only Firefox memory-cache pref differs.
# Fail-closed if existing Firefox user.js in source layers is ambiguous.
set -eu
[ "$#" -eq 5 ] || { echo "Usage: $0 original-main.sfs source-probe-ydrv.sfs control-ydrv.sfs tuned-ydrv.sfs audit.txt" >&2; exit 2; }
base=$1; probe=$2; control=$3; tuned=$4; audit=$5
[ -s "$base" ] && [ -s "$probe" ] && [ ! -e "$control" ] && [ ! -e "$tuned" ] || exit 3
cp "$probe" "$control"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/rootfs"
unsquashfs -d "$tmp/rootfs" "$probe" >/dev/null
pref=opt/FirefoxESR-portable64/profile/user.js
mkdir -p "$tmp/rootfs/opt/FirefoxESR-portable64/profile"
orig=$tmp/original_user.js
found=0
for layer in "$(dirname "$base")"/*.sfs; do
  [ -s "$layer" ] || continue
  if unsquashfs -cat "$layer" "$pref" > "$tmp/current.js" 2>/dev/null; then
    found=$((found + 1))
    cp "$tmp/current.js" "$orig"
  fi
done
[ "$found" -le 1 ] || { echo "Multiple original Firefox user.js layers; refusing to modify" >&2; exit 5; }
if [ -f "$tmp/rootfs/$pref" ]; then
  echo "Measurement layer already modifies Firefox user.js; refusing" >&2
  exit 6
fi
if [ "$found" -eq 1 ]; then cp "$orig" "$tmp/rootfs/$pref"; else : > "$tmp/rootfs/$pref"; fi
cat >> "$tmp/rootfs/$pref" <<'PUPPY50_PREF'
//
// Puppy50 v36, experimental only: cap in-memory cache at 8 MiB.
// No browser sandboxing, site isolation, privacy or process security settings changed.
user_pref("browser.cache.memory.enable", true);
user_pref("browser.cache.memory.capacity", 8192);
PUPPY50_PREF
chmod 644 "$tmp/rootfs/$pref"
mksquashfs "$tmp/rootfs" "$tuned" -noappend -no-progress >/dev/null
unsquashfs -cat "$tuned" "$pref" > "$tmp/extracted_user.js"
cmp "$tmp/rootfs/$pref" "$tmp/extracted_user.js"
{
 echo 'PUPPY50_V36_EXPERIMENT=FIREFOX_MEMORY_CACHE_ONLY'
 echo 'BASELINE_INSTRUMENTATION_UNMODIFIED=yes'
 echo "ORIGINAL_USERJS_FOUND=$found"
 echo "BASELINE_YDRV_SHA256=$(sha256sum "$control" | cut -d' ' -f1)"
 echo "CAPPED_YDRV_SHA256=$(sha256sum "$tuned" | cut -d' ' -f1)"
 echo 'BROWSER_CACHE_MEMORY_CAPACITY_KIB=8192'
} > "$audit"
cat "$audit"
