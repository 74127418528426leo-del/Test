#!/bin/sh
# Puppy50 v40: measurement-only QA layer for RAM SFS loop backing and CD ejection.
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
  i=0
  while [ "$i" -lt 10 ]; do
    sleep 23
    i=$((i+1))
    if [ -w /dev/ttyS0 ]; then
      {
        echo "PUPPY50_V40_BEGIN sample=$i"
        echo "PUPPY50_V40_COPY_BACKING"
        n=0; sz=0
        for f in /initrd/mnt/tmpfs/*.sfs; do
          [ -s "$f" ] || continue
          n=$((n + 1))
          b=$(stat -c '%s' "$f")
          sz=$((sz + b))
          printf 'PUPPY50_V40_SFS file=%s size=%s\n' "$(basename "$f")" "$b"
        done
        echo "PUPPY50_V40_TOTAL count=$n size=$sz"
        echo "PUPPY50_V40_LOOP_BACKING"
        losetup -a 2>/dev/null || true
        echo "PUPPY50_V40_SWAP"
        cat /proc/swaps
        echo "PUPPY50_V40_MEMINFO"
        grep -E '^(MemTotal|MemAvailable|Shmem|SwapTotal|SwapFree):' /proc/meminfo
        echo "PUPPY50_V40_GUI"
        for p in Xorg jwm ROX-Filer; do
          if pidof "$p" >/dev/null 2>&1; then echo "PUPPY50_V40_GUI_PROCESS $p PASS"; else echo "PUPPY50_V40_GUI_PROCESS $p MISSING"; fi
        done
        echo "PUPPY50_V40_END sample=$i"
      } > /dev/ttyS0 2>&1
    fi
  done
) &
PROBE
  cat "$saved"
} > "$tmp/etc/rc.d/rc.local"
chmod +x "$tmp/etc/rc.d/rc.local"
mksquashfs "$tmp" "$out" -noappend -no-progress >/dev/null
echo "Saved original rc.local to $saved"
echo "Instrumented ydrv created: $out"
