#!/bin/sh
# Puppy50 Web v44 - official Alpine 3.24 minimal browser-only package closure.
# Never includes Puppy Classic packages or claims full WebGL/browser functionality.
set -eu
ROOT=/out/rootfs
mkdir -p "$ROOT/etc/apk/keys" /out/reports
cp /etc/apk/keys/* "$ROOT/etc/apk/keys/"
printf '%s\n' \
  'https://dl-cdn.alpinelinux.org/alpine/v3.24/main' \
  'https://dl-cdn.alpinelinux.org/alpine/v3.24/community' > "$ROOT/etc/apk/repositories"
# The installed package dependency closure is real, not an invented size.
# Keep Firefox's normal sandbox, network libraries and media codecs.
apk --root "$ROOT" --arch x86_64 --initdb --no-cache \
  add alpine-base openrc \
      firefox-esr xorg-server xinit xf86-input-libinput \
      mesa-dri-gallium mesa-gl mesa-egl \
      dbus dbus-x11 eudev \
      dhcpcd wpa_supplicant iw iproute2 ca-certificates curl \
      font-dejavu alsa-lib \
      linux-lts linux-firmware-intel \
  > /out/reports/apk-install.log 2>&1 || {
    tail -60 /out/reports/apk-install.log
    exit 3
  }
echo 'PUPPY50_WEB_V44_APK_INSTALL=SUCCESS'
# Inventory exact installed package names and versions.
apk --root "$ROOT" info -v > /out/reports/installed-packages.txt
apk --root "$ROOT" info > /out/reports/package-names.txt
for folder in usr/lib usr/share usr/bin usr/lib/firefox etc lib boot; do
 [ -d "$ROOT/$folder" ] && du -sb "$ROOT/$folder" || true
done > /out/reports/major-directory-sizes.txt
du -sb "$ROOT" > /out/reports/uncompressed-root-size.txt
find "$ROOT" -xdev -type f | wc -l > /out/reports/number-of-regular-files.txt
# Exercise the exact binaries available rather than assuming presence.
test -x "$ROOT/usr/bin/firefox-esr" || test -x "$ROOT/usr/lib/firefox/firefox"
test -x "$ROOT/usr/bin/Xorg" || test -x "$ROOT/usr/libexec/Xorg"
test -x "$ROOT/sbin/init"
echo 'PUPPY50_WEB_V44_BROWSER_XORG_INIT_PRESENT=PASS'
