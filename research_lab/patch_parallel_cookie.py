#!/usr/bin/env python3
"""Experimental initrd change: overlap fresh X11-cookie creation with DRM setup.

The original mcookie executable and Xauth authentication remain in use. A
private per-boot root-owned directory transfers the fresh cookie to the
launcher; failures abort rather than generate an insecure replacement. This
patch is for disposable QEMU research images only, not physical deployment.
"""
import argparse
from pathlib import Path


DRM_ANCHOR = "# P50_V125_DRM_PREREQ"
COOKIE = 'p50_cookie="$(mcookie)"'
LAUNCH = 'chroot "$p50_root" /usr/local/sbin/p50-v123-start-x >/dev/ttyS0 2>&1 &'

START = r'''# P50_PARALLEL_SECURE_XAUTH_COOKIE: fresh per boot, never log the secret.
p50_cookie_guest="/run/p50-cookie.$$"
p50_cookie_dir="$p50_root$p50_cookie_guest"
mkdir -m 0700 "$p50_cookie_dir" || panic "cookie: cannot create private directory"
printf 'P50_TRACE_COOKIE_BG_START %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
chroot "$p50_root" /bin/sh -c '
    p50_cookie_guest="$1"
    umask 077
    if /usr/bin/mcookie > "$p50_cookie_guest/pending"; then
        printf "P50_TRACE_COOKIE_BG_GENERATED %s\n" "$(cat /proc/uptime)" >/dev/ttyS0
        if mv "$p50_cookie_guest/pending" "$p50_cookie_guest/ready"; then
            printf "P50_TRACE_COOKIE_BG_READY %s\n" "$(cat /proc/uptime)" >/dev/ttyS0
            exit 0
        fi
    fi
    rm -f "$p50_cookie_guest/pending"
    : > "$p50_cookie_guest/failed"
    printf "P50_TRACE_COOKIE_BG_FAILED %s\n" "$(cat /proc/uptime)" >/dev/ttyS0
    exit 1
' p50-cookie "$p50_cookie_guest" &
'''
WAIT = r'''[ -n "${P50_EARLY_COOKIE_DIR:-}" ] || exit 22
p50_cookie_attempt=0
while [ ! -f "$P50_EARLY_COOKIE_DIR/ready" ]; do
    [ ! -f "$P50_EARLY_COOKIE_DIR/failed" ] || { printf 'P50_TRACE_COOKIE_WAIT_FAILED\n' >/dev/ttyS0; exit 23; }
    [ "$p50_cookie_attempt" -lt 300 ] || { printf 'P50_TRACE_COOKIE_WAIT_TIMEOUT\n' >/dev/ttyS0; exit 24; }
    sleep .05
    p50_cookie_attempt=$((p50_cookie_attempt+1))
done
p50_cookie="$(cat "$P50_EARLY_COOKIE_DIR/ready")" || exit 25
case "$p50_cookie" in *[!0123456789abcdefABCDEF]*|'') exit 26 ;; esac
[ "${#p50_cookie}" -eq 32 ] || exit 27
rm -f "$P50_EARLY_COOKIE_DIR/ready" || exit 28
rmdir "$P50_EARLY_COOKIE_DIR" || exit 29'''


def patch_text(src):
    if "P50_PARALLEL_SECURE_XAUTH_COOKIE" in src or "P50_V125_DRM_PREREQ" not in src:
        raise ValueError("unexpected or already modified initrd hook")
    if 'xauth -f /home/user/.Xauthority add :0 . "$p50_cookie"' not in src:
        raise ValueError("authenticated X11 launcher missing")
    for needle in (DRM_ANCHOR, COOKIE, LAUNCH):
        if src.count(needle) != 1:
            raise ValueError("unknown or ambiguous cookie experiment anchor")
    src = src.replace(DRM_ANCHOR, START + DRM_ANCHOR, 1)
    src = src.replace(COOKIE, WAIT, 1)
    src = src.replace(LAUNCH,
        'P50_EARLY_COOKIE_DIR="$p50_cookie_guest" ' + LAUNCH, 1)
    return src


def patch(root):
    root = Path(root).resolve(strict=True)
    if root == Path("/") or not root.is_dir():
        raise ValueError("refuse host root")
    path = root / "usr/lib/live/boot/9990-main.sh"
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError("expected an extracted initrd boot script")
    path.write_text(patch_text(path.read_text()))
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("extracted_root", type=Path)
    print(patch(parser.parse_args().extracted_root))
