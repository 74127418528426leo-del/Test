#!/usr/bin/env bash
# Puppy50 v80: normal browser with supervised HTTPS bridge using QEMU user NAT and optional
# host-only HTTPS CONNECT bridge. No writable disk, no exposed network port.
# The ISO checksum and probe safeguards are required.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISO="$HERE/Puppy50_Web_v70_Normal_Browser_Online.iso"
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

SUPERVISOR_PID=""
STATUS_DIR=""
cleanup() {
  if [[ -n "$SUPERVISOR_PID" ]]; then
    kill "$SUPERVISOR_PID" 2>/dev/null || true
    wait "$SUPERVISOR_PID" 2>/dev/null || true
  fi
  if [[ -n "$STATUS_DIR" && -d "$STATUS_DIR" ]]; then
    rm -rf -- "$STATUS_DIR"
  fi
}
trap cleanup EXIT INT TERM

if [[ "$NET" == nat ]]; then
  command -v python3 >/dev/null || {
    echo "Python3 is required for the host-only HTTPS bridge." >&2;exit 17;
  }
  test -s "$HERE/host_https_bridge.py" || {
    echo "The HTTPS bridge source is missing; use the complete VM bundle." >&2;exit 18;
  }
  test -s "$HERE/bridge_supervisor.py" || {
    echo "The v80 bridge watchdog is missing; use the complete VM bundle." >&2;exit 19;
  }
  STATUS_DIR="$(mktemp -d -t puppy50-v80-bridge.XXXXXXXX)"
  chmod 700 "$STATUS_DIR"
  python3 -u "$HERE/bridge_supervisor.py" \
    --bridge-script "$HERE/host_https_bridge.py" \
    --status "$STATUS_DIR/status.json" \
    --log "$STATUS_DIR/bridge.log" --port 3128 &
  SUPERVISOR_PID=$!
  for _ in {1..50}; do
    [[ -s "$STATUS_DIR/status.json" ]] && break
    if ! kill -0 "$SUPERVISOR_PID" 2>/dev/null; then
      echo "Bridge supervisor exited; refusing to use an unknown proxy." >&2;exit 20
    fi
    sleep 0.1
  done
  if [[ ! -s "$STATUS_DIR/status.json" ]]; then
    echo "Bridge supervisor failed to start." >&2;exit 21
  fi
  echo "Network: host Wi-Fi, Ethernet or hotspot via QEMU NAT and virtual Ethernet."
  echo "TLS-preserving HTTPS bridge: automatic owned-process restart on failure."
  echo "The guest still verifies certificates. Physical Wi-Fi selection happens on the host."
else
  echo "Networking disabled for this VM session."
fi

echo "Experimental online VM; HTTPS is verified for example.com only. Browser/system security updates remain unverified."
echo "Normal browsing: no automatic website navigation. Open links or enter URLs in Firefox."
if [[ "$NET" == nat ]]; then
  if [[ -s "$HERE/host_network_preflight_v70.py" ]]; then
    python3 "$HERE/host_network_preflight_v70.py" || true
  fi
fi
echo "No writable virtual hard disk. Guest browsing state is lost at shutdown."
qemu-system-x86_64 "${QEMU_MODE[@]}" -m "$RAM" -smp 2 \
  -drive "file=$ISO,if=ide,media=cdrom,readonly=on" \
  -boot order=d -vga std "${NIC[@]}" -no-reboot
