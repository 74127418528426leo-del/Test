import unittest
from boot_menu import patch_syslinux, patch_grub


class AutomaticMenuTests(unittest.TestCase):
    def test_syslinux_waits_briefly_and_boots_existing_default(self):
        old = 'include menu.cfg\ndefault vesamenu.c32\nprompt 0\ntimeout 0\n'
        new = patch_syslinux(old)
        self.assertIn('timeout 20\n', new)
        self.assertNotIn('timeout 0\n', new)
        self.assertIn('default vesamenu.c32\n', new)

    def test_grub_waits_briefly_and_preserves_default(self):
        new = patch_grub('set default=0\n\nsource /boot/grub/theme.cfg\n')
        self.assertIn('set default=0\n', new)
        self.assertIn('set timeout_style=menu\n', new)
        self.assertIn('set timeout=2\n', new)

    def test_unrecognized_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            patch_syslinux('already different')
        with self.assertRaises(ValueError):
            patch_grub('already different')


if __name__ == '__main__':
    unittest.main()
