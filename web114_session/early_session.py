#!/usr/bin/env python3
"""Test an early PAM/logind graphical session, without changing the fallback."""
import argparse
import importlib.util
from pathlib import Path

repo=Path(__file__).resolve().parents[1]
source=next((repo/name/'direct_session.py' for name in ('web113','v113') if (repo/name/'direct_session.py').is_file()),None)
if source is None:raise RuntimeError('Missing v113 direct-session patch')
spec=importlib.util.spec_from_file_location('p50_direct_session',source)
direct=importlib.util.module_from_spec(spec);spec.loader.exec_module(direct)

OLD_UNIT='''After=live-config.service systemd-user-sessions.service systemd-logind.service
Wants=live-config.service systemd-logind.service
'''
NEW_UNIT='''DefaultDependencies=no
Requires=local-fs.target
After=local-fs.target systemd-tmpfiles-setup.service
Wants=systemd-logind.service dbus.socket systemd-udev-trigger.service
After=systemd-logind.service dbus.socket systemd-udev-trigger.service
Before=sysinit.target
'''
OLD_PREP='''After=live-config.service
Wants=live-config.service
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/puppy50-prepare-session
'''
NEW_PREP='''DefaultDependencies=no
Requires=local-fs.target
After=local-fs.target systemd-tmpfiles-setup.service
Before=sysinit.target
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/puppy50-prepare-session
'''
EXTRA=r'''
\t\t# P50_V114_EARLY_BUS: isolate the display session from late user/network startup.
\t\tp50_lgsrc="${rootmnt}/usr/lib/systemd/system/systemd-logind.service"
\t\tp50_lgdst="${rootmnt}/etc/systemd/system/systemd-logind.service"
\t\t[ -f "${p50_lgsrc}" ] && [ ! -L "${p50_lgsrc}" ] && [ ! -e "${p50_lgdst}" ] && [ ! -L "${p50_lgdst}" ] || panic "p50: unexpected logind unit"
\t\t[ "$(grep -Fxc 'Wants=user.slice modprobe@drm.service' "${p50_lgsrc}")" = 1 ] && [ "$(grep -Fxc 'After=nss-user-lookup.target user.slice modprobe@drm.service' "${p50_lgsrc}")" = 1 ] || panic "p50: unexpected logind ordering"
\t\tsed 's/^After=nss-user-lookup.target user.slice modprobe@drm.service$/After=nss-user-lookup.target user.slice/' "${p50_lgsrc}" > "${p50_lgdst}" || panic "p50: cannot create logind test unit"
\t\tp50_watch="${rootmnt}/etc/systemd/system/p50-early-watch.service"
\t\tp50_wants="${rootmnt}/etc/systemd/system/sysinit.target.wants"
\t\t[ ! -e "${p50_watch}" ] && [ ! -L "${p50_watch}" ] && [ ! -L "${p50_wants}" ] || panic "p50: unexpected early diagnostic"
\t\tmkdir -p "${p50_wants}" || panic "p50: cannot create early diagnostic directory"
\t\tcat > "${p50_watch}" <<'P50_V114_WATCH_UNIT'
[Unit]
Description=Test-only early boot diagnostics
DefaultDependencies=no
After=local-fs.target systemd-tmpfiles-setup.service
Before=sysinit.target
[Service]
Type=simple
ExecStart=/bin/sh -c 'sleep 20; echo P50_V114_EARLY_WATCH_BEGIN > /dev/ttyS0; timeout 5 systemctl list-jobs --no-pager > /dev/ttyS0 2>&1; timeout 5 journalctl -b -u display-manager.service -u systemd-logind.service -u dbus.service -u dbus.socket -u p50-user-preparation.service --no-pager -o short-monotonic > /dev/ttyS0 2>&1; echo P50_V114_EARLY_WATCH_END > /dev/ttyS0'
P50_V114_WATCH_UNIT
\t\tln -s ../p50-early-watch.service "${p50_wants}/p50-early-watch.service" || panic "p50: cannot enable early diagnostic"
\t\tfor p50_service in dbus.socket dbus.service systemd-logind.service; do
\t\t\tp50_dropdir="${rootmnt}/etc/systemd/system/${p50_service}.d"
\t\t\tp50_drop="${p50_dropdir}/80-v114-early.conf"
\t\t\t[ ! -L "${p50_dropdir}" ] && [ ! -e "${p50_drop}" ] && [ ! -L "${p50_drop}" ] || panic "p50: unexpected early bus override"
\t\t\tmkdir -p "${p50_dropdir}" || panic "p50: cannot create early bus override"
\t\t\tcat > "${p50_drop}" <<'P50_V114_EARLY_UNIT'
[Unit]
DefaultDependencies=no
After=local-fs.target systemd-tmpfiles-setup.service
Before=sysinit.target
P50_V114_EARLY_UNIT
\t\t\tif [ "${p50_service}" != dbus.socket ]; then
\t\t\t\tprintf '%s\n' 'After=dbus.socket' >> "${p50_drop}" || panic "p50: cannot order bus socket"
\t\t\tfi
\t\tdone
'''.replace('\\t','\t')
REPORT=r'''(
    "$B" sleep 12
    {
        printf '\nP50_V114_EARLY_PROFILE_BEGIN\n'
        printf '%s\n' '--- ordering and service state ---'
        systemctl show -p DefaultDependencies -p After -p ActiveState display-manager.service dbus.socket dbus.service systemd-logind.service p50-user-preparation.service || true
        printf '%s\n' '--- monotonic session journal ---'
        journalctl -b -u display-manager.service -u systemd-logind.service -u p50-user-preparation.service -u dbus.service -u dbus.socket -u live-config.service --no-pager -o short-monotonic | tail -120 || true
        p50_after="$(systemctl show -p After --value display-manager.service)"
        p50_display="$(systemctl show -p DefaultDependencies --value display-manager.service)"
        p50_logind="$(systemctl show -p DefaultDependencies --value systemd-logind.service)"
        p50_socket="$(systemctl show -p DefaultDependencies --value dbus.socket)"
        if [ "$p50_display" = no ] && [ "$p50_logind" = no ] && [ "$p50_socket" = no ] && \
           ! printf ' %s ' "$p50_after" | grep -Eq ' (live-config.service|systemd-user-sessions.service|sysinit.target) '; then
            printf 'P50_V114_EARLY_ORDER_OK\n'
        else
            printf 'P50_V114_EARLY_ORDER_MISSING\n'
        fi
        printf 'P50_V114_EARLY_PROFILE_END\n'
    } >/dev/ttyS0 2>&1
) &
'''

def one_replace(text,old,new):
    if text.count(old)!=1:raise ValueError('Unexpected direct-session text')
    return text.replace(old,new,1)

def patch_main(text):
    result=direct.patch_main(text)
    result=one_replace(result,OLD_UNIT,NEW_UNIT)
    result=one_replace(result,OLD_PREP,NEW_PREP)
    marker='\t\tp50_prep="${rootmnt}/etc/systemd/system/p50-user-preparation.service"\n'
    return one_replace(result,marker,EXTRA+marker)

def patch_migration(text):
    result=direct.patch_migration(text)
    if 'P50_V114_EARLY_PROFILE_BEGIN' in result:raise ValueError('Already instrumented')
    return one_replace(result,direct.MIGRATE,REPORT+direct.MIGRATE)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify the live system')
    paths=[(root/'usr/lib/live/boot/9990-main.sh',patch_main),(root/'usr/lib/p50-stage/p50-migrate.sh',patch_migration)]
    updates=[]
    for path,func in paths:
        if path.is_symlink() or not path.is_file():raise ValueError('Expected regular initramfs file')
        updates.append((path,func(path.read_text())))
    for path,text in updates:path.write_text(text)

if __name__=='__main__':main()
