#!/usr/bin/env python3
"""Research-only read-only after-switchroot report for the failed v123 early X11."""
from pathlib import Path
import argparse

MARKER="\n\tFstab\n\tNetbase\n"
HOOK=r'''
    # P50_V124_POSTROOT_X11_FORENSIC: research-only, no system policy change.
    if [ -z "@{TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
        p50_diagnose="@{rootmnt}/usr/local/sbin/p50-v124-x11-diagnose"
        p50_unit="@{rootmnt}/etc/systemd/system/p50-v124-x11-diagnose.service"
        p50_dir="@{rootmnt}/etc/systemd/system/multi-user.target.wants"
        [ ! -e "$p50_diagnose" ] && [ ! -L "$p50_diagnose" ] || panic "v124: existing diagnostic"
        mkdir -p "$p50_dir" || panic "v124: cannot make service directory"
        cat >"$p50_diagnose" <<'P50_V124_DIAGNOSTIC'
#!/bin/sh
sleep 7
{
    printf '\nP50_V124_FORENSICS_START uptime='
    cat /proc/uptime
    printf '\n-- display and session processes --\n'
    ps -eo pid,ppid,uid,tty,comm,args | grep -E '[X]org|[f]irefox|[o]penbox|[d]bus-run-session|[l]ightdm|[s]tartx' | head -45 || true
    printf '\n-- active VT / framebuffer --\n'
    cat /sys/class/tty/tty0/active 2>&1 || true
    cat /proc/consoles || true
    printf '\n-- xauth/x11 sockets --\n'
    ls -la /tmp/.X11-unix /home/user/.Xauthority /run/user/1000 /run/p50-v123* 2>&1 || true
    printf '\n-- early Xorg log --\n'
    tail -100 /run/p50-v123-xorg.log 2>&1 || true
    printf '\n-- early Openbox log --\n'
    tail -100 /run/p50-v123-openbox.log 2>&1 || true
    printf '\n-- Firefox startup log --\n'
    tail -100 /tmp/puppy50-firefox.log 2>&1 || true
    printf '\n-- live-config/login/graphics journal --\n'
    journalctl -b -u display-manager.service -u systemd-logind.service -u live-config.service --no-pager -o short-monotonic | tail -80 || true
    if command -v xwininfo >/dev/null 2>&1 && [ -f /home/user/.Xauthority ]; then
        printf '\n-- X11 window tree --\n'
        env DISPLAY=:0 XAUTHORITY=/home/user/.Xauthority xwininfo -root -tree 2>&1 | tail -75 || true
    fi
    if command -v xdpyinfo >/dev/null 2>&1 && [ -f /home/user/.Xauthority ]; then
        printf '\n-- X11 display server info --\n'
        env DISPLAY=:0 XAUTHORITY=/home/user/.Xauthority xdpyinfo 2>&1 | head -35 || true
    fi
    printf '\nP50_V124_FORENSICS_END\n'
} >/dev/ttyS0 2>&1
exit 0
P50_V124_DIAGNOSTIC
        chmod 0755 "$p50_diagnose" || panic "v124: cannot chmod diagnostic"
        cat >"$p50_unit" <<'P50_V124_SERVICE'
[Unit]
Description=Read-only post-root analysis of early X11 black-screen candidate
After=basic.target
[Service]
Type=simple
ExecStart=/usr/local/sbin/p50-v124-x11-diagnose
NoNewPrivileges=true
[Install]
WantedBy=multi-user.target
P50_V124_SERVICE
        ln -s ../p50-v124-x11-diagnose.service "$p50_dir/p50-v124-x11-diagnose.service" || panic "v124: cannot enable reporter"
    fi
'''.replace('\n    ','\n\t').replace('@{',chr(36)+'{')


def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():
        raise ValueError('Refusing host file modification')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if p.is_symlink() or not p.is_file(): raise ValueError('No extracted live main')
    s=p.read_text()
    if s.count(MARKER)!=1 or 'P50_V124_POSTROOT_X11_FORENSIC' in s:
        raise ValueError('Unexpected or already patched live script')
    if 'P50_V123_BEFORE_PID1' not in s: raise ValueError('Original failed v123 attempt required')
    p.write_text(s.replace(MARKER,HOOK+MARKER,1))
    return p

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
