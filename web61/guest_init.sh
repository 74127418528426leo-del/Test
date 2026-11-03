#!/bin/busybox sh
# Minimal Debian WPE guest init after proven compressed RAM-root switch.
# No Xorg/Openbox, no physical swap, no TLS/sandbox weakening.
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export PATH HOME=/home/web WPE_PLATFORM=headless
export XDG_RUNTIME_DIR=/run/user/1000
log() { echo "$*" >/dev/ttyS0 2>/dev/null || true; }
log "PUPPY50_V61_DEBIAN_GUEST_INIT_BEGIN"
mkdir -p /run/user/1000 /dev/shm /tmp /var/tmp /home/web
mount -t tmpfs -o size=16m,mode=0755 tmpfs /run 2>/dev/null || true
mkdir -p /run/user/1000
chmod 0700 /run/user/1000
chown 1000:1000 /run/user/1000 /home/web
mount -t tmpfs -o size=32m,mode=1777 tmpfs /dev/shm 2>/dev/null || true
chmod 1777 /tmp /dev/shm
# The early RAM-initrd had already mounted /proc, /sys and devtmpfs and
# moved them into the RAM-root. Do not rely on host Docker namespaces.
if [ ! -r /proc/self/status ]; then log "PUPPY50_V61_NO_PROC"; exec /bin/busybox sh; fi
log "PUPPY50_V61_UNPRIVILEGED_USERNS_CONFIG"
cat /proc/sys/user/max_user_namespaces >/dev/ttyS0 2>/dev/null || true
cat /proc/sys/kernel/unprivileged_userns_clone >/dev/ttyS0 2>/dev/null || true
log "PUPPY50_V61_BEGIN_GUEST_MEMORY"
grep -E '^(MemTotal|MemAvailable|SwapTotal|SwapFree|Shmem):' /proc/meminfo >/dev/ttyS0 || true

# Guest-only memory telemetry. The full RAM-root tmpfs IS physically included
# in /proc/meminfo; unlike the previous Docker cgroup feasibility test.
(
 i=0
 while [ "$i" -lt 30 ]; do
   {
     echo "PUPPY50_V61_MEMORY_SAMPLE_BEGIN n=$i"
     grep -E '^(MemTotal|MemAvailable|SwapTotal|SwapFree|Shmem):' /proc/meminfo || true
     for p in /proc/[0-9]*; do
       [ -r "$p/comm" ] || continue
       comm=$(cat "$p/comm" 2>/dev/null) || continue
       case "$comm" in
         *WebKit*|*WPE*|*puppy50-wpe*)
           rss=$(awk '/^Rss:/{print $2;exit}' "$p/smaps_rollup" 2>/dev/null) || rss=0
           pss=$(awk '/^Pss:/{print $2;exit}' "$p/smaps_rollup" 2>/dev/null) || pss=0
           echo "PUPPY50_V61_PROCESS pid=${p##*/} comm=$comm rss_kib=${rss:-0} pss_kib=${pss:-0}"
           ;;
       esac
     done
     echo "PUPPY50_V61_MEMORY_SAMPLE_END n=$i"
   } >/dev/ttyS0 2>/dev/null || true
   i=$((i+1))
   sleep 3
 done
) &
log "PUPPY50_V61_WPE_SANDBOXED_LAUNCH_REQUESTED"
# No WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS override.
# setpriv drops root identity *before* WPE creates its sandboxed processes.
/usr/bin/setpriv --reuid 1000 --regid 1000 --clear-groups \
  /usr/local/bin/puppy50-wpe-headless >/dev/ttyS0 2>&1
status=$?
log "PUPPY50_V61_WPE_ENGINE_EXIT_CODE=$status"
log "PUPPY50_V61_WPE_END"
# Continue serial evidence without reusing removable media.
exec /bin/busybox sh </dev/console >/dev/ttyS0 2>&1
