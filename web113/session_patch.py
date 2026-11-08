#!/usr/bin/env python3
"""Test earlier LightDM scheduling without changing browser or login executables."""
import argparse
from pathlib import Path

MAIN='\n\tFstab\n\tNetbase\n'
MIGRATE='"$B" sleep 8\nemit P50_STAGE_START\n'
LIGHTDM=r'''[Unit]
After=live-config.service plymouth-quit.service
Wants=live-config.service
P50_DEFAULT_DEPENDENCIES

[Service]
ExecStartPre=/bin/sh -c 'echo P50_V113_LIGHTDM_STARTED $(cat /proc/uptime) > /dev/ttyS0'
'''
BUS_SOCKET='''[Unit]
DefaultDependencies=no
After=local-fs.target systemd-tmpfiles-setup.service
Before=sysinit.target
'''
BUS_SERVICE='''[Unit]
DefaultDependencies=no
After=local-fs.target systemd-tmpfiles-setup.service dbus.socket
Before=sysinit.target
'''
REPORT=r'''(
    "$B" sleep 12
    {
        printf '\nP50_V113_SESSION_PROFILE_BEGIN\n'
        printf 'UPTIME '; cat /proc/uptime
        printf '\n--- startup timing ---\n'; systemd-analyze time || true
        printf '\n--- relevant journal ---\n'; journalctl -b -u dbus.service -u dbus.socket -u lightdm.service -u live-config.service -u systemd-logind.service --no-pager -o short-monotonic || true
        printf '\n--- service ordering ---\n'; systemctl show -p After -p Before -p Wants -p Requires -p DefaultDependencies lightdm.service dbus.service dbus.socket || true
        p50_fragment="$(systemctl show -p FragmentPath --value lightdm.service)"
        p50_after="$(systemctl show -p After --value lightdm.service)"
        case " ${p50_after} " in
          *' systemd-user-sessions.service '*) printf 'P50_V113_SESSION_ORDER_MISSING\n' ;;
          *) if [ "${p50_fragment}" = /etc/systemd/system/lightdm.service ]; then printf 'P50_V113_SESSION_ORDER_OK\n'; else printf 'P50_V113_SESSION_ORDER_MISSING\n'; fi ;;
        esac
        printf '\n--- user processes ---\n'; ps -eo user,comm,args | grep -E '[f]irefox|[n]m-applet|[p]olkit|[o]penbox|[X]org' || true
        if pgrep -u user -f '[f]irefox' >/dev/null 2>&1 && pgrep -u user -x nm-applet >/dev/null 2>&1 && pgrep -u user -x tint2 >/dev/null 2>&1 && pgrep -u user -x p50-status >/dev/null 2>&1; then
            printf 'P50_V113_SESSION_UI_OK\n'
        else
            printf 'P50_V113_SESSION_UI_MISSING\n'
        fi
        printf '\nP50_V113_SESSION_PROFILE_END\n'
    } >/dev/ttyS0 2>&1
) &
'''


def patch_main(text,mode):
    if text.count(MAIN)!=1 or 'P50_V113_SESSION_EXPERIMENT' in text:
        raise ValueError('Unexpected or previously patched boot main')
    if mode not in ('parallel','earlybus'):raise ValueError('Unknown session experiment')
    light=LIGHTDM.replace('P50_DEFAULT_DEPENDENCIES','DefaultDependencies=no' if mode=='earlybus' else '')
    hook=r'''
\t# P50_V113_SESSION_EXPERIMENT: test-only service ordering; full-RAM fallback unchanged.
\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
\t\tp50_session_base="${rootmnt}/usr/lib/systemd/system/lightdm.service"
\t\tp50_session_override="${rootmnt}/etc/systemd/system/lightdm.service"
\t\t[ -f "${p50_session_base}" ] && [ ! -L "${p50_session_base}" ] && [ ! -e "${p50_session_override}" ] && [ ! -L "${p50_session_override}" ] || panic "p50: unexpected LightDM unit"
\t\t[ "$(grep -Fxc 'After=systemd-user-sessions.service' "${p50_session_base}")" = 1 ] && grep -Fqx 'ExecStart=/usr/sbin/lightdm' "${p50_session_base}" || panic "p50: unexpected LightDM dependency"
\t\tsed '/^After=systemd-user-sessions.service$/d' "${p50_session_base}" > "${p50_session_override}" || panic "p50: cannot copy LightDM unit"
\t\tp50_session_dir="${rootmnt}/etc/systemd/system/lightdm.service.d"
\t\tp50_session_drop="${p50_session_dir}/80-v113-experiment.conf"
\t\t[ -d "${p50_session_dir}" ] && [ ! -L "${p50_session_dir}" ] && [ ! -e "${p50_session_drop}" ] && [ ! -L "${p50_session_drop}" ] || panic "p50: unexpected LightDM configuration"
\t\tcat > "${p50_session_drop}" <<'P50_V113_LIGHTDM_UNIT'
P50_LIGHTDM_CONTENT
P50_V113_LIGHTDM_UNIT
P50_BUS_INSTALL
\tfi
'''.replace('\\t','\t').replace('P50_LIGHTDM_CONTENT',light.rstrip())
    bus=''
    if mode=='earlybus':
        bus=r'''
\t\tfor p50_bus_name in dbus.socket dbus.service; do
\t\t\tp50_bus_dir="${rootmnt}/etc/systemd/system/${p50_bus_name}.d"
\t\t\tp50_bus_drop="${p50_bus_dir}/80-v113-experiment.conf"
\t\t\t[ ! -L "${p50_bus_dir}" ] && [ ! -e "${p50_bus_drop}" ] && [ ! -L "${p50_bus_drop}" ] || panic "p50: unexpected bus override"
\t\t\tmkdir -p "${p50_bus_dir}" || panic "p50: cannot create bus override"
\t\t\tif [ "${p50_bus_name}" = dbus.socket ]; then
\t\t\t\tcat > "${p50_bus_drop}" <<'P50_V113_BUS_SOCKET'
P50_BUS_SOCKET_CONTENT
P50_V113_BUS_SOCKET
\t\t\telse
\t\t\t\tcat > "${p50_bus_drop}" <<'P50_V113_BUS_SERVICE'
P50_BUS_SERVICE_CONTENT
P50_V113_BUS_SERVICE
\t\t\tfi
\t\tdone
'''.replace('\\t','\t').replace('P50_BUS_SOCKET_CONTENT',BUS_SOCKET.rstrip()).replace('P50_BUS_SERVICE_CONTENT',BUS_SERVICE.rstrip())
        # Explicit names are retained for audit and tests.
        bus='\t\t# Overrides are installed into dbus.socket.d and dbus.service.d.\n'+bus
    return text.replace(MAIN,hook.replace('P50_BUS_INSTALL',bus.rstrip())+MAIN,1)


def patch_migration(text):
    if text.count(MIGRATE)!=1 or 'P50_V113_SESSION_PROFILE_BEGIN' in text:
        raise ValueError('Unexpected or previously patched migration script')
    return text.replace(MIGRATE,REPORT+MIGRATE,1)


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('mode',choices=('parallel','earlybus'));a=p.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify the running system')
    files=[(root/'usr/lib/live/boot/9990-main.sh',lambda s:patch_main(s,a.mode)),(root/'usr/lib/p50-stage/p50-migrate.sh',patch_migration)]
    new=[]
    for path,fn in files:
        if path.is_symlink() or not path.is_file():raise ValueError('Expected regular extracted boot file')
        new.append((path,fn(path.read_text())))
    for path,data in new:path.write_text(data)

if __name__=='__main__':main()
