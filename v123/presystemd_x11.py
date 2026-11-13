#!/usr/bin/env python3
"""Isolated QEMU-only proof-of-concept for launching an authenticated X11
session BEFORE Linux PID1/systemd. Not a deployable image.

This deliberately preserves browser sandbox/nonroot operation and DOES NOT
disable X11 authentication or TCP restrictions. If the early session cannot
survive switch-root, the browser frame proof must fail. No speed claims until
an actual screenshot plus verified RAM and authenticated post-eject HTTP200.
"""
from pathlib import Path
import argparse

MARKER="\n\tFstab\n\tNetbase\n"
HOOK=r'''
    # P50_V123_BEFORE_PID1: isolated QEMU-only research, unsafe for physical release.
    if [ -z "@{TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
        p50_root="@{rootmnt}"
        p50_dm="$p50_root/etc/systemd/system/display-manager.service"
        p50_start="$p50_root/usr/local/sbin/p50-v123-start-x"
        grep -q '^user:' "$p50_root/etc/passwd" || panic "v123: nonroot account missing"
        [ -L "$p50_dm" ] && [ "$(readlink "$p50_dm")" = "/lib/systemd/system/lightdm.service" ] || panic "v123: unknown display-manager alias"
        for p50_tool in /usr/bin/xauth /usr/bin/mcookie /usr/bin/setpriv /usr/bin/dbus-run-session /usr/bin/openbox-session /usr/lib/xorg/Xorg; do
            [ -x "$p50_root$p50_tool" ] || panic "v123: missing security-critical X11 prerequisite $p50_tool"
        done
        [ ! -e "$p50_start" ] && [ ! -L "$p50_start" ] || panic "v123: unexpected launcher"
        rm "$p50_dm" || panic "v123: cannot remove original LightDM alias"
        ln -s /dev/null "$p50_dm" || panic "v123: cannot mask late duplicate display"
        for p50_mnt in dev proc sys run; do
            if ! mountpoint -q "$p50_root/$p50_mnt"; then
                mount --bind "/$p50_mnt" "$p50_root/$p50_mnt" || panic "v123: cannot prepare $p50_mnt bind for chroot"
            fi
        done
        cat > "$p50_start" <<'P50_V123_START_X'
#!/bin/sh
set -eu
umask 077
p50_cookie="$(mcookie)"
mkdir -p /home/user /tmp/.X11-unix /run/user/1000
chown user:user /run/user/1000
chmod 0700 /run/user/1000
xauth -f /home/user/.Xauthority add :0 . "$p50_cookie"
chown user:user /home/user/.Xauthority
chmod 0600 /home/user/.Xauthority
printf 'P50_V123_XORG_START %s\n' "$(cat /proc/uptime)" > /dev/ttyS0
/usr/lib/xorg/Xorg :0 -auth /home/user/.Xauthority -nolisten tcp -noreset vt1 \
    >/run/p50-v123-xorg.log 2>&1 &
p50_xpid=$!
p50_i=0
while [ "$p50_i" -lt 35 ]; do
    [ -S /tmp/.X11-unix/X0 ] && break
    kill -0 "$p50_xpid" 2>/dev/null || { cat /run/p50-v123-xorg.log >/dev/ttyS0; exit 20; }
    sleep 0.10
    p50_i=$((p50_i+1))
done
[ -S /tmp/.X11-unix/X0 ] || { cat /run/p50-v123-xorg.log >/dev/ttyS0; exit 21; }
printf 'P50_V123_OPENBOX_START %s\n' "$(cat /proc/uptime)" > /dev/ttyS0
setpriv --reuid=user --regid=user --init-groups \
    env HOME=/home/user USER=user LOGNAME=user DISPLAY=:0 \
    XAUTHORITY=/home/user/.Xauthority XDG_RUNTIME_DIR=/run/user/1000 \
    /usr/bin/dbus-run-session -- /usr/bin/openbox-session \
    >/run/p50-v123-openbox.log 2>&1 &
exit 0
P50_V123_START_X
        chmod 0700 "$p50_start" || panic "v123: cannot secure launcher"
        printf 'P50_V123_INITRD_LAUNCH_REQUEST %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
        chroot "$p50_root" /usr/local/sbin/p50-v123-start-x >/dev/ttyS0 2>&1 &
    fi
'''.replace('\n    ','\n\t').replace('@{',chr(36)+'{')


def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():
        raise ValueError('Refuse host mutation; only extracted initrd allowed')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if p.is_symlink() or not p.is_file():
        raise ValueError('Expected staged live-boot shell script')
    data=p.read_text()
    if data.count(MARKER)!=1 or 'P50_V123_BEFORE_PID1' in data:
        raise ValueError('Unknown or already-patched initrd layout')
    if 'P50_V118_EARLY_USER' not in data or 'P50_V119_LIVECONFIG_DISABLED' not in data:
        raise ValueError('Require nonroot user and test-only late config isolation')
    p.write_text(data.replace(MARKER,HOOK+MARKER,1))
    return p

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
