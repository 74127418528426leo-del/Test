#!/usr/bin/env python3
"""Patch extracted experimental Debian Live root, NEVER the running host."""
import argparse,json
from pathlib import Path
CONF="""[Seat:*]
autologin-user=user
autologin-user-timeout=0
user-session=openbox
autologin-session=openbox
greeter-hide-users=false
allow-guest=false
"""
PREFLIGHT=r'''#!/bin/sh
set -eu
say(){ printf '%s\n' "$1" >/dev/ttyS0 2>/dev/null || true; }
if ! grep -q 'boot=live' /proc/cmdline;then say P50_V91_NON_LIVE_BOOT_REFUSED;exit 28;fi
say P50_V91_LIVE_LOGIN_PREFLIGHT_STARTED
if ! id user >/dev/null 2>&1;then
 useradd -m -s /bin/bash -c 'Puppy50 Live' user
 say P50_V91_LIVE_ACCOUNT_CREATED
else
 say P50_V91_LIVE_ACCOUNT_PRESENT
fi
install -d -m 0755 -o user -g "$(id -gn user)" /home/user/.config/openbox
if [ ! -f /etc/skel/.config/openbox/autostart ];then say P50_V91_NO_SKELETON_AUTOSTART;exit 29;fi
cp /etc/skel/.config/openbox/autostart /home/user/.config/openbox/autostart
chown user:"$(id -gn user)" /home/user/.config/openbox/autostart
chmod 0755 /home/user/.config/openbox/autostart
say P50_V91_OPENBOX_AUTOSTART_COPIED
# Live-only overlay. This file takes precedence over LightDM conf.d snippets.
cat >/etc/lightdm/lightdm.conf <<'EOF'
[Seat:*]
autologin-user=user
autologin-user-timeout=0
user-session=openbox
autologin-session=openbox
greeter-hide-users=false
allow-guest=false
EOF
if [ ! -f /usr/share/xsessions/openbox.desktop ];then say P50_V91_OPENBOX_XSESSION_MISSING;exit 30;fi
say P50_V91_LIGHTDM_AUTOLOGIN_PREPARED
exit 0
'''
PROBE=r'''#!/bin/sh
set -u
say(){ printf '%s\n' "$1" >/dev/ttyS0 2>/dev/null || true; }
sleep 60
n=0
while [ "$n" -lt 12 ];do
 if id user >/dev/null 2>&1;then say P50_V91_USER_PRESENT;else say P50_V91_USER_MISSING;fi
 if pgrep -u user -f '[f]irefox' >/dev/null 2>&1;then
  say P50_V91_NONROOT_FIREFOX_PROCESS_SEEN
  exit 0
 fi
 say P50_V91_FIREFOX_NOT_VISIBLE_TO_PROCESS_PROBE
 n=$((n+1))
 sleep 15
done
if [ -r /var/log/lightdm/lightdm.log ];then
 grep -Ei 'error|failed|session|autologin|user' /var/log/lightdm/lightdm.log | tail -12 | sed 's/^/P50_V91_LIGHTDM_LOG /' >/dev/ttyS0 2>/dev/null || true
fi
exit 0
'''
UNIT="""[Unit]
Description=Puppy50 Live graphical process diagnostics
After=lightdm.service
Wants=lightdm.service
[Service]
Type=simple
ExecStart=/usr/local/sbin/puppy50-gui-diagnostics
User=root
NoNewPrivileges=true
[Install]
WantedBy=multi-user.target
"""
DROPIN="""[Unit]
After=live-config.service
Wants=live-config.service
[Service]
ExecStartPre=/usr/local/sbin/puppy50-prepare-session
"""
def write(path,content,mode=0o644):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content)
    path.chmod(mode)
def patch(root):
    root=Path(root).resolve(strict=True)
    if root==Path("/") or not root.is_dir():raise ValueError("Never modify real system root")
    mandatory=['usr/bin/firefox-esr','usr/bin/lightdm',
      'usr/share/xsessions/openbox.desktop','etc/skel/.config/openbox/autostart',
      'usr/local/sbin/puppy50-network-probe','etc/ssl/certs/ca-certificates.crt']
    missing=[p for p in mandatory if not (root/p).exists()]
    if missing:raise ValueError("Required real Live packages missing: "+repr(missing))
    source=root/'etc/lightdm/lightdm.conf.d/50-puppy50.conf'
    if not source.is_file() or 'autologin-user=user' not in source.read_text():
        raise ValueError('Unrecognized original live LightDM config')
    write(root/'etc/lightdm/lightdm.conf.d/99-puppy50-autologin.conf',CONF)
    write(root/'usr/local/sbin/puppy50-prepare-session',PREFLIGHT,0o755)
    write(root/'usr/local/sbin/puppy50-gui-diagnostics',PROBE,0o755)
    write(root/'etc/systemd/system/lightdm.service.d/10-puppy50-live-preflight.conf',DROPIN)
    write(root/'etc/systemd/system/puppy50-gui-diagnostics.service',UNIT)
    return {'schema':'PUPPY50_V91_LIVE_GUI_BOOT_FIX',
       'nonroot_live_account_prepared':True,'only_live_boot_allowed':True,
       'Firefox_binary_modified':False,'NetworkManager_modified':False,
       'TLS_or_sandbox_disabled':False,'physical_WiFi_proven':False,
       'real_Firefox_page_proven':False}
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('extracted_root',type=Path)
    args=parser.parse_args()
    print(json.dumps(patch(args.extracted_root),indent=2))
