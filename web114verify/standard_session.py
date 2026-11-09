#!/usr/bin/env python3
"""Explore a less divergent early session; diagnostic, never a release patch."""
import argparse
import importlib.util
from pathlib import Path

repo=Path(__file__).resolve().parents[1]
source=next((repo/name/'early_session.py' for name in ('web114_session','v114_session') if (repo/name/'early_session.py').is_file()),None)
if source is None:raise RuntimeError('Missing original early-session prototype')
spec=importlib.util.spec_from_file_location('p50_early_session',source)
early=importlib.util.module_from_spec(spec);spec.loader.exec_module(early)

OLD_LOGIND='''sed 's/^After=nss-user-lookup.target user.slice modprobe@drm.service$/After=nss-user-lookup.target user.slice/' "${p50_lgsrc}" > "${p50_lgdst}" || panic "p50: cannot create logind test unit"'''
NEW_LOGIND='''cp "${p50_lgsrc}" "${p50_lgdst}" || panic "p50: cannot copy original logind unit"'''
OLD_SESSION='/usr/bin/dbus-run-session /usr/bin/openbox-session'
NEW_SESSION='/usr/bin/dbus-run-session /etc/X11/Xsession /usr/bin/openbox-session'
MARKER='\t\tp50_prep="${rootmnt}/etc/systemd/system/p50-user-preparation.service"\n'
PROBE=r'''
\t\tp50_xsession_probe="${rootmnt}/etc/X11/Xsession.d/89puppy50-probe"
\t\t[ -d "${rootmnt}/etc/X11/Xsession.d" ] && [ ! -L "${rootmnt}/etc/X11/Xsession.d" ] && [ ! -e "${p50_xsession_probe}" ] && [ ! -L "${p50_xsession_probe}" ] || panic "p50: unexpected Xsession probe"
\t\tcat > "${p50_xsession_probe}" <<'P50_V114_XSESSION_PROBE'
printf '%s\n' P50_V114_XSESSION_HOOK_RAN > /tmp/p50-v114-xsession-hook
P50_V114_XSESSION_PROBE
'''.replace('\\t','\t')
REPORT=r'''(
    "$B" sleep 12
    if [ -s /tmp/p50-v114-xsession-hook ]; then
        echo P50_V114_XSESSION_HOOK_OK >/dev/ttyS0
    else
        echo P50_V114_XSESSION_HOOK_MISSING >/dev/ttyS0
    fi
) &
'''

def patch_main(text):
    result=early.patch_main(text)
    for old,new in ((OLD_LOGIND,NEW_LOGIND),(OLD_SESSION,NEW_SESSION)):
        if result.count(old)!=1:raise ValueError('Unexpected early-session prototype')
        result=result.replace(old,new,1)
    if result.count(MARKER)!=1:raise ValueError('Unexpected session hook')
    result=result.replace(MARKER,PROBE+MARKER,1)
    return result

def patch_migration(text):
    result=early.patch_migration(text)
    if result.count(early.direct.MIGRATE)!=1 or 'P50_V114_XSESSION_HOOK_OK' in result:
        raise ValueError('Unexpected migration script')
    return result.replace(early.direct.MIGRATE,REPORT+early.direct.MIGRATE,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify the running system')
    paths=[(root/'usr/lib/live/boot/9990-main.sh',patch_main),(root/'usr/lib/p50-stage/p50-migrate.sh',patch_migration)]
    updates=[]
    for path,fn in paths:
        if path.is_symlink() or not path.is_file():raise ValueError('Expected regular extracted boot file')
        updates.append((path,fn(path.read_text())))
    for path,text in updates:path.write_text(text)

if __name__=='__main__':main()
