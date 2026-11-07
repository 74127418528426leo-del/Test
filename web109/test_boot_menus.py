import unittest
from boot_menus import patch_bios, patch_grub

BIOS='''label live-amd64
\tmenu label ^Live system (amd64)
\tmenu default
\tlinux /live/vmlinuz
\tinitrd /live/initrd.img
\tappend boot=live components toram quiet locales=en_US.UTF-8

label live-amd64-failsafe
\tmenu label Live system (amd64 fail-safe mode)
\tlinux /live/vmlinuz
\tinitrd /live/initrd.img
\tappend boot=live components memtest noapic noapm nodma nomce nosmp nosplash vga=788
'''
GRUB='''source /boot/grub/config.cfg
menuentry "Live system (amd64)" --hotkey=l {
\tlinux\t/live/vmlinuz-6.12.115+deb13.1-amd64 boot=live components toram quiet locales=en_US.UTF-8 findiso=${iso_path}
\tinitrd\t/live/initrd.img-6.12.115+deb13.1-amd64
}
menuentry "Live system (amd64 fail-safe mode)" {
\tlinux\t/live/vmlinuz-6.12.115+deb13.1-amd64 boot=live components memtest noapic noapm nodma nomce nosmp nosplash vga=788
\tinitrd\t/live/initrd.img-6.12.115+deb13.1-amd64
}
menuentry "Verify integrity" {
\tlinux /live/vmlinuz boot=live components toram verify-checksums
}
'''
class MenuTests(unittest.TestCase):
    def test_bios_default_is_fast_and_both_fallbacks_copy_to_ram(self):
        out=patch_bios(BIOS)
        fast,rest=out.split('label live-amd64-fullram',1)
        fullram,recovery=rest.split('label live-amd64-failsafe',1)
        self.assertNotIn('components toram',fast)
        self.assertIn('components toram quiet',fullram)
        self.assertIn('components toram memtest',recovery)
        self.assertIn('wait for RAM READY',fast)
    def test_uefi_default_is_fast_and_other_entries_keep_toram(self):
        out=patch_grub(GRUB)
        fast,rest=out.split('menuentry "Full RAM first (fallback)"',1)
        fullram,recovery=rest.split('menuentry "Recovery',1)
        self.assertNotIn('components toram',fast)
        self.assertIn('components toram quiet',fullram)
        self.assertIn('components toram memtest',recovery)
        self.assertIn('components toram verify-checksums',recovery)
    def test_rejects_missing_or_ambiguous_originals(self):
        for fn in (patch_bios,patch_grub):
            with self.assertRaises(ValueError):fn('unexpected')
        with self.assertRaises(ValueError):patch_bios(BIOS+BIOS)
        with self.assertRaises(ValueError):patch_grub(GRUB+GRUB)

if __name__=='__main__':unittest.main()
