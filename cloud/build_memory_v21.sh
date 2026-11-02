#!/bin/sh
# Puppy50 v21: passive stable-baseline profiler with original rc.local preserved.
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
# Puppy50 v21: observe, do not reclaim pages or alter applications.
(
  # Wait until the original Xorg + JWM desktop services are present.
  ready=0
  for i in $(seq 1 100); do
    if pidof Xorg >/dev/null 2>&1 && pidof jwm >/dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 3
  done
  if [ "$ready" = 0 ]; then
    echo "PUPPY50_V21_DESKTOP_NOT_READY" > /dev/ttyS0
    exit 0
  fi
  sleep 12
  n=1
  while [ "$n" -le 8 ]; do
    if [ -w /dev/ttyS0 ]; then
      {
        echo "PUPPY50_V21_BEGIN sample=$n"
        printf 'UPTIME '; cat /proc/uptime
        printf 'LOAD '; cat /proc/loadavg
        echo "PUPPY50_GUI Xorg=$(pidof Xorg 2>/dev/null) jwm=$(pidof jwm 2>/dev/null) ROX=$(pidof ROX-Filer 2>/dev/null)"
        grep -E '^(MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapCached|Shmem|AnonPages|Slab|SReclaimable|SUnreclaim|KernelStack|PageTables|SwapTotal|SwapFree):' /proc/meminfo
        echo "PUPPY50_PSI_MEMORY"; cat /proc/pressure/memory 2>/dev/null || true
        echo "PUPPY50_TOP_ANON_START"
        for f in /proc/[0-9]*/status; do
          [ -r "$f" ] || continue
          awk '
            /^Name:/ {name=$2}
            /^Pid:/ {pid=$2}
            /^VmRSS:/ {rss=$2}
            /^RssAnon:/ {anon=$2}
            /^RssFile:/ {file=$2}
            /^RssShmem:/ {shmem=$2}
            /^VmSwap:/ {swap=$2}
            END {if(rss>0) printf "PROC %s %s %.0f %.0f %.0f %.0f %.0f\n",pid,name,rss,anon,file,shmem,swap}
          ' "$f" 2>/dev/null
        done | sort -k5,5nr | head -n 24
        echo "PUPPY50_TOP_ANON_END"
        echo "PUPPY50_PSS_SELECTED"
        for pid in $(pidof Xorg jwm ROX-Filer firefox 2>/dev/null); do
          [ -r "/proc/$pid/smaps_rollup" ] || continue
          awk -v pid="$pid" '
            /^Rss:/ {rss=$2}
            /^Pss:/ {pss=$2}
            /^Pss_Anon:/ {anon=$2}
            /^Pss_File:/ {file=$2}
            END {printf "PSS %s %.0f %.0f %.0f %.0f\n",pid,pss,rss,anon,file}
          ' "/proc/$pid/smaps_rollup" 2>/dev/null || true
        done
        echo "PUPPY50_V21_END sample=$n"
      } > /dev/ttyS0 2>&1
    fi
    n=$((n + 1))
    sleep 24
  done
) &
PROBE
  cat "$saved"
} > "$tmp/etc/rc.d/rc.local"
chmod +x "$tmp/etc/rc.d/rc.local"
mksquashfs "$tmp" "$out" -noappend -no-progress >/dev/null
echo "Saved original rc.local to $saved"
echo "Instrumented ydrv created: $out"
