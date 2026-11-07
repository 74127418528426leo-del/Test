#!/usr/bin/env python3
"""Restrict the legacy test bridge to detected QEMU/KVM guest machines."""
import argparse
import json
from pathlib import Path

IP_TEST = "ip -o -4 addr show | grep -Eq 'inet 10\\.0\\.2\\.[0-9]+/' && \\\n"
HELPER = '''#!/bin/sh
# This bridge is for the developer's QEMU/KVM test environment only.
# Unknown, unavailable, or failed detection must never enable a proxy.
kind=$(systemd-detect-virt --vm 2>/dev/null) || exit 1
case "$kind" in
  qemu|kvm) exit 0 ;;
  *) exit 1 ;;
esac
'''


def patch(root):
    root = Path(root).resolve(strict=True)
    if root == Path('/') or not root.is_dir():
        raise ValueError('Refusing to patch the running host')
    directory = root / 'usr/local/sbin'
    probe = directory / 'puppy50-network-probe'
    helper = directory / 'puppy50-qemu-bridge-allowed'
    if not probe.is_file() or not probe.resolve().is_relative_to(root):
        raise ValueError('Expected extracted v104 network probe is missing')
    original = probe.read_text()
    if original.count(IP_TEST) != 1 or helper.exists():
        raise ValueError('Unrecognized or already modified network probe')
    replacement = '/usr/local/sbin/puppy50-qemu-bridge-allowed && \\\n     ' + IP_TEST
    helper.write_text(HELPER)
    helper.chmod(0o755)
    probe.write_text(original.replace(IP_TEST, replacement, 1))
    return {'guarded_qemu_bridge': True, 'direct_connect_code_unchanged': True,
            'firefox_tls_settings_unchanged': True, 'physical_network_tested': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('extracted_root', type=Path)
    print(json.dumps(patch(parser.parse_args().extracted_root), indent=2))
