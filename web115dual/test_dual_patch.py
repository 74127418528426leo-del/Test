import subprocess
import unittest
from pathlib import Path
from dual_patch import patch_helper,patch_migration
from stage_boot_patch import HOOK

BASE=(Path(__file__).parent/'p50-migrate.sh').read_text()

class DualPatchTests(unittest.TestCase):
 def test_both_copies_must_verify_before_any_mapper_switch(self):
  text=patch_migration(BASE)
  for token in ('P50_DUAL_EXTRA_COPY_VERIFIED','p50-switch-extra','P50_DUAL_EXTRA_RAM_BACKING'):
   self.assertIn(token,text)
  self.assertLess(text.index('P50_DUAL_EXTRA_COPY_VERIFIED'),text.index('SWITCH_ATTEMPTED=1'))
  self.assertLess(text.index('p50-switch-extra'),text.index('emit P50_STAGE_READY'))
  self.assertIn('(size + extra_size + 1023) / 1024',text)
  self.assertIn('"$B" losetup -d "$EXTRA_OLD_LOOP"',text)
  self.assertIn('"$B" losetup -d "$OLD_LOOP"',text)
  self.assertIn('P50_DUAL_RETAINED_LOOPS_AND_COPIES',text)
  result=subprocess.run(['sh','-n'],input=text,text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_failed_or_repeated_patch_is_refused(self):
  for source in ('wrong',BASE+BASE,patch_migration(BASE)):
   with self.assertRaises(ValueError):patch_migration(source)
  with self.assertRaises(ValueError):patch_helper(patch_helper(HOOK))
 def test_extra_mapping_is_only_created_on_staged_local_media_path(self):
  text=patch_helper(HOOK)
  self.assertIn('[ -z "${TORAM:-}" ]',text)
  self.assertIn('/run/live/medium/live/extras.squashfs',text)
  self.assertIn('p50-staged-extra',text)
  self.assertEqual(subprocess.run(['sh','-n'],input=text,text=True,capture_output=True).returncode,0)

if __name__=='__main__':unittest.main()
