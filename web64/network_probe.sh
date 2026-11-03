#!/bin/sh
# QEMU NAT network diagnostic: DHCP, DNS and CA-verified HTTPS.
# Does NOT disable TLS verification or Firefox sandbox. No secrets printed.
# Network failure must never prevent the offline RAM-only browser from opening.
set -u
echo 'PUPPY50_V64_NETWORK_BEGIN'
echo 'PUPPY50_V64_NETWORK_PROFILE=QEMU_E1000_USER_NAT'
if [ ! -d /sys/class/net/eth0 ]; then
  echo 'PUPPY50_V64_NIC_MISSING=eth0'
  echo 'PUPPY50_V64_NETWORK_READY=FAIL'
  exit 20
fi
ip link set dev eth0 up >/dev/null 2>&1 || true
i=0
while [ "$i" -lt 10 ]; do
  if ip -o -4 addr show dev eth0 | grep -q 'inet '; then break; fi
  i=$((i+1))
  sleep 1
done
if ! ip -o -4 addr show dev eth0 | grep -q 'inet '; then
  echo 'PUPPY50_V64_DHCP_START_ATTEMPT'
  dhcpcd -4 -t 20 eth0 >/tmp/puppy50-dhcp.log 2>&1 || true
  i=0
  while [ "$i" -lt 15 ]; do
    if ip -o -4 addr show dev eth0 | grep -q 'inet '; then break; fi
    i=$((i+1))
    sleep 1
  done
fi
if ip -o -4 addr show dev eth0 | grep -q 'inet '; then
  echo 'PUPPY50_V64_DHCP_IPV4=PASS'
else
  echo 'PUPPY50_V64_DHCP_IPV4=FAIL'
  echo 'PUPPY50_V64_NETWORK_READY=FAIL'
  exit 21
fi
if ip -4 route show default | grep -q default; then
  echo 'PUPPY50_V64_DEFAULT_ROUTE=PASS'
else
  echo 'PUPPY50_V64_DEFAULT_ROUTE=FAIL'
  echo 'PUPPY50_V64_NETWORK_READY=FAIL'
  exit 22
fi
if [ ! -s /etc/resolv.conf ]; then
  echo 'PUPPY50_V64_DNS_CONFIG=FAIL'
  echo 'PUPPY50_V64_NETWORK_READY=FAIL'
  exit 23
fi
echo 'PUPPY50_V64_DNS_CONFIG=PRESENT'
echo 'PUPPY50_V64_PREBOOT_RESOLVERS_BEGIN'
grep '^nameserver ' /etc/resolv.conf || true
echo 'PUPPY50_V64_PREBOOT_RESOLVERS_END'
# The VM is explicitly launched with QEMU's DEFAULT 10.0.2.0/24 user
# networking. Its documented DNS forwarder lives at 10.0.2.3. The root
# was staged inside a Docker builder and might inherit a host-specific
# resolver that the isolated VM cannot reach. Use QEMU's actual DNS
# forwarder instead of stale host/Docker DNS server addresses.
printf 'nameserver 10.0.2.3\noptions timeout:3 attempts:2\n' > /etc/resolv.conf || {
  echo 'PUPPY50_V64_QEMU_DNS_OVERRIDE=FAIL'
  exit 26
}
echo 'PUPPY50_V64_QEMU_DNS_OVERRIDE=10.0.2.3'
echo 'PUPPY50_V64_QEMU_DNS_LOOKUP_BEGIN'
if command -v nslookup >/dev/null 2>&1; then
  if nslookup example.com 10.0.2.3 >/tmp/puppy50-dns-probe.log 2>&1; then
    echo 'PUPPY50_V64_QEMU_DNS_LOOKUP=PASS'
  else
    echo 'PUPPY50_V64_QEMU_DNS_LOOKUP=FAIL'
    tail -8 /tmp/puppy50-dns-probe.log || true
  fi
fi
echo 'PUPPY50_V64_QEMU_DNS_LOOKUP_END'
if ! command -v curl >/dev/null 2>&1; then
  echo 'PUPPY50_V64_CURL_MISSING'
  echo 'PUPPY50_V64_NETWORK_READY=FAIL'
  exit 24
fi
# A non-zero curl status includes failed DNS/TCP/CA verification/HTTPS. We
# deliberately NEVER bypass certificate verification or ignore TLS errors.
if curl --fail --silent --show-error --location --proto '=https' \
     --tlsv1.2 --connect-timeout 12 --max-time 35 --retry 1 \
     --output /tmp/puppy50-example-https.html \
     https://example.com/; then
  if [ -s /tmp/puppy50-example-https.html ]; then
    echo 'PUPPY50_V64_DNS_TLS_HTTPS_EXTERNAL=PASS'
    echo 'PUPPY50_V64_NETWORK_READY=PASS'
    exit 0
  fi
fi
echo 'PUPPY50_V64_DNS_TLS_HTTPS_EXTERNAL=FAIL'
echo 'PUPPY50_V64_NETWORK_READY=FAIL'
exit 25
