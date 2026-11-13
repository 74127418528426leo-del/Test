#!/usr/bin/env python3
"""Add a nonblocking, root-level systemd startup reporter to a test-only initrd.

Unlike initramfs background reporters, this reporter runs after switch-root
under the real guest systemd and prints its journal/critical-chain to serial.
It modifies no Firefox, kernel, network manager, RAM-migration or fallback bytes.
"""
from pathlib import Path
import argparse

MARKER="\n\tFstab\n\tNetbase\n"
HOOK=r'''
    # P50_V120_SYSTEMD_DIAGNOSTIC_ONLY.
    if [ -z "@{TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
        p50_bin="@{rootmnt}/usr/local/sbin/p50-v120-profile"
        p50_unit="@{rootmnt}/etc/systemd/system/p50-v120-profile.service"
        p50_wants="@{rootmnt}/etc/systemd/system/multi-user.target.wants"
        [ ! -e "$p50_bin" ] && [ ! -L "$p50_bin" ] || panic "v120: profiler already exists"
        [ ! -e "$p50_unit" ] && [ ! -L "$p50_unit" ] || panic "v120: profiling service already exists"
        mkdir -p "$p50_wants" || panic "v120: cannot install profiler"
        cat >"$p50_bin" <<'P50_V120_PROFILE_SCRIPT'
#!/bin/sh
# This is a read-only after-boot diagnostic process. Do not block Firefox.
sleep 11
{
    printf '\nP50_V120_CRITICAL_BEGIN\n'
    printf 'GUEST_UPTIME '; cat /proc/uptime
    printf '\nP50_V120_SYSTEMD_TIME\n'; systemd-analyze time || true
    printf '\nP50_V120_DISPLAY_CHAIN\n'; systemd-analyze critical-chain display-manager.service || true
    printf '\nP50_V120_GRAPHICAL_CHAIN\n'; systemd-analyze critical-chain graphical.target || true
    printf '\nP50_V120_LOGIN_JOURNAL\n'; journalctl -b -u display-manager.service -u lightdm.service -u live-config.service -u systemd-logind.service --no-pager -o short-monotonic | tail -100 || true
    printf '\nP50_V120_BOOT_BLAME\n'; systemd-analyze blame | head -45 || true
    printf '\nP50_V120_BROWSER_PROCESS\n'; ps -eo pid,ppid,user,comm,args | grep -E '[f]irefox|[o]penbox|[l]ightdm|[X]org|[N]etworkManager' | head -20 || true
    printf 'P50_V120_CRITICAL_END\n'
} >/dev/ttyS0 2>&1
exit 0
P50_V120_PROFILE_SCRIPT
        chmod 0755 "$p50_bin" || panic "v120: cannot make reporter executable"
        cat >"$p50_unit" <<'P50_V120_PROFILE_UNIT'
[Unit]
Description=Nonblocking Puppy50 v120 startup profiling (research only)
After=basic.target

[Service]
Type=simple
ExecStart=/usr/local/sbin/p50-v120-profile
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
P50_V120_PROFILE_UNIT
        ln -s ../p50-v120-profile.service "$p50_wants/p50-v120-profile.service" || panic "v120: cannot start profiler"
    fi
'''.replace('\n    ','\n\t').replace('@{',chr(36)+'{')


def patch(root):
    root=Path(root).resolve(strict=True)
    if root==Path('/') or not root.is_dir():
        raise ValueError('Only extracted disposable initramfs may be changed')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if p.is_symlink() or not p.is_file():raise ValueError('Unexpected live-boot file')
    s=p.read_text()
    if s.count(MARKER)!=1 or 'P50_V120_SYSTEMD_DIAGNOSTIC_ONLY' in s:
        raise ValueError('Unexpected or already patched live-boot file')
    p.write_text(s.replace(MARKER,HOOK+MARKER,1))
    return p


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
