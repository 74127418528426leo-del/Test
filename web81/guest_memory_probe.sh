#!/bin/sh
# Puppy50 v81: read-only RAM and kernel memory-pressure sampling.
# This experimental diagnostic writes only fixed counters to QEMU ttyS0,
# never URLs, site data, passwords, browser profile or environment variables.
# Does not alter Firefox sandbox, memory limits, swap or network routing.
set -u
tick=0
while :; do
  uptime=$(awk '{print $1}' /proc/uptime 2>/dev/null || echo 0)
  counts=$(awk '
   /^MemTotal:/ {total=$2}
   /^MemAvailable:/ {avail=$2}
   /^MemFree:/ {free=$2}
   /^SwapTotal:/ {swaptotal=$2}
   /^SwapFree:/ {swapfree=$2}
   /^AnonPages:/ {anon=$2}
   /^Shmem:/ {shmem=$2}
   END {printf "total_kib=%s available_kib=%s free_kib=%s swap_total_kib=%s swap_free_kib=%s anon_kib=%s shmem_kib=%s",
     total,avail,free,swaptotal,swapfree,anon,shmem}
  ' /proc/meminfo 2>/dev/null)
  oom=$(awk '$1=="oom_kill" {print $2}' /proc/vmstat 2>/dev/null)
  [ -n "$oom" ] || oom=-1
  psi_some=-1
  psi_full=-1
  if [ -r /proc/pressure/memory ]; then
    psi_some=$(awk '$1=="some" {sub("avg10=","",$2);print $2}' /proc/pressure/memory 2>/dev/null)
    psi_full=$(awk '$1=="full" {sub("avg10=","",$2);print $2}' /proc/pressure/memory 2>/dev/null)
    [ -n "$psi_some" ] || psi_some=-1
    [ -n "$psi_full" ] || psi_full=-1
  fi
  firefox_count=0
  firefox_vm_rss_kib=0
  # VmRSS includes mapped/shared pages counted across multiple processes.
  # This is for trends only, NOT unique/PSS RAM accounting.
  for proc in /proc/[0-9]*; do
    [ -r "$proc/comm" ] || continue
    name=$(cat "$proc/comm" 2>/dev/null || true)
    case "$name" in
      firefox*|"Web Content"|"Socket Process"|"RDD Process"|"Privileged Cont"|"Utility Process")
        firefox_count=$((firefox_count+1))
        rss=$(awk '/^VmRSS:/ {print $2;exit}' "$proc/status" 2>/dev/null)
        case "$rss" in ''|*[!0-9]*) rss=0;; esac
        firefox_vm_rss_kib=$((firefox_vm_rss_kib+rss))
        ;;
    esac
  done
  printf 'PUPPY50_V81_MEM tick=%s uptime_sec=%s %s oom_kill=%s psi_some_avg10=%s psi_full_avg10=%s browser_processes=%s browser_VmRSS_sum_kib=%s\n'      "$tick" "$uptime" "$counts" "$oom" "$psi_some" "$psi_full"      "$firefox_count" "$firefox_vm_rss_kib" >/dev/ttyS0 2>/dev/null || true
  tick=$((tick+1))
  sleep 10
done
