#!/usr/bin/env python3
"""Research-only fast path: launch X11+Openbox directly as a nonroot user.

Apply AFTER v118/precreate_user.py to a disposable extracted Debian Live
initramfs. Removes LightDM and live-config only from this test's staged
boot entry. Full-RAM fallback initrd and the published v117 ISO are untouched.
"""
from pathlib import Path
import argparse

MARKER = "\n\tFstab\n\tNetbase\n"
DIRECT = r'''
    # P50_V120_DIRECT: isolated staged research boot, full-RAM fallback unchanged.
    if [ -z "@{TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
        p50_dm="@{rootmnt}/etc/systemd/system/display-manager.service"
        p50_lightdm="@{rootmnt}/etc/systemd/system/lightdm.service"
        [ -L "$p50_dm" ] && [ "$(readlink "$p50_dm")" = "/lib/systemd/system/lightdm.service" ] || panic "v120: unexpected display manager"
        [ ! -e "$p50_lightdm" ] && [ ! -L "$p50_lightdm" ] || panic "v120: unexpected LightDM override"
        grep -q '^user:' "@{rootmnt}/etc/passwd" || panic "v120: missing nonroot user"
        grep -Fqx 'ExecStartPre=' "@{rootmnt}/etc/systemd/system/lightdm.service.d/10-puppy50-live-preflight.conf" || panic "v120: old preflight present"
        [ -x "@{rootmnt}/usr/bin/startx" ] && [ -x "@{rootmnt}/usr/bin/dbus-run-session" ] || panic "v120: missing X11 components"
        [ -x "@{rootmnt}/usr/bin/openbox-session" ] || panic "v120: missing Openbox"
        rm "$p50_dm" || panic "v120: cannot remove original LightDM alias"
        ln -s /dev/null "$p50_lightdm" || panic "v120: cannot mask LightDM"
        cat >"$p50_dm" <<'P50_V120_DIRECT_UNIT'
[Unit]
Description=Puppy50 direct unprivileged X11 cold-start experiment
After=systemd-logind.service systemd-user-sessions.service
Wants=systemd-logind.service
Conflicts=getty@tty1.service
After=getty@tty1.service

[Service]
Type=simple
User=user
PAMName=login
Environment=HOME=/home/user XDG_SESSION_TYPE=x11 XDG_SESSION_CLASS=user XDG_SEAT=seat0
ExecStart=/usr/bin/startx /usr/bin/dbus-run-session /usr/bin/openbox-session -- :0 vt1 -keeptty -nolisten tcp
StandardInput=tty
TTYPath=/dev/tty1
TTYReset=yes
Restart=on-failure
RestartSec=2
P50_V120_DIRECT_UNIT
        printf 'P50_V120_DIRECT_READY %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
    fi
'''.replace('\n    ', '\n\t').replace('@{', chr(36)+'{')


def patch(root: Path) -> Path:
    root=root.resolve(strict=True)
    if root == Path("/") or not root.is_dir():
        raise ValueError("Only a disposable extracted initrd root is accepted")
    p=root/'usr/lib/live/boot/9990-main.sh'
    if p.is_symlink() or not p.is_file():
        raise ValueError("Expected genuine live-boot initrd script")
    s=p.read_text()
    if s.count(MARKER)!=1 or "P50_V120_DIRECT" in s:
        raise ValueError("Unexpected live boot script or already patched")
    if 'P50_V118_EARLY_USER' not in s or 'P50_V119_LIVECONFIG_DISABLED' not in s:
        raise ValueError("v120 requires the v118 account and v119 service-skip patches")
    p.write_text(s.replace(MARKER,DIRECT+MARKER,1))
    return p


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('extracted_root',type=Path)
    args=a.parse_args()
    print(patch(args.extracted_root))
