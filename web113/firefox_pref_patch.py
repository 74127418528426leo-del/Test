#!/usr/bin/env python3
"""Isolated Firefox spare-process startup experiments, preserving sandbox defaults."""
import argparse
import json
from pathlib import Path

MAIN='\n\tFstab\n\tNetbase\n'
MIGRATE='"$B" sleep 8\nemit P50_STAGE_START\n'
MODES={'off':('dom.ipc.processPrelaunch.enabled',False),
       'delay':('dom.ipc.processPrelaunch.delayMs',8000)}

def policy(mode):
    if mode not in MODES:raise ValueError('Unknown Firefox preference experiment')
    key,value=MODES[mode]
    return json.dumps({'policies':{'Preferences':{key:{'Value':value,'Status':'user'}}}},separators=(',',':'))


def patch_main(text,mode):
    if text.count(MAIN)!=1 or 'P50_V113_PRELAUNCH_PREF' in text:
        raise ValueError('Unexpected or already patched boot main')
    value=policy(mode)
    hook=r'''
\t# P50_V113_PRELAUNCH_PREF: test one changeable browser startup preference.
\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
\t\tp50_link="${rootmnt}/usr/lib/firefox-esr/distribution"
\t\t[ -L "${p50_link}" ] && [ "$(readlink "${p50_link}")" = '../../share/firefox-esr/distribution' ] || panic "p50: unexpected Firefox distribution link"
\t\tp50_dir="${rootmnt}/usr/share/firefox-esr/distribution"
\t\t[ -d "${p50_dir}" ] && [ ! -L "${p50_dir}" ] || panic "p50: unexpected Firefox distribution directory"
\t\tfor p50_policy in "${rootmnt}/etc/firefox/policies/policies.json" "${rootmnt}/etc/firefox-esr/policies/policies.json" "${p50_dir}/policies.json"; do
\t\t\t[ ! -e "${p50_policy}" ] && [ ! -L "${p50_policy}" ] || panic "p50: unexpected existing Firefox policy"
\t\tdone
\t\tprintf '%s\n' 'P50_V113_POLICY_JSON' > "${p50_dir}/policies.json" || panic "p50: cannot write experiment policy"
\tfi
'''.replace('\\t','\t').replace('P50_V113_POLICY_JSON',value)
    return text.replace(MAIN,hook+MAIN,1)


def patch_migration(text,mode):
    if text.count(MIGRATE)!=1 or 'P50_V113_PREF_PROFILE_BEGIN' in text:
        raise ValueError('Unexpected or already patched migration script')
    key,value=MODES[mode]
    js='false' if value is False else str(value)
    expected='user_pref("'+key+'", '+js+');'
    report=r'''(
    "$B" sleep 12
    {
        printf '\nP50_V113_PREF_PROFILE_BEGIN\n'
        printf '%s\n' '--- installed experiment policy ---'
        cat /usr/share/firefox-esr/distribution/policies.json 2>/dev/null || true
        printf '\n%s\n' '--- Firefox profile paths ---'
        ls -la /home/user/.mozilla/firefox 2>/dev/null || true
        find /home/user /tmp -maxdepth 7 -name prefs.js -type f -print 2>/dev/null | head -30 || true
        p50_pid="$(pgrep -u user -x firefox-esr | head -1)"
        if [ -n "$p50_pid" ] && [ -r "/proc/$p50_pid/environ" ]; then
            tr '\000' '\n' <"/proc/$p50_pid/environ" | grep -E '^(HOME|XDG_CONFIG_HOME|XDG_CACHE_HOME)=' || true
        fi
        p50_found=0
        for p50_pref_file in /home/user/.mozilla/firefox/*/prefs.js; do
            if [ -r "$p50_pref_file" ]; then
                printf 'P50_V113_PREF_FILE %s\n' "$p50_pref_file"
                grep -F 'dom.ipc.processPrelaunch.' "$p50_pref_file" || true
            fi
            if [ -r "$p50_pref_file" ] && grep -Fqx 'P50_EXPECTED_PREF' "$p50_pref_file"; then p50_found=1; fi
        done
        if [ "$p50_found" = 1 ]; then printf 'P50_V113_PREF_OBSERVED\n'; else printf 'P50_V113_PREF_MISSING\n'; fi
        printf '%s\n' '--- browser processes ---'
        ps -eo user,comm,args | grep -E '[f]irefox|[W]eb Content|[i]solated' || true
        printf '\nP50_V113_PREF_PROFILE_END\n'
    } >/dev/ttyS0 2>&1
) &
'''.replace('P50_EXPECTED_PREF',expected)
    return text.replace(MIGRATE,report+MIGRATE,1)


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('mode',choices=tuple(MODES));a=p.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify the running system')
    files=[(root/'usr/lib/live/boot/9990-main.sh',lambda s:patch_main(s,a.mode)),(root/'usr/lib/p50-stage/p50-migrate.sh',lambda s:patch_migration(s,a.mode))]
    output=[]
    for path,fn in files:
        if path.is_symlink() or not path.is_file():raise ValueError('Expected regular extracted boot file')
        output.append((path,fn(path.read_text())))
    for path,data in output:path.write_text(data)

if __name__=='__main__':main()
