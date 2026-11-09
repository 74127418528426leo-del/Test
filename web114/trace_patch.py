#!/usr/bin/env python3
"""Install a short-lived open monitor in an isolated diagnostic initramfs."""
import argparse
from pathlib import Path

MARKER='\n\tFstab\n\tNetbase\n'
HOOK=r'''
\t# P50_V114_OPEN_TRACE: diagnostic only; unchanged full-RAM fallback.
\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
\t\tp50_unit="${rootmnt}/etc/systemd/system/p50-open-trace.service"
\t\tp50_wants="${rootmnt}/etc/systemd/system/sysinit.target.wants"
\t\t[ ! -e "${p50_unit}" ] && [ ! -L "${p50_unit}" ] && [ ! -L "${p50_wants}" ] || panic "p50: unexpected trace service"
\t\tmkdir -p "${p50_wants}" || panic "p50: cannot create trace service directory"
\t\t[ ! -e "${p50_wants}/p50-open-trace.service" ] && [ ! -L "${p50_wants}/p50-open-trace.service" ] || panic "p50: trace service already enabled"
\t\tcat > "${p50_unit}" <<'P50_V114_TRACE_UNIT'
[Unit]
Description=Experimental nonblocking startup file-open trace
DefaultDependencies=no
Requires=local-fs.target
After=local-fs.target
Before=sysinit.target lightdm.service
[Service]
Type=notify
NotifyAccess=main
ExecStart=/run/p50-stage/tools/p50-open-trace /run/p50-stage/open-trace.tsv 22 /
ExecStopPost=-/usr/bin/curl --fail --connect-timeout 5 --max-time 15 --noproxy=* --data-binary=@/run/p50-stage/open-trace.tsv http://10.0.2.2:8767/trace --output /run/p50-stage/trace-response.txt
Nice=10
TimeoutStartSec=10
[Install]
WantedBy=sysinit.target
P50_V114_TRACE_UNIT
\t\tln -s ../p50-open-trace.service "${p50_wants}/p50-open-trace.service" || panic "p50: cannot enable trace service"
\tfi
'''.replace('\\t','\t')

def patch_main(text):
    if text.count(MARKER)!=1 or 'P50_V114_OPEN_TRACE' in text:
        raise ValueError('Unexpected or already patched live boot main')
    return text.replace(MARKER,HOOK+MARKER,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    root=a.root.resolve(strict=True)
    if root==Path('/'):raise ValueError('Refusing to modify the running system')
    path=root/'usr/lib/live/boot/9990-main.sh'
    if path.is_symlink() or not path.is_file():raise ValueError('Expected regular boot main')
    path.write_text(patch_main(path.read_text()))

if __name__=='__main__':main()
