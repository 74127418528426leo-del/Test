#!/usr/bin/env python3
"""Inject isolated, reversible v113 boot experiments into an extracted initramfs."""
import argparse
from pathlib import Path

MAIN_MARKER='\n\tFstab\n\tNetbase\n'
DEVICE_MARKER='            udevadm settle\n            p50_mm="$(/usr/lib/p50-stage/dm-init info -c --noheadings --separator : -o major,minor p50-staged-root | tr -d \'[:space:]\')" || panic "p50: cannot inspect root mapping"'
MIGRATION_MARKER='"$B" sleep 8\nemit P50_STAGE_START\n'

PROFILE_MAIN=r'''
	# P50_V113_PROFILE: research-only instrumentation on staged boot.
	if [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
		printf 'P50_V113_ROOT_HOOK %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
		p50_autostart="${rootmnt}/etc/skel/.config/openbox/autostart"
		grep -Fq 'firefox-esr file:///usr/share/puppy50web/index.html' "${p50_autostart}" || panic "p50: missing browser autostart"
		sed -i 's|^firefox-esr file:|printf "P50_V113_FIREFOX_EXEC %s" "$(cat /proc/uptime)" > /tmp/p50-v113-firefox-exec; firefox-esr file:|' "${p50_autostart}" || panic "p50: cannot instrument browser"
		grep -Fq 'P50_V113_FIREFOX_EXEC' "${p50_autostart}" || panic "p50: missing browser marker"
		p50_preflight="${rootmnt}/usr/local/sbin/puppy50-prepare-session"
		[ -f "${p50_preflight}" ] && [ ! -L "${p50_preflight}" ] || panic "p50: missing session preflight"
		[ ! -e "${p50_preflight}.v113-original" ] || panic "p50: unexpected preflight wrapper"
		mv "${p50_preflight}" "${p50_preflight}.v113-original" || panic "p50: cannot stage preflight"
		cat > "${p50_preflight}" <<'P50_V113_PREFLIGHT'
#!/bin/sh
printf 'P50_V113_PREFLIGHT_BEGIN %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
/usr/local/sbin/puppy50-prepare-session.v113-original "$@"
p50_rc=$?
printf 'P50_V113_PREFLIGHT_END %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
exit "$p50_rc"
P50_V113_PREFLIGHT
		chmod 0755 "${p50_preflight}" || panic "p50: cannot set preflight permissions"
	fi
'''.replace('\\t','\t')

PROFILE_REPORT=r'''(
    "$B" sleep 12
    {
        printf '\nP50_V113_PROFILE_BEGIN\n'
        printf 'P50_V113_REPORT_UPTIME '; cat /proc/uptime
        if [ -r /tmp/p50-v113-firefox-exec ]; then cat /tmp/p50-v113-firefox-exec; printf '\n'; else printf 'P50_V113_FIREFOX_EXEC_MISSING\n'; fi
        printf '\n--- systemd startup ---\n'; systemd-analyze time || true
        printf '\n--- lightdm critical chain ---\n'; systemd-analyze critical-chain lightdm.service || true
        printf '\n--- lightdm and live-config journal ---\n'; journalctl -b -u lightdm.service -u live-config.service --no-pager -o short-monotonic || true
        printf '\n--- session processes ---\n'; ps -eo pid,ppid,user,comm,args | grep -E '[f]irefox|[X]org|[l]ightdm|[o]penbox' || true
        printf '\nP50_V113_PROFILE_END\n'
    } >/dev/ttyS0 2>&1
) &
'''


def patch_main(text, mode):
    if text.count(MAIN_MARKER)!=1 or 'P50_V113_PREFETCH' in text or 'P50_V113_PROFILE' in text:
        raise ValueError('Unexpected or already patched main boot script')
    if mode=='profile':
        return text.replace(MAIN_MARKER,PROFILE_MAIN+MAIN_MARKER,1)
    if mode not in ('xul','browser'):
        raise ValueError('Unknown main experiment')
    files=['"${rootmnt}/usr/lib/firefox-esr/libxul.so"']
    if mode=='browser':
        files += ['"${rootmnt}/usr/lib/firefox-esr/omni.ja"','"${rootmnt}/usr/lib/firefox-esr/browser/omni.ja"']
    hook='''
\t# P50_V113_PREFETCH: speculative, reclaimable page-cache reads; no file changes.
\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
\t\t( cat '''+' '.join(files)+''' >/dev/null 2>&1 ) &
\tfi
'''
    return text.replace(MAIN_MARKER,hook+MAIN_MARKER,1)


def patch_helper(text, mode):
    if text.count(DEVICE_MARKER)!=1 or 'P50_V113_SETTLE' in text or 'P50_V113_NO_GLOBAL_SETTLE' in text:
        raise ValueError('Unexpected or already patched backing-device helper')
    if mode=='no-settle':
        return text.replace(DEVICE_MARKER,DEVICE_MARKER.replace('            udevadm settle\n','            # P50_V113_NO_GLOBAL_SETTLE: explicit node verification remains below.\n',1),1)
    if mode=='profile':
        replacement=DEVICE_MARKER.replace('            udevadm settle\n',
            '            printf "P50_V113_SETTLE_BEGIN %s\\n" "$(cat /proc/uptime)" >/dev/ttyS0\n'
            '            udevadm settle\n'
            '            printf "P50_V113_SETTLE_END %s\\n" "$(cat /proc/uptime)" >/dev/ttyS0\n',1)
        return text.replace(DEVICE_MARKER,replacement,1)
    raise ValueError('Unknown helper experiment')


def patch_migration(text):
    if text.count(MIGRATION_MARKER)!=1 or 'P50_V113_PROFILE_BEGIN' in text:
        raise ValueError('Unexpected or already patched migration script')
    return text.replace(MIGRATION_MARKER,PROFILE_REPORT+MIGRATION_MARKER,1)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path)
    parser.add_argument('mode',choices=('xul','browser','no-settle','profile'));args=parser.parse_args()
    root=args.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify the running system')
    targets=[]
    if args.mode in ('xul','browser','profile'):
        targets.append((root/'usr/lib/live/boot/9990-main.sh',lambda s:patch_main(s,args.mode)))
    if args.mode in ('no-settle','profile'):
        targets.append((root/'usr/lib/live/boot/9990-misc-helpers.sh',lambda s:patch_helper(s,args.mode)))
    if args.mode=='profile':targets.append((root/'usr/lib/p50-stage/p50-migrate.sh',patch_migration))
    changes=[]
    for path,fn in targets:
        if path.is_symlink() or not path.is_file():raise ValueError('Expected a regular extracted boot script: '+str(path))
        changes.append((path,fn(path.read_text())))
    for path,content in changes:path.write_text(content)

if __name__=='__main__':main()
