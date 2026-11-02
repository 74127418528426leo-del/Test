#!/bin/sh
# Puppy50 v37: bounded Firefox process PSS attribution at exactly 384MiB.
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
  # Passive feature gate; no network and no user files modified.
  ready=0
  i=0
  while [ "$i" -lt 100 ]; do
    if pidof Xorg >/dev/null 2>&1 && pidof jwm >/dev/null 2>&1; then ready=1; break; fi
    i=$((i+1)); sleep 2
  done
  {
    echo "PUPPY50_V25_BEGIN"
    echo "PUPPY50_TEST desktop_processes=$ready"
    for app in Xorg jwm ROX-Filer; do
      if pidof "$app" >/dev/null 2>&1; then echo "PUPPY50_TEST $app=PASS"; else echo "PUPPY50_TEST $app=FAIL"; fi
    done
    for app in firefox plocate rox xrandr ip aplay; do
      if command -v "$app" >/dev/null 2>&1; then echo "PUPPY50_TEST executable_$app=PASS"; else echo "PUPPY50_TEST executable_$app=MISSING"; fi
    done
    # Test X11 socket connectivity without starting external apps or opening windows.
    if [ -S /tmp/.X11-unix/X0 ]; then echo "PUPPY50_TEST x11_socket=PASS"; else echo "PUPPY50_TEST x11_socket=FAIL"; fi
    if [ "$ready" = 1 ]; then
      export DISPLAY=:0
      if command -v xrandr >/dev/null 2>&1 && xrandr -q >/dev/null 2>&1; then
        echo "PUPPY50_TEST xrandr_query=PASS"
      else
        echo "PUPPY50_TEST xrandr_query=NOT_VERIFIED"
      fi
    fi
    echo "PUPPY50_MEMORY"
    grep -E '^(MemTotal|MemAvailable|MemFree|AnonPages|Shmem|SUnreclaim|SwapTotal|SwapFree):' /proc/meminfo
    echo "PUPPY50_V25_END"
  } > /dev/ttyS0 2>&1
  # Now attempt a real offline browser launch in the disposable guest.
  # Preserve the original browser/launcher; only run it, do not repackage apps.
  {
    echo "PUPPY50_V26_BEGIN"
    for entry in defaultbrowser firefox firefox-esr firefox-bin chromium; do
      if command -v "$entry" >/dev/null 2>&1; then
        echo "PUPPY50_V26_ENTRY $entry PRESENT"
      else
        echo "PUPPY50_V26_ENTRY $entry MISSING"
      fi
    done
    if [ "$ready" = 1 ]; then
      export DISPLAY=:0
      entry=""
      for possible in defaultbrowser firefox firefox-esr; do
        if command -v "$possible" >/dev/null 2>&1; then entry="$possible"; break; fi
      done
      if [ -n "$entry" ]; then
        echo "PUPPY50_V26_BROWSER_REQUEST $entry"
        # Local-only deterministic content, with no network dependency.
        cat > /tmp/puppy50-offline-browser-proof.html <<'PUPPY50_LOCAL_HTML'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>PUPPY50 OFFLINE PAGE PROOF</title>
<style>
html,body{margin:0;min-height:100%;background:#07152a;color:#fbe8b7;font:700 38px Arial,sans-serif}
main{padding:55px 60px}
p{font:24px Arial,sans-serif;color:#d4e8ff}
</style>
</head>
<body><main>PUPPY50 OFFLINE PAGE PROOF<p>Real local HTML rendered by original Firefox ESR.</p></main></body>
</html>
PUPPY50_LOCAL_HTML
        echo "PUPPY50_V30_OFFLINE_PAGE_CREATED"
        ("$entry" file:///tmp/puppy50-offline-browser-proof.html >/tmp/puppy50_browser_v30.log 2>&1) &
      else
        echo "PUPPY50_V26_BROWSER_REQUEST NONE"
      fi
    else
      echo "PUPPY50_V26_BROWSER_REQUEST NO_GUI"
    fi
    i=1
    while [ "$i" -le 6 ]; do
      sleep 30
      echo "PUPPY50_V28_WINDOW_SCAN_BEGIN scan=$i"
      if command -v xwininfo >/dev/null 2>&1; then
        xwininfo -root -tree 2>&1 | head -n 100
      else
        echo "PUPPY50_V28_XWININFO_NOT_INSTALLED"
      fi
      echo "PUPPY50_V28_WINDOW_SCAN_END scan=$i"
      echo "PUPPY50_V28_PROCESS_SCAN scan=$i"
      ps | grep -Ei 'firefox|chromium|seamonkey' | grep -v grep || true
      echo "PUPPY50_V28_MEMORY scan=$i"
      grep -E '^(MemTotal|MemAvailable|SwapTotal|SwapFree|AnonPages|SUnreclaim|Cached):' /proc/meminfo
      echo "PUPPY50_V29_SWAPDEV scan=$i"
      cat /proc/swaps
      if [ -r /sys/block/zram0/mm_stat ]; then
        echo "PUPPY50_V29_ZRAM scan=$i"
        cat /sys/block/zram0/mm_stat
      fi
      echo "PUPPY50_V29_VMSTAT scan=$i"
      grep -E '^(pgmajfault|pswpin|pswpout) ' /proc/vmstat || true
      echo "PUPPY50_V29_MEM_PRESSURE scan=$i"
      cat /proc/pressure/memory 2>/dev/null || true
      if [ "$i" = 2 ] || [ "$i" = 6 ]; then
        echo "PUPPY50_V37_PROCESS_PSS_BEGIN scan=$i"
        count=0
        for pid in $(pidof firefox-bin 2>/dev/null); do
          if [ "$count" -ge 6 ]; then break; fi
          count=$((count+1))
          if [ -r "/proc/$pid/smaps_rollup" ]; then
            awk -v id="$pid" '
              /^Rss:/ {r=$2}
              /^Pss:/ {p=$2}
              /^Pss_Anon:/ {a=$2}
              /^Pss_File:/ {f=$2}
              /^SwapPss:/ {s=$2}
              END {printf "PUPPY50_V37_PSS pid=%s RssKiB=%d PssKiB=%d AnonKiB=%d FileKiB=%d SwapPssKiB=%d\n",id,r,p,a,f,s}
            ' "/proc/$pid/smaps_rollup" 2>/dev/null || true
          fi
        done
        echo "PUPPY50_V37_PROFILED_PROCESS_COUNT $count"
        for pid in $(pidof Xorg jwm ROX-Filer 2>/dev/null); do
          if [ -r "/proc/$pid/smaps_rollup" ]; then
            awk -v id="$pid" '
              /^Rss:/ {r=$2} /^Pss:/ {p=$2} /^Pss_Anon:/ {a=$2}
              END {printf "PUPPY50_V37_GUI_PSS pid=%s RssKiB=%d PssKiB=%d AnonKiB=%d\n",id,r,p,a}
            ' "/proc/$pid/smaps_rollup" 2>/dev/null || true
          fi
        done
        echo "PUPPY50_V37_KERNEL_COUNTERS"
        grep -E '^(Slab|SReclaimable|SUnreclaim|PageTables|KernelStack|Shmem|AnonPages):' /proc/meminfo
        echo "PUPPY50_V37_PROCESS_PSS_END scan=$i"
      fi
      i=$((i+1))
    done
    echo "PUPPY50_V26_BROWSER_PROCS"
    ps | grep -Ei 'firefox|chromium|browser|seamonkey' | grep -v grep || true
    echo "PUPPY50_V26_MEM_AFTER_BROWSER"
    grep -E '^(MemTotal|MemAvailable|AnonPages|SwapTotal|SwapFree):' /proc/meminfo
    echo "PUPPY50_V26_END"
  } > /dev/ttyS0 2>&1
) &
PROBE
  cat "$saved"
} > "$tmp/etc/rc.d/rc.local"
chmod +x "$tmp/etc/rc.d/rc.local"
mksquashfs "$tmp" "$out" -noappend -no-progress >/dev/null
echo "Saved original rc.local to $saved"
echo "Instrumented ydrv created: $out"
