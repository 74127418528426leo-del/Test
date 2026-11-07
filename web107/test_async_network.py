import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest

from async_network import patch

UNIT = '''[Unit]\nWants=NetworkManager-wait-online.service\nAfter=NetworkManager.service NetworkManager-wait-online.service\nBefore=display-manager.service\n[Service]\nType=oneshot\nExecStart=/usr/local/sbin/puppy50-network-probe\n'''
AUTOSTART = '''#!/bin/sh\nnm-applet &\nfirefox-esr file:///usr/share/puppy50web/index.html >/tmp/puppy50-firefox.log 2>&1 &\n'''


class AsyncNetworkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.unit = self.root / 'etc/systemd/system/puppy50-network-probe.service'
        self.auto = self.root / 'etc/skel/.config/openbox/autostart'
        self.probe = self.root / 'usr/local/sbin/puppy50-network-probe'
        self.guard = self.root / 'usr/local/sbin/puppy50-qemu-bridge-allowed'
        for f, text in [(self.unit, UNIT), (self.auto, AUTOSTART), (self.probe, 'probe untouched'), (self.guard, 'guard untouched')]:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)
        self.cmdline = self.root / 'cmdline'
        self.marker = self.root / 'network-mode'
        self.failflag = self.root / 'service-failed'
        fakebin = self.root / 'bin'
        fakebin.mkdir()
        fake = fakebin / 'systemctl'
        fake.write_text('#!/bin/sh\n[ -e "$P50_FAKE_FAILURE" ]\n')
        fake.chmod(0o755)
        self.env = dict(os.environ, PATH=str(fakebin)+':/usr/bin:/bin', P50_FAKE_FAILURE=str(self.failflag))

    def tearDown(self):
        self.tmp.cleanup()

    def test_nonblocking_default_preserves_probe_and_network_applet(self):
        patch(self.root)
        self.assertNotIn('Before=display-manager.service', self.unit.read_text())
        self.assertIn('After=NetworkManager.service NetworkManager-wait-online.service', self.unit.read_text())
        self.assertIn('nm-applet', self.auto.read_text())
        self.assertIn('/usr/local/bin/puppy50-fast-browser', self.auto.read_text())
        self.assertEqual(self.probe.read_text(), 'probe untouched')
        self.assertEqual(self.guard.read_text(), 'guard untouched')

    def test_normal_boot_never_waits_for_absent_network_marker(self):
        patch(self.root)
        self.cmdline.write_text('boot=live toram quiet')
        waiter = self.root / 'usr/local/libexec/puppy50-wait-test-bridge'
        start = time.monotonic()
        self.assertEqual(subprocess.run([waiter, self.cmdline, self.marker], env=self.env, timeout=2).returncode, 0)
        self.assertLess(time.monotonic()-start, .8)

    def test_opt_in_waits_until_policy_selection_is_finished(self):
        patch(self.root)
        self.cmdline.write_text('boot=live puppy50.test_bridge=1 toram')
        waiter = self.root / 'usr/local/libexec/puppy50-wait-test-bridge'
        thread = threading.Thread(target=lambda: (time.sleep(.2), self.marker.write_text('qemu-bridge')))
        thread.start()
        start = time.monotonic()
        try:
            self.assertEqual(subprocess.run([waiter, self.cmdline, self.marker], env=self.env, timeout=4).returncode, 0)
            self.assertGreaterEqual(time.monotonic()-start, .2)
            self.assertTrue(self.marker.exists())
        finally:
            thread.join(timeout=2)

    def test_opt_in_stops_waiting_when_probe_service_has_failed(self):
        patch(self.root)
        self.cmdline.write_text('boot=live toram puppy50.test_bridge=1')
        self.failflag.touch()
        waiter = self.root / 'usr/local/libexec/puppy50-wait-test-bridge'
        self.assertEqual(subprocess.run([waiter, self.cmdline, self.marker], env=self.env, timeout=2).returncode, 0)
        self.assertFalse(self.marker.exists())

    def test_inexact_opt_in_token_does_not_wait(self):
        patch(self.root)
        self.cmdline.write_text('boot=live puppy50.test_bridge=10')
        waiter = self.root / 'usr/local/libexec/puppy50-wait-test-bridge'
        self.assertEqual(subprocess.run([waiter, self.cmdline, self.marker], env=self.env, timeout=2).returncode, 0)

    def test_unrecognized_startup_refuses_without_partial_edits(self):
        self.auto.write_text('unknown autostart')
        with self.assertRaises(ValueError):
            patch(self.root)
        self.assertEqual(self.unit.read_text(), UNIT)
        self.assertFalse((self.root / 'usr/local/bin/puppy50-fast-browser').exists())


if __name__ == '__main__':
    unittest.main()
