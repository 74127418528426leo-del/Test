#!/usr/bin/env bash
# Offline live ISO VM, no physical disk or network.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISO="$DIR/Puppy50_Web_QEMU_Preview_v62.iso"
command -v qemu-system-x86_64 >/dev/null || { echo "Install qemu-system-x86 on Linux." >&2; exit 10; }
test -s "$ISO" || { echo "ISO not found: $ISO" >&2; exit 11; }
test -s "$DIR/SHA256SUMS" || { echo "SHA256SUMS missing" >&2; exit 12; }
(cd "$DIR"; sha256sum -c SHA256SUMS) || { echo "ISO checksum mismatch" >&2; exit 13; }
RAM="${PUPPY50_RAM_MIB:-1024}"
case "$RAM" in
  1024|2048|4096) ;;
  384) echo "384 MiB boots but does not render Firefox yet." >&2 ;;
  *) echo "RAM must be 1024/2048/4096 or experimental 384 MiB." >&2; exit 14 ;;
esac
MODE=(-machine pc,accel=tcg -cpu qemu64)
if [[ -r /dev/kvm && -w /dev/kvm ]]; then
  MODE=(-machine pc,accel=kvm -cpu host)
else
  echo "KVM unavailable: slow software emulation used." >&2
fi
echo "Experimental QEMU standard-VGA browser ISO: offline, nonpersistent, and not hardware-ready."
exec qemu-system-x86_64 "${MODE[@]}" -m "$RAM" -smp 2 \
  -drive "file=$ISO,if=ide,media=cdrom,readonly=on" \
  -boot order=d -vga std -nic none -no-reboot
