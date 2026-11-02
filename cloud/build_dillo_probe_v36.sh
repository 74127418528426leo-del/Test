#!/bin/sh
# Puppy50 v26: original browser launcher test after verified graphical boot.
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
    echo "PUPPY50_V31_PRESEED_BEGIN"
    if [ -s /var/lib/plocate/plocate.db ]; then
      echo "PUPPY50_V31_DB_PRESENT=yes"
      ls -l /var/lib/plocate/plocate.db
      if /usr/bin/plocate -d /var/lib/plocate/plocate.db 'ROX-Filer' 2>/tmp/puppy50_v31_query.err | grep -q '/usr/local/apps/ROX-Filer'; then
        echo "PUPPY50_V31_ROX_SEARCH=PASS"
      else
        echo "PUPPY50_V31_ROX_SEARCH=FAIL"
        cat /tmp/puppy50_v31_query.err
      fi
    else
      echo "PUPPY50_V31_DB_PRESENT=no"
      echo "PUPPY50_V31_ROX_SEARCH=FAIL"
    fi
    echo "PUPPY50_V31_PRESEED_END"
    echo "PUPPY50_V25_END"
  } > /dev/ttyS0 2>&1
  # Separate lightweight browser trial. Original Firefox remains installed.
  {
    echo "PUPPY50_V36_BEGIN"
    if ! command -v dillo >/dev/null 2>&1; then
      echo "PUPPY50_V36_DILLO_MISSING"
    else
      echo "PUPPY50_V36_DILLO_PRESENT"
      cat > /tmp/puppy50-v36-dillo.html <<'HTML'
<!doctype html>
<html><head><title>PUPPY50 V36 DILLO PAGE PASS</title></head>
<body style="background:#f5f9ff;color:#002b56">
<h1>PUPPY50 V36 DILLO PAGE PASS</h1><p>Lightweight offline webpage.</p>
</body></html>
HTML
      export DISPLAY=:0
      dillo file:///tmp/puppy50-v36-dillo.html >/tmp/puppy50-v36-dillo.log 2>&1 &
      echo "PUPPY50_V36_LAUNCH_REQUESTED"
      i=1
      while [ "$i" -le 5 ]; do
        sleep 22
        echo "PUPPY50_V36_SCAN_BEGIN scan=$i"
        ps | grep -Ei 'dillo' | grep -v grep || true
        if command -v xwininfo >/dev/null 2>&1; then
          xwininfo -root -tree 2>&1 | head -n 95
        fi
        grep -E '^(MemTotal|MemAvailable|SwapTotal|SwapFree|AnonPages):' /proc/meminfo
        if [ -r /sys/block/zram0/mm_stat ]; then
          echo PUPPY50_V36_ZRAM
          cat /sys/block/zram0/mm_stat
        fi
        echo "PUPPY50_V36_SCAN_END scan=$i"
        i=$((i+1))
      done
      echo "PUPPY50_V36_DILLO_LOG_BEGIN"
      tail -c 1600 /tmp/puppy50-v36-dillo.log 2>/dev/null || true
      echo "PUPPY50_V36_DILLO_LOG_END"
    fi
    echo "PUPPY50_V36_END"
  } > /dev/ttyS0 2>&1
) &
PROBE
  cat "$saved"
} > "$tmp/etc/rc.d/rc.local"
chmod +x "$tmp/etc/rc.d/rc.local"
mksquashfs "$tmp" "$out" -noappend -no-progress >/dev/null
echo "Saved original rc.local to $saved"
echo "Instrumented ydrv created: $out"
