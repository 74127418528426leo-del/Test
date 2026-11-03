#!/usr/bin/env bash
# Reproducible *experimental* Debian 13 RAM-only browser/physical-network ISO.
# This is a separate managed prototype, not an update or installer for v70.
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$PWD/output_v85}"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
mkdir -p "$OUT/build"
cd "$OUT/build"
lb config \
  --mode debian \
  --distribution trixie \
  --binary-images iso-hybrid \
  --debian-installer none \
  --archive-areas "main contrib non-free-firmware" \
  --apt-secure true \
  --apt-recommends false \
  --apt-indices false \
  --firmware-chroot true \
  --bootappend-live "boot=live components toram quiet locales=en_US.UTF-8" \
  --mirror-bootstrap https://deb.debian.org/debian \
  --mirror-chroot https://deb.debian.org/debian \
  --mirror-binary https://deb.debian.org/debian
cp -a "$SRC/config/." "$OUT/build/config/"
echo "PUPPY50_V85_LIVE_BUILD_CONFIGURED"
sudo lb build
ISO="$(find . -maxdepth 1 -type f -name '*.iso' | head -1)"
if [[ ! -s "$ISO" ]]; then
    echo "PUPPY50_V85_NO_ISO_PRODUCED" >&2;exit 10
fi
cp -v -- "$ISO" "$OUT/Puppy50_v85_Debian_Managed_Browser_WIFI_TEST_ONLY.iso"
(cd "$OUT" && sha256sum Puppy50_v85_Debian_Managed_Browser_WIFI_TEST_ONLY.iso > SHA256SUMS)
echo "PUPPY50_V85_TEST_ONLY_ISO_CREATED"
stat -c "PUPPY50_V85_ISO_BYTES=%s" "$OUT/Puppy50_v85_Debian_Managed_Browser_WIFI_TEST_ONLY.iso"
