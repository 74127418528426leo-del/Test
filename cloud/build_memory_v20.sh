#!/bin/sh
# Puppy50 v20: bounded diagnostic probe; preserves original rc.local, only cache test within throwaway VM.
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
# Do not collect hundreds of smaps: the v19 exhaustive scan ran beyond its boot window.
(
  sleep 8
  mode=control
  if grep -q 'puppy50_reclaim=1' /proc/cmdline; then mode=cache_reclaim; fi
  snapshot() {
    stage=$1
    {
      echo "PUPPY50_V20_BEGIN mode=$mode stage=$stage"
      echo "UPTIME $(cat /proc/uptime)"
      grep -E '^(MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapCached|Shmem|AnonPages|Active|Inactive|Slab|SReclaimable|SUnreclaim|KReclaimable|KernelStack|PageTables|SwapTotal|SwapFree|Committed_AS):' /proc/meminfo
      echo "PUPPY50_VMSTAT"
      grep -E '^(pgfault|pgmajfault|pswpin|pswpout) ' /proc/vmstat
      echo "PUPPY50_SWAPS"
      cat /proc/swaps
      if [ -r /sys/block/zram0/mm_stat ]; then
        echo "PUPPY50_ZRAM"; cat /sys/block/zram0/mm_stat
      fi
      echo "PUPPY50_PROCESS_PSS"
      for f in /proc/[0-9]*/comm; do
        [ -r "$f" ] || continue
        name=$(cat "$f" 2>/dev/null) || continue
        case "$name" in
          Xorg|X|jwm|ROX-Filer|rox|firefox*|dbus-daemon|udevd|pulseaudio|conky|xwin|urxvt|gtkdialog|geany)
            pid=$(basename "$(dirname "$f")")
            if [ -r "/proc/$pid/smaps_rollup" ]; then
              awk -v name="$name" -v pid="$pid" '
                /^Pss:/ {pss=$2}
                /^Rss:/ {rss=$2}
                /^Pss_Anon:/ {anon=$2}
                /^Pss_File:/ {file=$2}
                /^Pss_Shmem:/ {shmem=$2}
                END {printf "PSS pid=%s name=%s pss_kib=%.0f rss_kib=%.0f anon_kib=%.0f file_kib=%.0f shmem_kib=%.0f\n",pid,name,pss,rss,anon,file,shmem}' "/proc/$pid/smaps_rollup" 2>/dev/null || true
            fi
            ;;
        esac
      done
      echo "PUPPY50_V20_END mode=$mode stage=$stage"
    } > /dev/ttyS0 2>&1
  }
  if [ -w /dev/ttyS0 ]; then
    snapshot before
    if [ "$mode" = cache_reclaim ]; then
      sync
      if echo 3 > /proc/sys/vm/drop_caches; then
        echo "PUPPY50_V20_RECLAIM_TRIGGER success" > /dev/ttyS0
      else
        echo "PUPPY50_V20_RECLAIM_TRIGGER failed" > /dev/ttyS0
      fi
    fi
    sleep 12
    snapshot after
    sleep 12
    snapshot later
  fi
) &
PROBE
  cat "$saved"
} > "$tmp/etc/rc.d/rc.local"
chmod +x "$tmp/etc/rc.d/rc.local"
mksquashfs "$tmp" "$out" -noappend -no-progress >/dev/null
echo "Saved original rc.local to $saved"
echo "Instrumented ydrv created: $out"
