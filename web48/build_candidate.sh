#!/bin/sh
# Build *comparison images*, not production OS images.
# Run ONLY inside a disposable alpine:3.24 container with /out mounted.
# Every candidate uses an identical base and includes an actual package dependency closure.
set -eu
[ "$#" -eq 2 ] || { echo "usage: build_candidate.sh firefox|epiphany /out" >&2; exit 2; }
KIND=$1
OUT=$2
case "$KIND" in
  firefox|epiphany) ;;
  *) echo "unknown candidate: $KIND" >&2; exit 2 ;;
esac
ROOT="$OUT/roots/$KIND"
REPORT="$OUT/reports/$KIND"
mkdir -p "$ROOT/etc/apk/keys" "$REPORT"
cp /etc/apk/keys/* "$ROOT/etc/apk/keys/"
printf '%s\n' 'https://dl-cdn.alpinelinux.org/alpine/v3.24/main' \
 'https://dl-cdn.alpinelinux.org/alpine/v3.24/community' > "$ROOT/etc/apk/repositories"

# Actual common dependencies, held identical for two comparative closures.
# Firmware and modules are included here; source pruning later uses identical
# hardware profile, and all browser-related binaries remain untouched.
COMMON="alpine-base openrc dbus eudev dhcpcd wpa_supplicant iw iproute2 ca-certificates font-dejavu alsa-lib linux-lts linux-firmware-intel mesa-dri-gallium mesa-gl mesa-egl"
case "$KIND" in
 firefox)
  BROWSER="firefox-esr xorg-server xinit xf86-input-libinput dbus-x11 openbox xrandr xf86-video-vesa xf86-video-fbdev"
  ;;
 epiphany)
  # Real GNOME Web browser dependency closure on the same Alpine/Xorg stack.
  # Epiphany and Firefox support different standards and have distinct UX.
  BROWSER="epiphany xorg-server xinit xf86-input-libinput dbus-x11 openbox xrandr xf86-video-vesa xf86-video-fbdev"
  ;;
esac

if ! apk --root "$ROOT" --arch x86_64 --initdb --no-cache add $COMMON $BROWSER > "$REPORT/apk-install.log" 2>&1; then
  # The candidate cannot be measured as an installed complete runtime.
  # Preserve installation failure, but NEVER present any partial tree as a pass.
  echo "UNAVAILABLE_OR_INSTALL_FAILED" > "$REPORT/status"
  tail -35 "$REPORT/apk-install.log"
  exit 10
fi
echo "COMPLETE_PACKAGE_CLOSURE_ONLY" > "$REPORT/status"
apk --root "$ROOT" info -v > "$REPORT/installed-package-versions.txt"
apk --root "$ROOT" info > "$REPORT/installed-package-names.txt"
apk --root "$ROOT" info -s > "$REPORT/installed-package-size-info.txt" 2>/dev/null || :
apk --version > "$REPORT/apk-version.txt"
cat /etc/alpine-release > "$REPORT/alpine-version.txt"
test -s "$ROOT/boot/vmlinuz-lts"
if [ "$KIND" = firefox ]; then
  test -x "$ROOT/usr/bin/firefox-esr" || test -x "$ROOT/usr/lib/firefox/firefox"
else
  test -x "$ROOT/usr/bin/epiphany" || exit 11
fi
echo "PUPPY50_V48_COMPLETE_APK_CLOSURE candidate=$KIND"
