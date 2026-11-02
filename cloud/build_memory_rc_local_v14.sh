#!/bin/sh
# Puppy50 v14: preserves original rc.local in a separate experimental ISO layer.
set -eu
if [ "$#" -ne 3 ]; then echo "Usage: $0 main.sfs output-ydrv.sfs original-rc.local-saved-copy" >&2; exit 2; fi
base=$1
out=$2
saved=$3
[ -r "$base" ] || { echo "Missing source SFS" >&2; exit 1; }
[ ! -e "$out" ] || { echo "Output already exists" >&2; exit 1; }
command -v unsquashfs >/dev/null || exit 2
command -v mksquashfs >/dev/null || exit 2
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/etc/rc.d" "$tmp/root/Startup"
# Scan every original layer that was extracted from the ISO. Never silently
# replace rc.local in a layer whose content we have not inspected.
found=0
for layer in "$(dirname "$base")"/*.sfs; do
  [ -r "$layer" ] || continue
  if unsquashfs -cat "$layer" etc/rc.d/rc.local > "$saved" 2>/dev/null; then
    echo "Existing rc.local found in $layer" >&2
    found=1
  fi
done
if [ "$found" -eq 0 ]; then
  # Puppy installations may intentionally have no rc.local. Add the hook as
  # a new overlay file, not as a replacement of an unknown original.
  : > "$saved"
  echo 'No original rc.local in any supplied SFS; creating a new one' >&2
fi
{
  echo '#!/bin/sh'
  echo '# Puppy50 temporary diagnostic hook; original rc.local follows unmodified.'
  cat <<'PROBE'
(
  sleep 6
  n=1
  while [ "$n" -le 12 ]; do
    if [ -w /dev/ttyS0 ]; then
      {
        echo "PUPPY50_V14_BEGIN sample=$n"
        cat /proc/uptime
        grep -E '^(MemTotal|MemFree|MemAvailable|Buffers|Cached|Shmem|Slab|KernelStack|PageTables|SwapTotal|SwapFree):' /proc/meminfo
        cat /proc/swaps
        if [ -r /sys/block/zram0/mm_stat ]; then
          echo PUPPY50_ZRAM_MM_STAT
          cat /sys/block/zram0/mm_stat
        fi
        echo PUPPY50_GRAPHICS_PROCESSES
        ps | grep -Ei 'Xorg|Xwayland|jwm|rox' | grep -v grep || true
        echo "PUPPY50_V14_END sample=$n"
      } > /dev/ttyS0 2>&1
    fi
    n=$((n + 1))
    sleep 15
  done
) &
PROBE
  cat "$saved"
} > "$tmp/etc/rc.d/rc.local"
chmod +x "$tmp/etc/rc.d/rc.local"
mksquashfs "$tmp" "$out" -noappend -no-progress >/dev/null
echo "Saved original rc.local to $saved"
echo "Instrumented ydrv created: $out"
