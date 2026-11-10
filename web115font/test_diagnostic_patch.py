import os,subprocess,tempfile,unittest
from pathlib import Path
from diagnostic_patch import PROOF,MARKER,patch_main
from font_cache_clean import patch_main as clean_patch

class DiagnosticTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.src=self.base/'source';self.src.mkdir()
  (self.src/'a-le64.cache-9').write_bytes(b'font data')
  self.root=self.base/'guest';self.dest=self.root/'var/cache/fontconfig';self.dest.mkdir(parents=True)
  (self.dest/'a-le64.cache-9').write_bytes(b'font data')
  self.bin=self.base/'busybox';self.bin.write_text('#!/bin/sh\nexec "$@"\n');self.bin.chmod(0o755)
 def tearDown(self):self.tmp.cleanup()
 def run_proof(self,toram=''):
  hook=PROOF.replace('/usr/lib/p50-fontcache','"$TEST_SOURCE"').replace('/usr/lib/p50-stage/busybox','"$TEST_BB"').replace('>/dev/ttyS0','>"$TEST_SERIAL"').replace('chroot "${rootmnt}" /usr/bin/fc-cache -s -v','fake_fc_cache')
  pre='''set -e
panic(){ echo "$*" >&2; exit 42; }
fake_fc_cache(){ echo '/usr/share/fonts: skipping, existing cache is valid: 1 fonts, 0 dirs'; }
function [ { if test "$#" -eq 3 && test "$1" = "-b" && test "$2" = "/dev/mapper/p50-staged-root"; then return 0; fi; builtin [ "$@"; }
'''
  return subprocess.run(['bash','-c',pre+hook],env={**os.environ,'TORAM':toram,'rootmnt':str(self.root),'TEST_SOURCE':str(self.src),'TEST_BB':str(self.bin),'TEST_SERIAL':str(self.base/'serial')},capture_output=True,text=True)
 def test_emits_preinit_hashes_and_creates_a_watcher_only_for_fast_boot(self):
  result=self.run_proof();self.assertEqual(result.returncode,0,result.stderr)
  serial=(self.base/'serial').read_text();self.assertIn('P50_FONT_BEFORE a-le64.cache-9',serial);self.assertIn('P50_FONT_AFTER a-le64.cache-9',serial);self.assertIn('P50_FONT_VALIDITY_RC 0',serial)
  unit=self.root/'etc/systemd/system/p50-fontwatch.service';self.assertIn('Before=sysinit.target lightdm.service',unit.read_text())
 def test_fullram_fallback_is_not_instrumented(self):
  result=self.run_proof('1');self.assertEqual(result.returncode,0,result.stderr);self.assertFalse((self.base/'serial').exists());self.assertFalse((self.root/'etc').exists())
 def test_accepts_only_clean_script_and_inserts_once(self):
  clean=clean_patch('#!/bin/sh'+MARKER);diag=patch_main(clean)
  self.assertLess(diag.index('P50_V114_OPTIONAL_FONTCACHE'),diag.index('P50_FONT_DIAGNOSTIC_ONLY'));self.assertLess(diag.index('P50_FONT_DIAGNOSTIC_ONLY'),diag.index('Fstab'))
  self.assertEqual(subprocess.run(['sh','-n'],input=diag,text=True,capture_output=True).returncode,0)
  for bad in ('different',diag):
   with self.assertRaises(ValueError):patch_main(bad)
if __name__=='__main__':unittest.main()
