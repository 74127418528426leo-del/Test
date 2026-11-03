#!/usr/bin/env bash
# Puppy50 v86: visually verified 1536MiB v70 with supervised host-only HTTPS bridge using QEMU user NAT and optional
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
RAM="${PUPPY50_RAM_MIB:-1536}"
case "$RAM" in
  1024|1280|1536|1792|2048|4096) ;;
  384) echo "WARNING: 384 MiB Linux boots but Firefox rendering does not pass." >&2 ;;
  *) echo "Guest RAM must be 1024/1280/1536/1792/2048/4096 or experimental 384." >&2;exit 15 ;;
esac
# v86: do not silently allocate more memory than this Linux host can spare.
# The public v70 ISO successfully showed Wikipedia at 1536 MiB in real KVM
# (run 41695446129). 1024 MiB browsers have shown severe memory pressure.
if [[ "$RAM" == 1024 || "$RAM" == 384 ]]; then
  echo "WARNING: this RAM amount is below the v70 1536 MiB visually tested browser configuration." >&2
fi
HOST_AVAILABLE_MIB="$(awk '/^MemAvailable:/ {printf "%d", $2/1024; exit}' /proc/meminfo)"
HOST_TOTAL_MIB="$(awk '/^MemTotal:/ {printf "%d", $2/1024; exit}' /proc/meminfo)"
if [[ -z "$HOST_AVAILABLE_MIB" || -z "$HOST_TOTAL_MIB" ]]; then
  echo "Cannot read available host RAM. Refusing unsafe VM memory allocation." >&2
  exit 24
fi
REQUIRED_AVAILABLE_MIB=$((RAM+768))
if (( HOST_AVAILABLE_MIB < REQUIRED_AVAILABLE_MIB )); then
  echo "Puppy50 memory safety: guest requests ${RAM} MiB but only ${HOST_AVAILABLE_MIB} MiB is currently available on the host." >&2
  echo "Reserve at least 768 MiB for Xubuntu and host apps. Close programs, or choose a smaller guest using PUPPY50_RAM_MIB." >&2
  echo "No VM started, no network changed, no memory allocated." >&2
  exit 25
fi
if (( HOST_TOTAL_MIB < RAM+512 )); then
  echo "Insufficient total host RAM for requested guest size." >&2
  exit 26
fi
echo "Puppy50 host memory: total ${HOST_TOTAL_MIB} MiB, available ${HOST_AVAILABLE_MIB} MiB."
echo "Guest: ${RAM} MiB; host spare estimate after guest allocation: $((HOST_AVAILABLE_MIB-RAM)) MiB."
echo "Network connectivity is supplied by your authorized host Wi-Fi/Ethernet/hotspot."

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
  test -s "$HERE/host_https_bridge_supervisor_v80.py" || {
    echo "Missing Puppy50 v80 recovery supervisor." >&2; exit 21;
  }
  # Keep the host-only TLS pass-through available if its own process crashes.
  # Fail closed if an unknown program occupies the static port.
  python3 -u "$HERE/host_https_bridge_supervisor_v80.py" \
    --bridge "$HERE/host_https_bridge.py" --port 3128 &
  BRIDGE_PID=$!
  sleep 0.5
  kill -0 "$BRIDGE_PID" 2>/dev/null || {
    echo "Failed to start host-only HTTPS bridge." >&2;exit 20;
  }
  echo "Networking: e1000 + QEMU NAT over the host's Wi-Fi/Ethernet/hotspot."
  echo "Fallback: supervised host-only 127.0.0.1:3128 TCP CONNECT (public TLS passthrough)."
else
  echo "Networking disabled for this VM session."
fi

echo "Experimental v70 browser VM; 1536MiB Wikipedia rendering verified in v84. Browser security updates are UNVERIFIED and outdated."
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
