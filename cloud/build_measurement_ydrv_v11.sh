#!/bin/sh
# Additive measurement-only Puppy layer for QEMU experiments.
set -eu
[ "$#" -eq 1 ] || { echo "Usage: $0 ydrv_dpupbw64_10.0.12.sfs" >&2; exit 2; }
command -v mksquashfs >/dev/null || { echo "Install squashfs-tools" >&2; exit 1; }
[ ! -e "$1" ] || { echo "Refusing to overwrite output" >&2; exit 1; }
dir=$(mktemp -d)
trap 'rm -rf "$dir"' EXIT HUP INT TERM
mkdir -p "$dir/root/Startup"
cat > "$dir/root/Startup/puppy50_probe" <<'GUEST'
#!/bin/sh
[ -w /dev/ttyS0 ] || exit 0
(
  sleep 3
  for n in 1 2 3 4 5; do
    {
      echo "PUPPY50_GUEST_BEGIN sample=$n"
      cat /proc/uptime
      grep -E '^(MemTotal|MemFree|MemAvailable|Cached|Shmem|Slab|KernelStack|PageTables|SwapTotal|SwapFree):' /proc/meminfo
      cat /proc/swaps
      echo "PUPPY50_GUEST_END sample=$n"
    } > /dev/ttyS0 2>&1
    sleep 15
  done
) &
GUEST
chmod 755 "$dir/root/Startup/puppy50_probe"
mksquashfs "$dir" "$1" -noappend -no-progress >/dev/null
