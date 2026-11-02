#!/bin/sh
# Puppy50 v50: read-only bounded guest memory diagnostic.
# Start from root before Xorg and Firefox. Output directly to VM serial.
# Does not alter security settings, swap, processes, graphics, or the browser.
set -u
PATH=/bin:/sbin:/usr/bin:/usr/sbin
export PATH
i=0
echo 'PUPPY50_V50_WATCH_BEGIN'
echo "PUPPY50_V50_WATCH_KERNEL=$(uname -r)"
while [ "$i" -lt 65 ]; do
  echo "PUPPY50_V50_SAMPLE_BEGIN index=$i"
  if [ -r /proc/meminfo ]; then
    awk '/^(MemTotal|MemAvailable|MemFree|Shmem|SwapTotal|SwapFree|Cached|SReclaimable|Slab):/ {
      printf "PUPPY50_V50_MEM %s %s\n",$1,$2
    }' /proc/meminfo
  fi
  if [ -r /proc/vmstat ]; then
    awk '$1=="oom_kill" || $1=="pgmajfault" || $1=="pswpin" || $1=="pswpout" {
      printf "PUPPY50_V50_VMSTAT %s %s\n",$1,$2
    }' /proc/vmstat
  fi
  if [ -r /proc/pressure/memory ]; then
    awk '{printf "PUPPY50_V50_PSI %s\n",$0}' /proc/pressure/memory
  fi
  if [ -r /proc/swaps ]; then
    awk 'NR>1 {printf "PUPPY50_V50_SWAP %s %s %s %s\n",$1,$2,$3,$4}' /proc/swaps
  fi
  for proc in /proc/[0-9]*; do
    [ -r "$proc/comm" ] || continue
    IFS= read -r comm < "$proc/comm" || continue
    case "$comm" in
      firefox*|Web\ Content*|Isolated\ Web*|Privileged\ Cont*|RDD\ Process*|GPU\ Process*|Socket\ Process*|Utility\ Process*|Xorg|openbox)
        pid=${proc##*/}
        rss=""
        pss=""
        [ -r "$proc/status" ] && rss=$(awk '$1=="VmRSS:"{print $2;exit}' "$proc/status" 2>/dev/null) || :
        [ -r "$proc/smaps_rollup" ] && pss=$(awk '$1=="Pss:"{print $2;exit}' "$proc/smaps_rollup" 2>/dev/null) || :
        echo "PUPPY50_V50_PROCESS pid=$pid comm=$comm rss_kib=${rss:-unavailable} pss_kib=${pss:-unavailable}"
        state=$(awk '$1=="State:"{print $2;exit}' "$proc/status" 2>/dev/null) || :
        threads=$(awk '$1=="Threads:"{print $2;exit}' "$proc/status" 2>/dev/null) || :
        vmsize=$(awk '$1=="VmSize:"{print $2;exit}' "$proc/status" 2>/dev/null) || :
        vmpeak=$(awk '$1=="VmPeak:"{print $2;exit}' "$proc/status" 2>/dev/null) || :
        wchan="unavailable"
        [ -r "$proc/wchan" ] && IFS= read -r wchan < "$proc/wchan" || :
        echo "PUPPY50_V52_STATE pid=$pid comm=$comm state=${state:-unknown} threads=${threads:-unknown} vmsize_kib=${vmsize:-unknown} vmpeak_kib=${vmpeak:-unknown} wchan=${wchan:-unavailable}"
        # Firefox parent wait state and representative thread channels;
        # avoid hundreds of costly /proc reads in multiprocess environments.
        case "$comm" in
          firefox*)
            sampled=0
            for task in "$proc"/task/[0-9]*; do
              [ -r "$task/wchan" ] || continue
              tid=${task##*/}
              tw="unavailable"
              IFS= read -r tw < "$task/wchan" || :
              echo "PUPPY50_V52_THREAD pid=$pid tid=$tid wchan=${tw:-unavailable}"
              sampled=$((sampled+1))
              [ "$sampled" -lt 6 ] || break
            done
            ;;
        esac
        ;;
    esac
  done
  if [ "$i" -eq 8 ] || [ "$i" -eq 24 ] || [ "$i" -eq 48 ]; then
    echo "PUPPY50_V50_XORG_LOG_SNIP_BEGIN"
    [ ! -f /var/log/Xorg0.log ] || tail -n 14 /var/log/Xorg0.log 2>/dev/null || :
    echo "PUPPY50_V50_XORG_LOG_SNIP_END"
    echo "PUPPY50_V50_FIREFOX_LOG_SNIP_BEGIN"
    [ ! -f /var/log/firefox.log ] || tail -n 14 /var/log/firefox.log 2>/dev/null || :
    echo "PUPPY50_V50_FIREFOX_LOG_SNIP_END"
  fi
  echo "PUPPY50_V50_SAMPLE_END index=$i"
  i=$((i+1))
  sleep 3
done
echo 'PUPPY50_V50_WATCH_END'
