import subprocess
import tempfile
import unittest
from pathlib import Path
from fault_patch import patch_helper,patch_migration

ROOT=Path(__file__).resolve().parents[1]
DUAL=next((ROOT/n for n in ('web115dual','v115_duallayer') if (ROOT/n).is_dir()),None)

class FaultPatchTests(unittest.TestCase):
 def test_helper_retains_real_suspend_and_recovery_ioctls(self):
  source=(DUAL/'p50-switch-extra.c').read_text()
  result=patch_helper(source)
  self.assertLess(result.index('req.flags=DM_SUSPEND_FLAG;'),result.index('P50_TEST_POST_SUSPEND_INJECTED'))
  self.assertLess(result.index('P50_TEST_POST_SUSPEND_INJECTED'),result.index('call(fd,DM_TABLE_CLEAR'))
  self.assertIn('P50_TEST_REAL_RECOVERY clear=%d resume=%d',result)
  with self.assertRaises(ValueError):patch_helper(result)
 def test_migration_diagnostic_fails_closed_after_recovery(self):
  import sys
  sys.path.insert(0,str(DUAL))
  from dual_patch import patch_migration as build_dual
  base=(DUAL/'p50-migrate.sh').read_text()
  result=patch_migration(build_dual(base))
  self.assertIn('P50_TEST_EXTRA_TABLE_RESTORED',result)
  self.assertIn("fail 'injected post-suspend failure'",result)
  self.assertIn('P50_DUAL_RETAINED_LOOPS_AND_COPIES',result)
  self.assertEqual(subprocess.run(['sh','-n'],input=result,text=True).returncode,0)
  with self.assertRaises(ValueError):patch_migration(result)

if __name__=='__main__':unittest.main()
