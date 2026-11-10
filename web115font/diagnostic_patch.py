#!/usr/bin/env python3
"""Install test-only pre-session verification and a nonblocking cache-open trace."""
import argparse
from pathlib import Path

MARKER='\n\tFstab\n\tNetbase\n'
PROOF=r'''
\t# P50_FONT_DIAGNOSTIC_ONLY: verify installed caches before starting systemd.
\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
\t\t{
\t\t\techo P50_FONT_BEFORE_INIT_BEGIN
\t\t\tfor p50_font_phase in BEFORE AFTER; do
\t\t\t\tif [ "${p50_font_phase}" = AFTER ]; then
\t\t\t\t\techo P50_FONT_VALIDITY_BEGIN
\t\t\t\t\tif LC_ALL=C chroot "${rootmnt}" /usr/bin/fc-cache -s -v; then p50_font_rc=0; else p50_font_rc=$?; fi
\t\t\t\t\tprintf 'P50_FONT_VALIDITY_RC %s\n' "${p50_font_rc}"
\t\t\t\t\techo P50_FONT_VALIDITY_END
\t\t\t\tfi
\t\t\t\tfor p50_font_src in /usr/lib/p50-fontcache/*-le64.cache-9; do
\t\t\t\t\tp50_font_name="${p50_font_src##*/}"
\t\t\t\t\tp50_font_a=$(/usr/lib/p50-stage/busybox sha256sum "${p50_font_src}" 2>/dev/null) || p50_font_a=missing
\t\t\t\t\tp50_font_b=$(/usr/lib/p50-stage/busybox sha256sum "${rootmnt}/var/cache/fontconfig/${p50_font_name}" 2>/dev/null) || p50_font_b=missing
\t\t\t\t\tprintf 'P50_FONT_%s %s %s %s\n' "${p50_font_phase}" "${p50_font_name}" "${p50_font_a%% *}" "${p50_font_b%% *}"
\t\t\t\tdone
\t\t\tdone
\t\t\techo P50_FONT_BEFORE_INIT_END
\t\t} >/dev/ttyS0 2>&1
\t\tp50_watch="${rootmnt}/etc/systemd/system/p50-fontwatch.service"
\t\tp50_wants="${rootmnt}/etc/systemd/system/sysinit.target.wants"
\t\t[ ! -e "${p50_watch}" ] && [ ! -L "${p50_watch}" ] && [ ! -L "${p50_wants}" ] || panic "p50: unexpected diagnostic watcher"
\t\tmkdir -p "${p50_wants}" || panic "p50: cannot create diagnostic watcher directory"
\t\tcat > "${p50_watch}" <<'P50_FONT_WATCH_UNIT'
[Unit]
Description=Diagnostic font cache open watcher
DefaultDependencies=no
Requires=local-fs.target
After=local-fs.target
Before=sysinit.target lightdm.service
[Service]
Type=notify
NotifyAccess=main
ExecStart=/run/p50-stage/tools/font-access /dev/ttyS0 15 /
TimeoutStartSec=10
[Install]
WantedBy=sysinit.target
P50_FONT_WATCH_UNIT
\t\tln -s ../p50-fontwatch.service "${p50_wants}/p50-fontwatch.service" || panic "p50: cannot enable diagnostic watcher"
\tfi
'''.replace('\\t','\t')

def patch_main(text):
 if text.count(MARKER)!=1 or 'P50_FONT_DIAGNOSTIC_ONLY' in text or 'P50_V114_OPTIONAL_FONTCACHE' not in text:raise ValueError('Unexpected clean boot script')
 return text.replace(MARKER,PROOF+MARKER,1)

def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root.resolve(strict=True)
 if root==Path('/'):raise ValueError('Refusing to modify running system')
 path=root/'usr/lib/live/boot/9990-main.sh'
 if path.is_symlink() or not path.is_file():raise ValueError('Expected isolated regular boot script')
 path.write_text(patch_main(path.read_text()))
if __name__=='__main__':main()
