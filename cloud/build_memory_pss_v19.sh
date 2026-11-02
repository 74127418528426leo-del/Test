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
  while [ "$n" -le 5 ]; do
    if [ -w /dev/ttyS0 ]; then
      {
        echo "PUPPY50_V19_BEGIN sample=$n"
        echo "UPTIME $(cat /proc/uptime)"
        cat /proc/meminfo
        echo PUPPY50_SWAPS
        cat /proc/swaps
        echo PUPPY50_PROCS_BEGIN
        for f in /proc/[0-9]*/smaps_rollup; do
          [ -r "$f" ] || continue
          pid=$(basename "$(dirname "$f")")
          [ -r "/proc/$pid/comm" ] || continue
          name=$(cat "/proc/$pid/comm" 2>/dev/null | tr '\t\n' '  ' | cut -c1-48) || continue
          awk -v pid="$pid" -v comm="$name" '
          /^Rss:/ {rss=$2}
          /^Pss:/ {pss=$2}
          /^Pss_Anon:/ {anon=$2}
          /^Pss_File:/ {file=$2}
          /^Pss_Shmem:/ {shmem=$2}
          /^Private_Dirty:/ {dirty=$2}
          /^SwapPss:/ {swappss=$2}
          END {if(pss!="") printf "PROC pid=%s pss_kib=%.0f rss_kib=%.0f anon_kib=%.0f file_kib=%.0f shmem_kib=%.0f private_dirty_kib=%.0f swap_pss_kib=%.0f name=%s\n",pid,pss,rss,anon,file,shmem,dirty,swappss,comm}' "$f" 2>/dev/null || true
        done
        echo PUPPY50_PROCS_END
        echo "PUPPY50_V19_END sample=$n"
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
