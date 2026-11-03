import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from direct_insmod_loader import generate
TEST='''drivers/scsi_mod.ko:
drivers/ata_piix.ko: drivers/scsi_mod.ko
drivers/sr_mod.ko: drivers/scsi_mod.ko
fs/isofs.ko:
drivers/loop.ko:
fs/squashfs.ko:
fs/overlay.ko:
drivers/evdev.ko:
drivers/psmouse.ko:
drivers/mousedev.ko:
'''
class Tests(unittest.TestCase):
 def test_recursion_order(self):
  _,o=generate(TEST,'6.18.60')
  self.assertLess(o.index('drivers/scsi_mod.ko'),o.index('drivers/ata_piix.ko'))
  self.assertLess(o.index('drivers/scsi_mod.ko'),o.index('drivers/sr_mod.ko'))
 def test_full_dependencies_included(self):
  sh,o=generate(TEST,'6.18.60')
  self.assertEqual(len(o),10)
  self.assertIn('insmod "/lib/modules/6.18.60/drivers/sr_mod.ko"',sh)
  self.assertIn('insmod "/lib/modules/6.18.60/drivers/evdev.ko"',sh)
  self.assertIn('insmod "/lib/modules/6.18.60/drivers/psmouse.ko"',sh)
  self.assertIn('insmod "/lib/modules/6.18.60/drivers/mousedev.ko"',sh)
 def test_missing_module_rejected(self):
  with self.assertRaises(ValueError):generate('fs/overlay.ko:\n','6.18.60')
 def test_bad_external_dependency(self):
  with self.assertRaises(ValueError):generate(TEST.replace('drivers/scsi_mod.ko:\n',''),'6.18.60')
 def test_validate_files(self):
  with self.assertRaises(ValueError):generate(TEST,'6.18.60',lambda p:p!='fs/overlay.ko')
