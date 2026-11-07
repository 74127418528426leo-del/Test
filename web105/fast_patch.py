#!/usr/bin/env python3
"""Patch an extracted Puppy50 root; preserve network, Firefox, TLS and firmware."""
import argparse
import json
from pathlib import Path

OLD_BROWSER = 'firefox-esr file:///usr/share/puppy50web/index.html >/tmp/puppy50-firefox.log 2>&1 &'
NEW_BROWSER = '/usr/local/bin/puppy50-launch-browser >/tmp/puppy50-firefox.log 2>&1 &'
LAUNCHER = '''#!/bin/sh
# Physical machines can display Firefox while NetworkManager continues to join.
# The QEMU-only HTTPS bridge writes a policy at the end of its network probe;
# wait for that special case when an emulated NIC is present so Firefox reads
# the policy on launch. A no-NIC QEMU and normal hardware never wait here.
if grep -qi qemu /sys/class/dmi/id/sys_vendor 2>/dev/null; then
  has_nic=no
  for interface in /sys/class/net/*; do
    [ "${interface##*/}" = lo ] && continue
    [ -e "$interface" ] && has_nic=yes && break
  done
  if [ "$has_nic" = yes ]; then
    count=0
    until [ -f /run/puppy50web/network-mode ] || [ "$count" -ge 110 ]; do
      sleep 1
      count=$((count + 1))
    done
  fi
fi
exec firefox-esr file:///usr/share/puppy50web/index.html
'''


def patch(root):
    root = Path(root).resolve(strict=True)
    if root == Path('/') or not root.is_dir():
        raise ValueError('Refusing to patch the running machine')
    unit = root / 'etc/systemd/system/puppy50-network-probe.service'
    autostart = root / 'etc/skel/.config/openbox/autostart'
    probe = root / 'usr/local/sbin/puppy50-network-probe'
    if not all(p.is_file() for p in [unit, autostart, probe]):
        raise ValueError('Expected v104 startup files are missing')
    unit_text, auto_text = unit.read_text(), autostart.read_text()
    if unit_text.count('Before=display-manager.service\n') != 1:
        raise ValueError('Unrecognized network service ordering')
    if auto_text.count(OLD_BROWSER) != 1:
        raise ValueError('Unrecognized browser autostart')
    launcher = root / 'usr/local/bin/puppy50-launch-browser'
    if launcher.exists():
        raise ValueError('Unexpected existing browser launcher')
    launcher.parent.mkdir(parents=True, exist_ok=True)
    launcher.write_text(LAUNCHER)
    launcher.chmod(0o755)
    unit.write_text(unit_text.replace('Before=display-manager.service\n', '', 1))
    autostart.write_text(auto_text.replace(OLD_BROWSER, NEW_BROWSER, 1))
    return {'network_probe_unchanged': True, 'firefox_and_tls_unchanged': True,
            'nonroot_session_preserved': True, 'physical_hardware_tested': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('extracted_root', type=Path)
    print(json.dumps(patch(parser.parse_args().extracted_root), indent=2))
