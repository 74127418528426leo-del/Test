#!/bin/sh
# Puppy50 v27: preserve original plocate autostart entry and defer its initial run.
# Fail closed: this builder refuses to patch unknown or conflicting layouts.
set -eu
if [ "$#" -ne 4 ]; then
  echo "Usage: $0 original_main.sfs output_ydrv.sfs saved_original_desktop_entry preexisting_probe_ydrv.sfs" >&2; exit 2
fi
base=$1; out=$2; saved=$3; probe=$4
[ -r "$base" ] && [ -r "$probe" ] || { echo "Missing original or probe SFS" >&2; exit 2; }
[ ! -e "$out" ] || { echo "Refusing to overwrite an existing ydrv" >&2; exit 2; }
command -v unsquashfs >/dev/null
command -v mksquashfs >/dev/null
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
unsquashfs -d "$tmp" "$probe" >/dev/null
mkdir -p "$tmp/etc/xdg/autostart" "$tmp/usr/local/bin"
found=0
for layer in "$(dirname "$base")"/*.sfs; do
  [ -r "$layer" ] || continue
  if unsquashfs -cat "$layer" etc/xdg/autostart/plocate-update.desktop > "$saved.tmp" 2>/dev/null; then
    found=$((found+1))
    mv "$saved.tmp" "$saved"
  fi
done
rm -f "$saved.tmp"
[ "$found" -eq 1 ] || { echo "Expected exactly one original plocate entry, found $found" >&2; exit 3; }
test "$(grep -c '^Exec=plocate-update-db$' "$saved")" -eq 1 || {
  echo "Expected exactly the original plocate Exec line" >&2; exit 3;
}
sed 's|^Exec=plocate-update-db$|Exec=/usr/local/bin/puppy50-plocate-deferred|' "$saved" > "$tmp/etc/xdg/autostart/plocate-update.desktop"
cat > "$tmp/usr/local/bin/puppy50-plocate-deferred" <<'LAUNCH'
#!/bin/sh
# Only delay the automatic update. Preserve plocate binaries and user menu actions.
(
  echo "PUPPY50_INDEX_DEFERRED scheduled" > /dev/ttyS0 2>/dev/null || true
  sleep 240
  echo "PUPPY50_INDEX_DEFERRED starting" > /dev/ttyS0 2>/dev/null || true
  if command -v ionice >/dev/null 2>&1; then
    ionice -c3 nice -n19 plocate-update-db
  else
    nice -n19 plocate-update-db
  fi
  rc=$?
  echo "PUPPY50_INDEX_DEFERRED exit=$rc" > /dev/ttyS0 2>/dev/null || true
) >/var/log/puppy50-plocate-v27.log 2>&1 &
exit 0
LAUNCH
chmod 755 "$tmp/usr/local/bin/puppy50-plocate-deferred"
mksquashfs "$tmp" "$out" -noappend -no-progress >/dev/null
echo "Preserved original desktop entry: $saved"
echo "Added delayed equivalent: $out"
