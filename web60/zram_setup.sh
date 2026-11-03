#!/bin/sh
# Experimental 384MiB RAM-only compressed swap. NEVER uses a physical disk.
# Fail closed so uninitialized swap is not falsely called a zram test.
set -u
log() { echo "$*" >/dev/ttyS0 2>/dev/null || true; }
fail() { log "PUPPY50_V60_ZRAM_FAILED=$1"; return 60; }
if [ ! -e /sys/block/zram0/disksize ]; then fail "no_zram_device" || exit 60; fi
if [ ! -b /dev/zram0 ]; then
    mdev -s >/dev/ttyS0 2>&1 || true
fi
[ -b /dev/zram0 ] || { fail "missing_block_node"; exit 60; }
if [ "$(cat /sys/block/zram0/disksize 2>/dev/null)" != "0" ]; then
    fail "device_already_initialized"; exit 60
fi
# The virtual 256MiB swap size is NOT more physical RAM.
# The compressed allocator has a separate 128MiB physical memory ceiling.
echo 128M > /sys/block/zram0/mem_limit || { fail "memory_limit"; exit 60; }
echo 256M > /sys/block/zram0/disksize || { fail "disksize"; exit 60; }
if command -v mkswap >/dev/null 2>&1; then
    mkswap /dev/zram0 >/dev/ttyS0 2>&1 || { fail "mkswap"; exit 60; }
elif busybox --list | grep -qx mkswap; then
    busybox mkswap /dev/zram0 >/dev/ttyS0 2>&1 || { fail "busybox_mkswap"; exit 60; }
else
    fail "no_mkswap"; exit 60
fi
if command -v swapon >/dev/null 2>&1; then
    swapon -p 100 /dev/zram0 >/dev/ttyS0 2>&1 || { fail "swapon"; exit 60; }
elif busybox --list | grep -qx swapon; then
    busybox swapon /dev/zram0 >/dev/ttyS0 2>&1 || { fail "busybox_swapon"; exit 60; }
else
    fail "no_swapon"; exit 60
fi
grep -q '^/dev/zram0 ' /proc/swaps || { fail "not_listed_in_swap"; exit 60; }
echo 100 > /proc/sys/vm/swappiness || { fail "swappiness"; exit 60; }
echo 0 > /proc/sys/vm/page-cluster || true
log "PUPPY50_V60_ZRAM_ACTIVE=PASS"
log "PUPPY50_V60_ZRAM_PHYSICAL_LIMIT=128M"
log "PUPPY50_V60_ZRAM_VIRTUAL_SWAP=256M"
cat /proc/swaps >/dev/ttyS0 2>/dev/null || true
exit 0
