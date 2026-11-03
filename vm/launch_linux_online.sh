#!/usr/bin/env bash
# Puppy50 Web v64 ONLINE QEMU launcher.
# Trust-but-verify checksum; virtual Ethernet NAT uses host's current Internet.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISO="$DIR/Puppy50_Web_v64_Online_QEMU.iso"
command -v qemu-system-x86_64 >/dev/null || {
  echo "Please install QEMU: sudo apt-get install qemu-system-x86" >&2
  exit 10
}
test -s "$ISO" || { echo "ISO file not found: $ISO" >&2; exit 11; }
test -s "$DIR/SHA256SUMS" || { echo "SHA256SUMS missing" >&2; exit 12; }
(cd "$DIR" && sha256sum -c SHA256SUMS) || { echo "ISO SHA256 did not match!" >&2; exit 13; }
RAM="${PUPPY50_RAM_MIB:-1024}"
case "$RAM" in
  1024|2048|4096) ;;
  384) echo "WARNING: At 384MiB Linux boots, but Firefox browsing is not functional." >&2 ;;
  *) echo "Unsupported RAM setting; use 1024, 2048, 4096 or experimental 384." >&2; exit 14 ;;
esac
NET="${PUPPY50_NETWORK:-nat}"
case "$NET" in
  nat)
    NIC=(-nic user,model=e1000,ipv6=off)
    echo "Networking: outbound QEMU NAT via the HOST's Internet connection."
    ;;
  off)
    NIC=(-nic none)
    echo "Networking: intentionally OFF."
    ;;
  *) echo "PUPPY50_NETWORK must be nat or off, got: $NET" >&2;exit 15 ;;
esac
MODE=(-machine pc,accel=tcg -cpu qemu64)
if [[ -r /dev/kvm && -w /dev/kvm ]]; then
  MODE=(-machine pc,accel=kvm -cpu host)
else
  echo "KVM unavailable: software emulation may be very slow." >&2
fi
echo "QEMU virtual Ethernet shares the host's Wi-Fi, Ethernet, or hotspot via NAT."
echo "No physical Wi-Fi adapter/SSID selection exists inside this QEMU guest."
echo "No attached writable hard disk; browsing data is ephemeral."
exec qemu-system-x86_64 "${MODE[@]}" -m "$RAM" -smp 2 \
  -drive "file=$ISO,if=ide,media=cdrom,readonly=on" \
  -boot order=d -vga std "${NIC[@]}" -no-reboot
