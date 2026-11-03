#!/bin/sh
# Puppy50 v67: guest e1000 DHCP + DNS + end-to-end CA-verified HTTPS.
# Try direct QEMU NAT first; when blocked, use a separately authorized
# host-only TCP CONNECT bridge at 10.0.2.2:3128.
# Never disable certificate verification, browser sandbox or network isolation.
set -u
log() { echo "$*" >/dev/ttyS0 2>/dev/null || true; }
log "PUPPY50_V67_NETWORK_PROBE_BEGIN"
ip link set dev eth0 up 2>/dev/null || true
if ! ip -o -4 addr show dev eth0 | grep -q 'inet '; then
  dhcpcd -4 -t 18 eth0 >/tmp/v67-dhcp.log 2>&1 || true
fi
if ! ip -o -4 addr show dev eth0 | grep -q 'inet '; then
  log "PUPPY50_V67_DHCP=FAIL"
  exit 21
fi
log "PUPPY50_V67_DHCP=PASS"
if ! ip -4 route show default | grep -q default; then
  log "PUPPY50_V67_ROUTE=FAIL"
  exit 22
fi
log "PUPPY50_V67_ROUTE=PASS"
# QEMU user-mode NAT fixes DNS at 10.0.2.3, regardless of stale
# Docker staging resolv.conf baked into the filesystem.
printf 'nameserver 10.0.2.3\noptions timeout:3 attempts:2\n' > /etc/resolv.conf
if nslookup example.com 10.0.2.3 >/tmp/v67-dns.log 2>&1; then
  log "PUPPY50_V67_DNS=PASS"
else
  log "PUPPY50_V67_DNS=FAIL"
  exit 23
fi

# A successful curl with normal CA trust is distinct from a DNS/TCP connect.
# No insecure flags or host CA substitution are permitted.
URL=https://example.com/
echo direct > /run/puppy50-network-mode
if curl --noproxy '*' --fail --silent --show-error --location \
  --proto '=https' --connect-timeout 6 --max-time 12 \
  --output /tmp/v67-example.html "$URL" &&
  [ -s /tmp/v67-example.html ]; then
  log "PUPPY50_V67_EXTERNAL_TLS_DIRECT=PASS"
  log "PUPPY50_V67_EXTERNAL_TLS_CA_VERIFIED=PASS"
  log "PUPPY50_V64_DNS_TLS_HTTPS_EXTERNAL=PASS"
  log "PUPPY50_V64_NETWORK_READY=PASS"
  exit 0
fi

log "PUPPY50_V67_EXTERNAL_TLS_DIRECT=FAIL"
# Host-only bridge keeps real external TLS end-to-end and simply forwards
# the HTTPS CONNECT socket; the public certificate is checked IN THE GUEST.
if curl --proxy http://10.0.2.2:3128 --noproxy '' \
  --fail --silent --show-error --location --proto '=https' \
  --connect-timeout 10 --max-time 26 \
  --output /tmp/v67-example.html "$URL" &&
  [ -s /tmp/v67-example.html ]; then
  echo proxy > /run/puppy50-network-mode
  log "PUPPY50_V67_EXTERNAL_TLS_VIA_HOST_CONNECT=PASS"
  log "PUPPY50_V67_EXTERNAL_TLS_CA_VERIFIED=PASS"
  log "PUPPY50_V64_DNS_TLS_HTTPS_EXTERNAL=PASS"
  log "PUPPY50_V64_NETWORK_READY=PASS"

  # Firefox Enterprise Proxy policy is applied only when the independently
  # CA-verified guest HTTPS CONNECT request passes. No certificate settings
  # or browser sandbox settings are modified.
  mkdir -p /usr/lib/firefox-esr/distribution
  cat > /usr/lib/firefox-esr/distribution/policies.json <<'EOF'
{
  "policies": {
    "Proxy": {
      "Mode": "manual",
      "SSLProxy": "10.0.2.2:3128",
      "Locked": false,
      "Passthrough": "localhost,127.0.0.1"
    }
  }
}
EOF
  chmod 644 /usr/lib/firefox-esr/distribution/policies.json
  log "PUPPY50_V67_FIREFOX_HTTPS_PROXY_POLICY=APPLIED"
  exit 0
fi
log "PUPPY50_V67_EXTERNAL_TLS_VIA_HOST_CONNECT=FAIL"
log "PUPPY50_V67_EXTERNAL_TLS_CA_VERIFIED=FAIL"
log "PUPPY50_V64_DNS_TLS_HTTPS_EXTERNAL=FAIL"
log "PUPPY50_V64_NETWORK_READY=FAIL"
exit 25
