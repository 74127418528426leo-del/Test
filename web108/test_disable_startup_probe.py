import tempfile
import unittest
from pathlib import Path

from disable_startup_probe import disable_startup_probe


class StartupProbeDisableTests(unittest.TestCase):
    def fixture(self, temp):
        root = Path(temp) / 'image'
        unit_dir = root / 'etc/systemd/system'
        wants = unit_dir / 'multi-user.target.wants'
        wants.mkdir(parents=True)
        unit = unit_dir / 'puppy50-network-probe.service'
        unit.write_text('[Unit]\nBefore=display-manager.service\n[Service]\nExecStart=/usr/local/sbin/puppy50-network-probe\n')
        (wants / unit.name).symlink_to('/etc/systemd/system/' + unit.name)
        network = root / 'usr/sbin/NetworkManager'
        network.parent.mkdir(parents=True)
        network.write_bytes(b'network manager')
        return root, unit, wants / unit.name, network

    def test_masks_only_the_automatic_developer_probe(self):
        with tempfile.TemporaryDirectory() as temp:
            root, unit, enabled, network = self.fixture(temp)
            disable_startup_probe(root)
            self.assertTrue(unit.is_symlink())
            self.assertEqual(unit.readlink(), Path('/dev/null'))
            self.assertFalse(enabled.is_symlink())
            self.assertEqual(network.read_bytes(), b'network manager')

    def test_rejects_unexpected_unit_without_mutating_anything(self):
        with tempfile.TemporaryDirectory() as temp:
            root, unit, enabled, network = self.fixture(temp)
            unit.write_text('[Service]\nExecStart=/some/other/program\n')
            with self.assertRaises(ValueError):
                disable_startup_probe(root)
            self.assertEqual(unit.read_text(), '[Service]\nExecStart=/some/other/program\n')
            self.assertTrue(enabled.is_symlink())
            self.assertEqual(network.read_bytes(), b'network manager')

    def test_rejects_an_enable_link_pointing_elsewhere(self):
        with tempfile.TemporaryDirectory() as temp:
            root, unit, enabled, _ = self.fixture(temp)
            enabled.unlink()
            enabled.symlink_to('/etc/systemd/system/unrelated.service')
            with self.assertRaises(ValueError):
                disable_startup_probe(root)
            self.assertFalse(unit.is_symlink())
            self.assertEqual(enabled.readlink(), Path('/etc/systemd/system/unrelated.service'))


if __name__ == '__main__':
    unittest.main()
