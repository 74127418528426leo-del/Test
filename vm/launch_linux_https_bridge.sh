#!/usr/bin/env bash
# Puppy50 v68: reproduce the network-enabled QEMU guest and its optional
# host-only HTTPS CONNECT bridge. No writable disk, no exposed network port.
# The ISO checksum and probe safeguards are required.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISO="$HERE/Puppy50_Web_v67_HTTPS_Bridge_Experimental.iso"
test -s "$ISO" || { echo "Missing ISO: $ISO" >&2;exit 11; }
test -s "$HERE/SHA256SUMS" || { echo "Missing ISO SHA256SUMS" >&2;exit 12; }
(cd "$HERE" && sha256sum -c SHA256SUMS) || {
  echo "ISO SHA256 mismatch. Not running." >&2
  exit 13
}
command -v qemu-system-x86_64 >/dev/null || {
 echo "Install QEMU: sudo apt-get install qemu-system-x86" >&2;exit 14;
}
RAM="${PUPPY50_RAM_MIB:-1024}"
case "$RAM" in
  1024|2048|4096) ;;
  384) echo "WARNING: 384 MiB Linux boots but Firefox rendering does not pass." >&2 ;;
  *) echo "Guest RAM must be 1024/2048/4096 or experimental 384." >&2;exit 15 ;;
esac
NET="${PUPPY50_NETWORK:-nat}"
case "$NET" in
  nat) NIC=(-nic user,model=e1000,ipv6=off) ;;
  off) NIC=(-nic none) ;;
  *) echo "PUPPY50_NETWORK must be nat or off." >&2;exit 16 ;;
esac
QEMU_MODE=(-machine pc,accel=tcg -cpu qemu64)
if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
  QEMU_MODE=(-machine pc,accel=kvm -cpu host)
else
  echo "No KVM access; QEMU software emulation may be slow." >&2
fi

BRIDGE_PID=""
cleanup() {
  if [[ -n "$BRIDGE_PID" ]]; then
    kill "$BRIDGE_PID" 2>/dev/null || true
    wait "$BRIDGE_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if [[ "$NET" == nat ]]; then
  command -v python3 >/dev/null || {
    echo "Python3 is required for the optional, secure outbound HTTPS bridge." >&2;exit 17;
  }
  test -s "$HERE/host_https_bridge.py" || {
    echo "The HTTPS bridge source is missing; use the complete VM bundle." >&2;exit 18;
  }
  # Safety: if a different application owns localhost:3128, refuse to
  # silently direct the guest browser to that unknown proxy.
  if python3 - <<'PY'
import socket
s=socket.socket()
try:
    s.bind(('127.0.0.1',3128))
except OSError:
    raise SystemExit(0)  # occupied
else:
    raise SystemExit(1)  # free
finally:
    s.close()
PY
  then
    echo "Host TCP port 3128 is already in use; refusing unknown proxy." >&2
    exit 19
  fi
  python3 "$HERE/host_https_bridge.py" --port 3128 &
  BRIDGE_PID=$!
  sleep 0.5
  kill -0 "$BRIDGE_PID" 2>/dev/null || {
    echo "Failed to start host-only HTTPS bridge." >&2;exit 20;
  }
  echo "Networking: e1000 + QEMU NAT over the host's Wi-Fi/Ethernet/hotspot."
  echo "Fallback: host-only 127.0.0.1:3128 TCP CONNECT (public TLS passthrough)."
else
  echo "Networking disabled for this VM session."
fi

echo "Experimental VM; secure Internet browsing and physical-hardware portability are not certified."
echo "No writable virtual hard disk. Guest browsing state is lost at shutdown."
qemu-system-x86_64 "${QEMU_MODE[@]}" -m "$RAM" -smp 2 \
  -drive "file=$ISO,if=ide,media=cdrom,readonly=on" \
  -boot order=d -vga std "${NIC[@]}" -no-reboot
