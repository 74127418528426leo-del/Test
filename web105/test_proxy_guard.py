import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from proxy_guard import patch

ORIGINAL = """#!/bin/sh
if ip -o -4 addr show | grep -Eq 'inet 10\\.0\\.2\\.[0-9]+/' && \\
     curl --proxy http://10.0.2.2:3128 https://example.com/; then
  echo bridge
fi
"""


class ProxyGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.probe = self.root / 'usr/local/sbin/puppy50-network-probe'
        self.probe.parent.mkdir(parents=True)
        self.probe.write_text(ORIGINAL)
        self.probe.chmod(0o755)
        self.bin = self.root / 'fakebin'
        self.bin.mkdir()
        detector = self.bin / 'systemd-detect-virt'
        detector.write_text('#!/bin/sh\nprintf "%s\\n" "$TEST_KIND"\nexit "${TEST_EXIT:-0}"\n')
        detector.chmod(0o755)
        self.cmdline = self.root / 'cmdline'
        self.cmdline.write_text('boot=live toram puppy50.test_bridge=1 quiet')

    def tearDown(self):
        self.temp.cleanup()

    def test_fallback_is_guarded_and_direct_tls_code_is_not_replaced(self):
        patch(self.root)
        new = self.probe.read_text()
        self.assertIn('/usr/local/sbin/puppy50-qemu-bridge-allowed &&', new)
        self.assertIn('curl --proxy http://10.0.2.2:3128 https://example.com/', new)
        self.assertEqual(self.probe.stat().st_mode & 0o777, 0o755)

    def test_detector_allows_only_qemu_and_kvm(self):
        patch(self.root)
        helper = self.root / 'usr/local/sbin/puppy50-qemu-bridge-allowed'
        for kind, allowed in [('kvm', True), ('qemu', True), ('none', False),
                              ('vmware', False), ('', False)]:
            with self.subTest(kind=kind):
                env = dict(os.environ, PATH=str(self.bin), TEST_KIND=kind)
                self.assertEqual(subprocess.run([helper, self.cmdline], env=env).returncode == 0, allowed)

    def test_vm_alone_never_enables_bridge_without_explicit_boot_opt_in(self):
        patch(self.root)
        helper = self.root / 'usr/local/sbin/puppy50-qemu-bridge-allowed'
        env = dict(os.environ, PATH=str(self.bin), TEST_KIND='kvm')
        for cmdline in ['boot=live toram', 'badpuppy50.test_bridge=1',
                        'puppy50.test_bridge=10', 'puppy50Xtest_bridge=1']:
            with self.subTest(cmdline=cmdline):
                self.cmdline.write_text(cmdline)
                self.assertNotEqual(subprocess.run([helper, self.cmdline], env=env).returncode, 0)

    def test_detector_failure_or_missing_detector_denies_bridge(self):
        patch(self.root)
        helper = self.root / 'usr/local/sbin/puppy50-qemu-bridge-allowed'
        env = dict(os.environ, PATH=str(self.bin), TEST_KIND='kvm', TEST_EXIT='1')
        self.assertNotEqual(subprocess.run([helper, self.cmdline], env=env).returncode, 0)
        env = dict(os.environ, PATH=str(self.root / 'missing'), TEST_KIND='')
        self.assertNotEqual(subprocess.run([helper, self.cmdline], env=env).returncode, 0)

    def test_unrecognized_script_is_rejected_without_creating_helper(self):
        self.probe.write_text('unknown script')
        with self.assertRaises(ValueError):
            patch(self.root)
        self.assertFalse((self.probe.parent / 'puppy50-qemu-bridge-allowed').exists())


if __name__ == '__main__':
    unittest.main()
