#!/usr/bin/env python3
"""Test-only Firefox software WebRender setting at real first-window paint.

Mozilla bug 2084921 reports Linux CI's llvmpipe shader compilation delaying the
first browser paint. This experiment uses Firefox ESR enterprise Preferences,
without disabling its sandbox, process isolation, networking or TLS. The
policy must be installed BEFORE the early pre-PID1 nonroot Firefox is launched.
"""
from pathlib import Path
import argparse,json

MAIN_MARKER='cat > "$p50_start" <<\'P50_V123_START_X\''
MIGRATE_MARKER='"$B" sleep 8\nemit P50_STAGE_START\n'
POLICY=json.dumps({"policies":{"Preferences":{
    "gfx.webrender.software":{"Value":True,"Status":"user"}
}}},separators=(",",":"))

HOOK=r'''
        # P50_V129_SOFTWARE_WEBRENDER: nonproduction first-paint experiment.
        p50_policy_link="$p50_root/usr/lib/firefox-esr/distribution"
        [ -L "$p50_policy_link" ] && [ "$(readlink "$p50_policy_link")" = '../../share/firefox-esr/distribution' ] || panic "v129: unknown Firefox distribution path"
        p50_policy_dir="$p50_root/usr/share/firefox-esr/distribution"
        [ -d "$p50_policy_dir" ] && [ ! -L "$p50_policy_dir" ] || panic "v129: unexpected Firefox policy dir"
        for p50_existing in "$p50_root/etc/firefox/policies/policies.json" "$p50_root/etc/firefox-esr/policies/policies.json" "$p50_policy_dir/policies.json"; do
            [ ! -e "$p50_existing" ] && [ ! -L "$p50_existing" ] || panic "v129: prior Firefox policy must not be overwritten"
        done
        printf '%s\n' 'P50_V129_POLICY_JSON' > "$p50_policy_dir/policies.json" || panic "v129: cannot install test preference"
        printf 'P50_V129_POLICY_BEFORE_BROWSER %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
'''

REPORT=r'''(
    "$B" sleep 12
    {
        printf '\nP50_V129_PREF_PROFILE_BEGIN\n'
        p50_policy=/usr/share/firefox-esr/distribution/policies.json
        if [ -f "$p50_policy" ]; then cat "$p50_policy"; else printf 'POLICY_MISSING\n'; fi
        p50_seen=0
        for p50_pref_file in /home/user/.config/mozilla/firefox/*/prefs.js /home/user/.mozilla/firefox/*/prefs.js; do
            if [ -f "$p50_pref_file" ]; then
                grep -F 'gfx.webrender.software' "$p50_pref_file" || true
                if grep -Fqx 'user_pref("gfx.webrender.software", true);' "$p50_pref_file"; then
                    p50_seen=1
                fi
            fi
        done
        if [ "$p50_seen" = 1 ]; then
            printf 'P50_V129_PREF_OBSERVED\n'
        else
            printf 'P50_V129_PREF_NOT_PERSISTED\n'
        fi
        printf 'P50_V129_PREF_PROFILE_END\n'
    } >/dev/ttyS0 2>&1
) &
'''

def patch(root:Path)->tuple[Path,Path]:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():
        raise ValueError("Only modify disposable extracted initrd")
    main=root/'usr/lib/live/boot/9990-main.sh'
    migration=root/'usr/lib/p50-stage/p50-migrate.sh'
    if any(not p.is_file() or p.is_symlink() for p in (main,migration)):
        raise ValueError("Expected both original regular boot/migration scripts")
    s=main.read_text(); m=migration.read_text()
    if any(marker not in s for marker in ('P50_V123_BEFORE_PID1','P50_V126_PRESERVE_XSOCKET','P50_V127_DIRECT_BROWSER')):
        raise ValueError("Requires authenticated Xorg, preserved socket and parallel Firefox launch")
    if s.count(MAIN_MARKER)!=1 or m.count(MIGRATE_MARKER)!=1:
        raise ValueError("Unexpected live-boot source: cannot prove pre-Firefox injection")
    if 'P50_V129_SOFTWARE_WEBRENDER' in s or 'P50_V129_PREF_PROFILE_BEGIN' in m:
        raise ValueError("Already patched")
    injected=HOOK.replace('P50_V129_POLICY_JSON',POLICY)
    main.write_text(s.replace(MAIN_MARKER,injected+MAIN_MARKER,1))
    migration.write_text(m.replace(MIGRATE_MARKER,REPORT+MIGRATE_MARKER,1))
    return main,migration

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('extracted_root',type=Path)
    print(patch(parser.parse_args().extracted_root))
