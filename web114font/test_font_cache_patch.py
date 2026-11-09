import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from font_cache_patch import HOOK,MARKER,MIGRATE,patch_main,patch_migration

class CachePatchTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.source=self.root/'source';self.source.mkdir();(self.source/'test.cache-8').write_bytes(b'unchanged-cache')
  (self.root/'guest/var/cache/fontconfig').mkdir(parents=True)
 def tearDown(self):self.temp.cleanup()
 def run_hook(self,toram=''):
  script=HOOK.replace('p50_cache_source=/usr/lib/p50-fontcache','p50_cache_source="$TEST_SOURCE"')
  pre='''panic(){ echo "$*" >&2; exit 42; }
function [ { if test "$#" -eq 3 && test "$1" = "-b" && test "$2" = "/dev/mapper/p50-staged-root"; then return 0; fi; builtin [ "$@"; }
'''
  return subprocess.run(['bash','-c',pre+script],env={**os.environ,'TORAM':toram,'rootmnt':str(self.root/'guest'),'TEST_SOURCE':str(self.source)},capture_output=True,text=True)
 def test_staged_boot_installs_exact_cache_file(self):
  r=self.run_hook();self.assertEqual(r.returncode,0,r.stderr)
  self.assertEqual((self.root/'guest/var/cache/fontconfig/test.cache-8').read_bytes(),b'unchanged-cache')
 def test_full_ram_fallback_is_not_modified(self):
  r=self.run_hook('1');self.assertEqual(r.returncode,0,r.stderr)
  self.assertFalse((self.root/'guest/var/cache/fontconfig/test.cache-8').exists())
 def test_missing_or_symlinked_cache_destination_fails_closed(self):
  target=self.root/'guest/var/cache/fontconfig';target.rmdir();target.symlink_to(self.source,target_is_directory=True)
  r=self.run_hook();self.assertEqual(r.returncode,42)
 def test_scripts_have_one_expected_insertion_and_valid_shell(self):
  main=patch_main('#!/bin/sh'+MARKER);migration=patch_migration('#!/bin/sh\n'+MIGRATE)
  for s in (main,migration):self.assertEqual(subprocess.run(['sh','-n'],input=s,text=True,capture_output=True).returncode,0)
  for f,s in ((patch_main,'wrong'),(patch_main,main),(patch_migration,'wrong'),(patch_migration,migration)):
   with self.assertRaises(ValueError):f(s)
if __name__=='__main__':unittest.main()
