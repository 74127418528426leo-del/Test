import os
import tempfile
import unittest
from pathlib import Path

from split_firmware import split_firmware


class FirmwareLayerTests(unittest.TestCase):
    def fixture(self, temp):
        root, layer = Path(temp) / 'root', Path(temp) / 'layer'
        firmware = root / 'usr/lib/firmware'
        firmware.mkdir(parents=True)
        layer.mkdir()
        (firmware / 'network.bin').write_bytes(b'network firmware')
        (firmware / 'graphics.bin').write_bytes(b'graphics firmware')
        (firmware / 'alias.bin').symlink_to('network.bin')
        (root / 'usr/lib/library.so').write_bytes(b'important library')
        return root, layer, firmware

    def test_moves_complete_firmware_tree_without_changing_other_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root, layer, firmware = self.fixture(temp)
            os.utime(root / 'usr/lib', ns=(1_400_000_000_000_000_000, 1_400_000_000_000_000_000))
            before = (root / 'usr/lib').stat().st_mtime_ns
            split_firmware(root, layer)
            self.assertFalse(firmware.exists())
            self.assertEqual((layer / 'usr/lib/firmware/network.bin').read_bytes(), b'network firmware')
            self.assertEqual((layer / 'usr/lib/firmware/alias.bin').readlink(), Path('network.bin'))
            self.assertEqual((root / 'usr/lib/library.so').read_bytes(), b'important library')
            self.assertEqual((root / 'usr/lib').stat().st_mtime_ns, before)
            self.assertEqual((layer / 'usr/lib').stat().st_mtime_ns, before)

    def test_rejects_firmware_symlink_without_touching_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root, layer, firmware = self.fixture(temp)
            import shutil
            shutil.rmtree(firmware)
            outside = Path(temp) / 'outside'
            outside.mkdir()
            (outside / 'keep').write_text('safe')
            firmware.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                split_firmware(root, layer)
            self.assertEqual((outside / 'keep').read_text(), 'safe')

    def test_rejects_existing_layer_target_and_nested_layer(self):
        with tempfile.TemporaryDirectory() as temp:
            root, layer, firmware = self.fixture(temp)
            (layer / 'usr/lib/firmware').mkdir(parents=True)
            with self.assertRaises(ValueError):
                split_firmware(root, layer)
            self.assertTrue((firmware / 'network.bin').exists())
            nested = root / 'nested'
            nested.mkdir()
            with self.assertRaises(ValueError):
                split_firmware(root, nested)
            self.assertTrue((firmware / 'network.bin').exists())

    def test_layer_root_retains_source_root_permissions(self):
        with tempfile.TemporaryDirectory() as temp:
            root, layer, _ = self.fixture(temp)
            os.chmod(root, 0o755)
            os.chmod(layer, 0o700)
            os.utime(root, ns=(1_400_000_000_000_000_000, 1_400_000_000_000_000_000))
            split_firmware(root, layer)
            self.assertEqual(layer.stat().st_mode & 0o7777, root.stat().st_mode & 0o7777)
            self.assertEqual(layer.stat().st_uid, root.stat().st_uid)
            self.assertEqual(layer.stat().st_gid, root.stat().st_gid)
            self.assertEqual(layer.stat().st_mtime_ns, root.stat().st_mtime_ns)


if __name__ == '__main__':
    unittest.main()
