#!/usr/bin/env python3
"""Let the standard live browser start while its network probe runs.

The optional, explicitly opted-in QEMU proxy must finish writing its Firefox
policy before Firefox starts. The network probe and proxy guard are unchanged.
"""
import argparse
import json
from pathlib import Path

OLD = 'firefox-esr file:///usr/share/puppy50web/index.html >/tmp/puppy50-firefox.log 2>&1 &'
NEW = '/usr/local/bin/puppy50-fast-browser >/tmp/puppy50-firefox.log 2>&1 &'
LAUNCHER = '''#!/bin/sh
/usr/local/libexec/puppy50-wait-test-bridge
exec firefox-esr file:///usr/share/puppy50web/index.html
'''
WAITER = '''#!/bin/sh
# Real machines and normal virtual boots do not need a test proxy policy.
# A deliberately enabled test bridge must finish its policy decision before
# Firefox starts. If the system service fails, the direct browser can open.
cmdline=${1:-/proc/cmdline}
marker=${2:-/run/puppy50web/network-mode}
/usr/bin/grep -Eq '(^|[[:space:]])puppy50[.]test_bridge=1([[:space:]]|$)' "$cmdline" 2>/dev/null || exit 0
while [ ! -f "$marker" ]; do
  if systemctl is-failed --quiet puppy50-network-probe.service 2>/dev/null; then
    exit 0
  fi
  # A oneshot with RemainAfterExit becomes active only after it exits.
  # If it completed but could not write the marker, no late policy write can occur.
  state=$(systemctl show --property=ActiveState --value puppy50-network-probe.service 2>/dev/null || true)
  [ "$state" = active ] && exit 0
  sleep 1
done
exit 0
'''


def patch(root):
    root = Path(root).resolve(strict=True)
    if root == Path('/') or not root.is_dir():
        raise ValueError('Refusing to modify the running system')
    unit = root / 'etc/systemd/system/puppy50-network-probe.service'
    autostart = root / 'etc/skel/.config/openbox/autostart'
    probe = root / 'usr/local/sbin/puppy50-network-probe'
    guard = root / 'usr/local/sbin/puppy50-qemu-bridge-allowed'
    inputs = [unit, autostart, probe, guard]
    if any(not f.is_file() or not f.resolve().is_relative_to(root) for f in inputs):
        raise ValueError('Expected v106 network or session files missing')
    unit_text, auto_text = unit.read_text(), autostart.read_text()
    if unit_text.count('Before=display-manager.service\n') != 1 or auto_text.count(OLD) != 1:
        raise ValueError('Unrecognized network ordering or browser autostart')
    launch = root / 'usr/local/bin/puppy50-fast-browser'
    waiter = root / 'usr/local/libexec/puppy50-wait-test-bridge'
    if launch.exists() or waiter.exists():
        raise ValueError('Unexpected existing launcher')
    for path, content in [(launch, LAUNCHER), (waiter, WAITER)]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        path.chmod(0o755)
    unit.write_text(unit_text.replace('Before=display-manager.service\n', '', 1))
    autostart.write_text(auto_text.replace(OLD, NEW, 1))
    return {'network_probe_and_guard_unchanged': True,
            'default_network_wait_removed_from_display_path': True,
            'test_bridge_policy_waits_for_probe': True,
            'physical_hardware_tested': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('extracted_root', type=Path)
    print(json.dumps(patch(p.parse_args().extracted_root), indent=2))
