import tempfile
import unittest
from pathlib import Path

import lean_initrd


BIOS = '''label live-amd64
\tmenu label ^Fast start (wait for RAM READY)
\tlinux /live/vmlinuz
\tinitrd /live/initrd.img
\tappend boot=live components quiet
label live-amd64-fullram
\tmenu label Full RAM first (fallback)
\tlinux /live/vmlinuz
\tinitrd /live/initrd.img
\tappend boot=live components toram quiet
label live-amd64-failsafe
\tmenu label Recovery (full RAM, safe mode)
\tlinux /live/vmlinuz
\tinitrd /live/initrd.img
\tappend boot=live components toram memtest
'''
GRUB = '''menuentry "Fast start (wait for RAM READY)" --hotkey=l {
\tlinux\t/live/vmlinuz boot=live components quiet findiso=${iso_path}
\tinitrd\t/live/initrd.img-6.12.115+deb13.1-amd64
}
menuentry "Full RAM first (fallback)" {
\tlinux\t/live/vmlinuz boot=live components toram quiet findiso=${iso_path}
\tinitrd\t/live/initrd.img-6.12.115+deb13.1-amd64
}
menuentry "Recovery (full RAM, safe mode)" {
\tlinux\t/live/vmlinuz boot=live components toram memtest
\tinitrd\t/live/initrd.img-6.12.115+deb13.1-amd64
}
'''


class LeanInitrdTests(unittest.TestCase):
    def test_fallbacks_use_original_initrd_and_fast_entry_remains_unchanged(self):
        bios, grub = lean_initrd.patch_menus(BIOS, GRUB)
        self.assertEqual(bios.count('\tinitrd /live/initrd.img\n'), 1)
        self.assertEqual(bios.count('\tinitrd /live/initrd-full.img\n'), 2)
        self.assertEqual(grub.count('\tinitrd\t/live/initrd.img-6.12.115+deb13.1-amd64\n'), 1)
        self.assertEqual(grub.count('\tinitrd\t/live/initrd-full.img\n'), 2)
        self.assertIn('menuentry "Fast start (wait for RAM READY)"', grub)

    def test_missing_or_ambiguous_menu_rejected(self):
        with self.assertRaises(ValueError):
            lean_initrd.patch_menus(BIOS.replace('label live-amd64-fullram', 'label missing'), GRUB)
        with self.assertRaises(ValueError):
            lean_initrd.patch_menus(BIOS, GRUB + GRUB)

    def test_only_selected_early_firmware_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'firmware').mkdir()
            (root / 'firmware/a').write_bytes(b'abc')
            (root / 'firmware/b').write_bytes(b'defg')
            (root / 'firmware/keep').write_bytes(b'keep')
            result = lean_initrd.remove_early_firmware(root, {'firmware/a': 3, 'firmware/b': 4})
            self.assertFalse((root / 'firmware/a').exists())
            self.assertFalse((root / 'firmware/b').exists())
            self.assertEqual((root / 'firmware/keep').read_bytes(), b'keep')
            self.assertEqual(sum(x['size'] for x in result), 7)

    def test_validation_happens_before_any_file_is_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'a').write_bytes(b'abc')
            with self.assertRaises(ValueError):
                lean_initrd.remove_early_firmware(root, {'a': 3, 'missing': 4})
            self.assertEqual((root / 'a').read_bytes(), b'abc')

    def test_symlink_and_parent_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'root'
            root.mkdir()
            outside = Path(temp) / 'outside'
            outside.write_bytes(b'abc')
            (root / 'link').symlink_to(outside)
            for name in ['link', '../outside']:
                with self.assertRaises(ValueError):
                    lean_initrd.remove_early_firmware(root, {name: 3})
            self.assertEqual(outside.read_bytes(), b'abc')


if __name__ == '__main__':
    unittest.main()
