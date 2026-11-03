#!/bin/sh
# Bounded serial telemetry, not a benchmark; avoids writing to disk.
set -u
i=0
while [ "$i" -lt 48 ]; do
  {
    echo "PUPPY50_V60_ZRAM_SAMPLE_BEGIN n=$i"
    grep -E '^(MemTotal|MemAvailable|Shmem|SwapTotal|SwapFree):' /proc/meminfo || :
    if [ -r /sys/block/zram0/mm_stat ]; then
      printf 'PUPPY50_V60_ZRAM_MM_STAT '
      cat /sys/block/zram0/mm_stat
    fi
    if [ -r /sys/block/zram0/io_stat ]; then
      printf 'PUPPY50_V60_ZRAM_IO_STAT '
      cat /sys/block/zram0/io_stat
    fi
    echo "PUPPY50_V60_ZRAM_SAMPLE_END n=$i"
  } > /dev/ttyS0 2>/dev/null || true
  i=$((i+1))
  sleep 4
done
