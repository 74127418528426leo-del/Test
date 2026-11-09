import unittest
from menus import patch_menus

BIOS='''label live\n append boot=live components usb-storage.delay_use=0 quiet\nlabel full\n append boot=live components toram quiet\nlabel recovery\n append boot=live components toram noapic\n'''
UEFI='''menuentry fast {\n linux /live/vmlinuz boot=live components quiet\n}\nmenuentry full {\n linux /live/vmlinuz boot=live components toram quiet\n}\nmenuentry recovery {\n linux /live/vmlinuz boot=live components toram noapic\n}\nmenuentry verify {\n linux /live/vmlinuz boot=live components toram verify-checksums\n}\n# linux /live/vmlinuz boot=live toram\n'''
class MenuTests(unittest.TestCase):
 def test_adds_full_layer_only_to_full_ram_entries(self):
  b,u=patch_menus(BIOS,UEFI)
  self.assertIn('append boot=live components usb-storage.delay_use=0 quiet',b)
  self.assertEqual(b.count('toram module=full'),2)
  self.assertEqual(u.count('toram module=full'),3)
  self.assertIn('# linux /live/vmlinuz boot=live toram',u)
 def test_unexpected_or_already_patched_menu_is_rejected(self):
  with self.assertRaises(ValueError):patch_menus(BIOS.replace(' toram noapic',' noapic'),UEFI)
  b,u=patch_menus(BIOS,UEFI)
  with self.assertRaises(ValueError):patch_menus(b,u)
if __name__=='__main__':unittest.main()
