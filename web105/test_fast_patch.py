import tempfile
import unittest
from pathlib import Path
from fast_patch import patch

SERVICE = '''[Unit]\nWants=NetworkManager-wait-online.service\nAfter=NetworkManager.service NetworkManager-wait-online.service\nBefore=display-manager.service\n[Service]\nExecStart=/usr/local/sbin/puppy50-network-probe\n'''
AUTOSTART = '''#!/bin/sh\nnm-applet &\nfirefox-esr file:///usr/share/puppy50web/index.html >/tmp/puppy50-firefox.log 2>&1 &\n'''


class FastBootPatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.unit = self.root / 'etc/systemd/system/puppy50-network-probe.service'
        self.autostart = self.root / 'etc/skel/.config/openbox/autostart'
        self.probe = self.root / 'usr/local/sbin/puppy50-network-probe'
        for path, contents in [(self.unit, SERVICE), (self.autostart, AUTOSTART), (self.probe, 'unchanged')]:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)

    def tearDown(self):
        self.temp.cleanup()

    def test_network_probe_no_longer_blocks_display_or_changes_the_probe(self):
        patch(self.root)
        self.assertNotIn('Before=display-manager.service', self.unit.read_text())
        self.assertIn('NetworkManager-wait-online.service', self.unit.read_text())
        self.assertEqual('unchanged', self.probe.read_text())

    def test_nonroot_session_uses_browser_launcher_and_keeps_network_applet(self):
        patch(self.root)
        self.assertIn('nm-applet', self.autostart.read_text())
        self.assertIn('/usr/local/bin/puppy50-launch-browser', self.autostart.read_text())
        self.assertTrue((self.root / 'usr/local/bin/puppy50-launch-browser').stat().st_mode & 0o111)

    def test_unknown_autostart_is_rejected_without_partial_edits(self):
        self.autostart.write_text('different setup')
        with self.assertRaises(ValueError):
            patch(self.root)
        self.assertEqual(SERVICE, self.unit.read_text())


if __name__ == '__main__':
    unittest.main()
