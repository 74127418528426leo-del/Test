#!/bin/sh
# Read-only guest probe for Puppy50 Web. Must run in the real booted GUEST,
# preferably with privileges to read process smaps_rollup.
# This logs evidence; it never claims a browser rendered or HTTPS worked.
set -eu
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH

echo 'PUPPY50_RAM_PROBE_BEGIN'
echo 'PUPPY50_RAM_PROBE_VERSION=1'
uname -r | sed 's/^/KERNEL_RELEASE=/'
if [ -r /proc/mounts ]; then
  awk '$2=="/" || $2=="/.web-ram" || $2=="/.web-rw" || $2=="/.web-lower" || $3=="iso9660" {
    printf "MOUNT source=%s target=%s fstype=%s\n", $1, $2, $3
  }' /proc/mounts
fi
if [ -f /.web-ram/webroot.sfs ]; then
  echo "RAM_IMAGE_BYTES=$(stat -c '%s' /.web-ram/webroot.sfs)"
  echo 'RAM_IMAGE_PATH=/.web-ram/webroot.sfs'
else
  echo 'RAM_IMAGE_MISSING=1'
fi

# The kernel's path for an attached loop file may reflect the pre-move
# mountpoint; report raw evidence instead of guessing its current backing.
for file in /sys/block/loop*/loop/backing_file; do
  [ -r "$file" ] || continue
  path=${file%/loop/backing_file}
  dev=${path##*/}
  backing=$(cat "$file" 2>/dev/null || :)
  [ -n "$backing" ] && printf 'LOOP_BACKING device=%s path=%s\n' "$dev" "$backing"
done
if [ -r /proc/meminfo ]; then
  awk '/^(MemTotal|MemAvailable|MemFree|Shmem|SwapTotal|SwapFree|Slab|SReclaimable|Cached|Buffers):/ {
    printf "MEMINFO key=%s kib=%s\n", $1,$2
  }' /proc/meminfo
fi
if [ -r /proc/vmstat ]; then
  awk '$1=="oom_kill" || $1=="pgmajfault" || $1=="pswpin" || $1=="pswpout" {
    printf "VMSTAT key=%s count=%s\n",$1,$2
  }' /proc/vmstat
fi
if [ -r /proc/swaps ]; then
  awk 'NR>1 {printf "SWAP_DEVICE path=%s type=%s size_kib=%s used_kib=%s\\n", $1,$2,$3,$4}' /proc/swaps
fi
if [ -r /proc/pressure/memory ]; then
  awk '{printf "MEMORY_PSI %s\n",$0}' /proc/pressure/memory
fi
# PSS avoids naïvely double counting libraries shared across processes.
# Inaccessible process smaps are omitted, not silently counted as zero.
for proc in /proc/[0-9]*; do
  [ -r "$proc/comm" ] || continue
  comm=$(cat "$proc/comm" 2>/dev/null || :)
  case "$comm" in
    *firefox*|*WebKit*|*epiphany*|*Web\ Content*|*Isolated\ Web*|*Privileged\ Cont*|*RDD\ Process*|*Socket\ Process*|*Utility\ Process*|Xorg|Xwayland|openbox|cog)
      [ -r "$proc/smaps_rollup" ] || continue
      pss=$(awk '$1=="Pss:" {print $2; exit}' "$proc/smaps_rollup" 2>/dev/null || :)
      [ -n "$pss" ] || continue
      printf 'PROCESS_PSS pid=%s comm=%s kib=%s\n' "${proc##*/}" "$comm" "$pss"
      ;;
  esac
done
echo 'PUPPY50_RAM_PROBE_END'
