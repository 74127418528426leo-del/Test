import tempfile
import unittest
from pathlib import Path

from trim_gpu_firmware import trim_gpu_firmware


class GraphicsFirmwarePruningTests(unittest.TestCase):
    def test_only_the_explicit_graphics_firmware_trees_are_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'root'
            paths = [
                'usr/lib/firmware/amdgpu/card.bin',
                'usr/lib/firmware/radeon/card.bin',
                'usr/lib/firmware/nvidia/ga102/gsp.bin',
                'usr/lib/firmware/i915/graphics.bin',
                'usr/lib/firmware/iwlwifi-card.ucode',
                'usr/lib/firmware/rtl_nic/ethernet.bin',
                'usr/lib/firefox-esr/firefox-esr',
                'etc/ssl/certs/ca-certificates.crt',
            ]
            for relative in paths:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(relative.encode())
            result = trim_gpu_firmware(root)
            for relative in paths[:3]:
                self.assertFalse((root / relative).exists())
            for relative in paths[3:]:
                self.assertEqual((root / relative).read_bytes(), relative.encode())
            self.assertEqual(set(result), {'amdgpu', 'radeon', 'nvidia'})
            self.assertTrue(all(result[name]['files'] == 1 for name in result))

    def test_rejects_a_symlink_target_before_deleting_anything(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            firmware = temp / 'root/usr/lib/firmware'
            (firmware / 'amdgpu').mkdir(parents=True)
            (firmware / 'amdgpu/keep.bin').write_text('keep')
            outside = temp / 'outside'
            outside.mkdir()
            (outside / 'keep.bin').write_text('keep')
            (firmware / 'radeon').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                trim_gpu_firmware(temp / 'root')
            self.assertEqual((outside / 'keep.bin').read_text(), 'keep')
            self.assertTrue((firmware / 'amdgpu/keep.bin').exists())

    def test_rejects_symlinked_ancestors(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            root = temp / 'root'
            root.mkdir()
            outside = temp / 'elsewhere'
            (outside / 'lib/firmware/nvidia').mkdir(parents=True)
            (outside / 'lib/firmware/nvidia/keep.bin').write_text('keep')
            (root / 'usr').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                trim_gpu_firmware(root)
            self.assertTrue((outside / 'lib/firmware/nvidia/keep.bin').exists())


if __name__ == '__main__':
    unittest.main()
