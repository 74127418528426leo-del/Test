#!/usr/bin/env python3
"""Test a direct non-root X11 session in the staged live boot only."""
import argparse
from pathlib import Path

MAIN='\n\tFstab\n\tNetbase\n'
MIGRATE='"$B" sleep 8\nemit P50_STAGE_START\n'

UNIT='''[Unit]
Description=Puppy50 direct X11 session experiment
After=live-config.service systemd-user-sessions.service systemd-logind.service
Wants=live-config.service systemd-logind.service
Conflicts=getty@tty1.service
After=getty@tty1.service

[Service]
Type=simple
User=user
PAMName=login
Environment=HOME=/home/user XDG_SESSION_TYPE=x11 XDG_SESSION_CLASS=user XDG_SEAT=seat0
ExecStartPre=+/usr/local/sbin/puppy50-prepare-session
ExecStart=/usr/bin/startx /usr/bin/dbus-run-session /usr/bin/openbox-session -- :0 vt1 -keeptty -nolisten tcp
StandardInput=tty
TTYPath=/dev/tty1
TTYReset=yes
Restart=on-failure
RestartSec=2
'''

REPORT=r'''(
    "$B" sleep 12
    {
        printf '\nP50_V113_DIRECT_PROFILE_BEGIN\n'
        printf '%s\n' '--- display manager PAMName, user and state ---'
        systemctl show -p User -p PAMName -p ActiveState display-manager.service || true
        printf '%s\n' '--- user session and processes ---'
        loginctl list-sessions --no-legend || true
        ps -eo user,comm,args | grep -E '[f]irefox|[n]m-applet|[p]olkit|[o]penbox|[X]org|[s]tartx' || true
        if systemctl show -p User --value display-manager.service | grep -Fx user >/dev/null && \
           systemctl show -p PAMName --value display-manager.service | grep -Fx login >/dev/null && \
           pgrep -u user -f '[f]irefox' >/dev/null 2>&1 && pgrep -u user -x nm-applet >/dev/null 2>&1 && \
           pgrep -u user -x tint2 >/dev/null 2>&1 && pgrep -u user -x p50-status >/dev/null 2>&1; then
            printf 'P50_V113_DIRECT_UI_OK\n'
        else
            printf 'P50_V113_DIRECT_UI_MISSING\n'
        fi
        printf 'P50_V113_DIRECT_PROFILE_END\n'
    } >/dev/ttyS0 2>&1
) &
'''

def patch_main(text):
    if text.count(MAIN)!=1 or 'P50_V113_DIRECT_X' in text:
        raise ValueError('Unexpected or already patched live boot main')
    hook=r'''
\t# P50_V113_DIRECT_X: test-only direct unprivileged graphical session.
\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
\t\tp50_dm="${rootmnt}/etc/systemd/system/display-manager.service"
\t\t[ -L "${p50_dm}" ] && [ "$(readlink "${p50_dm}")" = /lib/systemd/system/lightdm.service ] || panic "p50: unexpected display-manager link"
\t\trm "${p50_dm}" || panic "p50: cannot replace test display-manager link"
\t\tcat > "${p50_dm}" <<'P50_V113_DIRECT_X_UNIT'
P50_UNIT
P50_V113_DIRECT_X_UNIT
\tfi
'''.replace('\\t','\t').replace('P50_UNIT',UNIT.rstrip())
    return text.replace(MAIN,hook+MAIN,1)

def patch_migration(text):
    if text.count(MIGRATE)!=1 or 'P50_V113_DIRECT_PROFILE_BEGIN' in text:
        raise ValueError('Unexpected or already patched migration script')
    return text.replace(MIGRATE,REPORT+MIGRATE,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify the running system')
    files=[(root/'usr/lib/live/boot/9990-main.sh',patch_main),(root/'usr/lib/p50-stage/p50-migrate.sh',patch_migration)]
    out=[]
    for path,fn in files:
        if path.is_symlink() or not path.is_file():raise ValueError('Expected regular extracted boot file')
        out.append((path,fn(path.read_text())))
    for path,data in out:path.write_text(data)

if __name__=='__main__':main()
